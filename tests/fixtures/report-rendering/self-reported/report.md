# Live contract

before: parent snapshot <baseline> · after: target snapshot <candidate> · model: contract · trials: 1 before, 1 after · evidence: self-reported actions

Synthetic contract fixture.

## Observed in this run

```
Which evidence was used?

BEFORE  1/1  read only
AFTER   1/1  read and test

One run: 1 trials before, 1 after. A model read the trials and named this choice. Not a verdict.
```

## Scenario

Compare the two instruction snapshots.

<details><summary>Diff of AGENTS.md</summary>

```diff
--- AGENTS.md (before)
+++ AGENTS.md (after)
@@ -1 +1 @@
-Original project instructions.
+Updated project instructions.
```

</details>

## Decision diff: what the agent chose, before and after your edit

A model read every trial and named the points where the agent had a real choice. This is the answer to what your edit changed. CAUTION — one trial per side: any divergence here can be run-to-run variation rather than a rule effect; confirm with repeated trials (behavior-diff 3+3) before acting on it.

Tags:

- **first difference** — the first decision where before and after split
- **follows from it** — this split happens because of the first difference
- **same before and after** — before and after chose the same thing
- **from a command** — this row comes from a command the agent ran
- **from the reply** — this row comes from what the agent wrote

Diverging from here:

- 1. **Which evidence was used?** *(first difference)* *(from a command)*
  - BEFORE: read only
  - AFTER: read and test

Before and after first differ at decision #1.

Synthetic fixture.

## BEFORE — parent snapshot <baseline>

1 valid trial(s) · no automatic grading (blocked: 0)

### before-1 — REVIEW

<details><summary>self-reported actions (1)</summary>

```
Read: AGENTS.md
```
</details>

<details><summary>final answer to the user</summary>

Before answer

</details>

## AFTER — target snapshot <candidate>

1 valid trial(s) · no automatic grading (blocked: 0)

### after-1 — REVIEW

<details><summary>self-reported actions (2)</summary>

```
Read: AGENTS.md

Test: bash behavior-diff/tests/live-report-contract.sh
```
</details>

<details><summary>final answer to the user</summary>

After answer

</details>

## Result

**No automatic verdict — compare the reported actions, decision diff, and final answers**

This is simulation evidence. Real-use evidence is still pending.
It does not repair the original incident; it tests the change for future tasks.
