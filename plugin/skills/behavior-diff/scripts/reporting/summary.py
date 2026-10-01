"""Validate optional extractor narrative and derive an evidence-safe visual summary."""

from dataclasses import dataclass
from typing import Optional, Tuple

ICONS = ("neutral", "continue", "stop", "report", "edit", "inspect", "test", "delegate")
EVIDENCE_KINDS = ("plans", "answers", "actions")
SUMMARY_STATUSES = ("changed", "unchanged", "mixed", "unavailable")


@dataclass(frozen=True)
class NarrativeChoiceData:
    choice: str
    label: str
    detail: str


@dataclass(frozen=True)
class NarrativeSideData:
    icon: str
    choices: Tuple[NarrativeChoiceData, ...]


@dataclass(frozen=True)
class NarrativeClaimData:
    text: str
    decisions: Tuple[int, ...]


@dataclass(frozen=True)
class NarrativeData:
    decision: int
    headline: str
    scenario: str
    evidence_kind: str
    before: NarrativeSideData
    after: NarrativeSideData
    why: Optional[NarrativeClaimData]
    caution: Optional[NarrativeClaimData]


def _text(value, limit):
    if type(value) is not str or not value.strip() or len(value.strip()) > limit:
        raise ValueError("invalid narrative text")
    if any(ord(char) < 32 for char in value) or "<" in value or ">" in value:
        raise ValueError("narrative must contain plain text")
    return value.strip()


def _row_field(row, name):
    return row[name] if type(row) is dict else getattr(row, name)


def parse_narrative(raw, rows, positions=None):
    """Discard only unsupported narrative; retain existing decision observations."""
    if raw is None:
        return None
    if positions is None:
        positions = {index: index for index in range(1, len(rows) + 1)}
    try:
        if type(raw) is not dict or type(raw.get("decision")) is not int:
            raise ValueError("invalid narrative decision")
        decision = positions[raw["decision"]]
        row = rows[decision - 1]
        kind = raw["evidence_kind"]
        anchor = _row_field(row, "anchor")
        if type(kind) is not str or kind not in EVIDENCE_KINDS:
            raise ValueError("invalid narrative evidence kind")
        if not (
            kind in ("plans", "answers")
            and anchor == "answer"
            or kind == "actions"
            and type(anchor) is int
            and anchor >= 1
        ):
            raise ValueError("narrative evidence kind disagrees with anchor")
        sides = []
        for side in ("before", "after"):
            source = raw[side]
            if type(source) is not dict or type(source.get("choices")) is not list:
                raise ValueError("invalid narrative side")
            names = tuple(
                _row_field(choice, "choice") for choice in _row_field(row, side)
            )
            choices = tuple(
                NarrativeChoiceData(
                    _text(choice["choice"], 1000),
                    _text(choice["label"], 80),
                    _text(choice["detail"], 200),
                )
                for choice in source["choices"]
                if type(choice) is dict
            )
            if (
                len(choices) != len(source["choices"])
                or len(choices) != len(names)
                or len({choice.choice for choice in choices}) != len(choices)
                or {choice.choice for choice in choices} != set(names)
            ):
                raise ValueError(
                    "narrative choices must cover the selected row exactly"
                )
            icon = source.get("icon")
            sides.append(
                NarrativeSideData(
                    icon if type(icon) is str and icon in ICONS else "neutral", choices
                )
            )
        claims = []
        for name in ("why", "caution"):
            claim = raw.get(name)
            if claim is None:
                claims.append(None)
                continue
            if type(claim) is not dict or type(claim.get("decisions")) is not list:
                raise ValueError("invalid narrative claim")
            refs = claim["decisions"]
            if (
                not refs
                or any(type(ref) is not int or ref not in positions for ref in refs)
                or len(set(refs)) != len(refs)
            ):
                raise ValueError("invalid narrative claim references")
            claims.append(
                NarrativeClaimData(
                    _text(claim["text"], 240), tuple(positions[ref] for ref in refs)
                )
            )
        return NarrativeData(
            decision,
            _text(raw["headline"], 120),
            _text(raw["scenario"], 220),
            kind,
            sides[0],
            sides[1],
            claims[0],
            claims[1],
        )
    except (KeyError, TypeError, ValueError, IndexError):
        return None


def _row_status(row, decisions):
    from reporting import content

    if not content.valid_decision_choices(row, decisions):
        return "unavailable"
    if content.unanimous_choices(row, decisions) is None:
        return "mixed"
    return "changed" if content.choices_changed(row.before, row.after) else "unchanged"


def _lead_candidates(decisions):
    """Prefer outcomes and meaningful process differences over answer wording."""
    rows = decisions.rows
    outcome = decisions.outcome
    if outcome and _row_status(rows[outcome - 1], decisions) == "changed":
        return (outcome,)
    changed_actions = tuple(
        index
        for index, row in enumerate(rows, 1)
        if type(row.anchor) is int and _row_status(row, decisions) == "changed"
    )
    if changed_actions:
        return changed_actions
    if outcome and _row_status(rows[outcome - 1], decisions) == "mixed":
        return (outcome,)
    mixed_actions = tuple(
        index
        for index, row in enumerate(rows, 1)
        if type(row.anchor) is int
        and _row_status(row, decisions) == "mixed"
        and content_changed(row)
    )
    if mixed_actions:
        return mixed_actions
    linked_changes = tuple(
        index
        for index, row in enumerate(rows, 1)
        if row.edit_hunks
        and _row_status(row, decisions) != "unavailable"
        and content_changed(row)
    )
    if linked_changes:
        return linked_changes
    if outcome and _row_status(rows[outcome - 1], decisions) != "unavailable":
        return (outcome,)
    linked = tuple(
        index
        for index, row in enumerate(rows, 1)
        if row.edit_hunks and _row_status(row, decisions) != "unavailable"
    )
    return linked or tuple(
        index
        for index, row in enumerate(rows, 1)
        if _row_status(row, decisions) != "unavailable"
    )


def content_changed(row):
    from reporting.content import choices_changed

    return choices_changed(row.before, row.after)


def build_summary(metadata, variants, decisions):
    from reporting import content
    from reporting.schema import (
        EvidenceClaimData,
        SummaryChoiceData,
        SummarySideData,
        VisualSummaryData,
    )

    complete = content.complete_evidence(variants, decisions)
    candidates = _lead_candidates(decisions)
    if (
        decisions.before_count != variants.before.total
        or decisions.after_count != variants.after.total
    ):
        candidates = ()
    narrative = decisions.narrative
    if not complete or narrative is None or narrative.decision not in candidates:
        narrative = None
    lead = narrative.decision if narrative else next(iter(candidates), None)
    row = decisions.rows[lead - 1] if lead else None
    status = _row_status(row, decisions) if row else "unavailable"
    if not complete:
        status = "unavailable"
    notices = [
        "One scenario only; counts and narrative are model interpretations, not causal proof."
    ]
    if not complete:
        notices.append(
            "Trial evidence is incomplete, blocked, invalid, or dropped; inspect the trial records."
        )
    if variants.before.total == 1 or variants.after.total == 1:
        notices.append(
            "At least one side has one trial; differences may reflect trial-to-trial variation."
        )
    primary_status = (
        _row_status(decisions.rows[decisions.outcome - 1], decisions)
        if decisions.outcome
        else "unavailable"
    )
    if primary_status == "mixed":
        notices.append(
            "The primary result has mixed trial choices; see its full distribution in Decision diff."
        )
    elif primary_status == "unavailable":
        notices.append(
            "No primary result was identified; this comparison cannot establish a result change."
        )
    different_process = (
        complete
        and primary_status == "unchanged"
        and any(
            type(value.anchor) is int
            and content_changed(value)
            and _row_status(value, decisions) in ("changed", "mixed")
            for value in decisions.rows
        )
    )
    if different_process:
        notices.append(
            "The primary result is the same; process choices differ in this scenario."
        )
    if not narrative:
        notices.append(
            "Plain-language narrative unavailable; original extracted choices are shown without added explanation."
        )
    if status == "unavailable":
        headline = "Insufficient evidence for a Before/After conclusion."
    elif narrative:
        headline = narrative.headline
    elif different_process:
        headline = "Same result; different process choices."
    elif status == "mixed":
        headline = "Trial choices vary in this scenario."
    elif status == "changed":
        headline = "Different choices were observed in this scenario."
    else:
        headline = "No difference was observed in the selected comparison."
    if status == "unchanged":
        notices.append(
            "Matching choices in this scenario do not prove that the instruction edit has no effect."
        )
    sides = []
    for side in ("before", "after"):
        variant = getattr(variants, side)
        source = getattr(narrative, side) if narrative else None
        descriptions = (
            {choice.choice: choice for choice in source.choices} if source else {}
        )
        choices = (
            tuple(
                SummaryChoiceData(
                    choice.choice,
                    descriptions[choice.choice].label if source else choice.choice,
                    descriptions[choice.choice].detail if source else "",
                    choice.count,
                )
                for choice in getattr(row, side)
            )
            if row
            else ()
        )
        sides.append(
            SummarySideData(
                source.icon if source else "neutral", choices, variant.total
            )
        )
    if row is None:
        evidence_label = (
            "No usable decision extraction; trial records remain available."
        )
    elif row.anchor == "answer":
        evidence_label = (
            "Plans stated in final answers; not executed actions."
            if narrative and narrative.evidence_kind == "plans"
            else "Choices extracted from final answers; not evidence of tool execution."
        )
    elif metadata.trace_source == "self-reported":
        evidence_label = (
            "Choices extracted from self-reported actions; not captured tool evidence."
        )
    else:
        evidence_label = "Choices extracted from recorded tool events; records do not prove successful completion."

    def claim(value):
        return EvidenceClaimData(value.text, value.decisions) if value else None

    return VisualSummaryData(
        headline,
        narrative.scenario if narrative else "",
        evidence_label,
        status,
        lead,
        sides[0],
        sides[1],
        claim(narrative.why) if narrative else None,
        claim(narrative.caution) if narrative else None,
        tuple(notices),
    )
