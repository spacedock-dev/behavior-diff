---
title: Reduce Behavior Diff assessment latency without weakening evidence
status: backlog
source: Captain request on 2026-10-27 to diagnose and refactor recent slowdown; Captain selected the Spacedock workflow.
started:
completed:
verdict:
score: 0.9
worktree:
issue:
linear:
pr:
mod-block:
id: vnaxvsdna9hvd5fgebv5fp5y
gates:
    version: 1
    records:
        - id: gate:vnaxvsdna9hvd5fgebv5fp5y:backlog
          stage: backlog
          attempts:
            - id: gate-attempt:vnaxvsdna9hvd5fgebv5fp5y-backlog-1
              briefing:
                id: briefing:vnaxvsdna9hvd5fgebv5fp5y:backlog:attempt-1:revision-1
                digest: sha256:15dd9ace496c0ed91b9667f4846449cb7f178a709ce31f0050a98d6932fc5fac
                room-ref: ./reduce-assessment-latency/review/backlog/briefing-1
---

Make Behavior Diff comparisons faster by diagnosing and refactoring the measured bottleneck while preserving comparable trials and report evidence.

## Problem

The Captain reports recent slow comparisons. Offline inspection of five recent saved comparisons found assessment taking 72–99 seconds on the serial critical path. The latest inspected comparison took 149 seconds overall, with parallel trials ending after 75 seconds and assessment taking 73 seconds. Scenarios and hosts differ, so these numbers establish stage costs, not a same-input version regression. Current prompt construction on the latest run took 0.0665 seconds and produced 186,681 characters. Its returned excerpts contain 21,072 exact duplicate characters; pretty JSON for evidence, purpose and scenario adds 10,461 characters. No model call was made during diagnosis. Private artifacts and their contents must remain outside tracked code and state.

## Proposed approach

Design worker should evaluate lossless assessment-input compaction and exact-text interning while preserving every trial-specific evidence record, identity, source, range, status, reason and availability limit. Measure input reduction on fixed recorded runs, validate round-trip evidence equivalence with synthetic boundary cases, and compare with the simplest alternative of whitespace-only JSON compaction. Do not assume reduced input proves lower model latency. Investigate host startup context only if it can be shown relevant without live model calls; do not broaden into host configuration changes by default.

## Risk evidence

Runner already launches trials concurrently. Local prompt build is far below the observed assessment wall time. The fixed prompt plus schema is roughly 39,000 characters. Saved runs are private and read-only. Runtime compatibility must be exercised in a disposable repository before real workflow dispatch per runtime/omp.md.

## Expected surface and tolerance

Worker to establish at ideation. Candidate expected under plugin/skills/behavior-diff/scripts/, relevant tests/, and docs/architecture.md. No report hierarchy changes.

## Acceptance criteria

Design worker must propose exact criteria, including a value measurement against a fixed-input baseline, evidence identity/content preservation, unchanged privacy/truncation rules and deterministic offline verification. No unsupported wall-clock speedup claim.

## Test plan

Offline only. Exercise real prompt generation and assessment ingestion/rendering seams using saved private runs read-only and synthetic temporary fixtures. Relevant deterministic contracts and formatters after implementation. No paid Behavior Diff runs without fresh explicit approval.

## Decisions and dependencies

Captain chose the existing Spacedock workflow rather than direct-FO editing. The original refactor request supplies initial selection approval, not approval of an unknown design, push, PR, merge, release or paid runs. Do not touch existing tasks or their worktrees. No Linear publication approved.

### Feedback Cycles

## Out of scope

Fewer trials, weaker criteria/evidence, model substitutions, changed report formats or hierarchy, caching trial outcomes, new permanent profiling infrastructure, CI/provider changes, publication of private run data, paid model-backed verification, push, PR, merge and release.
