#!/usr/bin/env python3
"""Synthetic shared-data staging boundaries; no models, credentials, or network.

Default checks exercise only the private prepare/verify helper and never launch
the runner. Pass --runner-smoke for a manual smoke that runs the shipped runner
and trial adapters with local fake claude/codex executables first on PATH.
"""

import argparse
import io
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / "plugin/skills/behavior-diff/scripts"
HELPER = SCRIPTS / "prepare_shared.py"
RUNNER = SCRIPTS / "behavior-diff.sh"

TARGET = "CLAUDE.md"
BEFORE = b"# Synthetic rules\n\nAnswer from the records file.\n"
AFTER = b"# Synthetic rules\n\nAnswer from the records file and cite each row.\n"
EXPLICIT = b"# Synthetic rules\n\nExplicit synthetic Before version.\n"
PURPOSE = {
    "goals": [
        {
            "text": "Cite each synthetic record row.",
            "source": "session",
            "basis": "explicit",
            "reference": "Synthetic request",
        }
    ]
}
SCENARIO = {
    "summary": "Synthetic records include one negative amount.",
    "rationale": "A negative row tests whether every row is still cited.",
    "conditions": ["One synthetic record has a negative amount."],
    "limitations": ["Only two synthetic records are included."],
    "checks": [
        {
            "id": "cite-rows",
            "goal": 1,
            "text": "The answer cites each synthetic record row.",
            "mode": "new",
            "required_evidence": "The final answer names both synthetic rows.",
            "evidence_kind": "output",
        }
    ],
    "source_requirements": [],
}
SOURCE = {
    "forge": "github",
    "repository_url": "https://github.com/example-org/synthetic-skills",
    "before_commit": "a" * 40,
    "after_commit": "b" * 40,
    "pull_requests": [
        {
            "number": 7,
            "title": "Synthetic rule edit",
            "url": "https://github.com/example-org/synthetic-skills/pull/7",
            "applies_to": "after",
        }
    ],
}
COMMITTED = {
    TARGET: BEFORE,
    ".gitignore": b"data/\n*.local\n",
    "docs/guide.md": b"Committed synthetic guide.\n",
    "docs/status.md": b"Committed synthetic status.\n",
    "run.sh": (b"#!/bin/sh\necho synthetic\n", True),
    "notes/purpose.json": json.dumps(PURPOSE).encode(),
    "notes/scenario.json": json.dumps(SCENARIO).encode(),
}
WORKING = {
    TARGET: AFTER,
    "docs/guide.md": b"Uncommitted synthetic guide.\n",
    "scratch.txt": b"Untracked synthetic note.\n",
    "cache.local": b"Ignored synthetic cache.\n",
}
SHARED = {
    "data/records.csv": b"id,amount\n1,10\n2,-5\n",
    "data/tool.sh": (b"#!/bin/sh\ncat data/records.csv\n", True),
    "docs/status.md": b"Shared synthetic status.\n",
}
PRIVATE = ["notes/purpose.json", "notes/scenario.json"]
TRIAL_MODEL = "synthetic-trial-model"
EXTRACT_MODEL = "synthetic-extract-model"


def normalized(files):
    return {
        name: content if isinstance(content, tuple) else (content, False)
        for name, content in files.items()
    }


# Expected scratch baseline for the standard Git fixture: HEAD content only,
# reviewed shared files on top, private context removed.
BASELINE = normalized(
    {
        TARGET: BEFORE,
        ".gitignore": COMMITTED[".gitignore"],
        "docs/guide.md": COMMITTED["docs/guide.md"],
        "docs/status.md": SHARED["docs/status.md"],
        "run.sh": COMMITTED["run.sh"],
        "data/records.csv": SHARED["data/records.csv"],
        "data/tool.sh": SHARED["data/tool.sh"],
    }
)


def write_files(root, files):
    for name, (data, executable) in normalized(files).items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        path.chmod(0o755 if executable else 0o644)


def encoded(path):
    # Hook store key: percent-encode '%' first, then '/'.
    return str(path).replace("%", "%25").replace("/", "%2F")


def tree_state(root, skip_git=False):
    """Every entry under root, including hidden files, by kind and content."""
    state = {}
    for current, dirs, files in os.walk(root):
        base = Path(current)
        if skip_git and base == root and ".git" in dirs:
            dirs.remove(".git")
        for name in sorted(dirs + files):
            path = base / name
            key = path.relative_to(root).as_posix()
            mode = path.lstat().st_mode
            if stat.S_ISLNK(mode):
                state[key] = ("link", os.readlink(path))
            elif stat.S_ISDIR(mode):
                state[key] = ("dir", stat.S_IMODE(mode))
            elif stat.S_ISREG(mode):
                state[key] = ("file", path.read_bytes(), stat.S_IMODE(mode))
            else:
                state[key] = ("special", stat.S_IFMT(mode))
    return state


def trace_events(trace):
    results, finals = [], []
    for line in trace.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        event = json.loads(line)
        if event.get("type") == "user":
            for item in event["message"]["content"]:
                if item.get("type") == "tool_result":
                    results.append(item["content"])
        elif event.get("type") == "result":
            finals.append(event.get("result") or "")
    return results, finals


class Fixtures:
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="shared-data-test-")
        self.addCleanup(temp.cleanup)
        self.tmp = Path(temp.name).resolve()
        self.home = self.tmp / "home"
        self.home.mkdir()
        (self.tmp / "tmp").mkdir()
        gitconfig = self.tmp / "gitconfig"
        gitconfig.write_text(
            "[user]\n\tname = Synthetic Tester\n\temail = tester@example.invalid\n"
            "[init]\n\tdefaultBranch = main\n[commit]\n\tgpgSign = false\n"
            "[core]\n\tautocrlf = false\n",
            encoding="utf-8",
        )
        self.store_home = self.tmp / "behavior-home"
        self.env = {
            "PATH": os.environ["PATH"],
            "HOME": str(self.home),
            "LANG": "C",
            "TMPDIR": str(self.tmp / "tmp"),
            "GIT_CONFIG_GLOBAL": str(gitconfig),
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_AUTHOR_DATE": "2026-01-01T00:00:00Z",
            "GIT_COMMITTER_DATE": "2026-01-01T00:00:00Z",
            "BEHAVIOR_DIFF_HOME": str(self.store_home),
        }
        self.stages = 0

    def git(self, cwd, *args):
        return subprocess.run(
            ["git", "-C", str(cwd), *args],
            env=self.env,
            check=True,
            capture_output=True,
        ).stdout

    def git_project(self, name="project", committed=COMMITTED, working=WORKING):
        project = self.tmp / name
        project.mkdir()
        self.git(project, "init", "-q")
        write_files(project, committed)
        self.git(project, "add", "-A")
        self.git(project, "commit", "-qm", "Synthetic fixture")
        write_files(project, working)
        return project

    def folder(self, name, files):
        root = self.tmp / name
        root.mkdir()
        write_files(root, files)
        return root

    def store_entry(self, target, name, data, mtime, key=None):
        store = self.store_home / "baselines" / (key or encoded(target))
        store.mkdir(parents=True, exist_ok=True)
        entry = store / name
        entry.write_bytes(data)
        os.utime(entry, (mtime, mtime))
        return entry

    def prepare(
        self,
        project,
        data,
        output=None,
        file=TARGET,
        before=None,
        exclude=(),
        env=None,
        handoff=None,
    ):
        if output is None:
            self.stages += 1
            output = self.tmp / f"stage-{self.stages}"
        argv = [
            sys.executable,
            str(HELPER),
            "prepare",
            "--project",
            str(project),
            "--file",
            file,
            "--data",
            str(data),
            "--output",
            str(output),
        ]
        if handoff is not None:
            argv += ["--handoff", str(handoff)]
        if before is not None:
            argv += ["--before-file", str(before)]
        for name in exclude:
            argv += ["--exclude", name]
        result = subprocess.run(
            argv, env=env or self.env, capture_output=True, text=True
        )
        return result, output

    def verify(self, root):
        return subprocess.run(
            [sys.executable, str(HELPER), "verify", str(root)],
            env=self.env,
            capture_output=True,
            text=True,
        )

    def staged(self, project, data, **options):
        result, output = self.prepare(project, data, **options)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(Path(result.stdout.strip()).resolve(), output.resolve())
        return output

    def archive_files(self, repo, rev="HEAD"):
        raw = self.git(repo, "archive", "--format=tar", rev)
        files = {}
        with tarfile.open(fileobj=io.BytesIO(raw), mode="r:") as bundle:
            for entry in bundle:
                if entry.isdir():
                    continue
                self.assertTrue(entry.isfile(), entry.name)
                with bundle.extractfile(entry) as stream:
                    files[entry.name] = (stream.read(), bool(entry.mode & 0o111))
        return files

    def working_files(self, root):
        files = {}
        for name, entry in tree_state(root, skip_git=True).items():
            if entry[0] == "dir":
                continue
            self.assertEqual(entry[0], "file", name)
            files[name] = (entry[1], bool(entry[2] & 0o111))
        return files

    def original_state(self, *roots):
        states = []
        for root in roots:
            facts = []
            if (root / ".git").is_dir():
                for args in (
                    ("rev-parse", "--verify", "-q", "HEAD"),
                    ("for-each-ref",),
                    ("ls-files", "-s"),
                    ("stash", "list"),
                    ("config", "--local", "--list"),
                    ("status", "--porcelain=v1", "-uall", "--ignored"),
                ):
                    facts.append(
                        subprocess.run(
                            ["git", "-C", str(root), *args],
                            env=self.env,
                            capture_output=True,
                        ).stdout
                    )
            states.append((tree_state(root, skip_git=True), facts))
        return states

    def assert_rejected(self, result, output):
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertTrue(result.stderr.strip())
        self.assertFalse(output.exists() or output.is_symlink(), output)

    def standard(self):
        return self.git_project(), self.folder("data", SHARED)

    def handoff_file(self, settings=None):
        context = self.tmp / "private"
        context.mkdir(mode=0o700, exist_ok=True)
        values = {
            "purpose.json": PURPOSE,
            "scenario.json": SCENARIO,
            "source.json": SOURCE,
        }
        for name, value in values.items():
            path = context / name
            path.write_text(json.dumps(value))
            path.chmod(0o600)
        for name, text in (
            (
                "task.txt",
                "Read every project file, then summarize the records using the rules.",
            ),
            ("notes.md", "Synthetic private case criteria."),
            ("tool.py", "print('synthetic')\n"),
        ):
            path = context / name
            path.write_text(text)
            path.chmod(0o600)
        record = {
            key + "_file": str(context / name)
            for key, name in (
                ("task", "task.txt"),
                ("purpose", "purpose.json"),
                ("scenario", "scenario.json"),
                ("source", "source.json"),
                ("notes", "notes.md"),
            )
        }
        record.update(
            references=["docs/guide.md"],
            tools=[str(context / "tool.py")],
            settings=settings or {"agent": "codex", "model": TRIAL_MODEL},
        )
        path = context / "handoff.json"
        path.write_text(json.dumps(record))
        path.chmod(0o600)
        return path


class HandoffTests(Fixtures, unittest.TestCase):
    def frozen(self, project, descriptor, **options):
        output = self.tmp / "direct"
        result = subprocess.run(
            [
                sys.executable,
                str(HELPER),
                "freeze",
                "--project",
                str(project),
                "--file",
                TARGET,
                "--output",
                str(output),
                "--handoff",
                str(descriptor),
                *options.get("args", []),
            ],
            env=self.env,
            capture_output=True,
            text=True,
        )
        return result, output

    def test_non_null_purpose_rejects_null_scenario_before_freezing(self):
        project = self.git_project(
            committed={k: v for k, v in COMMITTED.items() if k not in PRIVATE}
        )
        data = self.folder("data", SHARED)
        descriptor = self.handoff_file()
        scenario = descriptor.parent / "scenario.json"
        scenario.write_text("null")
        # General nullable-reader behavior is unchanged outside the new handoff.
        reader = subprocess.run(
            [
                sys.executable,
                str(SCRIPTS / "scenario.py"),
                str(scenario),
                "--purpose-file",
                str(descriptor.parent / "purpose.json"),
            ],
            env=self.env,
            capture_output=True,
            text=True,
        )
        self.assertEqual(reader.returncode, 0, reader.stderr)
        self.assertIsNone(json.loads(reader.stdout))
        for mode in ("staged", "direct"):
            with self.subTest(mode=mode):
                result, root = (
                    self.prepare(project, data, handoff=descriptor)
                    if mode == "staged"
                    else self.frozen(project, descriptor)
                )
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                self.assertTrue(result.stderr.strip())
                self.assertFalse(root.exists())

    def test_complete_staged_handoff_rejects_every_context_and_settings_mutation(self):
        project, data = self.standard()
        descriptor = self.handoff_file()
        stage = self.staged(project, data, handoff=descriptor, exclude=PRIVATE)
        record = json.loads(descriptor.read_text())
        for key in (
            "task_file",
            "purpose_file",
            "scenario_file",
            "source_file",
            "notes_file",
        ):
            path = Path(record[key])
            original = path.read_bytes()
            path.write_bytes(original + b" ")
            self.assertNotEqual(self.verify(stage).returncode, 0, key)
            path.write_bytes(original)
        for path in (
            descriptor,
            descriptor.parent / "tool.py",
            stage / "project/docs/guide.md",
        ):
            original = path.read_bytes()
            path.unlink()
            self.assertNotEqual(self.verify(stage).returncode, 0)
            path.write_bytes(original + b" ")
            path.chmod(0o600)
            self.assertNotEqual(self.verify(stage).returncode, 0)
            path.write_bytes(original)
        Path(record["notes_file"]).chmod(0o644)
        self.assertNotEqual(self.verify(stage).returncode, 0)

    def test_frozen_handoff_rejects_isolation_environment_changes(self):
        project, data = self.standard()
        self.env["BEHAVIOR_DIFF_CODEX_ISOLATION_ROOT"] = str(self.tmp / "runtime")
        self.env["BEHAVIOR_DIFF_CODEX_DENY_READ"] = str(project)
        stage = self.staged(project, data, handoff=self.handoff_file())
        result = self.verify(stage)
        self.assertEqual(result.returncode, 0, result.stderr)
        for name in (
            "BEHAVIOR_DIFF_CODEX_ISOLATION_ROOT",
            "BEHAVIOR_DIFF_CODEX_DENY_READ",
        ):
            original = self.env.pop(name)
            self.assertNotEqual(self.verify(stage).returncode, 0)
            self.env[name] = original + "-different"
            self.assertNotEqual(self.verify(stage).returncode, 0)
            self.env[name] = original
        result = self.verify(stage)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_direct_freeze_uses_archive_not_unrelated_work_and_rejects_stale_after(
        self,
    ):
        project = self.git_project(
            committed={k: v for k, v in COMMITTED.items() if k not in PRIVATE}
        )
        original = self.original_state(project)
        result, root = self.frozen(project, self.handoff_file())
        self.assertEqual(result.returncode, 0, result.stderr)
        (project / "scratch.txt").write_text("Unrelated later synthetic work")
        self.assertEqual(self.verify(root).returncode, 0)
        (project / TARGET).write_bytes(b"stale")
        self.assertNotEqual(self.verify(root).returncode, 0)
        (project / TARGET).write_bytes(AFTER)
        (project / "scratch.txt").write_bytes(WORKING["scratch.txt"])
        self.assertEqual(self.original_state(project), original)

    def test_invalid_private_or_incomplete_handoffs_fail_before_output(self):
        project, data = self.standard()
        descriptor = self.handoff_file()
        original = descriptor.read_text()
        for change in (
            {"references": ["missing.md"]},
            {"references": ["../outside"]},
            {"purpose_file": str(descriptor.parent / "notes.md")},
            {"settings": {"agent": "codex", "command": "touch unwanted"}},
            {"notes_file": str(project / "notes/purpose.json")},
        ):
            descriptor.write_text(json.dumps({**json.loads(original), **change}))
            result, root = self.prepare(
                project, data, handoff=descriptor, exclude=PRIVATE
            )
            self.assert_rejected(result, root)
        descriptor.write_text(original)
        scenario = descriptor.parent / "scenario.json"
        record = json.loads(scenario.read_text())
        record["checks"][0]["goal"] = 2
        scenario.write_text(json.dumps(record))
        result, root = self.prepare(project, data, handoff=descriptor, exclude=PRIVATE)
        self.assert_rejected(result, root)

    def test_direct_absent_before_is_verified_and_context_symlinks_rejected(self):
        project = self.git_project(
            committed={"docs/guide.md": b"Synthetic reference\n"},
            working={TARGET: AFTER},
        )
        self.store_entry(project / TARGET, "1-ABSENT", b"", 1000)
        descriptor = self.handoff_file()
        result, root = self.frozen(project, descriptor)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((root / "before").exists())
        newer = self.store_entry(project / TARGET, "2", BEFORE, 2000)
        self.assertNotEqual(self.verify(root).returncode, 0)
        newer.unlink()
        valid = self.verify(root)
        self.assertEqual(valid.returncode, 0, valid.stderr)
        notes = descriptor.parent / "notes.md"
        notes.unlink()
        notes.symlink_to(descriptor.parent / "task.txt")
        self.assertNotEqual(self.verify(root).returncode, 0)


class SharedDataBoundaryTests(Fixtures, unittest.TestCase):
    def test_git_head_baseline_freezes_shared_files_and_only_after_differs(self):
        project, data = self.standard()
        original = self.original_state(project, data)
        stage = self.staged(project, data, exclude=PRIVATE)
        scratch = stage / "project"

        self.assertEqual(stat.S_IMODE(stage.stat().st_mode), 0o700)
        self.assertEqual(stat.S_IMODE((stage / "freeze.json").stat().st_mode), 0o600)
        self.assertTrue((stage / "home").is_dir())
        self.assertEqual((stage / "before").read_bytes(), BEFORE)
        self.assertEqual(self.archive_files(scratch), BASELINE)
        self.assertEqual(
            self.working_files(scratch), {**BASELINE, TARGET: (AFTER, False)}
        )
        status = self.git(scratch, "status", "--porcelain=v1", "-uall").decode()
        self.assertEqual(status.splitlines(), [f" M {TARGET}"])
        self.assertEqual(self.git(scratch, "remote").strip(), b"")
        self.assertIn(b"Signed-off-by:", self.git(scratch, "log", "-1", "--format=%B"))
        self.assertEqual(self.original_state(project, data), original)
        self.assertEqual(self.verify(stage).returncode, 0)

    def test_frozen_stage_no_longer_depends_on_original_inputs(self):
        project, data = self.standard()
        stage = self.staged(project, data, exclude=PRIVATE)
        frozen = tree_state(stage / "project", skip_git=True)
        (data / "data/records.csv").write_bytes(b"id,amount\n9,99\n")
        (project / TARGET).write_bytes(b"# Later unrelated edit\n")
        self.store_entry(project / TARGET, "20260105-000000-1", b"later", 5000)
        self.assertEqual(self.verify(stage).returncode, 0)
        self.assertEqual(tree_state(stage / "project", skip_git=True), frozen)

    def test_git_redirect_environment_is_rejected_before_handoff(self):
        project, data = self.standard()
        stage = self.staged(project, data, exclude=PRIVATE)
        original = self.original_state(project, data)
        for key, value in (
            ("GIT_INDEX_FILE", str(project / ".git/index")),
            ("GIT_DIR", str(project / ".git")),
            ("GIT_CONFIG_COUNT", "1"),
        ):
            with self.subTest(key=key):
                env = dict(self.env, **{key: value})
                result, output = self.prepare(project, data, exclude=PRIVATE, env=env)
                self.assert_rejected(result, output)
                checked = subprocess.run(
                    [sys.executable, str(HELPER), "verify", str(stage)],
                    env=env,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(checked.returncode, 2)
        self.assertEqual(self.original_state(project, data), original)

    def test_global_git_configuration_cannot_run_staging_hooks(self):
        project, data = self.standard()
        marker = self.tmp / "hook-ran"
        hooks = self.tmp / "hooks"
        hooks.mkdir()
        for name in ("pre-commit", "commit-msg", "post-commit"):
            hook = hooks / name
            hook.write_text(f"#!/bin/sh\ntouch '{marker}'\nexit 1\n")
            hook.chmod(0o755)
        attributes = self.tmp / "attributes"
        attributes.write_text("*.csv export-ignore\n")
        hostile_home = self.tmp / "hostile-home"
        hostile_home.mkdir()
        hostile = hostile_home / ".gitconfig"
        hostile.write_text(
            f"[core]\n\thooksPath = {hooks}\n\tattributesFile = {attributes}\n"
            f"[commit]\n\tgpgSign = true\n[gpg]\n\tprogram = {shutil.which('false')}\n"
        )
        original = self.original_state(project, data)
        env = dict(
            self.env,
            HOME=str(hostile_home),
            GIT_CONFIG_GLOBAL=str(hostile),
        )
        stage = self.staged(project, data, exclude=PRIVATE, env=env)
        self.assertEqual(self.archive_files(stage / "project"), BASELINE)
        self.assertNotIn(
            b"gpgsig", self.git(stage / "project", "cat-file", "commit", "HEAD")
        )
        self.assertFalse(marker.exists())
        self.assertEqual(self.original_state(project, data), original)

    def test_launch_git_config_cannot_change_frozen_archive(self):
        project, data = self.standard()
        original = self.original_state(project, data)
        stage = self.staged(project, data, exclude=PRIVATE)
        self.assertEqual(self.archive_files(stage / "project"), BASELINE)
        with Path(self.env["GIT_CONFIG_GLOBAL"]).open("a") as stream:
            stream.write("\n[tar]\n\tumask = 0111\n")
        self.assertFalse(self.archive_files(stage / "project")["data/tool.sh"][1])
        result = self.verify(stage)
        self.assertEqual(result.returncode, 2, result.stderr)
        result, output = self.prepare(project, data, exclude=PRIVATE)
        self.assert_rejected(result, output)
        self.assertEqual(self.original_state(project, data), original)

    def test_attribute_induced_archive_changes_are_rejected(self):
        cases = {
            "project export-ignore": (
                {".gitattributes": b"data/** export-ignore\n"},
                {"data/records.csv": b"id\n1\n"},
            ),
            "shared export-ignore": (
                {},
                {
                    "data/.gitattributes": b"records.csv export-ignore\n",
                    "data/records.csv": b"1\n",
                },
            ),
            "shared export-subst": (
                {},
                {
                    "data/.gitattributes": b"stamp.txt export-subst\n",
                    "data/stamp.txt": b"$Format:%H$\n",
                },
            ),
        }
        for label, (extra, shared) in cases.items():
            with self.subTest(label):
                name = label.replace(" ", "-")
                project = self.git_project(name, {**COMMITTED, **extra})
                data = self.folder(name + "-data", shared)
                original = self.original_state(project, data)
                result, output = self.prepare(project, data)
                self.assert_rejected(result, output)
                self.assertEqual(self.original_state(project, data), original)

    def test_explicit_before_wins_and_is_read_literally(self):
        project, data = self.standard()
        self.store_entry(project / TARGET, "20260101-000000-ABSENT", b"", 1000)
        literal = self.tmp / "CLAUDE.md-ABSENT"
        literal.write_bytes(EXPLICIT)
        stage = self.staged(project, data, before=literal, exclude=PRIVATE)
        self.assertEqual(
            self.archive_files(stage / "project")[TARGET], (EXPLICIT, False)
        )
        self.assertEqual((stage / "before").read_bytes(), EXPLICIT)
        self.assertEqual((stage / "project" / TARGET).read_bytes(), AFTER)

    def test_before_file_inside_project_is_excluded_from_shared_baseline(self):
        project = self.git_project(
            committed={**COMMITTED, "drafts/old-CLAUDE.md": EXPLICIT}
        )
        data = self.folder("data", SHARED)
        stage = self.staged(
            project, data, before=project / "drafts/old-CLAUDE.md", exclude=PRIVATE
        )
        archived = self.archive_files(stage / "project")
        self.assertNotIn("drafts/old-CLAUDE.md", archived)
        self.assertEqual(archived[TARGET], (EXPLICIT, False))
        self.assertNotIn("drafts/old-CLAUDE.md", self.working_files(stage / "project"))

    def test_empty_home_override_uses_default_hook_baseline(self):
        project = self.folder("project", {TARGET: AFTER})
        data = self.folder("data", SHARED)
        self.store_home = self.home / ".behavior-diff"
        self.store_entry(project / TARGET, "20260101-000000", BEFORE, 1000)
        self.env["BEHAVIOR_DIFF_HOME"] = ""
        original = self.original_state(project, data, self.store_home)
        stage = self.staged(project, data)
        self.assertEqual((stage / "before").read_bytes(), BEFORE)
        self.assertEqual(self.archive_files(stage / "project")[TARGET][0], BEFORE)
        self.assertEqual((stage / "project" / TARGET).read_bytes(), AFTER)
        self.assertEqual(self.original_state(project, data, self.store_home), original)

    def test_hook_baseline_uses_newest_visible_entry_under_percent_encoded_key(self):
        project = self.folder(
            "pct%dir", {TARGET: AFTER, "notes.md": b"Synthetic notes.\n"}
        )
        data = self.folder("data", SHARED)
        target = project / TARGET
        self.store_entry(target, "20260101-000000-1", b"older\n", 1000)
        self.store_entry(target, "20260102-000000-2", BEFORE, 2000)
        self.store_entry(target, ".session-synthetic", b"hidden marker\n", 3000)
        naive = str(target).replace("/", "%2F")
        self.assertNotEqual(naive, encoded(target))
        self.store_entry(target, "20260109-000000-3", b"decoy\n", 9000, key=naive)

        stage = self.staged(project, data)
        self.assertEqual(self.archive_files(stage / "project")[TARGET], (BEFORE, False))
        self.assertEqual((stage / "before").read_bytes(), BEFORE)

        self.store_entry(target, "20260103-000000-ABSENT", b"", 4000)
        stage = self.staged(project, data)
        scratch = stage / "project"
        self.assertNotIn(TARGET, self.archive_files(scratch))
        self.assertEqual((scratch / TARGET).read_bytes(), AFTER)
        status = self.git(scratch, "status", "--porcelain=v1", "-uall").decode()
        self.assertEqual(status.splitlines(), [f"?? {TARGET}"])
        self.assertFalse((stage / "before").exists())
        marker_dir = stage / "home/baselines" / encoded(scratch.resolve() / TARGET)
        entries = [entry.name for entry in marker_dir.iterdir()]
        self.assertEqual(len(entries), 1)
        self.assertTrue(entries[0].endswith("-ABSENT"))
        self.assertEqual(self.verify(stage).returncode, 0)

    def test_untracked_target_without_recorded_before_is_rejected(self):
        committed = {name: data for name, data in COMMITTED.items() if name != TARGET}
        data = self.folder("data", SHARED)
        for label, project in (
            ("git", self.git_project("git", committed)),
            ("folder", self.folder("folder", {TARGET: AFTER})),
        ):
            with self.subTest(label):
                result, output = self.prepare(project, data)
                self.assert_rejected(result, output)

    def test_identical_before_and_after_are_rejected(self):
        data = self.folder("data", SHARED)
        unchanged = self.git_project("unchanged", working={})
        result, output = self.prepare(unchanged, data)
        self.assert_rejected(result, output)
        project = self.git_project()
        same = self.tmp / "same.md"
        same.write_bytes(AFTER)
        result, output = self.prepare(project, data, before=same)
        self.assert_rejected(result, output)

    def test_instruction_executable_mode_change_is_rejected(self):
        data = self.folder("data", SHARED)
        project = self.git_project()
        (project / TARGET).chmod(0o755)
        result, output = self.prepare(project, data)
        self.assert_rejected(result, output)
        project = self.git_project("explicit")
        before = self.tmp / "before-exec.md"
        before.write_bytes(EXPLICIT)
        before.chmod(0o755)
        result, output = self.prepare(project, data, before=before)
        self.assert_rejected(result, output)

    def test_unborn_repository_copies_folder_without_git_or_nested_state(self):
        project = self.tmp / "unborn"
        project.mkdir()
        self.git(project, "init", "-q")
        write_files(
            project,
            {
                TARGET: AFTER,
                "notes.md": b"Untracked notes.\n",
                "bin/check": (b"#!/bin/sh\n", True),
            },
        )
        nested_home = project / ".bd-home"
        self.env["BEHAVIOR_DIFF_HOME"] = str(nested_home)
        self.store_home = nested_home
        self.store_entry(project / TARGET, "20260101-000000-1", BEFORE, 1000)
        data = self.folder("data", SHARED)
        original = self.original_state(project, data)
        stage = self.staged(project, data)
        expected = normalized(
            {
                TARGET: BEFORE,
                "notes.md": b"Untracked notes.\n",
                "bin/check": (b"#!/bin/sh\n", True),
                **SHARED,
            }
        )
        self.assertEqual(self.archive_files(stage / "project"), expected)
        self.assertEqual(self.original_state(project, data), original)

    def test_copy_cap_rejects_oversized_inputs(self):
        big = b"x" * 4096
        small = {TARGET: AFTER}
        env = dict(self.env, BEHAVIOR_DIFF_COPY_CAP_KB="2")
        cases = (
            (
                "git",
                self.git_project("git", {**COMMITTED, "big.txt": big}),
                SHARED,
                None,
            ),
            (
                "folder",
                self.folder("folder", {**small, "big.txt": big}),
                SHARED,
                BEFORE,
            ),
            ("shared", self.folder("small", small), {"data/big.txt": big}, BEFORE),
        )
        for label, project, shared, before in cases:
            with self.subTest(label):
                data = self.folder(label + "-data", shared)
                before_file = None
                if before is not None:
                    before_file = self.tmp / f"{label}-before.md"
                    before_file.write_bytes(before)
                result, output = self.prepare(
                    project, data, before=before_file, env=env
                )
                self.assert_rejected(result, output)

    def test_unsafe_target_paths_are_rejected(self):
        project, data = self.standard()
        (project / "link.md").symlink_to(TARGET)
        (project / "linkdir").symlink_to("docs")
        original = self.original_state(project, data)
        for target in (
            "",
            ".",
            "./CLAUDE.md",
            "../project/CLAUDE.md",
            str(project / TARGET),
            "CLAUDE.md/",
            "missing.md",
            "docs",
            "link.md",
            "linkdir/guide.md",
            ".git/config",
        ):
            with self.subTest(target=target):
                result, output = self.prepare(project, data, file=target)
                self.assert_rejected(result, output)
        self.assertEqual(self.original_state(project, data), original)

    def test_unsafe_shared_data_is_rejected(self):
        project, _ = self.standard()
        outside = self.tmp / "outside.txt"
        outside.write_bytes(b"outside\n")
        cases = {
            "symlink": lambda root: (root / "link.csv").symlink_to(outside),
            "fifo": lambda root: os.mkfifo(root / "pipe"),
            "git internals": lambda root: write_files(
                root, {".git/config": b"[core]\n"}
            ),
            "selected instruction": lambda root: write_files(
                root, {TARGET: b"shadow\n"}
            ),
            "instruction case alias": lambda root: write_files(
                root, {"claude.md": b"x\n"}
            ),
            "excluded path": lambda root: write_files(
                root, {"notes/purpose.json": b"{}\n"}
            ),
            "excluded ancestor": lambda root: write_files(root, {"notes": b"file\n"}),
            "directory collision": lambda root: write_files(root, {"docs": b"file\n"}),
            "file ancestor collision": lambda root: write_files(
                root, {"run.sh/x": b"x\n"}
            ),
            "case collision": lambda root: write_files(root, {"Docs/guide.md": b"x\n"}),
            "empty": lambda root: None,
        }
        for label, build in cases.items():
            with self.subTest(label):
                data = self.tmp / ("data-" + label.replace(" ", "-"))
                data.mkdir()
                if label != "empty":
                    write_files(data, {"data/records.csv": b"id\n1\n"})
                build(data)
                result, output = self.prepare(project, data, exclude=PRIVATE)
                self.assert_rejected(result, output)
        real = self.folder("real-data", SHARED)
        (self.tmp / "data-link").symlink_to(real)
        result, output = self.prepare(project, self.tmp / "data-link", exclude=PRIVATE)
        self.assert_rejected(result, output)

    def test_shared_data_cannot_replace_nested_instruction_ancestry(self):
        target = "skills/demo/SKILL.md"
        project = self.git_project(
            "nested", {target: BEFORE, "skills/demo/ref.md": b"ref\n"}, {target: AFTER}
        )
        for label, shared in (
            ("ancestor file", {"skills": b"file\n"}),
            ("instruction as directory", {target + "/x": b"x\n"}),
        ):
            with self.subTest(label):
                data = self.folder("data-" + label.replace(" ", "-"), shared)
                result, output = self.prepare(project, data, file=target)
                self.assert_rejected(result, output)
        data = self.folder("data-ok", {"skills/demo/fixture.json": b"{}\n"})
        stage = self.staged(project, data, file=target)
        archived = self.archive_files(stage / "project")
        self.assertEqual(archived[target], (BEFORE, False))
        self.assertEqual(archived["skills/demo/fixture.json"], (b"{}\n", False))

    def test_unsafe_project_inputs_are_rejected(self):
        data = self.folder("data", SHARED)
        before = self.tmp / "before.md"
        before.write_bytes(BEFORE)
        linked = self.git_project("linked", {**COMMITTED, "alias.md": b""})
        (linked / "alias.md").unlink()
        (linked / "alias.md").symlink_to(TARGET)
        self.git(linked, "add", "alias.md")
        self.git(linked, "commit", "-qm", "Synthetic symlink")
        submodule = self.git_project("submodule")
        head = self.git(submodule, "rev-parse", "HEAD").decode().strip()
        self.git(
            submodule,
            "update-index",
            "--add",
            "--cacheinfo",
            f"160000,{head},vendor/lib",
        )
        self.git(submodule, "commit", "-qm", "Synthetic gitlink")
        folder_link = self.folder("folder-link", {TARGET: AFTER})
        (folder_link / "alias.md").symlink_to(TARGET)
        folder_fifo = self.folder("folder-fifo", {TARGET: AFTER})
        os.mkfifo(folder_fifo / "pipe")
        nested_git = self.folder(
            "nested-git", {TARGET: AFTER, "vendor/.git/HEAD": b"ref\n"}
        )
        cases = (
            ("tracked symlink", linked, None, TARGET),
            ("submodule", submodule, None, TARGET),
            ("folder symlink", folder_link, before, TARGET),
            ("folder fifo", folder_fifo, before, TARGET),
            ("nested git", nested_git, before, TARGET),
            ("repository subdirectory", self.git_project(), None, "docs/guide.md"),
        )
        for label, project, before_file, target in cases:
            with self.subTest(label):
                if label == "repository subdirectory":
                    project, target = project / "docs", "guide.md"
                    (project / target).write_bytes(b"changed\n")
                result, output = self.prepare(
                    project, data, file=target, before=before_file
                )
                self.assert_rejected(result, output)

    def test_output_location_must_be_new_and_outside_inputs(self):
        project, data = self.standard()
        existing = self.tmp / "existing"
        existing.mkdir()
        (existing / "keep.txt").write_bytes(b"keep\n")
        dangling = self.tmp / "dangling"
        dangling.symlink_to(self.tmp / "nowhere")
        original = self.original_state(project, data)
        for label, output in (
            ("inside project", project / "stage"),
            ("inside data", data / "stage"),
            ("missing parent", self.tmp / "missing" / "stage"),
        ):
            with self.subTest(label):
                result, _ = self.prepare(project, data, output=output, exclude=PRIVATE)
                self.assert_rejected(result, output)
        for label, output in (("existing", existing), ("dangling symlink", dangling)):
            with self.subTest(label):
                entries = sorted(self.tmp.iterdir())
                result, _ = self.prepare(project, data, output=output, exclude=PRIVATE)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(sorted(self.tmp.iterdir()), entries)
        self.assertEqual([path.name for path in existing.iterdir()], ["keep.txt"])
        self.assertEqual((existing / "keep.txt").read_bytes(), b"keep\n")
        self.assertTrue(dangling.is_symlink())
        self.assertEqual(self.original_state(project, data), original)

        inside = project / "shared"
        write_files(inside, SHARED)
        result, output = self.prepare(project, inside)
        self.assert_rejected(result, output)
        result, output = self.prepare(project, self.tmp)
        self.assert_rejected(result, output)

    def test_output_containment_rejects_case_aliases(self):
        project, data = self.standard()
        original = self.original_state(project, data)
        for root in (project, data):
            alias = root.with_name(root.name.swapcase())
            if not alias.exists() or not alias.samefile(root):
                self.skipTest("requires a case-insensitive filesystem")
            result, output = self.prepare(
                project, data, output=alias / "stage", exclude=PRIVATE
            )
            self.assert_rejected(result, output)
        self.assertEqual(self.original_state(project, data), original)

    def test_exclusions_remove_private_context_but_never_the_instruction(self):
        project, data = self.standard()
        stage = self.staged(project, data, exclude=["notes"])
        self.assertEqual(self.archive_files(stage / "project"), BASELINE)
        for exclude in (
            [TARGET],
            ["../notes"],
            ["/notes"],
            ["notes/../CLAUDE.md"],
            ["."],
        ):
            with self.subTest(exclude=exclude):
                result, output = self.prepare(project, data, exclude=exclude)
                self.assert_rejected(result, output)
        alias = self.folder("alias-data", {"Notes/answer.md": b"Synthetic answer.\n"})
        result, output = self.prepare(project, alias, exclude=["notes"])
        self.assert_rejected(result, output)

    def test_verify_rejects_changes_after_freeze(self):
        def edit(name, data):
            return lambda stage: (stage / "project" / name).write_bytes(data)

        def commit(stage):
            self.git(stage / "project", "commit", "-q", "--allow-empty", "-m", "later")

        def attributes(stage):
            info = stage / "project/.git/info"
            info.mkdir(parents=True, exist_ok=True)
            (info / "attributes").write_text("data/** export-ignore\n")

        tampers = {
            "shared content": edit("data/records.csv", b"id\n9\n"),
            "shared mode": lambda stage: (stage / "project/data/records.csv").chmod(
                0o755
            ),
            "shared removed": lambda stage: (stage / "project/data/tool.sh").unlink(),
            "instruction": edit(TARGET, b"# Different After\n"),
            "extra file": edit("extra.txt", b"extra\n"),
            "new commit": commit,
            "archive attributes": attributes,
            "worktree redirect": lambda stage: self.git(
                stage / "project", "config", "core.worktree", str(self.tmp)
            ),
            "before copy": lambda stage: (stage / "before").write_bytes(b"tampered\n"),
            "before copy removed": lambda stage: (stage / "before").unlink(),
            "freeze record removed": lambda stage: (stage / "freeze.json").unlink(),
        }
        project, data = self.standard()
        for label, tamper in tampers.items():
            with self.subTest(label):
                stage = self.staged(project, data, exclude=PRIVATE)
                self.assertEqual(self.verify(stage).returncode, 0)
                tamper(stage)
                self.assertNotEqual(self.verify(stage).returncode, 0)
        self.assertNotEqual(self.verify(self.tmp / "no-stage").returncode, 0)

    def test_verify_rejects_changed_absent_before(self):
        committed = {name: data for name, data in COMMITTED.items() if name != TARGET}
        project = self.git_project(committed=committed)
        data = self.folder("data", SHARED)
        self.store_entry(project / TARGET, "20260101-000000-ABSENT", b"", 1000)

        def marker_dir(stage):
            return (
                stage
                / "home/baselines"
                / encoded((stage / "project").resolve() / TARGET)
            )

        tampers = {
            "marker removed": lambda stage: next(marker_dir(stage).iterdir()).unlink(),
            "newer baseline": lambda stage: (
                marker_dir(stage) / "20990101-000000-1"
            ).write_bytes(BEFORE),
            "before copy added": lambda stage: (stage / "before").write_bytes(BEFORE),
            "instruction committed": lambda stage: (
                self.git(stage / "project", "add", "-f", TARGET),
                self.git(stage / "project", "commit", "-qm", "later"),
            ),
        }
        for label, tamper in tampers.items():
            with self.subTest(label):
                stage = self.staged(project, data, exclude=PRIVATE)
                self.assertNotIn(TARGET, self.archive_files(stage / "project"))
                self.assertEqual(self.verify(stage).returncode, 0)
                tamper(stage)
                self.assertNotEqual(self.verify(stage).returncode, 0)


FAKE_HOST = r"""
import json, os, shlex, subprocess, sys, tempfile
from pathlib import Path

host, args = sys.argv[1], sys.argv[2:]


def option(name):
    return args[args.index(name) + 1] if name in args else None


def record(kind, model):
    entry = {"host": host, "kind": kind, "model": model, "cwd": os.getcwd(),
             "trial": os.environ.get("BEHAVIOR_DIFF_TRIAL")}
    with open(os.environ["FAKE_HOST_LOG"], "a", encoding="utf-8") as log:
        log.write(json.dumps(entry) + "\n")


def project_files():
    # Read what is on disk: the runner's trial commit omits gitignored files.
    files = []
    for current, dirs, names in os.walk("."):
        if current == ".":
            dirs[:] = [name for name in dirs if name != ".git"]
        for name in names:
            path = Path(current, name)
            name = path.as_posix().removeprefix("./")
            files.append((name, path.read_text(encoding="utf-8")))
    return sorted(files)


def emit(event):
    sys.stdout.write(json.dumps(event) + "\n")


def nested_comparison():
    runner = os.environ.get("FAKE_NESTED_RUNNER")
    if not runner:
        return
    # Exercise real nested runner allocation, not just echo its environment.
    with tempfile.TemporaryDirectory(dir=Path.cwd().parent) as temporary:
        root = Path(temporary)
        project = root / "project"
        project.mkdir()
        (project / "CLAUDE.md").write_text("Synthetic new rule.\n")
        before = root / "before.md"
        before.write_text("Synthetic old rule.\n")
        env = dict(os.environ)
        del env["FAKE_NESTED_RUNNER"]
        env["FAKE_HOST_LOG"] = str(root / "nested-host.jsonl")
        subprocess.run(
            ["bash", runner, "--file", "CLAUDE.md", "--before-file", str(before),
             "--task", "Read the rules.", "--agent", host, "--model", "synthetic",
             "--extract-model", "synthetic", "--fast"],
            cwd=project, env=env, check=True, capture_output=True, timeout=120)


def claude_trial():
    nested_comparison()
    record("trial", option("--model"))
    emit({"type": "system", "subtype": "init", "session_id": "synthetic",
          "model": option("--model")})
    files = project_files()
    for number, (name, text) in enumerate(files, 1):
        call = f"toolu_synthetic_{number}"
        emit({"type": "assistant", "message": {"role": "assistant", "content": [
            {"type": "tool_use", "id": call, "name": "Read",
             "input": {"file_path": name}}]}})
        emit({"type": "user", "message": {"role": "user", "content": [
            {"type": "tool_result", "tool_use_id": call, "content": text}]}})
    answer = f"Synthetic answer after reading {len(files)} files."
    emit({"type": "assistant", "message": {"role": "assistant", "content": [
        {"type": "text", "text": answer}]}})
    emit({"type": "result", "subtype": "success", "is_error": False,
          "result": answer})


def codex_trial():
    nested_comparison()
    record("trial", option("-m"))
    emit({"type": "thread.started", "thread_id": "synthetic"})
    emit({"type": "turn.started"})
    files = project_files()
    for number, (name, text) in enumerate(files, 1):
        command = "/bin/bash -lc " + shlex.quote("cat " + shlex.quote(name))
        emit({"type": "item.completed", "item": {
            "id": f"item_{number}", "type": "command_execution",
            "command": command, "aggregated_output": text, "exit_code": 0,
            "status": "completed"}})
    emit({"type": "item.completed", "item": {
        "id": "item_final", "type": "agent_message",
        "text": f"Synthetic answer after reading {len(files)} files."}})
    emit({"type": "turn.completed", "usage": {
        "input_tokens": 0, "cached_input_tokens": 0, "output_tokens": 0}})


def main():
    if host == "claude":
        if "--output-format" in args:
            claude_trial()
            return 0
        record("extract", option("--model"))
        sys.stdout.write("Synthetic extraction reply; intentionally not JSON.\n")
        return 0
    if args[:1] == ["exec"] and "--json" in args:
        codex_trial()
        return 0
    if args[:1] == ["exec"] and "-o" in args:
        sys.stdin.read()
        record("extract", option("-m"))
        Path(option("-o")).write_text('{"synthetic": "malformed', encoding="utf-8")
        return 0
    sys.stderr.write("fake codex: unexpected invocation\n")
    return 9


raise SystemExit(main())
"""


class RunnerSmokeTests(Fixtures, unittest.TestCase):
    """Manual: the shipped runner and adapters consume a prepared stage."""

    enabled = False

    @classmethod
    def setUpClass(cls):
        if not cls.enabled:
            raise unittest.SkipTest("manual smoke; pass --runner-smoke")

    def setUp(self):
        super().setUp()
        fakebin = self.tmp / "fakebin"
        fakebin.mkdir()
        host = self.tmp / "fake_host.py"
        host.write_text(FAKE_HOST, encoding="utf-8")
        for name in ("claude", "codex"):
            launcher = fakebin / name
            launcher.write_text(
                f'#!/bin/sh\nexec "{sys.executable}" "{host}" {name} "$@"\n'
            )
            launcher.chmod(0o755)
        opener = fakebin / "open"  # the runner opens the report on success
        opener.write_text("#!/bin/sh\nexit 0\n")
        opener.chmod(0o755)
        self.log = self.tmp / "fake-host.jsonl"
        self.env["PATH"] = f"{fakebin}{os.pathsep}{self.env['PATH']}"
        self.env["FAKE_HOST_LOG"] = str(self.log)
        context = self.tmp / "context"
        context.mkdir()
        self.source = context / "source.json"
        self.source.write_text(json.dumps(SOURCE), encoding="utf-8")

    def run_stage(self, stage):
        result = subprocess.run(
            [sys.executable, str(HELPER), "verify", str(stage), "--json"],
            env=self.env,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        handoff = json.loads(result.stdout)
        result = subprocess.run(
            [str(RUNNER), *handoff["argv"]],
            cwd=handoff["project"],
            env={**self.env, "BEHAVIOR_DIFF_HOME": handoff["home"]},
            capture_output=True,
            text=True,
            timeout=900,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        verified = self.verify(stage)
        self.assertEqual(verified.returncode, 0, verified.stdout + verified.stderr)

    def check_run(self, stage, agent, trials, before, purpose):
        runs = sorted((stage / "home/runs").iterdir())
        self.assertEqual(len(runs), 1)
        run = runs[0]
        report = (run / "report.html").read_text(encoding="utf-8")
        config_text = (run / "config.json").read_text(encoding="utf-8")
        config = json.loads(config_text)
        self.assertEqual(config["source"], SOURCE)
        expected_purpose = subprocess.run(
            [sys.executable, str(SCRIPTS / "purpose.py"), str(purpose)],
            env=self.env,
            check=True,
            capture_output=True,
            text=True,
        ).stdout
        self.assertEqual(config["purpose"], json.loads(expected_purpose))
        self.assertEqual(config["scenario_record"], SCENARIO)
        scratch = self.git(stage / "project", "rev-parse", "HEAD").decode().strip()
        for text in (config_text, report):
            self.assertNotIn(scratch, text)
            self.assertNotIn(f"commit {scratch[:7]}", text)
        if before is not None:
            self.assertEqual(config["before_label"], str(stage / "before"))

        common = {
            name: content
            for name, content in self.archive_files(stage / "project").items()
            if name != TARGET
        }
        self.assertEqual(
            common["data/records.csv"], normalized(SHARED)["data/records.csv"]
        )
        self.assertEqual(common["data/tool.sh"], normalized(SHARED)["data/tool.sh"])
        for private in PRIVATE:
            self.assertNotIn(private, common)
        for variant in ("before", "after"):
            for number in range(1, trials + 1):
                with self.subTest(trial=f"{variant}-{number}"):
                    trial = run / f"{variant}-{number}"
                    # The runner's trial commit uses `git add -A`, so gitignored
                    # shared files arrive on disk but not in that commit.
                    snapshot = self.working_files(trial / "project")
                    committed = self.archive_files(trial / "project")
                    self.assertLessEqual(committed.items(), snapshot.items())
                    self.assertEqual(committed.get(TARGET), snapshot.get(TARGET))
                    self.assertEqual(
                        {
                            name: content
                            for name, content in snapshot.items()
                            if name != TARGET
                        },
                        common,
                    )
                    expected = AFTER if variant == "after" else before
                    if expected is None:
                        self.assertNotIn(TARGET, snapshot)
                    else:
                        self.assertEqual(snapshot[TARGET][0], expected)
                    results, finals = trace_events(trial / "trace.jsonl")
                    self.assertEqual(
                        sorted(results),
                        sorted(data.decode() for data, _ in snapshot.values()),
                    )
                    self.assertTrue(any(finals))
        grades = (run / "grades.tsv").read_text().splitlines()
        self.assertEqual(len(grades), 2 * trials)
        self.assertTrue(all(line.split("\t")[1] == "REVIEW" for line in grades))
        for name in ("grading", "extraction", "rendering"):
            stage = json.loads((run / "stages" / f"{name}.json").read_text())
            self.assertEqual(stage["stage"], name)
            self.assertEqual(
                stage["state"], "failed" if name == "extraction" else "completed"
            )
        coordinator = json.loads((run / "coordinator-status.json").read_text())
        self.assertEqual(coordinator["phase"], "rendering")
        self.assertEqual(coordinator["report"]["state"], "available")
        self.assertEqual(
            json.loads((run / "status.json").read_text())["state"], "completed"
        )

        calls = [json.loads(line) for line in self.log.read_text().splitlines()]
        launched = [call for call in calls if call["kind"] == "trial"]
        extracted = [call for call in calls if call["kind"] == "extract"]
        self.assertEqual(len(launched), 2 * trials)
        self.assertTrue(extracted)
        self.assertTrue(all(call["host"] == agent for call in calls))
        for call in launched:
            self.assertEqual(call["model"], TRIAL_MODEL)
            self.assertEqual(call["trial"], "1")
            self.assertTrue(Path(call["cwd"]).resolve().is_relative_to(run))
        self.assertTrue(all(call["model"] == EXTRACT_MODEL for call in extracted))

    def smoke(self, agent, trials, before_file=None, absent=False):
        committed = COMMITTED
        if absent:
            committed = {
                name: data for name, data in COMMITTED.items() if name != TARGET
            }
        project = self.git_project(committed=committed)
        data = self.folder("data", SHARED)
        if absent:
            self.store_entry(project / TARGET, "20260101-000000-ABSENT", b"", 1000)
        original = self.original_state(project, data, self.store_home)
        descriptor = self.handoff_file(
            {
                "agent": agent,
                "model": TRIAL_MODEL,
                "extract_model": EXTRACT_MODEL,
                "fast": trials == 1,
            }
        )
        stage = self.staged(
            project, data, before=before_file, exclude=PRIVATE, handoff=descriptor
        )
        purpose = descriptor.parent / "purpose.json"
        self.run_stage(stage)
        before = (
            None if absent else (before_file.read_bytes() if before_file else BEFORE)
        )
        self.check_run(stage, agent, trials, before, purpose)
        self.assertEqual(self.original_state(project, data, self.store_home), original)

    def nested_smoke(self, agent):
        self.env["FAKE_NESTED_RUNNER"] = str(RUNNER)
        self.smoke(agent, 1)
        stage = self.tmp / "stage-1"
        (outer,) = (stage / "home/runs").iterdir()
        for side in ("before", "after"):
            trial = outer / f"{side}-1"
            (nested,) = (trial / "behavior-diff-home/runs").iterdir()
            self.assertTrue((nested / "report.html").is_file())
            self.assertEqual(
                (nested / "grades.tsv").read_text().splitlines(),
                ["before-1\tREVIEW\t-", "after-1\tREVIEW\t-"],
            )

    def test_claude_nested_comparisons_preserve_outer_evidence(self):
        self.nested_smoke("claude")

    def test_codex_nested_comparisons_preserve_outer_evidence(self):
        self.nested_smoke("codex")

    def test_unsafe_git_environment_blocks_runner_handoff(self):
        project, data = self.standard()
        stage = self.staged(project, data, exclude=PRIVATE)
        original = self.original_state(project, data)
        masked = self.tmp / "masked-gitconfig"
        masked.write_text(
            Path(self.env["GIT_CONFIG_GLOBAL"]).read_text()
            + "\n[tar]\n\tumask = 0111\n"
        )
        overrides = (
            {"GIT_INDEX_FILE": str(project / ".git/index")},
            {
                "GIT_CONFIG_COUNT": "1",
                "GIT_CONFIG_KEY_0": "core.worktree",
                "GIT_CONFIG_VALUE_0": str(project),
            },
            {"GIT_CONFIG_GLOBAL": str(masked)},
        )
        for override in overrides:
            with self.subTest(override=next(iter(override))):
                env = dict(self.env, **override, BEHAVIOR_DIFF_HOME=str(stage / "home"))
                result = subprocess.run(
                    [
                        "bash",
                        "-c",
                        '"$1" "$2" verify "$3" && cd "$3/project" && '
                        'bash "$4" --file CLAUDE.md --before-file "$3/before" '
                        '--task "Read the shared data." --agent claude '
                        "--model synthetic-trial-model --fast",
                        "staged-smoke",
                        sys.executable,
                        str(HELPER),
                        str(stage),
                        str(RUNNER),
                    ],
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                self.assertEqual(result.returncode, 2)
                self.assertFalse(self.log.exists(), "unsafe setup launched a host")
                self.assertFalse((stage / "home/runs").exists())
                self.assertEqual(self.original_state(project, data), original)

    def test_claude_three_by_three_head_baseline(self):
        self.smoke("claude", 3)

    def test_codex_three_by_three_head_baseline(self):
        self.smoke("codex", 3)

    def test_claude_fast_absent_before(self):
        self.smoke("claude", 1, absent=True)

    def test_codex_fast_explicit_before(self):
        literal = self.tmp / "CLAUDE.md-ABSENT"
        literal.write_bytes(EXPLICIT)
        self.smoke("codex", 1, before_file=literal)


def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--runner-smoke", action="store_true")
    options, remaining = parser.parse_known_args()
    RunnerSmokeTests.enabled = options.runner_smoke
    unittest.main(argv=[sys.argv[0], *remaining])


if __name__ == "__main__":
    main()
