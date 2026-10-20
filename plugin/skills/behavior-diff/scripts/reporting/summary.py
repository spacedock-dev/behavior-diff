"""Derive the assessment-first Summary from validated target, purpose and trial health.

Optional extractor narrative is validated here too, but it only labels observed
branches; it never decides the Summary's conclusion.
"""

from dataclasses import dataclass
from typing import Optional, Tuple

from reporting.explanation import _text as _plain_text
from reporting.instruction import normalize_edit_hunks

ICONS = ("neutral", "continue", "stop", "report", "edit", "inspect", "test", "delegate")
EVIDENCE_KINDS = ("plans", "answers", "actions")
SUMMARY_STATUSES = ("changed", "unchanged", "mixed", "unavailable")
# Overall Summary finding, decided only from validated target checks and trial health.
FINDING_STATES = (
    "not_met",
    "inconclusive",
    "baseline_incomplete",
    "improved",
    "already_met",
    "preserved",
    "unavailable",
)
CHECK_STATES = FINDING_STATES[:-1]
UNMET = "The expected improvement did not happen in these tests."
FINDING_HEADLINES = {
    "not_met": UNMET,
    "inconclusive": "These tests did not settle whether the expected behavior happened.",
    "baseline_incomplete": (
        "After met the expected behavior, but incomplete Before results do not show an improvement."
    ),
    "improved": "After met the expected behavior in these tests; Before did not.",
    "already_met": (
        "Before already met the expected behavior; no added benefit was shown in these tests."
    ),
    "preserved": "The behavior expected to stay the same held in these tests.",
    "unavailable": "The expected behavior could not be checked in these tests.",
}
PRESERVATION_UNMET = "A behavior expected to stay the same did not hold in these tests."
CHECK_LABELS = {
    "not_met": "not met",
    "inconclusive": "not settled",
    "baseline_incomplete": "met After; Before incomplete",
    "improved": "met After; not met Before",
    "already_met": "already met Before",
    "preserved": "preserved",
}
CHECK_MEANINGS = {
    "not_met": "At least one After trial did not meet this.",
    "inconclusive": (
        "Some After trials were unclear, lacked evidence, or were not assessed, "
        "so this is not settled."
    ),
    "baseline_incomplete": (
        "Every After trial met this, but Before trials were incomplete, unclear, or "
        "not assessed, so no improvement is shown."
    ),
    "improved": (
        "Every After trial met this and at least one Before trial did not. "
        "This does not prove the edit caused the difference."
    ),
    "already_met": "Before already met this, so the edit showed no added benefit here.",
    "preserved": "Every After trial still met this.",
}
NEXT_ACTIONS = {
    "not_met": (
        "Revise the edit or its expectation, then retest; inspect the After trials "
        "that did not meet the expected behavior."
    ),
    "inconclusive": (
        "Inspect or rerun the unclear, missing, or interrupted trials before drawing a conclusion."
    ),
    "baseline_incomplete": (
        "Inspect or rerun the incomplete Before trials before claiming an improvement."
    ),
    "improved": (
        "Review the evidence and decide whether to accept the edit; these tests do not "
        "show reliability in other situations."
    ),
    "already_met": (
        "Decide whether the edit is still needed; Before already met the expected "
        "behavior in these tests."
    ),
    "preserved": "Review the evidence and decide whether to accept the edit.",
    "unavailable": (
        "Inspect the trial evidence directly; no validated check of the expected "
        "behavior is available."
    ),
}
GATE_NOTE = "This report does not approve or block the change; the decision is yours."
CHECK_SCOPES = {
    "output": (
        "Checked against final answers. An answer describing a plan or action does "
        "not show that it was carried out."
    ),
    "source_consistency": "Checked final answers against recorded sources.",
    "recorded_action": "Checked against recorded tool activity.",
}
SELF_REPORTED_SCOPE = (
    "Checked against self-reported actions, not independently captured tool activity."
)
PURPOSE_SUMMARY_LIMIT = 320


@dataclass(frozen=True)
class NarrativeChoiceData:
    choice: str
    label: str
    detail: str


@dataclass(frozen=True)
class NarrativeClaimData:
    text: str
    decisions: Tuple[int, ...]


@dataclass(frozen=True)
class NarrativeSideData:
    icon: str
    choices: Tuple[NarrativeChoiceData, ...]
    start: Optional[NarrativeClaimData] = None


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
    context: Optional[NarrativeClaimData] = None


@dataclass(frozen=True)
class EditIntentData:
    text: str
    edit_hunks: Tuple[int, ...]


def parse_intent(raw, hunk_count):
    """Validate an edit-only interpretation independently of trial observations."""
    if type(raw) is not dict:
        return None
    try:
        text = _text(raw.get("text"), 240)
        edit_hunks = normalize_edit_hunks(raw.get("edit_hunks"), hunk_count)
        if not edit_hunks:
            return None
        return EditIntentData(text, edit_hunks)
    except ValueError:
        return None


def parse_purpose_summary(raw, purpose):
    """Keep a plain paraphrase of frozen goals; it never creates or replaces purpose."""
    if raw is None or not purpose:
        return None
    try:
        return _plain_text(raw, PURPOSE_SUMMARY_LIMIT)
    except ValueError:
        return None


def build_intent(expected, decisions):
    from reporting.schema import InstructionIntentData

    if decisions.purpose:
        return InstructionIntentData(
            " ".join(goal.text for goal in decisions.purpose), "purpose", ()
        )
    if decisions.target_assessment is not None and decisions.intent is not None:
        return InstructionIntentData(
            decisions.intent.text, "inferred", decisions.intent.edit_hunks
        )

    if type(expected) is str and expected.strip():
        return InstructionIntentData(expected, "expected", ())
    if decisions.intent is not None:
        return InstructionIntentData(
            decisions.intent.text, "inferred", decisions.intent.edit_hunks
        )
    return InstructionIntentData(
        "No interpretation of this instruction edit is available.", "unavailable", ()
    )


def _text(value, limit):
    if type(value) is not str or not value.strip() or len(value.strip()) > limit:
        raise ValueError("invalid narrative text")
    if any(ord(char) < 32 for char in value) or "<" in value or ">" in value:
        raise ValueError("narrative must contain plain text")
    return value.strip()


def _row_field(row, name):
    return row[name] if type(row) is dict else getattr(row, name)


def _claim(raw, limit, positions):
    if type(raw) is not dict or type(raw.get("decisions")) is not list:
        raise ValueError("invalid narrative claim")
    refs = raw["decisions"]
    if (
        not refs
        or any(type(ref) is not int or ref not in positions for ref in refs)
        or len(set(refs)) != len(refs)
    ):
        raise ValueError("invalid narrative claim references")
    return NarrativeClaimData(
        _text(raw.get("text"), limit), tuple(positions[ref] for ref in refs)
    )


def _optional_claim(raw, limit, positions):
    """Omit an unsupported optional claim without discarding validated comparisons."""
    if raw is None:
        return None
    try:
        return _claim(raw, limit, positions)
    except ValueError:
        return None


def _side_members(branches):
    """Return exact trial names for a side, or None when attribution is incomplete."""
    if type(branches) not in (list, tuple) or not branches:
        return None
    names = []
    for branch in branches:
        if type(branch) is dict:
            trials, count = branch.get("trials"), branch.get("n", branch.get("count"))
        else:
            trials, count = branch.trials, branch.count
        if (
            type(trials) not in (list, tuple)
            or not trials
            or len(trials) != count
            or any(type(name) is not str or not name.strip() for name in trials)
        ):
            return None
        names.extend(trials)
    return set(names) if len(set(names)) == len(names) else None


def _start(raw, side, lead, rows, positions):
    """Keep a start only when one cited branch holds exactly every lead trial.

    A start is an observed state or step shared by the side's lead trials. It
    never joins differing row memberships into a counted path or proves a cause.
    """
    claim = _optional_claim(raw, 80, positions)
    if claim is None or len(claim.decisions) != 1:
        return None
    lead_members = _side_members(_row_field(lead, side))
    cited = _row_field(rows[claim.decisions[0] - 1], side)
    if lead_members is None or len(cited) != 1 or _side_members(cited) != lead_members:
        return None
    return claim


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
                    icon if type(icon) is str and icon in ICONS else "neutral",
                    choices,
                    _start(source.get("start"), side, row, rows, positions),
                )
            )
        # Why/caution stay mandatory-valid when present; newer optional claims
        # (context, starts) degrade alone so the validated comparison survives.
        why, caution = (
            None if raw.get(name) is None else _claim(raw[name], limit, positions)
            for name, limit in (("why", 480), ("caution", 240))
        )
        return NarrativeData(
            decision,
            _text(raw["headline"], 120),
            _text(raw["scenario"], 220),
            kind,
            sides[0],
            sides[1],
            why,
            caution,
            _optional_claim(raw.get("context"), 480, positions),
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
    """Rank fallback rows when no usable narrative selects the lead."""
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


def question_distribution(criterion, side, total):
    """Keep unknown and unassessed trials distinct from supported Yes/No counts."""
    trials = getattr(criterion, side)
    labels = (
        ("met", "Yes"),
        ("not_met", "No"),
        ("uncertain", "Unclear"),
        ("unassessable", "Not enough evidence"),
    )
    values = [
        f"{label} ({count}/{total})"
        for outcome, label in labels
        if (count := sum(trial.outcome == outcome for trial in trials))
    ]
    if total > len(trials):
        values.append(f"Not assessed ({total - len(trials)}/{total})")
    return "; ".join(values) or "No assessed trials"


def question_distribution_changed(criterion, before_total, after_total):
    """Emphasize only complete binary assessments whose proportions differ."""
    before, after = criterion.before, criterion.after
    return (
        len(before) == before_total > 0
        and len(after) == after_total > 0
        and all(trial.outcome in ("met", "not_met") for trial in (*before, *after))
        and sum(trial.outcome == "met" for trial in before) * after_total
        != sum(trial.outcome == "met" for trial in after) * before_total
    )


def _side_health(criterion, side, variant):
    """A side is usable only when every recorded trial completed and was assessed."""
    trials = getattr(criterion, side)
    return (
        variant.total > 0
        and len(trials) == variant.total
        and variant.valid == variant.total
        and not variant.blocked
        and all(trial.outcome in ("met", "not_met") for trial in trials)
    )


def check_state(criterion, variants):
    after = criterion.after
    if any(trial.outcome == "not_met" for trial in after):
        return "not_met"
    if not _side_health(criterion, "after", variants.after):
        return "inconclusive"
    if not _side_health(criterion, "before", variants.before):
        return "baseline_incomplete"
    if all(trial.outcome == "met" for trial in criterion.before):
        return "preserved" if criterion.mode == "preservation" else "already_met"
    return "improved"


def finding_state(states):
    if not states:
        return "unavailable"
    return next(state for state in CHECK_STATES if state in states)


def build_checks(metadata, variants, target):
    from reporting.schema import SummaryCheckData

    checks = []
    for number, criterion in enumerate(target.criteria if target else (), 1):
        state = check_state(criterion, variants)
        scope = (
            SELF_REPORTED_SCOPE
            if criterion.evidence_kind == "recorded_action"
            and metadata.trace_source == "self-reported"
            else CHECK_SCOPES[criterion.evidence_kind]
        )
        checks.append(
            SummaryCheckData(
                number,
                criterion.text,
                criterion.mode,
                state,
                question_distribution(criterion, "before", variants.before.total),
                question_distribution(criterion, "after", variants.after.total),
                CHECK_MEANINGS[state],
                scope,
            )
        )
    return tuple(checks)


ANSWER_SCOPED = "Judged from final answers, not observed actions."
MET_STATES = ("baseline_incomplete", "improved", "already_met", "preserved")


def finding_text(state, checks):
    if state == "not_met" and all(
        check.mode == "preservation" for check in checks if check.state == "not_met"
    ):
        return PRESERVATION_UNMET
    # A met answer-only check cannot read as proof that actions happened.
    if state in MET_STATES and any(
        check.scope == CHECK_SCOPES["output"] for check in checks
    ):
        return f"{FINDING_HEADLINES[state]} {ANSWER_SCOPED}"
    return FINDING_HEADLINES[state]


def unchecked_goals(decisions):
    """Frozen goal numbers that no validated criterion checks."""
    from reporting.target import effective_purpose

    target = decisions.target_assessment
    if target is None:
        return ()
    goals = effective_purpose(decisions.purpose, decisions.intent)
    covered = {criterion.goal for criterion in target.criteria}
    return tuple(n for n in range(1, len(goals) + 1) if n not in covered)


def finding_meaning(checks, rejection=None, unchecked=()):
    if not checks:
        from reporting.target import UNAVAILABLE

        if rejection is None:
            return UNAVAILABLE
        return (
            f"{UNAVAILABLE} The returned target check was rejected by validation: "
            f"{rejection}."
        )
    counts = [
        f"{sum(check.state == state for check in checks)} {CHECK_LABELS[state]}"
        for state in CHECK_STATES
        if any(check.state == state for check in checks)
    ]
    noun = "check" if len(checks) == 1 else "checks"
    text = f"Of {len(checks)} recorded {noun}: {', '.join(counts)}."
    if unchecked:
        text += " No check covers recorded goal " + ", ".join(map(str, unchecked)) + "."
    return text


def build_summary(metadata, variants, decisions):
    from reporting import content
    from reporting.schema import (
        EvidenceClaimData,
        SummaryChoiceData,
        SummarySideData,
        VisualSummaryData,
    )

    def claim(value):
        return EvidenceClaimData(value.text, value.decisions) if value else None

    complete = content.complete_evidence(variants, decisions)
    candidates = _lead_candidates(decisions)
    if (
        decisions.before_count != variants.before.total
        or decisions.after_count != variants.after.total
    ):
        candidates = ()
    narrative = decisions.narrative
    if not complete:
        narrative = None
    lead = narrative.decision if narrative else next(iter(candidates), None)
    row = decisions.rows[lead - 1] if lead else None
    status = _row_status(row, decisions) if row else "unavailable"
    if not complete:
        status = "unavailable"
    notices = [
        "One scenario only; counts and narrative are model interpretations, not causal proof."
    ]
    checks = build_checks(metadata, variants, decisions.target_assessment)
    states = {check.state for check in checks}
    unchecked = unchecked_goals(decisions)
    if checks and unchecked:
        # A conclusion needs every frozen goal checked; a gap leaves it unsettled.
        states.add("inconclusive")
    state = finding_state(states)
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
            "The primary result varies across trials; see its full distribution in Behavior diff."
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
            "The primary result is the same; actions differ in this scenario."
        )
    if not narrative:
        notices.append(
            "Plain-language narrative unavailable; original extracted comparisons are shown without added explanation."
        )
    headline = finding_text(state, checks)
    if status == "unchanged":
        notices.append(
            "Matching observations in this scenario do not prove that the instruction edit has no effect."
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
                source.icon if source else "neutral",
                choices,
                variant.total,
                claim(source.start) if source else None,
            )
        )
    if row is None:
        evidence_label = (
            "No usable comparison extraction; trial records remain available."
        )
    elif row.anchor == "answer":
        evidence_label = (
            "Plans stated in final answers; not executed actions."
            if narrative and narrative.evidence_kind == "plans"
            else "Based on final answers. An answer describing an action does not prove it happened."
        )
    elif metadata.trace_source == "self-reported":
        evidence_label = "Based on self-reported actions. These are not independently captured tool evidence."
    else:
        evidence_label = "Based on recorded tool calls. Recorded calls do not establish successful completion."

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
        claim(narrative.context) if narrative else None,
        state,
        finding_meaning(checks, decisions.target_rejection, unchecked),
        checks,
        NEXT_ACTIONS[state],
    )
