---
title: Use Jev for semantic judgments when configured
status: ideation
source: Captain request to proactively use Jev when the user has configured a token
started:
completed:
verdict:
score:
worktree:
issue:
linear:
pr:
mod-block:
id: sd4j775gcwrmhxnd0rm84a36
gates:
    version: 1
    records:
        - id: gate:sd4j775gcwrmhxnd0rm84a36:backlog
          stage: backlog
          attempts:
            - id: gate-attempt:sd4j775gcwrmhxnd0rm84a36-backlog-1
              briefing:
                id: briefing:sd4j775gcwrmhxnd0rm84a36:backlog:attempt-1:revision-1
                digest: sha256:a0cab9b4000ceb7af934c4bca09c0bd39b56cf3e14d3ef83399ac8c81babfa04
                room-ref: ./use-jev-for-semantic-judgments/review/backlog/briefing-1
              resolution:
                type: Resolution
                id: resolution:spacedock:sd4j775gcwrmhxnd0rm84a36:backlog:1
                briefing: briefing:sd4j775gcwrmhxnd0rm84a36:backlog:attempt-1:revision-1
                by: person:captain
                at: "2026-10-23T08:37:01.854168Z"
                decision: approve
                reason: Captain approved starting ideation in chat; implementation and paid model runs remain unapproved.
              application:
                target-stage: ideation
                state: consumed
---

Make Behavior Diff proactively use Jev for useful semantic judgments when the
user has configured a Jev token, rather than limiting Jev use to search through
find. Preserve evidence quality, deterministic verification, and user authority.

## Problem

The Captain wants Behavior Diff to use available Jev capabilities more actively
for semantic work. Current integration points and token discovery have not been
audited; this request does not assert that a particular integration is missing.

## Proposed approach

During ideation, identify supported token configuration and host capabilities
without exposing credentials. Use Eval's judge and judge_batch where available;
verify the supported integration for each shipped host rather than assuming
omp's Eval surface exists in Claude Code or Codex.

Apply judgments where useful to rank candidate evidence, classify findings,
assess whether observations support individual acceptance criteria, and evaluate
independent hypotheses against available observations. Batch independent
questions about one state in one judge call. Use judge_batch for multiple states
or candidates evaluated against the same questions.

Keep deterministic checks in code. Treat judge results as evidence, not proof;
verify important conclusions through tests, runtime observations, or primary
sources. Do not use Jev to grant permissions or replace user approvals.

In the final response, briefly state what Jev evaluated and how the results
affected decisions. If there was no useful opportunity, say so instead of making
unnecessary calls. Missing configuration must not make Jev a required dependency
for the existing Behavior Diff workflow.

## Risk evidence

No implementation investigation or live Jev call has been performed for this
intake. A configured token does not establish a working integration or authorize
additional actions. Ideation must resolve credential discovery, host support,
and handling of unavailable or failed judgments without leaking secrets or
claiming that unperformed evaluations ran.

## Expected surface and tolerance

Product home: the canonical Behavior Diff skill and its bundled integration
under plugin/. This is a product task, not a change to FO approval authority or
a Spacedock runtime adapter. Exact files, change size, and tolerance are to be
proposed during ideation. Preserve Claude Code and Codex behavioral equivalence.

## Acceptance criteria

Draft criteria for design review:

**AC-1 — Configured users receive useful semantic assistance beyond search.**
Verified by: a manual exercise with synthetic evidence and supported Jev
configuration showing applicable ranking, finding classification, criterion
support assessment, and hypothesis evaluation. Compare against the existing
path and identify a concrete decision the judgments informed; search-only use
or calls without a useful decision fail this criterion.

**AC-2 — Independent judgments use the appropriate batch shape.**
Verified by: observed invocation records for independent questions about one
state and for multiple candidates under shared questions. Per-question fan-out
where one call suffices, or failure to use judge_batch for the latter case,
fails this criterion. Keep private payloads and credentials out of commits.

**AC-3 — Token-aware use preserves availability and credential privacy.**
Verified by: isolated configured, unconfigured, and unavailable-provider exercises
using the supported credential contract. The unconfigured path remains usable,
secrets are absent from output and persisted artifacts, and failed or skipped
judgments are not represented as successful evaluations.

**AC-4 — Evidence and approval boundaries remain intact.**
Verified by: an exercise where a judge favors a conclusion contradicted by a
deterministic check or primary observation, and one involving an approval-bound
action. The contradiction remains visible and the action stays unauthorized
without the user's approval; judge-only proof or permission fails the criterion.

**AC-5 — Users can tell what Jev contributed.**
Verified by: final responses from a useful-judgment case and a no-useful-opportunity
case. The former names the evaluation and its decision impact; the latter states
that no useful opportunity existed without manufacturing calls or conclusions.

## Test plan

During ideation, select existing deterministic checks and synthetic cases for
configuration, batching, failure, and authority boundaries. Keep all model-backed
checks manual and outside CI. Exercise the actual supported host integration and
report unsupported capabilities explicitly. This filing starts no live run;
record any required live-run approval separately before execution.

## Decisions and dependencies

The Captain requested filing this task, not starting design or implementation.
The supplied guidance defines desired product behavior; the token variable name,
provider configuration, and cross-host API mapping remain to be investigated.
Do not introduce a new report format solely to describe Jev usage; agree on the
smallest user-facing disclosure during design.

### Feedback Cycles

No correction rounds recorded.

## Out of scope

Making Jev mandatory; replacing deterministic checks; granting permissions or
auto-approving gates; unnecessary model calls; storing tokens or private evidence;
changing the Spacedock runtime adapter; unrelated report redesign.
