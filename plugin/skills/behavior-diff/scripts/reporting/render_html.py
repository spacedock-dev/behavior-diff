"""Pure HTML renderers for Behavior Diff reports."""

import html

from reporting import content
from reporting.schema import ReportData


_RESULT_BACKGROUNDS = {
    "good": "var(--pass)",
    "bad": "var(--fail)",
    "neutral": "var(--accent)",
}


def _resolve_css(css: str, result_kind: str) -> str:
    if css.count("__RESULT_BG__") != 1:
        raise ValueError("report.css must contain __RESULT_BG__ exactly once")
    return css.replace("__RESULT_BG__", _RESULT_BACKGROUNDS[result_kind])


def _diff_line_class(line: str) -> str:
    if line.startswith("+"):
        return "d-add"
    if line.startswith("-"):
        return "d-del"
    return "d-ctx"


def _trial_card(trial, self_reported: bool, mode: str) -> str:
    escaped = html.escape
    verdict_class = escaped(trial.verdict.lower())
    if self_reported:
        evidence = "\n\n".join(trial.commands) or "(no self-reported actions)"
    else:
        evidence = "\n\n".join("$ " + command for command in trial.commands) or "(no commands)"
    actions = (
        ""
        if trial.actions == "-"
        else f'<p class="acts">{escaped(trial.actions)}</p>'
    )
    return (
        f'<article class="trial">'
        f'<p class="trial-head"><span class="badge {verdict_class}">{escaped(trial.verdict)}'
        f"</span><strong>{escaped(trial.name)}</strong></p>{actions}"
        f"<details><summary>{'self-reported actions' if self_reported else 'Commands the agent ran'} "
        f"({len(trial.commands)})</summary><pre>{escaped(evidence)}</pre></details>"
        f"<details {'open' if mode == 'review' else ''}>"
        f"<summary>Final answer to the user</summary>"
        f"<pre>{escaped(trial.final.strip())}</pre></details></article>"
    )


def _lane(steps, css_class: str) -> str:
    boxes = []
    for index, step in enumerate(steps):
        if index:
            boxes.append('<div class="farrow">↓</div>')
        boxes.append(f'<div class="fstep {css_class}"><span>{html.escape(step)}</span></div>')
    return "".join(boxes)


def _branch_html(prefix, paths, total: int, css_class: str) -> str:
    rendered = ""
    if not paths:
        body = _lane(prefix, css_class) or '<p class="fnote">(same steps as the shared flow)</p>'
        return f'<div class="fbranch"><p class="fpath-head">all {total} trials</p>{body}</div>'
    if prefix:
        rendered += f'<p class="fpath-head">all {total} trials</p>' + _lane(prefix, css_class)
        rendered += '<div class="farrow">↓</div>'
    rendered += f'<div class="fsplit">splits into {len(paths)} paths</div>'
    lanes = "".join(
        f'<div class="fpath"><p class="fpath-head">{path.count} of {total} trials</p>'
        f"{_lane(path.steps, css_class)}</div>"
        for path in paths
    )
    rendered += (
        f'<div class="fpaths" style="grid-template-columns:repeat({len(paths)},1fr)">'
        f"{lanes}</div>"
    )
    return f'<div class="fbranch">{rendered}</div>'


def _decision_choices(choices, total: int, css_class: str) -> str:
    lines = []
    for choice in choices:
        count = "" if choice.count == total else f' <span class="fcount">{choice.count}/{total}</span>'
        lines.append(f'<div class="dline">{html.escape(choice.choice)}{count}</div>')
    return f'<div class="fstep {css_class} dcell">' + ("".join(lines) or "—") + "</div>"


def _decision_label(index: int, row, fork: int | None) -> str:
    when = (
        '<span class="dwhen">in the final answer</span>'
        if row.anchor == "answer"
        else '<span class="dwhen">during the work</span>'
    )
    if index == fork:
        tag = '<span class="dtag">root change</span>'
    elif not row.diverges:
        tag = '<span class="dtag dtag-same">same</span>'
    elif fork and index > fork:
        tag = '<span class="dwhen">downstream</span>'
    else:
        tag = ""
    tag += when
    title = row.topic or row.decision
    subtitle = row.decision if row.topic else ""
    if row.note:
        subtitle = f"{subtitle} — {row.note}" if subtitle else row.note
    note = f'<span class="dnote">{html.escape(subtitle)}</span>' if subtitle else ""
    return f'<p class="dq dspan">{index} · {html.escape(title)}{tag}{note}</p>'


def render_artifact(report: ReportData, css: str) -> str:
    """Render a report body with its stylesheet inlined."""
    escaped = html.escape
    metadata = report.metadata
    report_content = report.content
    self_reported = metadata.trace_source == "self-reported"
    before = report.variants.before
    after = report.variants.after
    flow = report.command_flow
    before_total = flow.before.total
    after_total = flow.after.total
    decision_before_total = report.decisions.before_count
    decision_after_total = report.decisions.after_count

    columns = ""
    for label, variant in (("Before", before), ("After", after)):
        columns += (
            f'<section class="col"><header class="col-head"><h2>{label}</h2>'
            f'<span class="col-note">{escaped(variant.note)}</span></header>'
            f'<p class="count">{escaped(variant.count_text + variant.count_suffix)}</p>'
            + "".join(_trial_card(trial, self_reported, metadata.mode) for trial in variant.trials)
            + "</section>"
        )

    diff_html = "".join(
        f'<span class="{_diff_line_class(line)}">{escaped(line)}</span>\n'
        for line in report.rule_diff.rstrip().splitlines()
    )
    shared_html = "".join(
        f'<div class="fstep shared"><span>{escaped(step)}</span>'
        f'<span class="fcount">before {before_total}/{before_total} · after {after_total}/{after_total}</span></div>'
        f'<div class="fline"></div>'
        for step in flow.shared
    )
    if flow.same:
        flow_html = (
            f'<div class="flow">{shared_html}'
            f'<p class="fnote">Both variants used the same command '
            f"categories; the buckets are coarse, so their actual work "
            f"paths and depth may still differ — see the decision diff "
            f"and the trial cards.</p></div>"
        )
    else:
        flow_html = (
            f'<div class="flow">{shared_html}'
            f'<div class="fork-label">paths diverge here</div>'
            f'<div class="fork">'
            f'<div><p class="fork-side">BEFORE</p>'
            f"{_branch_html(flow.before.prefix, flow.before.paths, before_total, 'b')}</div>"
            f'<div><p class="fork-side">AFTER</p>'
            f"{_branch_html(flow.after.prefix, flow.after.paths, after_total, 'a')}</div>"
            f"</div></div>"
        )

    decisions_html = ""
    if report.decisions.rows:
        fork = report.decisions.fork
        lead_count = 0
        for row in report.decisions.rows:
            if row.diverges:
                break
            lead_count += 1
        parts = []
        for index, row in enumerate(report.decisions.rows[:lead_count], 1):
            before_choices = content.branch_text(row.before, decision_before_total)
            after_choices = content.branch_text(row.after, decision_after_total)
            choice = before_choices if before_choices == after_choices else f"before: {before_choices} · after: {after_choices}"
            parts.append(_decision_label(index, row, fork))
            parts.append(
                f'<div class="fstep shared"><span>{escaped(choice)}</span>'
                f'<span class="fcount">before {decision_before_total}/{decision_before_total} · '
                f"after {decision_after_total}/{decision_after_total}</span></div>"
            )
            parts.append('<div class="fline"></div>')
        rest = report.decisions.rows[lead_count:]
        if rest:
            parts.append('<div class="fork-label">paths diverge here</div>')
            grid = ['<p class="fork-side">BEFORE</p><p class="fork-side">AFTER</p>']
            for offset, row in enumerate(rest):
                index = lead_count + offset + 1
                if offset:
                    grid.append('<div class="farrow">↓</div><div class="farrow">↓</div>')
                grid.append(_decision_label(index, row, fork))
                if row.diverges:
                    grid.append(_decision_choices(row.before, decision_before_total, "b"))
                    grid.append(_decision_choices(row.after, decision_after_total, "a"))
                else:
                    grid.append(
                        '<div class="fstep shared dspan"><span>'
                        + escaped(content.branch_text(row.before, decision_before_total))
                        + "</span></div>"
                    )
            parts.append(f'<div class="dgrid">{"".join(grid)}</div>')
        footer = content.decision_footer(report.decisions.rows, fork)
        if report.decisions.fork_note:
            footer += " " + report.decisions.fork_note
        if report.decisions.dropped:
            footer += " " + content.dropped_rows(report.decisions.dropped)
        decisions_html = (
            f'<p class="section-label">{escaped(report_content.decision_heading)}</p>'
            f'<p class="sub">{escaped(report_content.decision_blurb)}</p>'
            f'<div class="flow">{"".join(parts)}</div>'
            f'<p class="fnote dfoot">{escaped(footer)}</p>'
        )

    flow_section = ""
    if not self_reported:
        flow_section = (
            f'<p class="section-label">{escaped(report_content.flow_heading)}</p>'
            + (
                '<p class="sub">Steps are described from the agents\' actual commands. '
                "A path is a sequence at least one trial literally took — arrows "
                "connect steps inside a path, and a split shows where trials went "
                "different ways. Full commands are in the trial cards below.</p>"
            )
            + flow_html
        )
        if decisions_html:
            flow_section = (
                '<details class="flowfold"><summary>'
                + content.flow_fold_summary()
                + "</summary>"
                + flow_section
                + "</details>"
            )

    observation_html = f'<p class="obs">{escaped(report_content.observation)}</p>' if report_content.observation else ""
    expected_html = (
        ""
        if not report_content.expected
        else (
            f'<p class="section-label">{escaped(report_content.expected_heading)}</p>'
            f'<p class="sub">{escaped(report_content.expected)}</p>'
        )
    )
    resolved_css = _resolve_css(css, report.result.kind)
    return f"""<title>{escaped(report_content.title)}</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
{resolved_css}</style>

<h1>{escaped(report_content.title)}</h1>
<p class="sub">{escaped(report_content.subtitle)}</p>
{observation_html}

<p class="section-label">{escaped(report_content.scenario_heading)}</p>
<pre class="scenario">{escaped(report_content.scenario)}</pre>
{expected_html}

<p class="section-label">{escaped(report_content.diff_heading)}</p>
<pre>{diff_html}</pre>

{decisions_html}

{flow_section}

<p class="section-label">Trials</p>
<div class="cols">{columns}</div>

<p class="section-label">{escaped(report_content.result_heading)}</p>
<div class="result">{escaped(report.result.text)}</div>

<p class="footer">Simulation evidence from Behavior Diff
(model: {escaped(metadata.model)}, {before.total} trial(s) per variant).
{escaped(report_content.boundary)}</p>
"""


def render_document(artifact: str) -> str:
    """Wrap an artifact body in a complete HTML document."""
    return (
        '<!doctype html><html><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        "</head><body>" + artifact + "</body></html>"
    )
