"""Bound recorded tool returns and explicitly declared captured output artifacts.

Offsets describe the returned text, not file line numbers. Filtering is deliberately
conservative and cannot certify arbitrary prose as free of private information.
"""

import json
import hashlib
import os
import stat
from contextlib import nullcontext
import re
import shlex
from pathlib import Path
from reporting.context_boundary import boundary_exclusion

from reporting.sources import (
    DESCRIPTOR_TRUNCATED,
    SENSITIVE_SOURCE,
    sensitive_text,
    source_matches,
)

EXCERPT_LIMIT = 4096
TRIAL_LIMIT = 16384
RUN_LIMIT = 131072
RECORD_LIMIT = 128
SOURCE_LIMIT = 240
ARTIFACT_BYTE_LIMIT = 65536
SELF_REPORTED = "self-reported action, not a captured return"
DUPLICATE_CALL = "duplicate tool call identity"
DUPLICATE_RESULT = "duplicate tool result identity"
# A tool record proves its call ran only when the call itself was captured once.
UNPROVEN_CALL_REASONS = (SELF_REPORTED, DUPLICATE_CALL, DUPLICATE_RESULT)
_ORDER = (
    "lexical trial order with a reserved share for each remaining trial; "
    "leading returned characters"
)
_SELECTION = "fair-share character budget across readable returns; " + _ORDER
_REQUIRED_SELECTION = (
    "readable returns matching frozen source requirements fair-share each trial "
    "budget first, then other readable returns fair-share the remainder; " + _ORDER
)
_READ_TOOLS = {"read", "read_file", "readfile", "grep", "glob", "find", "ls"}
_READ_COMMANDS = {"cat", "head", "tail", "grep", "rg", "ls", "wc"}
_SHELL_WRAPPERS = {"/bin/sh", "/bin/bash", "/bin/zsh"}
_GH_API_SWITCHES = {"--paginate", "--slurp", "-i", "--include"}
_GH_API_OPTIONS = {
    "-X": "--method",
    "--method": "--method",
    "-H": "--header",
    "--header": "--header",
    "-q": "--jq",
    "--jq": "--jq",
    "-t": "--template",
    "--template": "--template",
    "--cache": "--cache",
    "--hostname": "--hostname",
}


def _read_only_api(words):
    """Admit `gh api` only as one unambiguous GET without request-body input."""
    endpoints = []
    index = 0
    while index < len(words):
        word = words[index]
        index += 1
        if word in _GH_API_SWITCHES:
            continue
        name, value = word, None
        if word.startswith("--") and "=" in word:
            name, value = word.split("=", 1)
        elif word[:2] in {"-X", "-H", "-q", "-t"} and len(word) > 2:
            name, value = word[:2], word[2:]
        option = _GH_API_OPTIONS.get(name)
        if option:
            if value is None:
                if index == len(words):
                    return False
                value = words[index]
                index += 1
            if option == "--method" and value != "GET":
                return False
            if option == "--header" and not re.fullmatch(r"(?i)accept:.*", value):
                return False
        elif word.startswith("-"):
            # Fields, raw fields, --input, and unknown flags may send a body.
            return False
        else:
            endpoints.append(word)
    return len(endpoints) == 1 and endpoints[0] != "graphql"


def _eligible_command(command):
    if type(command) is not str or re.search(r"[|;&<>`\n]|\$\(", command):
        return False
    try:
        words = shlex.split(command)
        if len(words) == 3 and words[0] in _SHELL_WRAPPERS and words[1] == "-lc":
            # Decode only the recorded command argument, never run the shell.
            command = words[2]
            if re.search(r"[|;&<>`\n]|\$\(", command):
                return False
            words = shlex.split(command)
    except ValueError:
        return False
    return bool(words) and (
        words[0] in _READ_COMMANDS
        or len(words) > 1
        and words[0] == "git"
        and words[1] in {"show", "diff", "log"}
        or len(words) > 2
        and words[:2] == ["gh", "pr"]
        and words[2] in {"view", "diff"}
        or words[:2] == ["gh", "api"]
        and _read_only_api(words[2:])
    )


def _descriptor(part):
    tool = part.get("name", "unknown")
    args = part.get("input")
    args = args if type(args) is dict else {}
    descriptor = str(tool) + " " + json.dumps(args, ensure_ascii=False, sort_keys=True)
    if sensitive_text(descriptor):
        return SENSITIVE_SOURCE, False, "sensitive source"
    name = str(tool).lower().rsplit("__", 1)[-1]
    eligible = name in _READ_TOOLS
    if name in {"bash", "shell", "exec", "exec_command"}:
        # Codex preserves its raw wrapper alongside the command-flow display field.
        eligible = _eligible_command(args.get("raw_command", args.get("command", "")))
    if len(descriptor) > SOURCE_LIMIT:
        descriptor = descriptor[: SOURCE_LIMIT - 24] + DESCRIPTOR_TRUNCATED
    return descriptor, eligible, "not an eligible recorded read"


def _text_parts(value):
    if type(value) is str:
        return [value]
    if type(value) is list:
        return [
            item["text"]
            for item in value
            if type(item) is dict
            and item.get("type") == "text"
            and type(item.get("text")) is str
        ]
    return []


def _share(records, budget):
    """Fair-share `budget` over records' leading text; return characters kept."""
    low, high = 0, EXCERPT_LIMIT
    while low < high:
        cap = (low + high + 1) // 2
        if sum(min(len(record["text"]), cap) for record in records) <= budget:
            low = cap
        else:
            high = cap - 1
    spare = budget - sum(min(len(record["text"]), low) for record in records)
    used = 0
    for record in records:
        length = min(len(record["text"]), low)
        if spare and length < len(record["text"]):
            length += 1
            spare -= 1
        if length < len(record["text"]):
            record.update(
                text=record["text"][:length],
                status="truncated" if length else "omitted",
                reason="fair-share assessment truncation"
                if length
                else "assessment content budget exhausted",
            )
            record["range"]["end"] = length
        used += length
    return used


def _artifact_evidence(trial, paths):
    """Read only nominated regular files, using no-follow directory descriptors."""
    records = []
    for index, relative in enumerate(paths, 1):
        record = {
            "id": f"{trial.name}:artifact-{index}",
            "source": "artifact " + relative,
            "range": {"start": 0, "end": 0, "unit": "characters"},
            "text": "",
            "status": "unavailable",
            "reason": "required artifact missing or unsafe",
        }
        records.append(record)
        descriptors = []
        try:
            # Opening each component relative to an already opened directory
            # prevents both static links and path-swap escapes.
            directory = os.open(trial, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
            descriptors.append(directory)
            for part in ("project", *relative.split("/")[:-1]):
                directory = os.open(
                    part,
                    os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                    dir_fd=directory,
                )
                descriptors.append(directory)
            fd = os.open(
                relative.split("/")[-1],
                os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                dir_fd=directory,
            )
            descriptors.append(fd)
            info = os.fstat(fd)
            if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                raise ValueError("unsafe file")
            if info.st_size > ARTIFACT_BYTE_LIMIT:
                record.update(
                    status="omitted", reason="artifact exceeds bounded privacy scan"
                )
                continue
            with os.fdopen(os.dup(fd), "rb") as stream:
                data = stream.read(ARTIFACT_BYTE_LIMIT + 1)
            after = os.fstat(fd)
            if len(data) > ARTIFACT_BYTE_LIMIT or (
                info.st_size,
                info.st_mtime_ns,
                info.st_ctime_ns,
            ) != (after.st_size, after.st_mtime_ns, after.st_ctime_ns):
                record.update(reason="artifact changed or exceeded capture limit")
                continue
            text = data.decode("utf-8")
            if "\0" in text:
                raise ValueError("non-text artifact")
            if sensitive_text(text):
                record.update(
                    status="omitted", reason="potentially sensitive artifact content"
                )
                continue
            record["source"] += " sha256:" + hashlib.sha256(data).hexdigest()
            record.update(
                text=text[:EXCERPT_LIMIT],
                status="truncated" if len(text) > EXCERPT_LIMIT else "available",
                reason="artifact assessment truncation"
                if len(text) > EXCERPT_LIMIT
                else "",
            )
            record["range"]["end"] = len(record["text"])
        except (OSError, ValueError, UnicodeError):
            pass
        finally:
            for fd in reversed(descriptors):
                os.close(fd)
    return records


def _trial_evidence(
    path, name, remaining, self_reported=False, required=(), artifacts=()
):
    records = _artifact_evidence(path.parent, artifacts)
    pending = {}
    used = 0
    call_count = 0
    overflow = 0
    if not path.is_file() or path.is_symlink():
        records.append(
            {
                "id": f"{name}:trace",
                "source": "trial recording",
                "range": {"start": 0, "end": 0, "unit": "characters"},
                "text": "",
                "status": "unavailable",
                "reason": "recording missing or symlink excluded",
            }
        )
    stream_context = (
        path.open(encoding="utf-8", errors="replace")
        if path.is_file() and not path.is_symlink()
        else nullcontext([])
    )
    with stream_context as stream:
        for line in stream:
            try:
                event = json.loads(line)
            except ValueError:
                continue
            if type(event) is not dict:
                continue
            message = event.get("message")
            parts = message.get("content") if type(message) is dict else None
            if type(parts) is not list:
                continue
            for part in parts:
                if type(part) is not dict:
                    continue
                if part.get("type") == "tool_use":
                    call_count += 1
                    if call_count > RECORD_LIMIT:
                        overflow += 1
                        continue
                    source, eligible, reason = _descriptor(part)
                    record = {
                        "id": f"{name}:tool-{call_count}",
                        "source": source,
                        "range": {"start": 0, "end": 0, "unit": "characters"},
                        "text": "",
                        "status": "unavailable" if eligible else "omitted",
                        "reason": "no matching recorded return" if eligible else reason,
                    }
                    if (
                        self_reported
                        or str(part.get("name", "")).lower() == "reportedaction"
                    ):
                        record.update(
                            status="omitted",
                            reason=SELF_REPORTED,
                        )
                        eligible = False
                    records.append(record)
                    call_id = part.get("id")
                    if type(call_id) is str and call_id:
                        if call_id in pending:
                            previous, _ = pending[call_id]
                            previous.update(
                                status="unavailable",
                                text="",
                                reason=DUPLICATE_CALL,
                            )
                            previous["range"]["end"] = 0
                            record.update(
                                status="unavailable",
                                reason=DUPLICATE_CALL,
                            )
                            pending[call_id] = (record, False)
                        else:
                            pending[call_id] = (record, eligible)
                elif part.get("type") == "tool_result":
                    call_id = part.get("tool_use_id")
                    if type(call_id) is not str or call_id not in pending:
                        continue
                    record, eligible = pending[call_id]
                    if not eligible:
                        continue
                    # A second result for one identity cannot safely replace the first.
                    if record["reason"] != "no matching recorded return":
                        record.update(
                            status="unavailable",
                            text="",
                            reason=DUPLICATE_RESULT,
                        )
                        record["range"]["end"] = 0
                        continue
                    content = part.get("content")
                    texts = _text_parts(content)
                    if not texts:
                        record.update(reason="no recorded text content")
                        continue
                    if part.get("is_error"):
                        record.update(reason="recorded tool error")
                        continue
                    if any(sensitive_text(text) for text in texts):
                        record.update(
                            status="omitted",
                            reason="potentially sensitive returned content",
                        )
                        continue
                    budget = EXCERPT_LIMIT
                    length = sum(len(text) for text in texts) + len(texts) - 1
                    excerpt = []
                    left = budget
                    for text in texts:
                        if excerpt and left:
                            excerpt.append("\n")
                            left -= 1
                        excerpt.append(text[:left])
                        left -= min(left, len(text))
                        if not left:
                            break
                    text = "".join(excerpt)
                    nontext = type(content) is list and len(texts) != len(content)
                    truncated = (
                        length > len(text) or bool(part.get("truncated")) or nontext
                    )
                    record.update(
                        text=text,
                        status="truncated" if truncated else "available",
                        reason=(
                            "non-text content omitted"
                            if nontext
                            else "recorded or assessment truncation"
                            if truncated
                            else ""
                        ),
                    )
                    record["range"]["end"] = len(text)
    if overflow:
        records.append(
            {
                "id": f"{name}:overflow",
                "source": "additional recorded calls",
                "range": {"start": 0, "end": 0, "unit": "characters"},
                "text": "",
                "status": "omitted",
                "reason": f"{overflow} calls exceed the {RECORD_LIMIT}-record trial limit",
            }
        )
    priority, incidental = [], []
    for record in records:
        if record["text"]:
            matched = ":artifact-" in record["id"] or source_matches(
                record["source"], required
            )
            (priority if matched else incidental).append(record)
    budget = max(0, min(TRIAL_LIMIT, remaining))
    # Frozen required sources claim the same trial budget before incidental reads.
    used = _share(priority, budget)
    used += _share(incidental, budget - used)
    return records, used


def _required_inputs(config):
    """Return frozen source patterns and exact output paths; historical runs have none."""
    if type(config) is not dict or config.get("scenario_record") is None:
        return (), ()
    # Scenario validation imports target, which imports this module.
    from reporting.scenario import parse_scenario
    from reporting.target import parse_purpose

    try:
        scenario = parse_scenario(
            config["scenario_record"], parse_purpose(config.get("purpose"))
        )
    except (ValueError, TypeError, KeyError):
        raise ValueError(
            "invalid frozen scenario record in run configuration"
        ) from None
    patterns = tuple(
        dict.fromkeys(
            pattern
            for requirement in scenario.source_requirements
            for pattern in requirement.any_of
        )
    )
    artifacts = tuple(
        dict.fromkeys(
            path
            for requirement in scenario.artifact_requirements
            for path in requirement.paths
        )
    )
    return patterns, artifacts


def collect_run_evidence(run):
    """Return deterministic bounded excerpts plus explicit omission provenance."""
    run = Path(run)
    try:
        config = json.loads((run / "config.json").read_text())
    except (OSError, ValueError):
        config = {}
    self_reported = (
        type(config) is dict and config.get("trace_source") == "self-reported"
    )
    required, artifacts = _required_inputs(config)
    trials = {}
    remaining = RUN_LIMIT
    grades = run / "grades.tsv"
    names = (
        {line.split("\t", 1)[0] for line in grades.read_text().splitlines()}
        if grades.exists()
        else {path.name for path in run.iterdir() if path.is_dir()}
    )
    names = [
        name
        for name in sorted(names)
        if re.fullmatch(r"(?:before|after)-[A-Za-z0-9_-]+", name)
        and not (run / name).is_symlink()
    ]
    for index, name in enumerate(names):
        trial = run / name
        if boundary_exclusion(trial) is not None:
            trials[trial.name] = []
            continue
        trace = trial / "trace.jsonl"
        # Reserve a share for every remaining trial, including the other variant.
        allowance = remaining // (len(names) - index)
        records, used = _trial_evidence(
            trace, trial.name, allowance, self_reported, required, artifacts
        )
        trials[trial.name] = records
        remaining -= used
    return {
        "limits": {
            "per_excerpt_characters": EXCERPT_LIMIT,
            "per_trial_characters": TRIAL_LIMIT,
            "per_run_characters": RUN_LIMIT,
            "per_trial_records": RECORD_LIMIT + len(artifacts),
            "selection": ("declared artifacts and " if artifacts else "")
            + (_REQUIRED_SELECTION if required else _SELECTION),
            "privacy": "Known sensitive sources and credential/email patterns are omitted; arbitrary private prose cannot be reliably detected.",
            "provenance": "Ranges are character offsets in captured returns or explicitly declared project artifacts, not source-file lines. Artifact SHA-256 identifies captured bytes, not authorship or a read/action. Absence does not prove the agent lacked information.",
        },
        "trials": trials,
    }
