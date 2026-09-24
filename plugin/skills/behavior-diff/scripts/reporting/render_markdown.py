"""Pure Markdown renderer for Behavior Diff reports."""

import html
import re

from reporting import content
from reporting.schema import ReportData


def _text(value: str) -> str:
    """Keep untrusted text literal, including inside tables and link labels."""
    escaped = html.escape(value.replace("\r\n", "\n").replace("\r", "\n"), quote=False)
    escaped = re.sub(r"([\\`*_{}\[\]()#+.!-])", r"\\\1", escaped)
    return escaped.replace("|", "&#124;").replace("\n", "<br>")


def _choices(choices, total: int) -> str:
    return (
        " · ".join(
            f"{_text(choice.choice)} ({content.trial_count(choice.count, total)})"
            for choice in choices
        )
        or "—"
    )


def _decision_links(indexes) -> str:
    return " · ".join(f"[Decision {index}](#decision-{index})" for index in indexes)


def _comparison_table(report: ReportData, indexes, column: str, count_note: str):
    if not indexes:
        return []
    markdown = [
        _text(count_note) + "\n",
        f"| {column} | Before | After |",
        "| --- | --- | --- |",
    ]
    for index in indexes:
        row = report.decisions.rows[index - 1]
        source = content.source_label(row.anchor, report.metadata.trace_source)
        markdown.append(
            f"| [{_text(row.topic.strip() or row.decision)}](#decision-{index})"
            f"<br>{_text(source)} | {_choices(row.before, report.decisions.before_count)}"
            f" | {_choices(row.after, report.decisions.after_count)} |"
        )
    markdown.append("")
    return markdown


def _decision_markdown(report):
    decisions = report.decisions
    if not decisions.rows:
        return []
    legend = "\n".join(
        f"- **{_text(label)}** — {_text(meaning)}"
        for _, label, meaning in report.content.tag_legend
    )
    markdown = [
        '<a id="panel-decision"></a>\n',
        f"## {_text(report.content.decision_heading)}\n",
        _text(report.content.decision_blurb) + "\n",
        _text(content.TRIAL_COUNT_NOTE) + "\n",
        "Tags:\n",
        legend + "\n",
    ]
    labels = {
        kind: label
        for kind, label, _ in content.tag_legend(report.metadata.trace_source)
    }
    for index, row in enumerate(decisions.rows, 1):
        source = content.source_label(row.anchor, report.metadata.trace_source)
        if index == decisions.fork:
            mark = labels["root"]
        elif not row.diverges:
            mark = labels["same"]
        elif decisions.fork and index > decisions.fork:
            mark = labels["down"]
        else:
            mark = ""
        markdown += [
            f'<a id="decision-{index}"></a>\n',
            f"### {index} · {_text(row.decision or row.topic)}\n",
            f"*{_text(source)}{' · ' + _text(mark) if mark else ''}*\n",
            f"- BEFORE: {_choices(row.before, decisions.before_count)}",
            f"- AFTER: {_choices(row.after, decisions.after_count)}",
        ]
        if row.note:
            markdown.append(f"- Note: {_text(row.note)}")
        markdown.append("")
    markdown.append(_text(content.decision_footer(decisions.rows, decisions.fork)))
    if decisions.fork_note:
        markdown += [
            "\n### Model explanations\n",
            _text(content.INTERPRETATION_NOTE) + "\n",
            _text(decisions.fork_note),
        ]
    if decisions.dropped:
        markdown.append("\n" + _text(content.dropped_rows(decisions.dropped)))
    markdown.append("")
    return markdown


def _flow_markdown(report):
    flow = report.command_flow
    shared_counts = (
        f"Before: {content.trial_count(flow.before.total, flow.before.total)}"
        f" · After: {content.trial_count(flow.after.total, flow.after.total)}"
    )
    markdown = [
        '<a id="panel-flow"></a>\n',
        f"## {_text(report.content.flow_heading)}\n",
        _text(report.content.flow_purpose) + "\n",
        _text(content.flow_kinds_heading(flow.kinds)) + "\n",
    ]
    markdown += [f"- {_text(kind)}" for kind in flow.kinds]
    markdown.append("")
    if flow.same:
        markdown.append(
            "Every trial on both sides used the same kinds of command: "
            + _text(", ".join(flow.shared))
            + ". The kinds are coarse, so the actual work can still differ. "
            "See the Decision diff and trial evidence.\n"
        )
        markdown.append(shared_counts + "\n")
    else:
        markdown.append("Used by every trial, both sides:\n")
        markdown.extend(f"- {_text(step)} ({shared_counts})" for step in flow.shared)
        markdown.append("\nUsed on only one side:\n")
        for tag, branch in (("BEFORE", flow.before), ("AFTER", flow.after)):
            if not branch.paths:
                markdown.append(
                    f"- {tag}, {content.trial_count(branch.total, branch.total)}: "
                    + _text(", ".join(branch.prefix) or "(no other kind of command)")
                )
                continue
            lead = f"- {tag}"
            if branch.prefix:
                lead += (
                    f", {content.trial_count(branch.total, branch.total)}: "
                    + _text(", ".join(branch.prefix))
                )
            markdown.append(lead + ". Other command kinds by group of trials:")
            for path in branch.paths:
                markdown.append(
                    f"  - {content.trial_count(path.count, branch.total)}: "
                    + _text(", ".join(path.steps) or "(no other kind of command)")
                )
    markdown.append("")
    return markdown


def _count_line(variant):
    count = (
        f"**{_text(variant.count_text)}**"
        if variant.count_emphasized
        else _text(variant.count_text)
    )
    return count + _text(variant.count_suffix)


def render_markdown(report: ReportData) -> str:
    """Return the complete Markdown report without accessing external state."""
    metadata = report.metadata
    content_data = report.content
    result = report.result
    markdown = [f"# {_text(content_data.title)}\n", _text(content_data.subtitle) + "\n"]
    if content_data.note:
        markdown.append(_text(content_data.note) + "\n")
    markdown += [
        '<a id="panel-summary"></a>\n',
        f"## {_text(content_data.result_heading)}\n",
        f"**{_text(result.text)}**\n",
        _text(result.summary) + "\n",
        f"### {_text(content_data.scenario_heading)}\n",
        _text(content_data.scenario) + "\n",
    ]
    if content_data.expected:
        markdown += [
            f"### {_text(content_data.expected_heading)}\n",
            _text(content_data.expected) + "\n",
        ]
    markdown.append(f"### {_text(result.outcome_heading)}\n")
    markdown += _comparison_table(
        report,
        result.outcomes,
        "Final result" if report.decisions.outcome is not None else "Answer detail",
        content.TRIAL_COUNT_NOTE,
    )
    if not result.outcomes:
        markdown.append("No result or reported-answer comparison is available.\n")
    markdown.append(f"### {_text(result.behavior_heading)}\n")
    markdown += _comparison_table(
        report, result.behavior, "Action or check", content.BEHAVIOR_COUNT_NOTE
    )
    if not result.behavior:
        markdown.append("No separate action comparison is available.\n")
    if result.implications or report.decisions.fork_note:
        markdown += [
            "### Model explanations\n",
            _text(content.INTERPRETATION_NOTE) + "\n",
        ]
        markdown += [
            f"- {_text(claim.text)} {_decision_links(claim.decisions)}"
            for claim in result.implications
        ]
        if report.decisions.fork_note:
            fork_link = (
                _decision_links((report.decisions.fork,))
                if report.decisions.fork
                else ""
            )
            markdown.append(f"- {_text(report.decisions.fork_note)} {fork_link}")
        markdown.append("")
    links = []
    if report.decisions.rows:
        links.append("[Compare decisions](#panel-decision)")
    links.append("[Inspect trial evidence](#panel-trials)")
    markdown.append(" · ".join(links) + "\n")
    markdown += [
        f"<details><summary>{html.escape(content_data.diff_heading)}</summary>\n",
        "<pre><code>" + html.escape(report.rule_diff.rstrip()) + "</code></pre>\n",
        "</details>\n",
        f"## {_text(content_data.limits_heading)}\n",
    ]
    markdown += [f"- {_text(limit)}" for limit in result.limits]
    markdown.append("")
    markdown += _decision_markdown(report)
    if metadata.trace_source != "self-reported":
        markdown += _flow_markdown(report)
    markdown += ['<a id="panel-trials"></a>\n', "## Trial evidence\n"]
    for side, variant, label in (
        ("before", report.variants.before, f"BEFORE — {metadata.before_label}"),
        ("after", report.variants.after, f"AFTER — {metadata.after_label}"),
    ):
        markdown.append(f"### {_text(label)}\n")
        markdown.append(_count_line(variant) + "\n")
        for trial in variant.trials:
            anchor = f"trial-{side}-{trial.name.encode('utf-8').hex()}"
            markdown += [
                f'<a id="{anchor}"></a>\n',
                f"#### {_text(trial.name)} — {_text(trial.verdict)}\n",
            ]
            if trial.actions != "-":
                markdown.append(_text(trial.actions) + "\n")
            action_label = (
                "self-reported actions"
                if metadata.trace_source == "self-reported"
                else "commands the agent ran"
            )
            markdown.append(
                f"<details><summary>{action_label} ({len(trial.commands)})</summary>\n"
                "<pre>" + html.escape("\n\n".join(trial.commands)) + "</pre>\n"
                "</details>\n"
            )
            markdown.append(
                "<details><summary>final answer to the user</summary>\n"
                "<pre>" + html.escape(trial.final.strip()) + "</pre>\n"
                "</details>\n"
            )
    return "\n".join(markdown)
