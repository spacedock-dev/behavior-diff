---
name: run-behavior-diff-demo-journey
description: Drive the behavior-diff live demo in a herdr split pane — sandbox, a real second agent session on claude or codex, the nudge firing, the diff running, the report. Use for "run the behavior-diff demo", "demo the nudge journey", "show the behavior diff live", "demo it on codex", or before showing behavior-diff to anyone.
---

# behavior-diff live demo journey

You drive a second, real agent session in a pane beside you. The audience
watches that pane; you narrate. The payoff is one screen: the same task, the
same project, and one added `AGENTS.md` rule changes the agent's decision and
the user's result.

Background and the fixtures themselves: `e2e/README.md`.
Do not duplicate its content here — read it if a step needs context.

## Preflight — fail fast, before an audience is watching

Stop and say what is wrong if any of these fail. Do not improvise a fix
mid-demo.

1. `HERDR_ENV` is `1` and `herdr` is on PATH. If not, this skill does not
   apply — offer the plain terminal steps from the e2e README instead.
2. **Ask which agent drives the session** unless the user already said:
   `claude` (default model sonnet) or `codex` (default gpt-5.6-terra).
   Both carry the nudge hooks. The ask rate is a property of the agent, so
   demoing on the one your audience uses is the honest choice.
3. **Choose the fixture** unless the user already said:
   - `demo` — the main technical pricer story.
   - `demo-invoice-review` — the main non-developer story.
   - `demo-inbox-cleanup` — a simple output-diff smoke case, not a
     behavior-flow demo.
   - `demo-ascii-response` — the vague-rule demo. One line with no trigger
     point ("use ASCII to visualize content when explaining concepts").
     Nothing breaks; the point is that you can see what the rule did.
     Use it alongside `demo-invoice-review` — that one shows a rule change
     having a consequence, this one shows an unverifiable rule becoming
     verifiable.

   Use `demo` by default. In the commands below, replace `<fixture>` with the
   selected name.
4. Then the checks for that agent:

   **claude** — the plugin is enabled (`behavior-diff@spacedock` in
   `~/.claude/settings.json`), and the installed hooks match this repo's
   source, so you are not demoing an old build:

       diff -q ~/.claude/plugins/cache/spacedock/behavior-diff/*/hooks/hooks.json \
         plugin/hooks/hooks.json

   **codex** — three things, each of which fails *silently* and looks
   exactly like "the nudge does not work":
   - `[features] hooks = true` in `~/.codex/config.toml`, or hooks never run.
   - Every hook entry needs a one-time trust approval, given in an
     interactive Codex session. Do that before the audience arrives.
   - Codex runs a cache snapshot, not the marketplace source. After any
     plugin change: `codex plugin add behavior-diff@spacedock`.


## The journey

**1. Sandbox.** From the repo root:

    NUDGE_E2E_FIXTURE=<fixture> tests/nudge-e2e.sh setup
    # add NUDGE_E2E_AGENT=codex for a Codex demo

Read what it prints; it carries the session command for the chosen agent,
plus the prompt and the task for this fixture. Use the printed command rather
than composing your own — that is what keeps this skill and the harness from
drifting apart.

**2. Open the pane.** Ids are not durable — read yours fresh, never reuse
one from an earlier run:

    herdr pane list          # yours is the focused one
    NEW=$(herdr pane split <your-pane> --direction right --no-focus \
      | python3 -c 'import sys,json; print(json.load(sys.stdin)["result"]["pane"]["pane_id"])')
    herdr pane run "$NEW" "<the session command step 1 printed>"

For reference, that is `claude --model sonnet` or `codex -m gpt-5.6-terra`,
both prefixed with `cd /tmp/nudge-e2e && BEHAVIOR_DIFF_HOME=/tmp/nudge-e2e-state`.

Wait for the prompt to appear, then read the pane to confirm it says the
hooks loaded.

**3. The edit.** Send the rule prompt from step 1's output. Never mention
behavior-diff in it — if you do, the prompt caused the ask, not the hook,
and the demo is a lie. Narrate while it works: *nobody told it to run a
check; a hook noticed the rule file changed.*

**4. The ask.** The agent should ask, unprompted, whether to run
behavior-diff. This is the beat the demo exists for — let it sit on screen.

What it looks like differs by agent, and both count: Claude renders a
two-option AskUserQuestion (Run behavior-diff / Skip); Codex has no such
tool, so the whisper's fallback applies and the ask arrives as one plain
sentence. Say which you expect before it happens, so a plain sentence does
not read as a failure.

The ask has been seen answered without anyone pressing a key. The setup
prompt therefore includes the exact fixture task as a later request, while
telling the agent not to answer it during the edit turn. If auto mode accepts
the ask, the task is already in context.

Confirm the state behind the ask if you want the receipts:

    NUDGE_E2E_FIXTURE=<fixture> tests/nudge-e2e.sh check

When the ask stays on screen, do not select the bare **Run behavior-diff**
option. Accept it with the exact scenario instead. For Claude, select
**Type something**; for Codex, answer its plain question. Send:

    Run behavior-diff with this exact task:

    <the exact task step 1 printed>

The skill starts the comparison as soon as it has the task. There is no later
run-count or task-confirmation gate. If the driven agent starts with a
different task, interrupt it and stop: the demo contract failed.

**5. The payoff.** When the run finishes, read the pane and show the two
results.

For `demo`, show the two flows before the two answers. Expect before: use the
supplied passing replay, decide `FIXED`, and close the ticket. Expect after:
read `discount.py`, identify floor division as a risk, run a decimal-price
case, decide `NOT FIXED`, and keep the ticket open. Say: *same task, one rule,
different route, different evidence, different customer result.*

For `demo-inbox-cleanup`, focus on the messages that change. Expect before to
keep the parcel update and the class cancellation. Expect after to archive
both. Say: *the new rule removes the routine delivery update Emma wanted to
remove, but it also hides an important cancellation notice. Behavior-diff
showed the consequence before the rule controlled her real inbox.*

For `demo-invoice-review`, read
`e2e/demo-invoice-review/expectations.md` only after the trials
finish. Never send it to the driven agent. Expect before to inspect supplier
trust and payment history, find the duplicate invoice, and return `HOLD`.
Expect after to stop after supplier and amount checks and return `APPROVE`.
Say: *the shortcut bypassed an observable safeguard: the agent stopped
checking whether the invoice was already paid. That changed the decision and
created a duplicate-payment risk.* If the record-inspection paths did not
diverge, say the case did not demonstrate a meaningful behavior-flow change.

For `demo-ascii-response`, read
`e2e/demo-ascii-response/expectations.md` only after the trials
finish. Expect both sides to read the same records and reach the same cause —
identical flows are this fixture's point, not a failure. The single observable
is whether the answer contains a drawn timeline: measured at 1 of 6 before
trials and 6 of 6 after. Show the two answers side by side and say: *same
records, same cause, same conclusion — the only thing that changed is that
the answer is now a picture. She wrote one line hoping it would help, and it
took one run to see that it fired.* Say the honest part too: nothing here is
broken, and that is the point — this fixture is about seeing what a rule did,
not about catching a bug. Use repeated trials for consistency claims; one
sample only shows one outcome.

**6. Optional beat — the Stop line.** Only if someone asks what happens
when the agent stays quiet:

    NUDGE_E2E_FIXTURE=<fixture> tests/nudge-e2e.sh drop-whisper

Then any trivial message in that pane; the turn ends with one
`Stop says: 📊 …` line, and the next turn is silent.

**7. Clean up.** Ask first if they want the report kept — `reset` deletes
the state directory the reports live in.

    herdr pane close "$NEW"
    NUDGE_E2E_FIXTURE=<fixture> tests/nudge-e2e.sh reset

## When it goes wrong on stage

- **A stray keystroke sits in the input box.** `herdr pane send-keys "$NEW"
  ctrl+u` before the next `pane run`, or your prompt appends to it.
- **The agent did not ask.** That is a real result, not a bug to hide —
  say so, and note it as a data point on the ask rate. Do not re-prompt it
  into asking; that invalidates the demo.
- **Escape stops the agent, not the shell it started.** If a run is already
  in flight, `ps aux | grep behavior-diff.sh`.
- **A run starts with the wrong task.** Interrupt it immediately and stop.
  There is no later confirmation gate; a run against another scenario is not
  demo evidence.

## Boundaries

- Never demo against the user's real repo — the sandbox exists so the edit,
  the reports, and the hook state stay in `/tmp`.
- Never edit the driven pane's files yourself. Everything the audience sees
  must come from the agent in that pane.
- One pane, closed when done.
