---
title: Verify the value of overall-skill Before/After behavior comparison
status: ideation
source: Captain-requested follow-up from case-01-auto-download-audio.md
started: 2026-10-23T14:17:49Z
completed:
verdict:
score:
worktree:
issue:
linear:
pr:
mod-block:
id: pyjt2hqwf2ncmfgdr9xhxk29
gates:
    version: 1
    records:
        - id: gate:pyjt2hqwf2ncmfgdr9xhxk29:backlog
          stage: backlog
          attempts:
            - id: gate-attempt:pyjt2hqwf2ncmfgdr9xhxk29-backlog-1
              briefing:
                id: briefing:pyjt2hqwf2ncmfgdr9xhxk29:backlog:attempt-1:revision-1
                digest: sha256:42ac9a3a5689289fb1bca66945bf1c6802527253b67cd5406a699a794ec45daf
                room-ref: ./verify-overall-skill-behavior-value/review/backlog/briefing-1
              resolution:
                type: Resolution
                id: resolution:spacedock:pyjt2hqwf2ncmfgdr9xhxk29:backlog:1
                briefing: briefing:pyjt2hqwf2ncmfgdr9xhxk29:backlog:attempt-1:revision-1
                by: person:captain
                at: "2026-10-23T14:15:40.74238Z"
                decision: approve
                reason: 'Captain approved starting ideation. Approval recorded without consume: mandatory docs/feature-dev/runtime/omp.md preflight identifies no supported, disposable-smoke-verified adapter mapping for this omp session; preserve pending approval until dispatch is available in a supported runtime.'
              application:
                target-stage: ideation
                state: consumed
---

Test the hypothesis that users want to understand a skill's overall behavior
and compare it Before/After, beyond a scenario derived only from the change.
This is a candidate product direction to investigate, not an approved feature.

## Problem

A change-focused scenario may not answer how the skill pursues its broader goal,
which required behaviors remain, and what else changes. The source case proposes
a separate scenario grounded in the project's overall goal. Whether that adds
useful understanding or decision support remains unverified.

## Proposed approach

During ideation, define the user's question and a bounded representative
whole-skill task. Compare what a change-focused scenario explains with what an
overall-goal scenario adds, holding the relevant versions, context, and model
conditions explicit. Seek evidence that can reject the hypothesis as well as
support it. Do not assume a complete end-to-end simulator or a new report tab.

## Risk evidence

Source: `../spacedock-strategy/projects/behavior-diff/case-01-auto-download-audio.md`,
“The test question”, “Product value check”, final feedback, and stated limits.
Read the local source for context; keep private runs and transcripts outside
tracked state. A simulated path does not establish real external execution or
coverage of the entire skill. Missing tools or an invalid setup are inconclusive,
not evidence that the skill or product hypothesis failed.

## Expected surface and tolerance

No implementation estimate or product contract is approved. First bound a
verification proposal; any resulting feature needs its own accepted design.

## Acceptance criteria

Draft hypothesis-verification outcomes to refine during ideation:

**AC-1 — Evidence distinguishes the value of overall-goal and change-focused scenarios.**
Verified by: an approved bounded comparison with explicit user question, baseline,
coverage, and predeclared support/refutation criteria. Inspect resulting artifacts
and the reader's interpretation; showing only more output or treating the same
narrow scenario as whole-skill coverage fails.

**AC-2 — The outcome states whether the added view improves user understanding or a change decision.**
Verified by: interactive reader evaluation against the original question with
links to permitted evidence. Supported, unsupported, and inconclusive outcomes
are all valid; assuming demand from this single request or fabricating evidence
is not. A positive outcome is not required for successful verification.

## Test plan

Agree on the question, representative task boundary, comparison method, and
success/failure criteria before running anything. Reuse suitable saved evidence
first. Obtain required consent for live trials; record environment limitations.
Define tests for any later code change separately from hypothesis evaluation.

## Decisions and dependencies

Captain explicitly requested this hypothesis as a backlog task in the dev
workflow. Its initial scope is verification of a candidate product capability,
not permission to build it. We will discuss it later; no worker dispatch or model
runs now. Link any accepted verification plan and evidence in their existing
homes rather than duplicating a research log in state.
Related task: `refine-summary-page-signal`; summary clarity and added scenario
value are separate questions, with no assumed execution dependency.

### Feedback Cycles

None; hypothesis design and review have not started.

## Out of scope

Exhaustive skill coverage, a full simulator, repeated generator tuning, a new
product feature before validation, proven time-saving claims, or calling the
source case a confirmed demonstration of additional product value.
