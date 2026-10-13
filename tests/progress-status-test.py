#!/usr/bin/env python3
"""Synthetic progress writer, status reader, and owner-liveness contracts.

Every run directory, record, path, and owner process here is invented. No model
CLI runs; owners are local Bash, sleep, and test processes.
"""

import contextlib
import importlib.util
import json
import os
import signal
import stat
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / "plugin/skills/behavior-diff/scripts"
PROGRESS = SCRIPTS / "progress.py"
STATUS = SCRIPTS / "status.py"
OWNER_FIELDS = (
    "boot_id",
    "host",
    "machine_id",
    "pid",
    "pid_namespace",
    "process_start",
)
PREPARING = '{"phase":"preparing","state":"running"}'
FINISHED = '{"phase":"finished","state":"finished","exit_code":0,"final_result":true}'


def load_progress():
    spec = importlib.util.spec_from_file_location("progress", PROGRESS)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


progress = load_progress()


def timestamp(offset_seconds=0):
    moment = datetime.now(timezone.utc).replace(microsecond=0)
    return (moment + timedelta(seconds=offset_seconds)).strftime("%Y-%m-%dT%H:%M:%SZ")


def write_record(path, record):
    """Write a synthetic fixture directly, bypassing the shipped writer."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record), encoding="utf-8")


def run_record(**fields):
    record = {
        "schema_version": 1,
        "kind": "run",
        "started_at": timestamp(-300),
        "updated_at": timestamp(-5),
        "run_id": "diff-20261013-120000-Syn001",
        "project": "/synthetic/project",
        "target": "skills/example/SKILL.md",
        "agent": "claude",
        "model": "synthetic-model",
        "trials": 3,
        "phase": "running_trials",
        "state": "running",
        "report": {"state": "pending", "path": None},
    }
    record.update(fields)
    return record


def trial_record(**fields):
    record = {
        "schema_version": 1,
        "kind": "trial",
        "started_at": timestamp(-200),
        "updated_at": timestamp(-10),
        "ended_at": timestamp(-10),
        "phase": "finished",
        "state": "finished",
        "cli_exit_code": 0,
        "exit_code": 0,
        "final_result": True,
    }
    record.update(fields)
    if record["state"] == "running":
        record.pop("ended_at", None)
    return record


def live_identity():
    return progress.owner_identity(os.getpid())


def ended_identity():
    process = subprocess.Popen(["sleep", "30"])
    identity = progress.owner_identity(process.pid)
    process.kill()
    process.wait()
    return identity


def run_cli(script, *arguments, env=None, cwd=None, timeout=60):
    return subprocess.run(
        [sys.executable, str(script), *[str(argument) for argument in arguments]],
        capture_output=True,
        text=True,
        env=env,
        cwd=cwd,
        timeout=timeout,
        check=False,
    )


def status_json(run_dir, **options):
    result = run_cli(STATUS, run_dir, "--json", **options)
    assert result.returncode == 0, (result.returncode, result.stderr)
    assert "\x1b" not in result.stdout
    return json.loads(result.stdout)


def status_human(run_dir, **options):
    result = run_cli(STATUS, run_dir, **options)
    assert result.returncode == 0, (result.returncode, result.stderr)
    assert "\x1b" not in result.stdout, result.stdout
    return result.stdout


def trial_rows(view):
    variants = ("before", "after")
    return {row["trial"]: row for name in variants for row in view["trials"][name]}


def eventually(check, timeout=20):
    deadline = time.monotonic() + timeout
    while True:
        result = check()
        if result:
            return result
        if time.monotonic() > deadline:
            raise AssertionError("condition was not reached before the deadline")
        time.sleep(0.1)


def recorded_owner(path, kind):
    record = progress.read_record(path, kind)
    return record.get("owner") if record else None


@contextlib.contextmanager
def owner_shell(path, kind, fields):
    """Start a Bash owner that records itself with --owner and then stays alive."""
    script = '"$1" "$2" "$3" "$4" "$5" --owner || exit 1\nsleep 60\n'
    process = subprocess.Popen(
        ["bash", "-c", script, "owner", sys.executable, PROGRESS, path, kind]
        + [json.dumps(fields)],
        start_new_session=True,
    )
    try:
        owner = eventually(lambda: recorded_owner(path, kind))
        assert owner["pid"] == process.pid, (owner, process.pid)
        yield process
    finally:
        if process.poll() is None:
            with contextlib.suppress(ProcessLookupError):
                os.killpg(process.pid, signal.SIGKILL)
        process.wait()


@contextlib.contextmanager
def sandbox():
    with tempfile.TemporaryDirectory(prefix="progress-status-test-") as directory:
        yield Path(directory) / "synthetic runs"


def assert_writer_contract():
    with sandbox() as root:
        trial_dir = root / "diff-synthetic" / "before-1"
        trial_dir.mkdir(parents=True)
        path = trial_dir / "status.json"
        result = run_cli(PROGRESS, path, "trial", PREPARING)
        assert result.returncode == 0 and result.stdout == "", result
        assert stat.S_IMODE(path.stat().st_mode) == 0o600, oct(path.stat().st_mode)
        first = json.loads(path.read_text())
        assert first["schema_version"] == 1 and first["kind"] == "trial", first
        assert "ended_at" not in first and "owner" not in first, first

        result = run_cli(PROGRESS, path, "trial", '{"phase":"running"}')
        assert result.returncode == 0, result.stderr
        merged = json.loads(path.read_text())
        assert merged["started_at"] == first["started_at"], merged
        assert (merged["phase"], merged["state"]) == ("running", "running"), merged

        finished = {
            "phase": "finished",
            "state": "finished",
            "cli_exit_code": 3,
            "exit_code": 0,
            "final_result": True,
        }
        result = run_cli(PROGRESS, path, "trial", json.dumps(finished))
        assert result.returncode == 0, result.stderr
        final = json.loads(path.read_text())
        assert final["ended_at"] >= final["started_at"], final
        assert sorted(os.listdir(trial_dir)) == ["status.json"], os.listdir(trial_dir)

        before = path.read_bytes()
        rejected = [
            ('{"task":"synthetic secret prompt"}', "'task'"),
            ('{"stderr":"synthetic stderr"}', "'stderr'"),
            ('{"started_at":"2026-01-01T00:00:00Z"}', "writer-managed"),
            ('{"owner":null}', "writer-managed"),
            ('{"state":"passed"}', "'state'"),
            ('{"exit_code":256}', "'exit_code'"),
            ('{"final_result":"yes"}', "'final_result'"),
        ]
        for fields, expected in rejected:
            result = run_cli(PROGRESS, path, "trial", fields)
            assert result.returncode == 1, (fields, result)
            assert result.stderr.startswith("behavior-diff progress: "), result.stderr
            assert expected in result.stderr, (fields, result.stderr)
            assert "synthetic secret" not in result.stderr, result.stderr
            assert "Traceback" not in result.stderr, result.stderr
            assert path.read_bytes() == before, fields

        result = run_cli(PROGRESS, path, "run", '{"phase":"preparing"}')
        assert result.returncode == 1 and "expected 'run'" in result.stderr, result

        for fields in ("[1]", "not json", "NaN"):
            result = run_cli(PROGRESS, path, "trial", fields)
            assert result.returncode == 2, (fields, result)
            assert path.read_bytes() == before, fields

        missing = root / "absent directory" / "status.json"
        result = run_cli(PROGRESS, missing, "trial", PREPARING)
        assert result.returncode == 1, result
        assert "cannot write progress metadata" in result.stderr, result.stderr
        assert "Traceback" not in result.stderr and not missing.parent.exists()

        corrupt = root / "corrupt" / "status.json"
        corrupt.parent.mkdir(parents=True)
        corrupt.write_text("{synthetic corrupt")
        result = run_cli(PROGRESS, corrupt, "trial", PREPARING)
        assert result.returncode == 1 and "not valid JSON" in result.stderr, result
        assert corrupt.read_text() == "{synthetic corrupt"

        assessment = root / "diff-synthetic" / "assessment-status.json"
        record = progress.update(
            assessment, "assessment", {"state": "running"}, owner_pid=os.getpid()
        )
        assert record["owner"]["pid"] == os.getpid(), record
        assert tuple(sorted(record["owner"])) == OWNER_FIELDS, record["owner"]
        for call in (
            lambda: progress.update(
                assessment, "assessment", {}, owner=True, owner_pid=os.getpid()
            ),
            lambda: progress.owner_identity(0),
            lambda: progress.update(assessment, "assessment", {"reason": "Free text"}),
        ):
            try:
                call()
            except progress.ProgressError:
                pass
            else:
                raise AssertionError("Invalid progress request was accepted.")
        with patch.object(progress.os, "getppid", return_value=1):
            record = progress.update(assessment, "assessment", {}, owner=True)
        assert record["owner"]["pid"] == 1
        assert record["owner"]["process_start"] is None
        assert (
            progress.observe_owner(record["owner"], progress.host_identity())[0]
            == "uncertain"
        )


def assert_owner_is_the_calling_subshell():
    with sandbox() as root:
        run_dir = root / "diff-subshell"
        trial = run_dir / "before-1" / "status.json"
        trial.parent.mkdir(parents=True)
        write_record(
            run_dir / "status.json",
            run_record(trials=1, owner=live_identity()),
        )
        script = (
            '( "$1" "$2" "$3" trial \'{"phase":"running","state":"running"}\' --owner'
            " || exit 1\n"
            "  sleep 60 ) &\n"
            'printf \'%s %s\\n\' "$$" "$!"\n'
            "wait\n"
            "sleep 60\n"
        )
        shell = subprocess.Popen(
            ["bash", "-c", script, "runner", sys.executable, PROGRESS, trial],
            stdout=subprocess.PIPE,
            text=True,
            start_new_session=True,
        )
        try:
            top, child = (int(value) for value in shell.stdout.readline().split())
            owner = eventually(lambda: recorded_owner(trial, "trial"))
            assert owner["pid"] == child and owner["pid"] != top, (owner, top, child)
            row = trial_rows(status_json(run_dir))["before-1"]
            assert row["observed"] == "running", row
            assert row["owner"]["observation"] == "alive", row

            os.kill(child, signal.SIGKILL)

            def stopped():
                row = trial_rows(status_json(run_dir))["before-1"]
                return row if row["observed"] == "stopped" else None

            row = eventually(stopped)
            assert row["problems"] == ["worker_lost"], row
            assert row["owner"]["observation"] == "ended", row
        finally:
            with contextlib.suppress(ProcessLookupError):
                os.killpg(shell.pid, signal.SIGKILL)
            shell.wait()
            shell.stdout.close()


def assert_atomic_updates_under_concurrent_reads():
    with sandbox() as root:
        path = root / "diff-concurrent" / "after-1" / "status.json"
        path.parent.mkdir(parents=True)
        writer = subprocess.Popen(
            [
                sys.executable,
                "-c",
                "import sys\n"
                "sys.path.insert(0, sys.argv[1])\n"
                "import progress\n"
                "for index in range(400):\n"
                "    progress.update(sys.argv[2], 'trial', {'phase': 'running',"
                " 'state': 'running', 'cli_exit_code': index % 2})\n",
                str(SCRIPTS),
                str(path),
            ]
        )
        reads = 0
        while writer.poll() is None:
            record = progress.read_record(path, "trial")
            if record is not None:
                assert record["phase"] == "running", record
                reads += 1
        assert writer.wait() == 0
        assert reads > 0
        assert sorted(os.listdir(path.parent)) == ["status.json"]


def assert_counts_and_problems():
    with sandbox() as root:
        run_dir = root / "diff-counts"
        live = live_identity()
        write_record(run_dir / "status.json", run_record(owner=live))
        trials = {
            "before-1": trial_record(),
            "before-2": trial_record(cli_exit_code=1),
            "before-3": trial_record(phase="preparing", state="failed", exit_code=1),
            "after-1": trial_record(final_result=False),
            "after-2": trial_record(phase="normalizing", state="failed", exit_code=5),
            "after-3": trial_record(
                phase="running", state="running", cli_exit_code=None, owner=live
            ),
        }
        for name, record in trials.items():
            write_record(run_dir / name / "status.json", record)
        (run_dir / "after-3" / "trace.jsonl").write_text("{}\n")

        other_directory = root / "elsewhere"
        other_directory.mkdir()
        view = status_json(run_dir, cwd=other_directory)
        assert view["status"] == "running" and view["ended"] is False, view
        assert view["run"]["owner"]["observation"] == "alive", view["run"]
        counts = view["counts"]
        assert (counts["before"]["finished"], counts["before"]["failed"]) == (2, 1)
        assert (counts["after"]["finished"], counts["after"]["failed"]) == (1, 1)
        assert counts["after"]["running"] == 1 and counts["after"]["total"] == 3
        problems = {name: row["problems"] for name, row in trial_rows(view).items()}
        assert problems == {
            "before-1": [],
            "before-2": ["cli_exit_nonzero"],
            "before-3": ["preparation_failed"],
            "after-1": ["no_final_result"],
            "after-2": ["normalization_failed"],
            "after-3": [],
        }, problems
        assert trial_rows(view)["after-3"]["last_output_at"] is not None
        assert view["surviving_workers"] == [] and view["uncertain_workers"] == []

        text = status_human(run_dir, cwd=other_directory)
        for expected in (
            "Behavior Diff · skills/example/SKILL.md",
            "Status      Running",
            "Stage       Running trials",
            "Before      2 of 3 finished · 1 failed",
            "After       1 of 3 finished · 1 running · 1 failed",
            "Remaining   After trial 3 (running; last output",
            "Before trial 2: agent CLI exited 1",
            "Before trial 3: preparation failed",
            "After trial 1: no final result",
            "After trial 2: trace normalization failed",
            "Assessment  Not ready yet",
            "Report      Not ready yet",
        ):
            assert expected in text, (expected, text)
        assert "pass" not in text.lower() and "%" not in text, text


def assert_pending_and_quiet_workers():
    with sandbox() as root:
        run_dir = root / "diff-preparing"
        write_record(
            run_dir / "status.json",
            run_record(phase="preparing", owner=live_identity()),
        )
        view = status_json(run_dir)
        observed = {row["observed"] for row in trial_rows(view).values()}
        assert observed == {"pending"}, view
        assert all(row["problems"] == [] for row in trial_rows(view).values())
        assert "0 of 3 finished · 3 not started yet" in status_human(run_dir)

        quiet = root / "diff-codex"
        live = live_identity()
        write_record(
            quiet / "status.json", run_record(agent="codex", trials=1, owner=live)
        )
        write_record(
            quiet / "before-1" / "status.json",
            trial_record(phase="running", state="running", owner=live),
        )
        row = trial_rows(status_json(quiet))["before-1"]
        assert row["observed"] == "running" and row["problems"] == [], row
        assert row["last_output_at"] is None, row
        assert "Before trial 1 (running; no output yet)" in status_human(quiet)
        (quiet / "before-1" / "codex-raw.jsonl").write_text("{}\n")
        row = trial_rows(status_json(quiet))["before-1"]
        assert row["last_output_at"] is not None and row["problems"] == [], row
        after = trial_rows(status_json(quiet))["after-1"]
        assert after["observed"] == "pending", after


def assert_assessment_and_report_outcomes():
    with sandbox() as root:
        run_dir = root / "diff-fallback"
        report = run_dir / "report.html"
        write_record(
            run_dir / "status.json",
            run_record(
                trials=1,
                phase="finished",
                state="completed",
                exit_code=0,
                ended_at=timestamp(-1),
                report={"state": "available", "path": str(report)},
            ),
        )
        for name in ("before-1", "after-1"):
            write_record(run_dir / name / "status.json", trial_record())
        write_record(
            run_dir / "assessment-status.json",
            {
                "schema_version": 1,
                "kind": "assessment",
                "started_at": timestamp(-60),
                "updated_at": timestamp(-50),
                "ended_at": timestamp(-50),
                "state": "skipped",
                "reason": "insufficient_trials",
            },
        )
        report.write_text("<p>synthetic</p>")
        view = status_json(run_dir)
        assert view["status"] == "completed" and view["ended"] is True, view
        assert view["report"] == {
            "state": "available",
            "path": str(report),
            "file_present": True,
        }, view["report"]
        assert view["assessment"]["state"] == "skipped", view["assessment"]
        text = status_human(run_dir)
        assert "Assessment  Skipped (insufficient trials)" in text, text
        assert f"Report      {report}" in text and "Stage       Finished" in text, text

        report.unlink()
        assert "(file missing)" in status_human(run_dir)

        failed = root / "diff-render-failed"
        write_record(
            failed / "status.json",
            run_record(
                trials=1,
                phase="rendering",
                state="failed",
                exit_code=1,
                ended_at=timestamp(-1),
                report={"state": "failed", "path": None},
            ),
        )
        write_record(
            failed / "assessment-status.json",
            {
                "schema_version": 1,
                "kind": "assessment",
                "started_at": timestamp(-60),
                "updated_at": timestamp(-50),
                "state": "running",
                "reason": None,
                "owner": ended_identity(),
            },
        )
        view = status_json(failed)
        assert view["status"] == "failed" and view["report"]["state"] == "failed"
        assert view["assessment"]["owner"]["observation"] == "ended", view
        text = status_human(failed)
        for expected in (
            "Status      Failed (exit 1)",
            "Stage       Rendering report",
            "Report      Rendering failed",
            "Assessment  No outcome recorded (stopped while running)",
            "Before      0 of 1 finished · 1 no record",
            "Before trial 1: no trial record",
        ):
            assert expected in text, (expected, text)


def assert_owner_liveness():
    with sandbox() as root:
        local = progress.host_identity()
        assert local["boot_id"] is not None, "This platform needs a boot identity."
        live = live_identity()
        cases = [
            ("ended", ended_identity(), "owner_lost", {"process_exited", "pid_reused"}),
            (
                "reused",
                dict(live, process_start="ps:Thu Jan 1 00:00:00 1970"),
                "owner_lost",
                {"pid_reused"},
            ),
            (
                "other-host",
                dict(live, boot_id="synthetic-boot", machine_id="synthetic-host"),
                "uncertain",
                {"other_host_or_boot"},
            ),
            (
                "no-start",
                dict(live, process_start=None),
                "uncertain",
                {"start_unrecorded"},
            ),
            (
                "namespace",
                dict(live, pid_namespace="pid:[1]"),
                "uncertain",
                {"other_pid_namespace"},
            ),
            ("no-owner", None, "uncertain", {"owner_not_recorded"}),
        ]
        restarted = dict(live, boot_id="synthetic-earlier-boot")
        if local["machine_id"] is not None:
            cases.append(("restarted", restarted, "owner_lost", {"host_restarted"}))
        else:
            cases.append(("restarted", restarted, "uncertain", {"other_host_or_boot"}))
        for name, owner, status, reasons in cases:
            run_dir = root / f"diff-{name}"
            record = run_record(trials=1)
            if owner is not None:
                record["owner"] = owner
            write_record(run_dir / "status.json", record)
            view = status_json(run_dir)
            assert view["status"] == status, (name, view)
            assert view["run"]["owner"]["reason"] in reasons, (name, view["run"])
            assert view["ended"] is (status == "owner_lost"), (name, view)
            text = status_human(run_dir)
            if status == "uncertain":
                assert "Status      Status uncertain (" in text, text
                assert "last update" in text, text
            else:
                assert "Stopped without a final record" in text, text
            assert "Running" not in text.split("Stage")[0], text


def assert_workers_outlive_controller():
    with sandbox() as root:
        live = live_identity()
        ended = ended_identity()
        elsewhere = dict(live, boot_id="synthetic-boot", machine_id="synthetic-host")
        trials = {
            "before-1": trial_record(),
            "before-2": trial_record(phase="running", state="running", owner=live),
            "after-1": trial_record(phase="running", state="running", owner=elsewhere),
            "after-2": trial_record(phase="running", state="running", owner=ended),
        }
        controllers = {
            "diff-lost": run_record(trials=2, owner=ended),
            "diff-interrupted": run_record(
                trials=2,
                state="interrupted",
                exit_code=130,
                ended_at=timestamp(-2),
            ),
        }
        for run_name, record in controllers.items():
            run_dir = root / run_name
            write_record(run_dir / "status.json", record)
            for name, trial in trials.items():
                write_record(run_dir / name / "status.json", trial)
            view = status_json(run_dir)
            assert view["ended"] is True, view
            assert view["surviving_workers"] == ["before-2"], view
            assert view["uncertain_workers"] == ["after-1"], view
            rows = trial_rows(view)
            assert rows["after-2"]["observed"] == "stopped", rows["after-2"]
            assert rows["after-2"]["problems"] == ["worker_lost"], rows["after-2"]
            text = status_human(run_dir)
            for expected in (
                "Still alive Before trial 2 (running",
                "Uncertain   After trial 1 (liveness uncertain",
                "After trial 2: worker ended without a final record",
            ):
                assert expected in text, (expected, text)
        interrupted = status_json(root / "diff-interrupted")
        assert interrupted["status"] == "interrupted", interrupted


def assert_invalid_and_legacy_metadata():
    with sandbox() as root:
        legacy = root / "diff-20250101-000000"
        legacy.mkdir(parents=True)
        (legacy / "config.json").write_text("{}")
        (legacy / "report.html").write_text("<p>synthetic</p>")
        view = status_json(legacy)
        assert view["progress"] == "unavailable" and view["status"] == "unavailable"
        assert view["report_file"] == str(legacy / "report.html"), view
        assert "run" not in view and "trials" not in view, view
        assert "Unavailable: this run has no progress metadata" in status_human(legacy)

        empty = root / "empty"
        empty.mkdir()
        result = run_cli(STATUS, empty)
        assert result.returncode == 1 and result.stdout == "", result
        assert "no progress metadata or Behavior Diff run files" in result.stderr
        result = run_cli(STATUS, root / "absent")
        assert result.returncode == 1 and "is not a directory" in result.stderr

        valid = json.dumps(run_record(trials=1))
        cases = {
            "corrupt": ("{synthetic", "invalid", "not valid JSON"),
            "unsupported": (
                json.dumps(dict(run_record(), schema_version=2)),
                "unsupported",
                "unsupported schema version 2",
            ),
            "oversized": (valid + " " * (70 * 1024), "too_large", "exceeds"),
            "unknown-field": (
                json.dumps(dict(run_record(), task="synthetic task text")),
                "invalid",
                "'task'",
            ),
            "wrong-kind": (
                json.dumps(dict(run_record(), kind="trial")),
                "invalid",
                "unsupported trial progress field",
            ),
        }
        for name, (content, problem, detail) in cases.items():
            run_dir = root / name
            run_dir.mkdir()
            (run_dir / "status.json").write_text(content)
            result = run_cli(STATUS, run_dir, "--json")
            assert result.returncode == 1, (name, result)
            view = json.loads(result.stdout)
            assert view["status"] == "invalid", (name, view)
            assert view["diagnostics"][0]["problem"] == problem, (name, view)
            assert detail in view["diagnostics"][0]["detail"], (name, view)
            assert "synthetic task text" not in result.stdout + result.stderr
            human = run_cli(STATUS, run_dir)
            assert human.returncode == 1 and human.stdout == "", (name, human)
            assert detail in human.stderr, (name, human.stderr)

        linked = root / "linked"
        linked.mkdir()
        (root / "elsewhere.json").write_text(valid)
        (linked / "status.json").symlink_to(root / "elsewhere.json")
        result = run_cli(STATUS, linked)
        assert result.returncode == 1 and "symbolic link" in result.stderr, result

        fifo = root / "fifo"
        fifo.mkdir()
        os.mkfifo(fifo / "status.json")
        result = run_cli(STATUS, fifo, timeout=20)
        assert result.returncode == 1 and "not a regular file" in result.stderr, result

        partial = root / "diff-partial"
        write_record(
            partial / "status.json", run_record(trials=1, owner=live_identity())
        )
        (partial / "before-1").mkdir()
        (partial / "before-1" / "status.json").write_text("{synthetic")
        view = status_json(partial)
        rows = trial_rows(view)
        assert rows["before-1"]["observed"] == "invalid", rows
        assert rows["before-1"]["problems"] == ["record_invalid"], rows
        assert view["diagnostics"][0]["record"] == "before-1/status.json", view
        text = status_human(partial)
        assert "Warning     before-1/status.json: progress metadata is not" in text


def assert_terminal_safe_text():
    with sandbox() as root:
        run_dir = root / "diff-escapes"
        write_record(
            run_dir / "status.json",
            run_record(
                trials=1,
                target="skills/\x1b[31mred\u202e/SKILL.md",
                project="/synthetic/\x07bell",
                owner=live_identity(),
            ),
        )
        text = status_human(run_dir)
        assert "\x1b" not in text and "\x07" not in text and "\u202e" not in text
        assert "\\x1b[31mred\\u202e" in text, text
        result = run_cli(STATUS, run_dir, "--json")
        assert "\x1b" not in result.stdout and "\\u001b" in result.stdout, result


def assert_list_and_active():
    with sandbox() as root:
        home = root / "home with spaces"
        runs = home / "runs"
        live = live_identity()
        records = {
            "diff-20261013-120005-Active": run_record(
                run_id="diff-20261013-120005-Active", owner=live
            ),
            "diff-20261013-120004-Done": run_record(
                run_id="diff-20261013-120004-Done",
                state="completed",
                phase="finished",
                exit_code=0,
            ),
            "diff-20261013-120003-Unsure": run_record(
                run_id="diff-20261013-120003-Unsure",
                owner=dict(live, boot_id="synthetic-boot", machine_id="synthetic-host"),
            ),
        }
        for name, record in records.items():
            write_record(runs / name / "status.json", record)
        (runs / "diff-20261013-120002-Legacy").mkdir()
        (runs / "diff-20261013-120002-Legacy" / "config.json").write_text("{}")
        (runs / "diff-20261013-120001-Corrupt").mkdir()
        (runs / "diff-20261013-120001-Corrupt" / "status.json").write_text("{")
        (runs / "diff-20261013-120009-Link").symlink_to(
            runs / "diff-20261013-120005-Active"
        )
        (runs / "notes.txt").write_text("synthetic")
        env = dict(os.environ, BEHAVIOR_DIFF_HOME=str(home))
        other_directory = root / "elsewhere"
        other_directory.mkdir()

        result = run_cli(STATUS, "--list", "--json", env=env, cwd=other_directory)
        assert result.returncode == 0, result.stderr
        listing = json.loads(result.stdout)
        assert listing["runs_root"] == str(runs), listing
        summary = [
            (row["run_id"], row["status"], row["activity"]) for row in listing["runs"]
        ]
        assert summary == [
            ("diff-20261013-120005-Active", "running", "confirmed"),
            ("diff-20261013-120004-Done", "completed", "none"),
            ("diff-20261013-120003-Unsure", "uncertain", "uncertain"),
            ("diff-20261013-120002-Legacy", "unavailable", "none"),
            ("diff-20261013-120001-Corrupt", "invalid", "uncertain"),
        ], summary
        active = listing["runs"][0]
        assert (active["project"], active["target"]) == (
            "/synthetic/project",
            "skills/example/SKILL.md",
        ), active
        expected_start = records["diff-20261013-120005-Active"]["started_at"]
        assert active["started_at"] == expected_start, active

        result = run_cli(STATUS, "--list", "--active", "--json", env=env)
        names = [row["run_id"] for row in json.loads(result.stdout)["runs"]]
        assert names == [
            "diff-20261013-120005-Active",
            "diff-20261013-120003-Unsure",
            "diff-20261013-120001-Corrupt",
        ], names

        result = run_cli(STATUS, "--list", env=env)
        assert result.returncode == 0 and "\x1b" not in result.stdout, result
        for expected in (
            f"Runs in {runs}",
            "diff-20261013-120005-Active",
            "Status uncertain",
            "Unreadable status",
            "Details: python3 ",
        ):
            assert expected in result.stdout, (expected, result.stdout)

        default_home = root / "default home"
        write_record(
            default_home / ".behavior-diff" / "runs" / "diff-default" / "status.json",
            run_record(run_id="diff-default", state="completed", phase="finished"),
        )
        env = dict(os.environ, HOME=str(default_home), BEHAVIOR_DIFF_HOME="")
        result = run_cli(STATUS, "--list", "--json", env=env)
        assert [row["run_id"] for row in json.loads(result.stdout)["runs"]] == [
            "diff-default"
        ], result.stdout

        env = dict(os.environ, BEHAVIOR_DIFF_HOME=str(root / "absent home"))
        result = run_cli(STATUS, "--list", "--active", env=env)
        assert result.returncode == 0, result
        assert result.stdout.startswith("No active or uncertain runs in "), result


def assert_assessment_outlives_controller():
    with sandbox() as root:
        home = root / "assessment home"
        dead = ended_identity()
        live = live_identity()
        cases = (
            ("alive", live, "running", "confirmed"),
            ("uncertain", dict(live, process_start=None), "running", "uncertain"),
            ("ended", dead, "running", "none"),
            ("available", live, "available", "none"),
        )
        for name, owner, state, _ in cases:
            run_dir = home / "runs" / f"diff-{name}"
            write_record(
                run_dir / "status.json",
                run_record(
                    run_id=f"diff-{name}",
                    trials=1,
                    phase="comparing_evidence",
                    owner=dead,
                ),
            )
            for side in ("before", "after"):
                write_record(run_dir / f"{side}-1/status.json", trial_record())
            write_record(
                run_dir / "assessment-status.json",
                {
                    "schema_version": 1,
                    "kind": "assessment",
                    "started_at": timestamp(-10),
                    "updated_at": timestamp(),
                    "state": state,
                    "owner": owner,
                },
            )
        env = dict(os.environ, BEHAVIOR_DIFF_HOME=str(home))
        result = run_cli(STATUS, "--list", "--json", env=env)
        assert result.returncode == 0, result.stderr
        rows = {row["run_id"]: row for row in json.loads(result.stdout)["runs"]}
        for name, _, _, activity in cases:
            row = rows[f"diff-{name}"]
            assert row["status"] == "owner_lost", row
            assert row["activity"] == activity, row
            assert row["assessment_activity"] == activity, row
        result = run_cli(STATUS, "--list", "--active", "--json", env=env)
        assert result.returncode == 0, result.stderr
        assert {row["run_id"] for row in json.loads(result.stdout)["runs"]} == {
            "diff-alive",
            "diff-uncertain",
        }


def assert_usage_errors():
    with sandbox() as root:
        root.mkdir()
        for arguments in (
            (),
            ("--active",),
            ("--list", root),
            (root, "--json", "--watch"),
            ("--list", "--watch"),
            (root, "--active"),
        ):
            result = run_cli(STATUS, *arguments)
            assert result.returncode == 2, (arguments, result)


def start_watch(run_dir, cwd):
    return subprocess.Popen(
        [sys.executable, str(STATUS), str(run_dir), "--watch"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=cwd,
    )


def assert_watch():
    with sandbox() as root:
        other_directory = root / "elsewhere"
        other_directory.mkdir(parents=True)
        run_dir = root / "diff-watch"
        live = live_identity()
        write_record(run_dir / "status.json", run_record(trials=1, owner=live))
        for name in ("before-1", "after-1"):
            write_record(
                run_dir / name / "status.json",
                trial_record(phase="running", state="running", owner=live),
            )
        watcher = start_watch(run_dir, other_directory)
        assert watcher.stdout.readline().startswith("Behavior Diff · "), "no frame"
        before_trial = run_dir / "before-1" / "status.json"
        update = run_cli(PROGRESS, before_trial, "trial", FINISHED)
        assert update.returncode == 0, update.stderr
        time.sleep(3)
        after_trial = run_dir / "after-1" / "status.json"
        update = run_cli(PROGRESS, after_trial, "trial", FINISHED)
        assert update.returncode == 0, update.stderr
        update = run_cli(
            PROGRESS,
            run_dir / "status.json",
            "run",
            '{"phase":"finished","state":"completed","exit_code":0}',
        )
        assert update.returncode == 0, update.stderr
        output, errors = watcher.communicate(timeout=30)
        assert watcher.returncode == 0, (watcher.returncode, errors)
        output = "Behavior Diff · " + output
        assert "\x1b" not in output, output
        frames = output.count("Behavior Diff · ")
        assert 2 <= frames <= 4, output
        assert output.rstrip().split("Behavior Diff · ")[-1].count("Completed") == 1

        lost = root / "diff-watch-lost"
        (lost / "before-1").mkdir(parents=True)
        with owner_shell(
            lost / "status.json",
            "run",
            {
                "run_id": "diff-watch-lost",
                "trials": 1,
                "phase": "running_trials",
                "state": "running",
            },
        ) as owner:
            watcher = start_watch(lost, other_directory)
            assert watcher.stdout.readline().startswith("Behavior Diff · ")
            os.killpg(owner.pid, signal.SIGKILL)
            output, errors = watcher.communicate(timeout=30)
        assert watcher.returncode == 0, (watcher.returncode, errors)
        assert "Stopped without a final record" in output, output

        stopped = root / "diff-watch-interrupt"
        (stopped / "before-1").mkdir(parents=True)
        with owner_shell(
            stopped / "status.json",
            "run",
            {
                "run_id": "diff-watch-interrupt",
                "trials": 1,
                "phase": "running_trials",
                "state": "running",
            },
        ) as owner:
            before = sorted(os.listdir(stopped)), (stopped / "status.json").read_bytes()
            watcher = start_watch(stopped, other_directory)
            assert watcher.stdout.readline().startswith("Behavior Diff · ")
            watcher.send_signal(signal.SIGINT)
            output, errors = watcher.communicate(timeout=30)
            assert watcher.returncode == 130, (watcher.returncode, errors)
            assert "Traceback" not in errors, errors
            assert owner.poll() is None, "Closing watch stopped the run owner."
            after = sorted(os.listdir(stopped)), (stopped / "status.json").read_bytes()
            assert after == before, "Watch changed the run directory."
            assert status_json(stopped)["status"] == "running"


def main():
    assert_writer_contract()
    assert_owner_is_the_calling_subshell()
    assert_atomic_updates_under_concurrent_reads()
    assert_counts_and_problems()
    assert_pending_and_quiet_workers()
    assert_assessment_and_report_outcomes()
    assert_owner_liveness()
    assert_workers_outlive_controller()
    assert_invalid_and_legacy_metadata()
    assert_terminal_safe_text()
    assert_list_and_active()
    assert_assessment_outlives_controller()
    assert_usage_errors()
    assert_watch()
    print("Progress status contracts passed.")


if __name__ == "__main__":
    main()
