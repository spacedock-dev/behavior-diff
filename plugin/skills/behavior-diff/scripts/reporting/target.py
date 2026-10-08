"""Validate target criteria against immutable purpose and recorded trial evidence."""

from collections import Counter
import re
from dataclasses import dataclass
from typing import Tuple

from reporting.evidence import (
    EXCERPT_LIMIT,
    RECORD_LIMIT,
    RUN_LIMIT,
    SOURCE_LIMIT,
    TRIAL_LIMIT,
)
from reporting.explanation import _text

OUTCOMES = ("met", "not_met", "uncertain", "unassessable")
MODES = ("correction", "new", "change", "preservation")
UNAVAILABLE = (
    "Target assessment unavailable: no valid criterion assessment was recorded. "
    "Underlying trial answers and recorded evidence remain available; this is not an assessed-empty result."
)


@dataclass(frozen=True)
class PurposeGoalData:
    text: str
    source: str
    basis: str
    reference: str


@dataclass(frozen=True)
class EvidenceLimitsData:
    per_excerpt_characters: int
    per_trial_characters: int
    per_run_characters: int
    per_trial_records: int
    selection: str
    privacy: str
    provenance: str


def parse_evidence_limits(raw):
    if raw is None:
        return None
    if type(raw) is not dict or set(raw) != set(
        EvidenceLimitsData.__dataclass_fields__
    ):
        raise ValueError("invalid recorded evidence limits")
    for name in (
        "per_excerpt_characters",
        "per_trial_characters",
        "per_run_characters",
        "per_trial_records",
    ):
        if type(raw[name]) is not int or raw[name] <= 0:
            raise ValueError("invalid recorded evidence budget")
    for name in ("selection", "privacy", "provenance"):
        _text(raw[name], 600)
    return EvidenceLimitsData(**raw)


@dataclass(frozen=True)
class EvidenceRangeData:
    start: int
    end: int
    unit: str


@dataclass(frozen=True)
class RecordedEvidenceData:
    trial: str
    id: str
    source: str
    range: EvidenceRangeData
    text: str
    status: str
    reason: str


@dataclass(frozen=True)
class TrialAssessmentData:
    trial: str
    outcome: str
    refs: Tuple[str, ...]
    explanation: str
    output_excerpt: str


@dataclass(frozen=True)
class TargetCriterionData:
    id: str
    goal: int
    text: str
    mode: str
    required_evidence: str
    evidence_kind: str
    decisions: Tuple[int, ...]
    before: Tuple[TrialAssessmentData, ...]
    after: Tuple[TrialAssessmentData, ...]


@dataclass(frozen=True)
class TargetAssessmentData:
    criteria: Tuple[TargetCriterionData, ...]


def parse_purpose(raw):
    if raw is None:
        return ()
    if type(raw) is not dict or set(raw) != {"goals"}:
        raise ValueError("purpose must contain goals")
    goals = raw["goals"]
    if type(goals) is not list or not 1 <= len(goals) <= 8:
        raise ValueError("purpose needs one to eight distinct goals")
    parsed = []
    for goal in goals:
        if type(goal) is not dict or set(goal) != {
            "text",
            "source",
            "basis",
            "reference",
        }:
            raise ValueError("invalid purpose goal")
        if (
            type(goal["source"]) is not str
            or type(goal["basis"]) is not str
            or goal["source"] not in ("session", "commit", "diff")
            or goal["basis"] not in ("explicit", "inferred")
        ):
            raise ValueError("invalid purpose provenance")
        if goal["source"] == "diff" and goal["basis"] != "inferred":
            raise ValueError("diff purpose must be inferred")
        parsed.append(
            PurposeGoalData(
                _text(goal["text"], 1200),
                goal["source"],
                goal["basis"],
                _text(goal["reference"], 240),
            )
        )
    if len({" ".join(goal.text.split()).casefold() for goal in parsed}) != len(parsed):
        raise ValueError("duplicate purpose goals")
    return tuple(parsed)


def effective_purpose(purpose, intent):
    if purpose:
        return purpose
    if intent is not None:
        return (
            PurposeGoalData(
                intent.text,
                "diff",
                "inferred",
                "Instruction diff hunks " + ", ".join(map(str, intent.edit_hunks)),
            ),
        )
    return ()


def evidence_records(raw):
    """Retain omission metadata as well as readable recorded content."""
    if raw is None:
        return ()
    trials = raw.get("trials") if type(raw) is dict else None
    if type(trials) is not dict:
        raise ValueError("invalid recorded evidence")
    parsed = []
    seen = set()
    run_characters = 0
    for trial, entries in trials.items():
        if (
            type(trial) is not str
            or type(entries) is not list
            or len(entries) > RECORD_LIMIT + 1
        ):
            raise ValueError("invalid recorded evidence trial")
        trial_characters = 0
        for entry in entries:
            if type(entry) is not dict or set(entry) != {
                "id",
                "source",
                "range",
                "text",
                "status",
                "reason",
            }:
                raise ValueError("invalid recorded evidence entry")
            identifier = entry.get("id")
            region = entry.get("range")
            status = entry.get("status")
            if (
                type(identifier) is not str
                or re.fullmatch(
                    re.escape(trial) + r":(?:tool-[1-9][0-9]*|trace|overflow)",
                    identifier,
                )
                is None
                or identifier in seen
            ):
                raise ValueError("invalid recorded evidence identity")
            if status not in ("available", "truncated", "omitted", "unavailable"):
                raise ValueError("invalid recorded evidence status")
            if (
                identifier.endswith(":trace")
                and status != "unavailable"
                or identifier.endswith(":overflow")
                and status != "omitted"
            ):
                raise ValueError("invalid evidence availability metadata")
            if (
                type(region) is not dict
                or set(region) != {"start", "end", "unit"}
                or region.get("unit") != "characters"
                or type(region.get("start")) is not int
                or type(region.get("end")) is not int
                or not 0 <= region["start"] <= region["end"]
            ):
                raise ValueError("invalid returned-content range")
            for name in ("source", "text", "reason"):
                if type(entry.get(name)) is not str:
                    raise ValueError("invalid recorded evidence text")
            trial_characters += len(entry["text"])
            run_characters += len(entry["text"])
            if (
                len(entry["source"]) > SOURCE_LIMIT
                or len(entry["text"]) > EXCERPT_LIMIT
                or trial_characters > TRIAL_LIMIT
                or run_characters > RUN_LIMIT
            ):
                raise ValueError("recorded evidence exceeds the assessment budget")
            if region["end"] - region["start"] != len(entry["text"]):
                raise ValueError("recorded evidence range disagrees with excerpt")
            if status in ("omitted", "unavailable") and entry["text"]:
                raise ValueError("unavailable evidence must not carry content")
            seen.add(identifier)
            parsed.append(
                RecordedEvidenceData(
                    trial,
                    identifier,
                    entry["source"],
                    EvidenceRangeData(**region),
                    entry["text"],
                    status,
                    entry["reason"],
                )
            )
    return tuple(parsed)


def persisted_evidence(raw):
    if type(raw) is not list:
        raise ValueError("invalid persisted recorded evidence")
    trials = {}
    for entry in raw:
        if type(entry) is not dict or type(entry.get("trial")) is not str:
            raise ValueError("invalid persisted evidence trial")
        trials.setdefault(entry["trial"], []).append(
            {key: value for key, value in entry.items() if key != "trial"}
        )
    return evidence_records({"trials": trials})


def parse_target(raw, purpose, final_answers, evidence, rows=(), positions=None):
    """Invalid assessments stay unavailable, never become successful or assessed-empty."""
    if raw is None:
        return None
    try:
        if (
            type(raw) is not dict
            or set(raw) != {"criteria"}
            or type(raw["criteria"]) is not list
            or not 1 <= len(raw["criteria"]) <= 16
            or not purpose
        ):
            raise ValueError("invalid target criteria")
        positions = (
            positions
            if positions is not None
            else {i: i for i in range(1, len(rows) + 1)}
        )
        records = {entry.id: entry for entry in evidence}
        criteria = []
        seen = set()
        covered_goals = set()
        for item in raw["criteria"]:
            if type(item) is not dict or set(item) != {
                "id",
                "goal",
                "text",
                "mode",
                "required_evidence",
                "evidence_kind",
                "decisions",
                "before",
                "after",
            }:
                raise ValueError("invalid criterion fields")
            identifier = _text(item["id"], 80)
            goal = item["goal"]
            if (
                identifier != item["id"]
                or identifier in seen
                or type(goal) is not int
                or not 1 <= goal <= len(purpose)
                or item["mode"] not in MODES
            ):
                raise ValueError("invalid criterion identity")
            if item["evidence_kind"] not in (
                "output",
                "source_consistency",
                "recorded_action",
            ):
                raise ValueError("invalid criterion evidence requirement")
            references = item["decisions"]
            if (
                type(references) is not list
                or any(
                    type(ref) is not int or ref not in positions for ref in references
                )
                or len(set(references)) != len(references)
            ):
                raise ValueError("invalid criterion row references")
            sides = []
            for side in ("before", "after"):
                expected = {
                    name
                    for name, answer in (final_answers or {}).get(side, {}).items()
                    if answer.strip()
                }
                trials = item[side]
                if (
                    not expected
                    or type(trials) is not list
                    or len(trials) != len(expected)
                ):
                    raise ValueError("target must assess every completed trial")
                outcomes = []
                assigned = set()
                for trial in trials:
                    if type(trial) is not dict or set(trial) != {
                        "trial",
                        "outcome",
                        "refs",
                        "explanation",
                        "output_excerpt",
                    }:
                        raise ValueError("invalid target trial")
                    name = trial["trial"]
                    outcome = trial["outcome"]
                    refs = trial["refs"]
                    if (
                        type(name) is not str
                        or name not in expected
                        or name in assigned
                        or outcome not in OUTCOMES
                        or type(refs) is not list
                        or any(type(ref) is not str for ref in refs)
                        or len(set(refs)) != len(refs)
                    ):
                        raise ValueError("invalid target trial membership")
                    excerpt = trial["output_excerpt"]
                    if (
                        type(excerpt) is not str
                        or len(excerpt) > 1200
                        or (
                            excerpt
                            and (
                                name + ":answer" not in refs
                                or excerpt not in final_answers[side][name]
                            )
                        )
                    ):
                        raise ValueError(
                            "target output excerpt must be exact and trial-local"
                        )
                    for ref in refs:
                        if ref == name + ":answer":
                            continue
                        if ref not in records or records[ref].trial != name:
                            raise ValueError(
                                "target reference must resolve in its own trial"
                            )
                    usable = [
                        ref
                        for ref in refs
                        if ref == name + ":answer"
                        or records[ref].status in ("available", "truncated")
                        and records[ref].text
                    ]
                    if outcome in ("met", "not_met") and (
                        not refs or len(usable) != len(refs)
                    ):
                        raise ValueError(
                            "determinate target outcome needs available evidence"
                        )
                    if outcome in ("met", "not_met"):
                        has_output = name + ":answer" in refs
                        has_source = any(ref != name + ":answer" for ref in usable)
                        if (
                            item["evidence_kind"] == "source_consistency"
                            and not (has_output and has_source)
                            or item["evidence_kind"] == "output"
                            and not has_output
                            or item["evidence_kind"] == "recorded_action"
                            and not has_source
                        ):
                            raise ValueError(
                                "criterion lacks required source or output evidence"
                            )
                        if (
                            item["evidence_kind"] in ("output", "source_consistency")
                            and not excerpt.strip()
                        ):
                            raise ValueError(
                                "output assessment needs its relevant exact excerpt"
                            )
                    assigned.add(name)
                    outcomes.append(
                        TrialAssessmentData(
                            name,
                            outcome,
                            tuple(refs),
                            _text(trial["explanation"], 600),
                            excerpt,
                        )
                    )
                sides.append(tuple(outcomes))
            seen.add(identifier)
            covered_goals.add(goal)
            criteria.append(
                TargetCriterionData(
                    identifier,
                    goal,
                    _text(item["text"], 600),
                    item["mode"],
                    _text(item["required_evidence"], 600),
                    item["evidence_kind"],
                    tuple(positions[ref] for ref in references),
                    *sides,
                )
            )
        if covered_goals != set(range(1, len(purpose) + 1)):
            raise ValueError("target criteria must cover every purpose goal")
        return TargetAssessmentData(tuple(criteria))
    except (KeyError, TypeError, ValueError, AttributeError):
        return None


def distribution(criterion, side):
    counts = Counter(trial.outcome for trial in getattr(criterion, side))
    return "; ".join(
        f"{counts[outcome]} {outcome.replace('_', ' ')}"
        for outcome in OUTCOMES
        if counts[outcome]
    )


def conclusion(criterion):
    before = Counter(trial.outcome for trial in criterion.before)
    after = Counter(trial.outcome for trial in criterion.after)
    if before.get("unassessable", 0) == len(criterion.before) and after.get(
        "unassessable", 0
    ) == len(criterion.after):
        return "Not enough evidence to answer the target question."
    if before.get("met", 0) == len(criterion.before) and after.get("met", 0) == len(
        criterion.after
    ):
        return (
            "The targeted behavior was preserved in these trials."
            if criterion.mode == "preservation"
            else "Before already met the target; no incremental benefit was demonstrated in these trials."
        )
    if after.get("not_met", 0):
        if criterion.mode == "preservation":
            return "Behavior intended to survive was lost in at least one After trial."
        if before.get("not_met", 0):
            return "The target remains unmet in at least one After trial."
        return "At least one After trial did not meet the target."
    if after.get("met", 0) == len(criterion.after) and before.get("not_met", 0) == len(
        criterion.before
    ):
        return "All observed After trials met the target; Before did not. This does not establish causation or general reliability."
    return "Target outcomes are mixed or uncertain; retain each trial's outcome rather than a single pass/fail verdict."


def acceptance(criterion):
    if any(trial.outcome == "not_met" for trial in criterion.after):
        return "Decide whether to accept the edit with the observed target problem still present; inspect the affected After trials."
    if any(
        trial.outcome in ("uncertain", "unassessable")
        for trial in criterion.before + criterion.after
    ):
        return "Resolve the stated evidence gaps before drawing a stronger conclusion about the target."
    return "These trials support only the observed target outcome, not automatic acceptance, causation, or reliability on other scenarios."


def coverage(report, criterion, side):
    assessed = len(getattr(criterion, side))
    total = getattr(report.variants, side).total
    return f"{assessed} completed trials assessed of {total} total records"


def evidence_limit_text(limits):
    if limits is None:
        return "Recorded evidence budget metadata unavailable."
    return (
        f"At most {limits.per_excerpt_characters} characters per excerpt, "
        f"{limits.per_trial_characters} per trial, {limits.per_run_characters} per run, "
        f"and {limits.per_trial_records} tool records per trial. "
        f"Selection: {limits.selection}. {limits.privacy} {limits.provenance}"
    )
