#!/usr/bin/env python3
"""Synthetic source-return boundaries; no model or source retrieval."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / "plugin/skills/behavior-diff/scripts"
sys.path.insert(0, str(SCRIPTS))
from reporting.evidence import (  # noqa: E402
    EXCERPT_LIMIT,
    RECORD_LIMIT,
    RUN_LIMIT,
    TRIAL_LIMIT,
    collect_run_evidence,
)
from reporting.target import check_target, evidence_records, parse_purpose  # noqa: E402


def call(identity, path="facts.txt", text="Recorded cap: 500.", **result_fields):
    return [
        {
            "type": "assistant",
            "message": {
                "content": [
                    {
                        "type": "tool_use",
                        "id": identity,
                        "name": "Read",
                        "input": {"file_path": path, "offset": 20, "limit": 10},
                    }
                ]
            },
        },
        {
            "type": "user",
            "message": {
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": identity,
                        "content": text,
                        **result_fields,
                    }
                ]
            },
        },
    ]


def command(identity, text, output="Synthetic pull request body."):
    events = call(identity, text=output)
    events[0]["message"]["content"][0].update(name="Bash", input={"command": text})
    return events


PURPOSE = parse_purpose(
    {
        "goals": [
            {
                "text": "Read the synthetic source pull request before drafting.",
                "source": "session",
                "basis": "explicit",
                "reference": "Synthetic request",
            }
        ]
    }
)
ANSWERS = {
    "before": {"before-1": "Synthetic draft without a source."},
    "after": {"after-1": "Synthetic draft citing pull request 7."},
}


def criterion(
    kind="recorded_action",
    after_outcome="met",
    excerpt="",
    ref="after-1:tool-1",
    before_outcome="not_met",
):
    refs = [ref] if kind == "recorded_action" else [ref, "after-1:answer"]
    return {
        "criteria": [
            {
                "id": "source-read",
                "goal": 1,
                "text": "Reads the synthetic source pull request.",
                "mode": "new",
                "required_evidence": "A recorded pull request view.",
                "evidence_kind": kind,
                "decisions": [],
                "before": [
                    {
                        "trial": "before-1",
                        "outcome": before_outcome,
                        "refs": ["before-1:tool-1"],
                        "explanation": "Only a local file read is recorded.",
                        "output_excerpt": "",
                    }
                ],
                "after": [
                    {
                        "trial": "after-1",
                        "outcome": after_outcome,
                        "refs": refs,
                        "explanation": "The recorded call views the pull request.",
                        "output_excerpt": excerpt,
                    }
                ],
            }
        ]
    }


class RecordedEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def trace(self, events, trial="before-1"):
        directory = self.root / trial
        directory.mkdir(exist_ok=True)
        (directory / "trace.jsonl").write_text(
            "".join(json.dumps(x) + "\n" for x in events)
        )

    def records(self, trial="before-1"):
        return collect_run_evidence(self.root)["trials"][trial]

    def test_recorded_content_not_current_file_with_returned_range(self):
        (self.root / "facts.txt").write_text("Current cap: 9000.")
        self.trace(call("read-1"))
        record = self.records()[0]
        self.assertEqual(record["id"], "before-1:tool-1")
        self.assertEqual(record["text"], "Recorded cap: 500.")
        self.assertEqual(record["range"], {"start": 0, "end": 18, "unit": "characters"})
        self.assertIn('"offset": 20', record["source"])
        self.assertEqual(record["status"], "available")

    def test_missing_return_and_self_report_are_not_proof(self):
        self.trace(call("read-1")[:1])
        self.assertEqual(self.records()[0]["status"], "unavailable")
        self.trace(call("read-1"))
        (self.root / "config.json").write_text('{"trace_source":"self-reported"}')
        self.assertEqual(self.records()[0]["status"], "omitted")
        self.assertEqual(self.records()[0]["text"], "")

    def test_sensitive_sources_and_late_sensitive_content_are_omitted(self):
        for path, text in [
            (".env", "anything"),
            ("settings/secrets.fish", "anything"),
            ("facts.txt", "x" * (EXCERPT_LIMIT + 1) + " password=fictional-value"),
            ("facts.txt", "fictional.person@example.invalid"),
        ]:
            with self.subTest(path=path):
                self.trace(call("read-1", path, text))
                record = self.records()[0]
                self.assertEqual(record["status"], "omitted")
                self.assertEqual(record["text"], "")
                self.assertNotIn("secrets.fish", record["source"])

    def test_quoted_credential_keys_omit_whole_returns_and_sources(self):
        for key in ("api_key", "access-token", "password", "passwd", "client secret"):
            for quote in ('"', "'"):
                sensitive = f"{{{quote}{key}{quote}: {quote}fictional-value{quote}}}"
                for prefix in ("", "x" * (EXCERPT_LIMIT + 1)):
                    with self.subTest(key=key, quote=quote, late=bool(prefix)):
                        self.trace(call("read-1", text=prefix + sensitive))
                        record = self.records()[0]
                        self.assertEqual(record["status"], "omitted")
                        self.assertEqual(record["text"], "")
                        self.assertEqual(record["range"]["end"], 0)
                        self.assertEqual(
                            record["reason"], "potentially sensitive returned content"
                        )
                events = call("read-1")
                events[0]["message"]["content"][0]["input"][key] = "fictional-value"
                self.trace(events)
                record = self.records()[0]
                self.assertEqual(record["status"], "omitted")
                self.assertEqual(record["source"], "[sensitive source omitted]")
                self.assertEqual(record["text"], "")
                events = call("read-1", path=sensitive)
                self.trace(events)
                record = self.records()[0]
                self.assertEqual(record["status"], "omitted")
                self.assertEqual(record["source"], "[sensitive source omitted]")
                self.assertEqual(record["text"], "")

    def test_git_revision_paths_keep_sensitive_sources_excluded(self):
        for path in (".env", "secrets.fish", "credentials.json", "facts.txt"):
            command = f"git show HEAD:{path}"
            for wrapped in (command, f"/bin/sh -lc '{command}'"):
                with self.subTest(path=path, command=wrapped):
                    events = call("git-read", text="opaque fictional source content")
                    part = events[0]["message"]["content"][0]
                    part["name"] = "Bash"
                    part["input"] = {"command": wrapped}
                    self.trace(events)
                    record = self.records()[0]
                    if path == "facts.txt":
                        self.assertEqual(record["status"], "available")
                        self.assertEqual(
                            record["text"], "opaque fictional source content"
                        )
                    else:
                        self.assertEqual(record["status"], "omitted")
                        self.assertEqual(record["source"], "[sensitive source omitted]")
                        self.assertEqual(record["text"], "")

    def test_excerpt_trial_and_run_limits_keep_omission_records(self):
        events = sum(
            (call(str(i), text="z" * (EXCERPT_LIMIT + 5)) for i in range(6)), []
        )
        for number in range(10):
            side = "before" if number < 5 else "after"
            self.trace(events, f"{side}-{number % 5}")
        result = collect_run_evidence(self.root)
        total = 0
        for records in result["trials"].values():
            size = sum(len(r["text"]) for r in records)
            self.assertLessEqual(size, TRIAL_LIMIT)
            total += size
            for record in records:
                self.assertLessEqual(len(record["text"]), EXCERPT_LIMIT)
                self.assertEqual(record["range"]["end"], len(record["text"]))
        self.assertEqual(total, RUN_LIMIT)
        for records in result["trials"].values():
            self.assertTrue(all(record["text"] for record in records))
            self.assertTrue(all(record["status"] == "truncated" for record in records))
        self.assertEqual(result, collect_run_evidence(self.root))

    def test_late_source_return_survives_long_earlier_guides(self):
        facts = "Export cap is 700 rows; joined comparisons use preview rows."
        events = sum(
            (call(str(i), path=f"guide-{i}.md", text="g" * 9000) for i in range(8)),
            [],
        )
        self.trace(events + call("source", path="implementation.py", text=facts))
        records = self.records()
        self.assertEqual(records[-1]["text"], facts)
        self.assertEqual(records[-1]["status"], "available")
        self.assertLessEqual(
            sum(len(record["text"]) for record in records), TRIAL_LIMIT
        )

    def test_tool_errors_duplicates_nontext_and_record_overflow(self):
        self.trace(call("one", is_error=True))
        self.assertEqual(self.records()[0]["status"], "unavailable")
        events = call("one")
        self.trace(events + events[1:])
        self.assertEqual(self.records()[0]["text"], "")
        self.assertEqual(self.records()[0]["status"], "unavailable")
        self.trace(events + events)
        for record in self.records():
            self.assertEqual(record["status"], "unavailable")
            self.assertEqual(record["range"]["end"], 0)
            self.assertEqual(record["text"], "")
        self.trace(
            call(
                "one",
                text=[
                    {"type": "text", "text": "Recorded cap: 500."},
                    {"type": "image", "data": "synthetic"},
                ],
            )
        )
        self.assertEqual(self.records()[0]["status"], "truncated")
        self.assertEqual(self.records()[0]["reason"], "non-text content omitted")
        self.trace(call("one", text=[{"type": "image", "data": "synthetic"}]))
        self.assertEqual(self.records()[0]["status"], "unavailable")
        self.trace(sum((call(str(i)) for i in range(RECORD_LIMIT + 2)), []))
        self.assertEqual(len(self.records()), RECORD_LIMIT + 1)
        self.assertEqual(self.records()[-1]["id"], "before-1:overflow")
        self.assertEqual(self.records()[-1]["status"], "omitted")

    def test_codex_runner_wrappers_retain_only_simple_recorded_reads(self):
        stub = self.root / "bin"
        stub.mkdir()
        binary = stub / "codex"
        commands = [
            ("cat facts.txt", True),
            ("/bin/zsh -lc 'cat facts.txt'", True),
            ("/bin/bash -lc 'cat \"facts with spaces.txt\"'", True),
            ("/bin/sh -lc 'git show HEAD:facts.txt'", True),
            ("/bin/zsh -lc 'cat facts.txt; printf extra'", False),
            ("/bin/zsh -lc 'cat facts.txt | wc -l'", False),
            ("/bin/zsh -lc 'cat facts.txt > copy.txt'", False),
            ("/bin/zsh -lc 'cat $(printf facts.txt)'", False),
            ("/bin/zsh -lc 'cat `printf facts.txt`'", False),
            ("/bin/zsh -lc 'printf synthetic'", False),
            ("/bin/zsh -lc 'bash other.sh'", False),
            ("/bin/zsh -lc 'cat facts.txt' extra", False),
            ("/usr/bin/unknown -lc 'cat facts.txt'", False),
        ]
        binary.write_text(
            "#!/bin/sh\ncat <<'JSON'\n"
            + "\n".join(
                json.dumps(
                    {
                        "type": "item.completed",
                        "item": {
                            "id": f"cmd-{number}",
                            "type": "command_execution",
                            "command": command,
                            "aggregated_output": f"Synthetic recorded cap: {number}.",
                            "exit_code": 0,
                        },
                    }
                )
                for number, (command, _) in enumerate(commands)
            )
            + "\nJSON\n"
        )
        binary.chmod(0o700)
        trial = self.root / "before-1"
        trial.mkdir()
        task = self.root / "task.md"
        task.write_text("Read the synthetic facts.")
        subprocess.run(
            [
                "bash",
                str(SCRIPTS / "run-trial.sh"),
                "--agent",
                "codex",
                "--model",
                "synthetic-model",
                "--dir",
                str(trial),
                "--task-file",
                str(task),
            ],
            check=True,
            capture_output=True,
            env={**os.environ, "PATH": str(stub) + os.pathsep + os.environ["PATH"]},
        )
        records = self.records()
        self.assertEqual(len(records), len(commands))
        for number, ((command, eligible), record) in enumerate(zip(commands, records)):
            with self.subTest(command=command):
                if eligible:
                    self.assertEqual(
                        record["text"], f"Synthetic recorded cap: {number}."
                    )
                    self.assertEqual(record["status"], "available")
                else:
                    self.assertEqual(record["text"], "")
                    self.assertEqual(record["status"], "omitted")
                    self.assertEqual(record["reason"], "not an eligible recorded read")
                self.assertIn(json.dumps(command), record["source"])


class TargetEvidenceTests(unittest.TestCase):
    """A captured call proves that the call ran, never what it returned."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def recorded(self, after_events):
        for trial, events in (("before-1", call("read-1")), ("after-1", after_events)):
            directory = self.root / trial
            directory.mkdir(exist_ok=True)
            trace = directory / "trace.jsonl"
            trace.unlink(missing_ok=True)
            if events is not None:
                trace.write_text("".join(json.dumps(x) + "\n" for x in events))

    def check(self, raw):
        evidence = evidence_records(collect_run_evidence(self.root))
        return check_target(raw, PURPOSE, ANSWERS, evidence)

    def test_recorded_call_proves_action_despite_omitted_return(self):
        self.recorded(command("view-1", "gh pr view 7"))
        record = collect_run_evidence(self.root)["trials"]["after-1"][0]
        self.assertEqual((record["status"], record["text"]), ("omitted", ""))
        target, rejection = self.check(criterion())
        self.assertIsNone(rejection)
        self.assertEqual(target.criteria[0].after[0].outcome, "met")
        self.assertEqual(target.criteria[0].before[0].outcome, "not_met")

    def test_call_without_returned_content_cannot_prove_source_agreement(self):
        self.recorded(command("view-1", "gh pr view 7"))
        raw = criterion(
            "source_consistency",
            excerpt="citing pull request 7",
            before_outcome="unassessable",
        )
        self.assertEqual(
            self.check(raw),
            (None, "criterion lacks required source or output evidence"),
        )
        raw["criteria"][0]["after"][0]["outcome"] = "unassessable"
        target, rejection = self.check(raw)
        self.assertIsNone(rejection)
        self.assertEqual(target.criteria[0].after[0].outcome, "unassessable")

    def test_unproven_calls_cannot_support_determinate_outcomes(self):
        cases = (
            ("sensitive source", command("view-1", "cat .env"), "after-1:tool-1"),
            (
                "duplicate call identity",
                command("dup", "gh pr view 7") + command("dup", "gh pr view 7"),
                "after-1:tool-1",
            ),
            ("missing recording", None, "after-1:trace"),
            ("self-reported action", command("view-1", "gh pr view 7"), None),
        )
        for label, events, ref in cases:
            with self.subTest(label):
                self.recorded(events)
                if ref is None:
                    ref = "after-1:tool-1"
                    (self.root / "config.json").write_text(
                        '{"trace_source":"self-reported"}'
                    )
                self.assertEqual(
                    self.check(criterion(ref=ref)),
                    (None, "determinate target outcome needs available evidence"),
                )
                uncertain = criterion(
                    after_outcome="uncertain", ref=ref, before_outcome="uncertain"
                )
                self.assertIsNone(self.check(uncertain)[1])

    def test_output_outcome_needs_its_excerpt(self):
        self.recorded(command("view-1", "gh pr view 7"))
        raw = criterion("output", before_outcome="unassessable")
        self.assertEqual(
            self.check(raw),
            (None, "output assessment needs its relevant exact excerpt"),
        )
        excerpt = "citing pull request 7"
        raw["criteria"][0]["after"][0]["output_excerpt"] = excerpt
        target, rejection = self.check(raw)
        self.assertIsNone(rejection)
        self.assertEqual(target.criteria[0].after[0].output_excerpt, excerpt)


if __name__ == "__main__":
    unittest.main()
