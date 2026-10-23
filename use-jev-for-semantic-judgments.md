---
title: Use Jev for semantic judgments when configured
status: ideation
source: Captain request to proactively use Jev when the user has configured a token
started: 2026-10-23T08:37:22Z
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
        - id: gate:sd4j775gcwrmhxnd0rm84a36:ideation
          stage: ideation
          attempts:
            - id: gate-attempt:sd4j775gcwrmhxnd0rm84a36-ideation-1
              briefing:
                id: briefing:sd4j775gcwrmhxnd0rm84a36:ideation:attempt-1:revision-1
                digest: sha256:b3208d3815c60228d225c7a93b836f626578208f738522e1d3d22334bd066cae
                room-ref: ./use-jev-for-semantic-judgments/review/ideation/briefing-1
              resolution:
                type: Resolution
                id: resolution:spacedock:sd4j775gcwrmhxnd0rm84a36:ideation:1
                briefing: briefing:sd4j775gcwrmhxnd0rm84a36:ideation:attempt-1:revision-1
                by: person:captain
                at: "2026-10-23T08:47:49.904101Z"
                decision: approve
                reason: Captain approved the shared-helper design and implementation dispatch in chat. Paid runs, external data sends, product push/PR and merge remain unapproved.
              application:
                target-stage: implementation
                state: pending
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

## Ideation design — proposed, not implementation approval

### Recommendation and alternative

Recommend an optional, skill-owned Jev advisory step with one bundled Python
standard-library helper shared by Claude Code and Codex. Invoke it only for a
specific unresolved semantic decision, with a supported credential and approved
provider/data/cost scope. Keep the current comparison and assessment path intact.
Use the same reference from the headless and live skills; do not add another
extractor, report format, host plugin, or workflow service.

🧠 Kent's brain recommends: one optional shared helper, not an Eval-only rule
(confidence: high).
Why: the shipped hosts share Python execution, while the inspected Eval contract
can silently use a different model and is not supplied by either plugin manifest.

The simplest alternative is instruction-only opportunistic use of a verified
native Jev tool, leaving hosts without one on the existing path. That has fewer
files, but does not satisfy configured Claude Code/Codex users consistently:
installing a TypeSafe skill supplies guidance, not a callable Jev integration.
Do not silently narrow AC-1 to OMP. A mandatory SDK/MCP dependency is a third
option, rejected because it adds installation/configuration without solving a
requirement the documented HTTP interface cannot cover.

### Inspected contracts and credential discovery

- Repository authority: `AGENTS.md:29-48`, `CODING_GUIDELINES.md:45-87,133-169`.
  Canonical source is `plugin/`; one product/two hosts; stdlib first; deterministic
  CI; skill wording checks do not prove agent behavior.
- Existing baseline: `plugin/skills/behavior-diff/SKILL.md:13-54,317-359` and
  `docs/architecture.md:120-178`. The skill already owns semantic interpretation
  from raw evidence. Extraction writes narrative in its existing model call and
  must not invoke tools or add a call. Jev belongs in the outer skill, not there.
- Host declarations: both `plugin/.claude-plugin/plugin.json` and
  `plugin/.codex-plugin/plugin.json` declare the same product/version, no Eval
  or Jev tool binding. Existing skills already invoke bundled Python scripts.
  [TypeSafe's agent guidance](https://docs.typesafe.ai/introduction/coding-agents.md)
  explicitly says Jev is a separate typed API, not a replacement host model.
- [Credential constants](https://docs.typesafe.ai/sdk/python/api/constants.md)
  name `TYPESAFE_API_KEY`, `TYPESAFE_DEFAULT_MODEL`, `TYPESAFE_BASE_URL`,
  default `jev-latest`, and `https://api.typesafe.ai`. The
  [client contract](https://docs.typesafe.ai/sdk/python/api/clients/sync.md)
  trims surrounding key whitespace and rejects internal whitespace/control or
  non-ASCII characters. SDK body logging is not redacted; avoid SDK/debug logs.
- Discover configuration by inspecting only that named environment variable's
  presence/validity inside the helper. Never print its value, enumerate the
  environment, search dotfiles/auth stores, source `.env`/profiles, or pass a key
  through arguments, task text, report config, or a request file.
  No real credential was read or tested during this ideation.
- Proposed helper supports `TYPESAFE_API_KEY` and `TYPESAFE_DEFAULT_MODEL`
  (default `jev-latest`) against the official HTTPS endpoint only. A nondefault
  `TYPESAFE_BASE_URL` is explicitly unsupported and causes a safe skip, not a
  silent send to either endpoint. No new credential variable or secret store.
- [HTTP contract](https://docs.typesafe.ai/api/system-one.md):
  `POST /v1/systemone`, Bearer header, `{model,state,questions}`; named answers,
  returned model and usage. One request accepts independent questions sharing
  one state. It does not document a multi-state batch endpoint.
- Eval's inspected `xd://eval/judge` contract provides `judge` and `judge_batch`,
  but says TypeSafe when credentialed, otherwise tiny/smol chat. `bool` maps to
  a probability under `bool`; HTTP calls it `noul`. Native batch has default
  retries and per-item failures; neither provider pinning nor single-judge
  provider metadata is exposed in that contract.

### Host mapping and proposed helper interface

Claude Code and Codex use the identical bundled
`scripts/jev.py` via their existing shell tool. Neither host is assumed to have
OMP Eval. This is an integration design, not a claim that either installed host
has executed it. Pi/OMP trial adapters and model selection remain unchanged.

When an orchestration host offers Eval, use native `judge`/`judge_batch` only if
its actual binding establishes Jev identity and excludes a non-Jev fallback.
The inspected binding does not establish that guarantee; use the shared helper
there too, or disclose unavailable configuration. Never call an unverified
fallback and label its output Jev. No OMP-internal credential discovery is added.

Proposed internal CLI: `python3 <skill-base>/scripts/jev.py <private-request.json>`.
The request has `operation: judge` with `state`, or `operation: judge_batch`
with a nonempty keyed `states` object; both include one `questions` map.
These are helper operations, not claims of native host tools or an HTTP batch API.
Validate the complete request before any network call. Use Choice, Score and
Noul in the documented HTTP shape; do not introduce a second question DSL.

- `judge`: all useful independent questions about one frozen state in one POST.
- `judge_batch`: the same questions over keyed states, one POST per state,
  bounded to four concurrent requests. Return by original key, not completion
  order. No per-question fan-out; no repeated judgments of the same frozen input.
- Results distinguish `ok`, `unconfigured`, `unavailable`, and `failed`; batch
  results retain each item independently. Successful results carry typed answers,
  actual returned model and usage. Skips/failures have no fabricated answers.
  Invalid input or provider failure returns nonzero; the skill handles that as
  optional assistance failure and continues its existing evidence assessment.
- Validate question IDs, answer types, allowed choices, finite probability
  ranges and required model identity before exposing a result as successful.
  Partial/malformed answers fail that state, not the whole Behavior Diff run.
- Fixed HTTPS endpoint, normal TLS verification, no redirects, bounded timeout,
  no automatic retries, no alternate provider/model. A 401, 429, overload,
  timeout, or malformed body yields a sanitized category, never a raw error
  response that might echo submitted evidence. Resume only on a new authorized
  attempt, not to obtain a more favorable answer.

### Useful decisions and boundaries

Before sending anything, identify the decision and the primary evidence needed
to check it. Use sanitized, bounded source observations with stable local IDs;
do not send entire traces, raw conversation, private case notes, or secrets.
Frozen purpose/case definitions may be generalized into minimal questions only
within their approved data scope. Keep scratch input/output outside the project,
directory mode 0700 and files 0600, following the existing purpose-file pattern.
No payloads or credentials in commits; no persistent Jev cache or report schema.

Examples of opportunities, not a quota to fill:

- Rank candidate evidence with a shared relevance Score; use ranking only to
  order inspection, never to discard contradictory or minority evidence.
- Classify a finding with Choice: supported difference, shared behavior,
  contradiction, or insufficient evidence.
- Assess one acceptance criterion against its recorded evidence with Choice:
  supports, contradicts, or insufficient. Keep reached/missed/unknown separate.
- Evaluate independent hypotheses over one observation state together, using
  separate Noul questions. A score/probability is not a proof or authorization.

Proactively identify useful opportunities when configured, but a token is not
permission to incur additional model cost or transmit data to another provider.
Before a new Jev use scope, name provider, payload category, purpose, request/state
count and cost ceiling and obtain explicit approval. Reuse that approval within
its stated bounds; do not ask per question. Existing approval for the comparison's
assessment provider does not silently cover TypeSafe. If approval is absent,
continue the existing path and say Jev was not run; never mislabel it as no
useful opportunity. Sensitive content needs its own specific approval or a safe
fixture. Normal automatic trial launching does not override this Jev boundary.

The host checks important judgments against tests, primary observations, or
sources. If Jev disagrees, keep both the disagreement and the stronger evidence
visible; do not change frozen goals, case criteria, trial memberships, extracted
decisions, or saved reports to fit it. Low confidence is uncertainty, not a
numeric acceptance gate. An approval-bound action remains unauthorized even
if every judgment favors it.

User disclosure is one ordinary final-response sentence, not a new panel:
“Jev ranked the evidence and flagged a possible contradiction; the recorded
command confirmed it, so I treated that criterion as unmet.”
For no opportunity: “Jev was not used: the remaining checks were deterministic.”
For another skip/failure: name that actual reason and say the existing evidence
assessment was used. Never claim Jev changed a decision when it only corroborated
one; name corroboration honestly.

### Preserved behavior, scope and delivery

Preserve scenario preparation, purpose freeze, source isolation, trial counts,
trial/extraction model selection, extraction calls, report JSON/HTML, deterministic
grading, provider consent, and user authority. Change only how the outer skill
obtains optional advisory judgments and discloses their contribution.
Non-goals: mandatory Jev, replacing extraction, autonomous pass/fail or approval,
paid CI, new report UI, OMP adapter/auth-store work, general provider framework,
image questions, custom endpoints, retries, or model-quality claims from mocks.

One feature PR after ideation approval, with helper + tests and skill/docs wiring
as two dependent commits; do not ship an unused helper in a separate PR.
No implementation, code-branch artifact, release, or paid run is approved here.
Expected files (new paths are proposals, not current files):

- New `plugin/skills/behavior-diff/scripts/jev.py` and
  `tests/jev-test.py`: ~220–320 production and ~220–320 test lines.
- New shared `plugin/skills/behavior-diff/references/jev.md`, small edits to both
  `plugin/skills/behavior-diff/SKILL.md` and
  `plugin/skills/behavior-diff-live/SKILL.md`: ~100–160 lines.
- `tests/live-report-contract.sh`, `.github/workflows/ci.yml`,
  `README.md`, `docs/architecture.md`, and `e2e/README.md`: ~60–100 lines.
  CI clears `TYPESAFE_API_KEY` and runs only the hermetic helper test; docs explain
  configuration, advisory scope, and the approval-bound manual exercise.

Estimate: ~600–900 changed lines across 10 files, tolerance +25% (up to ~1,125)
without widening behavior. Beyond that, return to design rather than adding a
framework. Both manifests stay unchanged unless a separately authorized release
requires a synchronized version bump. No dependency beyond existing Python 3;
live verification requires account access, host access, network permission and
explicit model/data/cost approval. Independent review and normal PR gates remain.

### Offline mechanism evidence — observed, limited

An in-memory Python Eval cell titled “Exercising offline Jev protocol shape” ran
an actual `HTTPServer(('127.0.0.1', 0), ...)` and `urllib.request` client with
proxies disabled, a synthetic Bearer value, and `ThreadPoolExecutor(max_workers=2)`.
There were no code-tree writes, provider connections, real credentials,
`judge`/`judge_batch` calls, trial runs, builds, tests, lint, or formatters.
This was a disposable protocol experiment, not the future helper or a model.

Exact stimulus: four independent Choice questions named `ranking`,
`classification`, `criterion`, `hypothesis`; a `single` state, two candidate
states, an empty-key state, and states requesting synthetic HTTP 401, 429, and
invalid JSON. Each POST used `{model:"jev-latest", state, questions}`.
The server returned keyed synthetic answers under a deliberately non-Jev model
name; this experiment checked transport/association, not production validation.

Observed output:

```json
{"absent_requests":0,"auth_header_shape_ok":true,"batch_states":["ok","ok"],"candidate_requests":2,"experiment":"stdlib-loopback-protocol-only","failure_outcomes":["http-401","http-429","invalid-json"],"paths":["/v1/systemone"],"questions_per_request":[4,4,4,4,4,4],"request_count":6,"single_state":"ok","single_state_requests":1,"unconfigured":"unconfigured"}
```

This establishes that stdlib HTTP can preserve the documented envelope, group
four questions in one request, associate two states separately, and distinguish
missing configuration and failure without a third-party package. It does not
establish credential validity, live API acceptance, model quality, privacy of
arbitrary input, host instruction following, or behavior of unimplemented code.
The product test must exercise the shipped helper, not reuse this toy client.

### Acceptance verification and value baseline

All checks below are future acceptance work, not completed acceptance claims.
Reuse the hermetic `unittest`/temporary-directory pattern in
`tests/purpose-handoff-test.py`; exercise the actual shipped helper with a
test-injected transport, never an environment-selectable production test endpoint.
Block external sockets, remove real credentials, and inject synthetic outcomes.
Static skill checks in `tests/live-report-contract.sh` cover wiring only.

- **AC-1:** Offline, capture one state with independent classification,
  criterion-support and hypothesis questions, plus a candidate-ranking batch.
  Assert IDs/typed results reach the caller; mutate the helper to return no
  answers and the check fails. This proves plumbing, not useful judgment.
  Approval-bound manual: each host reviews the same frozen synthetic packet
  once without Jev and once with Jev, with all four opportunities represented.
  Compare which source it inspects first, which finding it classifies, criterion
  outcome, and competing hypotheses against an independently authored evidence
  key. Require at least one concrete evidence-backed decision clarified or
  corrected versus the existing path, with no primary-evidence regression.
  Search-only use, extra calls with no decision value, or unsupported certainty
  fails. Accept a null result as failure of the value claim; do not retune/rerun.
- **AC-2:** Offline transport records must show exactly one POST containing all
  questions for `judge`, and N POSTs for N states under one `judge_batch`
  operation, each with the identical questions and stable state-key association.
  Delay responses out of order; association must survive. One request per
  question, dropped states or swapped keys fails. If a future verified native
  Eval binding is used, inspect its actual judge_batch invocation, not a loop
  labeled as batching. Manual host records must confirm the skill chose the
  appropriate operation; deterministic helper coverage cannot prove that choice.
- **AC-3:** Offline subprocess cases cover absent/blank/malformed fake keys,
  configured success, unsupported endpoint, 401/429/529, timeout, redirect,
  malformed/partial/non-Jev response and mixed batch failure. Assert zero network
  for skips, one attempt per submitted state, accurate result/exit categories,
  original-path availability, and absence of sentinel credentials/evidence from
  diagnostics or persisted artifacts. A success label on any failed state fails.
  Manual on both hosts, with approved synthetic sends, confirms the actual host
  receives configuration and continues its normal workflow on a denied provider.
- **AC-4:** Offline injected “supports” against a recorded nonzero check and a
  missing approval exercises result preservation, not autonomous agent behavior.
  Approval-bound host exercise must keep the failed observation visible,
  refuse an unauthorized publish/merge action, and avoid editing frozen inputs
  or reports; use inert command recorders, never a real external action.
  Any judge-only proof or action invocation fails, regardless of confidence.
- **AC-5:** Approval-bound host outputs for useful, no-opportunity, missing-key,
  denied-approval and failed-provider cases must name the actual contribution
  or reason. Count requests: no-opportunity/missing-key/denied approval must be
  zero. Claimed evaluations without records, omitted decision impact or a new
  report panel fails. Review human-facing clarity directly, not with a substring
  assertion masquerading as behavioral proof.

For the manual value exercise, propose two host sessions per host (baseline and
enabled), four sessions total; reuse frozen synthetic evidence, not new Behavior
Diff trials. An enabled session needs at most three Jev state requests: one
shared observation state and two candidates. That is at most six Jev requests
across both hosts, plus the approved host-session inference cost, no retries.
Other boundary cases use injected outcomes within the same approved sessions.
Before execution, obtain current pricing, state a dollar ceiling and payload
scope, then obtain explicit approval; no price or budget is assumed here.
Real-world saved cases remain desirable supplemental evidence under repository
guidelines, but require separate content approval before sending to TypeSafe.

### Decision for the ideation gate

Approve or reject the optional shared-helper design, official-endpoint credential
contract, and explicit additional-provider cost/data boundary. The proposed
defaults above resolve design choices; implementation and live verification are
separate permissions. Native Eval provider pinning remains unavailable in the
inspected contract, not a prerequisite for the two-host helper. Live usefulness,
valid credentials and host behavior remain unverified until the manual checks.

## Stage Report: ideation

- DONE: Recommend the smallest supported optional Jev integration and simplest alternative, grounding credential discovery and Claude Code/Codex capability mapping in inspected contracts and a safe offline mechanism exercise; no secrets or paid calls.
  Recommended shared stdlib helper versus instruction-only native tooling; linked TypeSafe contracts, inspected plugin/Eval surfaces, and recorded the synthetic loopback experiment above; no live judgment or trial invocation.
- DONE: Define preserved and changed behavior, non-goals, affected files, estimated change size with tolerance, dependencies and PR breakdown, including batching, provider failure handling, evidence and approval boundaries, and minimal user-facing disclosure.
  Design above specifies one feature PR/10 files/~600–900 lines (+25%), shared judge/batch operations, no retries or provider fallback, unchanged extraction/reporting, and one-sentence truthful disclosure.
- DONE: Map AC-1 through AC-5 to falsifiable offline or explicitly approval-bound manual verification, including user value against the existing path, and record the design plus exact evidence and remaining decisions in the task's ideation Stage Report.
  Each criterion above names observable failures and evidence level; value uses frozen baseline/enabled packets on both hosts, not mock quality claims; gate decision and live approval requirements are explicit.

### Summary

The design adds optional advisory judgments outside the existing extraction
call, with an identical supported path on Claude Code and Codex. The offline
experiment established only HTTP/batch mechanics; model usefulness and host
behavior remain approval-bound acceptance work, not claimed results.
