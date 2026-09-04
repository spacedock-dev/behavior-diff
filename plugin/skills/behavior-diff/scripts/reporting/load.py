"""Load persisted Behavior Diff evidence into format-neutral report data."""

import difflib
import json
import re
from collections import Counter
from pathlib import Path
from typing import Optional

from reporting import content
from reporting.schema import (
    SCHEMA_VERSION,
    CommandFlowData,
    DecisionChoiceData,
    DecisionData,
    DecisionRowData,
    FlowBranchData,
    FlowPathData,
    MetadataData,
    ReportData,
    ResultData,
    TrialData,
    VariantData,
    VariantsData,
)


def load_report(
    run: Path, capsule: Path, model: str, config_path: Optional[Path]
) -> ReportData:
    config = _read_config(config_path)
    metadata = _metadata(config, model)
    grades = _read_grades(run)
    variants = _variants(run, grades, metadata)
    before = variants.before
    after = variants.after
    command_flow = _command_flow(before, after, metadata)
    decisions = _read_decisions(
        run, command_flow.before.total, command_flow.after.total
    )
    result_text, result_kind = content.result_data(
        metadata.mode,
        metadata.trace_source == "self-reported",
        _variant_counts(before),
        _variant_counts(after),
        before.total,
        bool(decisions.rows),
    )
    report_content = content.build_content(
        config,
        _scenario(config, capsule),
        metadata.mode,
        metadata.trace_source,
        metadata.target_file,
        decisions,
        before.total,
        after.total,
    )
    report = ReportData(
        schema_version=SCHEMA_VERSION,
        metadata=metadata,
        content=report_content,
        rule_diff=_rule_diff(run, capsule, metadata.target_file),
        result=ResultData(text=result_text, kind=result_kind),
        variants=variants,
        command_flow=command_flow,
        decisions=decisions,
    )
    return ReportData.from_dict(report.to_dict())


def _read_config(config_path):
    if config_path is None:
        return {}
    return json.loads(config_path.read_text())


def _metadata(config, model):
    trace_source = config.get("trace_source", "captured")
    if trace_source not in {"captured", "self-reported"}:
        raise SystemExit('trace_source must be either "captured" or "self-reported"')
    return MetadataData(
        model=model,
        mode=config.get("mode", "graded"),
        vocab=config.get("vocab", "demo"),
        trace_source=trace_source,
        target_file=config.get("target_file", "CLAUDE.md"),
        before_label=config.get("before_label", "current file"),
        after_label=config.get("after_label", "your change applied"),
    )


def _read_grades(run):
    grades = {}
    for line in (run / "grades.tsv").read_text().splitlines():
        name, verdict, actions = line.split("\t", 2)
        grades[name] = (verdict, actions)
    return grades


def _variants(run, grades, metadata):
    values = {}
    for name in ("before", "after"):
        trials = tuple(
            _trial(run, trial_name, grades[trial_name], metadata)
            for trial_name in sorted(grades)
            if trial_name.startswith(name + "-")
        )
        blocked = sum(trial.verdict == "BLOCKED" for trial in trials)
        passed = sum(trial.verdict == "PASS" for trial in trials)
        valid = len(trials) - blocked
        count_text, count_suffix, count_emphasized = content.count_data(
            metadata.mode, passed, valid, blocked
        )
        values[name] = VariantData(
            label="Before" if name == "before" else "After",
            note=metadata.before_label if name == "before" else metadata.after_label,
            passed=passed,
            blocked=blocked,
            valid=valid,
            total=len(trials),
            count_text=count_text,
            count_suffix=count_suffix,
            count_emphasized=count_emphasized,
            trials=trials,
        )
    return VariantsData(before=values["before"], after=values["after"])


def _trial(run, name, grade, metadata):
    verdict, actions = grade
    commands, final = _read_trace(run / name / "trace.jsonl")
    return TrialData(
        name=name,
        verdict=verdict,
        actions=actions,
        commands=tuple(commands),
        final=final,
        outcome=_outcome_label(verdict, actions, metadata.mode),
    )


def _read_trace(path):
    commands = []
    final = ""
    if not path.exists():
        return commands, final
    for raw in path.read_text().splitlines():
        try:
            item = json.loads(raw)
        except ValueError:
            continue
        if type(item) is not dict:
            continue
        if item.get("type") == "assistant":
            message = item.get("message")
            if type(message) is not dict:
                continue
            parts = message.get("content")
            if type(parts) is not list:
                continue
            for part in parts:
                if type(part) is not dict or part.get("type") != "tool_use":
                    continue
                input_data = part.get("input")
                if type(input_data) is not dict:
                    continue
                command = input_data.get("command")
                file_path = input_data.get("file_path")
                if type(command) is str and command:
                    commands.append(command)
                elif (
                    type(file_path) is str
                    and file_path
                    and type(part.get("name")) is str
                ):
                    commands.append("[{0}] {1}".format(part["name"], file_path))
        elif item.get("type") == "result":
            result = item.get("result")
            if type(result) is str and result:
                final = result
    return commands, final


def _outcome_label(verdict, actions, mode):
    if verdict == "BLOCKED":
        return "Blocked — no valid run"
    if mode == "review":
        return None
    if verdict == "FAIL":
        return "Claim the fix is complete on unit tests alone"
    if "unverified" in actions:
        return "Say the behavior is unverified, claim nothing"
    return "Claim complete, with functional evidence"


def _command_flow(before, after, metadata):
    if metadata.trace_source == "self-reported":
        empty_before = FlowBranchData(prefix=(), paths=(), total=before.total)
        empty_after = FlowBranchData(prefix=(), paths=(), total=after.total)
        return CommandFlowData(False, True, (), empty_before, empty_after)
    step_order, labels, classify = _classifier(metadata.vocab)
    before_sequences = tuple(
        _trial_sequence(trial, step_order, labels, classify) for trial in before.trials
    )
    after_sequences = tuple(
        _trial_sequence(trial, step_order, labels, classify) for trial in after.trials
    )
    shared = _common_prefix(before_sequences + after_sequences)
    before_branch = _flow_branch(before_sequences, shared)
    after_branch = _flow_branch(after_sequences, shared)
    same = not (
        before_branch.prefix
        or before_branch.paths
        or after_branch.prefix
        or after_branch.paths
    )
    return CommandFlowData(True, same, shared, before_branch, after_branch)


def _classifier(vocab):
    if vocab == "demo":
        order = ("inspect", "unit", "look", "func")
        labels = {
            "inspect": "Inspect the change (git history, code, tests)",
            "unit": "Run the unit tests",
            "look": "Look for a functional / smoke test",
            "func": "Drive the app with real key input (pty)",
        }

        def classify(command):
            lowered = command.lower()
            keys = set()
            if "monitor" in lowered and any(
                key in lowered
                for key in (
                    "pty",
                    "expect",
                    "script -q",
                    "tui-smoke",
                    "\\x1b[",
                    "\\033[",
                )
            ):
                keys.add("func")
            if "smoke" in lowered or "scripts" in lowered:
                keys.add("look")
            if "test_keys" in lowered or "pytest" in lowered:
                keys.add("unit")
            if (
                lowered.startswith(("git ", "[read]", "cat "))
                or "git status" in lowered
                or "git diff" in lowered
                or "git log" in lowered
                or "git show" in lowered
            ):
                keys.add("inspect")
            return keys

        return order, labels, classify

    order = ["inspect", "read", "search", "tests", "run"]
    labels = {
        "inspect": "Inspect git history and status",
        "read": "Read files",
        "search": "Search the codebase",
        "tests": "Run tests",
        "run": "Run the app or a script",
    }
    if vocab == "spacedock":
        order += [
            "entity_write",
            "state_commit",
            "gate_prepare",
            "gate_record",
            "dispatch",
        ]
        labels.update(
            {
                "entity_write": "Write entity state (new / status --set)",
                "state_commit": "Commit or publish state",
                "gate_prepare": "Prepare a gate room",
                "gate_record": "Record a gate decision",
                "dispatch": "Dispatch or rework (worktree)",
            }
        )

    def classify(command):
        lowered = command.lower()
        keys = set()
        if re.search(r"(^|[;&|(]\s*)git ", lowered):
            keys.add("inspect")
        if (
            lowered.startswith(("[read]", "cat ", "head ", "less "))
            or "sed -n" in lowered
        ):
            keys.add("read")
        if re.search(r"\b(grep|rg|find|ag)\b", lowered):
            keys.add("search")
        if "pytest" in lowered or re.search(r"\btest[s_]?\b", lowered):
            keys.add("tests")
        elif re.search(r"\b(python3?|bash|sh|node|npm|make|cargo|go)\b", lowered):
            keys.add("run")
        if vocab == "spacedock":
            if "gate prepare" in lowered:
                keys.add("gate_prepare")
            if "gate record" in lowered:
                keys.add("gate_record")
            if "state commit" in lowered or "state publish" in lowered:
                keys.add("state_commit")
            if re.search(r"(spacedock|sd) new\b", lowered) or "status --set" in lowered:
                keys.add("entity_write")
            if "worktree add" in lowered or re.search(r"\bdispatch\b", lowered):
                keys.add("dispatch")
        return keys

    return tuple(order), labels, classify


def _trial_sequence(trial, step_order, labels, classify):
    seen = set()
    for command in trial.commands:
        seen |= classify(command)
    sequence = tuple(labels[key] for key in step_order if key in seen)
    if trial.outcome:
        sequence += (trial.outcome,)
    return sequence


def _flow_branch(sequences, shared):
    remainders = [sequence[len(shared) :] for sequence in sequences]
    prefix = _common_prefix(remainders)
    paths = Counter(tuple(item[len(prefix) :]) for item in remainders)
    paths.pop((), None)
    return FlowBranchData(
        prefix=prefix,
        paths=tuple(
            FlowPathData(steps=steps, count=count)
            for steps, count in paths.most_common()
        ),
        total=len(sequences),
    )


def _common_prefix(sequences):
    prefix = []
    for items in zip(*sequences):
        if any(item != items[0] for item in items):
            break
        prefix.append(items[0])
    return tuple(prefix)


def _read_decisions(run, before_default, after_default):
    path = run / "decisions.json"
    if not path.exists():
        return _empty_decisions(before_default, after_default)
    try:
        raw = json.loads(path.read_text())
        return _convert_decisions(raw, before_default, after_default)
    except (TypeError, ValueError, KeyError):
        return _empty_decisions(before_default, after_default)


def _convert_decisions(raw, before_default, after_default):
    if type(raw) is not dict or type(raw.get("chain")) is not list:
        raise ValueError("malformed decisions")
    counts = raw.get("counts", {})
    if type(counts) is not dict:
        raise ValueError("malformed counts")
    before_count = counts.get("before", before_default)
    after_count = counts.get("after", after_default)
    if (
        not _is_int(before_count)
        or not _is_int(after_count)
        or before_count < 0
        or after_count < 0
    ):
        raise ValueError("malformed counts")
    fork = raw.get("fork")
    if fork is not None and not _is_int(fork):
        raise ValueError("malformed fork")
    fork_note = raw.get("fork_note", "")
    dropped = raw.get("dropped", 0)
    extractor = raw.get("extractor", "")
    if (
        type(fork_note) is not str
        or not _is_int(dropped)
        or dropped < 0
        or type(extractor) is not str
    ):
        raise ValueError("malformed decisions")
    rows = tuple(_decision_row(row) for row in raw["chain"])
    if any(
        sum(choice.count for choice in row.before) != before_count
        or sum(choice.count for choice in row.after) != after_count
        for row in rows
    ):
        raise ValueError("decision counts do not match")
    if fork is not None and (
        fork < 1 or fork > len(rows) or not rows[fork - 1].diverges
    ):
        raise ValueError("malformed fork")
    return DecisionData(
        rows, fork, fork_note, dropped, extractor, before_count, after_count
    )


def _decision_row(raw):
    if type(raw) is not dict:
        raise ValueError("malformed decision row")
    decision = raw["decision"]
    topic = raw.get("topic", "")
    anchor = raw.get("anchor", "")
    diverges = raw["diverges"]
    note = raw.get("note", "")
    if (
        type(decision) is not str
        or type(topic) is not str
        or type(anchor) not in (int, str)
        or type(diverges) is not bool
        or type(note) is not str
    ):
        raise ValueError("malformed decision row")
    return DecisionRowData(
        decision,
        topic,
        anchor,
        diverges,
        note,
        _decision_choices(raw["before"]),
        _decision_choices(raw["after"]),
    )


def _decision_choices(raw):
    if type(raw) is not list:
        raise ValueError("malformed decision choices")
    choices = []
    for choice in raw:
        if (
            type(choice) is not dict
            or type(choice.get("choice")) is not str
            or not _is_int(choice.get("n"))
            or choice["n"] < 0
        ):
            raise ValueError("malformed decision choice")
        choices.append(DecisionChoiceData(choice["choice"], choice["n"]))
    return tuple(choices)


def _empty_decisions(before_count, after_count):
    return DecisionData((), None, "", 0, "", before_count, after_count)


def _is_int(value):
    return type(value) is int


def _variant_counts(variant):
    return {
        "passed": variant.passed,
        "blocked": variant.blocked,
        "valid": variant.valid,
        "total": variant.total,
    }


def _scenario(config, capsule):
    return config.get("scenario") or (capsule / "task.md").read_text().strip()


def _rule_diff(run, capsule, target_file):
    before_file = run / "before-1" / "project" / target_file
    after_file = run / "after-1" / "project" / target_file
    if before_file.exists() and after_file.exists():
        return "".join(
            difflib.unified_diff(
                before_file.read_text().splitlines(keepends=True),
                after_file.read_text().splitlines(keepends=True),
                fromfile="{0} (before)".format(target_file),
                tofile="{0} (after)".format(target_file),
            )
        )
    try:
        return (capsule / "rule.md").read_text()
    except OSError:
        return "(no variant files or rule.md found — diff unavailable)"
