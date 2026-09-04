#!/usr/bin/env python3
"""Render a Behavior Diff run into report.md + report.html (+ artifact body).

Usage: render.py RUN_DIR CAPSULE_DIR MODEL [CONFIG_JSON]
"""

import html
import sys
from pathlib import Path

from reporting import content
from reporting.load import load_report


run = Path(sys.argv[1]).resolve()
capsule = Path(sys.argv[2]).resolve()
model = sys.argv[3]
config_path = Path(sys.argv[4]) if len(sys.argv) > 4 else None
report = load_report(run, capsule, model, config_path)


# Temporary bridge while the existing Markdown and HTML layout is split later.
metadata = report.metadata
report_content = report.content
MODE = metadata.mode
SELF_REPORTED = metadata.trace_source == "self-reported"
TARGET_FILE = metadata.target_file
TITLE = report_content.title
SUB = report_content.subtitle
EXPECTED = report_content.expected
BOUNDARY = report_content.boundary
scenario = report_content.scenario
rule_diff = report.rule_diff
result = report.result.text
result_kind = report.result.kind
dec_blurb = report_content.decision_blurb
obs_md = report_content.observation


def _bridge_variant(variant):
    return {
        "trials": [
            {
                "name": trial.name,
                "verdict": trial.verdict,
                "actions": trial.actions,
                "cmds": trial.commands,
                "final": trial.final,
            }
            for trial in variant.trials
        ],
        "passed": variant.passed,
        "blocked": variant.blocked,
        "valid": variant.valid,
        "total": variant.total,
    }


variants = {
    "before": _bridge_variant(report.variants.before),
    "after": _bridge_variant(report.variants.after),
}
b = variants["before"]
a = variants["after"]
count_line = {
    name: (
        "**" + variant.count_text + "**"
        if variant.count_emphasized
        else variant.count_text
    )
    for name, variant in (
        ("before", report.variants.before),
        ("after", report.variants.after),
    )
}

flow = report.command_flow
shared = flow.shared
bprefix = flow.before.prefix
aprefix = flow.after.prefix
bpaths = [(path.steps, path.count) for path in flow.before.paths]
apaths = [(path.steps, path.count) for path in flow.after.paths]
nb = flow.before.total
na = flow.after.total
same_flow = flow.same


def step_text(step):
    return step


dec = {
    "chain": [
        {
            "decision": row.decision,
            "topic": row.topic,
            "anchor": row.anchor,
            "diverges": row.diverges,
            "note": row.note,
            "before": [
                {"choice": choice.choice, "n": choice.count} for choice in row.before
            ],
            "after": [
                {"choice": choice.choice, "n": choice.count} for choice in row.after
            ],
        }
        for row in report.decisions.rows
    ],
    "fork": report.decisions.fork,
    "fork_note": report.decisions.fork_note,
    "dropped": report.decisions.dropped,
    "counts": {
        "before": report.decisions.before_count,
        "after": report.decisions.after_count,
    },
}


def branch_str(brs, n):
    return (
        " · ".join(
            (branch["choice"] if branch["n"] == n else f"{branch['choice']} ({branch['n']}/{n})")
            for branch in brs
        )
        or "—"
    )

dnb = dec["counts"]["before"]
dna = dec["counts"]["after"]
dec_md = []
if dec["chain"]:
    fork = dec["fork"]
    lead_n = 0
    for row in dec["chain"]:
        if row["diverges"]:
            break
        lead_n += 1
    dec_md += [f"## {report_content.decision_heading}\n", dec_blurb + "\n"]
    if lead_n:
        dec_md.append("Decided the same way on both sides:\n")
        for i, row in enumerate(dec["chain"][:lead_n], 1):
            before_choice = branch_str(row["before"], dnb)
            after_choice = branch_str(row["after"], dna)
            choice = (
                before_choice
                if before_choice == after_choice
                else f"before: {before_choice} · after: {after_choice}"
            )
            note = f" — {row['note']}" if row["note"] else ""
            when = " *(in the final answer)*" if row["anchor"] == "answer" else ""
            title = row["topic"] or row["decision"]
            dec_md.append(f"- {i}. **{title}**{when} → {choice}{note}")
        dec_md.append("")
    if lead_n < len(dec["chain"]):
        dec_md.append("Diverging from here:\n")
        for i, row in enumerate(dec["chain"][lead_n:], lead_n + 1):
            mark = " ⟵ root behavior change" if i == fork else (
                " *(downstream)*" if row["diverges"] and fork and i > fork else ""
            )
            mark += " *(in the final answer)*" if row["anchor"] == "answer" else ""
            title = (
                f"**{row['topic']}** — {row['decision']}"
                if row["topic"]
                else row["decision"]
            )
            if row["diverges"]:
                dec_md.append(f"- {i}. {title}{mark}")
                dec_md.append(f"  - BEFORE: {branch_str(row['before'], dnb)}")
                dec_md.append(f"  - AFTER: {branch_str(row['after'], dna)}")
            else:
                dec_md.append(
                    f"- {i}. {row['decision']} *(same)* → "
                    f"{branch_str(row['before'], dnb)}"
                )
            if row["note"]:
                dec_md.append(f"  - note: {row['note']}")
        dec_md.append("")
    dec_md.append(content.decision_footer(report.decisions.rows, report.decisions.fork))
    if report.decisions.fork_note:
        dec_md.append("\n" + report.decisions.fork_note)
    if report.decisions.dropped:
        dec_md.append("\n" + content.dropped_rows(report.decisions.dropped))
    dec_md.append("")
# ---------- report.md ----------
md = [f"# {TITLE}\n", SUB + "\n"]
if obs_md:
    md.append("**" + obs_md + "**\n")
md += [
    f"Model: {model} · {b['total']} trial(s) per variant.\n",
    f"## {report_content.scenario_heading}\n",
    scenario + "\n",
]
if EXPECTED:
    md += [f"## {report_content.expected_heading}\n", EXPECTED + "\n"]
md += [
    f"## {report_content.diff_heading}\n",
    "```diff\n" + rule_diff.rstrip() + "\n```\n",
]
md += dec_md
if not SELF_REPORTED:
    flow_md = [
        f"## {report_content.flow_heading}\n",
        (
            "Steps are described from the agents' actual commands; a "
            "path is a sequence at least one trial literally took. Full "
            "commands are in the trial sections below.\n"
        ),
    ]
    if same_flow:
        flow_md.append(
            "Every trial in both variants took the same steps: "
            + " → ".join(step_text(k) for k in shared)
            + ". Differences, if any, are in the final answers below.\n"
        )
    else:
        flow_md.append("Shared flow (every trial, both variants):\n")
        for k in shared:
            flow_md.append(f"- {step_text(k)}")
        flow_md.append("\nDivergence:\n")

        def md_branch(tag, prefix, paths, n):
            if not paths:
                flow_md.append(
                    f"- {tag}, all {n} trials → "
                    + (
                        " → ".join(step_text(step) for step in prefix)
                        or "(same steps as the shared flow)"
                    )
                )
                return
            lead = f"- {tag}"
            if prefix:
                lead += ", all trials → " + " → ".join(
                    step_text(step) for step in prefix
                )
            flow_md.append(lead + ", then splits:")
            for path, count in paths:
                flow_md.append(
                    f"  - {count} of {n} trials → "
                    + " → ".join(step_text(step) for step in path)
                )

        md_branch("BEFORE", bprefix, bpaths, nb)
        md_branch("AFTER", aprefix, apaths, na)
    flow_md.append("")
    if dec_md:
        md.append("<details><summary>" + content.flow_fold_summary() + "</summary>\n")
        md += flow_md
        md.append("</details>\n")
    else:
        md += flow_md
for variant_name, label in (
    ("before", f"BEFORE — {metadata.before_label}"),
    ("after", f"AFTER — {metadata.after_label}"),
):
    variant = variants[variant_name]
    md.append(f"## {label}\n")
    md.append(count_line[variant_name] + "\n")
    for trial in variant["trials"]:
        md.append(f"### {trial['name']} — {trial['verdict']}\n")
        if trial["actions"] != "-":
            md.append(trial["actions"] + "\n")
        action_label = (
            "self-reported actions" if SELF_REPORTED else "commands the agent ran"
        )
        md.append(
            f"<details><summary>{action_label} "
            f"({len(trial['cmds'])})</summary>\n\n```\n"
            + "\n\n".join(command[:500] for command in trial["cmds"])
            + "\n```\n</details>\n"
        )
        md.append(
            "<details><summary>final answer to the user</summary>\n\n"
            + trial["final"].strip()
            + "\n\n</details>\n"
        )
md += [
    f"## {report_content.result_heading}\n",
    f"**{result}**\n",
    BOUNDARY + "\n",
]
markdown = "\n".join(md)

# ---------- HTML ----------
esc = html.escape


def card(trial):
    cls = trial["verdict"].lower()
    if SELF_REPORTED:
        evidence = "\n\n".join(trial["cmds"]) or "(no self-reported actions)"
    else:
        evidence = "\n\n".join("$ " + command for command in trial["cmds"]) or "(no commands)"
    acts = (
        ""
        if trial["actions"] == "-"
        else f'<p class="acts">{esc(trial["actions"])}</p>'
    )
    return (
        f'<article class="trial">'
        f'<p class="trial-head"><span class="badge {cls}">{trial["verdict"]}'
        f"</span><strong>{esc(trial['name'])}</strong></p>{acts}"
        f"<details><summary>{'self-reported actions' if SELF_REPORTED else 'Commands the agent ran'} "
        f"({len(trial['cmds'])})</summary><pre>{esc(evidence)}</pre></details>"
        f"<details {'open' if MODE == 'review' else ''}>"
        f"<summary>Final answer to the user</summary>"
        f"<pre>{esc(trial['final'].strip())}</pre></details></article>"
    )


cols = ""
for name, label, variant in (
    ("before", "Before", report.variants.before),
    ("after", "After", report.variants.after),
):
    cols += (
        f'<section class="col"><header class="col-head"><h2>{label}</h2>'
        f'<span class="col-note">{esc(variant.note)}</span></header>'
        f'<p class="count">{esc(variant.count_text)}</p>'
        + "".join(card(trial) for trial in variants[name]["trials"])
        + "</section>"
    )

diff_html = "".join(
    f'<span class="{"d-add" if l.startswith("+") else "d-del" if l.startswith("-") else "d-ctx"}">{esc(l)}</span>\n'
    for l in rule_diff.rstrip().splitlines()
)

shared_html = "".join(
    f'<div class="fstep shared"><span>{esc(step_text(k))}</span>'
    f'<span class="fcount">before {nb}/{nb} · after {na}/{na}</span></div>'
    f'<div class="fline"></div>'
    for k in shared
)


def lane(steps, cls):
    boxes = []
    for i, s in enumerate(steps):
        if i:
            boxes.append('<div class="farrow">↓</div>')
        boxes.append(f'<div class="fstep {cls}"><span>{esc(step_text(s))}</span></div>')
    return "".join(boxes)


def branch_html(prefix, paths, n, cls):
    h = ""
    if not paths:
        body = (
            lane(prefix, cls) or '<p class="fnote">(same steps as the shared flow)</p>'
        )
        return (
            f'<div class="fbranch"><p class="fpath-head">all {n} trials</p>{body}</div>'
        )
    if prefix:
        h += f'<p class="fpath-head">all {n} trials</p>' + lane(prefix, cls)
        h += '<div class="farrow">↓</div>'
    h += f'<div class="fsplit">splits into {len(paths)} paths</div>'
    lanes = "".join(
        f'<div class="fpath"><p class="fpath-head">{cnt} of {n} trials</p>'
        f"{lane(path, cls)}</div>"
        for path, cnt in paths
    )
    h += (
        f'<div class="fpaths" '
        f'style="grid-template-columns:repeat({len(paths)},1fr)">'
        f"{lanes}</div>"
    )
    return f'<div class="fbranch">{h}</div>'


if same_flow:
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
        f"{branch_html(bprefix, bpaths, nb, 'b')}</div>"
        f'<div><p class="fork-side">AFTER</p>'
        f"{branch_html(aprefix, apaths, na, 'a')}</div>"
        f"</div></div>"
    )


def dec_choices(brs, n, cls):
    lines = []
    for br in brs:
        cnt = "" if br["n"] == n else f' <span class="fcount">{br["n"]}/{n}</span>'
        lines.append(f'<div class="dline">{esc(br["choice"])}{cnt}</div>')
    return f'<div class="fstep {cls} dcell">' + ("".join(lines) or "—") + "</div>"


def dec_label(i, row, fork):
    when = (
        '<span class="dwhen">in the final answer</span>'
        if row.get("anchor") == "answer"
        else '<span class="dwhen">during the work</span>'
    )
    if i == fork:
        tag = '<span class="dtag">root change</span>'
    elif not row["diverges"]:
        tag = '<span class="dtag dtag-same">same</span>'
    elif fork and i > fork:
        tag = '<span class="dwhen">downstream</span>'
    else:
        tag = ""
    tag += when
    title = row.get("topic") or row["decision"]
    sub = row["decision"] if row.get("topic") else ""
    if row.get("note"):
        sub = f"{sub} — {row['note']}" if sub else row["note"]
    note = f'<span class="dnote">{esc(sub)}</span>' if sub else ""
    return f'<p class="dq dspan">{i} · {esc(title)}{tag}{note}</p>'


dec_html = ""
if dec.get("chain"):
    fork = dec.get("fork")
    lead_n = 0
    for row in dec["chain"]:
        if row["diverges"]:
            break
        lead_n += 1
    parts = []
    for i, row in enumerate(dec["chain"][:lead_n], 1):
        bs = branch_str(row["before"], dnb)
        as_ = branch_str(row["after"], dna)
        choice = bs if bs == as_ else f"before: {bs} · after: {as_}"
        parts.append(dec_label(i, row, fork))
        parts.append(
            f'<div class="fstep shared"><span>{esc(choice)}</span>'
            f'<span class="fcount">before {dnb}/{dnb} · '
            f"after {dna}/{dna}</span></div>"
        )
        parts.append('<div class="fline"></div>')
    rest = dec["chain"][lead_n:]
    if rest:
        parts.append('<div class="fork-label">paths diverge here</div>')
        grid = ['<p class="fork-side">BEFORE</p><p class="fork-side">AFTER</p>']
        for j, row in enumerate(rest):
            i = lead_n + j + 1
            if j:
                grid.append('<div class="farrow">↓</div><div class="farrow">↓</div>')
            grid.append(dec_label(i, row, fork))
            if row["diverges"]:
                grid.append(dec_choices(row["before"], dnb, "b"))
                grid.append(dec_choices(row["after"], dna, "a"))
            else:
                grid.append(
                    '<div class="fstep shared dspan"><span>'
                    + esc(branch_str(row["before"], dnb))
                    + "</span></div>"
                )
        parts.append(f'<div class="dgrid">{"".join(grid)}</div>')
    foot = content.decision_footer(report.decisions.rows, report.decisions.fork)
    if report.decisions.fork_note:
        foot += " " + report.decisions.fork_note
    if report.decisions.dropped:
        foot += " " + content.dropped_rows(report.decisions.dropped)
    dec_html = (
        f'<p class="section-label">{esc(report_content.decision_heading)}</p>'
        f'<p class="sub">{esc(dec_blurb)}</p>'
        f'<div class="flow">{"".join(parts)}</div>'
        f'<p class="fnote dfoot">{esc(foot)}</p>'
    )

flow_section = ""
if not SELF_REPORTED:
    flow_section = (
        f'<p class="section-label">{esc(report_content.flow_heading)}</p>'
        + (
            "<p class=\"sub\">Steps are described from the agents' actual commands. "
            "A path is a sequence at least one trial literally took — arrows "
            "connect steps inside a path, and a split shows where trials went "
            "different ways. Full commands are in the trial cards below.</p>"
        )
        + flow_html
    )
    if dec_html:
        flow_section = (
            '<details class="flowfold"><summary>'
            + content.flow_fold_summary()
            + "</summary>"
            + flow_section
            + "</details>"
        )

obs_html = f'<p class="obs">{esc(obs_md)}</p>' if obs_md else ""

expected_html = (
    ""
    if not EXPECTED
    else (
        f'<p class="section-label">{esc(report_content.expected_heading)}</p>'
        f'<p class="sub">{esc(EXPECTED)}</p>'
    )
)
result_bg = {"good": "var(--pass)", "bad": "var(--fail)", "neutral": "var(--accent)"}[
    result_kind
]

body = f"""<title>{esc(TITLE)}</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
:root {{
  --ground:#f6f8f9; --panel:#ffffff; --ink:#1c2733; --muted:#5b6b7a;
  --border:#d9e1e7; --accent:#0b6e75; --accent-soft:#e3f0f1;
  --pass:#1a7f37; --fail:#cf222e; --blocked:#6e7781;
  --pass-soft:#e8f3ea; --fail-soft:#fbebec;
  --code-bg:#eef2f4; --d-add:#1a7f37; --d-del:#cf222e;
}}
body {{ background:var(--ground); color:var(--ink);
  font:15px/1.55 "IBM Plex Sans", -apple-system, "Segoe UI", sans-serif;
  max-width:1080px; margin:0 auto; padding:2.5rem 1.25rem 3rem; }}
h1 {{ font-size:1.7rem; font-weight:700; letter-spacing:-.01em;
  margin:0 0 .2rem; text-wrap:balance; }}
h2 {{ font-size:1.02rem; font-weight:600; margin:0; }}
.section-label {{ font-size:.72rem; font-weight:600; letter-spacing:.09em;
  text-transform:uppercase; color:var(--accent); margin:2rem 0 .5rem; }}
.sub {{ color:var(--muted); margin:.2rem 0 0; max-width:62ch; }}
pre {{ background:var(--code-bg); border:1px solid var(--border);
  border-radius:6px; padding:.7rem .85rem; overflow-x:auto;
  white-space:pre-wrap; margin:.5rem 0 0;
  font:12.5px/1.55 "IBM Plex Mono", ui-monospace, monospace; }}
.scenario {{ background:var(--panel); border:1px solid var(--border);
  border-left:3px solid var(--accent); border-radius:6px;
  padding:.85rem 1rem; max-width:62ch; white-space:pre-wrap; margin:0;
  font:13.5px/1.6 "IBM Plex Mono", ui-monospace, monospace; }}
.flow {{ max-width:760px; margin:.4rem auto 0; }}
.fstep {{ display:flex; justify-content:space-between; align-items:baseline;
  gap:1rem; background:var(--panel); border:1px solid var(--border);
  border-radius:6px; padding:.5rem .8rem; }}
.fstep.b {{ background:var(--fail-soft); border-color:var(--fail); }}
.fstep.a {{ background:var(--pass-soft); border-color:var(--pass); }}
.fcount {{ color:var(--muted); font-size:.8rem; white-space:nowrap;
  font-variant-numeric:tabular-nums; }}
.fline {{ width:2px; height:.7rem; background:var(--border); margin:0 auto; }}
.farrow {{ text-align:center; color:var(--muted); font-size:.85rem;
  line-height:1.4; }}
.fsplit {{ text-align:center; color:var(--muted); font-size:.7rem;
  letter-spacing:.08em; text-transform:uppercase; margin:.2rem 0 .35rem; }}
.fpaths {{ display:grid; gap:.7rem; align-items:start; }}
.fpath {{ min-width:0; }}
.fpath-head {{ text-align:center; font-size:.75rem; font-weight:600;
  color:var(--muted); margin:0 0 .3rem;
  font-variant-numeric:tabular-nums; }}
.fnote {{ text-align:center; color:var(--muted); font-size:.85rem; }}
.dgrid {{ display:grid; grid-template-columns:1fr 1fr;
  gap:.45rem .9rem; align-items:stretch; }}
.dspan {{ grid-column:1 / -1; }}
.dq {{ margin:.55rem 0 0; font-weight:600; font-size:.9rem; }}
.dq:first-child {{ margin-top:0; }}
.dnote {{ display:block; font-weight:400; font-size:.82rem;
  color:var(--muted); margin-top:.1rem; }}
.dtag {{ display:inline-block; margin-left:.4rem; font-size:.64rem;
  font-weight:700; letter-spacing:.07em; text-transform:uppercase;
  color:var(--panel); background:var(--accent); border-radius:3px;
  padding:.05rem .3rem; vertical-align:.08rem; }}
.dtag-same {{ background:var(--blocked); }}
.dcell {{ display:block; }}
.dline {{ padding:.05rem 0; }}
.obs {{ background:var(--accent-soft); border-left:3px solid var(--accent);
  border-radius:6px; padding:.6rem .9rem; margin:.8rem 0 0;
  font-weight:600; max-width:72ch; }}
.dwhen {{ margin-left:.45rem; font-size:.72rem; font-weight:400;
  color:var(--muted); letter-spacing:.02em; }}
.flowfold {{ margin-top:2rem; }}
.flowfold > summary {{ font-size:.9rem; font-weight:600; }}
.flowfold .section-label {{ margin-top:.8rem; }}
.dfoot {{ margin:.6rem 0 0; }}
.fork-label {{ text-align:center; color:var(--muted); font-size:.78rem;
  letter-spacing:.08em; text-transform:uppercase; margin:.2rem 0 .6rem; }}
.fork {{ display:grid; grid-template-columns:1fr 1fr; gap:1rem; }}
.fork-side {{ text-align:center; font-size:.75rem; font-weight:700;
  letter-spacing:.08em; color:var(--muted); margin:0 0 .4rem; }}
.fbranch {{ min-width:0; }}
.cols {{ display:grid; grid-template-columns:1fr 1fr; gap:1.1rem;
  margin-top:.5rem; }}
@media (max-width: 780px) {{
  .cols, .fork, .dgrid {{ grid-template-columns:1fr; }} }}
.col {{ background:var(--panel); border:1px solid var(--border);
  border-radius:8px; padding:1rem 1.1rem 1.1rem; min-width:0; }}
.col-head {{ display:flex; align-items:baseline; gap:.6rem; }}
.col-note {{ color:var(--muted); font-size:.85rem; }}
.count {{ margin:.35rem 0 .8rem; color:var(--muted);
  font-variant-numeric:tabular-nums; }}
.trial {{ border-top:1px solid var(--border); padding:.65rem 0 .35rem; }}
.trial-head {{ display:flex; align-items:center; gap:.55rem; margin:0; }}
.acts {{ margin:.25rem 0 .3rem; color:var(--muted); font-size:.92rem; }}
.badge {{ border-radius:4px; padding:1.5px 8px; font-size:11.5px;
  font-weight:700; letter-spacing:.04em; color:#fff; }}
.badge.pass {{ background:var(--pass); }}
.badge.fail {{ background:var(--fail); }}
.badge.blocked {{ background:var(--blocked); }}
.badge.review {{ background:var(--accent); }}
summary {{ cursor:pointer; color:var(--accent); font-size:.86rem;
  margin:.15rem 0; }}
summary:focus-visible {{ outline:2px solid var(--accent);
  outline-offset:2px; }}
details {{ margin-bottom:.25rem; }}
.d-add {{ color:var(--d-add); }} .d-del {{ color:var(--d-del); }}
.d-ctx {{ color:var(--muted); }}
.result {{ background:{result_bg}; color:#fff; border-radius:8px;
  padding:.85rem 1.1rem; font-size:1.15rem; font-weight:700;
  margin-top:.5rem; }}
.footer {{ color:var(--muted); font-size:.85rem; margin-top:1.6rem;
  max-width:70ch; }}
</style>

<h1>{esc(TITLE)}</h1>
<p class="sub">{esc(SUB)}</p>
{obs_html}

<p class="section-label">{esc(report_content.scenario_heading)}</p>
<pre class="scenario">{esc(scenario)}</pre>
{expected_html}

<p class="section-label">{esc(report_content.diff_heading)}</p>
<pre>{diff_html}</pre>

{dec_html}

{flow_section}

<p class="section-label">Trials</p>
<div class="cols">{cols}</div>

<p class="section-label">{esc(report_content.result_heading)}</p>
<div class="result">{esc(result)}</div>

<p class="footer">Simulation evidence from Behavior Diff
(model: {esc(model)}, {b["total"]} trial(s) per variant).
{esc(BOUNDARY)}</p>
"""
document = (
    '<!doctype html><html><head><meta charset="utf-8">'
    '<meta name="viewport" content="width=device-width, initial-scale=1">'
    "</head><body>" + body + "</body></html>"
)
report_json = report.to_json()

(run / "report-data.json").write_text(report_json)
(run / "report.md").write_text(markdown)
(run / "report-artifact.html").write_text(body)
(run / "report.html").write_text(document)

print(
    f"mode {MODE} · BEFORE pass {b['passed']}/{b['valid']} · "
    f"AFTER pass {a['passed']}/{a['valid']} → {result}"
)
print(f"report: {run / 'report.md'}")
print(f"page:   {run / 'report.html'}")
