"""Format-neutral wording for Behavior Diff reports."""

from collections import Counter

from reporting.schema import ContentData, ResultData


def subtitle(facts):
    """The header facts as one line, for formats that cannot lay out a row."""
    return " · ".join("{0}: {1}".format(label, value) for label, value in facts)


def meta(metadata, before_total, after_total):
    """Labeled facts for the report header, one per column."""
    trace = (
        "self-reported actions"
        if metadata.trace_source == "self-reported"
        else "captured tool calls"
    )
    return (
        ("before", metadata.before_label),
        ("after", metadata.after_label),
        ("model", metadata.model),
        ("trials", "{0} before, {1} after".format(before_total, after_total)),
        ("evidence", trace),
    )


def boundary():
    return (
        "This is simulation evidence. Real-use evidence is still pending.\n"
        "It does not repair the original incident; it tests the change "
        "for future tasks."
    )


def result_data(metadata, variants, decisions, expected):
    """Describe observed outcomes without turning observations into a grade."""
    outcomes = (
        (decisions.outcome,)
        if decisions.outcome is not None
        else tuple(
            index
            for index, row in enumerate(decisions.rows, 1)
            if row.anchor == "answer"
        )
    )
    changed = {
        index
        for index, row in enumerate(decisions.rows, 1)
        if choices_changed(row.before, row.after)
    }
    behavior = tuple(
        index
        for index, row in enumerate(decisions.rows, 1)
        if index not in outcomes and (index in changed or index == decisions.fork)
    )
    if not behavior:
        behavior = tuple(
            index
            for index, row in enumerate(decisions.rows, 1)
            if index not in outcomes and type(row.anchor) is int
        )

    limits, missing = _evidence_limits(metadata, variants, decisions, expected)
    if not outcomes:
        missing.append("No usable outcome or reported-answer comparison is available.")
    elif any(
        not _distribution(choices)
        or any(choice.count > 0 and not choice.choice.strip() for choice in choices)
        for index in outcomes
        for choices in (
            decisions.rows[index - 1].before,
            decisions.rows[index - 1].after,
        )
    ):
        missing.append("Outcome choices are missing or blank.")

    explicit = decisions.outcome is not None
    if missing:
        text = "Insufficient evidence to compare outcomes"
        summary = " ".join(missing)
    elif any(
        len(_distribution(choices)) > 1
        for index in outcomes
        for choices in (
            decisions.rows[index - 1].before,
            decisions.rows[index - 1].after,
        )
    ):
        if explicit:
            text = "Mixed outcomes in these trials"
            summary = (
                "The primary outcome varies between trials on at least one side. "
                "The table shows each distribution."
            )
        else:
            text = (
                "Reported answers changed in these trials"
                if changed.intersection(outcomes)
                else "Reported answers vary within these trials"
            )
            summary = (
                "Some answer dimensions vary between trials on the same side. "
                "These differences do not establish mixed task outcomes."
            )
    elif changed.intersection(outcomes):
        text = "Reported answers changed in these trials"
        if explicit:
            row = decisions.rows[decisions.outcome - 1]
            text = "Outcome changed: {0} → {1}".format(
                next(choice.choice for choice in row.before if choice.count > 0),
                next(choice.choice for choice in row.after if choice.count > 0),
            )
        summary = (
            "The model-extracted outcome choices differ between before and after."
            if explicit
            else "The model-extracted reported-answer choices differ between before and after."
        )
    elif changed.difference(outcomes):
        text = (
            "Same outcome; process changed"
            if explicit
            else "Same reported answers; process changed"
        )
        summary = (
            "The compared outcome distributions are unchanged, but other decision "
            "distributions differ."
        )
    else:
        text = "No difference observed in these trials"
        summary = (
            "The supplied decision distributions match. This does not establish "
            "that the instruction change has no effect."
        )
    if not explicit and outcomes:
        limits.append(
            "No primary task outcome was identified. These comparisons show reported "
            "answer dimensions, not a guessed primary outcome."
        )
    return ResultData(
        text=text,
        kind="neutral",
        summary=summary,
        outcomes=outcomes,
        behavior=behavior,
        implications=decisions.implications,
        limits=tuple(limits + missing),
    )


def _distribution(choices):
    counts = Counter()
    for choice in choices:
        if choice.count > 0:
            counts[choice.choice.strip()] += choice.count
    return counts


def choices_changed(before, after):
    """Compare choice proportions, independent of row order or trial totals."""
    before_counts = _distribution(before)
    after_counts = _distribution(after)
    before_total = sum(before_counts.values())
    after_total = sum(after_counts.values())
    return before_counts.keys() != after_counts.keys() or any(
        count * after_total != after_counts[choice] * before_total
        for choice, count in before_counts.items()
    )


def _evidence_limits(metadata, variants, decisions, expected):
    limits = [
        "One scenario was tested. This is simulation evidence; real-use evidence is absent."
    ]
    missing = []
    for variant, extracted_count in (
        (variants.before, decisions.before_count),
        (variants.after, decisions.after_count),
    ):
        limits.append(
            "{0}: {1} trial(s), {2} valid, {3} blocked.".format(
                variant.label, variant.total, variant.valid, variant.blocked
            )
        )
        if variant.valid == 0:
            missing.append("{0} has no valid trials.".format(variant.label))
        if variant.blocked or variant.valid != variant.total:
            missing.append(
                "{0} includes blocked or invalid trials.".format(variant.label)
            )
        incomplete = [trial.name for trial in variant.trials if not trial.final.strip()]
        if incomplete or len(variant.trials) != variant.total:
            missing.append(
                "{0} is missing complete trial evidence{1}.".format(
                    variant.label, ": " + ", ".join(incomplete) if incomplete else ""
                )
            )
        if decisions.rows and (
            extracted_count != variant.total
            or any(
                sum(choice.count for choice in choices) != variant.total
                for choices in (
                    row.before if variant is variants.before else row.after
                    for row in decisions.rows
                )
            )
        ):
            missing.append(
                "{0} decision counts disagree with the trial count.".format(
                    variant.label
                )
            )
    if decisions.dropped:
        missing.append(
            "{0} extracted decision row(s) were dropped; completeness is uncertain.".format(
                decisions.dropped
            )
        )
    if metadata.mode == "review":
        limits.append("Review mode does not assign an automatic pass or fail.")
    elif expected:
        limits.append(
            'Separate grading against the supplied expectation "{0}": '
            "before {1}/{2} valid trials met it; after {3}/{4} valid trials met it. "
            "These grades do not establish complete outcome evidence.".format(
                expected,
                variants.before.passed,
                variants.before.valid,
                variants.after.passed,
                variants.after.valid,
            )
        )
    if not expected:
        limits.append(
            "No explicit expected behavior was supplied; no correctness claim is made."
        )
    limits.append(
        "Decision choices and counts are model extractions from trial evidence, not "
        "independent measurements. Outcome selection, implications, and causal links "
        "are model interpretations."
    )
    if metadata.trace_source == "self-reported":
        limits.append(
            "Actions and answers are self-reported, not independently captured tool calls."
        )
    if variants.before.total == 1 or variants.after.total == 1:
        limits.append(
            "At least one side has a single trial. Differences may be run-to-run "
            "variation rather than an instruction effect."
        )
    return limits, missing


def count_data(mode, passed, valid, blocked):
    if mode == "review":
        return (
            "{0} valid trial(s) · no automatic grading (blocked: {1})".format(
                valid, blocked
            ),
            "",
            False,
        )
    return (
        "{0} of {1} valid trials met the expectation".format(passed, valid),
        " (blocked: {0})".format(blocked),
        True,
    )


def decision_blurb(single_trial):
    purpose = (
        "A model read the trial evidence and named points where the agent had "
        "a choice. These comparisons are model interpretations, not causal proof."
    )
    if single_trial:
        purpose += (
            " CAUTION — one trial per side: any divergence here can be "
            "run-to-run variation rather than a rule effect; confirm with "
            "repeated trials (behavior-diff 3+3) before acting on it."
        )
    return purpose


def flow_purpose():
    return (
        "A cross-check on the decision diff above, built from the actual "
        "commands the agents ran and sorted by rule. This section lists "
        "which kinds appeared on each side."
    )


def flow_kinds_heading(kinds):
    return "Every command is put into one of these {0} kinds:".format(len(kinds))


def source_label(anchor, trace_source):
    if anchor == "answer":
        return "from the reply"
    if trace_source == "self-reported":
        return "from a reported action"
    return "from a command"


def tag_legend(trace_source):
    """What each tag on a decision row means."""
    return (
        ("root", "first difference", "the first decision where before and after split"),
        (
            "down",
            "follows from it",
            "this split happens because of the first difference",
        ),
        ("same", "same before and after", "before and after chose the same thing"),
        (
            "cmd",
            source_label(1, trace_source),
            "this row comes from an action the agent reported"
            if trace_source == "self-reported"
            else "this row comes from a captured command",
        ),
        ("ans", "from the reply", "this row comes from what the agent wrote"),
    )


def headings(target_file):
    return {
        "behavior": "Behavior change",
        "limits": "Evidence limits",
        "scenario": "Scenario",
        "expected": "Expected behavior",
        "diff": "Diff of {0}".format(target_file),
        "decision": "Decision diff: what the agent chose, before and after your edit",
        "flow": "Flow diff: which kinds of command each side used",
        "result": "Result",
    }


def flow_fold_summary():
    return "Flow diff: which kinds of command each side used (no model involved)"


def decision_footer(rows, fork):
    divergent = sum(row.diverges for row in rows)
    if fork:
        rest = divergent - 1
        if not rest:
            return "Before and after first differ at decision #{0}.".format(fork)
        return (
            "Before and after first differ at decision #{0}. {1} later "
            "decision{2} also differ. The model reads them as following from "
            "#{0}, which is its reading, not something the run measured."
        ).format(fork, rest, "s" if rest != 1 else "")
    return "{0} of {1} decisions differ.".format(divergent, len(rows))


def dropped_rows(dropped):
    return (
        "{0} extractor row(s) were dropped because their counts did not match the trials."
    ).format(dropped)


def build_content(
    config,
    scenario,
    metadata,
    decisions,
    before_total,
    after_total,
):
    names = headings(metadata.target_file)
    facts = meta(metadata, before_total, after_total)
    return ContentData(
        title=config.get("title", "rk-monitor Behavior Check"),
        subtitle=subtitle(facts),
        meta=facts,
        note=config.get("sub", ""),
        behavior_heading=names["behavior"],
        limits_heading=names["limits"],
        scenario_heading=names["scenario"],
        scenario=scenario,
        expected_heading=names["expected"],
        expected=config.get("expected"),
        diff_heading=names["diff"],
        decision_heading=names["decision"],
        decision_blurb=decision_blurb(before_total == 1 and after_total == 1),
        tag_legend=tag_legend(metadata.trace_source),
        flow_heading=names["flow"],
        flow_purpose=flow_purpose(),
        result_heading=names["result"],
        boundary=boundary(),
    )
