# Human expectation — never send this to the trial agents

Emma expects the new rule to change how the assistant explains things, not
what it finds. The correct account of the incident is the same on both sides:
the mail service accepted the first reminder for order 5540 (message m-88339)
but replied too slowly, the script gave up at 30 seconds and sent the reminder
again (m-88342), and customer #131 received both emails.

## What this fixture is for

It is the vague-rule case. The rule is one line, it has no trigger point, and
nothing in it says which explanations count as "concepts" or how much drawing
is enough. Rules like this normally go unchecked — you write one, hope it
helps, and never find out whether it fired.

This fixture is deliberately **not** a case where anything breaks. Both
answers are correct and useful. The whole point is that you can see what your
rule did, in one run, without needing a disaster to make it visible.

## Measured result

Two full runs, three trials per side each, 2026-09-01, claude/sonnet:

```
                        ASCII drawing in the answer
  BEFORE                        1 of 6
  AFTER                         6 of 6
```

The before side is not a flat zero — one trial in six drew a timeline
unprompted. Say "almost never" rather than "never".

Both sides read the same three records and reach the same root cause. The
after trials turn the sequence into a drawn timeline; the before trials write
it as numbered prose. The after trials also tend to open with a one-line
plain summary before the picture — something the rule never asked for.

Do not quote a stronger claim than that. In particular this fixture does not
show the rule catching anything, and it is not evidence that the agent
understands the incident better.

## What to look for after the trials

One observable: does the final answer contain an ASCII drawing — a fenced
block with an aligned timeline, arrows, or boxes?

Three outcomes, all valid; report the one that happened.

1. **Drawings appear only on the after side.** The rule fired, and you can see
   exactly what it produced. This is the measured behaviour.
2. **Both sides draw.** The rule changed nothing visible on this question —
   worth knowing before trusting it.
3. **Drawings appear on some after trials only.** The rule fires
   inconsistently. `--fast` cannot show this; a vague rule is exactly the kind
   that fires sometimes, so use the full three-per-side run when consistency
   is the question.

A `--fast` pair is enough to show the shape in a live demo, but it settles
nothing on its own. This fixture was first read at one trial per side and the
reading was wrong in its emphasis; the three-per-side run is what produced the
numbers above.

The driven session must not open the shop records while it adds the rule. It
may read `pending-request.md`. If it explains the incident itself before the
trials, the payoff answer is already on screen — restart from a fresh sandbox.
