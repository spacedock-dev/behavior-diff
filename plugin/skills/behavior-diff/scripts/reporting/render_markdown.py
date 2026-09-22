"""Pure Markdown renderer for Behavior Diff reports."""

from reporting import content
from reporting.schema import ReportData


def _decision_markdown(report):
    decisions = report.decisions
    if not decisions.rows:
        return []

    before_total = decisions.before_count
    after_total = decisions.after_count
    lead_count = 0
    for row in decisions.rows:
        if row.diverges:
            break
        lead_count += 1

    legend = "\n".join(
        "- **{0}** — {1}".format(label, meaning)
        for _, label, meaning in report.content.tag_legend
    )
    markdown = [
        f"## {report.content.decision_heading}\n",
        report.content.decision_blurb + "\n",
        "Tags:\n",
        legend + "\n",
    ]
    if lead_count:
        markdown.append("Decided the same way on both sides:\n")
        for index, row in enumerate(decisions.rows[:lead_count], 1):
            before_choice = content.branch_text(row.before, before_total)
            after_choice = content.branch_text(row.after, after_total)
            choice = (
                before_choice
                if before_choice == after_choice
                else f"before: {before_choice} · after: {after_choice}"
            )
            note = f" — {row.note}" if row.note else ""
            when = (
                " *(from the reply)*"
                if row.anchor == "answer"
                else " *(from a command)*"
            )
            title = row.decision or row.topic
            markdown.append(f"- {index}. **{title}**{when} → {choice}{note}")
        markdown.append("")
    if lead_count < len(decisions.rows):
        markdown.append("Diverging from here:\n")
        for index, row in enumerate(decisions.rows[lead_count:], lead_count + 1):
            mark = (
                " *(first difference)*"
                if index == decisions.fork
                else (
                    " *(follows from it)*"
                    if row.diverges and decisions.fork and index > decisions.fork
                    else ""
                )
            )
            mark += (
                " *(from the reply)*"
                if row.anchor == "answer"
                else " *(from a command)*"
            )
            title = f"**{row.decision or row.topic}**"
            if row.diverges:
                markdown.append(f"- {index}. {title}{mark}")
                markdown.append(
                    f"  - BEFORE: {content.branch_text(row.before, before_total)}"
                )
                markdown.append(
                    f"  - AFTER: {content.branch_text(row.after, after_total)}"
                )
            else:
                markdown.append(
                    f"- {index}. {row.decision} *(same before and after)* → "
                    f"{content.branch_text(row.before, before_total)}"
                )
            if row.note:
                markdown.append(f"  - note: {row.note}")
        markdown.append("")
    markdown.append(content.decision_footer(decisions.rows, decisions.fork))
    if decisions.fork_note:
        markdown.append("\n" + decisions.fork_note)
    if decisions.dropped:
        markdown.append("\n" + content.dropped_rows(decisions.dropped))
    markdown.append("")
    return markdown


def _flow_markdown(report):
    flow = report.command_flow
    markdown = [
        f"## {report.content.flow_heading}\n",
        report.content.flow_purpose + "\n",
        content.flow_kinds_heading(flow.kinds) + "\n",
    ]
    markdown += [f"- {kind}" for kind in flow.kinds]
    markdown.append("")
    if flow.same:
        markdown.append(
            "Every trial on both sides used the same kinds of command: "
            + ", ".join(flow.shared)
            + ". Differences, if any, are in the final answers below.\n"
        )
    else:
        markdown.append("Used by every trial, both sides:\n")
        markdown.extend(f"- {step}" for step in flow.shared)
        markdown.append("\nUsed on only one side:\n")
        for tag, branch in (("BEFORE", flow.before), ("AFTER", flow.after)):
            if not branch.paths:
                markdown.append(
                    f"- {tag}, all {branch.total} trials: "
                    + (", ".join(branch.prefix) or "(no other kind of command)")
                )
                continue
            lead = f"- {tag}"
            if branch.prefix:
                lead += ", all trials: " + ", ".join(branch.prefix)
            markdown.append(lead + ", then splits:")
            for path in branch.paths:
                markdown.append(
                    f"  - {path.count} of {branch.total} trials: "
                    + (", ".join(path.steps) or "(no other kind of command)")
                )
    markdown.append("")
    return markdown


def _count_line(variant):
    count = (
        f"**{variant.count_text}**" if variant.count_emphasized else variant.count_text
    )
    return count + variant.count_suffix


def render_markdown(report: ReportData) -> str:
    """Return the complete Markdown report without accessing external state."""
    metadata = report.metadata
    content_data = report.content
    decisions = _decision_markdown(report)
    markdown = [f"# {content_data.title}\n", content_data.subtitle + "\n"]
    if content_data.note:
        markdown.append(content_data.note + "\n")
    if content_data.observation:
        markdown.append(f"## {content_data.observation_heading}\n")
        markdown.append("```\n" + content_data.observation + "\n```\n")
    markdown += [
        f"## {content_data.scenario_heading}\n",
        content_data.scenario + "\n",
    ]
    if content_data.expected:
        markdown += [
            f"## {content_data.expected_heading}\n",
            content_data.expected + "\n",
        ]
    markdown += [
        f"<details><summary>{content_data.diff_heading}</summary>\n",
        "```diff\n" + report.rule_diff.rstrip() + "\n```\n",
        "</details>\n",
    ]
    markdown += decisions
    if metadata.trace_source != "self-reported":
        flow = _flow_markdown(report)
        if decisions:
            markdown.append(
                "<details><summary>" + content.flow_fold_summary() + "</summary>\n"
            )
            markdown += flow
            markdown.append("</details>\n")
        else:
            markdown += flow
    for variant, label in (
        (report.variants.before, f"BEFORE — {metadata.before_label}"),
        (report.variants.after, f"AFTER — {metadata.after_label}"),
    ):
        markdown.append(f"## {label}\n")
        markdown.append(_count_line(variant) + "\n")
        for trial in variant.trials:
            markdown.append(f"### {trial.name} — {trial.verdict}\n")
            if trial.actions != "-":
                markdown.append(trial.actions + "\n")
            action_label = (
                "self-reported actions"
                if metadata.trace_source == "self-reported"
                else "commands the agent ran"
            )
            markdown.append(
                f"<details><summary>{action_label} ({len(trial.commands)})</summary>\n\n```\n"
                + "\n\n".join(command[:500] for command in trial.commands)
                + "\n```\n</details>\n"
            )
            markdown.append(
                "<details><summary>final answer to the user</summary>\n\n"
                + trial.final.strip()
                + "\n\n</details>\n"
            )
    markdown += [
        f"## {content_data.result_heading}\n",
        f"**{report.result.text}**\n",
        content_data.boundary + "\n",
    ]
    return "\n".join(markdown)
