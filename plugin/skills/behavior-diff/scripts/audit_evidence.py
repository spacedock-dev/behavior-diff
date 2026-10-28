#!/usr/bin/env python3
"""Locate original local evidence, without assessment filters or semantic verdicts.

Index JSON goes only to stdout. --file reads an exact byte page inside RUN_DIR;
redirect private output only to a 0600 file outside every trial project.
"""

import argparse
import hashlib
import json
from pathlib import Path
import stat
import sys

import progress
from reporting.load import read_trial_trace, trial_interruption


STREAMS = ("trace.jsonl", "codex-raw.jsonl", "pi-raw.jsonl", "omp-raw.jsonl")


def safe_path(root, name):
    path = Path(name)
    if (
        path.is_absolute()
        or not path.parts
        or any(x in (".", "..") for x in path.parts)
    ):
        raise ValueError("expected a run-relative path")
    current = root
    for part in path.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError("unsafe symlink")
    return current


def location(root, path):
    return {
        "file": path.relative_to(root).as_posix(),
        "offset": 0,
        "length": path.stat().st_size,
    }


def stream_index(root, name):
    try:
        path = safe_path(root, name)
        if not stat.S_ISREG(path.stat().st_mode):
            raise ValueError("unsafe file type")
        result = {"status": "available", **location(root, path), "events": []}
        with path.open("rb") as stream:
            offset = 0
            for line, raw in enumerate(stream, 1):
                row = {"line": line, "offset": offset, "length": len(raw)}
                offset += len(raw)
                try:
                    event = json.loads(raw)
                    if type(event) is not dict:
                        raise ValueError("not an object")
                    row.update(type=event.get("type"), status="available")
                    parts = event.get("message", {})
                    parts = parts.get("content", []) if type(parts) is dict else []
                    row["parts"] = [
                        {
                            "pointer": f"/message/content/{i}",
                            "type": part.get("type"),
                            "identity": part.get("id", part.get("tool_use_id")),
                            "name": part.get("name"),
                            "is_error": part.get("is_error"),
                            "truncated": part.get("truncated"),
                        }
                        for i, part in enumerate(parts if type(parts) is list else [])
                        if type(part) is dict
                    ]
                    # Native records are retained independently of normalized text.
                    item = event.get("item")
                    if type(item) is dict:
                        row["item"] = {
                            key: item.get(key)
                            for key in (
                                "id",
                                "type",
                                "item_type",
                                "status",
                                "exit_code",
                            )
                        }
                    row["identity"] = event.get("toolCallId")
                except (ValueError, UnicodeError):
                    row.update(status="malformed")
                result["events"].append(row)
        # Do not pair duplicate identities: expose every occurrence and ambiguity.
        identities = {}
        for row in result["events"]:
            for part in row.get("parts", []):
                identity = part["identity"]
                if isinstance(identity, str):
                    identities.setdefault(identity, []).append(
                        {
                            "line": row["line"],
                            "pointer": part["pointer"],
                            "type": part["type"],
                        }
                    )
        result["identities"] = identities
        result["identity_states"] = {}
        for identity, occurrences in identities.items():
            calls = sum(x["type"] == "tool_use" for x in occurrences)
            returns = sum(x["type"] == "tool_result" for x in occurrences)
            result["identity_states"][identity] = (
                "ambiguous"
                if calls > 1 or returns > 1
                else "missing_call"
                if not calls
                else "missing_return"
                if not returns
                else "recorded_pair"
            )
        return result
    except FileNotFoundError:
        return {"file": name, "status": "missing"}
    except (OSError, ValueError):
        return {"file": name, "status": "unsafe_or_unreadable"}


def artifacts(root, name):
    """Include ignored/untracked files, never traverse links or Git internals.

    Locations, not claims of authorship: the trial may also retain initial files.
    """
    result = []
    try:
        project = safe_path(root, name + "/project")
        if not project.is_dir():
            return [{"file": name + "/project", "status": "missing"}]

        def walk(folder):
            for path in sorted(folder.iterdir()):
                if path.name == ".git":
                    continue
                entry = {"file": path.relative_to(root).as_posix()}
                try:
                    mode = path.lstat().st_mode
                    if stat.S_ISDIR(mode):
                        walk(path)
                        continue
                    if not stat.S_ISREG(mode):
                        raise ValueError("unsafe file type")
                    entry.update(status="available", **location(root, path))
                    with path.open("rb") as stream:
                        digest = hashlib.sha256()
                        for block in iter(lambda: stream.read(65536), b""):
                            digest.update(block)
                        entry["sha256"] = digest.hexdigest()
                except (OSError, ValueError):
                    entry["status"] = "unsafe_or_unreadable"
                result.append(entry)

        walk(project)
    except (OSError, ValueError):
        result.append({"file": name + "/project", "status": "unsafe_or_unreadable"})
    return result


def index_run(root):
    diagnostics = []
    try:
        safe_path(root, "status.json")
        run = progress.read_record(root / "status.json", "run")
    except (progress.ProgressError, ValueError):
        run = None
        diagnostics.append("invalid or unsafe run status")
    names = set()
    if run:
        names.update(
            f"{side}-{i}"
            for side in ("before", "after")
            for i in range(1, run["trials"] + 1)
        )
    else:
        diagnostics.append(
            "expected trial count unknown; discovered trials are not completeness proof"
        )
    names.update(
        path.name
        for path in root.iterdir()
        if path.name.startswith(("before-", "after-"))
    )
    trials = {}
    for name in sorted(names):
        streams = {
            stream: stream_index(root, name + "/" + stream) for stream in STREAMS
        }
        row = {"streams": streams, "artifacts": artifacts(root, name)}
        try:
            safe_path(root, name + "/status.json")
            record = progress.read_record(root / name / "status.json", "trial")
            row["status"] = record if record else "missing"
            row["interruption"] = trial_interruption(root / name)
        except (progress.ProgressError, ValueError):
            row.update(
                status="unsafe_or_invalid", interruption="trial record unreadable"
            )
        if streams["trace.jsonl"]["status"] == "available":
            try:
                commands, final = read_trial_trace(root / name / "trace.jsonl")
                row["normalized"] = {
                    "commands": len(commands),
                    "nonempty_text": bool(final),
                }
            except (OSError, UnicodeError):
                row["normalized"] = "unreadable"
        row["stderr"] = stream_index(root, name + "/stderr.log")
        trials[name] = row
    return {
        "run": str(root),
        "diagnostics": diagnostics,
        "trials": trials,
        "boundary": "Local raw locations only, not completion, attribution or case judgments. "
        "Repeated identities remain separate. Read original pages, including native "
        "terminal/error events and artifacts, for every private case in every trial.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    parser.add_argument("--file", help="run-relative original log or artifact")
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--length", type=int, default=65536)
    args = parser.parse_args()
    try:
        root = args.run.resolve(strict=True)
        if args.offset < 0 or args.length < 1:
            raise ValueError("invalid byte page")
        if args.file:
            path = safe_path(root, args.file)
            if ".git" in Path(args.file).parts or not stat.S_ISREG(path.stat().st_mode):
                raise ValueError("unsafe file type")
            with path.open("rb") as stream:
                stream.seek(args.offset)
                sys.stdout.buffer.write(stream.read(args.length))
        else:
            print(json.dumps(index_run(root), indent=2, sort_keys=True))
    except (OSError, ValueError):
        print(
            "audit-evidence: invalid, unsafe or unreadable local evidence",
            file=sys.stderr,
        )
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
