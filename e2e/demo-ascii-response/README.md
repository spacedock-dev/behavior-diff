# ASCII-response demo — a vague rule you can finally check

Emma runs a small online shop. She struggles to follow her assistant's
explanations when they are all words, so she adds the kind of line people
really do put in `CLAUDE.md`:

> ## How to explain
>
> Use ASCII to visualize content when explaining concepts.

One sentence. No trigger point. Nothing says which explanations count as
"concepts", or how much drawing is enough, or when it applies at all.

That is what makes rules like this go unchecked. You write one, hope it helps,
and never find out whether it did anything — because you only ever see one
answer at a time, and you have nothing to compare it against.

Behavior-diff asks the same question with and without the rule, and puts the
two answers next to each other.

## The test case

Emma asks: *a customer got Tuesday's payment reminder twice — why?*

The cause is in the records. The mail service accepted the first reminder but
replied too slowly, the helper script gave up after 30 seconds and sent it
again, and customer #131 received both emails.

The route is not expected to change, and it doesn't. Both sides read the same
three records and find the same cause. The diff lives entirely in the answer
Emma reads.

| Observable result | Before | After the rule |
|---|---|---|
| Records inspected | log, mail activity, script | the same |
| Cause found | duplicate send after a slow reply | the same |
| ASCII drawing in the answer | **1 of 6 trials** | **6 of 6 trials** |
| Shape | numbered prose | a drawn timeline, often after a one-line summary |

## What the two answers look like

**Before** — the sequence as numbered prose:

> 1. `send-reminders.py` sent the reminder for order 5540 at 09:00:04.
> 2. The mail service actually sent the email (`m-88339`, delivered 09:00:33)
>    — but its reply back to the script took longer than 30 seconds.
> 3. The script's timeout fired at 09:00:34, assumed the send had failed, and
>    sent a second email (`m-88342`).

**After** — the same sequence, drawn:

```
09:00:04  script sends reminder for order 5540 (customer #131)
09:00:33  mail service actually sends it  (m-88339) ─┐  script hasn't
                                                     │  heard back yet
09:00:34  script's 30s timer runs out, assumes lost, │
          sends it AGAIN                             │
09:00:35  mail service sends the retry (m-88342) ────┘
```

Same records. Same cause. The answer is now drawn — and the after side also
tends to open with a one-line plain summary first, which the rule never asked
for.

## What to say during the demo

Before the run:

> Emma added one line: "use ASCII to visualize content when explaining
> concepts." It's the kind of rule everybody writes and nobody checks — you
> can't tell from a single answer whether it did anything. Behavior-diff asks
> the same question with and without it.

After the run:

> Same records, same cause, same conclusion. The only thing that changed is
> that the answer is now a picture. She wrote one line hoping it would help,
> and it took one run to see that it fired — and what shape it took.

Say the honest part too: **nothing here is broken.** Both answers are correct.
This fixture is not about catching a bug — it is about seeing what your rule
actually did. That is a different job from `demo-invoice-review`, which shows
a rule change removing a safeguard.

`expectations.md` holds the measured numbers and what Emma is looking for. The
live-demo operator reads it only after the trials finish. It must never be
copied into the sandbox or sent to a trial agent.

## Instruction-file layout

`project/AGENTS.md` is canonical and has no explanation-style section — the
rule is a pure append. `project/CLAUDE.md` only imports it. `edit-prompt.md`
asks the driven agent to add the section. `project/pending-request.md` holds
the exact neutral task. The record-access rule lets the driven agent read that
request while preparing a comparison, but keeps the shop records off-limits
until an isolated trial answers the question — otherwise the payoff answer is
on screen before the trials run. All records are synthetic.

## Run the journey

From the repository root:

    NUDGE_E2E_FIXTURE=demo-ascii-response behavior-diff/tests/nudge-e2e.sh setup

The setup command prints the isolated session command, edit prompt, and neutral
task. Because the rule is an append, the append-only `bin/behavior-diff` front
door also works, without a driven session:

    cd /tmp/nudge-e2e
    behavior-diff <repo>/behavior-diff/e2e/demo-ascii-response/rule.md --into AGENTS.md \
      --task "$(cat <repo>/behavior-diff/e2e/demo-ascii-response/task.md)" --fast

`--fast` is one trial per side — enough to show the shape in a live demo, and
it settles nothing on its own. This fixture was first read at one trial per
side and the reading was wrong in its emphasis; the numbers in
`expectations.md` come from the full three-per-side run. Drop `--fast`
whenever the question is whether the rule fires *consistently*.
