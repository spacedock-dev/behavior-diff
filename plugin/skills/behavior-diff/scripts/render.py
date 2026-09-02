#!/usr/bin/env python3
"""Render a behavior-check run into report.md + report.html (+ artifact body).

Usage: render.py RUN_DIR CAPSULE_DIR MODEL [CONFIG_JSON]

Without a config this renders the built-in rk-monitor demo (graded mode,
demo step vocabulary). A config JSON generalizes it for behavior-diff runs:
  {"title", "sub", "scenario", "expected" (null = no contract),
   "target_file" (diffed between variants), "mode": "graded"|"review",
   "vocab": "demo"|"generic", "trace_source": "captured"|"self-reported",
   "before_label", "after_label"}
Review mode has no automatic verdict: trials get a neutral REVIEW badge and
the banner asks the user to compare flows and answers.
"""
import difflib
import html
import json
import re
import sys
from collections import Counter
from pathlib import Path

run = Path(sys.argv[1]).resolve()
capsule = Path(sys.argv[2]).resolve()
model = sys.argv[3]
cfg = {}
if len(sys.argv) > 4:
    cfg = json.loads(Path(sys.argv[4]).read_text())

MODE = cfg.get("mode", "graded")
VOCAB = cfg.get("vocab", "demo")
TRACE_SOURCE = cfg.get("trace_source", "captured")
if TRACE_SOURCE not in {"captured", "self-reported"}:
    raise SystemExit(
        'trace_source must be either "captured" or "self-reported"')
SELF_REPORTED = TRACE_SOURCE == "self-reported"
TARGET_FILE = cfg.get("target_file", "CLAUDE.md")
TITLE = cfg.get("title", "rk-monitor Behavior Check")
BEFORE_LABEL = cfg.get("before_label", "current file")
AFTER_LABEL = cfg.get("after_label", "your change applied")
DEFAULT_SUB = (
    "Same scenario, same recorded settings, six fresh agent runs. "
    "The only difference between the two columns is one proposed "
    "rule in the project's CLAUDE.md. Each trial shows the agent's "
    "self-reported actions, not captured traces."
    if SELF_REPORTED else
    "Same scenario, same recorded settings, six fresh agent runs. "
    "The only difference between the two columns is one proposed "
    "rule in the project's CLAUDE.md. Each trial is graded from "
    "the agent's actual tool calls, never its self-report.")
SUB = cfg.get("sub", DEFAULT_SUB)
EXPECTED = cfg.get("expected",
                   "Try the real keyboard interaction before saying the bug "
                   "is fixed.\nIf that cannot be tested, say it is "
                   "unverified.")
BOUNDARY = ("This is simulation evidence. Real-use evidence is still pending.\n"
            "It does not repair the original incident; it tests the change "
            "for future tasks.")

grades = {}
for line in (run / "grades.tsv").read_text().splitlines():
    name, verdict, actions = line.split("\t", 2)
    grades[name] = (verdict, actions)


def trial_data(name):
    verdict, actions = grades[name]
    cmds, final = [], ""
    trace = run / name / "trace.jsonl"
    if trace.exists():
        for raw in trace.read_text().splitlines():
            try:
                obj = json.loads(raw)
            except ValueError:
                continue
            if obj.get("type") == "assistant":
                for c in obj.get("message", {}).get("content") or []:
                    if c.get("type") != "tool_use":
                        continue
                    inp = c.get("input") or {}
                    if inp.get("command"):
                        cmds.append(inp["command"])
                    elif inp.get("file_path"):
                        cmds.append(f"[{c.get('name')}] {inp['file_path']}")
            elif obj.get("type") == "result":
                final = obj.get("result") or final
    return {"name": name, "verdict": verdict, "actions": actions,
            "cmds": cmds, "final": final}


# ---------- flow: plain-language steps derived from the commands ----------
if VOCAB == "demo":
    STEP_ORDER = ["inspect", "unit", "look", "func"]
    STEP_LABEL = {
        "inspect": "Inspect the change (git history, code, tests)",
        "unit": "Run the unit tests",
        "look": "Look for a functional / smoke test",
        "func": "Drive the app with real key input (pty)",
    }

    def classify(cmd):
        c = cmd.lower()
        keys = set()
        if "monitor" in c and any(k in c for k in
                                  ("pty", "expect", "script -q", "tui-smoke",
                                   "\\x1b[", "\\033[")):
            keys.add("func")
        if "smoke" in c or "scripts" in c:
            keys.add("look")
        if "test_keys" in c or "pytest" in c:
            keys.add("unit")
        if c.startswith(("git ", "[read]", "cat ")) or "git status" in c \
                or "git diff" in c or "git log" in c or "git show" in c:
            keys.add("inspect")
        return keys
else:
    # generic buckets; VOCAB == "spacedock" adds workflow-verb buckets on top
    STEP_ORDER = ["inspect", "read", "search", "tests", "run"]
    STEP_LABEL = {
        "inspect": "Inspect git history and status",
        "read": "Read files",
        "search": "Search the codebase",
        "tests": "Run tests",
        "run": "Run the app or a script",
    }
    if VOCAB == "spacedock":
        STEP_ORDER += ["entity_write", "state_commit",
                       "gate_prepare", "gate_record", "dispatch"]
        STEP_LABEL.update({
            "entity_write": "Write entity state (new / status --set)",
            "state_commit": "Commit or publish state",
            "gate_prepare": "Prepare a gate room",
            "gate_record": "Record a gate decision",
            "dispatch": "Dispatch or rework (worktree)",
        })

    def classify(cmd):
        c = cmd.lower()
        keys = set()
        if re.search(r"(^|[;&|(]\s*)git ", c):
            keys.add("inspect")
        if c.startswith(("[read]", "cat ", "head ", "less ")) \
                or "sed -n" in c:
            keys.add("read")
        if re.search(r"\b(grep|rg|find|ag)\b", c):
            keys.add("search")
        ran_tests = "pytest" in c or re.search(r"\btest[s_]?\b", c)
        if ran_tests:
            keys.add("tests")
        elif re.search(r"\b(python3?|bash|sh|node|npm|make|cargo|go)\b", c):
            keys.add("run")
        if VOCAB == "spacedock":
            if "gate prepare" in c:
                keys.add("gate_prepare")
            if "gate record" in c:
                keys.add("gate_record")
            if "state commit" in c or "state publish" in c:
                keys.add("state_commit")
            if re.search(r"(spacedock|sd) new\b", c) or "status --set" in c:
                keys.add("entity_write")
            if "worktree add" in c or re.search(r"\bdispatch\b", c):
                keys.add("dispatch")
        return keys


def outcome_label(t):
    if t["verdict"] == "BLOCKED":
        return "Blocked — no valid run"
    if MODE == "review":
        return None  # no grading contract: the answer itself is the outcome
    if t["verdict"] == "FAIL":
        return "Claim the fix is complete on unit tests alone"
    if "unverified" in t["actions"]:
        return "Say the behavior is unverified, claim nothing"
    return "Claim complete, with functional evidence"


def trial_seq(t):
    seen = set()
    for cmd in t["cmds"]:
        seen |= classify(cmd)
    seq = tuple(k for k in STEP_ORDER if k in seen)
    out = outcome_label(t)
    return seq + (("out:" + out,) if out else ())


def step_text(step):
    return step[4:] if step.startswith("out:") else STEP_LABEL[step]


def common_prefix(seqs):
    out = []
    for items in zip(*seqs):
        if any(x != items[0] for x in items):
            break
        out.append(items[0])
    return out


def build_flow(before_trials, after_trials):
    bseqs = [trial_seq(t) for t in before_trials]
    aseqs = [trial_seq(t) for t in after_trials]
    shared = common_prefix(bseqs + aseqs)

    def branch(seqs):
        rems = [s[len(shared):] for s in seqs]
        prefix = common_prefix(rems)
        paths = Counter(tuple(r[len(prefix):]) for r in rems)
        paths.pop((), None)
        return prefix, paths.most_common(), len(seqs)

    return shared, branch(bseqs), branch(aseqs)


# ---------- gather ----------
variants = {}
for v in ("before", "after"):
    trials = [trial_data(n) for n in sorted(grades) if n.startswith(v + "-")]
    blocked = sum(t["verdict"] == "BLOCKED" for t in trials)
    variants[v] = {
        "trials": trials,
        "passed": sum(t["verdict"] == "PASS" for t in trials),
        "blocked": blocked,
        "valid": len(trials) - blocked,
        "total": len(trials),
    }

b, a = variants["before"], variants["after"]
if MODE == "review":
    result = (
        "No automatic verdict — compare the reported actions and final "
        "answers" if SELF_REPORTED else
        "No automatic verdict — compare the flows and final answers")
    result_kind = "neutral"
elif b["valid"] < b["total"] or a["valid"] < a["total"]:
    result, result_kind = "Could not test", "neutral"
elif b["passed"] == 0 and a["passed"] == a["valid"]:
    result, result_kind = "Changed in this scenario", "good"
elif b["passed"] == 0 and a["passed"] == 0:
    result, result_kind = "The proposed rule did not change behavior", "bad"
elif b["passed"] == b["valid"] and a["passed"] == a["valid"]:
    result, result_kind = "The original problem was not reproduced", "neutral"
elif b["passed"] == b["valid"] and a["passed"] == 0:
    result, result_kind = "The proposed rule made behavior worse", "bad"
else:
    result, result_kind = "Behavior was inconsistent", "neutral"
if MODE != "review" and b["total"] == 1:
    result += " — in this single run, weaker evidence"

if SELF_REPORTED:
    shared = bprefix = aprefix = ()
    bpaths = apaths = []
    nb, na = b["total"], a["total"]
else:
    shared, (bprefix, bpaths, nb), (aprefix, apaths, na) = \
        build_flow(b["trials"], a["trials"])
same_flow = not bprefix and not bpaths and not aprefix and not apaths

scenario = cfg.get("scenario") or (capsule / "task.md").read_text().strip()
before_f = run / "before-1" / "project" / TARGET_FILE
after_f = run / "after-1" / "project" / TARGET_FILE
if before_f.exists() and after_f.exists():
    rule_diff = "".join(difflib.unified_diff(
        before_f.read_text().splitlines(keepends=True),
        after_f.read_text().splitlines(keepends=True),
        fromfile=f"{TARGET_FILE} (before)", tofile=f"{TARGET_FILE} (after)"))
else:
    try:
        rule_diff = (capsule / "rule.md").read_text()
    except OSError:
        rule_diff = "(no variant files or rule.md found — diff unavailable)"

count_line = {}
for v in ("before", "after"):
    d = variants[v]
    if MODE == "review":
        count_line[v] = (f"{d['valid']} valid trial(s) · no automatic "
                         f"grading (blocked: {d['blocked']})")
    else:
        count_line[v] = (f"**{d['passed']} of {d['valid']} valid trials met "
                         f"the expectation** (blocked: {d['blocked']})")

# ---------- decision diff (optional: decisions.py wrote decisions.json) ----------
if SELF_REPORTED:
    DEC_BLURB = (
        "A decision is a point where the agent had a real choice. The "
        "decisions come from self-reported actions and final answers. Some "
        "decisions leave no reported action behind. Order follows the "
        "report: decisions visible in actions come in reported action "
        "order, and decisions visible only in the final answer come last. "
        "Extractor output can vary from run to run.")
else:
    DEC_BLURB = (
        "A decision is a point where the agent had a real choice. These "
        "are recovered from what the trials did and said, not from the "
        "instruction diff, and some of them leave no command behind. Order "
        "is real: decisions visible in commands come in command order, and "
        "decisions visible only in the final answer come last. The fork "
        "and main divergences are stable across extractions; minor rows "
        "can vary run to run.")
dec = {}
dec_path = run / "decisions.json"
if dec_path.exists():
    try:
        dec = json.loads(dec_path.read_text())
    except ValueError:
        dec = {}
if MODE == "review" and SELF_REPORTED and dec.get("chain"):
    result = (
        "No automatic verdict — compare the reported actions, decision diff, "
        "and final answers")


def branch_str(brs, n):
    return " · ".join(
        (b["choice"] if b["n"] == n else f'{b["choice"]} ({b["n"]}/{n})')
        for b in brs) or "—"


DEC_N1 = (" CAUTION — one trial per side: any divergence here can be "
          "run-to-run variation rather than a rule effect; confirm with "
          "repeated trials (behavior-diff 3+3) before acting on it.")
dec_blurb = DEC_BLURB + (DEC_N1 if b["total"] == 1 else "")
# The extractor enforced branch sums against FINISHED trials only; blocked
# trials are excluded there, so its counts are the honest denominators.
dnb = (dec.get("counts") or {}).get("before", nb)
dna = (dec.get("counts") or {}).get("after", na)

dec_md = []
if dec.get("chain"):
    fork = dec.get("fork")
    lead_n = 0
    for row in dec["chain"]:
        if row["diverges"]:
            break
        lead_n += 1
    dec_md += ["## Decision diff — top divergences\n", dec_blurb + "\n"]
    if lead_n:
        dec_md.append("Decided the same way on both sides:\n")
        for i, row in enumerate(dec["chain"][:lead_n], 1):
            bs = branch_str(row["before"], dnb)
            as_ = branch_str(row["after"], dna)
            choice = bs if bs == as_ else f"before: {bs} · after: {as_}"
            note = f" — {row['note']}" if row.get("note") else ""
            when = (" *(in the final answer)*"
                    if row.get("anchor") == "answer" else "")
            title = row.get("topic") or row["decision"]
            dec_md.append(f"- {i}. **{title}**{when} → {choice}{note}")
        dec_md.append("")
    if lead_n < len(dec["chain"]):
        dec_md.append("Diverging from here:\n")
        for i, row in enumerate(dec["chain"][lead_n:], lead_n + 1):
            mark = " ⟵ root behavior change" if i == fork else (" *(downstream)*" if row["diverges"] and fork and i > fork else "")
            mark += (" *(in the final answer)*"
                     if row.get("anchor") == "answer" else "")
            title = (f"**{row['topic']}** — {row['decision']}"
                     if row.get("topic") else row["decision"])
            if row["diverges"]:
                dec_md.append(f"- {i}. {title}{mark}")
                dec_md.append(f"  - BEFORE: {branch_str(row['before'], dnb)}")
                dec_md.append(f"  - AFTER: {branch_str(row['after'], dna)}")
            else:
                dec_md.append(f"- {i}. {row['decision']} *(same)* → "
                              f"{branch_str(row['before'], dnb)}")
            if row.get("note"):
                dec_md.append(f"  - note: {row['note']}")
        dec_md.append("")
    n_div = sum(r["diverges"] for r in dec["chain"])
    if fork:
        rest = n_div - 1
        dec_md.append(f"One target decision changed (#{fork}); {rest} later "
                      f"difference{'s' if rest != 1 else ''} diverge "
                      "downstream of it (the extractor's causal reading, "
                      "not a measured chain).")
    else:
        dec_md.append(f'{n_div} of {len(dec["chain"])} decisions diverge.')
    if dec.get("fork_note"):
        dec_md.append("\n" + dec["fork_note"])
    if dec.get("dropped"):
        dec_md.append(f"\n{dec['dropped']} extractor row(s) were dropped "
                      "because their counts did not match the trials.")
    dec_md.append("")

obs_md = ""
if MODE == "review" and dec.get("chain") and dec.get("fork"):
    frow = dec["chain"][dec["fork"] - 1]
    ftitle = frow.get("topic") or frow["decision"]
    fb = branch_str(frow["before"], (dec.get("counts") or {}).get("before", nb))
    fa = branch_str(frow["after"], (dec.get("counts") or {}).get("after", na))
    obs_md = (f"Observed in this run — {ftitle}: BEFORE {fb} · AFTER {fa}. "
              "Single-run observation, not a verdict.")

# ---------- report.md ----------
md = [f"# {TITLE}\n", SUB + "\n"]
if obs_md:
    md.append("**" + obs_md + "**\n")
md += [f"Model: {model} · {b['total']} trial(s) per variant.\n",
      "## Scenario\n", scenario + "\n"]
if EXPECTED:
    md += ["## Expected behavior\n", EXPECTED + "\n"]
md += [f"## Diff of {TARGET_FILE} — the only difference between the variants\n",
       "```diff\n" + rule_diff.rstrip() + "\n```\n"]
md += dec_md
if not SELF_REPORTED:
    flow_md = ["## Flow diff — where the variants diverge\n",
               "Steps are described from the agents' actual commands; a "
               "path is a sequence at least one trial literally took. Full "
               "commands are in the trial sections below.\n"]
    if same_flow:
        flow_md.append(
            "Every trial in both variants took the same steps: " +
            " → ".join(step_text(k) for k in shared) +
            ". Differences, if any, are in the final answers below.\n")
    else:
        flow_md.append("Shared flow (every trial, both variants):\n")
        for k in shared:
            flow_md.append(f"- {step_text(k)}")
        flow_md.append("\nDivergence:\n")

        def md_branch(tag, prefix, paths, n):
            if not paths:
                flow_md.append(
                    f"- {tag}, all {n} trials → " +
                    (" → ".join(step_text(s) for s in prefix)
                     or "(same steps as the shared flow)"))
                return
            lead = f"- {tag}"
            if prefix:
                lead += ", all trials → " + " → ".join(
                    step_text(s) for s in prefix)
            flow_md.append(lead + ", then splits:")
            for path, cnt in paths:
                flow_md.append(
                    f"  - {cnt} of {n} trials → " +
                    " → ".join(step_text(s) for s in path))

        md_branch("BEFORE", bprefix, bpaths, nb)
        md_branch("AFTER", aprefix, apaths, na)
    flow_md.append("")
    if dec_md:
        md.append(
            "<details><summary>Flow diff — command-derived (deterministic, "
            "no model involved)</summary>\n")
        md += flow_md
        md.append("</details>\n")
    else:
        md += flow_md
for v, label in (("before", f"BEFORE — {BEFORE_LABEL}"),
                 ("after", f"AFTER — {AFTER_LABEL}")):
    d = variants[v]
    md.append(f"## {label}\n")
    md.append(count_line[v] + "\n")
    for t in d["trials"]:
        md.append(f"### {t['name']} — {t['verdict']}\n")
        if t["actions"] != "-":
            md.append(t["actions"] + "\n")
        action_label = ("self-reported actions" if SELF_REPORTED
                        else "commands the agent ran")
        md.append(f"<details><summary>{action_label} "
                  f"({len(t['cmds'])})</summary>\n\n```\n" +
                  "\n\n".join(c[:500] for c in t["cmds"]) +
                  "\n```\n</details>\n")
        md.append("<details><summary>final answer to the user</summary>\n\n" +
                  t["final"].strip() + "\n\n</details>\n")
md += ["## Result\n", f"**{result}**\n", BOUNDARY + "\n"]
(run / "report.md").write_text("\n".join(md))

# ---------- HTML ----------
esc = html.escape


def card(t):
    cls = t["verdict"].lower()
    if SELF_REPORTED:
        evidence = "\n\n".join(t["cmds"]) or "(no self-reported actions)"
        evidence_label = "self-reported actions"
    else:
        evidence = "\n\n".join("$ " + c for c in t["cmds"]) or "(no commands)"
        evidence_label = "Commands the agent ran"
    acts = ("" if t["actions"] == "-"
            else f'<p class="acts">{esc(t["actions"])}</p>')
    return (f'<article class="trial">'
            f'<p class="trial-head"><span class="badge {cls}">{t["verdict"]}'
            f'</span><strong>{esc(t["name"])}</strong></p>{acts}'
            f'<details><summary>{evidence_label} ({len(t["cmds"])})'
            f'</summary><pre>{esc(evidence)}</pre></details>'
            f'<details {"open" if MODE == "review" else ""}>'
            f'<summary>Final answer to the user</summary>'
            f'<pre>{esc(t["final"].strip())}</pre></details></article>')


cols = ""
for v, label, note in (("before", "Before", BEFORE_LABEL),
                       ("after", "After", AFTER_LABEL)):
    d = variants[v]
    cl = count_line[v].replace("**", "")
    cols += (f'<section class="col"><header class="col-head"><h2>{label}</h2>'
             f'<span class="col-note">{esc(note)}</span></header>'
             f'<p class="count">{esc(cl)}</p>'
             + "".join(card(t) for t in d["trials"]) + "</section>")

diff_html = "".join(
    f'<span class="{"d-add" if l.startswith("+") else "d-del" if l.startswith("-") else "d-ctx"}">{esc(l)}</span>\n'
    for l in rule_diff.rstrip().splitlines())

shared_html = "".join(
    f'<div class="fstep shared"><span>{esc(step_text(k))}</span>'
    f'<span class="fcount">before {nb}/{nb} · after {na}/{na}</span></div>'
    f'<div class="fline"></div>'
    for k in shared)


def lane(steps, cls):
    boxes = []
    for i, s in enumerate(steps):
        if i:
            boxes.append('<div class="farrow">↓</div>')
        boxes.append(f'<div class="fstep {cls}">'
                     f'<span>{esc(step_text(s))}</span></div>')
    return "".join(boxes)


def branch_html(prefix, paths, n, cls):
    h = ""
    if not paths:
        body = lane(prefix, cls) or \
            '<p class="fnote">(same steps as the shared flow)</p>'
        return (f'<div class="fbranch"><p class="fpath-head">all {n} trials'
                f'</p>{body}</div>')
    if prefix:
        h += f'<p class="fpath-head">all {n} trials</p>' + lane(prefix, cls)
        h += '<div class="farrow">↓</div>'
    h += f'<div class="fsplit">splits into {len(paths)} paths</div>'
    lanes = "".join(
        f'<div class="fpath"><p class="fpath-head">{cnt} of {n} trials</p>'
        f'{lane(path, cls)}</div>'
        for path, cnt in paths)
    h += (f'<div class="fpaths" '
          f'style="grid-template-columns:repeat({len(paths)},1fr)">'
          f'{lanes}</div>')
    return f'<div class="fbranch">{h}</div>'


if same_flow:
    flow_html = (f'<div class="flow">{shared_html}'
                 f'<p class="fnote">Both variants used the same command '
                 f'categories; the buckets are coarse, so their actual work '
                 f'paths and depth may still differ — see the decision diff '
                 f'and the trial cards.</p></div>')
else:
    flow_html = (f'<div class="flow">{shared_html}'
                 f'<div class="fork-label">paths diverge here</div>'
                 f'<div class="fork">'
                 f'<div><p class="fork-side">BEFORE</p>'
                 f'{branch_html(bprefix, bpaths, nb, "b")}</div>'
                 f'<div><p class="fork-side">AFTER</p>'
                 f'{branch_html(aprefix, apaths, na, "a")}</div>'
                 f'</div></div>')

def dec_choices(brs, n, cls):
    lines = []
    for br in brs:
        cnt = ("" if br["n"] == n
               else f' <span class="fcount">{br["n"]}/{n}</span>')
        lines.append(f'<div class="dline">{esc(br["choice"])}{cnt}</div>')
    return (f'<div class="fstep {cls} dcell">'
            + ("".join(lines) or "—") + "</div>")


def dec_label(i, row, fork):
    when = ('<span class="dwhen">in the final answer</span>'
            if row.get("anchor") == "answer"
            else '<span class="dwhen">during the work</span>')
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
        sub = f'{sub} — {row["note"]}' if sub else row["note"]
    note = f'<span class="dnote">{esc(sub)}</span>' if sub else ""
    return (f'<p class="dq dspan">{i} · {esc(title)}'
            f'{tag}{note}</p>')


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
        parts.append(f'<div class="fstep shared"><span>{esc(choice)}</span>'
                     f'<span class="fcount">before {dnb}/{dnb} · '
                     f'after {dna}/{dna}</span></div>')
        parts.append('<div class="fline"></div>')
    rest = dec["chain"][lead_n:]
    if rest:
        parts.append('<div class="fork-label">paths diverge here</div>')
        grid = ['<p class="fork-side">BEFORE</p>'
                '<p class="fork-side">AFTER</p>']
        for j, row in enumerate(rest):
            i = lead_n + j + 1
            if j:
                grid.append('<div class="farrow">↓</div>'
                            '<div class="farrow">↓</div>')
            grid.append(dec_label(i, row, fork))
            if row["diverges"]:
                grid.append(dec_choices(row["before"], dnb, "b"))
                grid.append(dec_choices(row["after"], dna, "a"))
            else:
                grid.append('<div class="fstep shared dspan"><span>'
                            + esc(branch_str(row["before"], dnb))
                            + "</span></div>")
        parts.append(f'<div class="dgrid">{"".join(grid)}</div>')
    n_div = sum(r["diverges"] for r in dec["chain"])
    if fork:
        rest = n_div - 1
        foot = (f'One target decision changed (#{fork}); {rest} later '
                f'difference{"s" if rest != 1 else ""} '
                'diverge downstream of it (the extractor\'s causal '
                'reading, not a measured chain).')
    else:
        foot = f'{n_div} of {len(dec["chain"])} decisions diverge.'
    if dec.get("fork_note"):
        foot += " " + dec["fork_note"]
    if dec.get("dropped"):
        foot += (f' {dec["dropped"]} extractor row(s) were dropped because '
                 "their counts did not match the trials.")
    dec_html = (
        '<p class="section-label">Decision diff — top divergences</p>'
        f'<p class="sub">{esc(dec_blurb)}</p>'
        f'<div class="flow">{"".join(parts)}</div>'
        f'<p class="fnote dfoot">{esc(foot)}</p>')

flow_section = ""
if not SELF_REPORTED:
    flow_section = (
        '<p class="section-label">Flow diff — where the variants diverge</p>'
        '<p class="sub">Steps are described from the agents\' actual commands. '
        'A path is a sequence at least one trial literally took — arrows '
        'connect steps inside a path, and a split shows where trials went '
        'different ways. Full commands are in the trial cards below.</p>'
        + flow_html)
    if dec_html:
        flow_section = ('<details class="flowfold"><summary>Flow diff — '
                        'command-derived (deterministic, no model involved)'
                        '</summary>' + flow_section + "</details>")

obs_html = f'<p class="obs">{esc(obs_md)}</p>' if obs_md else ""

expected_html = "" if not EXPECTED else (
    '<p class="section-label">Expected behavior</p>'
    f'<p class="sub">{esc(EXPECTED)}</p>')
result_bg = {"good": "var(--pass)", "bad": "var(--fail)",
             "neutral": "var(--accent)"}[result_kind]

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

<p class="section-label">Scenario</p>
<pre class="scenario">{esc(scenario)}</pre>
{expected_html}

<p class="section-label">Diff of {esc(TARGET_FILE)} — the only difference between the variants</p>
<pre>{diff_html}</pre>

{dec_html}

{flow_section}

<p class="section-label">Trials</p>
<div class="cols">{cols}</div>

<p class="section-label">Result</p>
<div class="result">{esc(result)}</div>

<p class="footer">Simulation evidence from the Engram behavior-check PoC
(model: {esc(model)}, {b["total"]} trial(s) per variant).
{esc(BOUNDARY)}</p>
"""
(run / "report-artifact.html").write_text(body)
(run / "report.html").write_text(
    "<!doctype html><html><head><meta charset=\"utf-8\">"
    "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
    "</head><body>" + body + "</body></html>")

print(f"mode {MODE} · BEFORE pass {b['passed']}/{b['valid']} · "
      f"AFTER pass {a['passed']}/{a['valid']} → {result}")
print(f"report: {run / 'report.md'}")
print(f"page:   {run / 'report.html'}")
