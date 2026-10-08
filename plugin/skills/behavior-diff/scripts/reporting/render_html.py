"""Pure HTML renderers for Behavior Diff reports."""

import html
from itertools import zip_longest

from reporting import content
from reporting.attention import AttentionFindingData
from reporting.illustrations import illustration
from reporting.instruction import parse_diff_hunks
from reporting.schema import ReportData
from reporting.summary import question_distribution, question_distribution_changed
from reporting.target import (
    UNAVAILABLE,
    acceptance,
    evidence_limit_text,
)


def _diff_line_class(line: str) -> str:
    if line.startswith("+"):
        return "d-add"
    if line.startswith("-"):
        return "d-del"
    return "d-ctx"


def _trial_cell(trial, side: str, body: str, *, anchor: bool = False) -> str:
    identity = (
        f' id="{html.escape(content.trial_anchor(side, trial.name))}" tabindex="-1"'
        if trial and anchor
        else ""
    )
    if not trial:
        body = '<p class="note">No trial record on this side.</p>'
    return (
        f'<div class="trial-cell {side} {"b" if side == "before" else "a"}'
        f'{" trial" if anchor else ""}{" trial-missing" if not trial else ""}"{identity}>'
        f"{body}"
        "</div>"
    )


def _trial_group(index, before, after, self_reported: bool, mode: str, summary) -> str:
    escaped = html.escape
    trials = (("before", before), ("after", after))
    metadata = []
    answers = []
    actions = []
    commands = []
    action_heading, empty_actions = content.trial_action_labels(self_reported)
    for side, trial in trials:
        if trial:
            header = (
                f'<p class="trial-head"><strong>{escaped(trial.name)}</strong>'
                f'<span class="badge {escaped(trial.verdict.lower())}">'
                f"{escaped(trial.verdict)}</span></p>"
            )
            answer = (
                f"<pre>{escaped(trial.final)}</pre>"
                if trial.final.strip()
                else f'<p class="note">{escaped(content.NO_FINAL_ANSWER)}</p>'
            )
            action = (
                f'<p class="acts">{escaped(trial.actions)}</p>'
                if trial.actions and trial.actions != "-"
                else '<p class="note">No action summary recorded.</p>'
            )
            evidence = (
                "\n\n".join(
                    command if self_reported else "$ " + command
                    for command in trial.commands
                )
                or empty_actions
            )
            command_body = (
                f'<p class="note">{len(trial.commands)} '
                f"{'self-reported actions' if self_reported else 'recorded commands'}</p>"
                f"<pre>{escaped(evidence)}</pre>"
            )
        else:
            header = answer = action = command_body = ""
        metadata.append(_trial_cell(trial, side, header, anchor=True))
        answers.append(
            _trial_cell(
                trial,
                side,
                f'<section class="trial-answer" aria-label="{side.capitalize()} final answer">{answer}</section>',
            )
        )
        actions.append(_trial_cell(trial, side, action))
        commands.append(_trial_cell(trial, side, command_body))
    summary_intro = (
        f'<p class="trial-change-takeaway">{escaped(summary.takeaway)}</p>'
        if summary is not None
        else f'<p class="note trial-change-unavailable">{escaped(content.TRIAL_SUMMARY_UNAVAILABLE)}</p>'
    )
    descriptions = (
        "".join(
            _trial_cell(
                trial,
                side,
                f'<p class="trial-change-description">{escaped(sentence)}</p>',
            )
            for (side, trial), sentence in zip(trials, (summary.before, summary.after))
        )
        if summary is not None
        else ""
    )
    caveat = (
        f'<p class="note trial-change-caveat">{escaped(summary.caveat)}</p>'
        if summary is not None and summary.caveat
        else ""
    )
    group = content.trial_group_anchor(index)
    return (
        f'<section class="trial-group" id="{escaped(group)}" tabindex="-1" '
        f'aria-labelledby="{escaped(group)}-heading">'
        f'<h3 id="{escaped(group)}-heading">Trial {index}</h3>'
        f'<div class="evidence-controls" role="group" aria-label="Trial {index} supporting details" hidden>'
        '<button type="button" data-trial-details="show">Show both</button>'
        '<button type="button" data-trial-details="hide">Hide both</button></div>'
        '<div class="trial-pair">'
        f'<h4 class="trial-section-heading trial-change-heading">{escaped(content.TRIAL_CHANGE_HEADING)}</h4>'
        f"{summary_intro}"
        '<h4 class="trial-pair-heading before">Before</h4>'
        '<h4 class="trial-pair-heading after">After</h4>'
        f"{descriptions}{caveat}"
        '<h4 class="trial-section-heading">Trial record and verdict</h4>'
        f"{''.join(metadata)}"
        f'<h4 class="trial-section-heading">{escaped(content.FINAL_ANSWER_HEADING)}</h4>'
        f"{''.join(answers)}</div>"
        f'<details class="trial-shared-details" id="{escaped(group)}-support" '
        f"{'open' if mode == 'review' else ''}>"
        "<summary>Supporting details · Before and After</summary>"
        f'<div class="trial-pair">{"".join(actions)}</div>'
        f'<details class="trial-shared-details" id="{escaped(group)}-commands" '
        f"{'open' if mode == 'review' else ''}>"
        f"<summary>{escaped(action_heading)} · Before and After</summary>"
        f'<div class="trial-pair">{"".join(commands)}</div></details>'
        "</details></section>"
    )


def _trial_group_links(report) -> str:
    count = max(len(report.variants.before.trials), len(report.variants.after.trials))
    return "".join(
        f'<a href="#{html.escape(content.trial_group_anchor(index))}">Trial {index}</a>'
        for index in range(1, count + 1)
    )


def _decision_choices(choices, total: int) -> str:
    lines = []
    for choice in choices:
        count = f'<span class="choice-count">{content.trial_count(choice.count, total)}</span>'
        lines.append(f'<span class="dline">{html.escape(choice.choice)}{count}</span>')
    return "".join(lines) or html.escape(content.NO_EXTRACTED_CHOICE)


def _edit_links(row, report) -> str:
    if not row.edit_hunks:
        return (
            '<span class="dnote">Related edit unavailable — no mapping recorded.</span>'
        )
    links = " · ".join(
        f'<a href="#edit-hunk-{number}">'
        f"{html.escape(content.instruction_hunk_label(report.rule_diff, number))}</a>"
        for number in row.edit_hunks
    )
    return (
        f'<span class="edit-links">Related edit (model interpretation): {links}</span>'
    )


def _instruction_edit(report) -> str:
    lines = []
    blocks = []
    current = None
    remaining = 0
    hunks = {hunk.number: hunk for hunk in parse_diff_hunks(report.rule_diff)}
    for line, number in content.instruction_diff_lines(report.rule_diff):
        in_body = current is not None and remaining > 0
        if number:
            current = number
            remaining = len(hunks[number].lines)
            in_body = False
            label = content.instruction_hunk_label(report.rule_diff, number)
            blocks.append(
                f'<button type="button" data-select-edit="{number}" aria-pressed="false">'
                f"{html.escape(label)}</button>"
            )
        anchor = f' id="edit-hunk-{number}" tabindex="-1"' if number else ""
        block = f' data-edit-hunk="{current}"' if in_body or number else ""
        css_class = _diff_line_class(line) if in_body else "d-ctx"
        lines.append(
            f'<span{anchor}{block} class="{css_class}">{html.escape(line)}</span>\n'
        )
        if in_body:
            remaining -= 1
    controls = (
        '<div class="diff-toolbar" role="group" aria-label="Highlight changed instruction lines" hidden>'
        f"{''.join(blocks)}</div>"
        '<p class="note" id="edit-selection-status" role="status" aria-live="polite"></p>'
        if blocks
        else ""
    )
    aim_links = _edit_links(report.intent, report) if report.intent.edit_hunks else ""
    return (
        '<section class="instruction-edit" id="instruction-diff" tabindex="-1" '
        'aria-labelledby="instruction-edit-heading">'
        '<div class="edit-heading">'
        f'<h2 id="instruction-edit-heading">{html.escape(report.content.diff_heading)}</h2>'
        f"{_info('edit-info', 'About these instruction changes', f'<p>{html.escape(content.EDIT_LINK_NOTE)}</p>')}"
        "</div>"
        f'<p class="edit-aim">{html.escape(content.instruction_edit_aim(report.intent))}</p>'
        f"{aim_links}"
        f'<p class="edit-summary">{html.escape(content.instruction_edit_counts(report.rule_diff))}</p>'
        f"{controls}<pre>{''.join(lines)}</pre>"
        '<p class="note">+ added · − removed · unmarked context. '
        "Selected blocks highlight changed lines, not behavior evidence.</p></section>"
    )


def _decision_progression(report) -> str:
    decisions = report.decisions
    nodes = []
    for index, row in enumerate(decisions.rows, 1):
        status = content.decision_evidence_status(row, decisions, report)
        role = content.decision_role(index, row, decisions.outcome)
        role_key = (
            "result"
            if index == decisions.outcome
            else "action"
            if type(row.anchor) is int
            else "detail"
        )
        title = row.topic.strip() or row.decision
        source = content.source_label(row.anchor, report.metadata.trace_source)
        source_key = "ans" if row.anchor == "answer" else "cmd"
        final_class = " progression-final" if index == decisions.outcome else ""
        choices = (
            '<span class="decision-lanes">'
            + "".join(
                f'<span class="decision-lane {label.lower()} {"b" if label == "Before" else "a"}">'
                f'<span class="preview-label">{label}</span>'
                f"{_decision_choices(values, total)}</span>"
                for label, values, total in (
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
            f'<li class="decision-step"><details class="decision-row decision-{status.lower().replace(" ", "-")}{final_class}" '
            f'id="decision-{index}">'
            '<summary class="decision-node">'
            f'<span class="progression-number">{index}</span>'
            '<span class="progression-heading">'
            f'<span class="progression-topic">{html.escape(title)}</span>'
            f'<strong class="decision-status">{html.escape(status)}</strong>'
            f'<span class="progression-role decision-tag tag-{role_key}">{html.escape(role)}</span>'
            f'<span class="decision-tag tag-{source_key}">{html.escape(source)}</span></span>'
            '<span class="decision-disclosure"><span class="hint-show">Show evidence</span>'
            f'<span class="hint-hide">Hide evidence</span>{_CHEVRON}</span>'
            f"{choices}</summary>"
            f'<div class="decision-evidence">{question}'
            f'<p class="decision-meta"><span class="decision-tag tag-{source_key}">{html.escape(source)}</span></p>'
            f"{_edit_links(row, report)}{note}"
            '<details class="supporting-trials"><summary>View supporting trial records</summary>'
            f'<nav class="record-links" aria-label="Available trial records">{_trial_group_links(report)}</nav>'
            '<p class="note">These are the available source records. The saved comparison does not '
            "map each extracted behavior to individual trials.</p></details>"
            "</div></details></li>"
        )
    return (
        '<section class="progression" id="decision-progression" tabindex="-1" aria-labelledby="decision-progression-heading">'
        '<div class="decision-toolbar">'
        '<h2 class="comparison-heading" id="decision-progression-heading">Behavior comparisons</h2>'
        '<div class="evidence-controls" role="group" aria-label="Behavior comparison disclosures" hidden>'
        '<button type="button" data-evidence-expand="true" aria-controls="decision-list">Expand all</button>'
        '<button type="button" data-evidence-expand="false" aria-controls="decision-list">Collapse all</button>'
        "</div></div>"
        f'<p class="note" id="decision-progression-note">{html.escape(content.DECISION_PROGRESSION_NOTE)}</p>'
        f'<p class="note">{html.escape(content.TRIAL_COUNT_NOTE)}</p>'
        '<ol class="decision-path" id="decision-list" role="list" aria-describedby="decision-progression-note">'
        f"{''.join(nodes)}</ol></section>"
    )


_REPORT_INTERACTIONS = """<script>
(() => {
  const tabs = document.querySelector(".tabs");
  const panels = [...document.querySelectorAll(".panel")];
  const rows = [...document.querySelectorAll(".decision-row")];
  const editButtons = [...document.querySelectorAll("[data-select-edit]")];
  const editLines = [...document.querySelectorAll("[data-edit-hunk]")];
  let printState = null;
  const selectEdit = number => {
    editLines.forEach(line => line.classList.toggle("edit-selected",
      line.dataset.editHunk === number && line.matches(".d-add, .d-del")));
    editButtons.forEach(button =>
      button.setAttribute("aria-pressed", String(button.dataset.selectEdit === number)));
    const selected = editButtons.find(button => button.dataset.selectEdit === number);
    const status = document.getElementById("edit-selection-status");
    if (status) status.textContent = selected ? "Highlighted changed lines: " + selected.textContent : "";
  };
  const route = focus => {
    let id;
    try { id = decodeURIComponent(location.hash.slice(1)); }
    catch { id = ""; }
    const target = document.getElementById(id);
    const panel = target?.closest(".panel") || document.getElementById("panel-summary");
    panels.forEach(section => {
      section.hidden = section !== panel;
      section.classList.toggle("is-active", section === panel);
    });
    document.querySelectorAll(".tabbar a").forEach(link => {
      if (link.hash === "#" + panel.id) link.setAttribute("aria-current", "page");
      else link.removeAttribute("aria-current");
    });
    let disclosure = target?.closest("details");
    while (disclosure) {
      disclosure.open = true;
      disclosure = disclosure.parentElement.closest("details");
    }
    if (target?.id.startsWith("edit-hunk-")) selectEdit(target.dataset.editHunk);
    if (focus && target) {
      const focusTarget = target.matches("details") ? target.querySelector("summary") : target;
      focusTarget.setAttribute("tabindex", "-1");
      focusTarget.focus({preventScroll: true});
      target.scrollIntoView({block: "start"});
    }
  };
  const updateControls = () => {
    document.querySelectorAll("[data-evidence-expand]").forEach(button => {
      const expanded = button.dataset.evidenceExpand === "true";
      button.disabled = rows.every(row => row.open === expanded);
    });
    document.querySelectorAll(".trial-group").forEach(group => {
      const details = [...group.querySelectorAll("details")];
      group.querySelectorAll("[data-trial-details]").forEach(button => {
        const expanded = button.dataset.trialDetails === "show";
        button.disabled = details.every(detail => detail.open === expanded);
      });
    });
  };
  document.querySelectorAll(".evidence-controls, .diff-toolbar").forEach(control => {
    control.hidden = false;
  });
  document.querySelectorAll("[data-attention-dismiss]").forEach(button => {
    button.hidden = false;
  });
  document.addEventListener("toggle", updateControls, true);
  document.addEventListener("click", event => {
    const attentionButton = event.target.closest("[data-attention-dismiss]");
    if (attentionButton) {
      const finding = attentionButton.closest(".attention-finding");
      const dismissed = finding.classList.toggle("is-dismissed");
      attentionButton.setAttribute("aria-expanded", String(!dismissed));
      attentionButton.textContent = dismissed ? "Show again" : "Not relevant here";
    }
    const info = event.target.closest(".info > button");
    if (info) {
      const expanded = info.getAttribute("aria-expanded") !== "true";
      document.querySelectorAll(".info > button").forEach(button => {
        button.setAttribute("aria-expanded", "false");
        button.parentElement.classList.remove("info-open");
      });
      info.setAttribute("aria-expanded", String(expanded));
      info.parentElement.classList.toggle("info-open", expanded);
    } else if (!event.target.closest(".info")) {
      document.querySelectorAll(".info > button").forEach(button => {
        button.setAttribute("aria-expanded", "false");
        button.parentElement.classList.remove("info-open");
      });
    }
    const expand = event.target.closest("[data-evidence-expand]");
    if (expand) rows.forEach(row => { row.open = expand.dataset.evidenceExpand === "true"; });
    const trialButton = event.target.closest("[data-trial-details]");
    if (trialButton) trialButton.closest(".trial-group").querySelectorAll("details").forEach(detail => {
      detail.open = trialButton.dataset.trialDetails === "show";
    });
    const edit = event.target.closest("[data-select-edit]");
    if (edit) {
      selectEdit(edit.dataset.selectEdit);
      document.querySelector(".edit-selected")?.scrollIntoView({block: "center"});
    }
    updateControls();
    if (event.defaultPrevented || event.button !== 0 ||
        event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
    const link = event.target.closest('a[href^="#"]');
    if (link && link.hash === location.hash) route(true);
  });
  document.addEventListener("keydown", event => {
    if (event.key !== "Escape") return;
    document.querySelectorAll(".info > button").forEach(button => {
      button.setAttribute("aria-expanded", "false");
      button.parentElement.classList.remove("info-open");
    });
    if (document.activeElement?.closest(".info")) document.activeElement.blur();
  });
  window.addEventListener("hashchange", () => route(true));
  window.addEventListener("beforeprint", () => {
    if (printState !== null) return;
    printState = {
      details: [...document.querySelectorAll("details")].map(row => [row, row.open]),
      panels: panels.map(panel => [panel, panel.hidden])
    };
    printState.details.forEach(([row]) => { row.open = true; });
    panels.forEach(panel => { panel.hidden = false; });
  });
  window.addEventListener("afterprint", () => {
    if (printState === null) return;
    printState.details.forEach(([row, open]) => { row.open = open; });
    printState.panels.forEach(([panel, hidden]) => { panel.hidden = hidden; });
    printState = null;
    updateControls();
  });
  if (tabs) tabs.dataset.enhanced = "true";
  if (editButtons.length) selectEdit(editButtons[0].dataset.selectEdit);
  route(Boolean(location.hash));
  updateControls();
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
            else (
                f'<p class="note">{html.escape(content.NO_COMMANDS_RECORDED)}. '
                "This does not establish that no actions occurred.</p>"
            )
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
        f'<section class="flow-lane {side}" aria-labelledby="flow-{side}-heading">'
        f'<h3 id="flow-{side}-heading">{html.escape(label)}</h3>{body}</section>'
    )


def _attention_side(report, finding: AttentionFindingData, side: str) -> str:
    branches = []
    for choice, steps, count, total in content.attention_branches(
        report, finding, side
    ):
        pictures = (
            '<span class="attention-flow-arrow" aria-hidden="true">→</span>'.join(
                '<div class="attention-flow-step">'
                f"{illustration(step.icon)}<p>{html.escape(step.label)}</p></div>"
                for step in steps
            )
        )
        branches.append(
            f'<li class="attention-branch"><div class="attention-flow">{pictures}</div>'
            f'<p class="attention-choice">{html.escape(choice)}</p>'
            f'<span class="summary-count">{html.escape(content.trial_count(count, total))}</span></li>'
        )
    return (
        f'<section class="attention-side summary-{side}" aria-label="{side.capitalize()} observed behavior">'
        f'<h5 class="summary-side-label">{side.capitalize()}</h5>'
        f'<ul class="attention-branches">{"".join(branches)}</ul></section>'
    )


def _attention_guidance(finding: AttentionFindingData) -> str:
    return (
        '<dl class="attention-guidance"><dt>Matters if</dt>'
        f"<dd>{html.escape(finding.matters_if)}</dd><dt>What you can do</dt>"
        f"<dd>{html.escape(finding.next_step)}</dd></dl>"
    )


def _attention_notice(attention) -> str:
    if attention is None:
        return (
            f'<p class="attention-assessment">{html.escape(content.ATTENTION_UNAVAILABLE)}</p>'
            f'<div class="attention-unavailable"><p>{html.escape(content.ATTENTION_UNAVAILABLE_NOTE)}</p></div>'
        )
    assessment = (
        f'<p class="attention-assessment">{html.escape(attention.assessment)}</p>'
    )
    if not attention.findings:
        assessment += f'<div class="attention-empty"><p>{html.escape(content.ATTENTION_EMPTY_NOTE)}</p></div>'
    return assessment


def _attention_summary(report: ReportData) -> str:
    attention = report.decisions.attention
    parts = [_attention_notice(attention)]
    if attention is not None:
        for finding in attention.findings:
            relationship, evidence = content.attention_labels(
                finding, report.metadata.trace_source
            )
            body_id = f"attention-body-{finding.decision}"
            parts.append(
                '<article class="attention-finding">'
                '<header class="attention-heading">'
                f"<h4>{html.escape(finding.title)}</h4>"
                '<button class="attention-dismiss" type="button" data-attention-dismiss '
                f'aria-expanded="true" aria-controls="{body_id}" hidden>Not relevant here</button></header>'
                f'<div class="attention-body" id="{body_id}" data-attention-body>'
                '<div class="attention-pair">'
                f"{_attention_side(report, finding, 'before')}"
                f"{_attention_side(report, finding, 'after')}</div>"
                f'<p class="attention-consequence">{html.escape(finding.consequence)}</p>'
                '<p class="attention-meta">'
                f'<span class="attention-relationship">{html.escape(relationship)} · </span>'
                f'<span class="attention-evidence-kind">{html.escape(evidence)}</span></p>'
                f'<p class="attention-limit"><strong>Limit:</strong> {html.escape(finding.limit)}</p>'
                f"{_attention_guidance(finding)}</div></article>"
            )
    label = (
        'See why this matters <span aria-hidden="true">→</span>'
        if attention is not None and attention.findings
        else "Read the assessment"
    )
    parts.append(
        '<nav class="attention-nav" aria-label="Attention explanation">'
        f'<a href="#attention-explanation">{label}</a></nav>'
    )
    return "".join(parts)


def _attention_branch_evidence(report, finding: AttentionFindingData) -> str:
    sides = []
    for side in ("before", "after"):
        branches = []
        for choice, count, total, members in content.attention_branch_evidence(
            report, finding, side
        ):
            support = (
                '<nav class="attention-trial-links" aria-label="Supporting trials">'
                + " · ".join(
                    f'<a href="#{html.escape(content.trial_anchor(side, name))}">'
                    f"{html.escape(name)}</a>"
                    for name in members
                )
                + "</nav>"
                if members
                else '<p class="attention-membership-unavailable note">'
                + html.escape(content.ATTENTION_MEMBERSHIP_UNAVAILABLE)
                + "</p>"
            )
            branches.append(
                '<li class="attention-evidence-branch">'
                f"<p><strong>{html.escape(choice)}</strong> — "
                f"{html.escape(content.trial_count(count, total))}</p>{support}</li>"
            )
        sides.append(
            f'<section class="attention-evidence-side attention-evidence-{side}">'
            f"<h6>{side.capitalize()}</h6>"
            f"<ul>{''.join(branches)}</ul></section>"
        )
    return (
        '<section class="attention-observed-evidence"><h5>Observed branch evidence</h5>'
        f'<p class="note">{html.escape(content.ATTENTION_COUNT_NOTE)}</p>'
        + "".join(sides)
        + "</section>"
    )


def _attention_explanation(report: ReportData) -> str:
    attention = report.decisions.attention
    parts = [
        '<section id="attention-explanation" class="attention-explanation">'
        "<h3>What needs your attention</h3>",
        _attention_notice(attention),
    ]
    if attention is not None:
        for finding in attention.findings:
            relationship, evidence = content.attention_labels(
                finding, report.metadata.trace_source
            )
            references = tuple(
                dict.fromkeys(
                    (finding.decision,)
                    + tuple(
                        index for claim in finding.context for index in claim.decisions
                    )
                )
            )
            parts.extend(
                [
                    '<article class="attention-explanation-finding">',
                    f"<h4>{html.escape(finding.title)}</h4>",
                    '<section class="attention-interpretation">'
                    "<h5>Why this concern matters (model interpretation)</h5>",
                    '<p class="attention-meta">'
                    f'<span class="attention-relationship">{html.escape(relationship)} · </span>'
                    f'<span class="attention-evidence-kind">{html.escape(evidence)}</span></p>',
                    f"<p>{html.escape(finding.explanation)}</p></section>",
                    _attention_branch_evidence(report, finding),
                ]
            )
            if finding.context:
                parts.append(
                    '<section class="attention-context"><h5>Related context (model interpretation)</h5><ul>'
                )
                parts.extend(
                    f"<li>{html.escape(claim.text)} "
                    f'<span class="attention-context-citations">({_decision_links(claim.decisions)})</span></li>'
                    for claim in finding.context
                )
                parts.append("</ul></section>")
            parts.extend(
                [
                    '<section class="attention-uncertainty"><h5>Limits and uncertainty</h5>'
                    f'<p class="attention-limit">{html.escape(finding.limit)}</p></section>',
                    '<details class="attention-evidence"><summary>Check the evidence</summary>',
                    f'<nav class="evidence-nav" aria-label="Attention finding evidence">{_decision_links(references)}</nav>',
                    "</details></article>",
                ]
            )
    parts.append("</section>")
    return "".join(parts)


def _decision_links(indexes) -> str:
    return " · ".join(
        f'<a href="#decision-{index}">Comparison {index}</a>' for index in indexes
    )


def _summary_side(side, label: str) -> str:
    choices = []
    for choice in side.choices:
        detail = f"<p>{html.escape(choice.detail)}</p>" if choice.detail else ""
        choices.append(
            '<li class="summary-choice">'
            f"<h5>{html.escape(choice.label)}</h5>{detail}"
            '<span class="summary-count">'
            f"{html.escape(content.trial_count(choice.count, side.total))}"
            "</span></li>"
        )
    body = (
        f'<ul class="summary-choices">{"".join(choices)}</ul>'
        if choices
        else '<p class="summary-empty">No supported comparison is available.</p>'
    )
    return (
        f'<section class="summary-card summary-{label.lower()}" '
        f'aria-label="{label} observed behavior">'
        f'<h4 class="summary-side-label">{label}</h4>'
        f"{illustration(side.icon)}{body}</section>"
    )


def _primary_result_context(report) -> str:
    context = content.primary_result_context(report)
    if context is None or report.decisions.target_assessment is not None:
        return ""
    sides = "".join(
        f"<p><strong>{html.escape(label)}:</strong> {html.escape(text)}</p>"
        for label, text in context.sides
    )
    return (
        '<section class="primary-result-context" aria-label="Primary result context">'
        f"<h4>{html.escape(context.heading)} — {html.escape(context.status)}</h4>"
        f'{sides}<p class="note">{html.escape(context.note)}</p></section>'
    )


def _purpose_provenance(report):
    return "".join(
        '<p class="note purpose-provenance">'
        f"Goal {index}: {html.escape(goal.source)} · {html.escape(goal.basis)} · "
        f"{html.escape(goal.reference)}</p>"
        for index, goal in enumerate(report.decisions.purpose, 1)
    )


def _target_side(report, criterion, side):
    return html.escape(
        question_distribution(criterion, side, getattr(report.variants, side).total)
    )


def _target_summary(report):
    target = report.decisions.target_assessment
    if target is None:
        return f'<p class="note target-unavailable">{html.escape(UNAVAILABLE)}</p>'
    rows = []
    for criterion in target.criteria:
        result = (
            f"{_target_side(report, criterion, 'before')} → "
            f"{_target_side(report, criterion, 'after')}"
        )
        if question_distribution_changed(
            criterion, report.variants.before.total, report.variants.after.total
        ):
            result = f'<strong class="target-result-changed">{result}</strong>'
        rows.append(
            '<tr class="target-criterion">'
            f"<td>{html.escape(criterion.text)}</td><td>{result}</td></tr>"
        )
    return (
        '<div class="target-checks"><table>'
        '<thead><tr><th scope="col">What we checked</th>'
        '<th scope="col">Before → After</th></tr></thead>'
        f"<tbody>{''.join(rows)}</tbody></table></div>"
    )


def _target_explanation(report):
    target = report.decisions.target_assessment
    parts = ['<section class="target-evidence"><h3>What we checked</h3>']
    if target is None:
        parts.append(f"<p>{html.escape(UNAVAILABLE)}</p>")
    else:
        sources = {entry.id: entry for entry in report.decisions.recorded_evidence}
        for criterion in target.criteria:
            parts.append(
                f"<h4>{html.escape(criterion.text)}</h4>"
                f"<p>Before: {_target_side(report, criterion, 'before')} · "
                f"After: {_target_side(report, criterion, 'after')}</p>"
                f"<p>{html.escape(criterion.required_evidence)}</p>"
                '<details class="criterion-trials"><summary>Trial-by-trial reasoning and sources</summary>'
                f"<p>Goal {criterion.goal} · {html.escape(criterion.mode)}</p>"
                f"<p>{html.escape(acceptance(criterion))}</p>"
            )
            for side in ("before", "after"):
                for trial in getattr(criterion, side):
                    anchor = html.escape(content.trial_anchor(side, trial.trial))
                    parts.append(
                        f'<h5>{side.capitalize()} · <a href="#{anchor}">{html.escape(trial.trial)}</a>'
                        f" · {html.escape(trial.outcome.replace('_', ' '))}</h5>"
                        f"<p>{html.escape(trial.explanation)}</p>"
                    )
                    parts.append(
                        '<details class="raw-evidence"><summary>Recorded evidence</summary>'
                    )
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
                        parts.append(
                            f"<figure><figcaption>{html.escape(ref)} · {html.escape(label)}</figcaption>"
                            f"<pre>{html.escape(text)}</pre></figure>"
                        )
                    parts.append("</details>")
            parts.append("</details>")
    if report.decisions.recorded_evidence:
        parts.append(
            "<details><summary>Recorded source availability and limits</summary>"
        )
        parts.append(
            f"<p>{html.escape(evidence_limit_text(report.decisions.evidence_limits))}</p>"
        )
        for entry in report.decisions.recorded_evidence:
            parts.append(
                f"<p>{html.escape(entry.id)} · {html.escape(entry.source)} · "
                f"{html.escape(entry.status)} · {html.escape(entry.reason)}</p>"
                f"<pre>{html.escape(entry.text)}</pre>"
            )
        parts.append("</details>")
    parts.append("</section>")
    return "".join(parts)


def _change_explanation(report: ReportData) -> str:
    explanation = report.decisions.explanation
    navigation = (
        '<nav class="evidence-nav" aria-label="Change explanation evidence">'
        '<a href="#panel-decision">View behavior comparisons</a>'
        '<a href="#panel-flow">View recorded command flow</a>'
        '<a href="#instruction-diff">View instruction changes</a>'
        '<a href="#panel-trials">Inspect trial evidence</a></nav>'
    )
    complete = content.complete_trial_evidence(report)
    if explanation is None or not complete:
        notice = (
            content.CHANGE_EXPLANATION_UNAVAILABLE
            if complete
            else content.CHANGE_EXPLANATION_INCOMPLETE
        )
        return (
            "<h2>Understand the change</h2>"
            '<div class="empty-state"><h3>Change explanation unavailable</h3>'
            f"<p>{html.escape(notice)}</p></div>"
            + _attention_explanation(report)
            + _target_explanation(report)
            + navigation
        )
    parts = [
        '<div class="change-explanation"><p class="explanation-kicker">Understand the change</p>',
        f'<h2 class="explanation-headline">{html.escape(explanation.headline)}</h2>',
        f'<p class="explanation-overview">{html.escape(explanation.overview)}</p>',
        f'<p class="note">{html.escape(content.INTERPRETATION_NOTE)}</p>',
        '<ol class="explanation-steps" role="list">',
    ]
    references = []
    for number, step in enumerate(explanation.steps, 1):
        references.extend(step.decisions)
        parts.append(
            '<li class="explanation-step">'
            f'<h3><span class="explanation-number" aria-hidden="true">{number}</span>'
            f'{html.escape(step.title)}</h3><div class="explanation-pair">'
            f'<section class="explanation-side before"><h4>Before</h4><p>{html.escape(step.before)}</p></section>'
            f'<section class="explanation-side after"><h4>After</h4><p>{html.escape(step.after)}</p></section>'
            '</div><div class="explanation-meaning"><h4>What this means</h4>'
            f"<p>{html.escape(step.meaning)}</p>"
            f'<span class="evidence-links">{_decision_links(step.decisions)}</span></div></li>'
        )
    parts.append("</ol>")
    parts.append(_attention_explanation(report))
    for heading, claims in (
        ("What stays the same", explanation.unchanged),
        ("What this evidence cannot establish", explanation.limits),
    ):
        if claims:
            parts.append(f'<section class="explanation-claims"><h3>{heading}</h3><ul>')
            for claim in claims:
                references.extend(claim.decisions)
                parts.append(
                    f"<li>{html.escape(claim.text)}"
                    f'<span class="evidence-links">{_decision_links(claim.decisions)}</span></li>'
                )
            parts.append("</ul></section>")
    parts.append(_target_explanation(report))
    comparisons = content.explanation_comparisons(
        report, tuple(dict.fromkeys(references))
    )
    if comparisons:
        parts.append(
            '<details class="explanation-consistency"><summary>Consistency across trials</summary>'
            '<p class="note">All extracted branches for the cited comparisons are shown, '
            "including minority choices. Before and After trials are independent; "
            "these counts are model extractions, not causal proof.</p>"
        )
        for index, title, sides in comparisons:
            parts.append(f"<h4>{html.escape(title)}</h4>")
            parts.extend(
                f"<p><strong>{label}:</strong> {html.escape(text)}</p>"
                for label, text in sides
            )
            parts.append(
                f'<span class="evidence-links">{_decision_links((index,))}</span>'
            )
        parts.append("</details>")
    if explanation.examples:
        parts.append(
            '<details class="explanation-examples"><summary>Exact excerpts from the final answers</summary>'
        )
        for example in explanation.examples:
            anchor = html.escape(content.trial_anchor(example.side, example.trial))
            parts.append(
                f'<figure class="explanation-excerpt {example.side}">'
                f"<figcaption>{example.side.capitalize()} · {html.escape(example.trial)} · "
                f'<a href="#{anchor}">View full trial evidence</a></figcaption>'
                f"<pre>{html.escape(example.text)}</pre></figure>"
            )
        parts.append("</details>")
    parts.append(navigation + "</div>")
    return "".join(parts)


def _short_story_summary(report: ReportData) -> str:
    summary = report.summary
    intent = report.intent
    intent_label, intent_note = content.intent_context(intent)
    intent_badge = {
        "expected": "Supplied expectation",
        "inferred": "Inferred",
        "unavailable": "Unavailable",
        "purpose": "Recorded before trials",
    }[intent.source]
    intent_links = '<a href="#instruction-diff">View instruction changes</a>'
    claims = ""
    for label, claim, css_class in (
        ("Why it matters", summary.why, "summary-why"),
        ("Watch out", summary.caution, "summary-caution"),
    ):
        if claim:
            claims += (
                f'<div class="{css_class}"><strong>{label}</strong>'
                f"<p>{html.escape(claim.text)}</p>"
                f'<span class="evidence-links">{_decision_links(claim.decisions)}</span>'
                "</div>"
            )
    if summary.why is None:
        claims = (
            '<p class="note summary-interpretation-unavailable">'
            "No supported interpretation was supplied; these observations alone "
            "do not establish the edit's benefit.</p>"
        ) + claims
    lead_link = (
        '<a class="summary-evidence-button" href="#panel-explanation">'
        'Understand the change <span aria-hidden="true">→</span></a>'
    )
    notices = "".join(f"<li>{html.escape(note)}</li>" for note in summary.notices)
    scenario = (
        f'<p class="summary-context">{html.escape(summary.scenario)}</p>'
        if summary.scenario
        else ""
    )
    return (
        '<div class="short-story-summary">'
        f'<h2 class="summary-headline">{html.escape(summary.headline)}</h2>'
        '<ol class="story-steps" role="list">'
        '<li class="story-step"><span class="story-number" aria-hidden="true">1</span>'
        '<div class="story-body"><div class="intent-heading"><h3>The intended change</h3>'
        f'<span class="intent-source">{intent_badge}</span>'
        f"{_info('intent-info', intent_label, f'<p>{html.escape(intent_note)}</p>')}"
        f'<nav class="intent-evidence" aria-label="Instruction aim evidence">{intent_links}</nav>'
        "</div>"
        f'<p class="story-intent">{html.escape(intent.text)}</p>'
        f"{_purpose_provenance(report)}"
        "</div></li>"
        '<li class="story-step"><span class="story-number" aria-hidden="true">2</span>'
        '<div class="story-body"><h3>What the evidence shows</h3>'
        f"{scenario}"
        f'<p class="summary-provenance">{html.escape(summary.evidence_label)}</p>'
        '<div class="summary-pair">'
        f"{_summary_side(summary.before, 'Before')}"
        '<span class="summary-arrow" aria-hidden="true">→</span>'
        f"{_summary_side(summary.after, 'After')}</div>"
        f"{_primary_result_context(report)}"
        + _target_summary(report)
        + '<nav class="evidence-nav" aria-label="Summary evidence">'
        f"{lead_link}</nav>"
        "</div></li>"
        '<li class="story-step story-attention"><span class="story-number" aria-hidden="true">3</span>'
        '<div class="story-body"><h3>What needs your attention</h3>'
        f"{_attention_summary(report)}"
        "</div></li>"
        '<li class="story-step"><span class="story-number" aria-hidden="true">4</span>'
        '<div class="story-body"><h3>What this means</h3>'
        f'{claims}<ul class="summary-notices">{notices}</ul>'
        "</div></li></ol></div>"
    )


def _tag_legend(legend) -> str:
    groups = {
        "Comparison status": [],
        "Decision role": [],
        "Evidence source": [],
        "Other labels": [],
    }
    for key, label, meaning in legend:
        if key in ("changed", "same", "unavailable"):
            heading = "Comparison status"
        elif key in ("action", "result", "detail"):
            heading = "Decision role"
        elif key in ("cmd", "ans"):
            heading = "Evidence source"
        else:
            heading = "Other labels"
        groups[heading].append(
            f'<div><dt><span class="decision-tag tag-{html.escape(key)}">{html.escape(label)}</span></dt>'
            f"<dd>{html.escape(meaning)}</dd></div>"
        )
    return (
        "<p>Colors identify comparison status, decision role, or evidence source. "
        "They do not indicate success or failure.</p>"
        + "".join(
            f'<section class="legend-group"><h3>{heading}</h3>'
            f'<dl class="legend">{"".join(items)}</dl></section>'
            for heading, items in groups.items()
            if items
        )
    )


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
        f'aria-describedby="{pop_id}" aria-controls="{pop_id}" aria-expanded="false">{_INFO_ICON}</button>'
        f'<div class="pop" id="{pop_id}" role="note">'
        f'<p class="pop-title">{html.escape(label)}</p>{body}</div></div>'
    )


_CHEVRON = (
    '<svg class="chev" width="14" height="14" viewBox="0 0 24 24" fill="none" '
    'stroke="currentColor" stroke-width="2.5" stroke-linecap="round" '
    'stroke-linejoin="round" aria-hidden="true">'
    '<polyline points="9 6 15 12 9 18"></polyline></svg>'
)


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

    trial_groups = (
        "".join(
            _trial_group(
                index,
                before_trial,
                after_trial,
                self_reported,
                metadata.mode,
                content.trial_summary_for_group(
                    report.decisions, before_trial, after_trial
                ),
            )
            for index, (before_trial, after_trial) in enumerate(
                zip_longest(before.trials, after.trials), 1
            )
        )
        or '<p class="note">No trial records are available.</p>'
    )
    trial_overview = "".join(
        f'<section class="trial-cell {side}"><h3>{side.capitalize()}</h3>'
        f'<p class="col-note">{escaped(variant.note)}</p>'
        f'<p class="count">{escaped(variant.count_text + variant.count_suffix)}</p></section>'
        for side, variant in (("before", before), ("after", after))
    )
    trials_html = (
        f'<h2 class="section-label">{escaped(content.TRIAL_EVIDENCE_HEADING)}</h2>'
        f'<p class="sub">{escaped(content.trial_evidence_note(self_reported))}</p>'
        '<p class="note">Final answers are visible below. Each numbered comparison aligns '
        "Before on the left and After on the right. Supporting-detail disclosures open both "
        "sides together; matching numbers do not establish paired execution.</p>"
        f'<div class="trial-pair trial-overview">{trial_overview}</div>'
        f'<nav class="record-links" aria-label="Jump to trial">{_trial_group_links(report)}</nav>'
        f"{trial_groups}"
    )

    decisions_html = (
        '<div class="comparison-heading-with-info">'
        f'<h2 id="behavior-diff-heading">{escaped(report_content.decision_heading)}</h2>'
        f"{_info('pop-decision', 'Behavior comparison labels', _tag_legend(report_content.tag_legend))}</div>"
        '<div class="empty-state"><h3>Behavior comparison unavailable</h3>'
        f"<p>{escaped(content.NO_EXTRACTED_CHOICE)}</p>"
        "<p>Missing extraction does not establish absent behavior. "
        "The retained trial records remain available for inspection.</p></div>"
        f'<p class="note">{escaped(report.result.summary)}</p>'
        '<a href="#panel-trials">View available trial records</a>'
    )
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
        if not content.complete_trial_evidence(report):
            limitation += (
                '<p class="note">Trial evidence is incomplete. The extracted comparisons below '
                "are retained for inspection, not a complete Before/After conclusion.</p>"
            )
        decisions_html = (
            '<div class="comparison-heading-with-info">'
            f'<h2 id="behavior-diff-heading">{escaped(report_content.decision_heading)}</h2>'
            f"{_info('pop-decision', 'Behavior comparison labels', _tag_legend(report_content.tag_legend))}</div>"
            f'<p class="tab-overview">{escaped(content.decision_overview(report))}</p>'
            f'<p class="sub">{escaped(report_content.decision_blurb)}</p>'
            f"{limitation}"
            f"{_decision_progression(report)}"
            f'<p class="note">{escaped(footer)}</p>{explanation}'
            '<nav class="evidence-nav" aria-label="Behavior comparison evidence">'
            '<a href="#panel-trials">View supporting trial records</a></nav>'
        )

    flow_section = (
        '<h2 class="section-label">Flow diff</h2>'
        '<div class="empty-state"><h3>Recorded command flow unavailable</h3>'
        f"<p>{escaped(content.SELF_REPORTED_LIMIT)}</p>"
        "<p>No command sequence is inferred from answer text or self-reported actions.</p></div>"
        '<a href="#panel-trials">View available trial records</a>'
    )
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
            '<a href="#panel-decision">Compare behavior</a>'
            if report.decisions.rows
            else ""
        )
        flow_section = (
            '<div class="comparison-heading-with-info">'
            f"<h2>{escaped(report_content.flow_heading)}</h2>"
            f"{_info('pop-flow', content.flow_kinds_heading(flow.kinds).rstrip(':'), kinds_html)}</div>"
            '<section class="progression" id="flow-progression" tabindex="-1" aria-labelledby="flow-progression-heading">'
            '<h2 class="comparison-heading" id="flow-progression-heading">Recorded command sequences</h2>'
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

    scenario_html = "".join(
        f"<section><h3>{escaped(heading)}</h3><p>{escaped(text)}</p></section>"
        for heading, text in content.scenario_sections(report)
    )
    scenario_prompt = (
        '<details class="scenario-prompt"><summary>View full scenario prompt</summary>'
        f"<pre>{escaped(report_content.task)}</pre></details>"
        if report_content.task
        else f'<p class="note">{escaped(content.SCENARIO_PROMPT_UNAVAILABLE)}</p>'
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
    limits_html = "".join(f"<li>{escaped(limit)}</li>" for limit in result.limits)
    summary_html = f"""{_short_story_summary(report)}
<p class="note summary-boundary">{escaped(report_content.boundary)}</p>
<details class="summary-details"><summary>Full scenario and expected behavior</summary>
<div class="scenario-context">{scenario_html}</div>
{scenario_prompt}
</details>
<details class="summary-details"><summary>{escaped(report_content.limits_heading)}</summary>
<ul class="evidence-limits">{limits_html}</ul>
</details>"""

    tabs = [
        ("summary", "Summary", "", summary_html),
        ("explanation", "Understand the change", "", _change_explanation(report)),
        ("instruction", "Instruction changes", "", _instruction_edit(report)),
        (
            "decision",
            "Behavior diff",
            f"{len(report.decisions.rows)} comparisons"
            if report.decisions.rows
            else "",
            decisions_html,
        ),
        ("flow", "Flow diff", "", flow_section),
        (
            "trials",
            content.TRIAL_EVIDENCE_HEADING,
            f"{before.total} + {after.total} trials",
            trials_html,
        ),
    ]

    return f"""<title>{escaped(report_content.title)}</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
{css}</style>

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
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        "</head><body>" + artifact + "</body></html>"
    )
