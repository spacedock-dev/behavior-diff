#!/usr/bin/env python3
"""Atomically record Behavior Diff progress metadata and its owner process.

Usage: progress.py PATH KIND FIELDS_JSON [--owner]

Each record has exactly one producer, so a read-merge-replace update needs no
lock: the runner owns RUN_DIR/status.json, each trial worker owns
RUN_DIR/<before|after>-<n>/status.json, and the evidence extractor owns
RUN_DIR/assessment-status.json. status.py combines the records for readers.
Records hold operational metadata only: never task or purpose text, answers,
tool payloads, stderr content, credentials, or environment dumps.
"""

import argparse
import contextlib
import errno
import hashlib
import json
import os
import re
import socket
import stat
import subprocess
import sys
import tempfile
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

SCHEMA_VERSION = 1
MAX_RECORD_BYTES = 64 * 1024
MAX_TRIALS = 1000
RUN_RECORD = "status.json"
TRIAL_RECORD = "status.json"
ASSESSMENT_RECORD = "assessment-status.json"

RUN_PHASES = (
    "preparing",
    "running_trials",
    "checking_results",
    "comparing_evidence",
    "rendering",
    "finished",
)
RUN_STATES = ("running", "completed", "failed", "interrupted")
TRIAL_PHASES = ("preparing", "running", "normalizing", "finished")
TRIAL_STATES = ("running", "finished", "failed", "interrupted")
ASSESSMENT_STATES = ("running", "available", "skipped", "failed")
REPORT_STATES = ("pending", "available", "failed")
TERMINAL_STATES = {
    "run": ("completed", "failed", "interrupted"),
    "trial": ("finished", "failed", "interrupted"),
    "assessment": ("available", "skipped", "failed"),
}
WRITER_FIELDS = (
    "schema_version",
    "kind",
    "started_at",
    "updated_at",
    "ended_at",
    "owner",
)

_RUN_ID = re.compile(r"[A-Za-z0-9._-]+")
_REASON = re.compile(r"[a-z][a-z0-9_]*")
_FIELD_NAME = re.compile(r"[A-Za-z0-9_]{1,64}")
_TIMESTAMP = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z")
_TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
_PLATFORM_UUID = re.compile(r'"IOPlatformUUID" = "([^"]+)"')
_COMMAND_TIMEOUT_SECONDS = 5
_LINUX = sys.platform.startswith("linux")
_DARWIN = sys.platform == "darwin"


class ProgressError(Exception):
    """Progress metadata could not be validated, read, or written."""

    def __init__(self, message, code="invalid"):
        super().__init__(message)
        self.code = code


def utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0)


def format_timestamp(moment):
    return moment.astimezone(timezone.utc).strftime(_TIMESTAMP_FORMAT)


def parse_timestamp(text):
    return datetime.strptime(text, _TIMESTAMP_FORMAT).replace(tzinfo=timezone.utc)


def printable(text):
    """Escape control and format characters so metadata cannot drive a terminal."""
    return "".join(
        ascii(character)[1:-1]
        if unicodedata.category(character).startswith("C")
        or character in "\u2028\u2029"
        else character
        for character in str(text)
    )


def _text(limit, pattern=None, nullable=True):
    def check(value):
        if value is None:
            return nullable
        return (
            isinstance(value, str)
            and 0 < len(value) <= limit
            and (pattern is None or pattern.fullmatch(value) is not None)
        )

    return check


def _integer(low, high, nullable=True):
    def check(value):
        if value is None:
            return nullable
        return type(value) is int and low <= value <= high

    return check


def _choice(values, nullable=False):
    def check(value):
        if value is None:
            return nullable
        return isinstance(value, str) and value in values

    return check


def _boolean(value):
    return value is None or isinstance(value, bool)


def _timestamp(value):
    if not isinstance(value, str) or _TIMESTAMP.fullmatch(value) is None:
        return False
    try:
        parse_timestamp(value)
    except ValueError:
        return False
    return True


def _report(value):
    return (
        isinstance(value, dict)
        and "state" in value
        and set(value) <= {"state", "path"}
        and _choice(REPORT_STATES)(value["state"])
        and _text(4096)(value.get("path"))
    )


_OWNER_FIELDS = {
    "pid": _integer(1, 2**31 - 1, nullable=False),
    "process_start": _text(128),
    "host": _text(255),
    "boot_id": _text(128),
    "machine_id": _text(128),
    "pid_namespace": _text(128),
}


def _owner(value):
    return (
        isinstance(value, dict)
        and set(value) == set(_OWNER_FIELDS)
        and all(check(value[name]) for name, check in _OWNER_FIELDS.items())
    )


# name -> (validator, required)
_COMMON_FIELDS = {
    "started_at": (_timestamp, True),
    "updated_at": (_timestamp, True),
    "ended_at": (_timestamp, False),
    "owner": (_owner, False),
}
_KIND_FIELDS = {
    "run": {
        "run_id": (_text(128, _RUN_ID, nullable=False), True),
        "project": (_text(4096), False),
        "target": (_text(4096), False),
        "agent": (_text(64), False),
        "model": (_text(256), False),
        "trials": (_integer(1, MAX_TRIALS, nullable=False), True),
        "phase": (_choice(RUN_PHASES), True),
        "state": (_choice(RUN_STATES), True),
        "exit_code": (_integer(0, 255), False),
        "report": (_report, False),
    },
    "trial": {
        "phase": (_choice(TRIAL_PHASES), True),
        "state": (_choice(TRIAL_STATES), True),
        "cli_exit_code": (_integer(0, 255), False),
        "exit_code": (_integer(0, 255), False),
        "final_result": (_boolean, False),
    },
    "assessment": {
        "state": (_choice(ASSESSMENT_STATES), True),
        "reason": (_text(64, _REASON), False),
    },
}


def _field_label(name):
    if isinstance(name, str) and _FIELD_NAME.fullmatch(name):
        return f"'{name}'"
    return "<unprintable name>"


def validate(record):
    """Return record unchanged, or raise ProgressError if it is not schema v1."""
    if not isinstance(record, dict):
        raise ProgressError("progress metadata is not a JSON object")
    version = record.get("schema_version")
    if type(version) is not int:
        raise ProgressError("progress metadata has no integer schema_version")
    if version != SCHEMA_VERSION:
        shown = f" {version}" if abs(version) < 10**6 else ""
        raise ProgressError(
            f"progress metadata uses unsupported schema version{shown}", "unsupported"
        )
    kind = record.get("kind")
    if not isinstance(kind, str) or kind not in _KIND_FIELDS:
        raise ProgressError("progress metadata has an unknown kind")
    fields = dict(_COMMON_FIELDS, **_KIND_FIELDS[kind])
    unknown = [
        name
        for name in record
        if name not in fields and name not in ("schema_version", "kind")
    ]
    if unknown:
        labels = ", ".join(sorted(_field_label(name) for name in unknown))
        raise ProgressError(f"unsupported {kind} progress field(s): {labels}")
    for name, (check, required) in fields.items():
        if name not in record:
            if required:
                raise ProgressError(f"{kind} progress metadata is missing '{name}'")
        elif not check(record[name]):
            raise ProgressError(f"{kind} progress field '{name}' is invalid")
    return record


def _reject_constant(name):
    raise ValueError(f"unsupported JSON constant {name}")


def read_record(path, kind):
    """Return the validated record at path, or None when it does not exist yet.

    The read is bounded and never follows a symbolic link or blocks on a FIFO.
    """
    path = Path(path)
    try:
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    except FileNotFoundError:
        return None
    except OSError as error:
        if error.errno == errno.ELOOP:
            raise ProgressError("progress metadata is a symbolic link") from error
        raise ProgressError(
            f"cannot read progress metadata: {error.strerror or error}", "io"
        ) from error
    chunks = []
    size = 0
    try:
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            raise ProgressError("progress metadata is not a regular file")
        while size <= MAX_RECORD_BYTES:
            chunk = os.read(descriptor, MAX_RECORD_BYTES + 1 - size)
            if not chunk:
                break
            chunks.append(chunk)
            size += len(chunk)
    except OSError as error:
        raise ProgressError(
            f"cannot read progress metadata: {error.strerror or error}", "io"
        ) from error
    finally:
        os.close(descriptor)
    if size > MAX_RECORD_BYTES:
        raise ProgressError(
            f"progress metadata exceeds {MAX_RECORD_BYTES} bytes", "too_large"
        )
    try:
        record = json.loads(
            b"".join(chunks).decode("utf-8"), parse_constant=_reject_constant
        )
    except (ValueError, RecursionError) as error:
        raise ProgressError("progress metadata is not valid JSON") from error
    validate(record)
    if record["kind"] != kind:
        raise ProgressError(
            f"progress metadata records kind '{record['kind']}', expected '{kind}'"
        )
    return record


def _command_output(arguments, environment=None):
    try:
        result = subprocess.run(
            arguments,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            env=environment,
            timeout=_COMMAND_TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.SubprocessError, UnicodeError):
        return None
    return result.stdout if result.returncode == 0 else None


def _first_line(path):
    try:
        with open(path, encoding="ascii") as handle:
            return handle.readline(256).strip() or None
    except (OSError, UnicodeError):
        return None


def _boot_id():
    if _LINUX:
        return _first_line("/proc/sys/kernel/random/boot_id")
    if _DARWIN:
        output = _command_output(["/usr/sbin/sysctl", "-n", "kern.bootsessionuuid"])
        return (output or "").strip() or None
    return None


def _machine_id():
    raw = None
    if _LINUX:
        raw = _first_line("/etc/machine-id") or _first_line("/var/lib/dbus/machine-id")
    elif _DARWIN:
        output = _command_output(
            ["/usr/sbin/ioreg", "-rd1", "-c", "IOPlatformExpertDevice"]
        )
        match = _PLATFORM_UUID.search(output or "")
        raw = match.group(1) if match else None
    if not raw:
        return None
    # Persist an application-specific digest, never the host's raw identifier.
    digest = hashlib.sha256(b"behavior-diff progress machine\0" + raw.encode())
    return digest.hexdigest()[:32]


def _pid_namespace():
    if not _LINUX:
        return None
    try:
        return os.readlink("/proc/self/ns/pid")
    except OSError:
        return None


def host_identity():
    """Return the boot, machine, and PID-namespace context for local processes."""
    host = socket.gethostname()
    return {
        "host": host if 0 < len(host) <= 255 else None,
        "boot_id": _boot_id(),
        "machine_id": _machine_id(),
        "pid_namespace": _pid_namespace(),
    }


def _pid_exists(pid):
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except OSError:
        return True
    return True


def process_state(pid):
    """Return ('absent'|'zombie'|'present'|'unknown', start identity or None)."""
    if _LINUX:
        stat_path = f"/proc/{pid}/stat"
        try:
            with open(stat_path, encoding="ascii", errors="replace") as handle:
                text = handle.read(4096)
        except FileNotFoundError:
            return "absent", None
        except OSError:
            return "unknown", None
        # The command name may contain ')'; fields resume after the last one.
        fields = text.rpartition(")")[2].split()
        if len(fields) < 20 or not fields[19].isdigit():
            return "present", None
        state = "zombie" if fields[0] in ("Z", "X") else "present"
        return state, "linux:" + fields[19]
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return "absent", None
    except PermissionError:
        pass
    except OSError:
        return "unknown", None
    # Fixed locale and zone keep lstart identical for every writer and reader.
    output = _command_output(
        ["/bin/ps" if _DARWIN else "ps", "-o", "stat=,lstart=", "-p", str(pid)],
        dict(os.environ, LC_ALL="C", TZ="UTC0"),
    )
    lines = (output or "").strip().splitlines()
    status, _, started = (lines[0] if lines else "").partition(" ")
    started = " ".join(started.split())
    if not status or not started:
        return ("present" if _pid_exists(pid) else "absent"), None
    return ("zombie" if status.startswith("Z") else "present"), "ps:" + started


def owner_identity(pid):
    """Return the identity that lets readers recognize pid despite PID reuse."""
    if type(pid) is not int or pid < 1:
        raise ProgressError(
            "the owner process has already exited; its identity is unavailable",
            "owner_unavailable",
        )
    state, started = process_state(pid)
    if state in ("absent", "zombie"):
        raise ProgressError(
            "the owner process is not running; its identity is unavailable",
            "owner_unavailable",
        )
    return dict({"pid": pid, "process_start": started}, **host_identity())


def observe_owner(owner, local_host):
    """Classify a recorded owner as ('alive'|'ended'|'uncertain', reason code).

    A PID alone never proves liveness: the boot, PID namespace, and process
    start must match. Unverifiable identity stays uncertain, never ended.
    """
    if owner is None:
        return "uncertain", "owner_not_recorded"
    if owner["boot_id"] is None or local_host["boot_id"] is None:
        return "uncertain", "boot_unknown"
    if owner["boot_id"] != local_host["boot_id"]:
        if owner["machine_id"] is not None and (
            owner["machine_id"] == local_host["machine_id"]
        ):
            return "ended", "host_restarted"
        return "uncertain", "other_host_or_boot"
    if owner["pid_namespace"] != local_host["pid_namespace"]:
        return "uncertain", "other_pid_namespace"
    if owner["process_start"] is None:
        return "uncertain", "start_unrecorded"
    state, started = process_state(owner["pid"])
    if state == "absent":
        return "ended", "process_exited"
    if started is None:
        return "uncertain", "process_unreadable"
    if started != owner["process_start"]:
        return "ended", "pid_reused"
    if state == "zombie":
        return "ended", "process_exited"
    return "alive", "process_running"


def _replace(path, record):
    data = json.dumps(record, ensure_ascii=True, indent=2, sort_keys=True) + "\n"
    if len(data) > MAX_RECORD_BYTES:
        raise ProgressError(
            f"progress metadata exceeds {MAX_RECORD_BYTES} bytes", "too_large"
        )
    descriptor, temporary = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    try:
        with os.fdopen(descriptor, "w", encoding="ascii") as handle:
            os.fchmod(handle.fileno(), 0o600)
            handle.write(data)
        os.replace(temporary, path)
    except BaseException:
        with contextlib.suppress(OSError):
            os.unlink(temporary)
        raise


def update(path, kind, fields, owner=False, owner_pid=None):
    """Merge fields into one progress record and atomically replace it.

    Top-level fields replace earlier values; nested objects such as report are
    replaced whole. owner=True records the calling shell (os.getppid()), because
    Bash's $$ names the top-level script even inside a background subshell.
    owner_pid records that process instead, e.g. os.getpid() for an in-process
    producer. The parent directory must already exist. Returns the written
    record; every failure raises ProgressError and leaves the record unchanged.
    """
    path = Path(path)
    if kind not in _KIND_FIELDS:
        raise ProgressError("unknown progress record kind")
    if not isinstance(fields, dict):
        raise ProgressError("progress fields must be a JSON object")
    if owner and owner_pid is not None:
        raise ProgressError("pass owner or owner_pid, not both")
    managed = sorted(name for name in fields if name in WRITER_FIELDS)
    if managed:
        raise ProgressError(
            "writer-managed field(s) cannot be set: " + ", ".join(managed)
        )
    try:
        existing = read_record(path, kind)
        now = format_timestamp(utc_now())
        if existing is None:
            record = {"schema_version": SCHEMA_VERSION, "kind": kind, "started_at": now}
        else:
            record = dict(existing)
        record.update(fields)
        record["updated_at"] = now
        if owner:
            parent_pid = os.getppid()
            record["owner"] = owner_identity(parent_pid)
            if parent_pid == 1:
                # PID 1 can be the caller in a container or an orphan's adopter.
                # Only an explicit in-process owner_pid proves which it is.
                record["owner"]["process_start"] = None
        elif owner_pid is not None:
            record["owner"] = owner_identity(owner_pid)
        terminal = TERMINAL_STATES[kind]
        if record.get("state") in terminal:
            if existing is None or existing["state"] not in terminal:
                record["ended_at"] = now
        else:
            record.pop("ended_at", None)
        validate(record)
        _replace(path, record)
    except OSError as error:
        raise ProgressError(
            f"cannot write progress metadata: {error.strerror or error}", "io"
        ) from error
    return record


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Merge fields into one Behavior Diff progress record."
    )
    parser.add_argument("path", type=Path, metavar="PATH")
    parser.add_argument("kind", choices=sorted(_KIND_FIELDS), metavar="KIND")
    parser.add_argument("fields", metavar="FIELDS_JSON", help="JSON object to merge")
    parser.add_argument(
        "--owner",
        action="store_true",
        help="record the calling shell process as the owner of this record",
    )
    args = parser.parse_args(argv)
    try:
        fields = json.loads(args.fields, parse_constant=_reject_constant)
    except (ValueError, RecursionError):
        parser.error("FIELDS_JSON must be a JSON object")
    if not isinstance(fields, dict):
        parser.error("FIELDS_JSON must be a JSON object")
    try:
        update(args.path, args.kind, fields, owner=args.owner)
    except ProgressError as error:
        print(
            f"behavior-diff progress: {printable(args.path)}: {error}", file=sys.stderr
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
