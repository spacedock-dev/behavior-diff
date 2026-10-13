#!/usr/bin/env python3
"""Synthetic assessment outcomes stay distinct from process success."""

import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / "plugin/skills/behavior-diff/scripts"
sys.path.insert(0, str(SCRIPTS))
import decisions  # noqa: E402


class AssessmentProgressTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.run = Path(self.temp.name)

    def outcome(self):
        return json.loads((self.run / "assessment-status.json").read_text())

    def test_insufficient_trials_are_skipped_not_successful(self):
        with patch.object(decisions, "build_prompt", return_value=(None, {}, "")):
            decisions.main(self.run)
        self.assertEqual(self.outcome()["state"], "skipped")
        self.assertEqual(self.outcome()["reason"], "insufficient_trials")

    def test_failed_extractor_is_not_assessment_success(self):
        with (
            patch.object(decisions, "build_prompt", return_value=("synthetic", {}, "")),
            patch.object(decisions, "run_extractor", return_value=("none", None)),
        ):
            decisions.main(self.run)
        self.assertEqual(self.outcome()["state"], "failed")
        self.assertEqual(self.outcome()["reason"], "extractor_failed")

    def test_invalid_output_does_not_become_available(self):
        with (
            patch.object(decisions, "build_prompt", return_value=("synthetic", {}, "")),
            patch.object(
                decisions, "run_extractor", return_value=("synthetic", "not JSON")
            ),
        ):
            decisions.main(self.run)
        self.assertEqual(self.outcome()["state"], "failed")
        self.assertEqual(self.outcome()["reason"], "unusable_output")
        self.assertFalse((self.run / "decisions.json").exists())

    def test_unexpected_failure_preserves_exception_and_safe_reason(self):
        with patch.object(
            decisions, "build_prompt", side_effect=ValueError("private text")
        ):
            with self.assertRaisesRegex(ValueError, "private text"):
                decisions.main(self.run)
        self.assertEqual(self.outcome()["state"], "failed")
        self.assertEqual(self.outcome()["reason"], "unexpected_error")
        self.assertNotIn(
            "private text", (self.run / "assessment-status.json").read_text()
        )


if __name__ == "__main__":
    unittest.main()
