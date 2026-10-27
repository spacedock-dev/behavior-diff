---
title: Reduce full Behavior Diff skill execution time on Claude Code and Codex
status: ideation
source: Captain request to improve the complete native-host skill rather than OMP advisor configuration
started: 2026-10-27T13:28:15Z
completed:
verdict:
score: 0.95
worktree:
issue:
linear:
pr:
mod-block:
id: n2m85xea3h2q75xk6gzjebwm
gates:
    version: 1
    records:
        - id: gate:n2m85xea3h2q75xk6gzjebwm:backlog
          stage: backlog
          attempts:
            - id: gate-attempt:n2m85xea3h2q75xk6gzjebwm-backlog-1
              briefing:
                id: briefing:n2m85xea3h2q75xk6gzjebwm:backlog:attempt-1:revision-1
                digest: sha256:75e0a81279bf5edea45629dd0d61689ef0564c3cd24c8f31994d034d7fcf7be2
                room-ref: ./review/backlog/briefing-1
              resolution:
                type: Resolution
                id: resolution:spacedock:n2m85xea3h2q75xk6gzjebwm:backlog:1
                briefing: briefing:n2m85xea3h2q75xk6gzjebwm:backlog:attempt-1:revision-1
                by: person:captain
                at: "2026-10-27T13:27:52.697425Z"
                decision: approve
                reason: The Captain explicitly requests refactoring the complete Behavior Diff skill to reduce execution time under Claude Code or Codex; this accepts starting design, not an unknown design or merge.
              application:
                target-stage: ideation
                state: consumed
---

Reduce elapsed time from a user's comparison request through the final evidence-audited response when the canonical Behavior Diff skill runs in Claude Code or Codex.

## Problem

The previous OMP-only advisor change does not satisfy the requested end-to-end skill improvement. A recorded outer orchestration spent approximately 85.5% of its selected interval outside the runner, primarily in model/tool round trips for preparation, preflight and raw-evidence audit. That is a targeting clue, not a measured Claude Code or Codex result.

## Proposed approach

Measure the existing canonical skill under native Codex, then remove avoidable shared preparation, freeze/handoff and audit round trips using the smallest deterministic helpers and progressive instructions justified by that evidence. Keep scenario design and semantic judgment with the agent. Prefer extending existing mechanics to a second orchestrator; do not add a permanent benchmark framework or another standing gate.

## Risk evidence

Native Codex baselines must precede product changes. Capture phases, agent/tool turns, actual attempts and final raw-evidence audit, not only report rendering or extraction duration. No speed claim from OMP-only measurements.

## Expected surface and tolerance

Ideation must bound the canonical skill, shared references/helpers, relevant deterministic boundary tests and architecture documentation. PR #55 remains separate and is not the base or deliverable.

## Acceptance criteria

- **AC-1** Native Codex completes the same three pinned Recce-Team case requests through final raw-evidence audit on both versions, with reduced aggregate end-to-end wall time; report every paired case and phase without hiding slower, incomplete or inconclusive results. Verified by: private native Codex session traces and timing ledger. A candidate no faster overall or a runner-only measurement fails this value criterion. One paired observation per case limits generalization.
- **AC-2** The refactor preserves frozen purpose/scenario/data and reference closure, three trials per side, identical pinned models/settings, privacy exclusions and all-case raw evidence auditing. Verified by: actual frozen inputs, trial projects, statuses, source returns/artifacts and complete audit results. Missing a case or silently reducing delivery or audit invalidates speed acceptance.
- **AC-3** Deterministic mechanics reject stale, invalid or privacy-unsafe preparation and preserve evidence needed to distinguish reached/missed/unknown and supported/contradicted/insufficient. Verified by: exercised helper CLI smoke and relevant isolated boundary tests, including negative paths; prose-presence or forwarding-only tests are insufficient.
- **AC-4** Canonical Claude Code and Codex instructions use the shared improved path; callers, required references and concise architecture documentation agree. Verified by: complete consumer review and actual Codex changed-path execution, with any unexercised Claude-specific runtime limit explicit.

## Test plan

Use the three default real cases in e2e/README.md under the historical isolation rules and matching companion-file delivery. Six outer Codex skill executions, 36 trials and six extractions total, no automatic retries, pinned sol trial/outer and luna extraction IDs. Same neutral requests and historical source inputs per paired version; no later corrections or evaluator answer keys in agent context. Distinguish generated-case variation from mechanical savings. Keep all sessions and benchmark scaffolds private/outside Git; deterministic CI only. Implementation owns checks and fixes, independent reviewer remains read-only and does not duplicate them.

## Decisions and dependencies

Captain explicitly requested this complete native-host refactor and selected starting implementation in the original request; this supplies backlog selection, not an unknown design or merge approval. Fresh US$20 working benchmark budget approved, with token-derived monitoring and in-flight-request cap limitation disclosed. Captain separately approved only the pinned private Recce-Team skill files and necessary historical references to OpenAI through Codex plus fresh sanitized fixtures; no private conversations, customer data, credentials, later corrections or historical reports. No OMP or Jev benchmark calls. No authority to push, create/update PR, merge or release this new change.

### Feedback Cycles

## Out of scope

OMP advisor configuration; changing models, trial counts or evidence standards as a speedup; report presentation redesign; source-purpose hindsight; new CI lanes, standing gates, permanent benchmark infrastructure; unrelated workflow repair; automatically modifying PR #55.
