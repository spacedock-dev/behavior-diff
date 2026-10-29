#!/usr/bin/env python3
"""Synthetic, model-free native boundary contract tests."""

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import sys
from unittest.mock import patch
import subprocess

SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "plugin/skills/behavior-diff/scripts/native_context.py"
)
sys.path.insert(0, str(SCRIPT.parent))
from reporting.context_boundary import boundary_exclusion
from reporting.load import trial_interruption, _trial
from reporting.evidence import collect_run_evidence
from decisions import trials_of


class NativeContextTests(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.spec_from_file_location("native_context", SCRIPT)
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)

    def test_explicit_scope_and_absolute_paths(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "requirements.json"
            path.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "scope": "codex-local-filesystem",
                        "deny_read": ["relative"],
                    }
                )
            )
            with self.assertRaises(ValueError):
                self.module.load_requirements(path)

    def test_native_profile_never_uses_legacy_sandbox(self):
        with tempfile.TemporaryDirectory() as root:
            workspace = Path(root) / "workspace"
            workspace.mkdir()
            forbidden = Path(root) / "historical-memory"
            forbidden.mkdir()
            args = self.module.policy_args(workspace, [str(forbidden)])
            joined = " ".join(args)
            self.assertNotIn("--sandbox", args)
            self.assertNotIn("danger-full-access", joined)
            self.assertIn('default_permissions="behavior-diff-context"', args)
            self.assertIn('"deny"', joined)
            self.assertIn("enabled=false", joined)

    def test_observed_attempt_is_not_clean(self):
        with tempfile.TemporaryDirectory() as root:
            trace = Path(root) / "trace.jsonl"
            trace.write_text(
                json.dumps(
                    {
                        "type": "assistant",
                        "message": {
                            "content": [
                                {
                                    "type": "tool_use",
                                    "input": {
                                        "command": "cat /synthetic/forbidden/memory"
                                    },
                                }
                            ]
                        },
                    }
                )
                + "\n"
            )
            result = self.module.observe(trace, ["/synthetic/forbidden"])
            self.assertEqual(result["status"], "violation")
            self.assertNotIn("memory", json.dumps(result))

    def test_no_observation_is_not_clean_proof(self):
        with tempfile.TemporaryDirectory() as root:
            trace = Path(root) / "trace.jsonl"
            trace.write_text("")
            result = self.module.observe(trace, ["/synthetic/forbidden"])
            self.assertEqual(result["observation"], "not_observed")
            self.assertFalse(result["clean_context_proven"])

    def test_required_missing_marker_excluded_everywhere(self):
        with tempfile.TemporaryDirectory() as root:
            run = Path(root)
            (run / "config.json").write_text(
                json.dumps({"context_boundary_required": True})
            )
            trial = run / "before-1"
            trial.mkdir()
            (trial / "trace.jsonl").write_text(
                json.dumps({"type": "result", "result": "synthetic private result"})
                + "\n"
            )
            (run / "grades.tsv").write_text("before-1\tPASS\t-\n")
            self.assertIsNotNone(boundary_exclusion(trial))
            self.assertEqual(trial_interruption(trial), boundary_exclusion(trial))
            self.assertFalse(trials_of(run, finished_only=True))
            self.assertEqual(collect_run_evidence(run)["trials"]["before-1"], [])

    def test_violation_keeps_raw_evidence_out_of_assessment(self):
        with tempfile.TemporaryDirectory() as root:
            run = Path(root)
            trial = run / "after-1"
            trial.mkdir()
            (trial / "context-boundary.json").write_text(
                json.dumps({"version": 1, "status": "violation"})
            )
            (trial / "trace.jsonl").write_text(
                json.dumps({"type": "result", "result": "synthetic private result"})
                + "\n"
            )
            (run / "grades.tsv").write_text("after-1\tPASS\t-\n")
            self.assertFalse(trials_of(run, finished_only=True))
            all_trials = trials_of(run, finished_only=False)
            self.assertNotIn("synthetic private result", json.dumps(all_trials))
            self.assertEqual(collect_run_evidence(run)["trials"]["after-1"], [])
            report_trial = _trial(
                run, "after-1", ("PASS", "synthetic private action"), None
            )
            self.assertEqual(report_trial.verdict, "BLOCKED")
            self.assertEqual(report_trial.commands, ())
            self.assertEqual(report_trial.final, "")
            self.assertNotIn("synthetic private", report_trial.outcome)

    def test_prepared_trial_is_excluded_until_observation_finishes(self):
        with tempfile.TemporaryDirectory() as root:
            run = Path(root).resolve()
            trial = run / "before-1"
            project = trial / "project"
            project.mkdir(parents=True)
            requirements = run / "requirements.json"
            requirements.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "scope": "codex-local-filesystem",
                        "deny_read": [str(run / "historical-memory")],
                    }
                )
            )
            (run / "config.json").write_text(
                json.dumps(
                    {
                        "context_boundary_required": True,
                    }
                )
            )
            argv = [
                "native_context.py",
                "prepare",
                "--requirements",
                str(requirements),
                "--workspace",
                str(project),
                "--output",
                str(trial / "context-boundary.json"),
            ]
            with (
                patch.object(sys, "argv", argv),
                patch.object(self.module, "check_route"),
                patch.object(self.module, "preflight", return_value=[]),
            ):
                self.assertEqual(self.module.main(), 0)
            # A worker may leave partial evidence before normalization fails.
            (trial / "trace.jsonl").write_text(
                json.dumps(
                    {
                        "type": "result",
                        "result": "synthetic private result",
                    }
                )
                + "\n"
            )
            (run / "grades.tsv").write_text("before-1\tPASS\t-\n")
            self.assertIsNotNone(boundary_exclusion(trial))
            self.assertFalse(trials_of(run, finished_only=True))
            self.assertNotIn(
                "synthetic private result",
                json.dumps(trials_of(run, finished_only=False)),
            )
            self.assertEqual(collect_run_evidence(run)["trials"]["before-1"], [])

    def test_unsupported_host_fails_before_native_invocation(self):
        with (
            tempfile.TemporaryDirectory() as root,
            patch.object(self.module.subprocess, "run") as native,
        ):
            with self.assertRaises(ValueError):
                self.module.check_route("claude", Path(root))
            native.assert_not_called()

    def test_runner_rejects_required_unsupported_route_before_agent(self):
        with tempfile.TemporaryDirectory() as root:
            work = Path(root).resolve()
            (work / "SKILL.md").write_text("synthetic instruction")
            requirements = work / "requirements.json"
            requirements.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "scope": "codex-local-filesystem",
                        "deny_read": [str(work / "historical-memory")],
                    }
                )
            )
            result = subprocess.run(
                [
                    "bash",
                    str(SCRIPT.parent / "behavior-diff.sh"),
                    "--file",
                    "SKILL.md",
                    "--task",
                    "synthetic task",
                    "--agent",
                    "claude",
                    "--context-requirements-file",
                    str(requirements),
                ],
                cwd=work,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("native context boundary unavailable", result.stderr)
            self.assertNotIn("starting", result.stdout)

    def test_corrupt_config_excludes_missing_marker_evidence(self):
        for raw in (
            '{"context_boundary_required":',
            "[]",
            '{"context_boundary_required":"false"}',
        ):
            with self.subTest(raw=raw), tempfile.TemporaryDirectory() as root:
                run = Path(root)
                trial = run / "before-1"
                trial.mkdir()
                (run / "config.json").write_text(raw)
                (trial / "trace.jsonl").write_text(
                    json.dumps({"type": "result", "result": "synthetic private result"})
                    + "\n"
                )
                (run / "grades.tsv").write_text("before-1\tPASS\t-\n")
                self.assertIsNotNone(boundary_exclusion(trial))
                self.assertFalse(trials_of(run))
                self.assertEqual(collect_run_evidence(run)["trials"]["before-1"], [])
                report_trial = _trial(run, "before-1", ("PASS", "-"), None)
                self.assertEqual(report_trial.verdict, "BLOCKED")

    def test_missing_legacy_config_does_not_claim_boundary(self):
        with tempfile.TemporaryDirectory() as root:
            trial = Path(root) / "before-1"
            trial.mkdir()
            self.assertIsNone(boundary_exclusion(trial))

    def test_requirements_duplicate_keys_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "requirements.json"
            path.write_text(
                '{"version":1,"version":1,"scope":"codex-local-filesystem","deny_read":["/synthetic/history"]}'
            )
            with self.assertRaises(ValueError):
                self.module.load_requirements(path)


if __name__ == "__main__":
    unittest.main()
