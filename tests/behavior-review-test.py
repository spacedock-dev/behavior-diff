#!/usr/bin/env python3
"""Exercise the shipped replay CLI with synthetic records; no models/network."""

import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


SKILL = Path(__file__).resolve().parents[1] / "plugin/skills/behavior-review"


class ReplayTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="handoff-contract-")
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        self.home.chmod(0o700)
        self.root = self.home / "case"
        self.root.mkdir()
        shutil.copyfile(SKILL / "fixtures/synthetic.json", self.root / "synthetic.json")
        self.packet = json.loads((self.root / "synthetic.json").read_text())
        self.state = self.home / "session.json"
        self.call("init", goals=self.packet["goals"])

    def call(self, action, revision=1, ok=True, **fields):
        request = {"action": action, **fields}
        if action not in ("init", "show"):
            request["revision"] = revision
        before = self.state.read_bytes() if self.state.exists() else None
        result = subprocess.run(
            [
                "python3",
                str(SKILL / "scripts/replay.py"),
                "--state",
                str(self.state),
                "--root",
                str(self.root),
            ],
            input=json.dumps(request),
            text=True,
            capture_output=True,
        )
        self.assertEqual(result.returncode, 0 if ok else 1, result.stderr)
        if not ok:
            self.assertEqual(
                self.state.read_bytes() if self.state.exists() else None, before
            )
        return json.loads(result.stdout if ok else result.stderr)

    def bind(self, goal="checksum", revision=1, **overrides):
        observation = next(o for o in self.packet["observations"] if o["goal"] == goal)
        fields = dict(
            id=goal,
            status=observation["status"],
            origin="synthetic",
            reason=observation["reason"],
            scope=self.packet["scope"],
            citations=[observation["citation"]],
        )
        fields.update(overrides)
        return self.call("bind", revision, **fields)

    def rows(self, revision=1):
        self.call("confirm", revision)
        return {row["id"]: row for row in self.call("result", revision)["goals"]}

    def test_correction_preserves_other_support_and_clears_decision(self):
        self.bind("copy")
        self.bind()
        self.rows()
        self.call("decide", choice="accept")
        corrected = "Copy eventually — preserve recovery evidence, not strict ordering."
        state = self.call("correct", id="copy", text=corrected)
        self.assertEqual(state["revision"], 2)
        self.assertIsNone(state["decision"])
        self.assertNotIn("copy", state["bindings"])
        self.call("result", 2, ok=False)
        self.assertEqual(self.call("show")["revision"], 2)
        for action, fields in (
            ("result", {}),
            (
                "bind",
                dict(
                    id="copy",
                    status="supported",
                    origin="synthetic",
                    reason="Old mapping",
                    scope="Old scope",
                    citations=[self.packet["observations"][0]["citation"]],
                ),
            ),
        ):
            self.call(action, ok=False, **fields)
        rows = self.rows(2)
        self.assertEqual(rows["copy"]["text"], corrected)
        self.assertEqual(rows["copy"]["status"], "unverified")
        self.assertEqual(rows["checksum"]["status"], "supported")
        self.bind(
            "copy",
            2,
            status="supported",
            reason="Completion and recovery satisfy the corrected eventual-copy requirement.",
        )
        self.assertEqual(self.rows(2)["copy"]["status"], "supported")
        self.call("replace", 2, goals=self.packet["goals"])
        self.assertTrue(
            all(row["status"] == "unverified" for row in self.rows(3).values())
        )

    def test_support_contradiction_gap_and_read_only_evidence(self):
        self.bind("copy")
        self.bind()
        rows = self.rows()
        self.assertEqual(rows["copy"]["status"], "contradicted")
        self.assertEqual(rows["checksum"]["origin"], "synthetic")
        self.assertEqual(rows["service"]["status"], "unverified")
        self.assertTrue(rows["service"]["next"])
        before = (self.root / "synthetic.json").read_bytes()
        excerpt = self.call(
            "evidence", citation=self.packet["observations"][0]["citation"]
        )
        self.assertIn("error: source does not exist", excerpt["excerpt"])
        self.assertIn("status Done", excerpt["excerpt"])
        self.assertEqual((self.root / "synthetic.json").read_bytes(), before)
        self.call("decide", choice="request-verification")
        self.assertEqual(
            sorted(p.name for p in self.root.iterdir()), ["synthetic.json"]
        )

    def test_missing_changed_and_empty_citations_never_pass(self):
        self.bind(citations=[], ok=False)
        self.bind(citations=[{"path": "absent.txt", "start": 1, "end": 1}], ok=False)
        self.bind(
            citations=[{"path": "synthetic.json", "start": 999, "end": 999}], ok=False
        )
        self.bind()
        self.rows()
        evidence = self.root / "synthetic.json"
        evidence.write_text("changed source\n")
        self.call("decide", choice="accept", ok=False)
        self.assertEqual(self.rows()["checksum"]["status"], "unverified")
        evidence.unlink()
        row = self.rows()["checksum"]
        self.assertEqual(row["status"], "unverified")
        self.assertIn("Evidence gap", row["reason"])
        self.assertTrue(row["next"])

    def test_root_escape_symlink_and_root_switch_are_refused(self):
        outside = self.home / "outside.txt"
        outside.write_text("not in the permitted case\n")
        (self.root / "link.txt").symlink_to(outside)
        for path in ("../outside.txt", str(outside), "link.txt"):
            self.call(
                "evidence", ok=False, citation={"path": path, "start": 1, "end": 1}
            )
        original = self.root
        self.root = self.home
        self.call("show", ok=False)
        self.root = original

    def test_state_inside_evidence_root_is_refused_without_writes(self):
        before = {path.name: path.read_bytes() for path in self.root.iterdir()}
        self.root.chmod(0o700)
        self.state = self.root / "session.json"
        self.call("init", goals=self.packet["goals"], ok=False)
        self.assertEqual(
            {path.name: path.read_bytes() for path in self.root.iterdir()}, before
        )

    def test_snapshot_permissions_and_private_location(self):
        self.assertEqual(self.state.stat().st_mode & 0o777, 0o600)
        self.state.chmod(0o644)
        self.call("show", ok=False)
        self.state.chmod(0o600)
        self.home.chmod(0o755)
        self.call("show", ok=False)
        self.home.chmod(0o700)
        (self.home / ".git").mkdir()
        self.call("show", ok=False)


if __name__ == "__main__":
    unittest.main()
