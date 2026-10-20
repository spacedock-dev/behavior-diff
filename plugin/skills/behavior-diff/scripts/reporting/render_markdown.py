"""Pure Markdown renderer for Behavior Diff reports."""

import html
import re
from itertools import zip_longest

from reporting import content
from reporting.attention import AttentionFindingData
from reporting.provenance import ci_header_links, commit_links, header_links
from reporting.schema import ReportData
from reporting.summary import (
    GATE_NOTE,
    question_distribution,
    question_distribution_changed,
)
from reporting.target import (
    UNAVAILABLE,
    acceptance,
    evidence_limit_text,
)


def _text(value: str) -> str:
    """Keep untrusted text literal, including inside tables and link labels."""
    escaped = html.escape(value.replace("\r\n", "\n").replace("\r", "\n"), quote=False)
    escaped = re.sub(r"([\\`*_{}\[\]()#+.!-])", r"\\\1", escaped)
    return escaped.replace("|", "&#124;").replace("\n", "<br>")


def _choices(choices, total: int) -> str:
    return "<br><br>".join(
        f"{_text(choice.choice)}<br>{content.trial_count(choice.count, total)}"
        for choice in choices
    ) or _text(content.NO_EXTRACTED_CHOICE)


def _decision_links(indexes) -> str:
    return " · ".join(f"[Comparison {index}](#decision-{index})" for index in indexes)


def _edit_links(row, diff):
    if not row.edit_hunks:
        return "Related edit unavailable — no mapping recorded."
    links = " · ".join(
        f"[{_text(content.instruction_hunk_label(diff, number))}](#edit-hunk-{number})"
        for number in row.edit_hunks
    )
    return "Related edit (model interpretation): " + links


def _instruction_edit(report):
    lines = []
    for line, number in content.instruction_diff_lines(report.rule_diff):
        text = html.escape(line)
        if number:
            label = html.escape(
                content.instruction_hunk_label(report.rule_diff, number)
            )
            text = f'<span id="edit-hunk-{number}">{label}<br>{text}</span>'
        lines.append(text)
    return [
        f"### {_text(report.content.diff_heading)}\n",
        *(
            _recorded_purpose(report)
            if report.decisions.purpose
            else [_text(content.instruction_edit_aim(report.intent)) + "\n"]
        ),
        _text(content.instruction_edit_counts(report.rule_diff)) + "\n",
        "<pre><code>" + "\n".join(lines) + "</code></pre>\n",
        _text(content.EDIT_LINK_NOTE) + "\n",
    ]


def _recorded_purpose(report):
    """List every frozen goal in full with its provenance, independent of assessment."""
    markdown = [
        f"#### {content.RECORDED_PURPOSE_HEADING}\n",
        _text(content.RECORDED_PURPOSE_NOTE) + "\n",
    ]
    for index, goal in enumerate(report.decisions.purpose, 1):
        markdown += [
            f"**Goal {index}:** {_text(goal.text)}\n",
            _text(content.purpose_goal_source(goal)) + "\n",
        ]
    return markdown


def _attention_notice_markdown(attention):
    if attention is None:
        return [
            _text(content.ATTENTION_UNAVAILABLE) + "\n",
            _text(content.ATTENTION_UNAVAILABLE_NOTE) + "\n",
        ]
    markdown = [_text(attention.assessment) + "\n"]
    if not attention.findings:
        markdown.append(_text(content.ATTENTION_EMPTY_NOTE) + "\n")
    return markdown


def _attention_branches_markdown(report, finding: AttentionFindingData):
    markdown = []
    for side in ("before", "after"):
        markdown.append(f"**{side.capitalize()}**\n")
        for choice, steps, count, total in content.attention_branches(
            report, finding, side
        ):
            story = " → ".join(_text(step.label) for step in steps)
            markdown.append(
                f"- {story}<br>{_text(choice)} — "
                f"{_text(content.trial_count(count, total))}"
            )
        markdown.append("")
    return markdown


def _attention_summary_markdown(report):
    attention = report.decisions.attention
    markdown = [f"#### {content.SUMMARY_ATTENTION_HEADING}\n"]
    markdown += _attention_notice_markdown(attention)
    for item in content.attention_items(report):
        finding = item.finding
        if finding is None:
            gap = content.target_gap(report, item.criterion_number)
            anchor = content.target_criterion_anchor(item.criterion_number)
            markdown += [
                f"#### {_text(gap.title)}\n",
                f"**{_text(gap.result)}**\n",
                _text(gap.consequence) + "\n",
                _text(content.ATTENTION_TARGET_GAP_NOTE) + "\n",
                f"**What you can do:** {_text(gap.next_step)}\n",
                f"[See the target check →](#{anchor})\n",
            ]
            continue
        relationship, evidence = content.attention_labels(
            finding, report.metadata.trace_source
        )
        anchor = content.attention_finding_anchor(finding.decision)
        markdown += [
            f"#### {_text(finding.title)}\n",
            _text(finding.consequence) + "\n",
            f"**Relationship:** {_text(relationship)}<br>**Evidence:** {_text(evidence)}\n",
            f"**Limit:** {_text(finding.limit)}\n",
            f"**What you can do:** {_text(finding.next_step)}\n",
            f"[See the evidence for this concern →](#{anchor})\n",
        ]
    label = (
        "See why this matters →"
        if attention is not None and attention.findings
        else "Read the assessment"
    )
    markdown.append(f"[{label}](#attention-explanation)\n")
    return markdown


def _attention_branch_evidence_markdown(report, finding: AttentionFindingData):
    markdown = [
        "**Observed branch evidence**\n",
        _text(content.ATTENTION_COUNT_NOTE) + "\n",
    ]
    for side in ("before", "after"):
        markdown.append(f"**{side.capitalize()}**\n")
        for choice, count, total, members in content.attention_branch_evidence(
            report, finding, side
        ):
            support = (
                " · ".join(
                    f"[{_text(name)}](#{content.trial_anchor(side, name)})"
                    for name in members
                )
                if members
                else _text(content.ATTENTION_MEMBERSHIP_UNAVAILABLE)
            )
            markdown.append(
                f"- **{_text(choice)}** — {_text(content.trial_count(count, total))}"
                f"<br>{support}"
            )
        markdown.append("")
    return markdown


def _attention_explanation_markdown(report):
    attention = report.decisions.attention
    markdown = [
        '<a id="attention-explanation"></a>\n',
        "### What needs your attention\n",
    ]
    markdown += _attention_notice_markdown(attention)
    for item in content.attention_items(report):
        finding = item.finding
        if finding is None:
            continue
        relationship, evidence = content.attention_labels(
            finding, report.metadata.trace_source
        )
        markdown += [
            f'<a id="{content.attention_finding_anchor(finding.decision)}"></a>\n',
            f"#### {_text(finding.title)}\n",
            _text(finding.consequence) + "\n",
            "**Why this concern matters (model interpretation)**\n",
            f"**Relationship:** {_text(relationship)}<br>**Evidence:** {_text(evidence)}\n",
            _text(finding.explanation) + "\n",
            f"**Matters if:** {_text(finding.matters_if)}\n",
            f"**What you can do:** {_text(finding.next_step)}\n",
        ]
        markdown.append("**What each branch did**\n")
        markdown += _attention_branches_markdown(report, finding)
        markdown += _attention_branch_evidence_markdown(report, finding)
        if finding.context:
            markdown.append("**Related context (model interpretation)**\n")
            markdown += [
                f"- {_text(claim.text)} ({_decision_links(claim.decisions)})"
                for claim in finding.context
            ]
            markdown.append("")
        references = tuple(
            dict.fromkeys(
                (finding.decision,)
                + tuple(index for claim in finding.context for index in claim.decisions)
            )
        )
        markdown += [
            "**Limits and uncertainty**\n",
            _text(finding.limit) + "\n",
        ]
        markdown += [
            "<details><summary>Check the evidence</summary>\n",
            _decision_links(references) + "\n",
            "</details>\n",
        ]
    return markdown


def _decision_markdown(report):
    decisions = report.decisions
    if not decisions.rows:
        return [
            '<a id="panel-decision"></a>\n',
            "## Behavior diff\n",
            _text(content.NO_EXTRACTED_CHOICE) + "\n",
            "[View available trial records](#panel-trials)\n",
        ]
    markdown = [
        '<a id="panel-decision"></a>\n',
        f"## {_text(report.content.decision_heading)}\n",
        f"**{_text(content.decision_overview(report))}**\n",
        _text(report.content.decision_blurb) + "\n",
        '<a id="decision-progression"></a>\n',
        _text(content.DECISION_PROGRESSION_NOTE) + "\n",
        _text(content.TRIAL_COUNT_NOTE) + "\n",
    ]
    if report.metadata.trace_source == "self-reported":
        markdown.append(_text(content.SELF_REPORTED_LIMIT) + "\n")
    markdown += [
        "**Comparison labels · status, role, and source**\n",
        "\n".join(
            f"- **{_text(label)}** — {_text(meaning)}"
            for _, label, meaning in report.content.tag_legend
        ),
        "",
    ]
    for index, row in enumerate(decisions.rows, 1):
        source = content.source_label(row.anchor, report.metadata.trace_source)
        role = content.decision_role(index, row, decisions.outcome)
        status = content.decision_evidence_status(row, decisions, report)
        title = row.topic.strip() or row.decision
        markdown += [
            f'<a id="decision-{index}"></a>\n',
            f"#### {index} · {_text(title)}\n",
        ]
        if row.decision and row.decision != title:
            markdown.append(_text(row.decision) + "\n")
        markdown += [
            f"{_text(role)} · **{_text(status)}** · {_text(source)}\n",
            "| Before | After |",
            "| --- | --- |",
        ]
        markdown.append(
            f"| {_choices(row.before, decisions.before_count)}"
            f" | {_choices(row.after, decisions.after_count)} |\n"
        )
        markdown.append(_edit_links(row, report.rule_diff) + "\n")
        if row.note:
            markdown.append(f"Note: {_text(row.note)}\n")
        markdown.append(
            "Available trial records (all trials; row attribution is not recorded): "
            + " · ".join(
                f"[Trial {number}](#{content.trial_group_anchor(number)})"
                for number in range(
                    1,
                    max(
                        len(report.variants.before.trials),
                        len(report.variants.after.trials),
                    )
                    + 1,
                )
            )
            + "\n"
        )
    markdown.append(_text(content.decision_footer(decisions.rows)) + "\n")
    if decisions.dropped:
        markdown.append(_text(content.dropped_rows(decisions.dropped)) + "\n")
    if decisions.implications or decisions.fork_note:
        markdown += [
            "### Model explanations\n",
            _text(content.INTERPRETATION_NOTE) + "\n",
        ]
        markdown += [
            f"- {_text(claim.text)} {_decision_links(claim.decisions)}"
            for claim in decisions.implications
        ]
        if decisions.fork_note:
            fork_link = _decision_links((decisions.fork,)) if decisions.fork else ""
            markdown.append(f"- {_text(decisions.fork_note)} {fork_link}")
        markdown.append("")
    markdown.append("[Inspect trial evidence](#panel-trials)\n")
    return markdown


def _flow_markdown(report):
    flow = report.command_flow
    patterns = content.flow_patterns(flow)
    markdown = [
        '<a id="panel-flow"></a>\n',
        f"## {_text(report.content.flow_heading)}\n",
        '<a id="flow-progression"></a>\n',
        "### Flow progression\n",
        _text(content.FLOW_PROGRESSION_NOTE) + "\n",
    ]
    for side, variant, label in (
        ("before", report.variants.before, "Before"),
        ("after", report.variants.after, "After"),
    ):
        markdown.append(f"#### {label}\n")
        progressions = content.command_progressions(variant)
        if not progressions:
            markdown.append("No trials\n")
        for index, (commands, trials) in enumerate(progressions, 1):
            markdown += [
                f"##### Path {index} · {content.trial_count(len(trials), variant.total)}\n",
                " · ".join(
                    f"[{_text(trial.name)} — {_text(trial.verdict)}]"
                    f"(#{content.trial_anchor(side, trial.name)})"
                    for trial in trials
                )
                + "\n",
            ]
            if commands:
                markdown.append(
                    "<ol>\n"
                    + "".join(
                        f"<li><pre><code>{html.escape(command)}</code></pre></li>\n"
                        for command in commands
                    )
                    + "</ol>\n"
                )
            else:
                markdown.append(_text(content.NO_COMMANDS_RECORDED) + "\n")
    markdown += [
        "### Command-category comparison\n",
        f"**{_text(content.flow_overview(flow, patterns))}**\n",
        _text(report.content.flow_purpose) + "\n",
    ]
    if patterns:
        markdown += [
            _text(content.FLOW_COUNT_NOTE) + "\n",
            "| Command-category combination | Before | After |",
            "| --- | --- | --- |",
        ]
        for steps, before_count, after_count in patterns:
            label = ", ".join(steps) or "No categorized commands"
            before_count_text = (
                content.trial_count(before_count, flow.before.total)
                if flow.before.total
                else "No trials"
            )
            after_count_text = (
                content.trial_count(after_count, flow.after.total)
                if flow.after.total
                else "No trials"
            )
            markdown.append(
                f"| {_text(label)} | {before_count_text} | {after_count_text} |"
            )
        markdown.append("")
    else:
        markdown.append("No recorded command-category combinations are available.\n")
    markdown += [
        "<details><summary>Command categories</summary>\n",
        _text(content.flow_kinds_heading(flow.kinds)) + "\n",
    ]
    markdown += [f"- {_text(kind)}" for kind in flow.kinds]
    markdown.append("\n</details>\n")
    links = []
    if report.decisions.rows:
        links.append("[Compare behaviors](#panel-decision)")
    links.append("[Inspect trial evidence](#panel-trials)")
    markdown.append(" · ".join(links) + "\n")
    return markdown


def _count_line(variant):
    count = (
        f"**{_text(variant.count_text)}**"
        if variant.count_emphasized
        else _text(variant.count_text)
    )
    return count + _text(variant.count_suffix)


def _target_summary_markdown(report, target):
    lines = [
        "| What we checked | Before → After |",
        "| --- | --- |",
    ]
    for criterion in target.criteria:
        result = _text(
            question_distribution(criterion, "before", report.variants.before.total)
            + " → "
            + question_distribution(criterion, "after", report.variants.after.total)
        )
        if question_distribution_changed(
            criterion, report.variants.before.total, report.variants.after.total
        ):
            result = f"**{result}**"
        lines.append(f"| {_text(criterion.text)} | {result} |")
    return lines + [""]


def _target_explanation_markdown(report):
    target = report.decisions.target_assessment
    lines = ["### What we checked\n"]
    if target is None:
        lines.append(_text(UNAVAILABLE) + "\n")
    else:
        lines += _target_summary_markdown(report, target)
        sources = {entry.id: entry for entry in report.decisions.recorded_evidence}
        for number, criterion in enumerate(target.criteria, 1):
            lines += [
                f'<a id="{content.target_criterion_anchor(number)}"></a>\n',
                f"#### {_text(criterion.text)}\n",
                "Before: "
                + _text(
                    question_distribution(
                        criterion, "before", report.variants.before.total
                    )
                )
                + " · After: "
                + _text(
                    question_distribution(
                        criterion, "after", report.variants.after.total
                    )
                )
                + "\n",
                f"**Required evidence:** {_text(criterion.required_evidence)}\n",
            ]
            lines += [
                "<details><summary>Trial-by-trial reasoning and sources</summary>\n",
                f"Goal {criterion.goal} · {_text(criterion.mode)}\n",
                _text(acceptance(criterion)) + "\n",
            ]
            for side in ("before", "after"):
                for trial in getattr(criterion, side):
                    anchor = content.trial_anchor(side, trial.trial)
                    lines += [
                        f"**{side.capitalize()} · [{_text(trial.trial)}](#{anchor}) · "
                        f"{_text(trial.outcome.replace('_', ' '))}**\n",
                        _text(trial.explanation) + "\n",
                    ]
                    lines.append("<details><summary>Recorded evidence</summary>\n")
                    for ref in trial.refs:
                        entry = sources.get(ref)
                        if entry is None:
                            text = trial.output_excerpt
                            label = (
                                "Exact final-answer excerpt"
                                if text
                                else "Final-answer reference; inspect the full trial evidence"
                            )
                        else:
                            text = entry.text
                            label = f"{entry.source} · returned characters {entry.range.start}–{entry.range.end} · {entry.status} · {entry.reason}"
                        lines += [
                            _text(ref + " · " + label) + "\n",
                            "<pre>" + html.escape(text) + "</pre>\n",
                        ]
                    lines.append("</details>\n")
            lines.append("</details>\n")
    if report.decisions.recorded_evidence:
        lines.append(
            "<details><summary>Recorded source availability and limits</summary>\n"
        )
        lines.append(
            _text(evidence_limit_text(report.decisions.evidence_limits)) + "\n"
        )
        for entry in report.decisions.recorded_evidence:
            lines += [
                _text(f"{entry.id} · {entry.source} · {entry.status} · {entry.reason}")
                + "\n",
                "<pre>" + html.escape(entry.text) + "</pre>\n",
            ]
        lines.append("</details>\n")
    return lines


def _summary_checks_markdown(report):
    checks = report.summary.checks
    if not checks:
        return [_text(content.SUMMARY_NO_CHECKS) + "\n"]
    lines = [
        f"| Expected | Before | After | What this means | {content.SUMMARY_SCOPE_HEADING} |",
        "| --- | --- | --- | --- | --- |",
    ]
    lines += [
        f"| [{_text(check.text)}](#{content.target_criterion_anchor(check.criterion)}) "
        f"| {_text(check.before)} | {_text(check.after)} | {_text(check.meaning)} "
        f"| {_text(check.scope)} |"
        for check in checks
    ]
    lines.append("")
    return lines


def _summary_markdown(report):
    summary = report.summary
    intent = content.summary_intent(report)
    state_text, diagnostic = content.summary_state_text(report)
    markdown = [
        "## Summary\n",
        f"`{_text(content.summary_status(report))}`\n",
        f"**{_text(summary.headline)}**\n",
        f"### 1. {content.SUMMARY_FINDING_HEADING}\n",
        _text(state_text) + "\n",
    ]
    if diagnostic:
        markdown += [
            f"<details><summary>{content.SUMMARY_DIAGNOSTICS_LABEL}</summary>\n",
            _text(diagnostic) + "\n",
            "</details>\n",
        ]
    markdown += [
        f"### 2. {content.SUMMARY_EXPECTATION_HEADING}\n",
        f"#### {content.SUMMARY_EXPECTED_LABEL}\n",
        f"**{_text(intent.label)}**\n",
        _text(intent.text) + "\n",
        _text(intent.note) + "\n",
        "[Instruction changes →](#instruction-diff)\n",
        f"#### {content.SUMMARY_OBSERVED_LABEL}\n",
    ]
    markdown += [f"- {_text(line)}" for line in content.summary_observed(report)]
    markdown += [
        "",
        f"**{content.SUMMARY_IMPLICATION_LABEL}** "
        f"{_text(content.summary_implication(report))}\n",
    ]
    markdown += _summary_checks_markdown(report)
    markdown.append(f"### 3. {content.SUMMARY_METHOD_HEADING}\n")
    markdown.append(f"#### {content.SUMMARY_TASK_HEADING}\n")
    if report.content.task:
        markdown += [
            f"**{content.SUMMARY_TASK_LABEL}:** "
            f"{_text(content.task_preview(report.content.task))}\n",
            "<details><summary>Full task</summary>\n",
            "<pre><code>" + html.escape(report.content.task) + "</code></pre>\n",
            "</details>\n",
        ]
    else:
        markdown.append(_text(content.SCENARIO_PROMPT_UNAVAILABLE) + "\n")
    for heading, lines in content.summary_method_sections(report):
        markdown.append(f"#### {heading}\n")
        markdown += [f"- {_text(line)}" for line in lines]
        markdown.append("")
    markdown.append(f"#### {content.SUMMARY_CAVEATS_HEADING}\n")
    markdown += [f"- {_text(notice)}" for notice in summary.notices]
    markdown += ["", f"<details><summary>{content.SUMMARY_HELP_LABEL}</summary>\n"]
    markdown += [f"- {_text(line)}" for line in content.SUMMARY_HELP]
    markdown += ["", "</details>\n"]
    markdown += ["", f"### 4. {content.SUMMARY_EVIDENCE_HEADING}\n"]
    groups = content.summary_check_groups(report)
    if groups:
        markdown.append(f"#### {content.SUMMARY_DIGEST_HEADING}\n")
        markdown += [
            f"- **{_text(label)}** "
            + ", ".join(
                f"[Check {number}](#{content.target_criterion_anchor(number)})"
                for number in numbers
            )
            for _, label, numbers in groups
        ]
        markdown.append("")
    qualification = content.summary_qualification(report)
    if qualification:
        markdown.append(f"> {_text(qualification)}\n")
    markdown.append(_text(summary.evidence_label) + "\n")
    for side_name in ("before", "after"):
        side = getattr(summary, side_name)
        markdown.append(f"#### {side_name.capitalize()}\n")
        start = content.summary_start(report, side_name)
        if start is not None:
            markdown += [
                f"**Observed start:** {_text(start.text)}\n",
                _text(start.source) + "\n",
            ]
            if start.ordered:
                markdown.append("↓\n")
        if not side.choices:
            markdown.append("No supported comparison is available.\n")
        for choice in side.choices:
            markdown.append(f"**{_text(choice.label)}**\n")
            if choice.detail:
                markdown.append(_text(choice.detail) + "\n")
            markdown.append(_text(content.trial_count(choice.count, side.total)) + "\n")
    context = content.primary_result_context(report)
    if context is not None and report.decisions.target_assessment is None:
        markdown.append(f"#### {_text(context.heading)} — {_text(context.status)}\n")
        for label, text in context.sides:
            markdown.append(f"**{label}:** {_text(text)}\n")
        markdown.append(_text(context.note) + "\n")
    if summary.why is None:
        markdown.append(content.SUMMARY_INTERPRETATION_UNAVAILABLE + "\n")
    else:
        markdown.append(
            f"**{content.SUMMARY_MEANING_LABEL}:** {_text(summary.why.text)} "
            f"{_decision_links(summary.why.decisions)}\n"
        )
    if summary.context:
        markdown.append(
            f"**{content.SUMMARY_CONTEXT_LABEL}:** {_text(summary.context.text)} "
            f"{_decision_links(summary.context.decisions)}\n"
        )
    if summary.caution:
        markdown.append(
            f"**Watch out:** {_text(summary.caution.text)} "
            f"{_decision_links(summary.caution.decisions)}\n"
        )
    markdown += _attention_summary_markdown(report)
    markdown.append(
        "[Understand the change →](#panel-explanation) · "
        "[Behavior diff →](#panel-decision) · [Trial evidence →](#panel-trials)\n"
    )
    markdown += [
        f"### 5. {content.SUMMARY_NEXT_HEADING}\n",
        _text(summary.next_action) + "\n",
        _text(GATE_NOTE) + "\n",
    ]
    return markdown


def _explanation_markdown(report):
    explanation = report.decisions.explanation
    markdown = [
        '<a id="panel-explanation"></a>\n',
        "## Understand the change\n",
        f"**{content.EXPLANATION_CONCLUSION_LABEL}** {_text(report.summary.headline)} "
        "[Summary](#panel-summary)\n",
    ]
    qualification = content.summary_qualification(report)
    if qualification:
        markdown.append(f"> {_text(qualification)}\n")
    complete = content.complete_trial_evidence(report)
    if explanation is None or not complete:
        notice = (
            content.CHANGE_EXPLANATION_UNAVAILABLE
            if complete
            else content.CHANGE_EXPLANATION_INCOMPLETE
        )
        markdown += [
            "### Change explanation unavailable\n",
            _text(notice) + "\n",
        ]
        markdown += _attention_explanation_markdown(report)
        markdown += _target_explanation_markdown(report)
    else:
        markdown += [
            f"### {content.EXPLANATION_MODEL_LABEL} {_text(explanation.headline)}\n",
            _text(explanation.overview) + "\n",
            _text(content.INTERPRETATION_NOTE) + "\n",
        ]
        references = []
        for number, step in enumerate(explanation.steps, 1):
            references.extend(step.decisions)
            markdown += [
                f"### {number}. {_text(step.title)}\n",
                "#### Before\n",
                _text(step.before) + "\n",
                "#### After\n",
                _text(step.after) + "\n",
                "#### What this means\n",
                _text(step.meaning) + "\n",
                _decision_links(step.decisions) + "\n",
            ]
        markdown += _attention_explanation_markdown(report)
        for heading, claims in (
            ("What stays the same", explanation.unchanged),
            ("What this evidence cannot establish", explanation.limits),
        ):
            if claims:
                markdown.append(f"### {heading}\n")
                for claim in claims:
                    references.extend(claim.decisions)
                    markdown.append(
                        f"- {_text(claim.text)} {_decision_links(claim.decisions)}"
                    )
                markdown.append("")
        markdown += _target_explanation_markdown(report)
        comparisons = content.explanation_comparisons(
            report, tuple(dict.fromkeys(references))
        )
        if comparisons:
            markdown += [
                "<details><summary>Consistency across trials</summary>\n",
                "All extracted branches for the cited comparisons are shown, "
                "including minority choices. Before and After trials are independent; "
                "these counts are model extractions, not causal proof.\n",
            ]
            for index, title, sides in comparisons:
                markdown.append(f"#### {_text(title)}\n")
                markdown += [f"**{label}:** {_text(text)}\n" for label, text in sides]
                markdown.append(_decision_links((index,)) + "\n")
            markdown.append("</details>\n")
        if explanation.examples:
            markdown.append(
                "<details><summary>Exact excerpts from the final answers</summary>\n"
            )
            for example in explanation.examples:
                anchor = content.trial_anchor(example.side, example.trial)
                markdown += [
                    f"**{example.side.capitalize()} · {_text(example.trial)}** · "
                    f"[View full trial evidence](#{anchor})\n",
                    "<pre>" + html.escape(example.text) + "</pre>\n",
                ]
            markdown.append("</details>\n")
    markdown += [
        "[View behavior comparisons](#panel-decision) · "
        "[View recorded command flow](#panel-flow) · "
        "[View instruction changes](#instruction-diff) · "
        "[Inspect trial evidence](#panel-trials)\n",
    ]
    return markdown


def _source_link(link):
    return f"[{_text(link.text)}](<{link.url}>)"


def _link_row(links):
    return " · ".join(f"{_text(link.label)}: {_source_link(link)}" for link in links)


def _source_markdown(source, ci_context):
    """Caller-supplied Git history links, else CI run context; absent locally."""
    if source is None:
        if ci_context is None:
            return []
        return [_link_row(ci_header_links(ci_context)) + "\n"]
    before, after = commit_links(source)
    return [
        _link_row(header_links(source)) + "\n",
        f"{before.label}: {_source_link(before)} → {after.label}: {_source_link(after)}\n",
    ]


def render_markdown(report: ReportData) -> str:
    """Return the complete Markdown report without accessing external state."""
    metadata = report.metadata
    content_data = report.content
    result = report.result
    markdown = [f"# {_text(content_data.title)}\n"]
    markdown += _source_markdown(metadata.source, metadata.ci_context)
    markdown.append(_text(content_data.subtitle) + "\n")
    if content_data.note:
        markdown.append(_text(content_data.note) + "\n")
    markdown.append('<a id="panel-summary"></a>\n')
    markdown += _summary_markdown(report)
    markdown += [
        "<details><summary>Full scenario and expected behavior</summary>\n",
    ]
    for heading, text in content.scenario_sections(report):
        markdown += [f"### {_text(heading)}\n", _text(text) + "\n"]
    if content_data.task:
        markdown += [
            "<details><summary>View full scenario prompt</summary>\n",
            "<pre><code>" + html.escape(content_data.task) + "</code></pre>\n",
            "</details>\n",
        ]
    else:
        markdown.append(_text(content.SCENARIO_PROMPT_UNAVAILABLE) + "\n")
    markdown.append("</details>\n")
    markdown += [
        f"<details><summary>{html.escape(content_data.limits_heading)}</summary>\n",
    ]
    markdown += [f"- {_text(limit)}" for limit in result.limits]
    markdown.append("")
    markdown.append("</details>\n")
    markdown += _explanation_markdown(report)
    markdown.append('<a id="panel-instruction"></a>\n')
    markdown.append('<a id="instruction-diff"></a>\n')
    markdown.append("## Instruction changes\n")
    markdown += _instruction_edit(report)
    markdown += _decision_markdown(report)
    if metadata.trace_source != "self-reported":
        markdown += _flow_markdown(report)
    else:
        markdown += [
            '<a id="panel-flow"></a>\n',
            "## Flow diff\n",
            _text(content.SELF_REPORTED_LIMIT) + "\n",
        ]
    self_reported = metadata.trace_source == "self-reported"
    action_label, empty_actions = content.trial_action_labels(self_reported)
    markdown += [
        '<a id="panel-trials"></a>\n',
        f"## {_text(content.TRIAL_EVIDENCE_HEADING)}\n",
        _text(content.trial_evidence_note(self_reported)) + "\n",
    ]
    markdown.append(
        "Before and After are independent attempts, aligned by trial number for reading; "
        "they are not consecutive steps or verified paired executions.\n"
    )
    markdown.append(
        f"Before — {_text(metadata.before_label)}: {_count_line(report.variants.before)}\n"
    )
    markdown.append(
        f"After — {_text(metadata.after_label)}: {_count_line(report.variants.after)}\n"
    )
    for number, pair in enumerate(
        zip_longest(report.variants.before.trials, report.variants.after.trials), 1
    ):
        summary = content.trial_summary_for_group(report.decisions, *pair)
        markdown += [
            f'<a id="{content.trial_group_anchor(number)}"></a>\n',
            f"### Trial {number}\n",
            f"#### {_text(content.TRIAL_CHANGE_HEADING)}\n",
            _text(summary.takeaway if summary else content.TRIAL_SUMMARY_UNAVAILABLE)
            + "\n",
            '<table><thead><tr><th scope="col">Before</th><th scope="col">After</th></tr></thead><tbody>',
        ]
        if summary is not None:
            markdown.append(
                "<tr><td>"
                + "</td><td>".join(
                    html.escape(sentence)
                    if trial is not None
                    else "No trial record on this side."
                    for trial, sentence in zip(pair, (summary.before, summary.after))
                )
                + "</td></tr>"
            )
            if summary.caveat:
                markdown.append(
                    '<tr><td colspan="2">' + html.escape(summary.caveat) + "</td></tr>"
                )
        markdown += [
            '<tr><th colspan="2">Trial record and verdict</th></tr>',
        ]
        cells = []
        answers = []
        for side, trial in zip(("before", "after"), pair):
            if trial is None:
                cells.append(
                    '<span class="trial-missing">No trial record on this side.</span>'
                )
                answers.append(
                    '<span class="trial-missing">No trial record on this side.</span>'
                )
                continue
            anchor = content.trial_anchor(side, trial.name)
            cells.append(
                f'<a id="{anchor}"></a><strong>{html.escape(trial.name)}</strong> — {html.escape(trial.verdict)}'
            )
            if trial.verdict == "BLOCKED" and trial.outcome:
                cells[-1] += f"<p>{html.escape(trial.outcome)}</p>"
            answers.append(
                "<pre>"
                + html.escape(
                    trial.final if trial.final.strip() else content.NO_FINAL_ANSWER
                )
                + "</pre>"
            )
        markdown += [
            "<tr><td>" + "</td><td>".join(cells) + "</td></tr>",
            f'<tr><th colspan="2">{content.FINAL_ANSWER_HEADING}</th></tr>',
            "<tr><td>" + "</td><td>".join(answers) + "</td></tr></tbody></table>\n",
        ]
        markdown.append("<details><summary>Supporting details · both sides</summary>\n")
        markdown.append(
            '<table><thead><tr><th scope="col">Before</th><th scope="col">After</th></tr></thead><tbody><tr><td>'
            + "</td><td>".join(
                "<pre>" + html.escape(trial.actions) + "</pre>"
                if trial is not None and trial.actions != "-"
                else (
                    "No trial record available"
                    if trial is None
                    else "No action summary recorded"
                )
                for trial in pair
            )
            + "</td></tr></tbody></table>\n</details>\n"
        )
        markdown.append(
            f"<details><summary>{html.escape(action_label)} · both sides</summary>\n"
        )
        markdown.append(
            '<table><thead><tr><th scope="col">Before</th><th scope="col">After</th></tr></thead><tbody><tr><td>'
            + "</td><td>".join(
                "<pre>"
                + html.escape("\n\n".join(trial.commands) or empty_actions)
                + "</pre>"
                if trial is not None
                else "No trial record available"
                for trial in pair
            )
            + "</td></tr></tbody></table>\n</details>\n"
        )
    return "\n".join(markdown)
