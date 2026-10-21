---
title: Refine the summary page to make the main result clear
status: backlog
source: Captain-requested follow-up from case-01-auto-download-audio.md
started:
completed:
verdict:
score:
worktree:
issue:
linear:
pr:
mod-block:
id: dmz5fz1edtpmyc9vx28ez15w
---

Help readers understand the main Before/After result at a glance without
repeated uncertainty and secondary checks overwhelming the summary.

## Problem

The source case identifies a summary-page clarity problem: the main outcome
requires close reading, while repeated caveats distract from it. Improve the
information hierarchy without suppressing a material risk or implying that
untested behavior is safe.

## Proposed approach

Direction for later ideation, not an approved layout: lead with the tested
question and observed Before/After result; consolidate repeated qualifications;
keep important uncertainty visible once and retain access to supporting detail.
Use the existing preview workflow and renderer with evidence held constant.

## Risk evidence

Source: `../spacedock-strategy/projects/behavior-diff/case-01-auto-download-audio.md`,
“What the final demo report showed” and “What we keep and what we stop”.
Read the original in the local strategy checkout when designing. Do not copy
private reports, trial excerpts, or recordings into this state branch. The case
motivates this task; it does not prove additional product value or general safety.

## Expected surface and tolerance

Not estimated at backlog intake. Bound the summary/rendering surface and any
necessary extraction-contract changes during ideation before implementation.

## Acceptance criteria

Draft outcomes to refine with the Captain during ideation:

**AC-1 — The main tested question and Before/After result are understandable from the summary.**
Verified by: interactive comparison of current and proposed rendered summaries
using unchanged evidence; ask the reader to identify the outcome and its scope.
A reader still needing the detailed report to find the primary result fails.

**AC-2 — Repeated caveats no longer crowd out the outcome, without losing material uncertainty.**
Verified by: inspect rendered previews against the underlying evidence; show a
consolidated qualification and a reachable detail path. A missing material limit,
repeated equivalent warnings, or unsupported success claim fails.

## Test plan

Preview before implementation using the repository-required cases. Separate
presentation improvement from changes to evidence generation. Select relevant
renderer/contract checks once the design is approved; no live rerun authorized
by this backlog request.

## Decisions and dependencies

Captain requested backlog capture only; no design, implementation, or delivery
approval. Related task: `verify-overall-skill-behavior-value`; neither task is
blocked on the other. Do not require a whole-skill feature to reduce report noise.

### Feedback Cycles

None; design and review have not started.

## Out of scope

A new simulator, repeated generator tuning, hiding material failures, claims of
full-workflow time savings, and treating this case as proven product success.
