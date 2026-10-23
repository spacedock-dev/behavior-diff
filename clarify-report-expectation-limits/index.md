---
title: Make report evidence-limit wording agree with recorded expectations
status: backlog
source: Captain requested a separate task for the contradictory evidence-limit wording observed during PR 53 verification
started:
completed:
verdict:
score:
worktree:
issue:
linear:
pr:
mod-block:
id: 7c9fysvm07cp0yv31waysvjj
---

Help readers understand what a Behavior Diff report actually assessed, without contradictory statements about whether expected behavior was supplied.

## Problem

A synthetic pricer example displayed five recorded checks under "What these tests establish" while "Evidence limits" stated: "No explicit expected behavior was supplied. The report makes no correctness claim."

The separate expected grading field was empty, but scenario checks existed. The wording conflates absence of that grading field with absence of all expected behavior.

## Proposed approach

During ideation, trace the grading-expectation and scenario-check contracts and choose the smallest accurate wording/condition change. Distinguish a missing separate grading expectation from missing scenario checks. Preserve uncertainty when supplied checks are unresolved or their evidence is invalid; supplied expectations do not establish correctness.

The simplest alternative is to omit the misleading sentence in review mode if the report already explains its assessment limits accurately. Select based on actual report states, not a new report section.

## Risk evidence

The contradictory wording was observed in the rendered HTML during an approved one-before/one-after Claude pricer run. The condition in plugin/skills/behavior-diff/scripts/reporting/content.py:1264–1267 emits the sentence whenever expected is empty. Main and the PR 53 candidate had the same implementation; this is pre-existing, not a Jev regression. No private run payload or transcript is included here.

## Expected surface and tolerance

Likely home: existing report content generation and its behavioral coverage. Exact files, estimate and tolerance belong to ideation. Do not redesign the report or alter comparison semantics.

## Acceptance criteria

**AC-1 — Readers receive a consistent account of supplied expectations.**
Verified by: offline rendering of synthetic review input with recorded scenario checks and no separate grading expectation. The generated report acknowledges the checks without also claiming no expected behavior was supplied; the original contradictory example is the baseline.

**AC-2 — Absent expectations and incomplete evidence remain honestly distinguished.**
Verified by: offline cases with neither source of expectations, a separate grading expectation, and supplied but unresolved/rejected checks. Reports accurately identify what was supplied and do not claim correctness merely because checks exist. Any false claim of assessed or established correctness fails.

**AC-3 — The fix preserves report evidence and behavior.**
Verified by: compare rendered output and report data for the same frozen synthetic inputs before and after the change. Trial memberships, counts, check outcomes, evidence citations and uncertainty remain unchanged; inspect the actual HTML evidence-limit surface and supported text outputs.

## Test plan

Reuse existing reporting tests and synthetic fixtures. Render and inspect the actual report surface without model calls. Follow existing preview requirements where applicable; do not silently substitute synthetic inputs for required saved-case evidence. Run relevant deterministic checks after implementation. No live-run approval is granted by this filing.

## Decisions and dependencies

Captain approved filing this task only; dispatch will be requested separately. PR 53 is merged, but no Jev dependency is required for reproducing this wording defect. Keep scope on explanation consistency, not accepting the earlier Jev value claim.

### Feedback Cycles

No correction rounds recorded.

## Out of scope

Jev behavior, additional live trials, grading/scenario schema redesign, source-capture changes, nudge behavior, unrelated ShellCheck fixes, report layout redesign, PR creation or release.
