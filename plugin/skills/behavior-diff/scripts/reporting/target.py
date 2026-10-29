"""Validate target criteria against immutable purpose and recorded trial evidence."""

from collections import Counter
import re
from dataclasses import dataclass
from typing import Optional, Tuple

from reporting.evidence import (
    EXCERPT_LIMIT,
    RECORD_LIMIT,
    RUN_LIMIT,
    SOURCE_LIMIT,
    TRIAL_LIMIT,
    UNPROVEN_CALL_REASONS,
)
from reporting.explanation import _text
from reporting.sources import SENSITIVE_SOURCE, unmet_source_requirements

OUTCOMES = ("met", "not_met", "uncertain", "unassessable")
MODES = ("correction", "new", "change", "preservation")
EVIDENCE_KINDS = ("output", "source_consistency", "recorded_action")
_DEFINITION = ("id", "goal", "text", "mode", "required_evidence", "evidence_kind")
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
    rejection: Optional[str] = None


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
            or len(entries) > RECORD_LIMIT + 17
        ):
            raise ValueError("invalid recorded evidence trial")
        trial_characters = 0
        ordinary_records = 0
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
                    re.escape(trial)
                    + r":(?:tool-[1-9][0-9]*|artifact-(?:[1-9]|1[0-6])|trace|overflow)",
                    identifier,
                )
                is None
                or identifier in seen
            ):
                raise ValueError("invalid recorded evidence identity")
            if ":artifact-" not in identifier:
                ordinary_records += 1
                if ordinary_records > RECORD_LIMIT + 1:
                    raise ValueError("invalid recorded evidence trial")
            elif status in ("available", "truncated") and (
                type(entry.get("source")) is not str
                or re.fullmatch(r"artifact .+ sha256:[a-f0-9]{64}", entry["source"])
                is None
            ):
                raise ValueError("invalid captured artifact descriptor")
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


def _returned_content(record):
    return record.status in ("available", "truncated") and bool(record.text)


def _captured_call(record):
    """A captured call record proves that its listed call ran, not what it returned."""
    return (
        re.fullmatch(r".+:tool-[1-9][0-9]*", record.id) is not None
        and record.source != SENSITIVE_SOURCE
        and record.reason not in UNPROVEN_CALL_REASONS
    )


def parse_target(
    raw,
    purpose,
    final_answers,
    evidence,
    rows=(),
    positions=None,
    *,
    scenario=None,
    persisted=False,
):
    """Retain rejected checks without treating them as assessed outcomes."""
    return check_target(
        raw,
        purpose,
        final_answers,
        evidence,
        rows,
        positions,
        scenario=scenario,
        persisted=persisted,
    )[0]


def _criterion_definition(item, purpose, seen, frozen):
    if type(item) is not dict:
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
    if item["evidence_kind"] not in EVIDENCE_KINDS:
        raise ValueError("invalid criterion evidence requirement")
    definition = (
        identifier,
        goal,
        _text(item["text"], 600),
        item["mode"],
        _text(item["required_evidence"], 600),
        item["evidence_kind"],
    )
    if frozen is not None and (
        identifier not in frozen
        or definition
        != tuple(getattr(frozen[identifier], name) for name in _DEFINITION)
    ):
        raise ValueError("target criterion must restate its frozen scenario check")
    return definition


def _criterion_assessment(
    item,
    definition,
    final_answers,
    records,
    positions,
    requirements,
    persisted,
    artifact_paths=(),
):
    fields = set(_DEFINITION) | {"decisions", "before", "after"}
    if set(item) not in (fields, fields | {"rejection"}):
        raise ValueError("invalid criterion fields")
    rejection = item.get("rejection")
    if rejection is not None:
        if (
            not persisted
            or _text(rejection, 240) != rejection
            or any(item[field] != [] for field in ("decisions", "before", "after"))
        ):
            raise ValueError("invalid persisted criterion rejection")
        return TargetCriterionData(*definition, (), (), (), rejection)
    references = item["decisions"]
    if (
        type(references) is not list
        or any(type(ref) is not int or ref not in positions for ref in references)
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
        if not expected or type(trials) is not list or len(trials) != len(expected):
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
            name, outcome, refs = trial["trial"], trial["outcome"], trial["refs"]
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
            if type(excerpt) is not str or len(excerpt) > 1200:
                raise ValueError("invalid target output excerpt")
            output_sources = [
                final_answers[side][name] for ref in refs if ref == name + ":answer"
            ]
            output_sources.extend(
                record.text
                for ref in refs
                if (record := records.get(ref)) is not None
                and record.trial == name
                and ":artifact-" in record.id
                and _returned_content(record)
                and any(
                    record.source.startswith("artifact " + path + " sha256:")
                    for path in artifact_paths
                )
            )
            if excerpt and not output_sources:
                raise ValueError(
                    "target output excerpt must cite its trial answer or required artifact"
                )
            if excerpt and not any(excerpt in text for text in output_sources):
                raise ValueError("target output excerpt must be exact and trial-local")
            for ref in refs:
                if ref != name + ":answer" and (
                    ref not in records or records[ref].trial != name
                ):
                    raise ValueError("target reference must resolve in its own trial")
            answer = name + ":answer"
            content = [
                ref for ref in refs if ref != answer and _returned_content(records[ref])
            ]
            calls = [
                ref for ref in refs if ref != answer and _captured_call(records[ref])
            ]
            if outcome in ("met", "not_met"):
                if not refs or any(
                    ref != answer and ref not in content and ref not in calls
                    for ref in refs
                ):
                    raise ValueError(
                        "determinate target outcome needs available evidence"
                    )
                has_output = bool(output_sources)
                for path in artifact_paths:
                    if not any(
                        records[ref].source.startswith("artifact " + path + " sha256:")
                        for ref in content
                        if ":artifact-" in ref
                    ):
                        raise ValueError("criterion lacks a required captured artifact")
                if (
                    item["evidence_kind"] == "source_consistency"
                    and not (has_output and content)
                    or item["evidence_kind"] == "output"
                    and not has_output
                    or item["evidence_kind"] == "recorded_action"
                    and not calls
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
                if unmet_source_requirements(
                    requirements,
                    definition[0],
                    (records[ref].source for ref in content if ref in calls),
                ):
                    raise ValueError("criterion lacks a required frozen source")
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
    return TargetCriterionData(
        *definition, tuple(positions[ref] for ref in references), *sides
    )


def check_target(
    raw,
    purpose,
    final_answers,
    evidence,
    rows=(),
    positions=None,
    *,
    scenario=None,
    persisted=False,
):
    """Validate identities globally, then isolate each check's evidence failures.

    Missing, duplicate or rewritten definitions invalidate the whole assessment.
    A rejected check retains its definition and diagnostic, never invented outcomes.
    Only persisted producer output may carry an existing rejection diagnostic.
    """
    if raw is None:
        return None, None
    try:
        if (
            type(raw) is not dict
            or set(raw) != {"criteria"}
            or type(raw["criteria"]) is not list
            or not 1 <= len(raw["criteria"]) <= 16
            or not purpose
        ):
            raise ValueError("invalid target criteria")
        frozen = (
            {check.id: check for check in scenario.checks}
            if scenario is not None
            else None
        )
        definitions, seen, covered_goals = [], set(), set()
        for item in raw["criteria"]:
            definition = _criterion_definition(item, purpose, seen, frozen)
            definitions.append(definition)
            seen.add(definition[0])
            covered_goals.add(definition[1])
        if covered_goals != set(range(1, len(purpose) + 1)):
            raise ValueError("target criteria must cover every purpose goal")
        if frozen is not None and seen != set(frozen):
            raise ValueError("target criteria must assess every frozen scenario check")
        positions = (
            positions
            if positions is not None
            else {i: i for i in range(1, len(rows) + 1)}
        )
        records = {entry.id: entry for entry in evidence}
        criteria = []
        for item, definition in zip(raw["criteria"], definitions):
            requirements = (
                tuple(
                    requirement
                    for requirement in scenario.source_requirements
                    if requirement.check == definition[0]
                )
                if scenario is not None
                else ()
            )
            try:
                criterion = _criterion_assessment(
                    item,
                    definition,
                    final_answers,
                    records,
                    positions,
                    requirements,
                    persisted,
                    tuple(
                        path
                        for requirement in (
                            scenario.artifact_requirements if scenario else ()
                        )
                        if requirement.check == definition[0]
                        for path in requirement.paths
                    ),
                )
            except ValueError as error:
                criterion = TargetCriterionData(*definition, (), (), (), str(error))
            except (KeyError, TypeError, AttributeError):
                criterion = TargetCriterionData(
                    *definition, (), (), (), "malformed criterion assessment"
                )
            criteria.append(criterion)
        if scenario is not None:
            order = {check.id: index for index, check in enumerate(scenario.checks)}
            criteria.sort(key=lambda criterion: order[criterion.id])
        return TargetAssessmentData(tuple(criteria)), None
    except ValueError as error:
        return None, str(error)
    except (KeyError, TypeError, AttributeError):
        return None, "malformed target assessment"


def distribution(criterion, side):
    counts = Counter(trial.outcome for trial in getattr(criterion, side))
    return "; ".join(
        f"{counts[outcome]} {outcome.replace('_', ' ')}"
        for outcome in OUTCOMES
        if counts[outcome]
    )


def conclusion(criterion):
    if criterion.rejection:
        return "Not assessed: " + criterion.rejection + "."
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
            return "At least one After trial did not meet the preservation target."
        if before.get("not_met", 0):
            return "The target remains unmet in at least one After trial."
        return "At least one After trial did not meet the target."
    if after.get("met", 0) == len(criterion.after) and before.get("not_met", 0) == len(
        criterion.before
    ):
        return "All observed After trials met the target; Before did not. This does not establish causation or general reliability."
    return "Target outcomes are mixed or uncertain; retain each trial's outcome rather than a single pass/fail verdict."


def acceptance(criterion):
    if criterion.rejection:
        return "Resolve the rejected evidence before drawing a conclusion about this check."
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
        f"and {limits.per_trial_records} captured records per trial. "
        f"Selection: {limits.selection}. {limits.privacy} {limits.provenance}"
    )
