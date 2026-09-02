# Behavior-check PoC

Spike for the paired before/after simulation in
[`plans/engram-behavior-check-research-survey.md`](../plans/engram-behavior-check-research-survey.md):
does changing only one rule change the agent's observable next action?

- `e2e/` — the fixtures a run is driven from. Each holds a synthetic
  project, the task at the decision point, and the rule block to add.
  Everything here is synthetic; nothing comes from a real transcript.
  - `e2e/capsule/` — the frozen rk-monitor incident capsule (post-"fix"
    state, passing unit tests, a functional smoke check that is missing).
    The harder case, and what `tests/nudge-e2e.sh` uses by default.
  - `e2e/demo/` — the pricer: a passing ticket replay leads the before agent
    to close the ticket; a proposed verification rule reroutes the after
    agent through code inspection and a targeted counterexample. For showing
    someone a different flow, decision, and result.
  - `e2e/demo-inbox-cleanup/` — a non-developer backup: a broader cleanup
    rule archives the intended delivery update, but also hides an important
    event cancellation. Keep it as a simple output-diff smoke case.
  - `e2e/demo-invoice-review/` — the non-developer behavior-flow demo: a
    quick-review shortcut may skip payment history and approve a duplicate invoice.
    It shows different evidence, decision, and business result.
  - `e2e/demo-ascii-response/` — the vague-rule demo: one line with no
    trigger point ("use ASCII to visualize content when explaining
    concepts"). Nothing breaks — both agents read the same records and reach
    the same cause. Only the answer changes: 1 of 6 before trials drew a
    diagram, 6 of 6 after trials did. Use it to show that a rule nobody can
    normally check becomes checkable in one run.
- `bin/behavior-diff` — the quick front door. Point it at a markdown file
  holding the rule you are considering; it appends that rule to the repo's
  CLAUDE.md (or AGENTS.md), runs the diff, and restores the file exactly.
  You never paste a rule in by hand, and a rule you decide against leaves
  no trace:

      behavior-diff my-rule.md --task "the scenario the agents get" [--fast]
      behavior-diff my-rule.md --dry-run        # show the edit, run nothing

  It refuses to touch a target that already has uncommitted changes, so the
  diff can only be measuring the rule. Put it on your PATH with a symlink:
  `ln -s "$PWD/bin/behavior-diff" /usr/local/bin/behavior-diff`.

Run the demo:

    NUDGE_E2E_FIXTURE=demo tests/nudge-e2e.sh setup    # sandbox at /tmp/nudge-e2e
    cd /tmp/nudge-e2e
    behavior-diff <repo>/behavior-diff/e2e/demo/rule.md --into AGENTS.md \
      --task "$(cat <repo>/behavior-diff/e2e/demo/task.md)" --fast

Run the non-developer behavior-flow demo:

    NUDGE_E2E_FIXTURE=demo-invoice-review tests/nudge-e2e.sh setup

The invoice fixture replaces a rule section. Drive it through the printed
session command; do not use the append-only `bin/behavior-diff` front door.

Run the vague-rule demo (an appended rule, so the front door works):

    NUDGE_E2E_FIXTURE=demo-ascii-response tests/nudge-e2e.sh setup
    cd /tmp/nudge-e2e
    behavior-diff <repo>/behavior-diff/e2e/demo-ascii-response/rule.md --into AGENTS.md \
      --task "$(cat <repo>/behavior-diff/e2e/demo-ascii-response/task.md)" --fast

## Your own change, not the demo

`behavior-diff.sh` runs the same before/after engine on a real local
change. From a git repo where an instruction file (CLAUDE.md, a skill's
SKILL.md/README.md) has uncommitted edits:

    behavior-diff.sh --file CLAUDE.md --task "one-line scenario" [--fast]

Before = the repo at HEAD; After = the same snapshot plus only your
working-tree version of that file (other uncommitted edits stay out).
The report shows your git diff, a generic-vocabulary flow diff, and
every trial's commands and final answer — with **no automatic verdict**
(there is no per-case grading contract), so the banner asks you to
compare the flows and answers yourself. The task must exercise the
situation your change is about, or both variants will behave the same.

`plugin/` is the installable `behavior-diff@engram` plugin, and its
`skills/` directory IS the canonical source — no mirror, no materialize
step. Install via the marketplace one-liner in the repo README, or copy a
skill directory into `~/.claude/skills/` (behavior-diff carries `scripts/`
and `references/` inside it; the live and retro skills reference it as a
sibling, so install behavior-diff alongside them). No absolute paths in
skill content; runs land under `${BEHAVIOR_DIFF_HOME:-~/.behavior-diff}/runs/`.

`plugin/skills/behavior-diff/scripts/make-capsule.sh` mints binary-valid spacedock FO↔worker
capsules (phases: worker-mid, briefing-open, revise-recorded) with a
built-in precheck. `plugin/skills/behavior-diff/references/spacedock-duo.md` is the shared spacedock
module both skills load when the change is a workflow rule: it routes
single-role rules through the normal flow (capsule fixtures,
`--vocab spacedock`) and handoff rules through the two-agent worker→FO
duo cycle. `plugin/skills/behavior-diff-retro/SKILL.md` writes a retro into a
finished run dir and feeds durable lessons to `RETRO_NOTES.md`.

`plugin/skills/behavior-diff-live/SKILL.md` is the in-session variant: one trial
per side run as subagents the main agent launches and watches — for
experiments where you adjust the scenario and want visible progress.
Weaker evidence by design (single sample; subagents are told to read the
variant's CLAUDE.md rather than loading it natively) and it says so.

`plugin/skills/behavior-diff/SKILL.md` wraps the headless runner as an agent skill (install by
copying to `~/.claude/skills/behavior-diff/`): the agent finds the changed
file, drafts a leak-free task, confirms cost, runs the script, and
summarizes the report honestly.

## Hooks: the nudge (0.3.1)

A plugin install also brings two hooks so the product finds its own
moment — Claude Code and Codex both run them (see the Codex caveats
below). `plugin/hooks/hooks.json` registers:

- **PostToolUse** (`Edit|Write|MultiEdit`) → `rules-edit-detect.sh`: when
  the agent edits a `CLAUDE.md`, `AGENTS.md`, or `SKILL.md`, the path is
  recorded once per session under
  `${BEHAVIOR_DIFF_HOME:-~/.behavior-diff}/nudge/`, and — once per
  session — the hook whispers an `additionalContext` instruction to the
  agent: when the current task is done, ask the user whether to run
  behavior-diff (AskUserQuestion if available, one plain sentence
  otherwise; ask once, never run without an explicit yes).
- **Stop** → `rules-edit-remind.sh`: the fallback. If no whisper was sent
  this session and a recorded file still has uncommitted changes, one
  `systemMessage` line asks the user to run `/behavior-diff` before
  committing. A whispered session is silent here — the agent owns the
  question, and a second line would duplicate it right after the user
  answered. Once per session (claim by rename), single line only (the
  Stop surface prefixes every line), never a control key, every exit
  path `exit 0`.

Trials cannot nudge themselves: `run-trial.sh` exports
`BEHAVIOR_DIFF_TRIAL=1` and both hooks exit on it (the variable inherits
into Codex hook processes too). Hand edits made outside a session fire no
hook — the skill's own `git status` scan still catches them when invoked.

### Codex

The same two hooks run on Codex — no separate adapter. Codex
auto-discovers the plugin's `hooks/hooks.json`, maps `apply_patch` edits
into the `Edit|Write|MultiEdit` matcher, and delivers the
`additionalContext` whisper (verified live on codex-cli 0.149.1). Codex
sends no `tool_input.file_path`; `rules-edit-detect.sh` falls back to
reading the edited paths from the apply_patch grammar in
`tool_input.command` and joins them to the payload's `cwd`. Three caveats:

- Codex hooks are feature-flagged: set `[features] hooks = true` in
  `~/.codex/config.toml` or the hooks never run.
- Each hook entry needs a one-time trust approval in an *interactive*
  Codex session — `codex exec` never prompts and silently skips untrusted
  hooks.
- Codex runs a cache snapshot of the plugin, not the marketplace source:
  after updating the plugin, run `codex plugin add behavior-diff@engram`
  again to refresh the snapshot.

Self-check: `bash tests/hooks-test.sh` (fake payloads, no model). Live
delivery is a manual check, still owed — and it must verify the whisper
actually reaches the agent: if `additionalContext` goes undelivered on
this surface, remove the Stop suppression in `rules-edit-remind.sh`.

PoC boundaries, deliberately not the product: Claude-only, no redaction
(synthetic capsule), report stays in `runs/` (gitignored) instead of
`~/.engram/reports/`, the agent's global user CLAUDE.md is not isolated
(identical for both variants, so the comparison holds), and effectful
tools are excluded via allowlist rather than intercepted.
