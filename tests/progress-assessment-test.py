#!/usr/bin/env python3
"""Synthetic assessment outcomes stay distinct from process success."""

import contextlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / "plugin/skills/behavior-diff/scripts"
sys.path.insert(0, str(SCRIPTS))
import decisions  # noqa: E402
import progress  # noqa: E402
import posttrial  # noqa: E402
from reporting.load import load_report  # noqa: E402
from reporting.render_html import render_artifact  # noqa: E402
from reporting.render_markdown import render_markdown  # noqa: E402

PURPOSE = {
    "goals": [
        {
            "text": "State the synthetic export limit in the final answer.",
            "source": "session",
            "basis": "explicit",
            "reference": "Synthetic request",
        }
    ]
}


def synthetic_run(run, names=("before-1", "before-2", "after-1", "after-2")):
    """Write a synthetic review run whose every trial has a final answer."""
    (run / "config.json").write_text(
        json.dumps({"mode": "review", "target_file": "AGENTS.md", "purpose": PURPOSE})
    )
    (run / "task.md").write_text("Synthetic task.\n")
    (run / "grades.tsv").write_text("".join(f"{name}\tREVIEW\t-\n" for name in names))
    for name in names:
        (run / name).mkdir()
        (run / name / "trace.jsonl").write_text(
            json.dumps({"type": "result", "result": f"Synthetic answer {name}."}) + "\n"
        )


def trial_record(trial_dir, *updates):
    """Write the trial record through the shipped producer, in runner order."""
    path = trial_dir / progress.TRIAL_RECORD
    progress.update(
        path, "trial", {"phase": "preparing", "state": "running"}, owner_pid=os.getpid()
    )
    for fields in updates:
        progress.update(path, "trial", fields)


FINISHED = {"phase": "finished", "state": "finished", "exit_code": 0}


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

    def test_rejected_target_stays_available_with_its_reason(self):
        synthetic_run(self.run)
        trials = {"before": ["before-1", "before-2"], "after": ["after-1", "after-2"]}
        reply = {
            "chain": [
                {
                    "decision": "Which answer shape was used?",
                    "anchor": "answer",
                    "before": [{"choice": "short", "trials": trials["before"]}],
                    "after": [{"choice": "short", "trials": trials["after"]}],
                }
            ],
            "target_assessment": {
                "criteria": [
                    {
                        "id": "limit",
                        "goal": 1,
                        "text": "States the export limit.",
                        "mode": "new",
                        "required_evidence": "The final answer wording.",
                        "evidence_kind": "output",
                        "decisions": [],
                        **{
                            side: [
                                {
                                    "trial": name,
                                    "outcome": "met",
                                    "refs": [name + ":answer"],
                                    "explanation": "The answer is readable.",
                                    "output_excerpt": "",
                                }
                                for name in names
                            ]
                            for side, names in trials.items()
                        },
                    }
                ]
            },
        }
        extraction = ("synthetic", json.dumps(reply))
        with (
            patch.object(decisions, "run_extractor", return_value=extraction),
            contextlib.redirect_stdout(io.StringIO()),
        ):
            decisions.main(self.run)
        self.assertEqual(self.outcome()["state"], "available")
        self.assertEqual(self.outcome()["reason"], "target_rejected")
        saved = json.loads((self.run / "decisions.json").read_text())
        self.assertIsNone(saved["target_rejection"])
        rejected = saved["target_assessment"]["criteria"][0]
        self.assertTrue(rejected["rejection"])
        self.assertEqual(rejected["before"], [])
        self.assertEqual(rejected["after"], [])
        self.assertTrue((self.run / "decisions.raw.txt").exists())
        report = load_report(self.run, self.run, "synthetic", self.run / "config.json")
        self.assertEqual(
            report.decisions.target_assessment.criteria[0].rejection,
            rejected["rejection"],
        )
        self.assertEqual(report.summary.state, "unavailable")
        self.assertIsNone(report.decisions.target_rejection)


class NativeTrialFailureTests(unittest.TestCase):
    """Nonempty progress or error text from a failed host CLI is not an answer."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.run = Path(self.temp.name)
        synthetic_run(self.run)

    def load(self):
        return load_report(self.run, self.run, "synthetic", self.run / "config.json")

    def assert_blocked(self, reason):
        report = self.load()
        variant = report.variants.after
        trial = variant.trials[0]
        self.assertEqual(trial.name, "after-1")
        self.assertEqual(trial.verdict, "BLOCKED")
        self.assertEqual(trial.final, "")
        self.assertEqual(trial.outcome, "Blocked — " + reason)
        self.assertEqual((variant.blocked, variant.valid, variant.total), (1, 1, 2))
        self.assertIn(reason, render_artifact(report, ""))
        self.assertIn(reason, render_markdown(report))
        prompt, completed, _ = decisions.build_prompt(self.run, include_style=False)
        self.assertEqual(completed["after"], ["after-2"])
        self.assertIn(f"(not completed: {reason})", prompt)
        self.assertNotIn("Synthetic answer after-1.", prompt)

    def test_nonzero_host_exit_blocks_each_host_record_shape(self):
        shapes = {
            # run-trial.sh records Claude's exit while the phase is still running.
            "claude": ({"phase": "running"}, {"cli_exit_code": 1}),
            # Codex, Pi and OMP record the exit as normalization starts.
            "normalized": (
                {"phase": "running"},
                {"phase": "normalizing", "cli_exit_code": 1},
            ),
        }
        for host, updates in shapes.items():
            with self.subTest(host):
                trial_record(
                    self.run / "after-1", *updates, {**FINISHED, "final_result": True}
                )
                self.assert_blocked("agent CLI exited 1")
                (self.run / "after-1" / progress.TRIAL_RECORD).unlink()

    def test_interrupted_unfinished_and_unreadable_records_block(self):
        cases = (
            ({"state": "interrupted", "exit_code": 143}, "interrupted"),
            ({"phase": "running"}, "worker ended without a final record"),
        )
        for fields, reason in cases:
            with self.subTest(reason):
                trial_record(self.run / "after-1", fields)
                self.assert_blocked(reason)
                (self.run / "after-1" / progress.TRIAL_RECORD).unlink()
        (self.run / "after-1" / progress.TRIAL_RECORD).write_text("{")
        self.assert_blocked("trial record unreadable")

    def test_completed_and_unrecorded_trials_keep_their_answers(self):
        trial_record(
            self.run / "after-1",
            {"phase": "running"},
            {"cli_exit_code": 0},
            {**FINISHED, "final_result": True},
        )
        report = self.load()
        self.assertEqual(report.variants.after.blocked, 0)
        self.assertEqual(
            [trial.final for trial in report.variants.after.trials],
            ["Synthetic answer after-1.", "Synthetic answer after-2."],
        )
        _, completed, _ = decisions.build_prompt(self.run, include_style=False)
        self.assertEqual(completed["after"], ["after-1", "after-2"])


class PosttrialPipelineTests(unittest.TestCase):
    def test_extraction_failure_still_renders_and_preserves_renderer_exit(self):
        for render_exit in (0, 9, -15):
            with (
                self.subTest(render_exit=render_exit),
                tempfile.TemporaryDirectory() as tmp,
            ):
                run = Path(tmp)
                commands = []

                def execute(command, **kwargs):
                    commands.append(command)
                    if command[0] == "jq":
                        code = 0
                    elif command[1].endswith("decisions.py"):
                        code = 7
                    else:
                        self.assertTrue(command[1].endswith("render.py"))
                        code = render_exit
                        if code == 0:
                            (run / "report.html").write_text("synthetic report")
                    return posttrial.subprocess.CompletedProcess(command, code)

                records = []
                with (
                    patch.object(posttrial.subprocess, "run", side_effect=execute),
                    patch.object(
                        posttrial,
                        "record_run",
                        side_effect=lambda _, fields: records.append(fields),
                    ),
                    contextlib.redirect_stdout(io.StringIO()),
                ):
                    code = posttrial.run_posttrial(run, 1, "trial", "codex", "extract")
                self.assertEqual(code, 143 if render_exit == -15 else render_exit)
                self.assertEqual(len(commands), 4)
                self.assertEqual(
                    commands[2][-4:], ["--agent", "codex", "--model", "extract"]
                )
                extraction = json.loads((run / "stages/extraction.json").read_text())
                rendering = json.loads((run / "stages/rendering.json").read_text())
                self.assertEqual(extraction["state"], "failed")
                self.assertEqual(
                    rendering["state"], "completed" if render_exit == 0 else "failed"
                )
                self.assertEqual(
                    records[-1]["report"]["state"],
                    "available" if render_exit == 0 else "failed",
                )
                self.assertEqual(
                    (run / "grades.tsv").read_text(),
                    "before-1\tREVIEW\t-\nafter-1\tREVIEW\t-\n",
                )

    def test_skipped_extraction_and_missing_report_keep_distinct_states(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = Path(tmp)

            def execute(command, **kwargs):
                if len(command) > 1 and command[1].endswith("decisions.py"):
                    (run / "assessment-status.json").write_text(
                        json.dumps({"state": "skipped"})
                    )
                return posttrial.subprocess.CompletedProcess(
                    command, 2 if command[0] == "jq" else 0
                )

            records = []
            with (
                patch.object(posttrial.subprocess, "run", side_effect=execute),
                patch.object(
                    posttrial,
                    "record_run",
                    side_effect=lambda _, fields: records.append(fields),
                ),
                contextlib.redirect_stdout(io.StringIO()),
            ):
                code = posttrial.run_posttrial(run, 1, "trial", "", "")
            self.assertEqual(code, 0)
            self.assertEqual(
                json.loads((run / "stages/extraction.json").read_text())["state"],
                "skipped",
            )
            self.assertEqual(
                json.loads((run / "stages/rendering.json").read_text())["state"],
                "failed",
            )
            self.assertEqual(records[-1]["report"]["state"], "failed")
            self.assertEqual(
                (run / "grades.tsv").read_text(),
                "before-1\tBLOCKED\t-\nafter-1\tBLOCKED\t-\n",
            )


if __name__ == "__main__":
    unittest.main()
