# e2e — fixtures and how to run them

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

The two demos that carry the product story are `demo-invoice-review` and
`demo-ascii-response`, and they show different things:

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
prints the session command for the chosen agent — `claude --model sonnet`
or `codex -m gpt-5.6-terra` — plus the prompt and exact neutral task. The steps
are:

Both stacks carry the nudge hooks, and the ask rate belongs to the agent,
so the journey is worth running on each. Codex needs three things first,
each of which fails silently: `[features] hooks = true` in
`~/.codex/config.toml`, a one-time interactive trust approval per hook
entry, and `codex plugin add behavior-diff@engram` after any plugin change
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
on the prompt). It matters only for Journey A's Skip branch: if something
answers before you do, that is not the agent's choice — note it and re-run.
It does not cause a surprise spend. The behavior-diff skill states its cost
and waits before starting any trials, which is a separate gate that holds
either way.

**A stray keystroke sits in the input box.** `herdr pane send-keys "$NEW"
ctrl+u` clears it before your next `pane run`, or your prompt gets appended
to whatever was there.

**Escape interrupts the agent, not the background shell.** If the skill
already launched `behavior-diff.sh`, that keeps running after the interrupt;
`ps aux | grep behavior-diff.sh` to check, and remember the skill stops at
its own confirmation gate before spending trials.

**Headless is not a substitute for the interactive check.** `claude -p`
fires both hooks and is a fine smoke test, but it has no AskUserQuestion
(the agent falls back to a plain sentence) and it does not render the Stop
hook's `systemMessage` at all. Both of those need a real session.

**The sandbox holds the reports.** `reset` deletes `/tmp/nudge-e2e-state`,
and the run reports live under it. Copy anything you want to keep first.
