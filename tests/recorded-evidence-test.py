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
from reporting.scenario import parse_scenario  # noqa: E402
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


PURPOSE_RECORD = {
    "goals": [
        {
            "text": "Read the synthetic source pull request before drafting.",
            "source": "session",
            "basis": "explicit",
            "reference": "Synthetic request",
        }
    ]
}
PURPOSE = parse_purpose(PURPOSE_RECORD)
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

    def test_pull_request_reads_retain_returns_through_execution_adapters(self):
        for tool in ("Bash", "exec_command", "fixture__exec"):
            for text in (
                "gh pr view 7",
                "gh pr diff 7",
                "gh api repos/example/project/pulls/7",
                "gh api -X GET repos/example/project/pulls/7/files",
                "gh api -XGET --paginate repos/example/project/pulls/7/commits",
                "gh api --method=GET --jq .body repos/example/project/pulls/7",
                "gh api -H 'Accept: application/vnd.github.diff' "
                "repos/example/project/pulls/7",
                "/bin/zsh -lc 'gh api repos/example/project/pulls/7'",
            ):
                with self.subTest(tool=tool, command=text):
                    events = command("read-pr", text, "Synthetic source: cloud only.")
                    events[0]["message"]["content"][0]["name"] = tool
                    self.trace(events)
                    record = self.records()[0]
                    self.assertEqual(record["status"], "available")
                    self.assertEqual(record["text"], "Synthetic source: cloud only.")
                    self.assertEqual(record["range"]["end"], len(record["text"]))

    def test_execution_adapters_do_not_admit_mutations_or_compound_commands(self):
        for text in (
            "gh pr edit 7 --body altered",
            "gh pr merge 7",
            "gh api -X POST repos/example/project",
            "gh api -XPATCH repos/example/project/pulls/7",
            "gh api --method DELETE repos/example/project/labels/7",
            "gh api --method=get repos/example/project/pulls/7",
            "gh api repos/example/project/issues -f title=altered",
            "gh api -X GET search/issues -f q=altered",
            "gh api -F body=@notes.txt repos/example/project/issues/7/comments",
            "gh api --raw-field body=altered repos/example/project/issues",
            "gh api --input body.json repos/example/project/issues",
            "gh api -H 'X-HTTP-Method-Override: DELETE' repos/example/project",
            "gh api --verbose repos/example/project/pulls/7",
            "gh api graphql",
            "gh api",
            "gh api repos/example/project repos/example/other",
            "gh api repos/example/project -X",
            "gh pr view 7; gh pr merge 7",
            "gh pr diff 7 | cat",
            "gh pr view $(cat .env)",
        ):
            with self.subTest(command=text):
                events = command("not-read", text)
                events[0]["message"]["content"][0]["name"] = "fixture__exec"
                self.trace(events)
                record = self.records()[0]
                self.assertEqual((record["status"], record["text"]), ("omitted", ""))

    def test_pull_request_returns_keep_privacy_and_error_boundaries(self):
        for output, result_fields, status in (
            ("fictional.person@example.invalid", {}, "omitted"),
            ("permission denied", {"is_error": True}, "unavailable"),
        ):
            with self.subTest(status=status):
                events = command("read-pr", "gh pr view 7", output)
                events[0]["message"]["content"][0]["name"] = "fixture__exec"
                events[1]["message"]["content"][0].update(result_fields)
                self.trace(events)
                record = self.records()[0]
                self.assertEqual((record["status"], record["text"]), (status, ""))

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


def scenario_config(*groups):
    """Synthetic frozen run configuration binding one source-consistency check."""
    goal = {
        "text": "Report the synthetic export cap from its source.",
        "source": "session",
        "basis": "explicit",
        "reference": "Synthetic request",
    }
    check = {
        "id": "cap-agrees",
        "goal": 1,
        "text": "The reported cap agrees with the recorded source.",
        "mode": "new",
        "required_evidence": "The final answer and the recorded source return.",
        "evidence_kind": "source_consistency",
    }
    return {
        "purpose": {"goals": [goal]},
        "scenario_record": {
            "summary": "Synthetic guides surround one small source of the cap.",
            "rationale": "Long guides compete with the source for budget.",
            "conditions": ["The cap appears only in the synthetic source."],
            "limitations": [],
            "checks": [check],
            "source_requirements": [
                {"check": "cap-agrees", "any_of": list(patterns)} for patterns in groups
            ],
        },
    }


class SourceRequirementTests(unittest.TestCase):
    """Frozen source requirements reorder an unchanged budget, never widen it."""

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

    def configure(self, *groups):
        (self.root / "config.json").write_text(json.dumps(scenario_config(*groups)))

    def records(self, trial="before-1"):
        return collect_run_evidence(self.root)["trials"][trial]

    def guides(self, count):
        return sum(
            (
                call(f"g{i}", path=f"guide-{i}.md", text="g" * 9000)
                for i in range(count)
            ),
            [],
        )

    def test_more_incidental_reads_do_not_shrink_a_required_source(self):
        facts = "Export cap is 700 rows. " * 120
        source = call("source", path="src/export_limits.py", text=facts)
        for count in (4, 8, 16):
            with self.subTest(guides=count):
                self.trace(self.guides(count) + source)
                self.configure(["*src/export_limits.py*"])
                result = collect_run_evidence(self.root)
                records = result["trials"]["before-1"]
                self.assertEqual(records[-1]["text"], facts)
                self.assertEqual(records[-1]["status"], "available")
                self.assertEqual(records[-1]["id"], f"before-1:tool-{count + 1}")
                self.assertEqual(len(records), count + 1)
                self.assertLessEqual(
                    sum(len(record["text"]) for record in records), TRIAL_LIMIT
                )
                self.assertTrue(
                    all(record["text"] for record in records[:-1]),
                    "incidental reads still share the remainder",
                )
                selection = result["limits"]["selection"]
                self.assertIn("frozen source requirements", selection)
                (self.root / "config.json").unlink()
                unbound = collect_run_evidence(self.root)
                self.assertEqual(
                    [record["id"] for record in unbound["trials"]["before-1"]],
                    [record["id"] for record in records],
                )
                self.assertNotIn(
                    "frozen source requirements", unbound["limits"]["selection"]
                )
                if count == 16:
                    # Historical selection still fair-shares the same source down.
                    last = unbound["trials"]["before-1"][-1]
                    self.assertEqual(last["status"], "truncated")
                    self.assertLess(len(last["text"]), len(facts))

    def test_alias_and_groups_prioritize_every_matching_return(self):
        cap = "Export cap is 700 rows. " * 60
        joins = "Joined comparisons use preview rows. " * 40
        events = (
            self.guides(6)
            + command("api", "gh api repos/example/project/contents/limits-7", cap)
            + call("joins", path="docs/joins.md", text=joins)
        )
        self.trace(events)
        self.configure(
            ["*src/export_limits.py*", "*gh api repos/*/contents/limits-7*"],
            ["*docs/joins.md*"],
        )
        records = self.records()
        self.assertEqual((records[-2]["text"], records[-1]["text"]), (cap, joins))
        self.assertTrue(all(r["status"] == "truncated" for r in records[:-2]))
        self.assertEqual(sum(len(record["text"]) for record in records), TRIAL_LIMIT)

    def test_required_budget_exhaustion_keeps_omission_records(self):
        required = sum(
            (
                call(f"r{i}", path=f"src/limits-{i}.py", text="r" * EXCERPT_LIMIT)
                for i in range(5)
            ),
            [],
        )
        events = self.guides(2) + required
        for number in range(10):
            side = "before" if number < 5 else "after"
            self.trace(events, f"{side}-{number % 5}")
        self.configure(["*src/limits-?.py*"])
        result = collect_run_evidence(self.root)
        total = 0
        for name, records in result["trials"].items():
            with self.subTest(trial=name):
                size = sum(len(record["text"]) for record in records)
                self.assertLessEqual(size, TRIAL_LIMIT)
                total += size
                for record in records[:2]:
                    self.assertEqual(record["text"], "")
                    self.assertEqual(record["status"], "omitted")
                    self.assertEqual(record["range"]["end"], 0)
                    self.assertEqual(
                        record["reason"], "assessment content budget exhausted"
                    )
                for record in records[2:]:
                    self.assertEqual(record["status"], "truncated")
                    self.assertEqual(record["range"]["end"], len(record["text"]))
                    self.assertTrue(record["text"])
        self.assertLessEqual(total, RUN_LIMIT)
        self.assertEqual(result, collect_run_evidence(self.root))

    def test_required_matches_keep_privacy_error_and_descriptor_rules(self):
        facts = "Export cap is 700 rows. " * 120
        long = call("long", path="src/export_limits.py", text=facts)
        # The matching path stays visible; only a later argument is cut off.
        long[0]["message"]["content"][0]["input"]["window"] = "w" * 250
        events = (
            self.guides(8)
            + call("email", path="src/export_limits.py", text="a@example.invalid")
            + call("error", path="src/export_limits.py", is_error=True)
            + call("secret", path="secrets/export_limits.py")
            + long
        )
        self.trace(events)
        self.configure(["*export_limits.py*"])
        email, error, secret, long = self.records()[-4:]
        self.assertEqual((email["status"], email["text"]), ("omitted", ""))
        self.assertEqual((error["status"], error["text"]), ("unavailable", ""))
        self.assertEqual(secret["source"], "[sensitive source omitted]")
        self.assertEqual((secret["status"], secret["text"]), ("omitted", ""))
        # A truncated descriptor is not a trustworthy identity, so no priority.
        self.assertIn("src/export_limits.py", long["source"])
        self.assertTrue(long["source"].endswith("[descriptor truncated]"))
        self.assertEqual(long["status"], "truncated")
        self.assertEqual(long["reason"], "fair-share assessment truncation")
        self.assertLess(len(long["text"]), len(facts))

    def test_required_patterns_never_admit_mutating_or_ineligible_returns(self):
        self.trace(
            command("post", "gh api -X POST repos/example/project/limits-7")
            + command("edit", "gh pr edit 7 --body limits-7")
        )
        self.configure(["*limits-7*"])
        for record in self.records():
            self.assertEqual((record["status"], record["text"]), ("omitted", ""))
            self.assertEqual(record["reason"], "not an eligible recorded read")

    def test_invalid_frozen_scenario_fails_closed(self):
        self.trace(call("read-1"))
        config = scenario_config(["*"])
        (self.root / "config.json").write_text(json.dumps(config))
        with self.assertRaises(ValueError):
            collect_run_evidence(self.root)
        del config["scenario_record"]["source_requirements"]
        (self.root / "config.json").write_text(json.dumps(config))
        with self.assertRaises(ValueError):
            collect_run_evidence(self.root)
        config["scenario_record"] = None
        (self.root / "config.json").write_text(json.dumps(config))
        self.assertEqual(self.records()[0]["status"], "available")


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

    def check(self, raw, scenario=None):
        evidence = evidence_records(collect_run_evidence(self.root))
        return check_target(raw, PURPOSE, ANSWERS, evidence, scenario=scenario)

    def rejected(self, raw, scenario=None):
        """Return one criterion's own rejection; the target itself must survive."""
        target, rejection = self.check(raw, scenario)
        self.assertIsNone(rejection)
        (assessed,) = target.criteria
        self.assertEqual(assessed.decisions, ())
        self.assertEqual((assessed.before, assessed.after), ((), ()))
        return assessed.rejection

    def test_recorded_call_proves_action_despite_omitted_return(self):
        self.recorded(
            command("view-1", "gh pr view 7", "fictional.person@example.invalid")
        )
        record = collect_run_evidence(self.root)["trials"]["after-1"][0]
        self.assertEqual((record["status"], record["text"]), ("omitted", ""))
        target, rejection = self.check(criterion())
        self.assertIsNone(rejection)
        self.assertEqual(target.criteria[0].after[0].outcome, "met")
        self.assertEqual(target.criteria[0].before[0].outcome, "not_met")

    def test_call_without_returned_content_cannot_prove_source_agreement(self):
        self.recorded(command("view-1", "gh pr view 7")[:1])
        raw = criterion(
            "source_consistency",
            excerpt="citing pull request 7",
            before_outcome="unassessable",
        )
        self.assertEqual(
            self.rejected(raw), "criterion lacks required source or output evidence"
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
                    self.rejected(criterion(ref=ref)),
                    "determinate target outcome needs available evidence",
                )
                uncertain = criterion(
                    after_outcome="uncertain", ref=ref, before_outcome="uncertain"
                )
                target, rejection = self.check(uncertain)
                self.assertIsNone(rejection)
                self.assertIsNone(target.criteria[0].rejection)

    def test_output_outcome_needs_its_excerpt(self):
        self.recorded(command("view-1", "gh pr view 7"))
        raw = criterion("output", before_outcome="unassessable")
        self.assertEqual(
            self.rejected(raw), "output assessment needs its relevant exact excerpt"
        )
        excerpt = "citing pull request 7"
        raw["criteria"][0]["after"][0]["output_excerpt"] = excerpt
        target, rejection = self.check(raw)
        self.assertIsNone(rejection)
        self.assertEqual(target.criteria[0].after[0].output_excerpt, excerpt)

    def test_source_consistency_needs_every_frozen_source_group(self):
        check = {
            key: value
            for key, value in criterion("source_consistency")["criteria"][0].items()
            if key not in ("decisions", "before", "after")
        }
        record = {
            "summary": "One synthetic pull request and one facts file.",
            "rationale": "Agreement needs both the pull request and the facts file.",
            "conditions": ["The draft must agree with both synthetic sources."],
            "limitations": [],
            "checks": [check],
            "source_requirements": [
                {
                    "check": "source-read",
                    "any_of": ["*gh pr view 7*", "*pulls/7/files*"],
                },
                {"check": "source-read", "any_of": ["*facts.txt*"]},
            ],
        }
        (self.root / "config.json").write_text(
            json.dumps({"purpose": PURPOSE_RECORD, "scenario_record": record})
        )
        scenario = parse_scenario(record, PURPOSE)
        self.recorded(
            command("view-1", "gh pr view 7")
            + call("facts", text="Recorded cap: 500.")
            + command("other", "gh pr view 8")
        )
        excerpt = "citing pull request 7"
        cases = (
            (["after-1:tool-1", "after-1:tool-2"], None),
            (["after-1:tool-1"], "criterion lacks a required frozen source"),
            (["after-1:tool-2"], "criterion lacks a required frozen source"),
            (
                ["after-1:tool-3", "after-1:tool-2"],
                "criterion lacks a required frozen source",
            ),
        )
        for refs, expected in cases:
            with self.subTest(refs=refs):
                raw = criterion(
                    "source_consistency",
                    excerpt=excerpt,
                    before_outcome="unassessable",
                )
                raw["criteria"][0]["after"][0]["refs"] = refs + ["after-1:answer"]
                if expected:
                    self.assertEqual(self.rejected(raw, scenario), expected)
                    continue
                target, rejection = self.check(raw, scenario)
                self.assertIsNone(rejection)
                self.assertIsNone(target.criteria[0].rejection)
                self.assertEqual(target.criteria[0].after[0].outcome, "met")


if __name__ == "__main__":
    unittest.main()
