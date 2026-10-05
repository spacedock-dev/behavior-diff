"""Pure Markdown renderer for Behavior Diff reports."""

import html
import re
from itertools import zip_longest

from reporting import content
from reporting.schema import ReportData


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
        _text(content.instruction_edit_aim(report.intent)) + "\n",
        _text(content.instruction_edit_counts(report.rule_diff)) + "\n",
        "<pre><code>" + "\n".join(lines) + "</code></pre>\n",
        _text(content.EDIT_LINK_NOTE) + "\n",
    ]


def _other_findings_markdown(report):
    findings = content.additional_findings(report)
    markdown = ["<details><summary>Other findings</summary>\n"]
    if findings:
        for index, text in findings:
            row = report.decisions.rows[index - 1]
            source = content.source_label(row.anchor, report.metadata.trace_source)
            links = f"[Comparison {index} · {_text(source)}](#decision-{index})"
            for number in row.edit_hunks:
                label = _text(content.instruction_hunk_label(report.rule_diff, number))
                links += f" · [{label}](#edit-hunk-{number})"
            markdown.append(f"- {_text(text)}<br>{links}\n")
        markdown.append(_text(content.additional_findings_note(report)) + "\n")
    else:
        markdown.append(_text(content.NO_ADDITIONAL_FINDINGS) + "\n")
    markdown.append(
        "[View all behavior comparisons](#panel-decision)\n"
        if report.decisions.rows
        else "[Inspect trial evidence](#panel-trials)\n"
    )
    markdown.append("</details>\n")
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


def _summary_markdown(report):
    summary = report.summary
    intent = report.intent
    intent_label, intent_note = content.intent_context(intent)
    markdown = [
        "## Summary\n",
        f"**{_text(summary.headline)}**\n",
        "### 1. The intended change\n",
        f"**{_text(intent_label)}**\n",
        _text(intent.text) + "\n",
        _text(intent_note) + "\n",
    ]
    markdown += [
        "[View instruction changes](#instruction-diff)\n",
        "### 2. What was observed\n",
    ]
    if summary.scenario:
        markdown.append(_text(summary.scenario) + "\n")
    markdown.append(_text(summary.evidence_label) + "\n")
    markdown.append(f"Comparison: {_text(summary.status)}\n")
    for label, side in (("Before", summary.before), ("After", summary.after)):
        markdown.append(f"#### {label}\n")
        if not side.choices:
            markdown.append("No supported comparison is available.\n")
        for choice in side.choices:
            markdown.append(f"**{_text(choice.label)}**\n")
            if choice.detail:
                markdown.append(_text(choice.detail) + "\n")
            markdown.append(_text(content.trial_count(choice.count, side.total)) + "\n")
    context = content.primary_result_context(report)
    if context is not None:
        markdown.append(f"#### {_text(context.heading)} — {_text(context.status)}\n")
        for label, text in context.sides:
            markdown.append(f"**{label}:** {_text(text)}\n")
        markdown.append(_text(context.note) + "\n")
    target = (
        "panel-decision"
        if summary.decision is not None and summary.status != "unavailable"
        else "panel-trials"
    )
    label = (
        "View behavior comparisons"
        if target != "panel-trials"
        else "View available trial records"
    )
    markdown.append(f"[{label}](#{target})\n")
    markdown.append("### 3. What this does — and does not — establish\n")
    for label, claim in (
        ("Why it matters", summary.why),
        ("Watch out", summary.caution),
    ):
        if claim:
            markdown.append(
                f"**{label}:** {_text(claim.text)} {_decision_links(claim.decisions)}\n"
            )
    markdown += [f"- {_text(notice)}" for notice in summary.notices]
    markdown.append("")
    return markdown


def render_markdown(report: ReportData) -> str:
    """Return the complete Markdown report without accessing external state."""
    metadata = report.metadata
    content_data = report.content
    result = report.result
    markdown = [f"# {_text(content_data.title)}\n", _text(content_data.subtitle) + "\n"]
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
    markdown += _other_findings_markdown(report)
    markdown += [
        f"<details><summary>{html.escape(content_data.limits_heading)}</summary>\n",
    ]
    markdown += [f"- {_text(limit)}" for limit in result.limits]
    markdown.append("")
    markdown.append("</details>\n")
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
