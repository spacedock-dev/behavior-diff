# Live contract

Synthetic contract fixture.

**Observed in this run — Evidence choice: BEFORE read only · AFTER read and test. Single-run observation, not a verdict.**

Model: contract · 1 trial(s) per variant.

## Scenario

Compare the two instruction snapshots.

## Diff of AGENTS.md — the only difference between the variants

```diff
--- AGENTS.md (before)
+++ AGENTS.md (after)
@@ -1 +1 @@
-Original project instructions.
+Updated project instructions.
```

## Decision diff — top divergences

A decision is a point where the agent had a real choice. These are recovered from what the trials did and said, not from the instruction diff, and some of them leave no command behind. Order is real: decisions visible in commands come in command order, and decisions visible only in the final answer come last. The fork and main divergences are stable across extractions; minor rows can vary run to run. CAUTION — one trial per side: any divergence here can be run-to-run variation rather than a rule effect; confirm with repeated trials (behavior-diff 3+3) before acting on it.

Diverging from here:

- 1. **Evidence choice** — Which evidence was used? ⟵ root behavior change
  - BEFORE: read only
  - AFTER: read and test

One target decision changed (#1); 0 later differences diverge downstream of it (the extractor's causal reading, not a measured chain).

Synthetic fixture.

<details><summary>Flow diff — command-derived (deterministic, no model involved)</summary>

## Flow diff — where the variants diverge

Steps are described from the agents' actual commands; a path is a sequence at least one trial literally took. Full commands are in the trial sections below.

Shared flow (every trial, both variants):


Divergence:

- BEFORE, all 1 trials → (same steps as the shared flow)
- AFTER, all 1 trials → Run tests

</details>

## BEFORE — current file

1 valid trial(s) · no automatic grading (blocked: 0)

### before-1 — REVIEW

<details><summary>commands the agent ran (1)</summary>

```
Read: AGENTS.md
```
</details>

<details><summary>final answer to the user</summary>

Before answer

</details>

## AFTER — your change applied

1 valid trial(s) · no automatic grading (blocked: 0)

### after-1 — REVIEW

<details><summary>commands the agent ran (2)</summary>

```
Read: AGENTS.md

Test: bash behavior-diff/tests/live-report-contract.sh
```
</details>

<details><summary>final answer to the user</summary>

After answer

</details>

## Result

**No automatic verdict — compare the flows and final answers**

This is simulation evidence. Real-use evidence is still pending.
It does not repair the original incident; it tests the change for future tasks.
