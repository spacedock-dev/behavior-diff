"""Validate optional attention assessments without generating or hiding evidence."""

import re
from dataclasses import dataclass
from typing import Optional, Tuple

from reporting.explanation import _text as _plain_text
from reporting.summary import EVIDENCE_KINDS, NarrativeClaimData

ATTENTION_ICONS = (
    "neutral",
    "continue",
    "stop",
    "report",
    "edit",
    "inspect",
    "test",
    "delegate",
    "agent",
    "person",
    "clock",
    "file",
    "shared",
    "optional",
    "required",
)
_RELATIONSHIPS = ("expected", "additional", "unclear")
_URL = re.compile(
    r"[a-z][a-z0-9+.-]*://|www\.|(?:https?|mailto|tel|javascript|data):",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class AttentionStepData:
    icon: str
    label: str


@dataclass(frozen=True)
class AttentionChoiceData:
    choice: str
    steps: Tuple[AttentionStepData, ...]


@dataclass(frozen=True)
class AttentionFindingData:
    decision: int
    title: str
    matters_if: str
    consequence: str
    next_step: str
    evidence_kind: str
    relationship: str
    before: Tuple[AttentionChoiceData, ...]
    after: Tuple[AttentionChoiceData, ...]
    explanation: str
    context: Tuple[NarrativeClaimData, ...]
    limit: str
    status: str = "observed_difference"
    criterion: Optional[str] = None


@dataclass(frozen=True)
class AttentionData:
    assessment: str
    findings: Tuple[AttentionFindingData, ...]


def _text(value, limit):
    text = _plain_text(value, limit)
    if _URL.search(text):
        raise ValueError("attention must not contain URLs")
    return text


def _fields(value, names):
    if type(value) is not dict or set(value) != set(names):
        raise ValueError("invalid attention fields")
    return value


def _row_field(row, name):
    return row[name] if type(row) is dict else getattr(row, name)


def _reference(ref, positions, row_count):
    if type(ref) is not int or ref not in positions:
        raise ValueError("invalid attention reference")
    mapped = positions[ref]
    if type(mapped) is not int or not 1 <= mapped <= row_count:
        raise ValueError("invalid surviving attention reference")
    return mapped


def _distribution(row, side):
    branches = _row_field(row, side)
    if type(branches) not in (list, tuple) or not branches:
        raise ValueError("attention needs observed branches on each side")
    counts = {}
    for branch in branches:
        choice = _row_field(branch, "choice")
        count = (
            branch.get("n", branch.get("count"))
            if type(branch) is dict
            else branch.count
        )
        if (
            type(choice) is not str
            or not choice.strip()
            or choice in counts
            or type(count) is not int
            or count <= 0
        ):
            raise ValueError("invalid attention row distribution")
        counts[choice] = count
    return counts


def _choices(raw, names):
    if type(raw) is not list or len(raw) != len(names):
        raise ValueError("attention must cover every branch")
    choices = []
    for item in raw:
        _fields(item, ("choice", "steps"))
        choice = _text(item["choice"], 1000)
        # Branch identities are exact, not a normalized narrative approximation.
        if choice != item["choice"]:
            raise ValueError("attention branch identity must be exact")
        steps = item["steps"]
        if type(steps) is not list or len(steps) != 2:
            raise ValueError("each attention branch needs exactly two steps")
        parsed_steps = []
        for step in steps:
            _fields(step, ("icon", "label"))
            icon = step["icon"]
            if type(icon) is not str or icon not in ATTENTION_ICONS:
                raise ValueError("invalid attention icon")
            parsed_steps.append(AttentionStepData(icon, _text(step["label"], 80)))
        choices.append(AttentionChoiceData(choice, tuple(parsed_steps)))
    if len({choice.choice for choice in choices}) != len(choices) or {
        choice.choice for choice in choices
    } != set(names):
        raise ValueError("attention must cover exact row branches")
    return tuple(choices)


def parse_attention(raw, rows, positions=None, target=None) -> Optional[AttentionData]:
    """Reject an invalid bundle, never reinterpret it as an assessed-empty result.

    References follow surviving sorted rows. Counts stay solely in those rows;
    no finding can omit a minority branch or turn alternatives into a sequence.
    """
    if raw is None:
        return None
    if positions is None:
        positions = {index: index for index in range(1, len(rows) + 1)}
    try:
        _fields(raw, ("assessment", "findings"))
        assessment = _text(raw["assessment"], 600)
        if type(raw["findings"]) is not list or len(raw["findings"]) > len(rows):
            raise ValueError("invalid attention findings")
        findings = []
        seen = set()
        for item in raw["findings"]:
            _fields(
                item,
                (
                    "decision",
                    "title",
                    "matters_if",
                    "consequence",
                    "next_step",
                    "evidence_kind",
                    "relationship",
                    "status",
                    "criterion",
                    "before",
                    "after",
                    "explanation",
                    "context",
                    "limit",
                ),
            )
            decision = _reference(item["decision"], positions, len(rows))
            if decision in seen:
                raise ValueError("duplicate attention comparison")
            seen.add(decision)
            row = rows[decision - 1]
            before = _distribution(row, "before")
            after = _distribution(row, "after")
            before_total, after_total = sum(before.values()), sum(after.values())
            changed = any(
                before.get(choice, 0) * after_total
                != after.get(choice, 0) * before_total
                for choice in before.keys() | after.keys()
            )
            status = item["status"]
            if status not in (
                "pre_existing_problem",
                "observed_difference",
                "hypothetical_consequence",
            ):
                raise ValueError("invalid concern evidence status")
            criterion = item["criterion"]
            assessed = (
                next(
                    (value for value in target.criteria if value.id == criterion), None
                )
                if target is not None
                else None
            )
            if criterion is not None and (
                type(criterion) is not str or assessed is None
            ):
                raise ValueError("unknown attention target criterion")
            if not changed and not (
                assessed is not None
                and decision in assessed.decisions
                and status == "pre_existing_problem"
                and item["relationship"] == "expected"
                and any(value.outcome == "not_met" for value in assessed.before)
                and any(value.outcome == "not_met" for value in assessed.after)
            ):
                raise ValueError("unchanged attention needs an assessed target problem")
            kind = item["evidence_kind"]
            anchor = _row_field(row, "anchor")
            if (
                type(kind) is not str
                or kind not in EVIDENCE_KINDS
                or not (
                    kind in ("plans", "answers")
                    and anchor == "answer"
                    or kind == "actions"
                    and type(anchor) is int
                    and anchor >= 1
                )
            ):
                raise ValueError("attention evidence kind disagrees with anchor")
            relationship = item["relationship"]
            if type(relationship) is not str or relationship not in _RELATIONSHIPS:
                raise ValueError("invalid attention relationship")
            if type(item["context"]) is not list:
                raise ValueError("invalid attention context")
            context = []
            for claim in item["context"]:
                _fields(claim, ("text", "decisions"))
                refs = claim["decisions"]
                if type(refs) is not list or not refs:
                    raise ValueError("attention context needs evidence references")
                mapped = tuple(_reference(ref, positions, len(rows)) for ref in refs)
                if len(set(mapped)) != len(mapped):
                    raise ValueError("duplicate attention context reference")
                context.append(NarrativeClaimData(_text(claim["text"], 480), mapped))
            findings.append(
                AttentionFindingData(
                    decision,
                    _text(item["title"], 120),
                    _text(item["matters_if"], 480),
                    _text(item["consequence"], 480),
                    _text(item["next_step"], 480),
                    kind,
                    relationship,
                    _choices(item["before"], before),
                    _choices(item["after"], after),
                    _text(item["explanation"], 600),
                    tuple(context),
                    _text(item["limit"], 480),
                    status,
                    criterion,
                )
            )
        return AttentionData(assessment, tuple(findings))
    except (KeyError, TypeError, ValueError, IndexError, AttributeError):
        return None
