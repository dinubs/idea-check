# Idea Check

Idea Check continuously verifies that plain-language product ideas remain true.

Humans own the ideas. Coding agents own the implementation. An independent verification run attempts to falsify each idea using the strongest evidence available in the current environment.

Idea files are ordinary Markdown, not executable specifications:

```md
---
id: completed-work-is-durable
profiles: [ci, release, weekly]
blocking: true
---

# Customers never lose completed work

When a customer sees “Saved,” their work survives refreshes, sign-outs,
deployments, and temporary network failure.

The idea is false if “Saved” is shown but an older version later appears.
```

Only the frontmatter is operational. It identifies the idea, chooses verification profiles, and controls gating. The claim stays natural language.

## How it works

```text
ideas/*.md
    ↓
idea-check prepare
    ↓
your chosen coding agent attempts falsification
    ↓
structured evidence report
    ↓
idea-check validate
```

The agent does not decide the CI exit status. The deterministic validator rejects omitted ideas, duplicate results, profile mismatches, and unsupported report shapes before applying the human-owned `blocking` setting.

## Use with any agent

Clone the repository and install `skills/verify-ideas/` using your harness's Agent Skills mechanism. The skill follows the open `SKILL.md` format.

Prepare a run:

```sh
bin/idea-check prepare --root /path/to/project --profile ci
```

Give `.idea-check/current/prompt.md` to the harness, constrain its final output with `.idea-check/current/report-schema.json`, and save the final JSON as `.idea-check/current/report.json`.

For Codex CLI:

```sh
codex exec \
  --sandbox workspace-write \
  --output-schema .idea-check/current/report-schema.json \
  -o .idea-check/current/report.json \
  - < .idea-check/current/prompt.md

bin/idea-check validate
```

Other harnesses use the same prepared prompt and report contract. They do not need Codex plugin support.

## GitHub Actions with Codex

```yaml
- uses: actions/checkout@v6
  with:
    fetch-depth: 0

- uses: dinubs/idea-check@v1
  with:
    openai-api-key: ${{ secrets.OPENAI_API_KEY }}
    profile: ci
```

The action uses `openai/codex-action` as one harness wrapper, validates the structured report, and exposes the evidence directory for artifact upload. API credentials are passed directly to the official Codex action rather than exported to repository-controlled build steps.

## Exit codes

- `0`: no blocking idea failed
- `1`: at least one blocking idea was contradicted
- `2`: at least one blocking idea was inconclusive, blocked, not applicable, or missing
- `3`: malformed request or report

## Project status

This is an early working prototype. The protocol and report format are intentionally small so they can evolve through use on real products instead of becoming another requirements language.
