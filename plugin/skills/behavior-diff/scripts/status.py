#!/usr/bin/env python3
"""Show Behavior Diff run progress without changing the run.

  status.py RUN_DIR [--json | --watch]
  status.py --list [--active] [--json]

Exit status 0 means status was read, not that the comparison succeeded.
The run, each trial worker, and the assessment have separate progress records
(see progress.py); this reader combines them with its own liveness
observations and never writes to a run directory.
"""

import argparse
import json
import os
import shlex
import stat
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import progress

WATCH_INTERVAL_SECONDS = 2
VARIANTS = ("before", "after")
# run-trial.sh writes these streams while each agent runs. Codex, Pi, and OMP
# traces are normalized only after their CLI exits, so trace.jsonl is not live.
LIVE_STREAMS = {
    "claude": "trace.jsonl",
    "codex": "codex-raw.jsonl",
    "pi": "pi-raw.jsonl",
    "omp": "omp-raw.jsonl",
}
RUN_FILES = ("config.json", "task.md", "report.html")
LIVE_STATUSES = ("running", "uncertain")
ENDED_STATUSES = ("completed", "failed", "interrupted", "owner_lost")
ALIVE_TRIALS = ("preparing", "running", "normalizing")
UNFINISHED_TRIALS = ("pending",) + ALIVE_TRIALS + ("uncertain",)
OBSERVED_TRIALS = (
    "finished",
    "pending",
    "not_started",
    "preparing",
    "running",
    "normalizing",
    "uncertain",
    "failed",
    "interrupted",
    "stopped",
    "missing",
    "invalid",
)

PHASE_LABELS = {
    "preparing": "Preparing",
    "running_trials": "Running trials",
    "checking_results": "Checking trial results",
    "comparing_evidence": "Comparing evidence",
    "rendering": "Rendering report",
    "finished": "Finished",
}
TRIAL_LABELS = {
    "finished": "finished",
    "pending": "not started yet",
    "not_started": "not started",
    "preparing": "preparing",
    "running": "running",
    "normalizing": "normalizing trace",
    "uncertain": "liveness uncertain",
    "failed": "failed",
    "interrupted": "interrupted",
    "stopped": "worker lost",
    "missing": "no record",
    "invalid": "unreadable record",
}
STATUS_LABELS = {
    "running": "Running",
    "completed": "Completed",
    "failed": "Failed",
    "interrupted": "Interrupted",
    "owner_lost": "Stopped without a final record",
    "uncertain": "Status uncertain",
    "unavailable": "No progress metadata",
    "invalid": "Unreadable status",
}
OWNER_REASONS = {
    "process_exited": "owner process ended",
    "pid_reused": "owner process ended; its PID now belongs to another process",
    "host_restarted": "host restarted since the last update",
    "owner_not_recorded": "owner process not recorded",
    "boot_unknown": "host boot identity unavailable",
    "other_host_or_boot": "recorded on another host or before a restart",
    "other_pid_namespace": "recorded in another process namespace",
    "start_unrecorded": "owner process start not recorded",
    "process_unreadable": "owner process details unreadable",
}


def diagnostic(record, error):
    return {"record": record, "problem": error.code, "detail": str(error)}


def epoch_timestamp(seconds):
    return progress.format_timestamp(datetime.fromtimestamp(seconds, timezone.utc))


def owner_summary(owner, observation, reason):
    return {
        "pid": owner["pid"] if owner else None,
        "host": owner["host"] if owner else None,
        "observation": observation,
        "reason": reason,
    }


def run_status(run, local_host):
    """Return the observed run status and its owner observation."""
    owner = run.get("owner")
    if run["state"] != "running":
        return run["state"], owner_summary(owner, "not_checked", "final_state_recorded")
    observation, reason = progress.observe_owner(owner, local_host)
    status = {"alive": "running", "ended": "owner_lost"}.get(observation, "uncertain")
    return status, owner_summary(owner, observation, reason)


def last_output(trial_dir, agent):
    """Return the raw stream's modification time; it is not a health signal."""
    stream = LIVE_STREAMS.get(agent)
    if stream is None:
        return None
    try:
        info = os.stat(trial_dir / stream, follow_symlinks=False)
    except OSError:
        return None
    return epoch_timestamp(info.st_mtime) if stat.S_ISREG(info.st_mode) else None


def trial_problems(record, observed):
    problems = []
    state = record["state"]
    if state == "failed":
        problems.append(
            {
                "preparing": "preparation_failed",
                "normalizing": "normalization_failed",
            }.get(record["phase"], "worker_failed")
        )
    elif state == "interrupted":
        problems.append("interrupted")
    if observed == "stopped":
        problems.append("worker_lost")
    if record.get("cli_exit_code") not in (None, 0):
        problems.append("cli_exit_nonzero")
    if state != "failed" and record.get("exit_code") not in (None, 0):
        problems.append("worker_exit_nonzero")
    if record.get("final_result") is False:
        problems.append("no_final_result")
    return problems


def trial_view(run_dir, variant, index, run, live, local_host, diagnostics):
    name = f"{variant}-{index}"
    trial_dir = run_dir / name
    row = {
        "trial": name,
        "variant": variant,
        "index": index,
        "record": "present",
        "phase": None,
        "state": None,
        "cli_exit_code": None,
        "exit_code": None,
        "final_result": None,
        "started_at": None,
        "updated_at": None,
        "ended_at": None,
        "owner": None,
        "last_output_at": None,
    }
    try:
        record = progress.read_record(trial_dir / progress.TRIAL_RECORD, "trial")
    except progress.ProgressError as error:
        diagnostics.append(diagnostic(f"{name}/{progress.TRIAL_RECORD}", error))
        row.update(record="invalid", observed="invalid", problems=["record_invalid"])
        return row
    if record is None:
        # Workers record themselves; a later trial may not have started yet.
        if live and run["phase"] in ("preparing", "running_trials"):
            observed = "pending"
        elif run["phase"] == "preparing":
            observed = "not_started"
        else:
            observed = "missing"
        row.update(
            record="missing",
            observed=observed,
            problems=["record_missing"] if observed == "missing" else [],
        )
        return row
    for key in row:
        if key in record and key != "owner":
            row[key] = record[key]
    if record["state"] == "running":
        owner = record.get("owner")
        observation, reason = progress.observe_owner(owner, local_host)
        row["owner"] = owner_summary(owner, observation, reason)
        if observation == "alive":
            # A record still marked running is unfinished even if its phase advanced.
            phase = record["phase"]
            observed = phase if phase in ALIVE_TRIALS else "running"
        else:
            observed = "stopped" if observation == "ended" else "uncertain"
        row["last_output_at"] = last_output(trial_dir, run.get("agent"))
    else:
        observed = record["state"]
    row["observed"] = observed
    row["problems"] = trial_problems(record, observed)
    return row


def assessment_view(run_dir, status, local_host, diagnostics):
    view = {
        "record": "present",
        "state": None,
        "reason": None,
        "updated_at": None,
        "owner": None,
    }
    try:
        record = progress.read_record(
            run_dir / progress.ASSESSMENT_RECORD, "assessment"
        )
    except progress.ProgressError as error:
        diagnostics.append(diagnostic(progress.ASSESSMENT_RECORD, error))
        view["record"] = "invalid"
        return view
    if record is None:
        view["record"] = "missing"
        return view
    view.update(
        state=record["state"],
        reason=record.get("reason"),
        updated_at=record["updated_at"],
    )
    if record["state"] == "running":
        owner = record.get("owner")
        if owner is None:
            # Without its own owner, the assessment can only follow the run.
            observation = {"running": "alive", "uncertain": "uncertain"}.get(
                status, "ended"
            )
            view["owner"] = owner_summary(None, observation, "follows_run")
        else:
            observation, reason = progress.observe_owner(owner, local_host)
            view["owner"] = owner_summary(owner, observation, reason)
    return view


def report_view(run_dir, run):
    report = run.get("report") or {}
    path = report.get("path")
    present = None
    if path:
        candidate = Path(path)
        present = (candidate if candidate.is_absolute() else run_dir / path).is_file()
    return {"state": report.get("state"), "path": path, "file_present": present}


def build_view(run_dir, local_host, now):
    """Combine one run's records with current observations; never writes."""
    view = {
        "schema_version": progress.SCHEMA_VERSION,
        "observed_at": progress.format_timestamp(now),
        "run_dir": str(run_dir),
        "diagnostics": [],
    }
    try:
        run = progress.read_record(run_dir / progress.RUN_RECORD, "run")
    except progress.ProgressError as error:
        view["diagnostics"].append(diagnostic(progress.RUN_RECORD, error))
        view.update(progress="invalid", status="invalid", ended=None)
        return view
    if run is None:
        report = run_dir / "report.html"
        view.update(
            progress="unavailable",
            status="unavailable",
            ended=None,
            report_file=str(report) if report.is_file() else None,
        )
        if not any((run_dir / name).is_file() for name in RUN_FILES):
            view["diagnostics"].append(
                {
                    "record": progress.RUN_RECORD,
                    "problem": "not_a_run",
                    "detail": "no progress metadata or Behavior Diff run files",
                }
            )
        return view

    status, owner = run_status(run, local_host)
    live = status in LIVE_STATUSES
    trials = {
        variant: [
            trial_view(
                run_dir, variant, index, run, live, local_host, view["diagnostics"]
            )
            for index in range(1, run["trials"] + 1)
        ]
        for variant in VARIANTS
    }
    rows = [row for variant in VARIANTS for row in trials[variant]]
    counts = {}
    for variant in VARIANTS:
        tally = dict.fromkeys(OBSERVED_TRIALS, 0)
        for row in trials[variant]:
            tally[row["observed"]] += 1
        tally["total"] = len(trials[variant])
        counts[variant] = tally
    started = progress.parse_timestamp(run["started_at"])
    end = progress.parse_timestamp(run["ended_at"]) if "ended_at" in run else now
    summary = {
        key: run.get(key)
        for key in (
            "run_id",
            "project",
            "target",
            "agent",
            "model",
            "trials",
            "phase",
            "state",
            "exit_code",
            "started_at",
            "updated_at",
            "ended_at",
        )
    }
    summary["owner"] = owner
    view.update(
        progress="available",
        status=status,
        ended=status in ENDED_STATUSES,
        run=summary,
        elapsed_seconds=max(0, int((end - started).total_seconds())),
        trials=trials,
        counts=counts,
        # An ended runner does not prove its background workers ended.
        surviving_workers=[
            row["trial"] for row in rows if not live and row["observed"] in ALIVE_TRIALS
        ],
        uncertain_workers=[
            row["trial"] for row in rows if row["observed"] == "uncertain"
        ],
        assessment=assessment_view(run_dir, status, local_host, view["diagnostics"]),
        report=report_view(run_dir, run),
    )
    return view


def duration(seconds):
    seconds = max(0, int(seconds))
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours:
        return f"{hours}h {minutes}m"
    if minutes:
        return f"{minutes}m {seconds}s"
    return f"{seconds}s"


def moment(timestamp, now):
    when = progress.parse_timestamp(timestamp)
    age = duration((now - when).total_seconds())
    return f"{when.strftime('%Y-%m-%d %H:%M:%S')} UTC ({age} ago)"


def trial_name(row):
    return f"{row['variant'].capitalize()} trial {row['index']}"


def trial_detail(row, now):
    detail = TRIAL_LABELS[row["observed"]]
    if row["observed"] in ("running", "uncertain", "stopped"):
        if row["last_output_at"]:
            age = progress.parse_timestamp(row["last_output_at"])
            detail += f"; last output {duration((now - age).total_seconds())} ago"
        elif row["observed"] == "running":
            detail += "; no output yet"
    return f"{trial_name(row)} ({detail})"


def problem_text(problem, row):
    if problem == "worker_failed":
        stage = "after" if row["phase"] == "finished" else "during"
        exit_code = row["exit_code"]
        suffix = f" (exit {exit_code})" if exit_code is not None else ""
        return f"worker failed {stage} the agent run{suffix}"
    return {
        "preparation_failed": "preparation failed",
        "normalization_failed": "trace normalization failed",
        "interrupted": "interrupted",
        "worker_lost": "worker ended without a final record",
        "cli_exit_nonzero": f"agent CLI exited {row['cli_exit_code']}",
        "worker_exit_nonzero": f"worker exited {row['exit_code']}",
        "no_final_result": "no final result",
        "record_invalid": "trial record unreadable",
        "record_missing": "no trial record",
    }[problem]


def status_text(view, now):
    status = view["status"]
    run = view["run"]
    label = STATUS_LABELS[status]
    if status == "failed" and run["exit_code"] is not None:
        return f"{label} (exit {run['exit_code']})"
    if status == "owner_lost":
        return f"{label} ({OWNER_REASONS[run['owner']['reason']]})"
    if status == "uncertain":
        reason = OWNER_REASONS[run["owner"]["reason"]]
        return f"{label} ({reason}); last update {moment(run['updated_at'], now)}"
    return label


def assessment_text(assessment, live):
    state = assessment["state"]
    if assessment["record"] == "invalid":
        return "Unreadable record"
    if state is None:
        return "Not ready yet" if live else "No outcome recorded"
    if state == "running":
        observation = assessment["owner"]["observation"]
        if observation == "alive":
            return "In progress"
        if observation == "ended":
            return "No outcome recorded (stopped while running)"
        return "Recorded as running (liveness uncertain)"
    label = {"available": "Available", "skipped": "Skipped", "failed": "Failed"}[state]
    reason = assessment["reason"]
    return f"{label} ({reason.replace('_', ' ')})" if reason else label


def report_text(report, live):
    if report["state"] == "available":
        text = progress.printable(report["path"]) if report["path"] else "Available"
        return text + (" (file missing)" if report["file_present"] is False else "")
    if report["state"] == "failed":
        return "Rendering failed"
    return "Not ready yet" if live else "Not produced"


def render_human(view, now):
    lines = []

    def add(label, *values):
        for position, value in enumerate(values):
            heading = label if position == 0 else ""
            lines.append(f"{heading:<12}{value}".rstrip())

    if view["progress"] == "unavailable":
        name = progress.printable(Path(view["run_dir"]).name)
        lines.append(f"Behavior Diff · {name}")
        add("Progress", "Unavailable: this run has no progress metadata")
        report = view["report_file"]
        add("Report", progress.printable(report) if report else "Not found")
        return "\n".join(lines) + "\n"

    run = view["run"]
    live = view["status"] in LIVE_STATUSES
    rows = [row for variant in VARIANTS for row in view["trials"][variant]]

    def details(observed):
        return [trial_detail(row, now) for row in rows if row["observed"] in observed]

    title = progress.printable(run["target"] or run["run_id"])
    lines.append(f"Behavior Diff · {title}")
    add("Run", progress.printable(run["run_id"]))
    if run["project"]:
        add("Project", progress.printable(run["project"]))
    identity = [part for part in (run["agent"], run["model"]) if part]
    if identity:
        add("Agent", " · ".join(progress.printable(part) for part in identity))
    add("Status", status_text(view, now))
    add("Stage", PHASE_LABELS[run["phase"]])
    for variant in VARIANTS:
        counts = view["counts"][variant]
        parts = [f"{counts['finished']} of {counts['total']} finished"]
        parts += [
            f"{counts[state]} {TRIAL_LABELS[state]}"
            for state in OBSERVED_TRIALS
            if state != "finished" and counts[state]
        ]
        add(variant.capitalize(), " · ".join(parts))
    if live:
        add("Remaining", *details(UNFINISHED_TRIALS))
    else:
        add("Still alive", *details(ALIVE_TRIALS))
        add("Uncertain", *details(("uncertain",)))
    add(
        "Problems",
        *[
            f"{trial_name(row)}: {problem_text(problem, row)}"
            for row in rows
            for problem in row["problems"]
        ],
    )
    add("Assessment", assessment_text(view["assessment"], live))
    add("Report", report_text(view["report"], live))
    add("Elapsed", duration(view["elapsed_seconds"]))
    add("Updated", moment(run["updated_at"], now))
    add(
        "Warning",
        *[
            f"{item['record']}: {progress.printable(item['detail'])}"
            for item in view["diagnostics"]
        ],
    )
    return "\n".join(lines) + "\n"


def unreadable(view):
    """Return True when RUN_DIR has no readable Behavior Diff status."""
    return view["status"] == "invalid" or bool(
        view["progress"] == "unavailable" and view["diagnostics"]
    )


def report_unreadable(view):
    for item in view["diagnostics"]:
        path = Path(view["run_dir"]) / item["record"]
        print(
            f"behavior-diff status: {progress.printable(path)}: "
            f"{progress.printable(item['detail'])}",
            file=sys.stderr,
        )


def write_json(document):
    sys.stdout.write(json.dumps(document, ensure_ascii=True, indent=2, sort_keys=True))
    sys.stdout.write("\n")


def meaningful(view):
    """Drop values that change on every refresh without a recorded change."""
    stable = {
        key: value
        for key, value in view.items()
        if key not in ("observed_at", "elapsed_seconds")
    }
    if "trials" in stable:
        stable["trials"] = {
            variant: [
                {key: value for key, value in row.items() if key != "last_output_at"}
                for row in rows
            ]
            for variant, rows in stable["trials"].items()
        }
    return json.dumps(stable, sort_keys=True)


def watch(run_dir, local_host):
    """Redraw on meaningful changes until the run ends or its owner is lost."""
    stream = sys.stdout
    in_place = stream.isatty() and os.environ.get("TERM", "dumb") != "dumb"
    previous = None
    while True:
        now = progress.utc_now()
        view = build_view(run_dir, local_host, now)
        if unreadable(view):
            report_unreadable(view)
            return 1
        signature = meaningful(view)
        if in_place or signature != previous:
            text = render_human(view, now)
            if in_place:
                stream.write("\x1b[H\x1b[J" + text)
            else:
                stream.write(text if previous is None else "\n" + text)
            stream.flush()
            previous = signature
        if view["ended"] or view["progress"] == "unavailable":
            return 0
        time.sleep(WATCH_INTERVAL_SECONDS)


def list_row(run_dir, view):
    run = view.get("run") or {}
    surviving = view.get("surviving_workers", [])
    uncertain = view.get("uncertain_workers", [])
    assessment_owner = (view.get("assessment") or {}).get("owner") or {}
    assessment_activity = {
        "alive": "confirmed",
        "uncertain": "uncertain",
    }.get(assessment_owner.get("observation"), "none")
    if view["status"] == "running" or surviving or assessment_activity == "confirmed":
        activity = "confirmed"
    elif (
        view["status"] in ("uncertain", "invalid")
        or uncertain
        or assessment_activity == "uncertain"
    ):
        # Unreadable or unverifiable runs may still be live; never hide them.
        activity = "uncertain"
    else:
        activity = "none"
    return {
        "run_id": run.get("run_id") or run_dir.name,
        "run_dir": str(run_dir),
        "project": run.get("project"),
        "target": run.get("target"),
        "started_at": run.get("started_at"),
        "phase": run.get("phase"),
        "status": view["status"],
        "activity": activity,
        "surviving_workers": surviving,
        "uncertain_workers": uncertain,
        "assessment_activity": assessment_activity,
        "diagnostics": view["diagnostics"],
    }


def list_runs(runs_root, local_host, now, active_only):
    try:
        with os.scandir(runs_root) as iterator:
            names = [
                entry.name for entry in iterator if entry.is_dir(follow_symlinks=False)
            ]
    except FileNotFoundError:
        names = []
    rows = []
    for name in sorted(names, reverse=True):
        run_dir = runs_root / name
        row = list_row(run_dir, build_view(run_dir, local_host, now))
        if not active_only or row["activity"] != "none":
            rows.append(row)
    return rows


def render_list(runs_root, rows, active_only):
    if not rows:
        qualifier = "active or uncertain " if active_only else ""
        return f"No {qualifier}runs in {progress.printable(runs_root)}\n"
    table = [("RUN", "STATUS", "STARTED", "TARGET", "PROJECT")]
    for row in rows:
        status = STATUS_LABELS[row["status"]]
        if row["surviving_workers"]:
            status += f" ({len(row['surviving_workers'])} workers alive)"
        elif row["uncertain_workers"] and row["status"] != "uncertain":
            status += f" ({len(row['uncertain_workers'])} workers uncertain)"
        if row["assessment_activity"] == "confirmed":
            status += " (assessment running)"
        elif row["assessment_activity"] == "uncertain":
            status += " (assessment uncertain)"
        started = row["started_at"]
        table.append(
            (
                progress.printable(row["run_id"]),
                status,
                started.replace("T", " ").replace("Z", " UTC") if started else "-",
                progress.printable(row["target"] or "-"),
                progress.printable(row["project"] or "-"),
            )
        )
    widths = [max(len(line[column]) for line in table) for column in range(4)]
    lines = [f"Runs in {progress.printable(runs_root)}"]
    for line in table:
        cells = [cell.ljust(width) for cell, width in zip(line, widths)] + [line[4]]
        lines.append("  ".join(cells).rstrip())
    script = shlex.quote(str(Path(__file__).resolve()))
    lines.append(f"Details: python3 {script} {shlex.quote(str(runs_root))}/RUN")
    return "\n".join(lines) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Show Behavior Diff run progress without changing the run."
    )
    parser.add_argument("run_dir", nargs="?", type=Path, metavar="RUN_DIR")
    parser.add_argument(
        "--list",
        action="store_true",
        help="list runs under BEHAVIOR_DIFF_HOME (default ~/.behavior-diff)",
    )
    parser.add_argument(
        "--active",
        action="store_true",
        help="with --list, keep runs that are active or whose activity is uncertain",
    )
    output = parser.add_mutually_exclusive_group()
    output.add_argument("--json", action="store_true", help="print JSON")
    output.add_argument(
        "--watch", action="store_true", help="redraw until the run ends"
    )
    args = parser.parse_args(argv)
    if args.list == (args.run_dir is not None):
        parser.error("pass either RUN_DIR or --list")
    if args.active and not args.list:
        parser.error("--active requires --list")
    if args.list and args.watch:
        parser.error("--watch requires RUN_DIR")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="backslashreplace")

    try:
        local_host = progress.host_identity()
        if args.list:
            home = os.environ.get("BEHAVIOR_DIFF_HOME") or str(
                Path.home() / ".behavior-diff"
            )
            runs_root = Path(os.path.abspath(home)) / "runs"
            now = progress.utc_now()
            try:
                rows = list_runs(runs_root, local_host, now, args.active)
            except OSError as error:
                location = progress.printable(runs_root)
                reason = error.strerror or error
                print(
                    f"behavior-diff status: cannot list {location}: {reason}",
                    file=sys.stderr,
                )
                return 1
            if args.json:
                write_json(
                    {
                        "schema_version": progress.SCHEMA_VERSION,
                        "observed_at": progress.format_timestamp(now),
                        "runs_root": str(runs_root),
                        "active_only": args.active,
                        "runs": rows,
                    }
                )
            else:
                sys.stdout.write(render_list(runs_root, rows, args.active))
            return 0

        run_dir = Path(os.path.abspath(args.run_dir))
        if not run_dir.is_dir():
            location = progress.printable(run_dir)
            print(
                f"behavior-diff status: {location} is not a directory",
                file=sys.stderr,
            )
            return 1
        if args.watch:
            return watch(run_dir, local_host)
        now = progress.utc_now()
        view = build_view(run_dir, local_host, now)
        if args.json:
            write_json(view)
        elif not unreadable(view):
            sys.stdout.write(render_human(view, now))
        if unreadable(view):
            report_unreadable(view)
            return 1
        return 0
    except KeyboardInterrupt:
        # Stops this observer only; the run has no channel back to it.
        return 130
    except BrokenPipeError:
        # A closed console stays closed without a traceback at shutdown.
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, sys.stdout.fileno())
        return 1


if __name__ == "__main__":
    sys.exit(main())
