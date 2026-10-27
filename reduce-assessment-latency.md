---
title: Reduce Behavior Diff assessment latency without weakening evidence
status: ideation
source: Captain request on 2026-10-27 to diagnose and refactor recent slowdown; Captain selected the Spacedock workflow.
started: 2026-10-27T08:40:55Z
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
              resolution:
                type: Resolution
                id: resolution:spacedock:vnaxvsdna9hvd5fgebv5fp5y:backlog:1
                briefing: briefing:vnaxvsdna9hvd5fgebv5fp5y:backlog:attempt-1:revision-1
                by: person:captain
                at: "2026-10-27T08:40:25.393614Z"
                decision: approve
                reason: Captain explicitly requested diagnosis and refactoring, selected the Spacedock workflow, and pre-approved the ideation gate into implementation.
              application:
                target-stage: ideation
                state: consumed
---

Make the complete Behavior Diff skill faster without weakening trials, privacy,
preflight, goal checks, raw-evidence assessment, or report contracts. The entity
slug is narrower than the user-facing request; extraction is one stage, not the
whole task.

## Problem

The Captain reports slower comparisons. Existing local evidence identifies a
72–99-second serial assessment subprocess across five different runs, not a
same-input version regression. The latest runner took 149 seconds: concurrent
trials ended after 75 seconds and assessment took 73 seconds. That subprocess
includes CLI/session startup, inherited context, provider wait/prefill, reasoning,
and generation; its elapsed time does not isolate any one of them.

Preparation and post-run assessment also matter. Artifact timestamps show
627 seconds from purpose write to runner start and 205 seconds from report
completion to audit-file write. These are elapsed file gaps, not active compute
measurements or causal attribution. The original request is not complete merely
because the extractor prompt becomes smaller.

## Recommended approach

**Measure one unchanged extractor replay before selecting a latency fix.**
Offline work has not isolated an avoidable delay that explains the observed
seconds. The smallest justified next effect is a separately authorized profiling
replay, followed by a narrowly chosen implementation and one before/after pair.
Do not spend the pre-approved implementation stage on whitespace-only compaction
as if it were demonstrated user value.

Captain pre-approved ideation into implementation, not provider calls,
validation/delivery, push, PR, merge, or release. Implementation can prepare a
low-risk candidate offline, but actual latency acceptance remains open until the
specific provider/data/cost grant below. No paid calls were made in ideation.

## Evidence and competing hypotheses

The following are peer hypotheses, ranked by evidentiary strength rather than
the seed's preferred implementation. Source: current canonical code, existing
local measurements supplied with dispatch, read-only saved artifacts, and the
offline experiments described below. Only safe aggregates are recorded here.

1. **Assessment provider/session work is the runner bottleneck.** The 73-second
   extractor is on the serial critical path. Prediction: event-timed replay
   distinguishes a large pre-output interval from prolonged observable output.
   Neither outcome alone separates provider queueing, prefill, hidden reasoning,
   buffering, or host context. No raw extractor reply or extractor event stream
   was saved in the inspected run, so generation throughput cannot be recovered.
2. **Preparation/preflight contains expensive orchestration.** The 627-second
   artifact gap and a bespoke 73-line preflight with six Python functions show
   substantial setup, not its avoidable duration. Required premise probes,
   source verification, permission correction, and freeze work are real safety
   work. Prediction: a timed outer-skill trace attributes time to repeated
   mechanics versus scenario judgment. File mtimes cannot establish this.
3. **Post-run work repeats analysis or traverses evidence inefficiently.**
   The 205-second artifact gap is only a clue. Inspection found that the raw
   audit resolves unavailable automatic source judgments using original native
   returns and artifacts. It is necessary, not redundant report paraphrasing.
   Prediction: trial-at-a-time traversal can reduce repeated reads while keeping
   every case/trial check; no timed comparison currently supports that benefit.
4. **Output generation is disproportionately large.** The 165,341-byte saved
   decisions file is normalized output, not raw generated text. Approximately
   122,870 compact bytes are deterministic recorded evidence; target assessment
   is approximately 10,731 bytes, chain 2,318, explanation 2,118, and trial
   summaries 1,135. The run has five criteria and six decision rows. Output
   volume is plausible work, but file size does not prove decode dominance.
5. **Inherited host context/startup or input redundancy costs seconds.**
   Extractors inherit cwd. OMP disables tools/session/title, not context files,
   rules, skills, or extensions; Claude's empty allowedTools is not tools-empty.
   Current OMP help exposes context-disabling controls, but compatibility and
   initialized-session timing have not been exercised. Exact duplicate returned
   text is 21,072 characters; interning may reduce input but adds a reference
   contract and interpretation risk. Neither hypothesis is selected.

The fixed assessment prompt was already large: historical AST measurements
supplied by the FO show schema/prompt sizes of 7,586/28,316 characters at
7ee50c4 and c4c2c00, 7,724/29,411 at 4ff0321, and 7,910/31,319 at 8fd14ad
and HEAD. Recent scenario changes did not turn a tiny prompt into a 39k prompt.
Different saved scenarios/hosts cannot establish a version-induced slowdown.

### Offline timing and reversible experiment

- Existing prompt-build measurement: 0.0665 seconds, 186,681 characters.
- Read-only evidence collection, seven calls: median 0.047631 seconds,
  range 0.047596–0.053386. There are 83 records: 22 available, 18 truncated,
  43 omitted. All six trial identities must survive.
- In-memory normalization of a saved normalized-field projection, seven calls:
  median 0.002986 seconds, range 0.002549–0.004795. This is not recovered raw
  provider output and does not establish model compliance.
- Version-only process startup, three calls per CLI: OMP median 0.0130 seconds,
  Claude 0.0115, Codex 0.0125, Pi 0.2204; all exited zero. These fast paths
  are lower bounds, not initialized extraction-session measurements.
- Temporary AST-local replacement of only build_prompt's JSON serializers,
  with no file writes or provider calls: baseline median 0.054217 seconds,
  compact median 0.052910 over seven calls each. Ranges overlap. No material
  local speedup is established.
- The compact candidate produced 175,988 versus 186,681 characters, a reduction
  of 10,693 (5.73%). Savings: evidence 10,000, scenario 369, instruction hunks
  170, purpose 92, trial groups 55, completed names 7. All six decoded JSON
  blocks compared equal; every other format input, completed-trial membership,
  and instruction diff compared equal. No input-size-to-seconds claim follows.

The temporary candidate existed only in interpreter memory. No product edits,
temporary files, builds, tests, linters, formatters, or provider calls were made.

## Minimal candidate and simplest alternative

**Recommended: profile first, then change only the demonstrated seam.** Preserve
the existing one-call assessment and every required report section. If the one
profiling replay still cannot distinguish actionable causes, record that result;
do not manufacture a successful latency refactor.

The simplest implementation alternative is whitespace-only JSON serialization
inside `plugin/skills/behavior-diff/scripts/decisions.py:build_prompt`, using
compact separators for all six structured input blocks. It requires no text
interning, shared-string table, schema version, new dependency, public flag,
renderer change, or host configuration change. The offline experiment exercises
the risky semantic-preservation mechanism; another spike is unnecessary.
This is an optional low-risk candidate, not the selected explanation or a
substitute for the profiling prerequisite.

If generation dominates, consider removing only deterministic echoes of frozen
criterion definitions from the *model reply*, reconstructing them from the
validated frozen record before existing normalization. Keep every per-trial
outcome, reference, excerpt, explanation, and assessment obligation. This is a
different, larger contract migration and is not approved for implementation by
this design without profiling evidence and a concrete revised design.

If initialized host/context cost dominates, first exercise compatible isolation
in disposable environments for every affected host; never apply OMP flags to
Claude/Codex or remove installed style/provenance safeguards by analogy. If
outer preparation or raw audit dominates, optimize its repeated mechanics or
traversal, not case coverage or safety checks. Prose-only changes are not proof
of a speedup.

## Expected surface and tolerance

No implementation is required in ideation. The bounded whitespace candidate,
if the FO elects to prepare it before the live gate, is one focused PR:

- `plugin/skills/behavior-diff/scripts/decisions.py`: six serialization sites,
  approximately 10–25 changed lines, tolerance 50%; no new abstraction required.
- Existing `decisions.py:self_check` and/or `tests/target_contract.py`:
  approximately 40–80 lines, tolerance 50%, synthetic decoded-block/evidence
  preservation checks at the real prompt/ingestion boundary.
- `docs/architecture.md`: approximately 5–10 lines, tolerance 50%, describing
  lossless input formatting without a measured-speedup claim.
- No changes to trial count/model, execution permissions, report hierarchy,
  saved report schema, evidence collector budgets, skill preparation recipe,
  or raw-audit obligations for this candidate.

Retain the end-to-end investigation in this task rather than closing the request
when that PR compiles or its prompt shrinks. A different profiled cause changes
the implementation surface and must receive a concrete bounded design first.
No new permanent timing infrastructure, benchmark service, CI provider call,
parallel extraction, model substitution, outcome cache, or additional trial set.

## Acceptance criteria

1. **Measured user value, not payload size — interactive/consent-gated.**
   On an identical frozen assessment input with the exact same host/model and
   settings, report baseline and candidate subprocess seconds, pre-output
   seconds, observable-generation interval, and full runner critical-path
   effect. A candidate is an observed extractor improvement only when its
   elapsed seconds are lower and assessment fidelity is retained. One pair
   cannot establish stable population latency or a complete skill speedup.
   To close the user-facing request, measure preparation → runner → raw audit
   → final response on matched outer requests as well, without trading away
   obligations. Missing end-to-end measurement remains an explicit open gate.
2. **Lossless inputs — offline, if preparing the compact candidate.**
   Decode every structured prompt block on synthetic boundary runs and compare
   exact objects, order, trial identities, sources, ranges, statuses, reasons,
   retained text and Unicode/whitespace inside values. Compare non-JSON prompt
   sections and diff/hunk numbering unchanged. Empty/missing evidence,
   truncation, omitted/unavailable records and interrupted trials remain
   distinguishable. A deleted record or changed excerpt must fail this check.
3. **Assessment/report contracts survive — offline plus approved live replay.**
   Real prompt emission and ingestion/normalization/rendering seams retain
   scenario/check definitions, all completed memberships, minority outcomes,
   exact excerpts, source requirements and rejection behavior. Use synthetic
   fixtures for deterministic assertions; missing-source or foreign-trial
   mutations must still fail closed. Deterministic tests alone do not prove a
   model interprets the new formatting identically.
4. **No safety or scope regression — offline and interactive where needed.**
   Preserve private raw notes, provider disclosure/consent, historical
   isolation, neutral tasks, capability preflight, freeze checks, default trial
   counts, current exact models, first-result retention, and the full raw audit.
   Do not publish private artifacts, excerpts, paths, or hashes. Inspection and
   later deterministic checks cover the candidate's unchanged boundaries;
   actual skill execution is necessary for behavior/timing claims.
5. **Honest stopping condition.**
   No speedup claim from character counts, overlapping local timings, file
   mtimes, or a smaller saved decisions file. A null/noisy result stays null;
   no repeated reruns, weaker criteria, or silent narrowing to extraction.

## Verification and consent-gated next step

Offline implementation verification, run once after edits by the responsible
stage: `python3 plugin/skills/behavior-diff/scripts/decisions.py --check`,
`python3 tests/report-schema-test.py` (the driver for `target_contract.py`),
`python3 tests/scenario-contract-test.py`, `python3 tests/recorded-evidence-test.py`,
`python3 tests/progress-assessment-test.py`, and `bash tests/live-report-contract.sh`.
Use repository-required formatting and Markdown checks after implementation;
these commands were not run in ideation. Real saved inputs stay read-only.

**Smallest live grant to request, not authorization already held:**

- Purpose: distinguish pre-output/session work from observable generation on
  the slow assessment, then assess one evidence-preserving latency candidate.
- First authorize **one unchanged extractor replay**. Only after reviewing
  that profile, select a concrete candidate and use at most **two further
  extractor invocations**, baseline then candidate: at most three total,
  zero trial invocations, zero full comparison reruns, zero Jev calls.
- Pin OMP and the saved extractor selector `openai-codex/gpt-6-luna`; record
  the actual resolved provider/model and stop on mismatch. Use the same current
  frozen saved prompt/task, installed style guidance, evidence and invocation
  context for baseline and candidate; only the named candidate may differ.
  OMP's OpenAI-Codex provider receives private saved instruction/task content,
  derived purpose/scenario and bounded trial evidence. Require specific
  approval for that provider and payload; earlier run consent is not this grant.
- Proposed combined spend ceiling: **US$5 for all three extractor invocations**,
  subject to the Captain's explicit approval. Before any call, establish an
  enforceable request/output bound and current provider pricing or quota
  accounting that fits the remaining allowance. OMP's `--max-cost` may finish
  an in-flight request above its trigger and is not by itself a hard ceiling.
  If a hard currency bound is unavailable for this provider, disclose that and
  obtain a named quota/token allowance instead; do not claim US$5 is enforced.
- Use a disposable private timer/event capture, not committed infrastructure.
  Capture monotonic subprocess spawn/exit and timestamps of observable model
  text events, actual usage and exit status. OMP's JSON mode is documented by
  current CLI help; verify actual event semantics during the authorized replay.
  First stdout is not automatically first model token; buffering and hidden
  reasoning limit decomposition. Do not print/commit captured private events.
- Keep source runs/reports unchanged. Candidate outputs go only to a private
  disposable copy and are audited against every frozen check, trial identity,
  source record and evidence limit. Preserve disagreements; no retuning goals.
  If profiling is inconclusive or an invocation fails, report it within the
  three-call cap rather than silently retrying.

This small grant does **not** authorize outer-skill agent execution or prove
end-to-end skill latency. If preparation/audit remains the suspected bottleneck,
bring a separate bounded same-request outer-stage timing proposal with its own
session/request limits, provider/data disclosure and cost grant. Do not spend a
full six-trial comparison merely to time preparation or audit.

## Decisions and dependencies

Recommendation: take the one-replay profiling gate before choosing a latency fix
(confidence: high). Why: the smallest verifiable action avoids busywork while
preserving the evidence the user needs. The exact avoidable cause remains
unknown; no stronger causal outer-session trace was available in scoped history.

Captain's workflow and ideation-to-implementation preapproval stands. The FO
must surface the separate provider/data/budget decision; preapproval cannot
manufacture it. No Linear publication or product push is authorized. State
report synchronization follows the commissioned split-root state protocol.
Actual exposed ideation model: `openai-codex/gpt-6.1-sol`; the saved extractor
model above is different and must not be substituted for it.

## Out of scope

Fewer trials, weaker criteria/evidence, model substitutions, changed report
formats or hierarchy, outcome caches, new permanent profiling infrastructure,
CI/provider changes, private-data publication, or unauthorized paid runs,
product push, PR, merge, and release. The necessary raw audit is not optional.

## Stage Report: ideation

- DONE: Identify the assessment-latency bottleneck from actual local evidence, comparing input size, output-generation work and CLI startup/context without substituting payload reduction for measured seconds.
  The serial 73-second subprocess is established; prefill/startup/generation attribution remains unknown. Evidence and competing hypotheses also covers preparation and the necessary raw audit.
- DONE: Recommend the smallest evidence-preserving refactor and alternative, including affected files, size/tolerance, preserved contracts, risks, concrete AC and seconds-based verification; identify separately consent-gated live proof if needed.
  Recommend one profiled unchanged replay before choosing a fix; a fully bounded lossless-formatting alternative, five falsifiable AC, and a three-invocation/provider/data/budget proposal are recorded above.
- DONE: Commit the exact ideation report and design/acceptance criteria in the task state with DCO sign-off; no product edits and no builds/tests/lint/formatters or paid Behavior Diff calls.
  This entity is the sole write/commit target; read-only timings and an in-memory serialization experiment produced aggregate evidence without product or private-artifact changes.

### Summary

The original request concerns complete skill latency, not just extractor input
size. Offline measurements do not establish a useful latency fix: formatting
saves 10,693 input characters, but prompt-build timings overlap and the large
saved decisions file is mostly deterministic evidence. The next justified step
is specific consent for one timed extractor replay, with at most two follow-up
invocations; implementation preapproval remains valid but does not grant paid
execution or establish user-value acceptance.
