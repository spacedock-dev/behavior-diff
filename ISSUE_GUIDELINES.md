# Issue guidelines

Behavior Diff work is tracked in the Engram Linear project:
[Engram (reflection) — Self-Improvement (pillar 3)](https://linear.app/recce/project/engram-reflection-self-improvement-pillar-3-551d43270709).
Use the `behavior-diff` part label.

This guide adapts the issue rules from the private Engram repository. This file
is the canonical source for Behavior Diff issue classification. If a Linear
label description disagrees with this file, update the label description.

## When work needs an issue

Create an issue when work changes **what ships** or **what we believe**.

This includes:

- a product or test-harness change;
- a plan that the team intends to execute;
- a decision that closes an open question;
- a test run whose result will be cited later.

Do not create an issue for a routine edit with no decision, such as a typo fix,
a repeated green test run, or a document sync.

## Work type

Each issue states what changes when it closes:

- **Feature** — Behavior Diff gains an ability that it did not have.
- **Improvement** — an existing ability works better.
- **Bug** — supported input produces behavior that violates its contract.
- **Verification** — the product does not change; the issue produces evidence.

If an issue runs a test and fixes a problem, use `Bug` or `Improvement`.
`Verification` applies only when finding no problem is a complete result.

A narrow or incorrect specification is an `Improvement`, not a `Bug`. Use
`Bug` when working input produces the wrong result.

## Priority

Priority answers what to work on next:

- **Urgent** — shipped behavior harms users now. Resolve it within days.
- **High** — a user, decision, or other issue waits on it. Resolve it within
  two weeks.
- **Medium** — the work is real, but nothing waits on it, or it is blocked.
- **Low** — the work can wait one month without harm.

Do not keep blocked work at High. State the blocker in the issue description.

## Milestones

Milestones group delivery work with a date. Labels describe the kind of work.

- Name a milestone for its outcome, not for a week number.
- When reality changes, rename the milestone and record what shipped, stopped,
  or changed.
- Do not leave a milestone partly complete because an obsolete criterion never
  closed.

## Rule changes

When this guide changes, add a dated log entry that states the rule and its
reason. This prevents the same process decision from reopening without new
evidence.

## Log

- 2026-09-02 — Created the standalone Behavior Diff guide from the applicable
  Engram issue rules. Behavior Diff remains under the Engram Linear project and
  uses the `behavior-diff` part label.
