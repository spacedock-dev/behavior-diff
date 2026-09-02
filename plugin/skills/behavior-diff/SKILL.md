---
name: behavior-diff
description: Compare agent behavior before/after an uncommitted change to CLAUDE.md, AGENTS.md, or a skill file. Use for "behavior diff", "test my CLAUDE.md change", "did my rule change the agent's behavior", "before/after check on my rule edit".
---

# Behavior diff

Runs Behavior Diff on a local uncommitted instruction-file change. It starts
fresh headless agent trials with and without the change. The report shows the
git diff, a flow diff, and every trial's commands and final answer. There is
no automatic verdict. The user judges the evidence.

The runner is bundled with this skill: `scripts/behavior-diff.sh` inside
this skill's base directory. Pass `--agent` to match the agent running
this skill — `claude` under Claude Code, `codex` under Codex; you know
which one you are. Trials then run on that stack (model defaults:
sonnet for claude, gpt-5.6-terra for codex; override with `--model`). Your job is to prepare its two parameters —
`--file` and `--task` — well. Runs land under
`${BEHAVIOR_DIFF_HOME:-~/.behavior-diff}/runs/`.


**Spacedock workflow rule?** If the changed file is a spacedock workflow
doc (the repo contains `cmd/spacedock`, or the user says spacedock / FO /
ensign / gate), use Spacedock fixtures.
Spacedock fixtures are isolated before/after test repos. The real Spacedock
binary creates their workflow state. Do not create this state by editing files.
Before designing the run, read
`references/spacedock-duo.md` inside this skill's base directory. It chooses
the single-role or two-agent path. Create the fixtures with
`make-spacedock-fixtures.sh` from this skill's bundled `scripts/` directory.

## Steps

1. **Find the change.** In the user's current git repo, run
   `git status --porcelain` and keep only modified instruction files
   (CLAUDE.md, AGENTS.md, SKILL.md, agent-facing README.md). Exactly one
   candidate: use it. Several: ask the user which one. None: explain that
   the change must exist as an uncommitted edit first, and stop.
   Then read `git diff -- <file>` so you understand what rule changed.

   Three cases have no git "before", and each still works:
   - **Untracked file** (git does not know it — e.g. `~/.claude/CLAUDE.md`):
     the plugin's backup hook saved the pre-edit original under
     `${BEHAVIOR_DIFF_HOME:-~/.behavior-diff}/baselines/`, and the runner
     resolves the newest one by itself — run it with the same arguments.
     A parallel session may have saved a newer baseline than the change
     you mean to test; if the report's diff looks too small, pick the
     right entry from that store and pass it as `--before-file`.
     If the runner exits saying no baseline exists, ask the user for the
     original content and pass it as `--before-file <path>`.
   - **User-given before/after files** ("compare A.md and B.md"):
     run with `--file B.md --before-file A.md`.
   - **Non-git folder**: the runner builds both sandboxes from a plain
     copy of the working folder instead of a HEAD snapshot. Every trial
     copies the whole folder, so run from the smallest folder that holds
     the file; the "before" still needs a baseline or `--before-file`.

   In these cases read the change with `diff <before> <file>` instead of
   `git diff`.

2. **Draft the task.** `--task` must recreate the moment right before the
   agent used to make the wrong choice:
   - Ask the user for the real request from the incident that motivated
     the rule, and reuse it when they have one.
   - Never leak the expected behavior into the task. The changed rule must
     be the only place the guidance exists — if the task itself says what
     "good" looks like, both variants will comply and the diff shows
     nothing.
   - When the rule fires mid-task, start the task at the decision point:
     "You already did X (it is in the tree); decide/report Y."

3. **Run it as soon as the task is known.** Do not ask the user to confirm
   the file, task, cost, or run mode. Do not mention trial counts, cost, or
   full versus fast modes during normal execution. Preserve the current stack
   by passing `claude` under Claude Code or `codex` under Codex, then start the
   runner from the repo root in the background:

       behavior-diff.sh --agent <current-host> --file <file> --task "<task>"

   Only add `--fast` when the user explicitly requested it in the current
   request with `fast`, `--fast`, `two runs`, or `one trial per side`:

       behavior-diff.sh --agent <current-host> --file <file> --task "<task>" --fast

4. **Present the result.** The runner already opened `report.html` itself — do NOT open it again (that produces a duplicate tab); just summarize.
   Summarize the flow diff honestly:
   - Flows diverge → describe where, in one or two sentences.
   - Flows identical → say the task likely never reached the situation
     the rule targets, and suggest a sharper task. Do NOT claim the rule
     works or fails from identical flows.

## Boundaries

- The runner never modifies the user's repo; reports and traces stay
  local under the runs root above.
- The report quotes the user's real code. Never publish it anywhere
  without the user reviewing it first.
- Do not edit the user's instruction file yourself — this skill only
  measures a change the user already made.
