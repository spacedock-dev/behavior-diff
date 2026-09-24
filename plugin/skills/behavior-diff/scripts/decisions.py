#!/usr/bin/env python3
"""Decision diff for a Behavior Diff run. It shows what agents CHOSE, not
what they typed.

Usage: decisions.py RUN_DIR [--agent codex|claude|pi|omp] [--model NAME]
       decisions.py RUN_DIR --emit-prompt
       decisions.py RUN_DIR --ingest FILE [--extractor-label LABEL]

Defaults: codex with gpt-5.6-terra when the codex CLI is present, else
claude -p with sonnet. --agent pins one extractor (no cross-fallback).
Pi and OMP require --model; --model overrides the Claude or Codex default.

--emit-prompt prints the extraction prompt so a caller can run the model
call itself (the live skill hands it to an in-session subagent);
--ingest validates that extractor's raw reply through the same
extract_json/normalize path and writes decisions.json, exiting nonzero
when the reply yields no usable chain. Neither mode touches the CLI
extractors; the plain RUN_DIR invocation is unchanged.

The command-derived flow diff in render.py classifies commands into a fixed
bucket list, so it is blind twice over: an unfamiliar toolchain matches no
bucket (a C `cc` invocation scores as no step at all), and decisions that
leave no command behind (verdict shape, what the agent chose to withhold)
are invisible by construction.

This pass reads each trial's final answer plus its numbered evidence entries
and asks one model call to recover the ordered decision chain: the points where
a reviewer had a choice, and which branch each trial took. Output is
decisions.json, which render.py renders if present. Without it, captured runs
keep their command-derived flow, while self-reported runs keep the raw actions
and final answers without inventing a flow.

The extractor is NOT shown the instruction-file diff. Axes have to be
discovered from the supplied trial evidence, or the diff just grades the run
against whatever the author hoped the rule would do.
"""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SOURCE_TERMS = {
    "captured": {
        "source_note": "The numbered entries come from captured tool calls.",
        "schema_noun": "command",
        "entry_heading": "commands it ran:",
        "anchor_noun": "command",
        "decision_clause": (
            "A decision is not a command; some decisions leave no command"
        ),
        "evidence_clause": "what the trials actually did and said",
    },
    "self-reported": {
        "source_note": (
            "The numbered entries are self-reported actions, not captured tool calls."
        ),
        "schema_noun": "action",
        "entry_heading": "reported actions:",
        "anchor_noun": "action",
        "decision_clause": (
            "A decision is not an action; some decisions leave no action"
        ),
        "evidence_clause": "the reported actions and final answers",
    },
}

SCHEMA = """{{
  "chain": [
    {{"topic": "<2-4 plain words naming the observed result or behavior>",
     "decision": "<the choice available, phrased as a question>",
     "anchor": <earliest $N {schema_noun} number where it shows, or "answer">,
     "before": [{{"choice": "<branch taken>", "n": <trials>}}],
     "after":  [{{"choice": "<branch taken>", "n": <trials>}}],
     "diverges": true|false,
     "note": "<optional: one short clause, only if worth saying>"}}
  ],
  "fork": <1-based index into chain of the FIRST divergence, or null>,
  "fork_note": "<one possible explanation linking the first difference to later differences, or null>",
  "outcome": <1-based index of the primary task outcome in chain, or null>,
  "implications": [
    {{"text": "<one supported practical implication or risk>",
      "decisions": [<1-based indexes of the supporting chain rows>]}}
  ]
}}"""

PROMPT = """You are comparing two sets of agent trials. Every trial got the
same task in the same repo. The BEFORE trials and AFTER trials differ by one
edit to an instruction file. You are NOT told what that edit was — do not
guess at it, and do not assume either side is correct.

Task the agents were given:
{task}

Evidence source:
{source_note}

{trials}

Recover the DECISION CHAIN. A decision is a point where the agent had a real
choice and picked a branch: how to establish that something is true, which
inputs to check, what shape the answer takes, whether to report or withhold a
particular thing. {decision_clause} at all, and those matter most here.

Rules:
- Discover the decisions from {evidence_clause}. Do not work from a checklist
  of what you think the instruction edit was about.
- Anchor each decision to WHEN it is made: if any {anchor_noun} shows it, set
  "anchor" to the earliest $N {anchor_noun} number where it shows (in any
  trial); if it only shows in the final answer, set "anchor" to "answer".
- Order the chain by that anchor: {anchor_noun}-anchored decisions in
  {anchor_noun} order, then the answer-anchored ones in the order their
  evidence appears in the answers. Mark each with "diverges".
- Within one variant, trials may split. List each branch with its trial count.
  Counts per variant must sum to that variant's trial count.
- Phrase each "decision" as the open question, neutrally, so it reads the same
  for both sides: "How is correctness established?" not "Did it compile?".
- "topic" is a short observation label for a comparison table: "Review verdict",
  "Records inspected", "Payment-history check", or another label supported by
  this task. Use 2-4 plain words, not a question or an instruction.
- Keep "choice" under about 60 characters. Describe what happened, not what the
  agent should do. Do not imply intent, concealment, or skipped work without evidence.
- 6 to 10 decisions. Drop anything trivial.
- "fork" is the first diverging decision that can help explain later differences.
  Use null if the evidence supports no such link. Order alone does not prove a link.
- "fork_note" is a possible model explanation, not a proven cause. Use cautious
  language such as "can explain" rather than "determines" or "causes".
- Set "outcome" to the decision that records the task's primary result, not its
  process or wording. It can have a numbered anchor or an answer anchor.
  If the evidence does not establish a primary result, use null.
- Explain practical implications only when the supplied evidence supports them.
  Cite every supporting decision by its 1-based chain index. Return an empty
  "implications" list when no implication is supported.
- Keep observations separate from interpretation. An approval in a final answer
  does not prove that a payment occurred. A reported action is not a verified action.
  Do not invent risks, expected outcomes, success criteria, or facts from unread files.
- Counts describe each decision separately. Do not invent a per-trial path by
  combining counts from different rows. Do not treat a changed outcome as success.

Return ONLY JSON, no prose and no code fence, in exactly this shape:
{schema}"""


def trials_of(run):
    out = {}
    for d in sorted(p for p in run.iterdir() if p.is_dir()):
        trace = d / "trace.jsonl"
        if not trace.exists() or "-" not in d.name:
            continue
        variant = d.name.rsplit("-", 1)[0]
        if variant not in ("before", "after"):
            continue
        cmds, final = [], ""
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
        if final:
            out.setdefault(variant, []).append(
                {"name": d.name, "cmds": cmds, "final": final}
            )
    return out


def render_trials(trials, entry_heading):
    blocks = []
    for variant in ("before", "after"):
        for t in trials.get(variant, []):
            cmds = (
                "\n".join(f"  ${i}: " + c[:400] for i, c in enumerate(t["cmds"], 1))
                or "  (none)"
            )
            blocks.append(
                f"=== {t['name']} ({variant.upper()}) ===\n"
                f"{entry_heading}\n{cmds}\n"
                f"final answer it gave:\n{t['final'].strip()}\n"
            )
    return "\n".join(blocks)


TRACE_SOURCE_ERROR = 'trace_source must be either "captured" or "self-reported"'


def source_terms(run):
    """Return prompt terms from explicit or defaulted trace provenance."""
    config_path = run / "config.json"
    try:
        raw_config = config_path.read_text()
    except FileNotFoundError:
        config = {}
    except OSError:
        raise SystemExit(TRACE_SOURCE_ERROR) from None
    else:
        try:
            config = json.loads(raw_config)
        except ValueError:
            raise SystemExit(TRACE_SOURCE_ERROR) from None
    if not isinstance(config, dict):
        raise SystemExit(TRACE_SOURCE_ERROR)
    trace_source = config.get("trace_source", "captured")
    if not isinstance(trace_source, str) or trace_source not in SOURCE_TERMS:
        raise SystemExit(TRACE_SOURCE_ERROR)
    return SOURCE_TERMS[trace_source]


def source_note(run):
    """Describe whether numbered trial entries are captured or self-reported."""
    return source_terms(run)["source_note"]


def normalize(data, counts):
    """Validate counts and remap evidence references after sorting or dropping rows."""
    if type(data) is not dict or type(data.get("chain", [])) is not list:
        raise ValueError("expected a decision chain")
    chain, dropped = [], 0
    for pos, row in enumerate(data.get("chain", [])):
        if (
            type(row) is not dict
            or type(row.get("decision")) is not str
            or not row["decision"].strip()
        ):
            dropped += 1
            continue
        anchor = row.get("anchor")
        clean = {
            "decision": row["decision"].strip(),
            "topic": str(row.get("topic") or "").strip(),
            "anchor": anchor if type(anchor) is int and anchor >= 1 else "answer",
            "_pos": pos,
            "note": str(row.get("note") or "").strip(),
        }
        for variant in ("before", "after"):
            branches = row.get(variant)
            if type(branches) is not list or not branches:
                break
            choices = {}
            for branch in branches:
                if (
                    type(branch) is not dict
                    or type(branch.get("choice")) is not str
                    or not branch["choice"].strip()
                    or type(branch.get("n")) is not int
                    or branch["n"] <= 0
                    or branch["choice"].strip() in choices
                ):
                    break
                choices[branch["choice"].strip()] = branch["n"]
            else:
                if sum(choices.values()) == counts.get(variant, 0):
                    clean[variant] = [
                        {"choice": choice, "n": count}
                        for choice, count in choices.items()
                    ]
                    continue
            break
        else:
            before = {b["choice"]: b["n"] for b in clean["before"]}
            after = {b["choice"]: b["n"] for b in clean["after"]}
            clean["diverges"] = any(
                before.get(choice, 0) * counts["after"]
                != after.get(choice, 0) * counts["before"]
                for choice in before.keys() | after.keys()
            )
            chain.append(clean)
            continue
        dropped += 1
    chain.sort(
        key=lambda row: (
            (0, row["anchor"], row["_pos"])
            if type(row["anchor"]) is int
            else (1, 0, row["_pos"])
        )
    )
    positions = {row.pop("_pos") + 1: index for index, row in enumerate(chain, 1)}
    raw_fork = data.get("fork")
    fork = positions.get(raw_fork) if type(raw_fork) is int else None
    if fork is not None and not chain[fork - 1]["diverges"]:
        fork = None
    raw_outcome = data.get("outcome")
    outcome = positions.get(raw_outcome) if type(raw_outcome) is int else None
    implications = []
    raw_implications = data.get("implications", [])
    for claim in raw_implications if type(raw_implications) is list else []:
        if type(claim) is not dict:
            continue
        text, references = claim.get("text"), claim.get("decisions")
        if (
            type(text) is not str
            or not text.strip()
            or type(references) is not list
            or not references
            or any(type(ref) is not int or ref not in positions for ref in references)
            or len(set(references)) != len(references)
        ):
            continue
        implications.append(
            {"text": text.strip(), "decisions": [positions[ref] for ref in references]}
        )
    return {
        "chain": chain,
        "fork": fork,
        "dropped": dropped,
        "fork_note": str(data.get("fork_note") or "").strip() if fork else "",
        "outcome": outcome,
        "implications": implications,
    }


def extract_json(text):
    text = re.sub(r"^\s*```(?:json)?|```\s*$", "", text.strip())
    start = text.find("{")
    if start < 0:
        raise ValueError("no JSON object in extractor output")
    depth, instr, esc = 0, False, False
    for i, ch in enumerate(text[start:], start):
        if instr:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                instr = False
            continue
        if ch == '"':
            instr = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return json.loads(text[start : i + 1])
    raise ValueError("unbalanced JSON in extractor output")


DEFAULT_MODEL = {"codex": "gpt-5.6-terra", "claude": "sonnet"}


def _codex(prompt, model):
    with tempfile.NamedTemporaryFile("r", suffix=".md") as out:
        proc = subprocess.run(
            [
                "codex",
                "exec",
                "--ephemeral",
                "--skip-git-repo-check",
                "-s",
                "read-only",
                "-m",
                model,
                "-o",
                out.name,
                "-",
            ],
            input=prompt,
            capture_output=True,
            text=True,
        )
        answer = ""
        try:
            answer = open(out.name).read()
        except OSError:
            pass
    if proc.returncode == 0 and "{" in answer:
        return answer
    return None


def _claude(prompt, model):
    proc = subprocess.run(
        ["claude", "-p", prompt, "--model", model, "--allowedTools", ""],
        capture_output=True,
        text=True,
    )
    return proc.stdout if proc.returncode == 0 else None


def _pi(prompt, model):
    proc = subprocess.run(
        [
            "pi",
            "-p",
            "--no-tools",
            "--no-session",
            "--model",
            model,
        ],
        input=prompt,
        capture_output=True,
        text=True,
        env={
            **os.environ,
            "PI_SKIP_VERSION_CHECK": "1",
            "PI_TELEMETRY": "0",
        },
    )
    return proc.stdout if proc.returncode == 0 else None


def _omp(prompt, model):
    proc = subprocess.run(
        [
            "omp",
            "-p",
            "--no-tools",
            "--no-session",
            "--no-title",
            "--model",
            model,
        ],
        input=prompt,
        capture_output=True,
        text=True,
    )
    return proc.stdout if proc.returncode == 0 else None


def run_extractor(prompt, agent=None, model=None):
    """Run the decision extractor. With no agent, try Codex and then Claude.
    An explicit agent pins one extractor with no cross-fallback. Pi and OMP
    require an explicit model. Returns (label, text|None)."""
    runners = {
        "codex": _codex,
        "claude": _claude,
        "pi": _pi,
        "omp": _omp,
    }
    order = [agent] if agent else ["codex", "claude"]
    for a in order:
        if not shutil.which(a):
            if agent:
                print(f"decision diff: {a} CLI not found")
            continue
        m = model or DEFAULT_MODEL.get(a)
        if not m:
            print(f"decision diff: {a} requires --model")
            return "none", None
        answer = runners[a](prompt, m)
        if answer is not None:
            return f"{a}:{m}", answer
        print(
            f"decision diff: {a} ({m}) failed"
            + ("" if agent or a == "claude" else " — falling back to claude")
        )
    return "none", None


NEED_TRIALS = "decision diff: need finished trials on both sides — skipped"


def build_prompt(run):
    """Assemble the extraction prompt. Returns (prompt, counts); prompt is
    None when either variant has no finished trial. Every mode goes through
    here, so an external extractor gets the exact string the CLI path
    would send."""
    trials = trials_of(run)
    counts = {v: len(trials.get(v, [])) for v in ("before", "after")}
    if not counts["before"] or not counts["after"]:
        return None, counts
    task = (run / "task.md").read_text().strip()
    terms = source_terms(run)
    schema = SCHEMA.format(schema_noun=terms["schema_noun"])
    return PROMPT.format(
        task=task,
        source_note=terms["source_note"],
        trials=render_trials(trials, terms["entry_heading"]),
        schema=schema,
        anchor_noun=terms["anchor_noun"],
        evidence_clause=terms["evidence_clause"],
        decision_clause=terms["decision_clause"],
    ), counts


def write_decisions(run, raw, counts, extractor):
    """extract_json → normalize → decisions.json. On unusable output writes
    decisions.raw.txt, leaves decisions.json unwritten, returns False."""
    try:
        data = normalize(extract_json(raw), counts)
    except (ValueError, KeyError, TypeError) as exc:
        print(f"decision diff: unreadable extractor output — skipped ({exc})")
        (run / "decisions.raw.txt").write_text(raw)
        return False
    if not data["chain"]:
        print("decision diff: no usable decisions recovered — skipped")
        (run / "decisions.raw.txt").write_text(raw)
        return False
    data["extractor"] = extractor
    data["counts"] = counts
    (run / "decisions.json").write_text(json.dumps(data, indent=2))
    n_div = sum(r["diverges"] for r in data["chain"])
    drop_note = (
        f", {data['dropped']} row(s) dropped for inconsistent counts"
        if data["dropped"]
        else ""
    )
    print(
        f"decision diff ({extractor}): {len(data['chain'])} decisions, "
        f"{n_div} diverging{drop_note}"
    )
    return True


def main(run, agent=None, model=None):
    prompt, counts = build_prompt(run)
    if prompt is None:
        print(NEED_TRIALS)
        return
    extractor, raw = run_extractor(prompt, agent, model)
    if raw is None:
        print("decision diff: no extractor succeeded — skipped")
        return
    write_decisions(run, raw, counts, extractor)


def emit_prompt(run):
    prompt, _ = build_prompt(run)
    if prompt is None:
        sys.exit(NEED_TRIALS)
    print(prompt)


def ingest(run, reply_file, label):
    prompt, counts = build_prompt(run)
    if prompt is None:
        sys.exit(NEED_TRIALS)
    raw = Path(reply_file).read_text()
    if not write_decisions(run, raw, counts, label):
        sys.exit(1)


def self_check():
    def progress(message):
        print(f"[decisions] {message}", flush=True)

    progress("Normalize decision rows and parse extractor JSON")
    counts = {"before": 3, "after": 3}
    good = {
        "chain": [
            {
                "decision": "What verdict shape?",
                "anchor": "answer",
                "before": [{"choice": "PASS", "n": 2}, {"choice": "FAIL", "n": 1}],
                "after": [{"choice": "score /100", "n": 3}],
                "diverges": True,
            },
            {
                "decision": "How is correctness established?",
                "anchor": 2,
                "topic": "Correctness check",
                "before": [{"choice": "ran the program", "n": 3}],
                "after": [{"choice": "traced by hand", "n": 3}],
                "diverges": True,
            },
            {
                "decision": "bad row, counts do not add up",
                "anchor": 1,
                "before": [{"choice": "x", "n": 1}],
                "after": [{"choice": "y", "n": 3}],
                "diverges": False,
            },
        ],
        "fork": 2,
        "fork_note": "how truth is established",
        "outcome": 1,
        "implications": [
            {
                "text": "The answer changed with the evidence method.",
                "decisions": [2, 1],
            },
            {"text": "Unsupported claim from a dropped row.", "decisions": [1, 3]},
        ],
    }
    out = normalize(good, counts)
    assert len(out["chain"]) == 2, out  # bad row dropped
    assert out["dropped"] == 1, out  # ...and counted, not silent
    # action-anchored row sorts before the answer-anchored one
    assert out["chain"][0]["anchor"] == 2, out
    assert out["chain"][0]["topic"] == "Correctness check", out
    assert out["chain"][1]["topic"] == "", out  # missing topic stays empty
    assert out["chain"][1]["anchor"] == "answer", out
    # fork followed its row from raw position 2 to sorted position 1
    assert out["fork"] == 1, out
    assert out["chain"][1]["before"][1]["n"] == 1, out

    # a fork pointing at a dropped row resolves to None
    assert normalize({**good, "fork": 3}, counts)["fork"] is None
    # Claims keep their evidence after sorting; a partially lost citation invalidates them.
    assert out["outcome"] == 2
    assert out["implications"] == [
        {"text": "The answer changed with the evidence method.", "decisions": [1, 2]}
    ]
    assert normalize({**good, "outcome": 3}, counts)["outcome"] is None
    for reference in (True, 0, -1, 1.0, "1", 99):
        invalid = {
            **good,
            "outcome": reference,
            "implications": [{"text": "Unsupported", "decisions": [reference]}],
        }
        normalized = normalize(invalid, counts)
        assert normalized["outcome"] is None
        assert normalized["implications"] == []
    # Neither negative counts nor the model's divergence flag can imply a valid change.
    invalid_counts = {
        "chain": [
            {
                "decision": "What outcome?",
                "anchor": "answer",
                "before": [{"choice": "A", "n": 4}, {"choice": "B", "n": -1}],
                "after": [{"choice": "A", "n": 3}],
            }
        ]
    }
    assert normalize(invalid_counts, counts)["chain"] == []
    proportional = {
        "chain": [
            {
                "decision": "What outcome?",
                "anchor": "answer",
                "before": [{"choice": "A", "n": 2}],
                "after": [{"choice": "A", "n": 3}],
                "diverges": True,
            }
        ],
        "fork": 1,
    }
    normalized = normalize(proportional, {"before": 2, "after": 3})
    assert not normalized["chain"][0]["diverges"]
    assert normalized["fork"] is None

    fenced = '```json\n{"chain": [], "fork": null}\n```'
    assert extract_json(fenced) == {"chain": [], "fork": None}
    # a brace inside a string must not end the object early
    assert extract_json('{"a": "} not the end", "b": 1}')["b"] == 1

    progress("Build synthetic before and after traces")

    # ---- emit/ingest modes over a synthetic run dir ----
    me = Path(__file__).resolve()

    def cli(*argv, env=None):
        return subprocess.run(
            [sys.executable, str(me), *argv],
            capture_output=True,
            text=True,
            env=env,
        )

    with tempfile.TemporaryDirectory() as td:
        run = Path(td) / "run"
        task = "Sort the widget list and report the first divergence."
        sentinel = "SENTINEL-RULE-EDIT-73ab"
        run.mkdir()
        (run / "task.md").write_text(task)
        (run / "rule.md").write_text(f"Always {sentinel} before answering.")
        for name, ans in (
            ("before-1", "the list was already sorted"),
            ("after-1", "sorted it and flagged item 3"),
        ):
            d = run / name
            d.mkdir()
            (d / "trace.jsonl").write_text(
                json.dumps(
                    {
                        "type": "assistant",
                        "message": {
                            "content": [
                                {
                                    "type": "tool_use",
                                    "name": "Bash",
                                    "input": {"command": f"cat {name}.txt"},
                                }
                            ]
                        },
                    }
                )
                + "\n"
                + json.dumps({"type": "result", "result": ans})
                + "\n"
            )

        progress("Validate trace provenance and prompt wording")

        # A missing config file or trace_source key defaults to captured.
        captured = "The numbered entries come from captured tool calls."
        assert source_note(run) == captured
        (run / "config.json").write_text("{}")
        assert source_note(run) == captured

        # Supplied but invalid provenance fails before extractor dispatch.
        provenance_error = 'trace_source must be either "captured" or "self-reported"'
        invalid_configs = (
            "{",
            "null",
            json.dumps({"trace_source": None}),
            json.dumps({"trace_source": "invented"}),
            json.dumps({"trace_source": []}),
            "[]",
        )
        for invalid_config in invalid_configs:
            (run / "config.json").write_text(invalid_config)
            p = cli(str(run), "--emit-prompt")
            assert p.returncode != 0, p.stdout
            assert provenance_error in p.stderr, p.stderr

        # Live runs identify numbered entries as self-reported before emit.
        (run / "config.json").write_text(json.dumps({"trace_source": "self-reported"}))

        # emit prints exactly what the default path hands run_extractor
        p = cli(str(run), "--emit-prompt")
        assert p.returncode == 0, p.stderr
        prompt, _ = build_prompt(run)
        assert p.stdout == prompt + "\n", "emit-mode prompt differs"
        assert task in p.stdout
        assert "=== before-1 (BEFORE) ===" in p.stdout
        assert "=== after-1 (AFTER) ===" in p.stdout
        assert '"fork_note"' in p.stdout  # schema included
        assert (
            "The numbered entries are self-reported actions, not captured tool calls."
        ) in p.stdout
        assert "action number" in p.stdout
        assert "reported actions:" in p.stdout
        assert "commands it ran" not in p.stdout
        assert "actually did" not in p.stdout
        assert "A decision is not an action; some decisions leave no action" in p.stdout
        assert "A decision is not a command" not in p.stdout
        # Captured mode retains the original command/performed-action language.
        (run / "config.json").write_text(json.dumps({"trace_source": "captured"}))
        captured_prompt, _ = build_prompt(run)
        assert "captured tool calls" in captured_prompt
        assert "command number" in captured_prompt
        assert "commands it ran:" in captured_prompt
        assert "actually did and said" in captured_prompt
        assert "self-reported" not in captured_prompt
        assert (
            "A decision is not a command; some decisions leave no command"
            in captured_prompt
        )
        assert "A decision is not an action" not in captured_prompt
        (run / "config.json").write_text(json.dumps({"trace_source": "self-reported"}))
        # blind handoff: no rule content, no path back to the run dir
        assert sentinel not in p.stdout
        assert str(run) not in p.stdout

        progress("Validate CLI errors and failed extraction fallback")

        # new modes reject the CLI-extractor flags
        bad = cli(str(run), "--emit-prompt", "--agent", "codex")
        assert bad.returncode != 0 and "usage:" in bad.stderr, bad

        # garbage reply: nonzero, raw kept, no decisions.json — twice,
        # mirroring the live skill's one-retry policy
        garbage = run / "reply-bad.txt"
        garbage.write_text("no json here at all")
        for _ in range(2):
            p = cli(str(run), "--ingest", str(garbage))
            assert p.returncode != 0, p.stdout
        assert (run / "decisions.raw.txt").exists()
        assert not (run / "decisions.json").exists()

        # Failed extraction still renders raw actions and final answers.
        skip = (
            "decision diff skipped: extractor reply unparseable (2 subagent attempts)"
        )
        (run / "grades.tsv").write_text("before-1\tREVIEW\t-\nafter-1\tREVIEW\t-\n")
        (run / "config.json").write_text(
            json.dumps(
                {
                    "title": "check",
                    "sub": "synthetic self-check run. " + skip,
                    "scenario": task,
                    "expected": None,
                    "mode": "review",
                    "vocab": "generic",
                    "trace_source": "self-reported",
                }
            )
        )
        p = subprocess.run(
            [
                sys.executable,
                str(me.parent / "render.py"),
                str(run),
                str(run),
                "check",
                str(run / "config.json"),
            ],
            capture_output=True,
            text=True,
        )
        assert p.returncode == 0, p.stderr
        page = (run / "report.html").read_text()
        assert (
            "Decision diff: what the agent chose, before and after your edit"
            not in page
        )
        assert skip in page
        assert "cat before-1.txt" in page
        assert "the list was already sorted" in page
        assert "Flow diff" not in page

        progress("Validate successful decision ingestion")

        # Ingestion preserves outcome selection and its cited interpretation.
        reply = run / "reply-good.txt"
        reply.write_text(
            json.dumps(
                {
                    "chain": [
                        {
                            "topic": "Verdict shape",
                            "decision": "What verdict shape?",
                            "anchor": "answer",
                            "before": [{"choice": "prose", "n": 1}],
                            "after": [{"choice": "flagged item", "n": 1}],
                            "diverges": True,
                        }
                    ],
                    "fork": 1,
                    "fork_note": "shape",
                    "outcome": 1,
                    "implications": [
                        {"text": "The answer now flags an item.", "decisions": [1]}
                    ],
                }
            )
        )
        p = cli(
            str(run), "--ingest", str(reply), "--extractor-label", "subagent:sonnet"
        )
        assert p.returncode == 0, p.stdout + p.stderr
        data = json.loads((run / "decisions.json").read_text())
        assert len(data["chain"]) == 1, data
        assert data["extractor"] == "subagent:sonnet", data
        assert data["counts"] == {"before": 1, "after": 1}, data

        progress("Validate pinned Pi and OMP extractors")
        fake_bin = Path(td) / "bin"
        fake_bin.mkdir()
        fake_extractor = """#!/usr/bin/env python3
import os
import sys
from pathlib import Path

name = Path(sys.argv[0]).name.upper()
Path(os.environ[f"{name}_ARGS_FILE"]).write_text("\\n".join(sys.argv[1:]) + "\\n")
if name == "PI":
    Path(os.environ["PI_ENV_FILE"]).write_text(
        os.environ.get("PI_SKIP_VERSION_CHECK", "")
        + "\\n"
        + os.environ.get("PI_TELEMETRY", "")
        + "\\n"
    )
sys.stdin.read()
print(os.environ["EXTRACTOR_REPLY"])
"""
        for binary in ("pi", "omp"):
            path = fake_bin / binary
            path.write_text(fake_extractor)
            path.chmod(0o755)
        extractor_reply = json.dumps(
            {
                "chain": [
                    {
                        "decision": "Which result?",
                        "anchor": "answer",
                        "before": [{"choice": "before", "n": 1}],
                        "after": [{"choice": "after", "n": 1}],
                        "diverges": True,
                    }
                ],
                "fork": 1,
                "fork_note": "result",
            }
        )
        fake_env = {
            **os.environ,
            "PATH": f"{fake_bin}{os.pathsep}{os.environ['PATH']}",
            "EXTRACTOR_REPLY": extractor_reply,
            "PI_ARGS_FILE": str(Path(td) / "pi-args"),
            "OMP_ARGS_FILE": str(Path(td) / "omp-args"),
            "PI_ENV_FILE": str(Path(td) / "pi-env"),
        }
        for stack, model in (("pi", "test/pi-model"), ("omp", "test/omp-model")):
            (run / "decisions.json").unlink(missing_ok=True)
            p = cli(
                str(run),
                "--agent",
                stack,
                "--model",
                model,
                env=fake_env,
            )
            assert p.returncode == 0, p.stdout + p.stderr
            data = json.loads((run / "decisions.json").read_text())
            assert data["extractor"] == f"{stack}:{model}", data
            args = (Path(td) / f"{stack}-args").read_text().splitlines()
            assert "--no-tools" in args, args
            assert model in args, args
            assert ("--no-title" in args) == (stack == "omp"), args
        assert (Path(td) / "pi-env").read_text().splitlines() == ["1", "0"]

        progress("Reject incomplete trial sets")

        # a side without a finished trial flips emit to a nonzero exit
        (run / "after-1" / "trace.jsonl").unlink()
        p = cli(str(run), "--emit-prompt")
        assert p.returncode != 0
        assert "need finished trials on both sides" in p.stderr
    print("decisions.py self-check ok")


if __name__ == "__main__":
    if "--check" in sys.argv:
        self_check()
    else:
        args = sys.argv[1:]
        run_dir, agent, model = None, None, None
        emit, reply, label = False, None, None
        i = 0
        while i < len(args):
            if args[i] == "--agent":
                agent = args[i + 1]
                i += 2
            elif args[i] == "--model":
                model = args[i + 1]
                i += 2
            elif args[i] == "--emit-prompt":
                emit = True
                i += 1
            elif args[i] == "--ingest":
                reply = args[i + 1]
                i += 2
            elif args[i] == "--extractor-label":
                label = args[i + 1]
                i += 2
            else:
                run_dir = args[i]
                i += 1
        usage = (
            "usage: decisions.py RUN_DIR [--agent codex|claude|pi|omp] "
            "[--model NAME] | RUN_DIR --emit-prompt | "
            "RUN_DIR --ingest FILE [--extractor-label LABEL]"
        )
        if not run_dir or (agent and agent not in ("codex", "claude", "pi", "omp")):
            sys.exit(usage)
        # the new modes never touch a CLI extractor, so --agent/--model
        # cannot combine with them; emit and ingest are mutually exclusive
        if (emit or reply or label) and (agent or model):
            sys.exit(usage)
        if (emit and reply) or (label and not reply):
            sys.exit(usage)
        run = Path(run_dir).resolve()
        if emit:
            emit_prompt(run)
        elif reply:
            ingest(run, reply, label or "subagent")
        else:
            main(run, agent, model)
