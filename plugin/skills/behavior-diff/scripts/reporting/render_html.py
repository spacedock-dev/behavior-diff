"""Pure HTML renderers for Behavior Diff reports."""

import html
from itertools import zip_longest

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
    if result_kind not in _RESULT_BACKGROUNDS:
        raise ValueError("unsupported report result kind: {0}".format(result_kind))
    return css.replace("__RESULT_BG__", _RESULT_BACKGROUNDS[result_kind])


def _diff_line_class(line: str) -> str:
    if line.startswith("+"):
        return "d-add"
    if line.startswith("-"):
        return "d-del"
    return "d-ctx"


def _trial_card(trial, self_reported: bool, mode: str, side: str) -> str:
    escaped = html.escape
    verdict_class = escaped(trial.verdict.lower())
    if self_reported:
        evidence = "\n\n".join(trial.commands) or "(no self-reported actions)"
    else:
        evidence = (
            "\n\n".join("$ " + command for command in trial.commands) or "(no commands)"
        )
    actions = (
        "" if trial.actions == "-" else f'<p class="acts">{escaped(trial.actions)}</p>'
    )
    return (
        f'<article class="trial" id="trial-{side}-{trial.name.encode("utf-8").hex()}" tabindex="-1">'
        f'<p class="trial-head"><strong>{escaped(trial.name)}</strong>'
        f'<span class="badge {verdict_class}">{escaped(trial.verdict)}</span></p>{actions}'
        f"<details {'open' if mode == 'review' else ''}>"
        f"<summary>{'self-reported actions' if self_reported else 'Commands the agent ran'} "
        f"({len(trial.commands)})</summary><pre>{escaped(evidence)}</pre></details>"
        f"<details {'open' if mode == 'review' else ''}>"
        f"<summary>Final answer to the user</summary>"
        f"<pre>{escaped(trial.final.strip())}</pre></details></article>"
    )


_NO_EXTRA_STEPS = '<p class="fnote">(no other kind of command)</p>'


def _lane(steps, css_class: str) -> str:
    # No arrows between steps: the order here is the report's fixed listing
    # order, not the order the agent ran the commands in.
    return "".join(
        f'<div class="fstep {css_class}"><span>{html.escape(step)}</span></div>'
        for step in steps
    )


def _branch_html(prefix, paths, total: int, css_class: str) -> str:
    rendered = ""
    if not paths:
        body = (
            _lane(prefix, css_class)
            or '<p class="fnote">(same steps as the shared flow)</p>'
        )
        return f'<div class="fbranch"><p class="fpath-head">all {total} trials</p>{body}</div>'
    if prefix:
        rendered += f'<p class="fpath-head">all {total} trials</p>' + _lane(
            prefix, css_class
        )
        rendered += '<div class="farrow">↓</div>'
    rendered += f'<div class="fsplit">{len(paths)} groups of trials</div>'
    lanes = "".join(
        f'<div class="fpath"><p class="fpath-head">{path.count} of {total} trials</p>'
        f"{_lane(path.steps, css_class) or _NO_EXTRA_STEPS}</div>"
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
        count = f' <span class="fcount">{choice.count}/{total}</span>'
        lines.append(f'<div class="dline">{html.escape(choice.choice)}{count}</div>')
    return f'<div class="fstep {css_class} dcell">' + ("".join(lines) or "—") + "</div>"


def _decision_label(index: int, row, fork: int | None, trace_source: str) -> str:
    if index == fork:
        tags = '<span class="dtag">first difference</span>'
    elif not row.diverges:
        tags = '<span class="dtag dtag-same">same before and after</span>'
    elif fork and index > fork:
        tags = '<span class="dtag dtag-down">follows from it</span>'
    else:
        tags = ""
    tags += (
        f'<span class="dtag dtag-src">'
        f"{content.source_label(row.anchor, trace_source)}</span>"
    )
    # The question is what the reader scans; the topic only renames it.
    title = row.decision or row.topic
    note = f'<span class="dnote">{html.escape(row.note)}</span>' if row.note else ""
    return (
        f'<p class="dq dspan" id="decision-{index}" tabindex="-1">'
        f"{index} · {html.escape(title)}{tags}{note}</p>"
    )


_TAG_CLASS = {
    "root": "dtag",
    "down": "dtag dtag-down",
    "same": "dtag dtag-same",
    "cmd": "dtag dtag-src",
    "ans": "dtag dtag-src",
}


def _comparison_table(report: ReportData, indexes, caption: str) -> str:
    if not indexes:
        return ""
    rows = []
    for index in indexes:
        row = report.decisions.rows[index - 1]
        source = content.source_label(row.anchor, report.metadata.trace_source)
        rows.append(
            f'<tr><th scope="row"><a href="#decision-{index}">'
            f"{index} · {html.escape(row.decision or row.topic)}</a>"
            f'<span class="dnote">{source}</span></th>'
            f"<td>{_decision_choices(row.before, report.decisions.before_count, '')}</td>"
            f"<td>{_decision_choices(row.after, report.decisions.after_count, '')}</td></tr>"
        )
    return (
        '<div class="comparison-wrap"><table class="comparison">'
        f"<caption>{html.escape(caption)}</caption>"
        '<thead><tr><th scope="col">Decision evidence</th>'
        '<th scope="col">Before</th><th scope="col">After</th></tr></thead>'
        f"<tbody>{''.join(rows)}</tbody></table></div>"
    )


def _decision_links(indexes) -> str:
    return " · ".join(
        f'<a href="#decision-{index}">Decision {index}</a>' for index in indexes
    )


def _tag_legend(legend) -> str:
    items = "".join(
        f'<span><span class="{_TAG_CLASS[kind]} dtag-key">{html.escape(label)}</span>'
        f"{html.escape(meaning)}</span>"
        for kind, label, meaning in legend
    )
    return f'<div class="legend">{items}</div>'


_INFO_ICON = (
    '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" '
    'stroke="currentColor" stroke-width="2.2" stroke-linecap="round" '
    'aria-hidden="true"><circle cx="12" cy="12" r="10"></circle>'
    '<line x1="12" y1="11" x2="12" y2="17"></line>'
    '<line x1="12" y1="7.5" x2="12" y2="7.6"></line></svg>'
)


def _info(pop_id: str, label: str, body: str) -> str:
    """An info icon whose popover opens on hover, focus, or tap."""
    return (
        f'<div class="info"><button type="button" aria-label="{html.escape(label)}" '
        f'aria-describedby="{pop_id}">{_INFO_ICON}</button>'
        f'<div class="pop" id="{pop_id}" role="note">'
        f'<p class="pop-title">{html.escape(label)}</p>{body}</div></div>'
    )


_CHEVRON = (
    '<svg class="chev" width="14" height="14" viewBox="0 0 24 24" fill="none" '
    'stroke="currentColor" stroke-width="2.5" stroke-linecap="round" '
    'stroke-linejoin="round" aria-hidden="true">'
    '<polyline points="9 6 15 12 9 18"></polyline></svg>'
)


def _diff_stats(diff: str) -> str:
    # Only the file header sits before the first hunk; a content line that
    # starts with "---" or "+++" must still count.
    lines = diff.rstrip().splitlines()
    start = next(
        (i for i, line in enumerate(lines) if line.startswith("@@")), len(lines)
    )
    body = lines[start:]
    added = sum(line.startswith("+") for line in body)
    removed = sum(line.startswith("-") for line in body)
    return f"+{added} −{removed} lines"


def _tabs(tabs) -> str:
    """Fragment-driven views also reveal evidence inside a hidden panel."""
    labels = "".join(
        f'<a href="#panel-{tab_id}">{html.escape(label)}'
        + (f'<span class="tab-count">{html.escape(count)}</span>' if count else "")
        + "</a>"
        for tab_id, label, count, _ in tabs
    )
    panels = "".join(
        f'<section class="panel" id="panel-{tab_id}" tabindex="-1" '
        f'aria-label="{html.escape(label)}">{panel}</section>'
        for tab_id, label, _, panel in tabs
    )
    return (
        f'<div class="tabs"><nav class="tabbar" aria-label="Report views">'
        f"{labels}</nav>{panels}</div>"
    )


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

    before_note = f'<span class="col-note">{escaped(before.note)}</span>'
    after_note = f'<span class="col-note">{escaped(after.note)}</span>'
    runs = ""
    for index, (before_trial, after_trial) in enumerate(
        zip_longest(before.trials, after.trials), 1
    ):
        halves = ""
        for trial, css_class in ((before_trial, "b"), (after_trial, "a")):
            body = (
                _trial_card(
                    trial,
                    self_reported,
                    metadata.mode,
                    "before" if css_class == "b" else "after",
                )
                if trial
                else '<p class="fnote">(no trial on this side)</p>'
            )
            halves += f'<div class="half {css_class}">{body}</div>'
        runs += f'<article class="run"><p class="run-label">Run {index}</p>{halves}</article>'
    trials_html = (
        f'<p class="section-label">Trials result: what each agent ran and answered</p>'
        f'<p class="sub">Raw evidence, one card per run. Each run is an independent '
        f"trial. Rows pair runs by number so before and after sit side by side; "
        f"run 1 before is not the same run as run 1 after.</p>"
        f'<div class="run run-head"><span></span>'
        f'<div class="half-head b"><h2>Before</h2>{before_note}'
        f'<span class="count">{escaped(before.count_text + before.count_suffix)}</span></div>'
        f'<div class="half-head a"><h2>After</h2>{after_note}'
        f'<span class="count">{escaped(after.count_text + after.count_suffix)}</span></div>'
        f"</div>{runs}"
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
            f'<p class="fnote">Both sides used the same kinds of command. '
            f"The kinds are coarse, so the actual work can still differ: "
            f"see the decision diff and the trial cards.</p></div>"
        )
    else:
        flow_html = (
            f'<div class="flow">{shared_html}'
            f'<div class="fork-label">kinds used on only one side</div>'
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
        parts = ['<div class="dgrid">']
        for index, row in enumerate(report.decisions.rows, 1):
            parts.append(_decision_label(index, row, fork, metadata.trace_source))
            parts.append(
                '<div><p class="fork-side">Before</p>'
                + _decision_choices(row.before, decision_before_total, "b")
                + "</div>"
            )
            parts.append(
                '<div><p class="fork-side">After</p>'
                + _decision_choices(row.after, decision_after_total, "a")
                + "</div>"
            )
        parts.append("</div>")
        footer = content.decision_footer(report.decisions.rows, fork)
        if report.decisions.fork_note:
            footer += " Model interpretation: " + report.decisions.fork_note
        if report.decisions.dropped:
            footer += " " + content.dropped_rows(report.decisions.dropped)
        decisions_html = (
            f'<div class="section-label">{escaped(report_content.decision_heading)}'
            f"{_info('pop-decision', 'What the tags on each decision mean', _tag_legend(report_content.tag_legend))}</div>"
            f'<p class="sub">{escaped(report_content.decision_blurb)}</p>'
            f'<div class="flow">{"".join(parts)}</div>'
            f'<p class="fnote dfoot">{escaped(footer)}</p>'
        )

    flow_section = ""
    if not self_reported:
        kinds_html = (
            '<ul class="kinds">'
            + "".join(f"<li>{escaped(kind)}</li>" for kind in flow.kinds)
            + "</ul>"
        )
        flow_section = (
            f'<div class="section-label">{escaped(content.flow_fold_summary())}'
            f"{_info('pop-flow', content.flow_kinds_heading(flow.kinds).rstrip(':'), kinds_html)}</div>"
            + f'<p class="sub">{escaped(report_content.flow_purpose)}</p>'
            + flow_html
        )

    expected_html = (
        ""
        if not report_content.expected
        else (
            f'<p class="section-label">{escaped(report_content.expected_heading)}</p>'
            f'<p class="sub">{escaped(report_content.expected)}</p>'
        )
    )
    note_html = (
        f'<p class="note">{escaped(report_content.note)}</p>'
        if report_content.note
        else ""
    )
    meta_html = (
        '<p class="meta">'
        + "".join(
            f"<span><b>{escaped(label)}</b>{escaped(value)}</span>"
            for label, value in report_content.meta
        )
        + "</p>"
    )
    result = report.result
    outcomes_html = _comparison_table(
        report, result.outcomes, "Outcome comparisons extracted from trial evidence"
    )
    claims_html = ""
    if result.implications:
        claims_html = '<div class="interpretation"><h3>Model interpretation</h3><ul>'
        claims_html += "".join(
            f"<li>{escaped(claim.text)} "
            f'<span class="evidence-links">{_decision_links(claim.decisions)}</span></li>'
            for claim in result.implications
        )
        claims_html += "</ul></div>"
    evidence_links = (
        '<a href="#panel-decision">Compare decisions</a>'
        if report.decisions.rows
        else ""
    )
    evidence_links += '<a href="#panel-trials">Inspect trial evidence</a>'
    behavior_html = _comparison_table(
        report, result.behavior, "Per-step comparisons extracted from trial evidence"
    )
    if not result.behavior:
        behavior_html = (
            '<p class="sub">No separate process comparison is available.</p>'
        )
    if report.decisions.fork_note and report.decisions.fork:
        behavior_html += (
            '<p class="interpretation"><strong>Model interpretation:</strong> '
            f"{escaped(report.decisions.fork_note)} "
            f"{_decision_links((report.decisions.fork,))}</p>"
        )
    limits_html = "".join(f"<li>{escaped(limit)}</li>" for limit in result.limits)
    summary_html = f"""<h2 class="section-label">{escaped(report_content.result_heading)}</h2>
<p class="result">{escaped(result.text)}</p>
<p class="result-summary">{escaped(result.summary)}</p>
{outcomes_html}
{claims_html}
<nav class="evidence-nav" aria-label="Supporting evidence">{evidence_links}</nav>
<h2 class="section-label">{escaped(report_content.behavior_heading)}</h2>
<p class="sub">Model interpretation of decision evidence. Counts describe each step, not complete paths through individual trials.</p>
{behavior_html}
<h2 class="section-label">{escaped(report_content.scenario_heading)}</h2>
<pre class="scenario">{escaped(report_content.scenario)}</pre>
{expected_html}
<details class="fold"><summary>{_CHEVRON}{escaped(report_content.diff_heading)}
<span class="fold-stat">{_diff_stats(report.rule_diff)}</span>
<span class="fold-hint"><span class="hint-show">Show the diff</span><span class="hint-hide">Hide the diff</span></span></summary>
<pre>{diff_html}</pre></details>
<h2 class="section-label">{escaped(report_content.limits_heading)}</h2>
<ul class="evidence-limits">{limits_html}</ul>"""

    tabs = [("summary", "Summary", "", summary_html)]
    if decisions_html:
        tabs.append(
            (
                "decision",
                "Decision diff",
                f"{len(report.decisions.rows)} decision{'s' if len(report.decisions.rows) != 1 else ''}",
                decisions_html,
            )
        )
    if flow_section:
        tabs.append(("flow", "Flow diff", "", flow_section))
    tabs.append(
        ("trials", "Trials result", f"{before.total} + {after.total}", trials_html)
    )

    resolved_css = _resolve_css(css, report.result.kind)
    return f"""<title>{escaped(report_content.title)}</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
{resolved_css}</style>

<h1>{escaped(report_content.title)}</h1>
{meta_html}
{note_html}

{_tabs(tabs)}

<p class="footer">Simulation evidence from Behavior Diff
(model: {escaped(metadata.model)}, before: {before.total} trial(s), after: {after.total} trial(s)).</p>
"""


def render_document(artifact: str) -> str:
    """Wrap an artifact body in a complete HTML document."""
    return (
        '<!doctype html><html><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        "</head><body>" + artifact + "</body></html>"
    )
