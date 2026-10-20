"""Bound recorded tool returns for assessment; never retrieve source files.

Offsets describe the returned text, not file line numbers. Filtering is deliberately
conservative and cannot certify arbitrary prose as free of private information.
"""

import json
import re
import shlex
from pathlib import Path

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


def _trial_evidence(path, name, remaining, self_reported=False, required=()):
    records = []
    pending = {}
    used = 0
    call_count = 0
    overflow = 0
    if not path.is_file() or path.is_symlink():
        return [
            {
                "id": f"{name}:trace",
                "source": "trial recording",
                "range": {"start": 0, "end": 0, "unit": "characters"},
                "text": "",
                "status": "unavailable",
                "reason": "recording missing or symlink excluded",
            }
        ], used
    with path.open(encoding="utf-8", errors="replace") as stream:
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
            matched = source_matches(record["source"], required)
            (priority if matched else incidental).append(record)
    budget = max(0, min(TRIAL_LIMIT, remaining))
    # Frozen required sources claim the same trial budget before incidental reads.
    used = _share(priority, budget)
    used += _share(incidental, budget - used)
    return records, used


def _required_patterns(config):
    """Return frozen source-requirement patterns; historical runs have none."""
    if type(config) is not dict or config.get("scenario_record") is None:
        return ()
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
    return tuple(
        dict.fromkeys(
            pattern
            for requirement in scenario.source_requirements
            for pattern in requirement.any_of
        )
    )


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
    required = _required_patterns(config)
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
        trace = trial / "trace.jsonl"
        # Reserve a share for every remaining trial, including the other variant.
        allowance = remaining // (len(names) - index)
        records, used = _trial_evidence(
            trace, trial.name, allowance, self_reported, required
        )
        trials[trial.name] = records
        remaining -= used
    return {
        "limits": {
            "per_excerpt_characters": EXCERPT_LIMIT,
            "per_trial_characters": TRIAL_LIMIT,
            "per_run_characters": RUN_LIMIT,
            "per_trial_records": RECORD_LIMIT,
            "selection": _REQUIRED_SELECTION if required else _SELECTION,
            "privacy": "Known sensitive sources and credential/email patterns are omitted; arbitrary private prose cannot be reliably detected.",
            "provenance": "Ranges are offsets in recorded returned text, not source-file lines. Absence here does not prove the agent lacked information.",
        },
        "trials": trials,
    }
