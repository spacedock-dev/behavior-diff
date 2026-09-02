# DRC-4282 Pi and OMP Trial Stacks Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> superpowers:subagent-driven-development (recommended) or
> superpowers:executing-plans to implement this plan task-by-task. Steps use
> checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add upstream Pi (`pi`) and Oh My Pi (`omp`) as first-class Behavior Diff trial stacks while keeping one report format and clear ownership between skills and scripts.

**Architecture:** Skills make choices that need judgment. Scripts run repeatable mechanics. `run-trial.sh` is the stack adapter. It converts Claude, Codex, Pi, and OMP output into the existing canonical `trace.jsonl` format. Pi and OMP use separate CLI command profiles and one private JSON normalizer. The grader and renderer stay stack-neutral.

**Tech Stack:** Bash 3.2, Python 3, `jq`, Claude CLI, Codex CLI, Pi CLI, OMP CLI, deterministic shell contract tests.

**Issue:** [DRC-4282](https://linear.app/recce/issue/DRC-4282/trials-only-run-on-claude-or-codex-decide-the-binaryskill)

---

## Status

This document records the accepted design. It also gives the implementation order and test gates.

Accepted direction: **Add upstream Pi and OMP now.**

The work adds two trial stacks. It does not add Pi or OMP plugin packaging.

## Problem

Behavior Diff currently accepts only two values for `--agent`:

```text
claude
codex
```

The split between skill work and script work is also implicit. This creates two problems:

1. A Pi or OMP user gets a flat refusal instead of a useful path.
2. Future stack work can put judgment in scripts or repeat mechanics in skills.

The new design makes that split explicit and adds Pi and OMP without changing the report format.

## Design decision

### Ownership

| Layer | Owns | Does not own |
| --- | --- | --- |
| `behavior-diff` skill | Find the changed instruction file. Draft the decision-moment task. Select the current trial stack and exact model. Explain the result. | Build variants, launch trials, parse traces, grade runs, render HTML. |
| `behavior-diff-live` skill | Prepare the same task for both variants. Select the host-specific dispatch method. Explain the weaker live evidence. | Create a second report format or infer captured actions. |
| `behavior-diff.sh` | Build variants, launch trials, grade complete versus blocked runs, call the extractor, render the report. | Know Pi or OMP event fields. |
| `run-trial.sh` | Run one host CLI and normalize its output into canonical `trace.jsonl`. | Grade behavior or explain the result. |
| `decisions.py` | Extract the decision chain from canonical trial evidence. | Read raw Claude, Codex, Pi, or OMP trace formats. |
| `render.py` | Render canonical evidence. | Branch on the trial stack. |

### Data flow

```text
SKILL.md
  makes judgment calls
        |
        v
behavior-diff.sh
  builds before/after copies
  launches equal trials
        |
        v
run-trial.sh
  claude | codex | pi | omp
  converts raw events
        |
        v
trace.jsonl
  canonical tool calls + final answer
        |
        +-------------------+
        |                   |
        v                   v
decisions.py            render.py
  decision chain          one HTML report
```

### Stack adapter boundary

Keep the current switch in `run-trial.sh`:

```text
claude -> native stream-json is already canonical
codex  -> codex-raw.jsonl -> Codex normalizer -> canonical trace.jsonl
omp    -> omp-raw.jsonl   ┐
                         ├-> shared private normalizer -> canonical trace.jsonl
pi     -> pi-raw.jsonl    ┘
```

Pi and OMP need separate command profiles. Their flags and built-in tool names differ. Their official JSON event fields match, so one private normalizer avoids duplicate `jq` logic. Separate tests pin both input contracts.

Do not create one file per stack. Four small command branches and one private normalizer are easier to read than a public adapter framework.

Do not add a public external-adapter API. No external caller defines that contract.

## Public command contract

### Claude

```bash
behavior-diff.sh \
  --agent claude \
  --model sonnet \
  --file <instruction-file> \
  --task <decision-moment-task>
```

### Codex

```bash
behavior-diff.sh \
  --agent codex \
  --model gpt-5.6-terra \
  --file <instruction-file> \
  --task <decision-moment-task>
```

### OMP

```bash
behavior-diff.sh \
  --agent omp \
  --model <exact-current-omp-model> \
  --file <instruction-file> \
  --task <decision-moment-task>
```

### Pi

```bash
behavior-diff.sh \
  --agent pi \
  --model <exact-current-pi-model> \
  --file <instruction-file> \
  --task <decision-moment-task>
```

Pi and OMP require `--model`. Neither stack has a portable default provider and model. A silent fallback can test a different agent from the one the user means to measure.

Claude and Codex keep their current defaults.

## OMP trial command

`run-trial.sh` runs OMP in one disposable variant copy:

```bash
printf '%s\n' "$task" | omp -p \
  --mode json \
  --no-session \
  --no-title \
  --cwd "$dir" \
  --model "$model" \
  --tools read,bash,grep,glob \
  --approval-mode yolo
```

Each flag has one reason:

| Flag | Reason |
| --- | --- |
| `-p` | Run once and exit. |
| `--mode json` | Emit machine-readable events. |
| `--no-session` | Do not write a reusable OMP session. |
| `--no-title` | Avoid the extra title model call. |
| `--cwd` | Start inside the variant copy. |
| `--model` | Test the exact selected OMP model. |
| `--tools` | Exclude edit, write, browser, subagent, and network-specific tools. |
| `--approval-mode yolo` | Avoid an approval prompt in a headless run. |

The task goes through stdin. This avoids treating a task that starts with `-` as a CLI flag.

## Pi trial command

`run-trial.sh` runs upstream Pi in one disposable variant copy:

```bash
printf '%s\n' "$task" | pi -p \
  --mode json \
  --no-session \
  --model "$model" \
  --tools read,bash,grep,find,ls
```

Pi does not accept OMP's `--no-title` or `--approval-mode` flags. Pi also uses `find` and `ls` where the OMP profile uses `glob`.

The runner sets `PI_SKIP_VERSION_CHECK=1` and `PI_TELEMETRY=0` for each Pi trial. These settings stop unrelated Pi update checks and install telemetry. They do not disable the selected model provider.

### Pi and OMP event contract

Both CLIs emit one JSON object per line. The shared normalizer uses these stable events:

```json
{"type":"tool_execution_start","toolCallId":"call-1","toolName":"bash","args":{"command":"python3 -m pytest"}}
{"type":"message_end","message":{"role":"assistant","content":[{"type":"text","text":"The check passes."}]}}
```

OMP sources of record:

- `packages/coding-agent/src/modes/print-mode.ts` writes every printable event as one JSON line.
- `packages/agent/src/types.ts` defines `tool_execution_start` and `message_end`.
- The reviewed OMP revision was `984a4f2dc9e50f6645b8fe04a91570876f8d3c83`.

Pi sources of record:

- `packages/coding-agent/docs/json.md` documents the JSON-lines protocol.
- `packages/coding-agent/src/modes/json-event.ts` keeps final `message_end` values and emits compact stream updates.
- The reviewed Pi revision was `e266507b606b9552fa277252644054afd4384b11`.

Links:

- <https://github.com/can1357/oh-my-pi/blob/984a4f2dc9e50f6645b8fe04a91570876f8d3c83/packages/coding-agent/src/modes/print-mode.ts>
- <https://github.com/can1357/oh-my-pi/blob/984a4f2dc9e50f6645b8fe04a91570876f8d3c83/packages/agent/src/types.ts>
- <https://github.com/earendil-works/pi/blob/e266507b606b9552fa277252644054afd4384b11/packages/coding-agent/docs/json.md>
- <https://github.com/earendil-works/pi/blob/e266507b606b9552fa277252644054afd4384b11/packages/coding-agent/src/modes/json-event.ts>

### Canonical trace contract

All stacks keep the current format:

```json
{"type":"assistant","message":{"content":[{"type":"tool_use","name":"bash","input":{"command":"python3 -m pytest"}}]}}
{"type":"result","result":"The check passes."}
```

Pi and OMP normalization rules:

1. Convert each `tool_execution_start` event into one `tool_use` line.
2. Copy `toolName` to `name`.
3. Copy `args` to `input`.
4. When `args.path` exists, also write it as `input.file_path`. The current renderer reads `file_path` for non-command actions.
5. Select assistant `message_end` events.
6. Join their text blocks.
7. Use the last assistant message as the final result.
8. Write an empty result when no final assistant text exists. The existing grader marks that trial `BLOCKED`.

Raw output stays in `pi-raw.jsonl` or `omp-raw.jsonl`. This gives each stack a local debugging path without changing the report contract.

## Decision extractor contract

`decisions.py` gets separate Pi and OMP command profiles.

OMP:

```bash
printf '%s\n' "$prompt" | omp -p \
  --no-tools \
  --no-session \
  --no-title \
  --model "$model"
```

Pi:

```bash
printf '%s\n' "$prompt" | pi -p \
  --no-tools \
  --no-session \
  --model "$model"
```

Rules:

- A Pi trial run uses Pi for decision extraction unless the caller passes `--extract-agent`.
- An OMP trial run uses OMP for decision extraction unless the caller passes `--extract-agent`.
- Each extractor uses the same model as its trials unless the caller passes `--extract-model`.
- Pi and OMP extraction need an explicit model.
- Claude and Codex extractor order and defaults stay unchanged.
- `--emit-prompt` and `--ingest` stay stack-neutral.

This keeps Pi-only and OMP-only machines usable. It also avoids asking another stack to interpret the result by default.

## Live skill host contract

The live skill keeps one task and one report format. Only dispatch differs.

| Host | Dispatch | Delivery |
| --- | --- | --- |
| Claude Code | Launch two subagents in one parallel dispatch. | Each trial calls `SendMessage` to the main agent. |
| OMP | Launch one `task` batch with two task items. | Results return to the parent automatically. Do not ask for `SendMessage`. |
| Pi | Pi has no built-in subagent dispatch. Use the headless skill with `--agent pi`. | The headless runner collects Pi JSON events. |
| Codex without dispatch | Run two fresh contexts in sequence, or use the headless skill. | Collect each final answer directly. |

Every live path keeps these rules:

- The two prompts differ only by the variant directory.
- Each trial reads the instruction files inside its own variant.
- Each trial reports `ANSWER` and numbered `ACTIONS`.
- Each trial stays inside its variant and does not use networked or destructive commands.
- The summary says live subagents do not auto-load the variant instruction file.
- The summary says one trial per side is one sample.

## Install and support wording

Behavior Diff remains an installable plugin for Claude Code and Codex.

Pi and OMP are trial stacks, not plugin hosts in this change.

The README and plugin descriptions must make this difference clear:

| Surface | Claude Code | Codex | Pi | OMP |
| --- | --- | --- | --- | --- |
| Marketplace plugin install | Yes | Yes | No in DRC-4282 | No in DRC-4282 |
| Headless trial stack | Yes | Yes | Yes, with explicit `--model` | Yes, with explicit `--model` |
| Live trial dispatch | Parallel subagents | Fresh sequential contexts or headless | No built-in dispatch. Use headless. | One parallel `task` batch |

Do not add a Pi or OMP manifest, marketplace entry, install command, or edit hook.

## Error contract

### Supported stacks

The accepted values are:

```text
claude
codex
pi
omp
```

### Unknown stack

```text
behavior-diff: unsupported trial stack "<value>"
Supported stacks: claude, codex, pi, omp.
A new stack needs:
1. a fresh headless CLI run.
2. machine-readable tool and final-answer events.
3. a converter to canonical trace.jsonl.
```

### Missing Pi or OMP model

```text
behavior-diff: --agent pi requires --model with the exact Pi model ID
behavior-diff: --agent omp requires --model with the exact OMP model ID
```

### Missing Pi or OMP binary

Keep exit code `3` and name the command:

```text
behavior-diff: pi CLI required (--agent pi)
behavior-diff: omp CLI required (--agent omp)
```

### Incomplete Pi or OMP output

Do not invent a final answer. Keep the raw stream, write an empty canonical result, and let the current grader mark the trial `BLOCKED`.

## Safety and privacy

Pi and OMP trials run inside the same disposable project copies used by the other stacks.

Both tool lists exclude edit and write. OMP also excludes browser and subagent tools. Bash still has broad power. OMP needs `--approval-mode yolo` because a headless run cannot answer prompts. Pi has no built-in approval prompt.

The disposable copy is not an OS sandbox. A Pi or OMP bash command can still reach outside it or use the network. DRC-4282 records this limit. It does not add a new sandbox or change the trial task.

Do not write trial data to the repository. Raw traces, normalized traces, prompts, reports, and stderr stay under `${BEHAVIOR_DIFF_HOME:-~/.behavior-diff}/runs/`.

CI uses only stub CLIs and synthetic JSON. CI never calls a model or a live agent CLI.

## Scope

### In scope

- Accept `--agent pi` and `--agent omp` in both command entry points.
- Require an exact model for Pi and OMP.
- Run Pi and OMP headlessly.
- Normalize their matching JSON event contracts through one private helper.
- Keep separate raw trace files for Pi and OMP.
- Extract decisions with the same stack and model used for each trial.
- Add OMP live dispatch instructions.
- Direct Pi users to the headless path because Pi has no built-in subagents.
- State the skill and script ownership split.
- Add useful errors for unknown stacks.
- Add deterministic Pi and OMP contract tests.
- Update public support wording.

### Out of scope

- Pi or OMP plugin packaging.
- Pi or OMP plugin installation instructions.
- Pi or OMP edit hooks.
- A generic external adapter API.
- Gemini or a fifth trial stack.
- A new canonical trace format.
- A new report format.
- A change to automatic grading.
- A plugin version bump. Release work owns the version.

## Files

### Modify

- `plugin/skills/behavior-diff/scripts/behavior-diff.sh`
- `plugin/skills/behavior-diff/scripts/run-trial.sh`
- `plugin/skills/behavior-diff/scripts/decisions.py`
- `bin/behavior-diff`
- `plugin/skills/behavior-diff/SKILL.md`
- `plugin/skills/behavior-diff-live/SKILL.md`
- `README.md`
- `plugin/.claude-plugin/plugin.json`
- `plugin/.codex-plugin/plugin.json`
- `tests/hooks-test.sh`
- `tests/live-report-contract.sh`

### Do not modify

- `plugin/skills/behavior-diff/scripts/render.py`
- `plugin/.claude-plugin/plugin.json` version field
- `plugin/.codex-plugin/plugin.json` version field
- Marketplace files outside this repository
- Files under `${BEHAVIOR_DIFF_HOME:-~/.behavior-diff}/runs/`

---

## Task 1: Lock the CLI and skill contracts with failing tests

**Files:**

- Modify: `tests/hooks-test.sh`
- Modify: `tests/live-report-contract.sh`

- [ ] Add `run-trial.sh` to the shell test setup:

```bash
trial_runner=$here/../plugin/skills/behavior-diff/scripts/run-trial.sh
```

- [ ] Add fake `pi` and `omp` commands under the existing test `PATH`. Each command records its arguments, consumes stdin, and emits synthetic events.

OMP stub:

```bash
cat >"$stub/omp" <<'SH'
#!/bin/sh
printf '%s\n' "$@" >"$OMP_ARGS_FILE"
cat >/dev/null
cat <<'JSON'
{"type":"tool_execution_start","toolCallId":"call-1","toolName":"bash","args":{"command":"printf ok"}}
{"type":"tool_execution_start","toolCallId":"call-2","toolName":"read","args":{"path":"AGENTS.md"}}
{"type":"message_end","message":{"role":"assistant","content":[{"type":"text","text":"OMP done"}]}}
JSON
SH
chmod +x "$stub/omp"
```

Pi stub:

```bash
cat >"$stub/pi" <<'SH'
#!/bin/sh
printf '%s\n' "$@" >"$PI_ARGS_FILE"
cat >/dev/null
cat <<'JSON'
{"type":"tool_execution_start","toolCallId":"call-1","toolName":"bash","args":{"command":"printf ok"}}
{"type":"tool_execution_start","toolCallId":"call-2","toolName":"read","args":{"path":"AGENTS.md"}}
{"type":"message_end","message":{"role":"assistant","content":[{"type":"text","text":"Pi done"}]}}
JSON
SH
chmod +x "$stub/pi"
```

- [ ] Add runner tests for these contracts:

```text
--agent unknown exits 2 and lists claude, codex, pi, omp
--agent pi without --model exits 2
--agent omp without --model exits 2
--agent pi with a missing binary exits 3
--agent omp with a missing binary exits 3
```

- [ ] Run the tests and confirm they fail on the current two-stack validation:

```bash
bash tests/hooks-test.sh
```

Expected result: non-zero exit from the first new Pi or OMP assertion.

- [ ] Add direct `run-trial.sh` tests for both fake commands.

Check the OMP trial:

```text
omp-raw.jsonl exists
trace.jsonl contains a bash command tool_use
trace.jsonl maps AGENTS.md to input.file_path
trace.jsonl ends with result "OMP done"
OMP received -p, --mode json, --no-session, --no-title
OMP received --tools read,bash,grep,glob
OMP received --approval-mode yolo
OMP received the exact test model
```

Check the Pi trial:

```text
pi-raw.jsonl exists
trace.jsonl contains the same canonical tool_use shape
trace.jsonl maps AGENTS.md to input.file_path
trace.jsonl ends with result "Pi done"
Pi received -p, --mode json, --no-session
Pi received --tools read,bash,grep,find,ls
Pi received the exact test model
Pi did not receive --no-title or --approval-mode
```

- [ ] Add fake Pi and OMP outputs with no final assistant `message_end`. Check that neither trace has a non-empty canonical result. This is the grader's `BLOCKED` condition.

- [ ] Add live-report contract checks for exact ownership and host rules:

```text
The skill owns judgment.
The scripts own repeatable mechanics.
--agent pi
--model <exact-current-pi-model>
--agent omp
--model <exact-current-omp-model>
Pi has no built-in subagent dispatch.
one `task` batch
Results return to the parent automatically.
Pi and OMP are trial stacks, not plugin hosts
```

- [ ] Run both test files and confirm they fail for the missing implementation and prose:

```bash
bash tests/hooks-test.sh
bash tests/live-report-contract.sh
```

Expected result: both commands fail on the new assertions.

- [ ] Commit the failing contracts:

```bash
git add tests/hooks-test.sh tests/live-report-contract.sh
git commit --signoff -m "test: define Pi and OMP trial stack contracts"
```

## Task 2: Extend the runner command contract

**Files:**

- Modify: `plugin/skills/behavior-diff/scripts/behavior-diff.sh`
- Modify: `bin/behavior-diff`

- [ ] Change trial-stack validation in `behavior-diff.sh` to accept `pi` and `omp`. Use the error messages in this plan.

Use this model selection rule:

```bash
if [ -z "$model" ]; then
  case "$agent" in
    claude) model=sonnet ;;
    codex) model=gpt-5.6-terra ;;
    pi)
      echo "behavior-diff: --agent pi requires --model with the exact Pi model ID" >&2
      exit 2
      ;;
    omp)
      echo "behavior-diff: --agent omp requires --model with the exact OMP model ID" >&2
      exit 2
      ;;
  esac
fi
```

- [ ] Keep `command -v "$agent"` after model and required-argument validation. This produces the existing exit code `3` for a missing CLI.

- [ ] Pin the default extractor for Pi and OMP runs before calling `decisions.py`:

```bash
case "$agent" in
  pi | omp)
    if [ -z "$extract_agent" ]; then
      extract_agent=$agent
      [ -n "$extract_model" ] || extract_model=$model
    fi
    ;;
esac
```

An explicit `--extract-agent` still wins.

- [ ] Update `bin/behavior-diff` usage only. Its existing pass-through array already forwards `--agent`, `--model`, `--extract-agent`, and `--extract-model`.

```text
[--agent claude|codex|pi|omp] [--model NAME]
```

- [ ] Run the focused runner tests:

```bash
bash tests/hooks-test.sh
```

Expected result: the CLI validation assertions pass. The direct Pi and OMP adapter assertions still fail because `run-trial.sh` does not accept them yet.

- [ ] Commit:

```bash
git add plugin/skills/behavior-diff/scripts/behavior-diff.sh bin/behavior-diff
git commit --signoff -m "feat: accept Pi and OMP trial stacks"
```

## Task 3: Add Pi and OMP trace normalization

**Files:**

- Modify: `plugin/skills/behavior-diff/scripts/run-trial.sh`

- [ ] Update the header and usage to name all four stacks.

- [ ] Change validation to accept `claude`, `codex`, `pi`, or `omp`.

- [ ] Keep the Claude branch unchanged.

- [ ] Change the current `else` branch into `elif [ "$agent" = codex ]`. Keep its command and `jq` filters unchanged.

- [ ] Add one private `normalize_pi_omp_json` function. It accepts a raw Pi or OMP JSONL path and writes the existing canonical trace:

```bash
normalize_pi_omp_json() { # $1 = raw Pi or OMP JSONL
  local raw=$1
  jq -c '
    select(.type == "tool_execution_start")
    | {type: "assistant", message: {content: [{
        type: "tool_use",
        name: .toolName,
        input: ((.args // {})
          | if (has("file_path") or has("command")) then .
            elif has("path") then . + {file_path: .path}
            else .
            end)
      }]}}
  ' "$raw" >"$trace_dir/trace.jsonl"

  jq -s -c '
    [.[]
      | select(.type == "message_end" and .message.role == "assistant")
      | [.message.content[]? | select(.type == "text") | .text]
      | join("")]
    | {type: "result", result: (last // "")}
  ' "$raw" >>"$trace_dir/trace.jsonl"
}
```

- [ ] Add the OMP command branch. Save stdout to `omp-raw.jsonl`, then call the shared normalizer:

```bash
printf '%s\n' "$task" | omp -p \
  --mode json --no-session --no-title --cwd "$dir" \
  --model "$model" --tools read,bash,grep,glob \
  --approval-mode yolo \
  >"$trace_dir/omp-raw.jsonl" 2>"$trace_dir/stderr.log" || true
normalize_pi_omp_json "$trace_dir/omp-raw.jsonl"
```

- [ ] Add the Pi command branch. Save stdout to `pi-raw.jsonl`, then call the same normalizer:

```bash
printf '%s\n' "$task" | \
  PI_SKIP_VERSION_CHECK=1 PI_TELEMETRY=0 \
  pi -p --mode json --no-session --model "$model" \
  --tools read,bash,grep,find,ls \
  >"$trace_dir/pi-raw.jsonl" 2>"$trace_dir/stderr.log" || true
normalize_pi_omp_json "$trace_dir/pi-raw.jsonl"
```

- [ ] Run the focused tests:

```bash
bash tests/hooks-test.sh
```

Expected result: the fake Pi and OMP trials pass. Both missing-final cases have no non-empty result.

- [ ] Run Bash format checking for the changed scripts:

```bash
docker run --rm -v "$PWD:/mnt" -w /mnt \
  mvdan/shfmt:v3.14.0 -d -i 2 -ci \
  plugin/skills/behavior-diff/scripts/behavior-diff.sh \
  plugin/skills/behavior-diff/scripts/run-trial.sh \
  bin/behavior-diff tests/hooks-test.sh
```

Expected result: no diff.

- [ ] Commit:

```bash
git add plugin/skills/behavior-diff/scripts/run-trial.sh tests/hooks-test.sh
git commit --signoff -m "feat: normalize Pi and OMP trial traces"
```

## Task 4: Add Pi and OMP decision extractors

**Files:**

- Modify: `plugin/skills/behavior-diff/scripts/decisions.py`

- [ ] Extend the module usage and CLI validation from `codex|claude` to `codex|claude|pi|omp`.

- [ ] Add separate runners because their command flags differ:

```python
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
```

- [ ] Import `os` for the Pi subprocess environment.

- [ ] Add both runners. Keep the automatic fallback order as `codex`, then `claude`. Pi and OMP join the order only when the caller pins one.

```python
runners = {
    "codex": _codex,
    "claude": _claude,
    "pi": _pi,
    "omp": _omp,
}
order = [agent] if agent else ["codex", "claude"]
```

- [ ] Require a model for pinned Pi and OMP extractors:

```python
m = model or DEFAULT_MODEL.get(a)
if not m:
    print(f"decision diff: {a} requires --model")
    return "none", None
```

- [ ] Extend `self_check()` with fake Pi and OMP executables. Each fake command consumes stdin and returns valid extractor JSON.

Run both CLI cases:

```text
--agent pi --model test/pi-model
--agent omp --model test/omp-model
```

Check that:

```text
each run writes decisions.json
the Pi extractor label is pi:test/pi-model
the OMP extractor label is omp:test/omp-model
both fake commands receive --no-tools and the exact model
Pi does not receive --no-title
OMP receives --no-title
```

- [ ] Run the deterministic self-check:

```bash
python3 plugin/skills/behavior-diff/scripts/decisions.py --check
```

Expected result:

```text
decisions.py self-check ok
```

- [ ] Run Python formatting:

```bash
uvx ruff@0.16.5 format --check --diff \
  plugin/skills/behavior-diff/scripts/decisions.py
```

Expected result: no diff.

- [ ] Commit:

```bash
git add plugin/skills/behavior-diff/scripts/decisions.py
git commit --signoff -m "feat: extract Pi and OMP decision diffs"
```

## Task 5: Make skill ownership and host behavior explicit

**Files:**

- Modify: `plugin/skills/behavior-diff/SKILL.md`
- Modify: `plugin/skills/behavior-diff-live/SKILL.md`

- [ ] Add a short ownership section to the headless skill:

```text
The skill owns judgment. It finds the change, drafts the decision-moment task,
selects the current trial stack and model, and explains the evidence.

The scripts own repeatable mechanics. They build variants, run trials,
normalize traces, grade completeness, extract decisions, and render the report.
```

- [ ] Replace the current two-host instruction with four stack rules:

```text
Claude Code: --agent claude. The model defaults to sonnet.
Codex: --agent codex. The model defaults to gpt-5.6-terra.
Pi: --agent pi --model <exact-current-pi-model>. Never omit the model.
OMP: --agent omp --model <exact-current-omp-model>. Never omit the model.
```

- [ ] Keep the current rule that normal execution does not ask the user to confirm cost, file, task, or mode.

- [ ] Split the live launch step by host.

For Claude Code:

```text
Launch both subagents in one parallel dispatch. Each report calls SendMessage
to the main agent.
```

For OMP:

```text
Launch one `task` batch with two task items. Results return to the parent
automatically. Do not ask an OMP task agent to call SendMessage.
```

For Pi:

```text
Pi has no built-in subagent dispatch. Do not invent a parallel live path.
Use the headless skill with --agent pi and the exact Pi model.
```

For Codex without dispatch:

```text
Run two fresh contexts in sequence, or use the headless skill.
```

- [ ] Keep the common trial prompt and evidence limits outside the host branches. Do not copy the full prompt into each host path.

- [ ] Run the skill contract test:

```bash
bash tests/live-report-contract.sh
```

Expected result: ownership, Pi and OMP commands, and live host checks pass.

- [ ] Commit:

```bash
git add plugin/skills/behavior-diff/SKILL.md \
  plugin/skills/behavior-diff-live/SKILL.md \
  tests/live-report-contract.sh
git commit --signoff -m "docs: define trial stack ownership"
```

## Task 6: Update public support wording

**Files:**

- Modify: `README.md`
- Modify: `plugin/.claude-plugin/plugin.json`
- Modify: `plugin/.codex-plugin/plugin.json`
- Modify: `tests/live-report-contract.sh`

- [ ] Keep the existing Claude Code and Codex install commands unchanged.

- [ ] Add the support table from this design after the install introduction. State that Pi and OMP trial support does not mean plugin installation on either host.

- [ ] Change both manifest descriptions in the same edit:

```text
isolated before/after trials (claude, codex, pi, or omp)
```

- [ ] Keep both manifest versions at `0.3.2`. The release process owns the version bump.

- [ ] Add contract checks that both descriptions name all four trial stacks and both versions still match.

- [ ] Run:

```bash
bash tests/live-report-contract.sh
git diff --check
```

Expected result: both commands exit `0`.

- [ ] Commit:

```bash
git add README.md \
  plugin/.claude-plugin/plugin.json \
  plugin/.codex-plugin/plugin.json \
  tests/live-report-contract.sh
git commit --signoff -m "docs: describe Pi and OMP trial support"
```

## Task 7: Run full deterministic verification

- [ ] Run Bash formatting for the repository:

```bash
docker run --rm -v "$PWD:/mnt" -w /mnt \
  mvdan/shfmt:v3.14.0 -d -i 2 -ci .
```

Expected result: no diff.

- [ ] Run Python formatting for the repository:

```bash
uvx ruff@0.16.5 format --check --diff .
```

Expected result: no diff.

- [ ] Run the full deterministic suite:

```bash
bash tests/hooks-test.sh
python3 plugin/skills/behavior-diff/scripts/decisions.py --check
bash tests/live-report-contract.sh
bash tests/release-workflow-test.sh
```

Expected result: every command exits `0`.

- [ ] Run the Markdown whitespace check:

```bash
git diff --check
```

Expected result: no output.

- [ ] Confirm no test wrote run data into the repository:

```bash
git status --short
```

Expected result: only the planned source and test files are present before commits. After the planned commits, the tree is clean.

## Task 8: Run the optional paid Pi and OMP smoke gates

This is manual evidence. It is not a CI step.

- [ ] Check both local CLIs without a model call:

```bash
pi --version
omp --version
```

Expected result: both commands exit `0`.

The Pi preflight currently fails on this workstation because Node 20 does not export `node:fs.globSync`. Fixing the user's Pi runtime is outside this repository change. If it still fails, report the Pi smoke gate as blocked before any paid call.

- [ ] Ask Kent for approval to spend one fast Behavior Diff run on each working stack.

- [ ] If approved, create one synthetic temporary repository with one instruction-file edit. Do not use private code or a real transcript.

- [ ] Run one trial per side with Pi:

```bash
plugin/skills/behavior-diff/scripts/behavior-diff.sh \
  --agent pi \
  --model <approved-pi-model> \
  --file AGENTS.md \
  --task <synthetic-decision-moment-task> \
  --fast
```

- [ ] Run the same task with OMP:

```bash
plugin/skills/behavior-diff/scripts/behavior-diff.sh \
  --agent omp \
  --model <approved-omp-model> \
  --file AGENTS.md \
  --task <synthetic-decision-moment-task> \
  --fast
```

- [ ] Check the actual output surface for each completed stack:

```text
both raw traces exist
both canonical traces contain tool calls when the agent used tools
both canonical traces contain a non-empty final result
grades.tsv marks both runs REVIEW
report.html opens and shows commands plus final answers
decisions.json names the same stack and model used for the trials
```

- [ ] If approval is not given, report each paid gate as not run. Do not replace it with another model call or claim live proof.

- [ ] Do not commit the synthetic run or report.

## Task 9: Independent review before a pull request

- [ ] Read `REVIEWER_GUIDELINES.md`.

- [ ] Send the full diff to one independent read-only reviewer.

- [ ] Require checks for:

```text
Claude and Codex behavior did not change
Pi and OMP cannot run without an explicit model
Pi and OMP use separate command profiles
Pi and OMP raw events use one private canonical normalizer
missing final output becomes BLOCKED on both stacks
OMP live dispatch does not use Claude SendMessage rules
Pi live guidance does not invent built-in subagents
README does not claim Pi or OMP plugin installation
tests use only synthetic data and stub CLIs
both manifests stay equivalent
```

- [ ] Fix every validated blocking finding.

- [ ] Re-run the affected focused test and the full deterministic suite.

- [ ] Create the pull request only after all required gates pass, or name the exact missing gate.

---

## Acceptance criteria

DRC-4282 is complete when all statements below are true:

- `behavior-diff.sh --agent pi --model <id>` launches fresh headless Pi trials.
- `behavior-diff.sh --agent omp --model <id>` launches fresh headless OMP trials.
- Pi and OMP tool calls and final answers appear in canonical `trace.jsonl`.
- Pi and OMP use separate CLI command profiles and one private normalizer.
- Existing grading and rendering work without Pi or OMP branches.
- A missing final answer produces `BLOCKED` on both stacks.
- Each stack uses its trial model for decision extraction by default.
- The headless skill states the skill-versus-script ownership split.
- The live skill gives correct dispatch rules for Claude Code, OMP, Pi, and Codex.
- Pi live guidance uses the headless path because upstream Pi has no built-in subagents.
- Public wording separates plugin hosts from trial stacks.
- Claude and Codex paths keep their current commands and defaults.
- CI tests use only fake CLIs and synthetic events.
- The full deterministic suite passes.
- An independent reviewer gives a GO verdict, or the missing review gate is reported.

## Rejected alternatives

### Keep Pi or OMP unsupported

Rejected because both CLIs expose fresh headless JSON event streams with the evidence Behavior Diff needs.

### Treat `pi` as an alias for `omp`

Rejected because upstream Pi and OMP are separate products with different flags, tools, release lines, and runtime behavior. `--agent pi` must launch the real `pi` binary.

### Put Pi and OMP instructions only in the skill

Rejected because the skill would repeat variant, trace, and grading mechanics. It would also create a second report path.

### Use separate Pi and OMP normalizers

Rejected for now. Their official tool and final-message event fields match. One private helper removes duplicate `jq` while separate command tests detect either upstream contract changing.

### Add one script per stack

Rejected for now. Four command branches fit in `run-trial.sh`. Separate adapter files add a registry before another stack exists.

### Add a generic external adapter API

Rejected for now. No real external caller defines the right interface yet. `run-trial.sh` remains the internal adapter boundary.

### Use default Pi or OMP roles

Rejected because roles and provider mappings are user-specific. Each run must name the exact model under test.

### Change the canonical trace or renderer

Rejected because Pi and OMP events map to the current contract. A report change would add migration work without improving DRC-4282.
