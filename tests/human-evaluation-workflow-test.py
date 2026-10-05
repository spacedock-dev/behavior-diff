#!/usr/bin/env python3
"""Synthetic lifecycle contracts: no network, no credentials, no model inference."""

import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import random
import subprocess
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = (
    Path(__file__).resolve().parents[1]
    / ".agents/skills/run-behavior-diff-human-evaluation/scripts/evaluate.py"
)
SPEC = importlib.util.spec_from_file_location("human_evaluation_workflow", SCRIPT)
workflow = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(workflow)
REAL_RUN = subprocess.run


def command(repo, *arguments):
    result = REAL_RUN(
        ["git", "-C", str(repo), *arguments],
        capture_output=True,
        env=workflow.git_environment(),
    )
    if result.returncode:
        raise AssertionError(result.stderr.decode())
    return result.stdout.decode().strip()


def repository(path):
    path.mkdir()
    command(path, "init", "-q", "-b", "main")
    command(path, "config", "user.name", "synthetic-test")
    command(path, "config", "user.email", "synthetic@example.invalid")


def commit(repo, message):
    command(repo, "add", "-A")
    command(repo, "commit", "-qm", message)
    return command(repo, "rev-parse", "HEAD")


def synthetic_history(root):
    repo = root / "source"
    repository(repo)
    skill = repo / "skills/example/SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_bytes(b"Rule zero.\n")
    (repo / "README.txt").write_text("Synthetic repository.\n")
    commit(repo, "root")
    eligible = []
    for index in range(10):
        skill.write_bytes("Rule version {}.\n".format(index).encode())
        if index == 3:
            (repo / "README.txt").write_text("Outside-skill change is allowed.\n")
        eligible.append(commit(repo, "eligible {}".format(index)))
    skill.write_bytes(b"Rule  version  9.  \n\n")
    whitespace = commit(repo, "whitespace only")
    skill.write_bytes(b"Rule with a companion.\n")
    (skill.parent / "helper.txt").write_text("Companion changed.\n")
    companion = commit(repo, "companion change")
    other = repo / "skills/other/SKILL.md"
    other.parent.mkdir()
    other.write_bytes(b"Other rule.\n")
    added = commit(repo, "new skill is ineligible")
    skill.write_bytes(b"Two skills changed.\n")
    other.write_bytes(b"Other changed too.\n")
    multiple = commit(repo, "multiple skills")
    skill.unlink()
    skill.symlink_to("helper.txt")
    symlink = commit(repo, "symlink skill is ineligible")
    skill.unlink()
    skill.write_bytes(b"Restored regular file.\n")
    commit(repo, "nonregular before is ineligible")
    command(repo, "checkout", "-qb", "topic")
    skill.write_bytes(b"Topic rule.\n")
    eligible.append(commit(repo, "reachable topic candidate"))
    command(repo, "checkout", "-q", "main")
    (repo / "README.txt").write_text("Main unrelated change.\n")
    commit(repo, "no skill change")
    command(repo, "merge", "--no-ff", "-qm", "merge topic", "topic")
    tip = command(repo, "rev-parse", "HEAD")
    command(repo, "checkout", "-qb", "not-reachable")
    skill.write_bytes(b"Unreachable candidate must never be sampled.\n")
    unreachable = commit(repo, "unreachable")
    command(repo, "checkout", "-q", "main")
    return (
        repo,
        tip,
        set(eligible),
        {
            "whitespace": whitespace,
            "companion": companion,
            "added": added,
            "multiple": multiple,
            "symlink": symlink,
            "unreachable": unreachable,
        },
    )


class WorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.history_temp = tempfile.TemporaryDirectory(prefix="human-eval-history-")
        cls.history_root = Path(cls.history_temp.name).resolve()
        cls.source, cls.tip, cls.eligible, cls.special = synthetic_history(
            cls.history_root
        )

    @classmethod
    def tearDownClass(cls):
        cls.history_temp.cleanup()

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="human-eval-workflow-")
        self.root = Path(self.temporary.name).resolve()
        self.code = self.root / "code"
        repository(self.code)
        css = self.code / "plugin/skills/behavior-diff/scripts/reporting/report.css"
        css.parent.mkdir(parents=True)
        css.write_text("body { color: black; }\n")
        runner = css.parents[1] / "behavior-diff.sh"
        runner.write_text("#!/bin/sh\nexit 99\n")
        self.css = css
        self.runner = runner
        commit(self.code, "synthetic local code")
        self.code_patch = patch.object(workflow, "REPO_ROOT", self.code)
        self.code_patch.start()
        self.environment = patch.dict(os.environ, {}, clear=False)
        self.environment.start()
        for marker in workflow.CI_MARKERS:
            os.environ.pop(marker, None)
        self.session = self.root / "session"

    def tearDown(self):
        self.environment.stop()
        self.code_patch.stop()
        self.temporary.cleanup()

    def populate(self, seed=17, session=None):
        return workflow.populate_session(session or self.session, self.source, seed)

    def prepare(self):
        manifest = self.populate()
        for entry in manifest["cases"]:
            case = self.session / "case-{}".format(entry["id"])
            fixture = case / "fixture"
            repository(fixture)
            target = fixture / ".claude/skills/example/SKILL.md"
            target.parent.mkdir(parents=True)
            target.write_bytes((case / "before.md").read_bytes())
            (fixture / "input.txt").write_text("Synthetic task input.\n")
            commit(fixture, "Before")
            target.write_bytes((case / "after.md").read_bytes())
            workflow.save_json(
                case / "scenario.json",
                {
                    "file": ".claude/skills/example/SKILL.md",
                    "task": "Read the skill and explain the synthetic rule.",
                },
            )
            workflow.save_json(
                case / "question.json",
                {
                    "stem": "Which statement is supported by this synthetic case?",
                    "scope": "Synthetic instruction-following rule.",
                    "options": [
                        {
                            "statement": "Synthetic option {}".format(index),
                            "correct": index == 2,
                            "rationale": "Synthetic rationale {}".format(index),
                        }
                        for index in range(4)
                    ],
                },
            )
        return manifest

    def freeze(self):
        manifest = self.prepare()
        workflow.freeze_session(self.session)
        return manifest

    def test_complete_reachable_sampling_and_uniform_shuffle(self):
        enumeration = workflow.enumerate_candidates(self.source, self.tip)
        self.assertEqual(
            {item["sha"] for item in enumeration["candidates"]}, self.eligible
        )
        excluded = {item["sha"]: item["reason"] for item in enumeration["excluded"]}
        self.assertEqual(excluded[self.special["whitespace"]], "whitespace-only")
        self.assertEqual(
            excluded[self.special["companion"]], "companion-change-in-skill-directory"
        )
        self.assertIn("merge", excluded.values())
        self.assertIn("root", excluded.values())
        self.assertNotIn(self.special["unreachable"], excluded)
        manifest = self.populate()
        sampling = workflow.read_json(self.session / "sampling.json")
        expected = list(enumeration["candidates"])
        random.Random(17).shuffle(expected)
        self.assertEqual(sampling["order"], [item["sha"] for item in expected])
        self.assertEqual(
            [entry["sha"] for entry in manifest["cases"]], sampling["order"][:5]
        )
        self.assertEqual(
            sampling["reachable_commits"],
            len(sampling["candidates"]) + len(sampling["excluded"]),
        )
        self.assertEqual(manifest["source_repo"], "DataRecce/recce-team")
        self.assertEqual(manifest["source_tip"], self.tip)
        self.assertEqual(self.session.stat().st_mode & 0o777, 0o700)
        for entry in manifest["cases"]:
            workflow.verify_source_case(self.session, entry)

    def test_fresh_secret_seeds_unique_sessions_and_fixed_public_boundary(self):
        with patch.object(
            workflow.secrets, "randbits", side_effect=[123, 456]
        ) as fresh:
            first = workflow.populate_session(self.root / "first", self.source)
            second = workflow.populate_session(self.root / "second", self.source)
        self.assertEqual([first["seed"], second["seed"]], [123, 456])
        self.assertEqual(fresh.call_count, 2)
        self.assertNotEqual(first["cases"], second["cases"])
        cli = workflow.parser()
        for option in (
            "--source",
            "--source-repo",
            "--seed",
            "--sha",
            "--agent",
            "--trials",
            "--model",
        ):
            with (
                contextlib.redirect_stderr(io.StringIO()),
                self.assertRaises(SystemExit),
            ):
                cli.parse_args(["init", option, "handpicked"])
        home = self.root / "home"
        home.mkdir()
        with (
            patch.object(Path, "home", return_value=home),
            patch.object(workflow, "populate_session") as populate,
        ):
            one, two = workflow.init_session(), workflow.init_session()
        self.assertNotEqual(one, two)
        self.assertEqual(populate.call_args_list[0].args, (one,))
        self.assertEqual(populate.call_args_list[1].args, (two,))
        self.assertEqual(populate.call_args_list[0].kwargs, {})
        self.assertEqual(
            workflow.SOURCE_URL, "https://github.com/DataRecce/recce-team.git"
        )

    def test_public_population_clones_only_fixed_url_without_checkout(self):
        def refuse_clone(arguments, **kwargs):
            self.assertEqual(
                arguments[:5],
                ["git", "clone", "--no-checkout", "--no-local", workflow.SOURCE_URL],
            )
            self.assertEqual(arguments[5], str(self.session / "source"))
            return subprocess.CompletedProcess(
                arguments, 1, stdout=b"", stderr=b"Synthetic network refusal."
            )

        with (
            patch.object(workflow.subprocess, "run", side_effect=refuse_clone),
            self.assertRaisesRegex(
                workflow.EvaluationError, "Fixed upstream clone failed"
            ),
        ):
            workflow.populate_session(self.session)
        self.assertIn(
            b"Synthetic network refusal", (self.session / "clone.log").read_bytes()
        )

    def test_safe_launcher_resolves_real_binary_before_path_change(self):
        self.populate()
        real = self.root / "real-claude"
        real.write_text("#!/bin/sh\nexit 90\n")
        real.chmod(0o700)
        alias = self.root / "claude-alias"
        alias.symlink_to(real)
        original = os.environ.get("PATH", "")
        with patch.object(
            workflow.shutil,
            "which",
            side_effect=lambda name: (
                str(alias) if name == "claude" else "/synthetic/jq"
            ),
        ):
            settings = workflow.prepare_launcher(self.session)
        self.assertEqual(os.environ.get("PATH", ""), original)
        self.assertEqual(settings["real_executable"], str(real))
        viewer = self.root / "fallback-bin"
        viewer.mkdir()
        executable = viewer / "open"
        executable.write_text(
            '#!/bin/sh\nprintf viewer > "$1.viewer-invoked"\nexit 0\n'
        )
        executable.chmod(0o700)
        sentinel = self.root / "harmless-synthetic-report.html"
        sentinel.write_text("Synthetic report sentinel.")
        env = os.environ.copy()
        env["PATH"] = str(self.session / "bin") + os.pathsep + str(viewer)
        result = REAL_RUN(
            ["open", str(sentinel)], env=env, capture_output=True, text=True
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("gated until quiz submission", result.stderr)
        self.assertFalse(Path(str(sentinel) + ".viewer-invoked").exists())
        self.assertEqual(sentinel.read_text(), "Synthetic report sentinel.")
        with (
            patch.object(
                workflow.shutil, "which", return_value=str(self.session / "bin/claude")
            ),
            self.assertRaisesRegex(workflow.EvaluationError, "outside this session"),
        ):
            workflow.prepare_launcher(self.session)

    def test_replacement_next_unused_preserves_rejection_and_refuses_authored(self):
        manifest = self.populate()
        old = manifest["cases"][0]
        old_bytes = (self.session / "case-1/before.md").read_bytes()
        order = workflow.read_json(self.session / "sampling.json")["order"]
        replacement = workflow.replace_case(
            self.session, 1, "Cannot construct a discriminating scenario"
        )
        self.assertEqual(replacement["sha"], order[5])
        changed = workflow.load_session(self.session)
        self.assertEqual(changed["next_candidate"], 6)
        self.assertEqual(changed["rejections"][0]["rejected"], old)
        self.assertEqual(
            (
                self.session / "rejected" / ("case-1-" + old["sha"]) / "before.md"
            ).read_bytes(),
            old_bytes,
        )
        notes = self.session / "case-2/authored.txt"
        notes.write_text("Do not destroy authored work.")
        with self.assertRaisesRegex(workflow.EvaluationError, "authored"):
            workflow.replace_case(self.session, 2, "Reason")
        self.assertEqual(notes.read_text(), "Do not destroy authored work.")

    def test_freeze_once_and_no_replacement_or_post_live_freeze(self):
        self.freeze()
        receipt = (self.session / workflow.RECEIPT).read_bytes()
        with self.assertRaisesRegex(workflow.EvaluationError, "one-time"):
            workflow.freeze_session(self.session)
        with self.assertRaisesRegex(workflow.EvaluationError, "after freeze"):
            workflow.replace_case(self.session, 3, "Reason")
        self.assertEqual((self.session / workflow.RECEIPT).read_bytes(), receipt)
        other = self.root / "attempted"
        workflow.populate_session(other, self.source, 17)
        workflow.save_json(other / "case-1/attempt.json", {"attempt": "retained"})
        with self.assertRaisesRegex(workflow.EvaluationError, "live attempt"):
            workflow.freeze_session(other)

    def test_source_bytes_and_fixture_single_change_are_fail_closed(self):
        manifest = self.prepare()
        case = self.session / "case-1"
        snapshot = case / "before.md"
        original = snapshot.read_bytes()
        snapshot.write_bytes(original + b"Tampered.\n")
        with self.assertRaisesRegex(workflow.EvaluationError, "snapshot bytes"):
            workflow.freeze_session(self.session)
        self.assertFalse((self.session / "answer-key.json").exists())
        snapshot.write_bytes(original)
        (case / "fixture/input.txt").write_text("An unrelated change.\n")
        with self.assertRaisesRegex(workflow.EvaluationError, "sole working change"):
            workflow.freeze_session(self.session)
        self.assertFalse((self.session / workflow.RECEIPT).exists())
        self.assertEqual(workflow.load_session(self.session), manifest)

    def test_frozen_input_hashes_detect_contents_additions_modes_and_heads(self):
        self.freeze()
        workflow.verify_frozen(self.session)
        names = (
            "session.json",
            "sampling.json",
            "case-1/before.md",
            "case-1/after.md",
            "case-1/patch.diff",
            "case-1/scenario.json",
            "case-1/question.json",
            "case-1/fixture/input.txt",
            "answer-key.json",
            "public/questions.json",
        )
        for name in names:
            with self.subTest(name=name):
                path = self.session / name
                original = path.read_bytes()
                path.write_bytes(original + b"\n")
                with (
                    self.assertRaises(workflow.EvaluationError),
                    patch.object(workflow, "prepare_launcher") as launcher,
                ):
                    workflow.run_session(self.session, approve_live=True)
                launcher.assert_not_called()
                path.write_bytes(original)
        added = self.session / "case-1/fixture/extra.txt"
        added.write_text("Unfrozen file.")
        with self.assertRaisesRegex(workflow.EvaluationError, "drifted"):
            workflow.verify_frozen(self.session)
        added.unlink()
        mode = self.session / "case-1/fixture/input.txt"
        previous = mode.stat().st_mode
        mode.chmod(0o755)
        with self.assertRaisesRegex(workflow.EvaluationError, "drifted"):
            workflow.verify_frozen(self.session)
        mode.chmod(previous)
        fixture = self.session / "case-1/fixture"
        old = command(fixture, "rev-parse", "HEAD")
        command(fixture, "commit", "--allow-empty", "-qm", "Metadata drift")
        with self.assertRaisesRegex(workflow.EvaluationError, "drifted"):
            workflow.verify_frozen(self.session)
        command(fixture, "update-ref", "HEAD", old)
        workflow.verify_frozen(self.session)

    def test_current_dirty_css_is_captured_but_archive_survives_later_code(self):
        self.css.write_text("body { color: red; } /* uncommitted */\n")
        manifest = self.freeze()
        self.assertEqual(
            manifest["code"]["files"][self.css.relative_to(self.code).as_posix()][
                "sha256"
            ],
            workflow.digest(self.css.read_bytes()),
        )
        cache = self.code / "plugin/__pycache__"
        cache.mkdir()
        (cache / "generated.pyc").write_bytes(b"Import cache does not change source.")
        workflow.verify_frozen(self.session)
        self.css.write_text("body { color: blue; }\n")
        with self.assertRaisesRegex(workflow.EvaluationError, "Local code/HEAD"):
            workflow.verify_frozen(self.session)
        workflow.verify_frozen(self.session, check_code=False)
        commit(self.code, "Later local code")
        workflow.verify_frozen(self.session, check_code=False)

    def test_unsafe_paths_symlinks_and_state_in_repo_rejected(self):
        for value in (
            "/tmp/SKILL.md",
            "../SKILL.md",
            "x/../SKILL.md",
            "x/.git/SKILL.md",
            "x//SKILL.md",
            "./SKILL.md",
            "x\\SKILL.md",
        ):
            with self.subTest(path=value), self.assertRaises(workflow.EvaluationError):
                workflow.relative_file(value)
        with self.assertRaisesRegex(workflow.EvaluationError, "outside"):
            workflow.populate_session(self.code / "evaluation-state", self.source, 17)
        self.prepare()
        alias = self.root / "alias"
        alias.symlink_to(self.session, target_is_directory=True)
        with self.assertRaisesRegex(workflow.EvaluationError, "Symlink"):
            workflow.load_session(alias)
        external = self.root / "external.txt"
        external.write_text("Never read or overwrite external state.")
        link = self.session / "case-1/fixture/escape.txt"
        link.symlink_to(external)
        with self.assertRaises(workflow.EvaluationError):
            workflow.freeze_session(self.session)
        self.assertEqual(
            external.read_text(), "Never read or overwrite external state."
        )
        link.unlink()
        self.session.chmod(0o755)
        with self.assertRaisesRegex(workflow.EvaluationError, "private"):
            workflow.load_session(self.session)
        self.session.chmod(0o700)

    def test_no_live_without_consent_or_in_ci_or_altered_source(self):
        self.populate()
        with patch.object(workflow, "prepare_launcher") as launcher:
            with self.assertRaisesRegex(workflow.EvaluationError, "approve-live"):
                workflow.run_session(self.session)
            for marker in workflow.CI_MARKERS:
                with (
                    patch.dict(os.environ, {marker: "false"}),
                    self.assertRaisesRegex(workflow.EvaluationError, "CI"),
                ):
                    workflow.run_session(self.session, approve_live=True)
        launcher.assert_not_called()
        manifest = workflow.read_json(self.session / "session.json")
        manifest["source_repo"] = "other/repo"
        workflow.save_json(self.session / "session.json", manifest)
        with self.assertRaisesRegex(workflow.EvaluationError, "fixed DataRecce"):
            workflow.load_session(self.session)

    def synthetic_runner(self, arguments, **kwargs):
        if arguments[0] != "bash":
            return REAL_RUN(arguments, **kwargs)
        self.assertEqual(
            arguments[1],
            str(self.code / "plugin/skills/behavior-diff/scripts/behavior-diff.sh"),
        )
        self.assertEqual(
            arguments[2:12],
            [
                "--agent",
                "claude",
                "--trials",
                "3",
                "--model",
                "opus",
                "--extract-agent",
                "claude",
                "--extract-model",
                "sonnet",
            ],
        )
        case = Path(kwargs["cwd"]).parent
        run = Path(kwargs["env"]["BEHAVIOR_DIFF_HOME"]) / "runs/diff-synthetic"
        run.mkdir(parents=True)
        target = arguments[arguments.index("--file") + 1]
        for variant in ("before", "after"):
            for index in range(1, 4):
                trial = run / "{}-{}".format(variant, index)
                project = trial / "project"
                path = project / target
                path.parent.mkdir(parents=True)
                path.write_bytes((case / (variant + ".md")).read_bytes())
                trace = [
                    {
                        "type": "system",
                        "model": "claude-opus-synthetic",
                        "tools": ["Read", "Grep", "Glob"],
                    },
                    {
                        "type": "assistant",
                        "message": {
                            "content": [
                                {
                                    "type": "tool_use",
                                    "id": "read-1",
                                    "name": "Read",
                                    "input": {"file_path": target},
                                },
                                {
                                    "type": "tool_use",
                                    "id": "read-2",
                                    "name": "Read",
                                    "input": {"file_path": "absent.txt"},
                                },
                            ]
                        },
                    },
                    {
                        "type": "user",
                        "message": {
                            "content": [
                                {
                                    "type": "tool_result",
                                    "tool_use_id": "read-1",
                                    "content": "Synthetic source.",
                                },
                                {
                                    "type": "tool_result",
                                    "tool_use_id": "read-2",
                                    "is_error": True,
                                    "content": "File does not exist.",
                                },
                            ]
                        },
                    },
                    {
                        "type": "result",
                        "subtype": "success",
                        "result": "Synthetic answer.",
                        "total_cost_usd": 0.0,
                        "usage": {"input_tokens": 10, "output_tokens": 5},
                    },
                ]
                (trial / "trace.jsonl").write_text(
                    "\n".join(json.dumps(event) for event in trace) + "\n"
                )
        for name in ("report.html", "report.md", "report-data.json"):
            (run / name).write_text(
                "{}" if name.endswith(".json") else "Synthetic saved report."
            )
        kwargs["stdout"].write(b"Synthetic runner log; no model called.\n")
        return subprocess.CompletedProcess(arguments, 0)

    def test_single_attempt_retained_logs_models_reads_bytes_and_optional_decisions(
        self,
    ):
        self.freeze()
        with (
            patch.object(
                workflow,
                "prepare_launcher",
                return_value={"real_executable": "synthetic-only"},
            ),
            patch.object(workflow.subprocess, "run", side_effect=self.synthetic_runner),
        ):
            completed = workflow.run_session(self.session, approve_live=True, case_id=1)
            with self.assertRaisesRegex(workflow.EvaluationError, "already attempted"):
                workflow.run_session(self.session, approve_live=True, case_id=1)
        self.assertEqual(len(completed), 1)
        evidence = completed[0]
        self.assertFalse(evidence["blocked"])
        self.assertIsNone(evidence["artifacts"]["decisions.json"])
        self.assertEqual(evidence["cost_usd"], 0.0)
        self.assertEqual(len(evidence["trials"]), 6)
        for trial in evidence["trials"]:
            self.assertEqual(trial["actual_models"], ["claude-opus-synthetic"])
            self.assertEqual(trial["source_reads"]["successful"], 1)
            self.assertEqual(trial["source_reads"]["missing"], 1)
            self.assertEqual(trial["source_reads"]["successful_target"], 1)
            variant = trial["id"].split("-")[0]
            self.assertEqual(
                (
                    self.session / "case-1/trial-targets" / (trial["id"] + ".md")
                ).read_bytes(),
                (self.session / "case-1" / (variant + ".md")).read_bytes(),
            )
        self.assertIn(
            "Synthetic runner log", (self.session / "case-1/runner.log").read_text()
        )
        self.assertTrue((self.session / "case-1/attempt.json").is_file())

    def test_no_report_is_explicit_and_attempt_evidence_cannot_retry(self):
        self.freeze()

        def failed_runner(arguments, **kwargs):
            if arguments[0] == "bash":
                kwargs["stdout"].write(b"Synthetic launch failure.\n")
                return subprocess.CompletedProcess(arguments, 8)
            return REAL_RUN(arguments, **kwargs)

        with (
            patch.object(
                workflow,
                "prepare_launcher",
                return_value={"real_executable": "synthetic-only"},
            ),
            patch.object(workflow.subprocess, "run", side_effect=failed_runner),
        ):
            with self.assertRaisesRegex(workflow.EvaluationError, "no complete report"):
                workflow.run_session(self.session, approve_live=True, case_id=2)
            with self.assertRaisesRegex(workflow.EvaluationError, "already attempted"):
                workflow.run_session(self.session, approve_live=True, case_id=2)
        evidence = workflow.read_json(self.session / "case-2/run-evidence.json")
        self.assertEqual(evidence["runner_exit_code"], 8)
        self.assertTrue(evidence["blocked"])
        self.assertIsNone(evidence["cost_usd"])

    def test_blocked_trial_still_completes_saved_report_without_retry(self):
        self.freeze()

        def blocked_runner(arguments, **kwargs):
            result = self.synthetic_runner(arguments, **kwargs)
            if arguments[0] == "bash":
                run = Path(kwargs["env"]["BEHAVIOR_DIFF_HOME"]) / "runs/diff-synthetic"
                (run / "before-1/trace.jsonl").write_text(
                    '{"type":"result","is_error":true,"result":""}\n'
                )
            return result

        with (
            patch.object(
                workflow,
                "prepare_launcher",
                return_value={"real_executable": "synthetic-only"},
            ),
            patch.object(workflow.subprocess, "run", side_effect=blocked_runner),
        ):
            completed = workflow.run_session(self.session, approve_live=True, case_id=4)
            with self.assertRaisesRegex(workflow.EvaluationError, "already attempted"):
                workflow.run_session(self.session, approve_live=True, case_id=4)
        self.assertTrue(completed[0]["blocked"])
        self.assertIsNotNone(completed[0]["artifacts"]["report.html"])
        self.assertEqual(len(completed[0]["trials"]), 6)

    def test_default_runs_all_cases_sequentially_in_separate_roots(self):
        self.freeze()
        order = []

        def sequential_runner(arguments, **kwargs):
            if arguments[0] == "bash":
                order.append(Path(kwargs["cwd"]).parent.name)
            return self.synthetic_runner(arguments, **kwargs)

        with (
            patch.object(
                workflow,
                "prepare_launcher",
                return_value={"real_executable": "synthetic-only"},
            ),
            patch.object(workflow.subprocess, "run", side_effect=sequential_runner),
        ):
            completed = workflow.run_session(self.session, approve_live=True)
        self.assertEqual(order, ["case-1", "case-2", "case-3", "case-4", "case-5"])
        self.assertEqual([entry["case"] for entry in completed], [1, 2, 3, 4, 5])
        self.assertEqual(
            len({entry["artifacts"]["report.html"]["path"] for entry in completed}), 5
        )


if __name__ == "__main__":
    unittest.main()
