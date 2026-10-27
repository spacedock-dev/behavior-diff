---
title: Prototype the verification handoff journey
status: backlog
source: Captain request to create a dev-workflow prototype task after journey feedback
started:
completed:
verdict:
score:
worktree:
issue:
linear:
pr:
mod-block:
id: yxy4v1m92t2daz68kmmykqqh
---

Build an operable conversational prototype of handing post-change verification
to Behavior Diff. The user should understand the change, relevant evidence and
limits, then decide what to do, rather than direct every verification step.
This is a prototype implementation task, not another planning document or a
claim that autonomous verification is already delivered.

## Problem

Existing verification capabilities do not by themselves establish a low-effort
user experience. The user can still need to restate context, specify individual
tests, prompt continuation, or reconstruct findings from raw records. The
requested next deliverable is a prototype that makes these intervention points
observable. Journey direction has received positive feedback; implementation
and design choices still follow the workflow gates.

## Proposed approach

Start with one locally supplied workflow-change case and a conversational
surface; prefer existing host interaction and report components over a new UI.
Provide an actual walkthrough with three connected steps:

1. Handoff: accept the change and available discussion/documents. Propose the
   modification intent and verification goals for confirmation or correction.
   Offer bounded choices only where uncertain; permit none-of-the-above and
   free correction. Do not require the user to design tests from scratch.
2. Verification handoff: show the relevant plan and limits; ask only for missing
   information or decisions that require the user. Carry corrected goals into
   the subsequent result. Demonstrate this transition rather than only narrate it.
3. Decision: present findings, reasons and unverified requirements first, with
   accessible supporting evidence. Let the user decide to accept, revise or
   request further verification. Never perform merge or adoption automatically.

Reuse existing case evidence where appropriate, explicitly labeled as reused.
An evidence-backed replay is acceptable for this prototype; do not pretend it
is fresh execution, autonomous evidence generation or measured live latency.
The simplest alternative is a static storyboard, but it cannot exercise user
corrections or reveal actual takeover points, so it is insufficient alone.
Ideation must choose the smallest executable surface and present it for approval.

## Risk evidence

This request follows a reviewed journey and existing conditional capability
experiments; the question now concerns handoff effort, not proving all
verification capabilities from scratch. Use `intent mismatch` for behavior
that does not match a modification's intent, not `side effect` as a synonym.
Regression testing and simulation are candidate means, not the product goal.
Simulation does not establish real-service compatibility or complete coverage.
Known-answer replay cannot prove first-time intent inference accuracy.

Private source pointers, for local reading only:
- memo/private/2026-10-27-cl-discussion-pack.md
- memo/product/2026-10-26-behavior-review-product-testing-plan.md

These notes may lag later Captain direction: this task's handoff outcome is the
current requested scope. Obtain permitted evidence locally; do not copy private
runs, reports, transcripts, customer identifiers or personal paths into tracked
code or state. Use synthetic fixtures for committed demonstrations. Missing real
case evidence is a reported prerequisite, not permission to invent findings.

## Expected surface and tolerance

Ideation must identify the minimal runnable surface, changed files and size
estimate with tolerance before implementation. A standalone formal UI, new
orchestration platform and automatic remediation system are not assumed.
Report hierarchy changes must follow repository preview requirements.

## Acceptance criteria

Draft outcomes to refine at the ideation gate:

**AC-1 — A user can operate the full handoff-to-decision journey.**
Verified by: interactive walkthrough on the actual prototype, including a
correction of the proposed intent or verification goal and continuation to a
result that respects that correction. A static script or a correction ignored
by later steps fails this check.

**AC-2 — Findings remain evidence-bound and uncertainty is actionable.**
Verified by: exercise a supported result and a result with an unverified
requirement using permitted evidence. The user can locate the relevant support
and distinguish reused evidence from fresh execution. Treating missing evidence
as a pass, fabricating a run, or claiming whole-flow coverage from a slice fails.
No new model-backed run is implied by these prototype exercises.

**AC-3 — The prototype exposes whether verification work was handed off.**
Verified by: an interactive user walkthrough recorded outside tracked state,
comparing the user's usual need to arrange, chase and interpret verification
with actual intervention points in the prototype. Record each takeover, its
reason, necessary user decision versus avoidable agent work, and the user's
ability to decide from the result. Select the next experiment from the most
costly remaining takeover point. A negative or inconclusive value result is
valid; a positive claim based only on praise or the prototype's existence fails.
This evaluation is a Captain-dependent gate; do not invent user responses.

## Test plan

Exercise the actual surface through confirmation, correction, evidence viewing
and an evidence-gap path. Use deterministic synthetic fixtures for offline
checks and local permitted evidence for the user walkthrough. Tests must check
observable behavior, not instruction wording. Keep raw interaction records and
real evidence local; report only privacy-safe outcome summaries in state.
Separate prototype usability evidence from model capability, timing and complete
workflow validation. Fresh model trials, real external operations and private
data disclosure need their own applicable approval. No model calls in CI.

## Decisions and dependencies

- Captain requested task creation now and later execution through Spacedock.
  This does not authorize dispatch, an unknown design, paid runs, push, PR,
  merge or release. Start in backlog.
- Related task: `verify-overall-skill-behavior-value`
  (`pyjt2hqwf2ncmfgdr9xhxk29`). Its scenario-comparison scope is distinct.
  Reuse suitable existing artifacts, avoid overlapping edits, and coordinate
  shared surfaces before implementation; do not block automatically on its
  completion or supersede it without a Captain decision.
- Priority recommendation: High, because the next product discussion needs an
  operable prototype. No arbitrary numeric score or delivery date is assigned.
- Private evidence availability and user walkthrough are explicit dependencies.
  Select the local case and verify availability during ideation.

### Feedback Cycles

No review rounds yet.

## Out of scope

Formal product rename; broad capability research; comprehensive regression-suite
generation; live E2E runs; automatic fixes or merge; new permanent CI gates;
polished multi-case UI; proving simulation is faster or replaces all real E2E;
committing private evidence; changing the related task without approval.
