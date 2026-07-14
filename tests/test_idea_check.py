import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "skills" / "verify-ideas" / "scripts" / "idea_check.py"
SPEC = importlib.util.spec_from_file_location("idea_check", SCRIPT)
idea_check = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
sys.modules[SPEC.name] = idea_check
SPEC.loader.exec_module(idea_check)


class IdeaCheckTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        (self.root / "ideas").mkdir()

    def tearDown(self):
        self.temporary.cleanup()

    def write_idea(self, name="durable.md", metadata="", body=None):
        body = body or "# Completed work is durable\n\nSaved customer work survives a refresh and a new login."
        text = f"---\n{metadata}\n---\n\n{body}" if metadata else body
        (self.root / "ideas" / name).write_text(text, encoding="utf-8")

    def prepare(self, profile="ci"):
        args = Namespace(
            root=str(self.root),
            ideas="ideas",
            output=".idea-check/current",
            profile=profile,
            changed_since=None,
        )
        self.assertEqual(0, idea_check.prepare(args))
        return json.loads((self.root / ".idea-check/current/request.json").read_text())

    def report(self, request, result="supported", gaps=None):
        idea = request["ideas"][0]
        return {
            "schema_version": 1,
            "profile": request["profile"],
            "revision": request["revision"],
            "summary": "Verification completed.",
            "ideas": [
                {
                    "id": idea["id"],
                    "path": idea["path"],
                    "result": result,
                    "summary": f"The idea is {result}.",
                    "evidence": [
                        {
                            "kind": "test",
                            "description": "A direct probe completed.",
                            "direct": True,
                            "command": "example-test",
                            "exit_code": 0,
                        }
                    ],
                    "gaps": gaps or [],
                }
            ],
        }

    def test_discovers_plain_markdown_without_behavioral_dsl(self):
        self.write_idea()
        ideas = idea_check.discover(self.root, "ideas", "ci")
        self.assertEqual("durable", ideas[0].id)
        self.assertTrue(ideas[0].blocking)
        self.assertEqual(list(idea_check.PROFILES), ideas[0].profiles)

    def test_operational_metadata_filters_profiles(self):
        self.write_idea(metadata="id: save-promise\nprofiles: [release, weekly]\nblocking: false")
        with self.assertRaises(idea_check.IdeaCheckError):
            idea_check.discover(self.root, "ideas", "ci")
        ideas = idea_check.discover(self.root, "ideas", "release")
        self.assertEqual("save-promise", ideas[0].id)
        self.assertFalse(ideas[0].blocking)

    def test_prepare_creates_request_prompt_and_schema(self):
        self.write_idea()
        request = self.prepare()
        self.assertEqual("ci", request["profile"])
        self.assertEqual(["durable"], [idea["id"] for idea in request["ideas"]])
        self.assertTrue((self.root / ".idea-check/current/prompt.md").is_file())
        self.assertTrue((self.root / ".idea-check/current/report-schema.json").is_file())

    def test_supported_blocking_idea_passes(self):
        self.write_idea()
        request = self.prepare()
        code, gate = idea_check.validate_report(request, self.report(request), self.root)
        self.assertEqual(0, code)
        self.assertIn("PASS", gate)

    def test_contradicted_blocking_idea_fails(self):
        self.write_idea()
        request = self.prepare()
        code, gate = idea_check.validate_report(request, self.report(request, "contradicted"), self.root)
        self.assertEqual(1, code)
        self.assertIn("FAIL", gate)

    def test_inconclusive_blocking_idea_is_unknown(self):
        self.write_idea()
        request = self.prepare()
        report = self.report(request, "inconclusive", ["A production environment was unavailable."])
        code, gate = idea_check.validate_report(request, report, self.root)
        self.assertEqual(2, code)
        self.assertIn("UNKNOWN", gate)

    def test_omitted_idea_is_rejected(self):
        self.write_idea()
        request = self.prepare()
        report = self.report(request)
        report["ideas"] = []
        with self.assertRaisesRegex(idea_check.IdeaCheckError, "omitted"):
            idea_check.validate_report(request, report, self.root)

    def test_tracked_state_detects_content_changes(self):
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True)
        tracked = self.root / "tracked.txt"
        tracked.write_text("before\n", encoding="utf-8")
        subprocess.run(["git", "add", "tracked.txt"], cwd=self.root, check=True)
        before = idea_check.tracked_state(self.root)
        tracked.write_text("after\n", encoding="utf-8")
        self.assertNotEqual(before, idea_check.tracked_state(self.root))


if __name__ == "__main__":
    unittest.main()
