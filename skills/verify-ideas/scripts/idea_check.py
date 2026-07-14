#!/usr/bin/env python3
"""Prepare and validate harness-neutral Idea Check verification runs."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
PROFILES = ("ci", "release", "weekly")
RESULTS = ("supported", "contradicted", "inconclusive", "blocked", "not_applicable")


class IdeaCheckError(Exception):
    pass


@dataclass(frozen=True)
class Idea:
    id: str
    path: str
    title: str
    profiles: list[str]
    blocking: bool
    content: str


def _run_git(root: Path, *args: str) -> str:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()
    except (FileNotFoundError, subprocess.CalledProcessError):
        return ""


def revision(root: Path) -> str:
    return _run_git(root, "rev-parse", "--short=12", "HEAD") or "unknown"


def tracked_state(root: Path) -> str:
    status = _run_git(root, "status", "--porcelain=v1", "--untracked-files=all")
    lines = [line for line in status.splitlines() if ".idea-check/" not in line]
    payload = "\n".join(
        [
            *lines,
            "-- unstaged diff --",
            _run_git(root, "diff", "--binary"),
            "-- staged diff --",
            _run_git(root, "diff", "--cached", "--binary"),
        ]
    )
    return hashlib.sha256(payload.encode()).hexdigest()


def changed_files(root: Path, base: str | None) -> list[str]:
    if not base:
        return []
    output = _run_git(root, "diff", "--name-only", f"{base}...HEAD")
    if not output:
        output = _run_git(root, "diff", "--name-only", base)
    return [line for line in output.splitlines() if line]


def _frontmatter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end < 0:
        raise IdeaCheckError("Idea frontmatter starts with --- but has no closing ---")
    metadata: dict[str, str] = {}
    for raw in text[4:end].splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if ":" not in raw:
            raise IdeaCheckError(f"Invalid operational metadata line: {raw}")
        key, value = raw.split(":", 1)
        metadata[key.strip()] = value.strip()
    return metadata, text[end + 5 :]


def _list_value(value: str | None, default: list[str]) -> list[str]:
    if value is None:
        return default
    stripped = value.strip()
    if stripped.startswith("[") and stripped.endswith("]"):
        stripped = stripped[1:-1]
    values = [part.strip().strip("'\"") for part in stripped.split(",")]
    return [value for value in values if value]


def _bool_value(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    normalized = value.lower()
    if normalized in ("true", "yes", "1"):
        return True
    if normalized in ("false", "no", "0"):
        return False
    raise IdeaCheckError(f"Expected true or false, got {value!r}")


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def read_idea(root: Path, file_path: Path, ideas_dir: Path) -> Idea:
    text = file_path.read_text(encoding="utf-8")
    metadata, body = _frontmatter(text)
    relative = file_path.relative_to(root).as_posix()
    fallback_id = file_path.relative_to(ideas_dir).with_suffix("").as_posix().replace("/", ".")
    idea_id = metadata.get("id", fallback_id)
    if not re.fullmatch(r"[a-z0-9][a-z0-9._-]*", idea_id):
        raise IdeaCheckError(f"{relative}: id must use lowercase letters, digits, dots, dashes, or underscores")
    profiles = _list_value(metadata.get("profiles"), list(PROFILES))
    unknown_profiles = sorted(set(profiles) - set(PROFILES))
    if unknown_profiles:
        raise IdeaCheckError(f"{relative}: unknown profiles: {', '.join(unknown_profiles)}")
    title_match = re.search(r"^#\s+(.+?)\s*$", body, re.MULTILINE)
    title = title_match.group(1) if title_match else idea_id
    if len(body.strip()) < 20:
        raise IdeaCheckError(f"{relative}: idea body is too short to verify")
    return Idea(
        id=idea_id,
        path=relative,
        title=title,
        profiles=profiles,
        blocking=_bool_value(metadata.get("blocking"), True),
        content=body.strip(),
    )


def discover(root: Path, ideas_path: str, profile: str | None = None) -> list[Idea]:
    root = root.resolve()
    ideas_dir = (root / ideas_path).resolve()
    if not ideas_dir.is_dir():
        raise IdeaCheckError(f"Ideas directory does not exist: {ideas_dir}")
    ideas: list[Idea] = []
    ids: set[str] = set()
    for file_path in sorted(ideas_dir.rglob("*.md")):
        if file_path.name.lower() == "readme.md" or any(part.startswith(".") for part in file_path.relative_to(ideas_dir).parts):
            continue
        idea = read_idea(root, file_path, ideas_dir)
        if idea.id in ids:
            raise IdeaCheckError(f"Duplicate idea id: {idea.id}")
        ids.add(idea.id)
        if profile is None or profile in idea.profiles:
            ideas.append(idea)
    if not ideas:
        suffix = f" for profile {profile}" if profile else ""
        raise IdeaCheckError(f"No idea files found{suffix} under {ideas_path}")
    return ideas


def protocol_path() -> Path:
    return Path(__file__).resolve().parent.parent / "references" / "verification-protocol.md"


def schema_path() -> Path:
    return Path(__file__).resolve().parent.parent / "references" / "report-schema.json"


def prepare(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    if not root.is_dir():
        raise IdeaCheckError(f"Project root does not exist: {root}")
    ideas = discover(root, args.ideas, args.profile)
    output = (root / args.output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    (output / "artifacts").mkdir(exist_ok=True)
    (output / "work").mkdir(exist_ok=True)

    request = {
        "schema_version": SCHEMA_VERSION,
        "profile": args.profile,
        "revision": revision(root),
        "ideas_path": args.ideas,
        "changed_since": args.changed_since,
        "changed_files": changed_files(root, args.changed_since),
        "tracked_state": tracked_state(root),
        "ideas": [asdict(idea) for idea in ideas],
    }
    request_file = output / "request.json"
    request_file.write_text(json.dumps(request, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (output / "report-schema.json").write_text(schema_path().read_text(encoding="utf-8"), encoding="utf-8")

    relative_output = output.relative_to(root).as_posix()
    prompt = f"""# Idea Check verification run

Act as an independent product verifier. Attempt to falsify every selected idea against the current repository and environment.

The human-owned request is at `{relative_output}/request.json`. Read it completely, including each idea's natural-language content.

{protocol_path().read_text(encoding='utf-8')}

## Run-specific constraints

- Work from `{root}`.
- Use the `{args.profile}` profile.
- Do not modify tracked project files.
- Put disposable probes only under `{relative_output}/work/`.
- Put screenshots, logs, and other retained evidence only under `{relative_output}/artifacts/`.
- Investigate every idea in the request, even when recent changes appear unrelated.
- Your final response must be JSON only and must conform to `{relative_output}/report-schema.json`.
- Use the exact request profile, revision, idea IDs, and idea paths.
- Do not wrap the JSON in Markdown fences.

The deterministic validator will reject omitted or duplicate ideas, profile or revision mismatches, malformed evidence, and tracked-file modifications. It will compute the gate from the request's human-owned `blocking` fields.
"""
    (output / "prompt.md").write_text(prompt, encoding="utf-8")
    print(f"Prepared {len(ideas)} idea(s) for {args.profile} verification in {output}")
    return 0


def _expect(condition: bool, message: str) -> None:
    if not condition:
        raise IdeaCheckError(message)


def _validate_evidence(evidence: Any, idea_id: str) -> None:
    _expect(isinstance(evidence, list), f"{idea_id}: evidence must be an array")
    for index, entry in enumerate(evidence):
        prefix = f"{idea_id}: evidence[{index}]"
        _expect(isinstance(entry, dict), f"{prefix} must be an object")
        required = {"kind", "description", "direct"}
        allowed = required | {"command", "exit_code", "location", "artifact"}
        _expect(required <= entry.keys(), f"{prefix} is missing {sorted(required - entry.keys())}")
        _expect(set(entry) <= allowed, f"{prefix} has unknown fields {sorted(set(entry) - allowed)}")
        _expect(isinstance(entry["kind"], str) and entry["kind"], f"{prefix}.kind must be a string")
        _expect(isinstance(entry["description"], str) and entry["description"], f"{prefix}.description must be a string")
        _expect(isinstance(entry["direct"], bool), f"{prefix}.direct must be a boolean")
        if "exit_code" in entry:
            _expect(isinstance(entry["exit_code"], int), f"{prefix}.exit_code must be an integer")


def validate_report(request: dict[str, Any], report: dict[str, Any], root: Path) -> tuple[int, str]:
    _expect(report.get("schema_version") == SCHEMA_VERSION, "Unsupported or missing report schema_version")
    _expect(report.get("profile") == request["profile"], "Report profile does not match request")
    _expect(report.get("revision") == request["revision"], "Report revision does not match request")
    _expect(isinstance(report.get("summary"), str) and report["summary"], "Report summary must be a non-empty string")
    _expect(isinstance(report.get("ideas"), list), "Report ideas must be an array")
    _expect(set(report) == {"schema_version", "profile", "revision", "summary", "ideas"}, "Report has missing or unknown top-level fields")

    requested = {idea["id"]: idea for idea in request["ideas"]}
    reported: dict[str, dict[str, Any]] = {}
    for item in report["ideas"]:
        _expect(isinstance(item, dict), "Each idea result must be an object")
        required = {"id", "path", "result", "summary", "evidence", "gaps"}
        _expect(set(item) == required, f"Idea result has missing or unknown fields: {item.get('id', '<unknown>')}")
        idea_id = item["id"]
        _expect(isinstance(idea_id, str), "Idea result id must be a string")
        _expect(idea_id in requested, f"Report contains unrequested idea: {idea_id}")
        _expect(idea_id not in reported, f"Report contains duplicate idea: {idea_id}")
        _expect(item["path"] == requested[idea_id]["path"], f"{idea_id}: path does not match request")
        _expect(item["result"] in RESULTS, f"{idea_id}: invalid result {item['result']!r}")
        _expect(isinstance(item["summary"], str) and item["summary"], f"{idea_id}: summary must be a non-empty string")
        _validate_evidence(item["evidence"], idea_id)
        _expect(isinstance(item["gaps"], list) and all(isinstance(gap, str) and gap for gap in item["gaps"]), f"{idea_id}: gaps must be strings")
        if item["result"] == "supported":
            _expect(any(entry["direct"] for entry in item["evidence"]), f"{idea_id}: supported requires at least one direct evidence entry")
        if item["result"] in ("inconclusive", "blocked"):
            _expect(bool(item["gaps"]), f"{idea_id}: {item['result']} requires at least one evidence gap")
        reported[idea_id] = item

    missing = sorted(set(requested) - set(reported))
    _expect(not missing, f"Report omitted requested ideas: {', '.join(missing)}")
    _expect(tracked_state(root) == request["tracked_state"], "Verifier changed tracked project state")

    blocking = [reported[idea_id]["result"] for idea_id, idea in requested.items() if idea["blocking"]]
    if "contradicted" in blocking:
        code = 1
        gate = "FAIL: at least one blocking idea was contradicted"
    elif any(result != "supported" for result in blocking):
        code = 2
        gate = "UNKNOWN: at least one blocking idea was not supported"
    else:
        code = 0
        gate = "PASS: all blocking ideas are supported"
    return code, gate


def render_summary(request: dict[str, Any], report: dict[str, Any], gate: str) -> str:
    blocking_by_id = {idea["id"]: idea["blocking"] for idea in request["ideas"]}
    lines = [
        "# Idea Check report",
        "",
        f"**Profile:** {report['profile']}",
        f"**Revision:** {report['revision']}",
        f"**Gate:** {gate}",
        "",
        report["summary"],
        "",
    ]
    for item in report["ideas"]:
        blocking = "blocking" if blocking_by_id[item["id"]] else "non-blocking"
        lines.extend([
            f"## {item['id']}",
            "",
            f"**{item['result'].upper()}** · {blocking}",
            "",
            item["summary"],
            "",
        ])
        if item["evidence"]:
            lines.append("Evidence:")
            lines.append("")
            for evidence in item["evidence"]:
                direct = "direct" if evidence["direct"] else "inferred"
                lines.append(f"- `{evidence['kind']}` ({direct}): {evidence['description']}")
            lines.append("")
        if item["gaps"]:
            lines.append("Gaps:")
            lines.append("")
            lines.extend(f"- {gap}" for gap in item["gaps"])
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def validate(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    request_path = (root / args.request).resolve()
    report_path = (root / args.report).resolve()
    _expect(request_path.is_file(), f"Request does not exist: {request_path}")
    _expect(report_path.is_file(), f"Report does not exist: {report_path}")
    try:
        request = json.loads(request_path.read_text(encoding="utf-8"))
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise IdeaCheckError(f"Invalid JSON: {error}") from error
    code, gate = validate_report(request, report, root)
    summary_path = report_path.parent / "summary.md"
    summary_path.write_text(render_summary(request, report, gate), encoding="utf-8")
    print(gate)
    print(f"Human-readable report: {summary_path}")
    return code


def list_ideas(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    for idea in discover(root, args.ideas, args.profile):
        profiles = ",".join(idea.profiles)
        print(f"{idea.id}\t{profiles}\tblocking={str(idea.blocking).lower()}\t{idea.path}")
    return 0


def new_idea(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    ideas_dir = root / args.ideas
    idea_id = _slug(args.id)
    _expect(bool(idea_id), "Idea id cannot be empty")
    path = ideas_dir / f"{idea_id}.md"
    _expect(not path.exists(), f"Idea already exists: {path}")
    ideas_dir.mkdir(parents=True, exist_ok=True)
    title = args.title or args.id.replace("-", " ").strip().title()
    path.write_text(
        f"---\nid: {idea_id}\nprofiles: [ci, release, weekly]\nblocking: true\n---\n\n"
        f"# {title}\n\nState the idea in ordinary language.\n\n"
        "Explain why it matters and the conditions under which it must remain true.\n\n"
        "The idea is false if ...\n",
        encoding="utf-8",
    )
    print(path)
    return 0


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(prog="idea-check", description=__doc__)
    result.add_argument("--root", default=".", help="Project root (default: current directory)")
    subcommands = result.add_subparsers(dest="command", required=True)

    prepare_parser = subcommands.add_parser("prepare", help="Prepare an agent verification request")
    prepare_parser.add_argument("--profile", choices=PROFILES, default="ci")
    prepare_parser.add_argument("--ideas", default="ideas")
    prepare_parser.add_argument("--output", default=".idea-check/current")
    prepare_parser.add_argument("--changed-since")
    prepare_parser.set_defaults(handler=prepare)

    validate_parser = subcommands.add_parser("validate", help="Validate and gate an agent report")
    validate_parser.add_argument("--request", default=".idea-check/current/request.json")
    validate_parser.add_argument("--report", default=".idea-check/current/report.json")
    validate_parser.set_defaults(handler=validate)

    list_parser = subcommands.add_parser("list", help="List discovered ideas")
    list_parser.add_argument("--ideas", default="ideas")
    list_parser.add_argument("--profile", choices=PROFILES)
    list_parser.set_defaults(handler=list_ideas)

    new_parser = subcommands.add_parser("new", help="Create a plain-language idea file")
    new_parser.add_argument("id")
    new_parser.add_argument("--title")
    new_parser.add_argument("--ideas", default="ideas")
    new_parser.set_defaults(handler=new_idea)
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        return args.handler(args)
    except IdeaCheckError as error:
        print(f"idea-check: {error}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
