# pricer — the demo fixture

A fixture for showing someone what a behavior diff is. The sibling
`../capsule/` fixture tests the harder harness case. This fixture uses a
customer bug that an audience can understand in one sentence.

## The situation, in one sentence

A teammate says a discount bug is fixed, and the customer's exact example
now passes. Should the agent close the ticket?

## The decision the audience watches

Behavior Diff gives two agents the same project and the same task. The only
difference is one proposed rule in `AGENTS.md`.

Without the rule, the agent has the passing replay it was asked for:

    $ python3 price.py 100 10
    90.00

It can decide `FIXED`, close the ticket, and tell the customer the problem is
resolved.

With the rule, the agent must take a different route before it decides:

1. Read `discount.py`.
2. Notice that the calculation uses floor division (`//`).
3. Choose a price with cents to challenge that calculation.
4. Run the targeted check.

That route exposes the hidden bug:

    $ python3 price.py 99.99 10
    90.99          # should be 89.99 — the customer is overcharged a dollar

The after agent decides `NOT FIXED`, keeps the ticket open, and avoids making
a false promise to the customer.

That is the whole demo story:

    same task + one rule -> different route -> different evidence -> different decision

The rule does not name the decimal-price answer. It changes how the agent
chooses its next action: inspect the implementation, form a failure
hypothesis, and test that hypothesis.

This is the expected case shape, not a guaranteed model result. `--fast` is
one trial per side. If the before agent independently finds the hidden bug,
say so; the case did not diverge on that run.

## Instruction-file layout

`AGENTS.md` is the canonical project instruction file. `CLAUDE.md` contains
only `@AGENTS.md`, so Codex and Claude Code receive the same project rules.
The proposed rule is added to `AGENTS.md`, not duplicated in `CLAUDE.md`.

## What this fixture had to learn

The first version used the rule "run the program before you say it works".
Both variants ran the tiny program, so it produced no useful divergence.

The second version said to try one more input. That could change the result,
but it changed only one command in the flow and almost supplied the hidden
case in the rule itself.

The current version starts at the decision point, after the obvious replay
has passed. The proposed rule changes the route used to reach the decision,
not only the amount of testing.

## Running it

    NUDGE_E2E_FIXTURE=demo ../../tests/nudge-e2e.sh setup

Then follow the printed steps, or drive the diff directly:

    cd /tmp/nudge-e2e
    cat <path to>/demo/rule.md >> AGENTS.md      # the uncommitted rule edit
    behavior-diff.sh --file AGENTS.md --task "$(cat <path to>/demo/task.md)"

`--fast` runs one trial per side, which is enough to show the shape but not
enough to call anything settled; the default 3+3 is what a real check uses.
