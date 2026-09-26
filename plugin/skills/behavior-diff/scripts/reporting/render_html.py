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
    action_heading, empty_actions = content.trial_action_labels(self_reported)
    evidence = (
        "\n\n".join(
            command if self_reported else "$ " + command for command in trial.commands
        )
        or empty_actions
    )
    actions = (
        "" if trial.actions == "-" else f'<p class="acts">{escaped(trial.actions)}</p>'
    )
    return (
        f'<article class="trial" id="{escaped(content.trial_anchor(side, trial.name))}" tabindex="-1">'
        f'<p class="trial-head"><strong>{escaped(trial.name)}</strong>'
        f'<span class="badge {verdict_class}">{escaped(trial.verdict)}</span></p>{actions}'
        f"<details {'open' if mode == 'review' else ''}>"
        f"<summary>{escaped(action_heading)} "
        f"({len(trial.commands)})</summary><pre>{escaped(evidence)}</pre></details>"
        f"<details {'open' if mode == 'review' else ''}>"
        f"<summary>{escaped(content.FINAL_ANSWER_HEADING)}</summary>"
        f"<pre>{escaped(trial.final if trial.final.strip() else content.NO_FINAL_ANSWER)}</pre></details></article>"
    )


def _decision_choices(choices, total: int) -> str:
    lines = []
    for choice in choices:
        count = f'<span class="choice-count">{content.trial_count(choice.count, total)}</span>'
        lines.append(f'<div class="dline">{html.escape(choice.choice)}{count}</div>')
    return "".join(lines) or html.escape(content.NO_EXTRACTED_CHOICE)


def _decision_progression(report) -> str:
    decisions = report.decisions
    nodes = []
    for index, row in enumerate(decisions.rows, 1):
        status = content.decision_status(row)
        role = content.decision_role(index, row, decisions.outcome)
        title = row.topic.strip() or row.decision
        source = content.source_label(row.anchor, report.metadata.trace_source)
        final_class = " progression-final" if index == decisions.outcome else ""
        preview = ""
        if status == "Changed" or index == decisions.outcome:
            preview = (
                '<span class="progression-preview">'
                + "".join(
                    f'<span><span class="preview-label">{label}</span>'
                    f"{html.escape(content.decision_choices_preview(choices, total))}</span>"
                    for label, choices, total in (
                        ("Before", row.before, decisions.before_count),
                        ("After", row.after, decisions.after_count),
                    )
                )
                + "</span>"
            )
        question = (
            f'<p class="decision-question">{html.escape(row.decision)}</p>'
            if row.decision and row.decision != title
            else ""
        )
        note = f'<p class="dnote">{html.escape(row.note)}</p>' if row.note else ""
        nodes.append(
            f'<li><details class="decision-row decision-{status.lower()}{final_class}" '
            f'id="decision-{index}">'
            '<summary class="decision-node">'
            f'<span class="progression-number">{index}</span>'
            '<span class="progression-heading">'
            f'<span class="progression-topic">{html.escape(title)}</span>'
            f'<strong class="decision-status">{html.escape(status)}</strong>'
            f'<span class="progression-role">{html.escape(role)}</span></span>'
            '<span class="decision-disclosure"><span class="hint-show">Show evidence</span>'
            f'<span class="hint-hide">Hide evidence</span>{_CHEVRON}</span>'
            f"{preview}</summary>"
            f'<div class="decision-evidence">{question}'
            f'<p class="decision-meta">{html.escape(source)}</p>'
            '<table class="comparison decision-comparison">'
            f'<caption class="visually-hidden">Decision {index}: {html.escape(title)}</caption>'
            '<thead><tr><th scope="col">Before</th>'
            '<th scope="col">After</th></tr></thead><tbody><tr>'
            f"<td>{_decision_choices(row.before, decisions.before_count)}</td>"
            f"<td>{_decision_choices(row.after, decisions.after_count)}</td>"
            f"</tr></tbody></table>{note}"
            '<a class="decision-evidence-link" href="#panel-trials">Inspect trial evidence</a>'
            "</div></details></li>"
        )
    return (
        '<section class="progression" id="decision-progression" tabindex="-1" aria-labelledby="decision-progression-heading">'
        '<div class="decision-toolbar">'
        '<h2 class="comparison-heading" id="decision-progression-heading">Decision comparisons</h2>'
        '<button type="button" class="decision-toggle" id="decision-toggle" aria-controls="decision-list" hidden>Expand all</button></div>'
        f'<p class="note" id="decision-progression-note">{html.escape(content.DECISION_PROGRESSION_NOTE)}</p>'
        f'<p class="note">{html.escape(content.TRIAL_COUNT_NOTE)}</p>'
        '<ol class="decision-path" id="decision-list" role="list" aria-describedby="decision-progression-note">'
        f"{''.join(nodes)}</ol></section>"
    )


_REPORT_INTERACTIONS = """<script>
(() => {
  let printState = null;
  window.addEventListener("beforeprint", () => {
    if (printState !== null) return;
    printState = [...document.querySelectorAll("details")].map(row => [row, row.open]);
    printState.forEach(([row]) => { row.open = true; });
  });
  window.addEventListener("afterprint", () => {
    if (printState === null) return;
    printState.forEach(([row, open]) => { row.open = open; });
    printState = null;
  });
  const list = document.getElementById("decision-list");
  const button = document.getElementById("decision-toggle");
  if (!list || !button) return;
  const rows = [...list.querySelectorAll(".decision-row")];
  const updateButton = () => {
    button.textContent = rows.every(row => row.open) ? "Collapse all" : "Expand all";
  };
  button.hidden = false;
  button.addEventListener("click", () => {
    const expand = !rows.every(row => row.open);
    rows.forEach(row => { row.open = expand; });
    updateButton();
  });
  list.addEventListener("toggle", updateButton, true);
  const openLinkedDecision = () => {
    const row = document.getElementById(location.hash.slice(1));
    if (!row || !row.matches(".decision-row")) return;
    row.open = true;
    row.querySelector("summary").focus({preventScroll: true});
    row.scrollIntoView({block: "start"});
    updateButton();
  };
  window.addEventListener("hashchange", openLinkedDecision);
  document.addEventListener("click", event => {
    if (event.defaultPrevented || event.button !== 0 ||
        event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
    const link = event.target.closest('a[href^="#decision-"]');
    if (link && link.getAttribute("href") === location.hash) openLinkedDecision();
  });
  openLinkedDecision();
})();
</script>"""


def _flow_lane(variant, side: str, label: str) -> str:
    paths = []
    for index, (commands, members) in enumerate(
        content.command_progressions(variant), 1
    ):
        evidence = "".join(
            f'<li><a href="#{html.escape(content.trial_anchor(side, trial.name))}">'
            f"{html.escape(trial.name)}"
            f' <span class="progression-verdict">({html.escape(trial.verdict)})</span></a></li>'
            for trial in members
        )
        steps = "".join(
            '<li class="command-step">'
            f'<span class="progression-number">{step}</span>'
            f"<pre><code>{html.escape(command)}</code></pre></li>"
            for step, command in enumerate(commands, 1)
        )
        sequence = (
            f'<ol class="command-path" role="list" aria-label="Recorded command order">{steps}</ol>'
            if commands
            else f'<p class="note">{html.escape(content.NO_COMMANDS_RECORDED)}</p>'
        )
        paths.append(
            '<article class="command-group">'
            f'<h4>Path {index} <span class="path-count">'
            f"{html.escape(content.trial_count(len(members), variant.total))}</span></h4>"
            f'<ul class="path-evidence" aria-label="{html.escape(content.TRIAL_EVIDENCE_HEADING)}">{evidence}</ul>'
            f"{sequence}</article>"
        )
    body = "".join(paths) or '<p class="note">No trials</p>'
    return (
        f'<section class="flow-lane" aria-labelledby="flow-{side}-heading">'
        f'<h3 id="flow-{side}-heading">{html.escape(label)}</h3>{body}</section>'
    )


def _comparison_table(report: ReportData, indexes, column: str, count_note: str) -> str:
    if not indexes:
        return ""
    rows = []
    for index in indexes:
        row = report.decisions.rows[index - 1]
        source = content.source_label(row.anchor, report.metadata.trace_source)
        rows.append(
            f'<tr><th scope="row"><a href="#decision-{index}">'
            f"{html.escape(row.topic.strip() or row.decision)}</a>"
            f'<span class="dnote">{html.escape(source)}</span></th>'
            f"<td>{_decision_choices(row.before, report.decisions.before_count)}</td>"
            f"<td>{_decision_choices(row.after, report.decisions.after_count)}</td></tr>"
        )
    return (
        '<div class="comparison-wrap"><table class="comparison">'
        f"<caption>{html.escape(count_note)}</caption>"
        f'<thead><tr><th scope="col">{html.escape(column)}</th>'
        '<th scope="col">Before</th><th scope="col">After</th></tr></thead>'
        f"<tbody>{''.join(rows)}</tbody></table></div>"
    )


def _decision_links(indexes) -> str:
    return " · ".join(
        f'<a href="#decision-{index}">Decision {index}</a>' for index in indexes
    )


def _tag_legend(legend) -> str:
    items = "".join(
        f'<span><span class="decision-tag">{html.escape(label)}</span>'
        f"{html.escape(meaning)}</span>"
        for _, label, meaning in legend
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

    before_note = f'<span class="col-note">{escaped(before.note)}</span>'
    after_note = f'<span class="col-note">{escaped(after.note)}</span>'
    runs = ""
    for index, (before_trial, after_trial) in enumerate(
        zip_longest(before.trials, after.trials), 1
    ):
        halves = ""
        for trial, css_class in ((before_trial, "b"), (after_trial, "a")):
            side = "before" if css_class == "b" else "after"
            body = (
                _trial_card(trial, self_reported, metadata.mode, side)
                if trial
                else '<p class="fnote">(no trial on this side)</p>'
            )
            halves += (
                f'<div class="half {css_class}">'
                f'<p class="trial-side">{side.capitalize()}</p>{body}</div>'
            )
        runs += f'<article class="run"><p class="run-label">Trial {index}</p>{halves}</article>'
    trials_html = (
        f'<p class="section-label">{escaped(content.TRIAL_EVIDENCE_HEADING)}</p>'
        f'<p class="sub">{escaped(content.trial_evidence_note(self_reported))}</p>'
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

    decisions_html = ""
    if report.decisions.rows:
        decisions = report.decisions
        footer = content.decision_footer(decisions.rows)
        if decisions.dropped:
            footer += " " + content.dropped_rows(decisions.dropped)
        explanation = ""
        if decisions.implications or decisions.fork_note:
            explanation = (
                '<div class="interpretation"><h3>Model explanations</h3>'
                f'<p class="interpretation-note">{escaped(content.INTERPRETATION_NOTE)}</p><ul>'
            )
            explanation += "".join(
                f"<li>{escaped(claim.text)}"
                f'<span class="evidence-links">{_decision_links(claim.decisions)}</span></li>'
                for claim in decisions.implications
            )
            if decisions.fork_note:
                fork_link = _decision_links((decisions.fork,)) if decisions.fork else ""
                explanation += (
                    f"<li>{escaped(decisions.fork_note)}"
                    f'<span class="evidence-links">{fork_link}</span></li>'
                )
            explanation += "</ul></div>"
        limitation = (
            f'<p class="note">{escaped(content.SELF_REPORTED_LIMIT)}</p>'
            if self_reported
            else ""
        )
        decisions_html = (
            f'<div class="section-label">{escaped(report_content.decision_heading)}'
            f"{_info('pop-decision', 'Decision labels', _tag_legend(report_content.tag_legend))}</div>"
            f'<p class="tab-overview">{escaped(content.decision_overview(report))}</p>'
            f'<p class="sub">{escaped(report_content.decision_blurb)}</p>'
            f"{limitation}"
            f"{_decision_progression(report)}"
            f'<p class="note">{escaped(footer)}</p>{explanation}'
            '<nav class="evidence-nav" aria-label="Decision evidence">'
            '<a href="#panel-trials">Inspect trial evidence</a></nav>'
        )

    flow_section = ""
    if not self_reported:
        patterns = content.flow_patterns(flow)
        pattern_rows = []
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
            pattern_rows.append(
                f'<tr><th scope="row">{escaped(label)}</th>'
                f"<td>{escaped(before_count_text)}</td>"
                f"<td>{escaped(after_count_text)}</td></tr>"
            )
        flow_html = (
            '<div class="comparison-wrap"><table class="comparison">'
            f"<caption>{escaped(content.FLOW_COUNT_NOTE)}</caption>"
            '<thead><tr><th scope="col">Command-category combination</th>'
            '<th scope="col">Before</th><th scope="col">After</th></tr></thead>'
            f"<tbody>{''.join(pattern_rows)}</tbody></table></div>"
            if patterns
            else '<p class="note">No recorded command-category combinations are available.</p>'
        )
        kinds_html = (
            '<ul class="kinds">'
            + "".join(f"<li>{escaped(kind)}</li>" for kind in flow.kinds)
            + "</ul>"
        )
        flow_links = (
            '<a href="#panel-decision">Compare decisions</a>'
            if report.decisions.rows
            else ""
        )
        flow_section = (
            f'<div class="section-label">{escaped(report_content.flow_heading)}'
            f"{_info('pop-flow', content.flow_kinds_heading(flow.kinds).rstrip(':'), kinds_html)}</div>"
            '<section class="progression" id="flow-progression" tabindex="-1" aria-labelledby="flow-progression-heading">'
            '<h2 class="comparison-heading" id="flow-progression-heading">Flow progression</h2>'
            f'<p class="note">{escaped(content.FLOW_PROGRESSION_NOTE)}</p>'
            '<div class="flow-lanes">'
            f"{_flow_lane(before, 'before', 'Before')}"
            f"{_flow_lane(after, 'after', 'After')}</div></section>"
            '<h2 class="comparison-heading">Command-category comparison</h2>'
            f'<p class="tab-overview">{escaped(content.flow_overview(flow, patterns))}</p>'
            f'<p class="sub">{escaped(report_content.flow_purpose)}</p>{flow_html}'
            '<nav class="evidence-nav" aria-label="Command evidence">'
            f'{flow_links}<a href="#panel-trials">Inspect trial evidence</a></nav>'
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
        report,
        result.outcomes,
        "Final result" if report.decisions.outcome is not None else "Answer detail",
        content.TRIAL_COUNT_NOTE,
    )
    if not result.outcomes:
        outcomes_html = (
            '<p class="sub">No result or reported-answer comparison is available.</p>'
        )
    claims_html = ""
    if result.implications or report.decisions.fork_note:
        claims_html = (
            '<div class="interpretation"><h3>Model explanations</h3>'
            f'<p class="interpretation-note">{escaped(content.INTERPRETATION_NOTE)}</p><ul>'
        )
        claims_html += "".join(
            f"<li>{escaped(claim.text)} "
            f'<span class="evidence-links">{_decision_links(claim.decisions)}</span></li>'
            for claim in result.implications
        )
        if report.decisions.fork_note:
            fork_link = (
                _decision_links((report.decisions.fork,))
                if report.decisions.fork
                else ""
            )
            claims_html += (
                f"<li>{escaped(report.decisions.fork_note)}"
                f'<span class="evidence-links">{fork_link}</span></li>'
            )
        claims_html += "</ul></div>"
    evidence_links = (
        '<a href="#panel-decision">Compare decisions</a>'
        if report.decisions.rows
        else ""
    )
    evidence_links += '<a href="#panel-trials">Inspect trial evidence</a>'
    behavior_html = _comparison_table(
        report, result.behavior, "Action or check", content.BEHAVIOR_COUNT_NOTE
    )
    if not result.behavior:
        behavior_html = '<p class="sub">No separate action comparison is available.</p>'
    limits_html = "".join(f"<li>{escaped(limit)}</li>" for limit in result.limits)
    summary_html = f"""<h2 class="section-label">{escaped(report_content.result_heading)}</h2>
<p class="result">{escaped(result.text)}</p>
<p class="result-summary">{escaped(result.summary)}</p>
<h2 class="section-label">{escaped(report_content.scenario_heading)}</h2>
<pre class="scenario">{escaped(report_content.scenario)}</pre>
{expected_html}
<h2 class="comparison-heading">{escaped(result.outcome_heading)}</h2>
{outcomes_html}
<h2 class="comparison-heading">{escaped(result.behavior_heading)}</h2>
{behavior_html}
{claims_html}
<nav class="evidence-nav" aria-label="Supporting evidence">{evidence_links}</nav>
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
        (
            "trials",
            content.TRIAL_EVIDENCE_HEADING,
            f"{before.total} + {after.total} trials",
            trials_html,
        )
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
{_REPORT_INTERACTIONS}

<p class="footer">Simulation evidence from Behavior Diff
(model: {escaped(metadata.model)}, before: {before.total} {content.trial_noun(before.total)}, after: {after.total} {content.trial_noun(after.total)}).</p>
"""


def render_document(artifact: str) -> str:
    """Wrap an artifact body in a complete HTML document."""
    return (
        '<!doctype html><html><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        "</head><body>" + artifact + "</body></html>"
    )
