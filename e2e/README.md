# e2e — fixtures and how to run them

## Default manual verification examples

Use all three Recce-Team historical skill cases when manually verifying Behavior
Diff modifications:

| Skill | Verification focus |
|---|---|
| `claude-code-review` | Review/fix workflow, final review state, and the distinction between planned and executed actions. |
| `tdd-from-spec` | Implementation notes, file-state evidence, and unsupported claims about ignore or staging safety. |
| `decision-debate` | Direction generation versus interviewing, shared behavior, and sequencing differences. |

Use the pinned revisions, companion-file requirements, and retained evidence
records in the [Recce-Team runbook](recce-team-first-edit-attention.md).
Their previous exclusion or inconclusive status concerns **side-effect detection
demos**, not their use as real-world verification examples. Do not relabel any
case as a successfully detected regression.

For renderer changes, reuse saved extraction inputs unchanged and compare the
old and new renderer on all three cases. For extractor changes, reuse frozen
trial evidence and obtain approval for new extraction calls. For changes to
scenario drafting or trial execution, saved reports alone are insufficient:
obtain fresh approval for the affected live steps. Record each case's result or
the exact missing evidence; do not silently substitute a synthetic scenario.
Inspect the changed surface and its supporting evidence, preserving unchanged,
minority, and inconclusive outcomes.

Keep private sources, trials, reports, and temporary comparisons outside this
checkout. No model-backed verification runs in CI. Synthetic fixtures remain
the deterministic test set and supplemental edge-case examples.

## Local verification handoff prototype

For the isolated, conversational handoff-to-decision replay, explicitly load
[the maintainer skill source](../.agents/skills/verification-handoff-prototype/SKILL.md)
in Claude Code or Codex, then supply the change, permitted context and case root.
OMP can load that same path; this is not an installed-plugin or runtime-adapter claim.
The host operates the helper; the owner should not have to choose evidence IDs.

Python 3.10+ is sufficient. The skill includes the one-command helper invocation
and `fixtures/synthetic.json` for an offline, invented demonstration. Run its
deterministic behavior checks separately with:

```sh
python3 tests/verification-handoff-prototype-test.py
```

Use a mode-0700 directory outside all Git trees for mode-0600 session/packet files.
Real-case packets are privately prepared from permitted local sources, not shipped
with the repository; a fresh checkout can run only the synthetic demonstration.
Replay corrections invalidate changed-goal support and require current confirmation;
missing evidence remains actionable and unverified. No trials or external actions run.
An actual owner conversation must still exercise correction, evidence inspection
and a gap, and record real takeover points versus their baseline privately.
Helper checks alone do not establish acceptance, handoff value or live latency.

## Optional Jev manual verification

Run `python3 tests/jev-test.py` first. Its injected transport and subprocess
smoke checks exercise the shipped helper without sending data or making model
calls. Static skill checks cover wiring only, not agent compliance or usefulness.

Live verification is separate: obtain current pricing and explicit approval
for TypeSafe, synthetic payloads, host inference, and a dollar ceiling before
running. Use one baseline and one Jev-enabled session on each of Claude Code and
Codex (four sessions). Freeze one synthetic observation packet and two candidates,
plus an independently authored evidence key, before either session sees them.
Include a recorded failed check and an absent publish/merge approval.
Use inert action recorders, never real external actions.

- AC-1: Compare which evidence is inspected first, finding classification,
  criterion support, and competing hypotheses. Require one concrete
  evidence-backed decision clarified/corrected over baseline, without regression
  against primary evidence. A null result fails the value claim; do not retune.
- AC-2: Capture one `judge` with all independent questions and one `judge_batch`
  with two keyed candidates under a shared Score rubric per enabled session:
  at most six Jev state requests total, no retries. Check association and actual
  host operation choice, not just helper capability.
- AC-3: Exercise missing configuration and injected provider denial as well as
  approved success. The workflow must continue honestly; check private scratch
  output/diagnostics for credentials and unintended payload persistence.
- AC-4: Inject a favorable judgment despite the failed check. Keep the
  contradiction visible and frozen inputs/reports unchanged; the inert recorder
  must show no unauthorized publish/merge action.
- AC-5: Inspect final responses for useful, no-opportunity, missing-key,
  denied-approval and failed-provider cases. Count zero requests for the three
  skips; require the actual reason or decision impact, not a new report panel.

Keep invocation records private. Record host/helper revision, observed decisions,
request counts, failures and remaining gaps. The saved real cases above remain
supplemental evidence requiring separate content approval before TypeSafe sends;
missing private evidence is a gap, not permission to invent an equivalent.

## Synthetic nudge fixtures

Five fixtures. Each is a synthetic project, a task that stops on a decision,
and the rule block to add:

| Fixture | Proposed rule | Before | After | Use it for |
|---|---|---|---|---|
| `capsule/` (rk-monitor) | require a functional key-input test | reports the fix unverified | looks for the missing smoke check and reports unverified | Testing the harness |
| `demo/` (pricer) | inspect, form a risk hypothesis, then test | accepts the passing replay and closes the ticket | tests decimal prices and keeps the ticket open | Main technical demo |
| `demo-invoice-review/` | add a quick-review shortcut | checks payment history and holds a duplicate | may skip history and approve it | Main non-developer demo |
| `demo-inbox-cleanup/` | archive automated mail with no requested action | keeps a parcel update and a cancellation notice | archives both messages | Output-diff smoke case |
| `demo-ascii-response/` | use ASCII to visualize when explaining | numbered prose, almost never a drawing (1/6) | a drawn timeline (6/6) | Main vague-rule demo |

Pick with `NUDGE_E2E_FIXTURE=capsule|demo|demo-invoice-review|`
`demo-inbox-cleanup|demo-ascii-response`. See each demo's README for its full
story.

Two synthetic examples illustrate different product stories; they supplement,
not replace, the real-world manual verification set:

- **`demo-invoice-review`** — a *workflow* rule change. The new rule routes
  around a safeguard, so the agent checks different records and reaches a
  different decision. Use it to show a rule change having a consequence.
- **`demo-ascii-response`** — a *vague* rule change. One line with no trigger
  point ("use ASCII to visualize content when explaining concepts"). Nothing
  breaks: both answers are correct and both agents read the same records. The
  point is only that you can see what the rule did — 0 of 3 trials drew a
  picture before, 3 of 3 after. Use it to show that a rule nobody could
  normally check becomes checkable in one run.

`demo-inbox-cleanup` is a simple output-diff smoke case. `capsule` is for
testing the harness.

For the historical Recce-team decision-routing case, use the
[first-edit side-effect demo runbook](recce-team-first-edit-attention.md).
It compares the initial edit with its parent and evaluates the generated
**What needs your attention** section. The first replay did not reproduce the
historical side effect. Two excluded candidates remain recorded for provenance.
Later corrections are evaluator-only references; this is a manual
report-evaluation journey, not a sixth nudge fixture.

For new public-history leads, see the
[public skill side-effect candidates](public-skill-side-effect-candidates.md).
It records three candidates outside the earlier surveys, their historical
evidence, proposed replay boundaries, and licensing limits. These are research
leads, not validated demos or approval to run model-backed trials.

## What is actually being tested

The nudge is two hooks. `PostToolUse` notices an edit to CLAUDE.md /
AGENTS.md / SKILL.md, records it, and whispers to the agent once per
session: *when the task is done, ask the user whether to run behavior-diff.*
`Stop` is the fallback — it prints one reminder at end of turn, but only if
that whisper never went out.

Payload-level behavior is already covered without a model. What no script
can fake is whether the whisper reaches a live agent and whether the agent
then asks. That is what the journeys below are for.

## 1. The automated checks (no model, seconds)

Run these first — anything they catch is not worth a live session.

    bash ../tests/hooks-test.sh        # 14 scenarios, 27 assertions
    python3 ../plugin/skills/behavior-diff/scripts/decisions.py --check

## 2. The live journeys

    ../tests/nudge-e2e.sh setup        # NUDGE_E2E_FIXTURE=demo for the pricer
                                       # demo-invoice-review for non-developers
                                       # NUDGE_E2E_AGENT=codex for Codex

That builds a sandbox repo at `/tmp/nudge-e2e` and isolated hook state at
`/tmp/nudge-e2e-state`, so your real `~/.behavior-diff` is untouched. It
prints the session command for the chosen agent — `claude --model opus`
or `codex -m <resolved-model-id>` — plus the prompt and exact neutral task.
Codex defaults to the Behavior Diff selector `sol`, not a Codex CLI alias.
The shared `plugin/skills/behavior-diff/scripts/codex_model.py` helper queries
`codex debug models` and resolves the newest numeric stable
`gpt-<version>-sol` with `visibility=list`. Setup resolves once and prints
the exact ID; headless trials use one resolved ID for the entire invocation.
Set `NUDGE_E2E_MODEL=<exact-model-id>` to pin another model without catalog
discovery, or set it to `sol` to use the selector explicitly. Claude uses
Opus by default. `check`, `drop-whisper`, `reset`, and usage do not
discover a model or require Codex CLI access.

Both stacks carry the nudge hooks, and the ask rate belongs to the agent,
so the journey is worth running on each. Codex needs three things first,
each of which fails silently: `[features] hooks = true` in
`~/.codex/config.toml`, a one-time interactive trust approval per hook
entry, and `codex plugin add behavior-diff@spacedock` after any plugin change
(it runs a cache snapshot, not the source). Codex also has no
AskUserQuestion, so the ask arrives as one plain sentence rather than a
two-option prompt.

**Journey A — the whisper reaches the agent.** Start the session it printed,
then paste the rule prompt. The capsule rule goes into `CLAUDE.md`; the demo
rules go into canonical `AGENTS.md`, while `CLAUDE.md` imports that file.
Say nothing about behavior-diff: if you mention
it, your prompt caused the ask and the test proved nothing. The agent should
edit the named instruction file and then ask, unprompted, whether to run
behavior-diff.

Assert what it left behind, from another terminal:

    ../tests/nudge-e2e.sh check

Four things should pass: the edit recorded, the fixture's instruction file
is the recorded path, exactly one path (non-instruction files ignored), and
the whisper marker is present.

**Journey B — the Stop fallback.** It never happens naturally, because the
whisper fires first and suppresses it, so force it:

    ../tests/nudge-e2e.sh drop-whisper

Send any trivial message and end the turn. Expect exactly one line:

    Stop says: 📊 AGENTS.md changed this session — run /behavior-diff …

The demo fixtures show `AGENTS.md` in that line. The capsule fixture shows
`CLAUDE.md`.

End another turn: silence. The state file is now `*.edits.spoken` — the
reminder is claimed once per session.

    ../tests/nudge-e2e.sh reset        # deletes the sandbox AND any reports in it

Journey A is model behavior, not code. Run it a few times and record how
often it asks; that ask rate is the finding. If it turns out low, the Stop
hook's suppression should be removed so the fallback line carries the
journey — `rules-edit-remind.sh` already says so in a comment.

## 3. Driving it from herdr, on a split pane

Useful for a demo: your agent session drives a second, real agent session
beside it, and the audience watches both. Requires `HERDR_ENV=1`.

Get your own pane id — yours is the focused one, and ids are not durable, so
read them fresh every time:

    herdr pane list

Split right, keeping focus where you are, and capture the new id:

    NEW=$(herdr pane split <your-pane> --direction right --no-focus \
      | python3 -c 'import sys,json; print(json.load(sys.stdin)["result"]["pane"]["pane_id"])')

Start the sandbox session in it:

    herdr pane run "$NEW" "<the session command setup printed>"

Give it the prompt, then read what happened (`pane run` sends the text and
Enter together):

    herdr pane run "$NEW" "Add this to <the printed instruction file>: <the rule>"
    herdr pane read "$NEW" --source recent --lines 35

Drive the rest the same way — `drop-whisper` between turns for Journey B,
`herdr pane read` to see the Stop line render. When you are done:

    herdr pane close "$NEW"

### What will bite you

**The ask can get answered without you.** It has happened in a driven
pane; the cause was never pinned down (auto mode, or a stray Enter landing
on the prompt). Take the session out of auto mode before you send the rule
prompt, and approve the rule-file edit by hand. A run against another
scenario is invalid demo evidence; interrupt it and stop.

**The edit turn must not carry the task.** It used to, so that an
auto-accepted ask still had the task in context. That backfired on two
fixtures: told the rule was "meant to affect this later request", the agent
worked out what would change, which meant opening the business records the
payoff depends on staying unread — and on `demo-invoice-review` it then
refused the edit as a fraud-control gap. Manual mode replaces that
safety net.

**A stray keystroke sits in the input box.** `herdr pane send-keys "$NEW"
ctrl+u` clears it before your next `pane run`, or your prompt gets appended
to whatever was there.

**Escape interrupts the agent, not the background shell.** If the skill
already launched `behavior-diff.sh`, that keeps running after the interrupt;
check the process directly. There is no later confirmation gate.

**Headless is not a substitute for the interactive check.** `claude -p`
fires both hooks and is a fine smoke test, but it has no AskUserQuestion
(the agent falls back to a plain sentence) and it does not render the Stop
hook's `systemMessage` at all. Both of those need a real session.

**The sandbox holds the reports.** `reset` deletes `/tmp/nudge-e2e-state`,
and the run reports live under it. Copy anything you want to keep first.
