---
title: Reduce Behavior Diff assessment latency without weakening evidence
status: implementation
source: Captain request on 2026-10-27 to diagnose and refactor recent slowdown; Captain selected the Spacedock workflow.
started: 2026-10-27T08:40:55Z
completed:
verdict:
score: 0.9
worktree: .worktrees/spacedock-ensign-reduce-assessment-latency
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
        - id: gate:vnaxvsdna9hvd5fgebv5fp5y:ideation
          stage: ideation
          attempts:
            - id: gate-attempt:vnaxvsdna9hvd5fgebv5fp5y-ideation-1
              briefing:
                id: briefing:vnaxvsdna9hvd5fgebv5fp5y:ideation:attempt-1:revision-1
                digest: sha256:ac391a9d48e8e9c1f4a312ef7b1eee8961d11c20b102421bbf4e7a9ffaa97536
                room-ref: ./reduce-assessment-latency/review/ideation/briefing-1
              resolution:
                type: Resolution
                id: resolution:spacedock:vnaxvsdna9hvd5fgebv5fp5y:ideation:1
                briefing: briefing:vnaxvsdna9hvd5fgebv5fp5y:ideation:attempt-1:revision-1
                by: person:captain
                at: "2026-10-27T11:05:05.021632Z"
                decision: approve
                reason: 'Captain said: pre approve the identify gate, let us start implementation with pre-approval; Captain separately authorized at most three timed extraction calls/$3 total on the same saved evidence/provider/model. Accept profiling-first design with bounded latency/fidelity acceptance.'
              application:
                target-stage: implementation
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
seconds. The smallest justified next effect is the now-authorized profiling
replay, followed by a narrowly chosen implementation and one before/after pair.
Do not spend the pre-approved implementation stage on whitespace-only compaction
as if it were demonstrated user value.

Captain pre-approved ideation into implementation and subsequently authorized
at most three extraction invocations, US$3 total, on the same saved evidence
with the same configured OMP provider/model. This does not authorize new trials,
scenarios, publication, validation/delivery, product push, PR, merge, or release.
The implementation worker owns the entire replay ledger; this ideation worker
must not spend any of those invocations. No paid calls were made in ideation.

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

Do not close the refactor because its prompt shrinks or its code compiles.
A demonstrated seconds-based improvement at the selected real latency seam,
with preserved assessment fidelity, suffices for a bounded bottleneck claim.
A different profiled cause changes the implementation surface and must receive
a concrete bounded design first.
No new permanent timing infrastructure, benchmark service, CI provider call,
parallel extraction, model substitution, outcome cache, or additional trial set.

## Acceptance criteria

1. **Measured user value, not payload size — authorized bounded replay.**
   On an identical frozen assessment input with the exact same host/model and
   settings, report baseline and candidate subprocess seconds, pre-output
   seconds and observable-generation interval. A candidate is an observed
   improvement at the selected latency seam only when its elapsed seconds are
   lower and assessment fidelity is retained. Distinguish measured subprocess
   time from any inferred effect on the runner's serial critical path.
   One pair cannot establish stable population latency or a complete skill
   speedup. Preparation and post-run audit remain unmeasured limitations, not
   mandatory new outer-agent studies or additional paid full-skill runs.
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

**Captain-authorized live scope, superseding the earlier US$5 proposal:**

- Purpose: distinguish pre-output/session work from observable generation on
  the slow assessment, then assess one evidence-preserving latency candidate.
- The implementation worker may execute **one unchanged extractor replay**.
  Only after reviewing that profile, select a concrete candidate and use at
  most **two further extractor invocations**, baseline then candidate: at most
  three total, zero trial invocations, zero new scenarios, zero full comparison
  reruns, zero Jev calls. Failed attempts count toward the same three-call cap.
- Pin OMP and the saved extractor selector `openai-codex/gpt-6-luna`; record
  the actual resolved provider/model and stop on mismatch. Use the same current
  frozen saved prompt/task, installed style guidance, evidence and invocation
  context for baseline and candidate; only the named candidate may differ.
  The approved `openai-codex` provider receives the same private saved
  instruction/task content, derived purpose/scenario and bounded trial evidence.
  Captain specifically approved this saved-evidence/provider/model handoff;
  neither a different provider nor additional private content is authorized.
- Approved combined spend ceiling: **US$3 total for all three invocations**.
  FO verified the current catalog using `omp models find gpt-6-luna --json`:
  provider `openai-codex`, selector `openai-codex/gpt-6-luna`, context window
  272,000, maximum output 128,000, fixed per-million-token pricing of US$0.10
  input, US$0.50 output, US$0.01 cache read, US$0 cache write.
  Verify the actual exposed provider/model and current catalog before replay;
  stop on a price/model mismatch, without silently substituting or spending.
  At these prices, a conservative full-window/full-output request costs at most
  272,000 × 0.10 / 1,000,000 + 128,000 × 0.50 / 1,000,000 = US$0.0912.
  Set `--max-cost 0.50` per invocation. This trigger is not itself a hard cap:
  assuming the runtime starts no request after the threshold and permits at most
  one in-flight overrun, each invocation is bounded by US$0.5912 and all three
  by US$1.7736, below the approved US$3. Preserve this pricing/runtime caveat,
  record actual usage and cumulative cost, and do not treat unused allowance as
  authorization for more calls. No new budget prompt is needed within this grant.
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

This grant does **not** authorize outer-skill agent execution or prove end-to-end
skill latency. Unmeasured preparation/audit costs remain explicit limits on the
claim, not a mandatory additional study or a blocker to a demonstrated
bottleneck improvement. Any later outer-stage experiment requires separate
authority; do not spend a full six-trial comparison merely to time those stages.

## Decisions and dependencies

Recommendation: use the authorized one-replay profile before choosing a latency
fix (confidence: high). Why: the smallest verifiable action avoids busywork while
preserving the evidence the user needs. The exact avoidable cause remains
unknown; no stronger causal outer-session trace was available in scoped history.

Captain's workflow and ideation-to-implementation preapproval stands, and the
explicit three-invocation/US$3 saved-evidence grant now resolves the live replay
prerequisite. Only the implementation worker may consume that ledger. A bounded
measured improvement at the selected seam is sufficient; full outer preparation
and audit timings are not a newly imposed acceptance gate. No Linear publication
or product push is authorized. State report synchronization follows the
commissioned split-root state protocol.
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

## Stage Report: ideation (cycle 2)

- DONE: Identify the assessment-latency bottleneck from actual local evidence, comparing input size, output-generation work and CLI startup/context without substituting payload reduction for measured seconds.
  Existing offline evidence is unchanged; selected-seam timing and fidelity remain the required proof, with unmeasured outer preparation/audit retained as limitations.
- DONE: Recommend the smallest evidence-preserving refactor and alternative, including affected files, size/tolerance, preserved contracts, risks, concrete AC and seconds-based verification; identify separately consent-gated live proof if needed.
  Captain authorized at most three extraction invocations and US$3 total; AC1 now permits a bounded demonstrated seam improvement without imposing a new full-skill study.
- DONE: Commit the exact ideation report and design/acceptance criteria in the task state with DCO sign-off; no product edits and no builds/tests/lint/formatters or paid Behavior Diff calls.
  Amendment changes only this task body/report; implementation owns all three replay attempts, actual usage/cost accounting, and model/provider verification.

### Summary

This correction supersedes the earlier proposed US$5 grant and any requirement
for a new matched outer-agent preparation-to-audit study. The current fixed-price
catalog supports a conservative US$1.7736 three-invocation bound under the stated
cost-trigger/runtime assumptions, below the approved US$3; no invocation was
spent here. Same-input seconds comparison and all evidence/safety obligations
remain mandatory, and any claim must stay scoped to the measured latency seam.

## Stage Report: implementation

- DONE: Before product edits, profile one unchanged extraction on a private read-only replay of the frozen saved evidence using the explicitly approved exact OMP provider/model; capture monotonic startup, reasoning/text event intervals, elapsed seconds, usage and assessment validity within the shared three-call/$3 ledger. Send the observed cause and bounded proposed fix to FO before changing product behavior.
  Profile #1 exposed a trailing inherited advisor; FO authorized extraction-only suppression before mutation. Original aggregate spend is unknown because the ancillary advisor emitted no usage receipt; it is not claimed within $3.
- FAILED: After FO authorization, implement only the measured bottleneck refactor with migrated callers and unchanged evidence/privacy/report contracts; compare seconds and assessment fidelity on fixed inputs using only remaining authorized calls. Retain null/noisy/failure results; no fewer trials, changed criteria, model substitutions, or extra live calls.
  Code `83fafb201ce4348db23bace45ea0f94ae08ba89e` adds only an OMP process-local advisor-disable overlay and architecture explanation; elapsed time fell, but bounded-input uncertainty preservation remains a live assessment support gap, not verified fidelity.
- DONE: Run smoke and relevant deterministic checks/formatters once after edits, update architecture/changelog, DCO-signoff implementation/report commits and record every AC with actual evidence and limits. No pushes/PR/merge/release and no permanent profiling infrastructure.
  Final verification after FO-authorized removal of incidental wiring assertions passed; code/report commits are path-scoped and signed off. Architecture follows the existing documentation convention; no changelog exists.

- FAILED: AC-1 — Measured user value, not payload size — authorized bounded replay.
  Subprocess elapsed 69.069 → 40.553 seconds, first text 7.376 → 9.148, observable text span 37.784 → 30.044; lower elapsed is observed, but the fidelity conjunct is not established.
- SKIPPED: AC-2 — Lossless inputs — offline, if preparing the compact candidate.
  No compact candidate was prepared. Actual emitted user-message content is identical across replays; complete primary system/HTTP request byte equivalence was not captured.
- FAILED: AC-3 — Assessment/report contracts survive — offline plus approved live replay.
  Both responses normalize all five exact frozen checks and 30 memberships without rejection and the candidate renders; 12 candidate `met` judgments exceed the bounded state evidence, so normalization is not semantic fidelity proof.
- FAILED: AC-4 — No safety or scope regression — offline and interactive where needed.
  Unchanged baseline unexpectedly inherited an ancillary advisor outside the named model grant; actual ancillary provider/model/usage remain unverified. Captain acknowledged this incident and separately authorized advisor-disabled calls; candidate emitted zero advisor events and kept all other gates.
- DONE: AC-5 — Honest stopping condition.
  Two extraction invocations total, no new trials/scenarios or full outer run; third invocation remains unspent under FO HOLD. Raw results/disagreements were retained without prompt retuning, weaker criteria or a whole-skill speed claim.

### Evidence and limits

- Baseline events: session 0.866s, agent start 3.576s, first/last text 7.376/45.160s, text end 45.498s, primary agent end 45.728s, advisor card/yield 68.411s, exit 69.069s.
- Candidate events: session 0.913s, agent start 3.260s, first/last text 9.148/39.192s, text end 39.524s, primary agent end 39.781s, exit 40.553s; no advisor events. Both exited zero and exposed no reasoning deltas, not proof of zero hidden reasoning.
- Exact extraction provider/model: `openai-codex/gpt-6-luna`; auto resolved low in both, unchanged prompt/context/evidence. Baseline input/output 188028/5487 tokens, primary catalog cost $0.0215463; candidate 188028/4900, $0.0212528.
- Original ancillary spend is UNKNOWN, not zero. Captain's fresh separate $1 allowance covered at most two remaining isolated invocations with `--max-cost 0.25`; only one used ($0.0212528). Verified pricing/limits imply at most $0.6824 for that pair under the one-in-flight-overrun assumption; this does not reconcile the original $3 grant.
- Actual offline settings smoke: inherited advisor true → process overlay false → inherited true, all exits zero, without provider calls/global edits. Actual product `_omp` launcher was exercised with disposable event/cost instrumentation; private persistence and HTML/data rendering also exited zero.
- Final commands below all exited zero from the assigned worktree after the authorized correction; foreign/missing trial or frozen-check mutations and invalid source/excerpt contracts fail these deterministic checks, but they do not prove model judgment:
  `python3 plugin/skills/behavior-diff/scripts/decisions.py --check` — self-check passed.
  `python3 tests/report-schema-test.py` — report/schema contracts passed.
  `python3 tests/scenario-contract-test.py` — 10 tests passed.
  `python3 tests/recorded-evidence-test.py` — 23 tests passed.
  `python3 tests/progress-assessment-test.py` — 8 tests passed.
  `bash tests/live-report-contract.sh` — live-report deterministic contract passed.
  `uvx ruff@0.16.5 format --check --diff plugin/skills/behavior-diff/scripts/decisions.py` — already formatted.
  `git diff --check` — passed without diagnostics.
- The earlier pre-correction suite passed its deterministic tests but Ruff rejected formatting in added wiring assertions; FO directed removal of those assertions, not repinning. The complete final check chain then passed. No permanent regression test was added at a mock-only seam; real effective-settings and live consumer smoke supply the behavior evidence.
- Full raw audit covered all six original native traces, observation returns, final workspace/action journals and tracker reads: all support the actual intended conditions. Candidate classifications agree with richer raw artifacts; they overstate support available in its bounded extractor input. Baseline also overstates readable observation and incorrectly says draft arguments were absent; those defects are retained separately.
- Causal limits: tagged upstream OMP v18.13.1 hooks construct a separate advisor Agent at primary turn end; no direct primary-prompt mutation was found in inspected hooks. Baseline's advisor card arrived after primary completion; observable user content matches, but no full request capture establishes wire equivalence or rules out other runtime effects.
- Finding for independent validation: released user/workflow = owner reading a normal comparison; observable risk = unsupported certainty in 12 per-trial judgments; authority = value-ac[AC-3], preserving evidence/uncertainty obligations; trigger = candidate raw judgments versus frozen state requirements and omitted returns. Actual wrong underlying outcomes and advisor-caused regression were not demonstrated; FO held reruns and prompt/validator repair.
- Source artifacts stayed read-only; private ledger, raw replies/events, rendered copy and audits remain private for FO/reviewer access. No private excerpts, paths or digests enter this report. Implementation model exposed as `openai-codex/gpt-6.1-sol`; parent owns independent validation.

### Summary

The candidate removes an accidental OMP advisor review and its measured trailing wait without changing trials, extraction content, model, effort or the mandatory raw audit. This pair observed 28.516 seconds lower subprocess time, but output-length variability and unresolved bounded-evidence certainty prevent an unqualified fidelity or stable speedup claim. Preparation/post-run audit remain unmeasured; independent validation must disposition the explicit support gap.
