"""Format-neutral wording for Behavior Diff reports."""

from collections import Counter

from reporting.schema import ContentData, ResultData


TRIAL_COUNT_NOTE = (
    "A model extracts these counts from trial evidence. "
    "They count trials, not repeated actions within one trial."
)
BEHAVIOR_COUNT_NOTE = (
    "These comparisons cover actions, not every detail in the answers. "
    + TRIAL_COUNT_NOTE
    + " Counts from separate rows do not show a complete sequence within one trial."
)
INTERPRETATION_NOTE = (
    "These explanations are model interpretations, not causal proof. "
    "The comparisons do not establish that the instruction change caused a difference."
)
FLOW_COUNT_NOTE = (
    "Each row counts trials with the same complete category combination, not command calls. "
    "Each trial appears once on its side."
)
SELF_REPORTED_LIMIT = (
    "Actions are self-reported, not independently captured command evidence. "
    "Flow diff is unavailable for this report."
)
DECISION_PROGRESSION_NOTE = "These model-extracted comparisons are not a recorded execution path or a causal chain."
FLOW_PROGRESSION_NOTE = (
    "Commands follow their recorded order, including repeats. "
    "Only identical complete sequences are grouped within each side. "
    "Before and After are independent trials. Records can be incomplete and do not prove successful execution."
)


def trial_count(count, total):
    return "{0} of {1} trial{2}".format(count, total, "" if total == 1 else "s")


def trial_anchor(side, name):
    return "trial-{0}-{1}".format(side, name.encode("utf-8").hex())


def command_progressions(variant):
    """Group complete recorded sequences without normalizing or joining paths."""
    groups = {}
    for trial in variant.trials:
        members = groups.get(trial.commands)
        if members is None:
            groups[trial.commands] = [trial]
        else:
            members.append(trial)
    return tuple((commands, tuple(members)) for commands, members in groups.items())


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
    """Describe extracted results and actions without assigning a grade."""
    explicit = decisions.outcome is not None
    outcomes = (
        (decisions.outcome,)
        if explicit
        else tuple(
            index
            for index, row in enumerate(decisions.rows, 1)
            if row.anchor == "answer"
        )
    )
    actions = tuple(
        index
        for index, row in enumerate(decisions.rows, 1)
        if type(row.anchor) is int and index != decisions.outcome
    )
    changed_actions = tuple(
        index
        for index in actions
        if choices_changed(
            decisions.rows[index - 1].before, decisions.rows[index - 1].after
        )
    )
    behavior = changed_actions or actions
    answer_details_changed = explicit and any(
        row.anchor == "answer"
        and index != decisions.outcome
        and choices_changed(row.before, row.after)
        for index, row in enumerate(decisions.rows, 1)
    )
    limits, missing = _evidence_limits(metadata, variants, decisions, expected)
    outcome_status = _comparison_status(decisions.rows, outcomes)
    behavior_status = _comparison_status(decisions.rows, actions)
    # A mixed process can still have a clear change in its choice proportions.
    if changed_actions and behavior_status != "unavailable":
        behavior_status = "changed"
    if missing:
        outcome_status = behavior_status = "unavailable"
    if not outcomes:
        missing.append(
            "No usable final result or reported-answer comparison is available."
        )
    elif outcome_status == "unavailable" and not missing:
        missing.append("Result choices are missing or blank.")
    if not explicit:
        limits.insert(
            0,
            "The model did not identify a primary final result. "
            "Reported-answer comparisons do not establish the final result.",
        )
    if not actions:
        limits.append(
            "No separate action comparison is available. Answers can still contain process details."
        )
    elif behavior_status == "unavailable":
        limits.append(
            "The available action evidence is incomplete. "
            "Inspect the trial records before drawing a conclusion."
        )

    subject = "Final result" if explicit else "Reported answers"
    if missing:
        text = "Insufficient evidence to compare results"
        summary = " ".join(missing)
    elif outcome_status == "varies":
        text = (
            "Final result varies across trials"
            if explicit
            else "Reported answers vary across trials"
        )
        summary = (
            "The model identified different choices within at least one side. "
            "The table shows the trial counts for each choice."
        )
    elif outcome_status == "changed":
        if explicit:
            row = decisions.rows[decisions.outcome - 1]
            text = "Final result changed: {0} → {1}".format(
                next(iter(_distribution(row.before))),
                next(iter(_distribution(row.after))),
            )
        else:
            text = "Reported answers changed"
        summary = "The model identified different {0} before and after.".format(
            "final results" if explicit else "reported answers"
        )
    elif explicit and behavior_status == "changed":
        text = "Same result, different process"
        summary = (
            "The final result stayed the same. "
            "The model identified changes in the agent's actions."
        )
    else:
        text = subject + " unchanged"
        summary = (
            "The model identified the same {0} before and after. "
            "This does not establish that the instruction change has no effect."
        ).format("final result" if explicit else "reported answers")
        if answer_details_changed:
            text = "Final result unchanged; answer details changed"
    if answer_details_changed:
        summary += " Other answer details changed. The Decision diff preserves these comparisons."
    if behavior_status == "unchanged":
        summary += " No change was observed in the compared actions."
    if not explicit:
        summary = "No primary final result was identified. " + summary
    return ResultData(
        text=text,
        kind="neutral",
        summary=summary,
        outcome_heading=subject + " — " + outcome_status,
        behavior_heading="Behavior — " + behavior_status,
        outcomes=outcomes,
        behavior=behavior,
        implications=decisions.implications,
        limits=tuple(missing + limits),
    )


def _comparison_status(rows, indexes):
    if not indexes:
        return "unavailable"
    distributions = tuple(
        _distribution(choices)
        for index in indexes
        for choices in (rows[index - 1].before, rows[index - 1].after)
    )
    if any(not distribution or "" in distribution for distribution in distributions):
        return "unavailable"
    if any(len(distribution) > 1 for distribution in distributions):
        return "varies"
    if any(
        choices_changed(rows[index - 1].before, rows[index - 1].after)
        for index in indexes
    ):
        return "changed"
    return "unchanged"


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
    limits = ["One scenario was tested. Real-use evidence is absent."]
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
            "{0} extracted comparison row(s) were dropped. Completeness is uncertain.".format(
                decisions.dropped
            )
        )
    if metadata.mode == "review":
        limits.append("Review mode does not assign an automatic pass or fail.")
    elif expected:
        limits.append(
            'Separate grading against the supplied expectation "{0}": '
            "before {1}/{2} valid trials met it. After {3}/{4} valid trials met it. "
            "These grades do not establish complete result evidence.".format(
                expected,
                variants.before.passed,
                variants.before.valid,
                variants.after.passed,
                variants.after.valid,
            )
        )
    if not expected:
        limits.append(
            "No explicit expected behavior was supplied. The report makes no correctness claim."
        )
    limits.append(
        "A model extracts comparison choices and counts from trial evidence. "
        "They are not independent measurements. "
        "The primary result, explanations, and proposed causal links are model interpretations."
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
    purpose = "A model extracts these comparisons from trial evidence."
    if single_trial:
        purpose += (
            " CAUTION — one trial per side: differences can be run-to-run variation "
            "rather than an instruction effect. Repeat the comparison with more trials "
            "(behavior-diff 3+3) before drawing conclusions."
        )
    return purpose


def flow_purpose():
    return (
        "Fixed rules group captured commands. No model interprets this view. "
        "Categories are not execution steps and do not identify specific commands or files. "
        "Patterns do not explain why an agent acted. Blocked trial records can be incomplete."
    )


def flow_kinds_heading(kinds):
    return "The classifier recognizes these {0} command categories:".format(len(kinds))


def source_label(anchor, trace_source):
    if anchor == "answer":
        return "from the reply"
    if trace_source == "self-reported":
        return "from a reported action"
    return "from a command"


def tag_legend(trace_source):
    """What each tag on a decision row means."""
    return (
        ("changed", "Changed", "the extracted choice proportions differ between sides"),
        ("same", "Unchanged", "the extracted choice proportions match between sides"),
        ("action", "Action", "a comparison of actions in the trial evidence"),
        ("result", "Final result", "the result selected by the extractor"),
        ("detail", "Answer detail", "another comparison from the final answer"),
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
        "limits": "Evidence limits",
        "scenario": "Scenario",
        "expected": "Expected behavior",
        "diff": "Diff of {0}".format(target_file),
        "decision": "Decision diff: actions and answers compared",
        "flow": "Flow diff: recorded commands",
        "result": "Result",
    }


def decision_footer(rows):
    changed = sum(decision_status(row) == "Changed" for row in rows)
    unavailable = sum(decision_status(row) == "Unavailable" for row in rows)
    summary = "{0} of {1} comparisons have different choice proportions.".format(
        changed, len(rows)
    )
    if unavailable:
        summary += " {0} comparisons lack usable choices on one or both sides.".format(
            unavailable
        )
    return summary


def decision_role(index, row, outcome):
    if index == outcome:
        return "Final result"
    if type(row.anchor) is int:
        return "Action"
    return "Answer detail" if row.anchor == "answer" else "Comparison"


def decision_status(row):
    distributions = (_distribution(row.before), _distribution(row.after))
    if any(not values or "" in values for values in distributions):
        return "Unavailable"
    return "Changed" if choices_changed(row.before, row.after) else "Unchanged"


def decision_choices_preview(choices, total):
    """Keep mixed or incomplete evidence visible in a compact choice summary."""
    counts = _distribution(choices)
    return (
        " · ".join(
            choice
            if len(counts) == 1 and count == total
            else "{0} ({1})".format(choice, trial_count(count, total))
            for choice, count in counts.items()
        )
        or "No extracted choice"
    )


def decision_overview(report):
    changed = Counter(
        decision_role(index, row, report.decisions.outcome)
        for index, row in enumerate(report.decisions.rows, 1)
        if decision_status(row) == "Changed"
    )
    if not changed:
        return report.result.text
    labels = {
        "Action": "action comparison",
        "Final result": "final-result comparison",
        "Answer detail": "answer-detail comparison",
        "Comparison": "other comparison",
    }
    counts = ", ".join(
        "{0} {1}{2}".format(count, labels[role], "" if count == 1 else "s")
        for role, count in changed.items()
    )
    return report.result.text + ". Extracted differences: " + counts + "."


def flow_patterns(flow):
    """Expand the existing compressed groups into complete category combinations."""
    if not flow.enabled:
        return ()
    patterns = {}
    for side, branch in enumerate((flow.before, flow.after)):
        groups = (
            ((path.steps, path.count) for path in branch.paths)
            if branch.paths
            else (((), branch.total),)
        )
        for steps, count in groups:
            if count <= 0:
                continue
            # Older flow groups also contain grading labels; those are not commands.
            present = set(flow.shared + branch.prefix + steps)
            categories = tuple(kind for kind in flow.kinds if kind in present)
            counts = patterns.setdefault(categories, [0, 0])
            counts[side] += count
    return tuple(
        (categories, counts[0], counts[1])
        for categories, counts in sorted(patterns.items())
    )


def flow_overview(flow, patterns):
    if (
        not flow.enabled
        or not flow.before.total
        or not flow.after.total
        or not any(categories for categories, _, _ in patterns)
    ):
        return "Recorded command patterns — unavailable"
    changed = any(
        before * flow.after.total != after * flow.before.total
        for _, before, after in patterns
    )
    return "Recorded command patterns — " + ("changed" if changed else "unchanged")


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
