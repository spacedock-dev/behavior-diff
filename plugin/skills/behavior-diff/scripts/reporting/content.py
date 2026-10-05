"""Format-neutral wording for Behavior Diff reports."""

from collections import Counter

from reporting.instruction import parse_diff_hunks
from reporting.schema import ContentData, ResultData

TRIAL_EVIDENCE_HEADING = "Trial evidence"
FINAL_ANSWER_HEADING = "Final answer"
NO_COMMANDS_RECORDED = "No commands recorded"
NO_EXTRACTED_CHOICE = "No recorded behaviors"
NO_FINAL_ANSWER = "No final answer recorded"
RECORDED_COMMAND_LIMIT = (
    "Records can be incomplete and do not prove successful execution."
)


TRIAL_COUNT_NOTE = (
    "A model extracts these counts from trial evidence. "
    "They count trials, not repeated actions within one trial."
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
DECISION_PROGRESSION_NOTE = (
    "Read top to bottom in the model-extracted decision order. "
    "Before and After sides are aligned at each decision. "
    "This is not a recorded execution path or a causal chain; "
    "counts across decisions do not establish a complete path through one trial."
)
FLOW_PROGRESSION_NOTE = (
    "Commands follow their recorded order, including repeats. "
    "Only identical complete sequences are grouped within each side. "
    "Before and After trials are independent. " + RECORDED_COMMAND_LIMIT
)
CONSISTENT_HEADING = "Consistent changes across observed trials"
EDIT_LINK_NOTE = (
    "Related edits are model interpretations, not proof of causality or author intent. "
    "An unavailable link does not establish that the edit had no effect."
)
SCENARIO_PROMPT_UNAVAILABLE = (
    "The original scenario prompt is unavailable. The description above is not "
    "a verified copy of the prompt."
)


def instruction_edit_aim(intent):
    """Explain the saved aim without claiming to know the author's intent."""
    if intent.source == "inferred":
        return "Likely aim: " + intent.text
    if intent.source == "expected":
        return "Supplied expectation: " + intent.text
    return "No plain-language aim is saved for this edit."


def instruction_edit_counts(diff):
    """Count changed lines in validated hunks without interpreting their meaning."""
    hunks = parse_diff_hunks(diff)
    if not hunks:
        return (
            "Line counts unavailable for the saved diff."
            if diff.strip()
            else "No instruction diff was recorded."
        )
    removed = sum(line.startswith("-") for hunk in hunks for line in hunk.lines)
    added = sum(line.startswith("+") for hunk in hunks for line in hunk.lines)
    return "{0} {1} removed · {2} {3} added".format(
        removed,
        "line" if removed == 1 else "lines",
        added,
        "line" if added == 1 else "lines",
    )


def instruction_diff_lines(diff):
    """Retain all raw diff lines while attaching validated hunk identities."""
    hunks = iter(parse_diff_hunks(diff))
    hunk = next(hunks, None)
    for line in diff.splitlines():
        number = None
        if hunk is not None and line == hunk.header:
            number = hunk.number
            hunk = next(hunks, None)
        yield line, number


def unanimous_choices(row, decisions):
    """Return both choices only for complete, nonblank, unanimous coverage."""
    choices = []
    for values, total in (
        (row.before, decisions.before_count),
        (row.after, decisions.after_count),
    ):
        counts = _distribution(values)
        if total < 1 or len(counts) != 1 or "" in counts:
            return None
        choice, count = next(iter(counts.items()))
        if count != total:
            return None
        choices.append(choice)
    return tuple(choices)


def valid_decision_choices(row, decisions):
    return all(
        choices
        and all(choice.choice.strip() and choice.count > 0 for choice in choices)
        and len({choice.choice for choice in choices}) == len(choices)
        and sum(choice.count for choice in choices) == total
        for choices, total in (
            (row.before, decisions.before_count),
            (row.after, decisions.after_count),
        )
    )


def complete_trial_evidence(report):
    return complete_evidence(report.variants, report.decisions)


def complete_evidence(variants, decisions):
    if not decisions.rows or not all(
        valid_decision_choices(row, decisions) for row in decisions.rows
    ):
        return False
    return not decisions.dropped and all(
        total == variant.total
        and variant.total > 0
        and variant.valid == variant.total
        and not variant.blocked
        and len(variant.trials) == variant.total
        and all(trial.final.strip() for trial in variant.trials)
        for variant, total in (
            (variants.before, decisions.before_count),
            (variants.after, decisions.after_count),
        )
    )


def decision_evidence_status(row, decisions, report=None):
    status = decision_status(row)
    complete = report is None or complete_trial_evidence(report)
    if status == "Unchanged" and (
        not complete or unanimous_choices(row, decisions) is None
    ):
        return "Same choice proportions"
    return status


def consistent_changes(decisions):
    if min(decisions.before_count, decisions.after_count) < 2:
        return ()
    return tuple(
        index
        for index, row in enumerate(decisions.rows, 1)
        if (choices := unanimous_choices(row, decisions)) is not None
        and choices[0] != choices[1]
    )


def intent_context(intent):
    """Label the stored source without inferring intent during rendering."""
    if intent.source == "expected":
        return (
            "Supplied expected behavior",
            "This was supplied as expected behavior, not confirmed author intent. "
            "The observations below do not establish that it was achieved.",
        )
    if intent.source == "inferred":
        return (
            "Model interpretation of the instruction edit",
            "This interpretation is based on the linked edit, not confirmed author "
            "intent or evidence that the aim was achieved.",
        )
    return (
        "Aim unavailable",
        "Inspect the instruction edit for the recorded changes. "
        "The observed outcomes alone do not establish the edit's aim.",
    )


NO_ADDITIONAL_FINDINGS = (
    "No additional supported findings were selected for this summary."
)


def additional_findings_note(report):
    execution_note = (
        "Self-reported actions and answers do not prove execution."
        if report.metadata.trace_source == "self-reported"
        else "Answer choices do not prove execution."
    )
    reason = (
        ""
        if report.metadata.trace_source == "self-reported"
        else "Answer summaries do not prove execution."
    )
    note = (
        "Model-extracted counts describe trials, not repeated actions. "
        + execution_note
        + " Edit links are interpretations, not causal proof."
    )
    if not complete_trial_evidence(report):
        note += (
            " Trial evidence is incomplete; these counts do not establish "
            "a complete comparison."
        )
    return note


def additional_findings(report):
    """Select up to three evidence-qualified comparisons, excluding the lead."""
    decisions = report.decisions
    complete = complete_trial_evidence(report)
    candidates = []
    for index, row in enumerate(decisions.rows, 1):
        if index == report.summary.decision:
            continue
        unanimous = unanimous_choices(row, decisions)
        if index == decisions.outcome and (unanimous is None or not complete):
            priority = 0
        elif valid_decision_choices(row, decisions) and choices_changed(
            row.before, row.after
        ):
            priority = 1
        elif (
            complete
            and row.edit_hunks
            and unanimous is not None
            and unanimous[0] == unanimous[1]
        ):
            priority = 2
        else:
            continue
        candidates.append((priority, index, row))
    findings = []
    for _, index, row in sorted(candidates, key=lambda item: item[:2])[:3]:
        sides = []
        for label, choices, total in (
            ("Before", row.before, decisions.before_count),
            ("After", row.after, decisions.after_count),
        ):
            branches = (
                "; ".join(
                    "{0} ({1})".format(choice.choice, trial_count(choice.count, total))
                    for choice in choices
                )
                or NO_EXTRACTED_CHOICE
            )
            sides.append("{0}: {1}.".format(label, branches))
        status = decision_evidence_status(row, decisions, report)
        if not complete or not valid_decision_choices(row, decisions):
            status = "Incomplete evidence"
        elif unanimous_choices(row, decisions) is None:
            status = "Behaviors varied across trials"
        text = "{0} — {1}. {2}".format(
            row.topic.strip() or row.decision, status, " ".join(sides)
        )
        findings.append((index, text))
    return tuple(findings)


def trial_noun(count):
    return "trial" if count == 1 else "trials"


def trial_count(count, total):
    return "{0} of {1} {2}".format(count, total, trial_noun(total))


def trial_action_labels(self_reported):
    if self_reported:
        return "Self-reported actions", "No self-reported actions"
    return "Recorded commands", NO_COMMANDS_RECORDED


def trial_evidence_note(self_reported):
    return (
        "Before and After trials are independent, even when their trial numbers match. "
        + (SELF_REPORTED_LIMIT if self_reported else RECORDED_COMMAND_LIMIT)
    )


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
        missing.append("Result states are missing or blank.")
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
            "The model identified different behaviors within at least one side. "
            "The table shows the trial counts for each behavior."
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
            "{0}: {1} {2}, {3} valid, {4} blocked.".format(
                variant.label,
                variant.total,
                trial_noun(variant.total),
                variant.valid,
                variant.blocked,
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
        missing.append(dropped_rows(decisions.dropped) + " Completeness is uncertain.")
    if metadata.mode == "review":
        limits.append("Review mode does not assign an automatic pass or fail.")
    elif expected:
        limits.append(
            'Separate grading against the supplied expectation "{0}": '
            "Before: {1} of {2} valid {3} met it. After: {4} of {5} valid {6} met it. "
            "These grades do not establish complete result evidence.".format(
                expected,
                variants.before.passed,
                variants.before.valid,
                trial_noun(variants.before.valid),
                variants.after.passed,
                variants.after.valid,
                trial_noun(variants.after.valid),
            )
        )
    if not expected:
        limits.append(
            "No explicit expected behavior was supplied. The report makes no correctness claim."
        )
    limits.append(
        "A model extracts behaviors and counts from trial evidence. "
        "They are not independent measurements. "
        "The primary result, explanations, and proposed causal links are model interpretations."
    )
    if metadata.trace_source == "self-reported":
        limits.append(SELF_REPORTED_LIMIT)
    if variants.before.total == 1 or variants.after.total == 1:
        limits.append(
            "At least one side has a single trial. Differences can reflect trial-to-trial "
            "variation rather than an instruction effect."
        )
    return limits, missing


def count_data(mode, passed, valid, blocked):
    if mode == "review":
        return (
            "{0} valid {1} · no automatic grading (blocked: {2})".format(
                valid, trial_noun(valid), blocked
            ),
            "",
            False,
        )
    return (
        "{0} of {1} valid {2} met the expectation".format(
            passed, valid, trial_noun(valid)
        ),
        " (blocked: {0})".format(blocked),
        True,
    )


def decision_blurb(single_trial):
    purpose = "A model extracts these comparisons from trial evidence."
    if single_trial:
        purpose += (
            " CAUTION — one trial per side: differences can reflect trial-to-trial variation "
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
        return "from the final answer"
    if trace_source == "self-reported":
        return "from a self-reported action"
    return "from a recorded command"


def tag_legend(trace_source):
    """What each tag on a decision row means."""
    return (
        ("changed", "Changed", "extracted behavior proportions differ between sides"),
        ("same", "Unchanged", "complete trials show the same unanimous behavior"),
        (
            "same",
            "Same proportions",
            "proportions match, but behaviors are mixed or trial evidence is incomplete",
        ),
        (
            "unavailable",
            "Unavailable",
            "the extracted states do not support a comparison",
        ),
        ("action", "Action", "a comparison of actions in the trial evidence"),
        ("result", "Final result", "the primary result identified by the model"),
        ("detail", "Answer detail", "another comparison from the final answer"),
        (
            "cmd",
            source_label(1, trace_source),
            "this row comes from an action the agent reported"
            if trace_source == "self-reported"
            else "this row comes from a recorded command",
        ),
        (
            "ans",
            source_label("answer", trace_source),
            "this row comes from the final answer",
        ),
    )


def headings(target_file):
    return {
        "limits": "Evidence limits",
        "scenario": "What we simulated",
        "expected": "Expected behavior",
        "diff": "Diff of {0}".format(target_file),
        "decision": "Decision diff: actions and answers compared",
        "flow": "Flow diff: recorded commands",
        "result": "Result",
    }


def decision_footer(rows):
    changed = sum(decision_status(row) == "Changed" for row in rows)
    unavailable = sum(decision_status(row) == "Unavailable" for row in rows)
    summary = "{0} of {1} comparisons have different behavior proportions.".format(
        changed, len(rows)
    )
    if unavailable:
        summary += (
            " {0} comparisons lack usable behaviors on one or both sides.".format(
                unavailable
            )
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


def decision_overview(report):
    consistent = (
        consistent_changes(report.decisions) if complete_trial_evidence(report) else ()
    )
    if consistent:
        names = ", ".join(
            report.decisions.rows[index - 1].topic.strip()
            or report.decisions.rows[index - 1].decision
            for index in consistent
        )
        return (
            CONSISTENT_HEADING
            + ": "
            + names
            + ". Result summary: "
            + report.result.text
        )
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
        return "Command-category combinations — unavailable"
    changed = any(
        before * flow.after.total != after * flow.before.total
        for _, before, after in patterns
    )
    return "Command-category combinations — " + ("changed" if changed else "unchanged")


def dropped_rows(dropped):
    return "Omitted {0} comparison{1}: counts did not match the trials.".format(
        dropped, "" if dropped == 1 else "s"
    )


def scenario_sections(report):
    """Explain the saved setup without deriving new facts from trial outcomes."""
    scenario = report.content.scenario
    task = report.content.task
    if not scenario or scenario == task:
        scenario = report.summary.scenario or (
            "The agent was given the task below under two instruction versions."
            if task
            else "No scenario description was saved."
        )
    metadata = report.metadata
    evidence = (
        "Evidence type: self-reported actions and answers, not captured tool activity."
        if metadata.trace_source == "self-reported"
        else "Evidence type: captured tool records and final answers, where available. "
        "A proposed action in an answer does not mean it was executed."
    )
    expected = (
        report.content.expected
        + "\nThis is the supplied expectation, not an observed result."
        if report.content.expected
        else "No expected behavior was supplied. This comparison describes what differed; "
        "it does not decide which behavior is correct."
    )
    return (
        (report.content.scenario_heading, scenario),
        (
            "What changed",
            "Instruction file: {0}\nBefore: {1}\nAfter: {2}\n"
            "The comparison tests the same task under these two instruction versions.".format(
                metadata.target_file, metadata.before_label, metadata.after_label
            ),
        ),
        (
            "How it was compared",
            "{0} Before {1} and {2} After {3} recorded. Each trial is a separate attempt "
            "at the scenario, not a later step in one task.\nModel: {4}\n{5}".format(
                report.variants.before.total,
                trial_noun(report.variants.before.total),
                report.variants.after.total,
                trial_noun(report.variants.after.total),
                metadata.model,
                evidence,
            ),
        ),
        (report.content.expected_heading, expected),
    )


def build_content(
    config,
    scenario,
    task,
    metadata,
    decisions,
    before_total,
    after_total,
):
    names = headings(metadata.target_file)
    facts = meta(metadata, before_total, after_total)
    return ContentData(
        title=config.get("title", "Behavior Diff"),
        subtitle=subtitle(facts),
        meta=facts,
        note=config.get("sub", ""),
        limits_heading=names["limits"],
        scenario_heading=names["scenario"],
        scenario=scenario,
        task=task,
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
