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
            f"{_text(choice.choice)} ({choice.count}/{total})" for choice in choices
        )
        or "—"
    )


def _decision_links(indexes) -> str:
    return " · ".join(f"[Decision {index}](#decision-{index})" for index in indexes)


def _comparison_table(report: ReportData, indexes, caption: str):
    if not indexes:
        return []
    markdown = [
        caption + "\n",
        "| Decision evidence | Before | After |",
        "| --- | --- | --- |",
    ]
    for index in indexes:
        row = report.decisions.rows[index - 1]
        source = content.source_label(row.anchor, report.metadata.trace_source)
        markdown.append(
            f"| [{index} · {_text(row.decision or row.topic)}](#decision-{index})"
            f"<br>{source} | {_choices(row.before, report.decisions.before_count)}"
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
        "Tags:\n",
        legend + "\n",
    ]
    for index, row in enumerate(decisions.rows, 1):
        source = content.source_label(row.anchor, report.metadata.trace_source)
        if index == decisions.fork:
            mark = "first difference"
        elif not row.diverges:
            mark = "same before and after"
        elif decisions.fork and index > decisions.fork:
            mark = "follows from it"
        else:
            mark = ""
        markdown += [
            f'<a id="decision-{index}"></a>\n',
            f"### {index} · {_text(row.decision or row.topic)}\n",
            f"*{source}{' · ' + mark if mark else ''}*\n",
            f"- BEFORE: {_choices(row.before, decisions.before_count)}",
            f"- AFTER: {_choices(row.after, decisions.after_count)}",
        ]
        if row.note:
            markdown.append(f"- Note: {_text(row.note)}")
        markdown.append("")
    markdown.append(_text(content.decision_footer(decisions.rows, decisions.fork)))
    if decisions.fork_note:
        markdown.append("\nModel interpretation: " + _text(decisions.fork_note))
    if decisions.dropped:
        markdown.append("\n" + _text(content.dropped_rows(decisions.dropped)))
    markdown.append("")
    return markdown


def _flow_markdown(report):
    flow = report.command_flow
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
            + ". Differences, if any, are in the final answers below.\n"
        )
    else:
        markdown.append("Used by every trial, both sides:\n")
        markdown.extend(f"- {_text(step)}" for step in flow.shared)
        markdown.append("\nUsed on only one side:\n")
        for tag, branch in (("BEFORE", flow.before), ("AFTER", flow.after)):
            if not branch.paths:
                markdown.append(
                    f"- {tag}, all {branch.total} trials: "
                    + _text(", ".join(branch.prefix) or "(no other kind of command)")
                )
                continue
            lead = f"- {tag}"
            if branch.prefix:
                lead += ", all trials: " + _text(", ".join(branch.prefix))
            markdown.append(lead + ", then splits:")
            for path in branch.paths:
                markdown.append(
                    f"  - {path.count} of {branch.total} trials: "
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
    ]
    markdown += _comparison_table(
        report, result.outcomes, "Outcome comparisons extracted from trial evidence"
    )
    if result.implications:
        markdown.append("### Model interpretation\n")
        markdown += [
            f"- {_text(claim.text)} {_decision_links(claim.decisions)}"
            for claim in result.implications
        ]
        markdown.append("")
    links = []
    if report.decisions.rows:
        links.append("[Compare decisions](#panel-decision)")
    links.append("[Inspect trial evidence](#panel-trials)")
    markdown += [
        " · ".join(links) + "\n",
        f"## {_text(content_data.behavior_heading)}\n",
        "Model interpretation of decision evidence. Counts describe each step, "
        "not complete paths through individual trials.\n",
    ]
    markdown += _comparison_table(
        report, result.behavior, "Per-step comparisons extracted from trial evidence"
    )
    if not result.behavior:
        markdown.append("No separate process comparison is available.\n")
    if report.decisions.fork_note and report.decisions.fork:
        markdown.append(
            "**Model interpretation:** "
            + _text(report.decisions.fork_note)
            + " "
            + _decision_links((report.decisions.fork,))
            + "\n"
        )
    markdown += [
        f"## {_text(content_data.scenario_heading)}\n",
        _text(content_data.scenario) + "\n",
    ]
    if content_data.expected:
        markdown += [
            f"## {_text(content_data.expected_heading)}\n",
            _text(content_data.expected) + "\n",
        ]
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
