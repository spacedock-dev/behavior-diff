---
title: Reduce Behavior Diff assessment latency without weakening evidence
status: validation
source: Captain request on 2026-10-27 to diagnose and refactor recent slowdown; Captain selected the Spacedock workflow.
started: 2026-10-27T08:40:55Z
completed:
verdict:
score: 0.9
worktree: .worktrees/spacedock-ensign-reduce-assessment-latency
issue:
linear:
pr: "#55"
mod-block: merge:pr-merge
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
                room-ref: ./review/backlog/briefing-1
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
                room-ref: ./review/ideation/briefing-1
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
        - id: gate:vnaxvsdna9hvd5fgebv5fp5y:validation
          stage: validation
          attempts:
            - id: gate-attempt:vnaxvsdna9hvd5fgebv5fp5y-validation-1
              briefing:
                id: briefing:vnaxvsdna9hvd5fgebv5fp5y:validation:attempt-1:revision-1
                digest: sha256:72536ff68006c46d7eccafea004f501ada833bacfdad619bd58df46efb73346f
                room-ref: ./review/validation/briefing-1
              withdrawal:
                by: agent:first-officer
                at: "2026-10-27T12:19:45.91402Z"
                reason: New saved-trace evidence confirms advisor events and steering messages inside all six OMP trials; extraction-only candidate leaves this separate latency/tested-stack risk unchanged. Prior presentation omitted this newly verified risk and must be superseded before decision.
            - id: gate-attempt:vnaxvsdna9hvd5fgebv5fp5y-validation-2
              briefing:
                id: briefing:vnaxvsdna9hvd5fgebv5fp5y:validation:attempt-2:revision-1
                digest: sha256:c96faad1335202939d8da39a696c13dc79202508bf110c14e5c60b49706878b0
                room-ref: ./review/validation/briefing-2
              resolution:
                type: Resolution
                id: resolution:spacedock:vnaxvsdna9hvd5fgebv5fp5y:validation:2
                briefing: briefing:vnaxvsdna9hvd5fgebv5fp5y:validation:attempt-2:revision-1
                by: person:captain
                at: "2026-10-27T12:45:23.718509Z"
                decision: approve
                reason: Captain approved the presented validation/briefing-2 for independently reviewed shared OMP trial-and-extraction advisor isolation, candidate 2e3d915542233a263c13d7f9d72c378452c20e01, with disclosed and accepted evidence limits. Push, PR, merge and release remain separately ungranted.
              application:
                target-stage: done
                state: pending
review-round:
    id: round:vnaxvsdna9hvd5fgebv5fp5y:validation:1
    stage: validation
    cycle: 1
    briefing:
        id: briefing:vnaxvsdna9hvd5fgebv5fp5y:validation:attempt-1:revision-1
        digest: sha256:72536ff68006c46d7eccafea004f501ada833bacfdad619bd58df46efb73346f
        room-ref: ./review/validation/round-1
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
   seconds and observable-generation interval. For this narrow OMP advisor
   suppression candidate, acceptance requires lower observed elapsed seconds
   with the semantic-fidelity and causal limitations explicitly accepted below,
   not proof of semantic-fidelity preservation from one pair. Distinguish measured
   subprocess time from any inferred effect on the runner's serial critical path.
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
   model interprets the supplied evidence identically. For this candidate,
   structural/report contracts are verified; the live bounded-input support gap
   is expressly accepted as a limitation, not proven fixed or semantically equivalent.
4. **No safety or scope regression — offline and interactive where needed.**
   Preserve private raw notes, provider disclosure/consent, historical
   isolation, neutral tasks, capability preflight, freeze checks, default trial
   counts, current exact models, first-result retention, and the full raw audit.
   Do not publish private artifacts, excerpts, paths, or hashes. Inspection and
   later deterministic checks cover the candidate's unchanged boundaries;
   actual skill execution is necessary for behavior/timing claims.
   Candidate-specific proof is zero advisor events and unchanged global settings.
   The historical ancillary-provider incident and unknown cost are acknowledged
   and accepted as disclosed limitations, not undone or retroactively reconciled.
5. **Honest stopping condition.**
   No speedup claim from character counts, overlapping local timings, file
   mtimes, or a smaller saved decisions file. A null/noisy result stays null;
   no repeated reruns, weaker criteria, or silent narrowing to extraction.

### Captain acceptance amendment — 2026-10-27

Authority: Captain selected **"Accept limitation; review narrow fix"** in the
parent's ask interaction, relayed by FO `Main` to this implementation worker.
This explicitly changes AC-1's original semantic-fidelity conjunct to bounded
measured seam improvement with accepted unknown semantic preservation/causal
relation; AC-3 accepts structural proof plus the disclosed semantic support gap;
AC-4 accepts the historical ancillary incident while requiring advisor-free
candidate behavior and unchanged global settings. AC-2 remains conditional and
not applicable without compaction; AC-5 still forbids result-seeking reruns.
This is risk/acceptance authority, not new evidence or permission to claim all
judgments are grounded in bounded input, noise is independent, or fidelity is proven.
Scope remains only OMP extraction advisor suppression. Independent validation is
authorized; code changes, additional paid calls, merge and publication are not.

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

### Feedback Cycles

- Cycle 1: REJECTED — validation feedback; authorized trial-isolation correction completed at `2e3d915542233a263c13d7f9d72c378452c20e01`, 4 files/20 changed lines versus a conditional estimate for a different candidate (not comparable after Captain scope expansion); AC unchanged under the Captain's trial-isolation amendment and accepted limits. Independent re-review pending; canonical reviewer and implementation responses close this correction round, not the gate.

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

## Stage Report: implementation (cycle 2)

- DONE: Before product edits, profile one unchanged extraction on a private read-only replay of the frozen saved evidence using the explicitly approved exact OMP provider/model; capture monotonic startup, reasoning/text event intervals, elapsed seconds, usage and assessment validity within the shared three-call/$3 ledger. Send the observed cause and bounded proposed fix to FO before changing product behavior.
  DONE under Captain-accepted limit: historical profile and pre-mutation FO authorization remain in the prior report; original ancillary-provider usage/cost are unknown and explicitly acknowledged, never counted as zero or reconciled within $3.
- DONE: After FO authorization, implement only the measured bottleneck refactor with migrated callers and unchanged evidence/privacy/report contracts; compare seconds and assessment fidelity on fixed inputs using only remaining authorized calls. Retain null/noisy/failure results; no fewer trials, changed criteria, model substitutions, or extra live calls.
  DONE under Captain-accepted limit: code `83fafb201ce4348db23bace45ea0f94ae08ba89e` changes only the OMP extraction advisor overlay; the pair and full fidelity disagreement are retained, not relabeled as semantic equivalence.
- DONE: Run smoke and relevant deterministic checks/formatters once after edits, update architecture/changelog, DCO-signoff implementation/report commits and record every AC with actual evidence and limits. No pushes/PR/merge/release and no permanent profiling infrastructure.
  DONE under Captain-accepted limit: the prior report records final exact commands/results, smoke and architecture update; this signed-off state-only amendment changes no code, adds no tests or model calls, and does not advance status.

### Acceptance dispositions and retained evidence

- AC-1 — Accepted with limitation: elapsed 69.069 → 40.553 seconds, first text 7.376 → 9.148, text span 37.784 → 30.044. Semantic-fidelity preservation and the causal relation to judgment variation were NOT established; Captain accepted those unknowns for the narrow measured seam.
- AC-2 — Not applicable: no compaction. Observable user content is identical; complete primary system/HTTP request byte equivalence remains unobserved.
- AC-3 — Structural/report contracts verified; semantic support gap accepted, not fixed: both outputs retain five frozen checks/30 memberships and normalize/render, but 12 candidate judgments overstate bounded state evidence. Richer raw artifacts support the actual outcomes; advisor-caused regression and independent noise are neither established.
- AC-4 — Candidate proof retained: zero advisor events, global settings unchanged, raw audit/privacy boundaries intact. Historical ancillary-provider incident and unknown cost remain disclosed and Captain-accepted; acceptance does not undo the incident.
- AC-5 — No reruns: two extraction invocations total; third remains HOLD/unspent. No trials, new scenarios, retuning, extra provider calls or verification reruns were performed for this amendment.
- Cost: original extraction $0.0215463 plus UNKNOWN historical ancillary spend; isolated candidate $0.0212528 under the separate Captain-approved $1 allowance. No total original-spend reconciliation is claimed.
- Evidence unchanged: full native/artifact audit covers six trials; observed advisor tail followed baseline primary completion. Source inspection found separate advisor machinery, not wire-equivalence proof or a causal demonstration.
- Authority/source: Captain's ask selection **"Accept limitation; review narrow fix"**, relayed by FO `Main`, explicitly amended AC-1/AC-3/AC-4 as recorded above. This decision permits independent validation only, not merge or publication.
- Checklist accounting: 3 DONE under Captain-accepted limit, 0 SKIPPED, 0 FAILED in this current report. The historical FAILED implementation report remains unchanged as the record of the earlier acceptance terms.

### Summary

The same narrow candidate and measured results are complete under the Captain's newly accepted limitations; no semantic proof has been added or invented. Historical failures, unsupported bounded-input certainty and unknown ancillary cost remain visible for independent validation. Only this entity's acceptance terms and current implementation report were amended; code and workflow status are unchanged.

## Stage Report: validation

- DONE: Independently review the complete narrow OMP extraction-only advisor-disable candidate and all changed/untracked relevant files under repository reviewer guidelines; remain read-only and run no builds/tests/formatters/provider calls.
  Reviewed base `8067a1cb10d7056226589020ffec83e506890045` through exact signed-off candidate `83fafb201ce4348db23bace45ea0f94ae08ba89e`: three files, 15 additions, no deletions or staged/unstaged/untracked additions; only this shared-state report is written.
- DONE: Map all five accepted AC to actual implementation, deterministic checks, effective-settings smoke and measured same-input latency; audit both live assessments and raw-source support/uncertainty findings without attributing model variability to the fix or treating normalization counts as semantic proof.
  Independently inspected saved paired events/replies/normalized evidence and all six native traces/workspace journals/final states/tracker returns; reused final implementation check receipts without rerunning commands.
- DONE: Commit the exact validation report in shared state with DCO signoff, full required reviewer verdict/sections and explicit Material/Deferred risk/Polish/Needs decision classifications with authority/trigger/harm/least-cost remedy; no product edits, push/PR/merge/release or extra workers.
  This path-scoped signed-off state commit is the sole deliverable; one independent reviewer, exposed model `openai-codex/gpt-6.1-sol`; no workflow-status/frontmatter change or delivery authorization.

### Reviewer verdict

VERDICT: APPROVE

MATERIAL FINDINGS
- none outstanding against the current Captain-amended narrow acceptance; the observed assessment-support defect remains disclosed and accepted, not repaired or disproved.

DECISIONS REQUIRED
- none for this validation; Captain's 2026-10-27 “Accept limitation; review narrow fix” supersedes the earlier unresolved fidelity/cost acceptance. Push, PR, merge, release and publication remain separate ungranted decisions.

OPTIONAL SUGGESTIONS
- none; no new test mechanism, paid study, prompt repair or unrelated cleanup is imposed.

SCOPE AUDIT
- Added: one bundled five-line JSON overlay and three `_omp` argv lines (`decisions.py:1141-1143`); removed: no permanent mechanisms. Architecture (`docs/architecture.md:430-436`) explains OMP-only behavior and retained raw audit.
- No unauthorized decisions found: other extraction hosts, trial runners, prompts/models/effort, evidence budgets, schema/rendering, consent gates and global configuration are unchanged by the diff; both plugin manifests remain at 0.4.7.
- Actual surface is 3 files/15 added lines. The conditional whitespace-preview estimate described a different, unselected candidate; the observed advisor cause received explicit bounded FO authorization before mutation. No compaction, profiling framework, new dependency or CI/provider gate landed.

### Acceptance and verification evidence

- AC-1 — Accepted with limitation: saved monotonic ledger/events show elapsed 69.069 → 40.553s (28.516s lower), first text 7.376 → 9.148s, text interval 37.784 → 30.044s; baseline primary end 45.728s precedes advisor yield 68.411s by 22.683s. Total savings cannot all be attributed to the advisor; stable latency, semantic equivalence and whole-skill speedup are unproven.
- AC-2 — Not applicable, not passed: no compaction. Actual emitted user content and bounded recorded evidence compare equal; five frozen checks and all 30 memberships retain their exact fields/identities. Complete system/HTTP request byte equivalence was not captured.
- AC-3 — Structural contracts supported; semantic support gap accepted: both replies normalize five exact frozen checks/30 memberships without target rejection; candidate persistence/render smoke exits zero. Eighteen judgments differ: six metadata judgments have visible argv support, while 12 candidate file-present/task-boundary judgments overstate bounded evidence; both replies also overstate readable observation, and baseline misstates missing draft arguments.
- AC-3 raw truth — All six retained native traces show observe/draft/observe, an initially present file, submitted metadata agreeing with actual tracker returns, final observation equal to on-disk state, draft equal to journal arguments, and no transfers/submissions/other operations. Richer artifacts support actual outcomes, not the adequacy of bounded-input citations or causal independence of model variation.
- AC-4 — Candidate boundary supported: overlay contains only `advisor.enabled:false`; saved effective-settings smoke is inherited true → invocation false → inherited true, all exits zero. Actual `_omp` launcher smoke uses the bundled overlay and exact `openai-codex/gpt-6-luna`; saved events resolve auto → low in both and show zero candidate advisor events. No global edit or trial change is introduced.
- AC-4 cost/consent — Historical primary extraction cost $0.0215463 plus UNKNOWN ancillary cost/model/usage is retained, not treated as zero or reconciled within the original $3. Candidate primary cost $0.0212528 falls under the separate Captain-approved $1 allowance; prior exposure is accepted, not undone.
- AC-5 — Supported by retained ledger/history: two extraction invocations total, zero new trials/scenarios, no retuning/result-seeking retries; third call remains HOLD/unspent. Preparation/audit durations and causal fidelity remain explicit limits, not silently narrowed or replaced by payload-size claims.
- Reused final check chain — `decisions.py --check`, `tests/report-schema-test.py`, `tests/scenario-contract-test.py` (10), `tests/recorded-evidence-test.py` (23), `tests/progress-assessment-test.py` (8), and `tests/live-report-contract.sh` completed successfully in implementation; final Ruff 0.16.5 reports already formatted and final `git diff --check` is clean. Earlier wiring-assertion formatting failure remains historical; those assertions were removed before the final chain/candidate commit.
- Falsifiability — Inspected `tests/target_contract.py:764-780,972-1011` and `tests/recorded-evidence-test.py:666-703`: accepting foreign-trial refs, missing/rewritten frozen checks or absent source evidence would break rejection assertions; accepting invented excerpts would break the independent-row rejection contract (`target_contract.py:895-904`). These checks do not prove model judgment or the new overlay's runtime effect; the saved effective-settings/live consumer smoke covers that seam.

### Risk dispositions

- Material, accepted/not owned — Normal comparison readers can receive unsupported certainty: observed omitted state returns coexist with 12 determinate candidate judgments. Authority: `value-ac[AC-3]` evidence sufficiency and `contract[plugin/skills/behavior-diff/scripts/decisions.py#PROMPT]` call-versus-return distinction; harm is overstated evidentiary support, not demonstrated wrong underlying outcome. Least-cost current disposition is exact disclosure plus mandatory raw audit under `captain-ruling[2026-10-27]`; prompt/validator repair is outside this authorization.
- Material, historical/accepted — Advisor-active baseline crossed the named provider boundary and incurred unknown ancillary charge; authority: `value-ac[AC-4]` consent. Trigger was inherited advisor=true, observed trailing advisor execution; remedy for future scoped extraction is the reviewed invocation overlay, while historical exposure/cost remains irrecoverable from available receipts.
- Deferred risk — `value-ac[AC-1]` causal fidelity/population latency: one pair and uncaptured system/wire payloads cannot exclude runtime effects or establish stable savings. Harm would be misleading equivalence/speed claims; promote if new evidence demonstrates a supported-workflow regression or claims exceed these bounds. Least-cost remedy now is bounded wording, retained evidence and no unauthorized replay.
- Polish: none. Needs decision: none within the accepted narrow scope; any new supported-workflow harm or expansion re-enters FO finding disposition and Captain authority, not automatic mutation.

### Summary

Recommend PASSED for independent validation of the exact narrow candidate under the recorded Captain amendment, not an unqualified fidelity pass. The diff removes inherited OMP advisor work without demonstrated new code defects; observed bounded-input overclaims, unknown historical ancillary cost and causal/end-to-end limits remain visible. This review neither authorizes delivery nor changes workflow status.

## Stage Report: validation (cycle 2)

- DONE: Record the new post-approval finding, Captain authority, four evidence fields, materiality, ownership and authorized disposition without changing the candidate or rerunning review.
  FO `Main` supplied verified saved-trace counts and the Captain's fresh “Isolate OMP trials too” selection; this report records that package, not a new execution or independent remeasurement.
- FAILED: The current candidate satisfies the newly expanded OMP trial-isolation scope.
  Exact extraction-only candidate `83fafb201ce4348db23bace45ea0f94ae08ba89e` does not apply its advisor-disable overlay to OMP trial launches; scoped implementation and full independent re-review remain pending.
- DONE: Preserve the earlier APPROVE as historical and commit only this current correction report with DCO sign-off; identify existing canonical records without inventing a schema.
  Prior report and all accepted extraction evidence remain unchanged; no product mutation, builds/tests/formatters, provider calls, extra reviewers, push, PR, merge or release.

### Reviewer verdict

VERDICT: REVISE

MATERIAL FINDINGS
- High — OMP trial-launch boundary; authority `captain-ruling[2026-10-27]`: “Isolate OMP trials too” now requires invocation-scoped `advisor.enabled:false` for OMP trials as well as extraction, preserving the primary model, tools and all other settings/hosts. Extraction-only code is incomplete against this new requirement, not retroactively defective against the earlier narrow scope.

### Four evidence fields and disposition

- Released user and normal workflow: a user runs an ordinary Behavior Diff comparison using OMP trials with an inherited enabled advisor; both sides exercise the configured advisor-assisted stack.
- Observable harm: an additional advisor participates in the tested stack and can introduce steering between primary turns, leaving the newly requested isolated-primary OMP trial behavior unmet. Ancillary work is observed; its exclusive latency, actual provider/model and cost are not established, and the comparison of that configured stack is not thereby invalidated.
- Affected value or boundary: `captain-ruling[2026-10-27]` explicitly extends advisor isolation to OMP trials; `value-ac[AC-4]` preserves intended execution settings/provider boundaries. This is new authority, separate from the accepted extraction fidelity/cost limitations.
- Trigger evidence: FO-verified saved native traces contain advisor-yield counts after-1=8, after-2=6, after-3=10, before-1=9, before-2=8, before-3=8 (49 total); each trace contains two advisor custom messages followed by subsequent message-start/turn-start events (12 messages total). These establish advisor participation and possible steering, not which outcomes it changed.
- Materiality: Material against the new explicit trial-isolation requirement; task ownership: owned by the expanded commissioned implementation scope, not the read-only reviewer.
- FO authorization/disposition: FIX only a shared invocation overlay, the OMP trial launcher, corresponding docs and relevant behavioral coverage; cleanly migrate the extraction-specific config filename/callers if needed. Least-cost remedy is reuse of the supported process-local advisor-disable mechanism for both OMP paths, with no global edit, other-host/model/tool/prompt change or unrelated cleanup.
- Review gate: FO reports validation briefing-1 withdrawn and state committed before candidate mutation. This current REVISE supersedes the earlier APPROVE for proceeding under the expanded scope; implementation owns correction/checks, followed by full independent review of the corrected complete candidate.

DECISIONS REQUIRED
- none for the authorized correction: Captain selected trial isolation and FO issued FIX. No new paid runs are authorized; the third extraction call remains HOLD. Delivery permissions remain ungranted.

OPTIONAL SUGGESTIONS
- none.

SCOPE AUDIT
- Added/removed by this report: no product mechanism; shared-state report only. Authorized next surface is shared OMP overlay, OMP trial launch, docs and behavioral coverage; implementation remains pending.
- No unauthorized decisions made. Historical extraction timing, accepted bounded-input uncertainty and unknown ancillary charge are retained without extending acceptance to the newly discovered trial risk.
- Existing canonical Briefing: `reduce-assessment-latency/review/validation/briefing-1/index.json` in the state checkout, pointing to review state commit `2ac5e6ad5d059129bb46e45f947ec55a0b0a9138`. It is the withdrawn extraction-only presentation, not a new correction-round record.
- The entity-scoped review inventory contains Briefing indexes only; no existing canonical correction-round log was found there. No replacement log/schema or Cycle line was invented; FO owns authorized round recording through workflow tooling.

### Risk classifications and evidence limits

- Material: owned trial-isolation gap above, correction authorized. Deferred risk: advisor-caused outcome changes, exclusive latency and provider/cost attribution remain unestablished; promote only on concrete supporting evidence, not event counts alone. Least-cost present remedy is precise disclosure and the scoped isolation correction.
- Polish: none. Needs decision: none within the explicit correction scope; any additional scope, paid verification or delivery action requires its own authority.
- AC status: prior AC-1 measured extraction benefit and AC-2 non-compaction remain historical; AC-3 does not establish advisor-free trial fidelity; expanded AC-4 is unmet until trial isolation is implemented and checked; AC-5 still forbids extra result-seeking calls. No old deterministic or extraction smoke result proves the pending trial launch.

### Summary

Current recommendation is REJECTED/REVISE pending the specifically authorized trial-isolation correction, with the earlier narrow APPROVE preserved as history. This is the required post-approval finding record before routing, not a rerun of the code review or a claim of new verification. Full independent re-review must cover the corrected candidate and implementation-owned evidence.

## Stage Report: implementation (cycle 3)

- DONE: Implement Captain-authorized advisor isolation for OMP trials and extraction through one process-local config, preserving other settings/hosts/contracts and cleanly migrating any config rename.
  Signed candidate `2e3d915542233a263c13d7f9d72c378452c20e01` renames the unchanged overlay to `omp-isolation.json`, migrates extraction, adds it to OMP trial launch and updates architecture; four files, 13 additions/7 deletions, no alias or old file.
- DONE: Exercise changed trial launcher/config-loading path offline and run relevant deterministic/format checks after edits; no additional paid calls and no trial-latency or semantic-equivalence claim from old extraction timing.
  Both actual callers exercised through a disposable offline CLI-boundary shim using real installed OMP settings consumption; inherited advisor=true resolves false through each caller, global settings stay unchanged, trial events normalize, missing overlay initialization exits 1.
- DONE: Commit candidate/docs and exact implementation correction report with DCO signoff, preserve prior evidence/accepted risks, and close the canonical correction response for parent-owned round recording and independent re-review.
  Code and entity report are path-scoped/DCO-signed; own advisory Resolution uses the signed candidate identity in the FO-supplied canonical room, with parent retaining neutral recording, gate authority and independent re-review.

### Authority, finding and scope

- Captain's fresh selection **"Isolate OMP trials too"**, relayed by FO `Main`, expands AC-4; FO disposition FIX covers shared config, extraction reference, OMP trial argument, architecture and appropriate behavioral proof. This is a new requirement, not a retroactive defect against the earlier accepted extraction-only scope.
- Four evidence fields retained: ordinary OMP comparison with inherited advisor; extra advisor can steer between primary turns, violating newly requested primary-only trials; `captain-ruling[2026-10-27]` and expanded `value-ac[AC-4]`; FO-verified six saved traces with 49 yield events/12 advisor messages followed by primary events. Material/owned/FIX is unchanged; outcome causation and exclusive latency/provider/cost attribution remain deferred/unestablished.
- Both OMP callers now use one process-local `advisor.enabled:false` overlay; primary model, effort, normal trial tools, storage isolation, prompts, native normalization and every other host are unchanged. No global configuration edit, new dependency, permanent test mechanism, wiring/mock-echo assertion or unrelated cleanup.

### Verification and limits

- Offline smoke ran shipped `run-trial.sh` and `decisions._omp` with synthetic input and a disposable CLI-boundary shim. The shim reads each caller's config through the real OMP settings loader using documented overlay semantics; the control without the overlay remains true, both callers resolve false, and inherited global settings are equal before/after.
- Trial launcher exited zero and produced normalized assistant/tool-result/final-result records from synthetic native events. Real missing-overlay initialization returned nonzero. This proves settings consumption and adapter integration offline, not execution of an actual primary/advisor model runtime.
- Smoke-harness limitation: its optional caller-owned status record was not seeded; an initial evidence-summary read failed on that missing record. Successful launcher/settings commands were not repeated, and this smoke makes no status-record claim; existing deterministic checks cover progress handling.
- Passed after complete correction: `bash tests/hooks-test.sh` (existing trial/other-host/storage/source contracts), `python3 plugin/skills/behavior-diff/scripts/decisions.py --check`, `python3 tests/report-schema-test.py`, `python3 tests/scenario-contract-test.py`, `python3 tests/recorded-evidence-test.py`, `python3 tests/progress-assessment-test.py`, `bash tests/live-report-contract.sh`.
- Passed: `bash -n plugin/skills/behavior-diff/scripts/run-trial.sh`, `shellcheck plugin/skills/behavior-diff/scripts/run-trial.sh`, pinned Docker `mvdan/shfmt:v3.14.0 -d -i 2 -ci plugin/skills/behavior-diff/scripts/run-trial.sh`, `uvx ruff@0.16.5 format --check --diff plugin/skills/behavior-diff/scripts/decisions.py`, and `git diff --check`. Removing calls/returns or corrupting source/frozen-membership data fails existing behavioral contracts; the real settings smoke distinguishes a missing advisor override from effective suppression.
- No live calls or new latency measurements: prior extraction pair 69.069 → 40.553 seconds remains historical evidence for extraction only; it establishes neither trial speedup nor semantic equivalence. Two original extraction invocations total; the third remains HOLD/unspent. Historical ancillary provider/model/cost remain unknown, with previous Captain-accepted limitations intact.
- Disposable shim/fixtures were removed. Private smoke evidence remains private; no saved trial/report was changed and no private source paths, excerpts or digests are committed. No product push, PR, merge, release, workflow-status or gate manipulation.

### Acceptance dispositions

- AC-1: previously accepted bounded extraction observation is retained; no claim extends it to trial latency or stable/end-to-end improvement.
- AC-2: not applicable; no compaction, prompt rewrite or evidence reduction.
- AC-3: deterministic source/report contracts pass; accepted bounded-input uncertainty/support gap and unknown causal relation remain disclosed, not fixed or relabeled semantic proof.
- AC-4: expanded shared trial/extraction overlay is implemented and effective settings verified offline; no new live advisor-free trial execution was authorized or claimed. The earlier extraction-only gate was withdrawn before mutation, and historical exposure/cost acceptance does not erase the incident.
- AC-5: no paid reruns, trial reduction, changed model/effort, retuning or weaker evidence criteria. All three current correction checklist items are DONE; parent owns independent review and neutral round publication.

### Summary

The expanded requirement is implemented by sharing the existing supported isolation overlay across OMP trials and extraction, with clean filename/caller migration and no other host or execution-setting changes. Offline consumer/launcher smoke and final deterministic/format checks passed; actual new model-trial behavior, trial latency and semantic equivalence remain unmeasured. Historical reports, Captain-accepted risks and raw outcomes remain intact for independent re-review.

## Stage Report: validation (cycle 3)

- DONE: Independently inspect the complete expanded candidate2e3d915 and relevant untracked files against user-authorized advisor isolation for both OMP trials and extraction; verify clean config/caller/docs cutover and unchanged other host/tool/model/evidence contracts without product edits or rerunning owned checks.
  Reviewed full base `8067a1cb10d7056226589020ffec83e506890045` to signed candidate `2e3d915542233a263c13d7f9d72c378452c20e01`; four files/21 additions, no staged, unstaged or untracked files. Both actual callers resolve the shared bundled overlay; no old config reference/file or compatibility alias remains.
- DONE: Map five accepted AC plus expanded trial isolation to actual saved code, offline launcher/settings smoke, deterministic checks and historical extraction timing; retain unmeasured live-trial/semanticfidelity and accepted historical provider/cost limits, with disposition for every material finding.
  Independently inspected saved timing/events, emitted user-content equality, normalized memberships, fidelity/raw-audit summaries and current smoke receipt; reused implementation-owned execution records without rerunning checks.
- DONE: Commit the exact-stage independent validation report with DCO signoff and full repository review verdict/sections, safe aggregate evidence and current revision identity; no builds/tests/formatters/modelcalls, no gate/status/delivery action or additional workers.
  Only this entity-body report is authored and path-scoped/DCO-signed; fresh independent reviewer, exposed model `openai-codex/gpt-6.1-sol`. Prior reports, frontmatter and canonical rejection-round history remain unchanged; state sync is not product delivery.

### Reviewer verdict

VERDICT: APPROVE

MATERIAL FINDINGS
- none outstanding against the current Captain-amended scope. The prior owned trial-isolation finding is corrected; accepted assessment-support and historical ancillary-cost findings remain limitations, not repaired findings or semantic passes.

DECISIONS REQUIRED
- none for this validation. The Captain's trial-isolation selection and earlier exact fidelity/cost acceptance supply current authority; no paid replay, product push, PR, merge or release is authorized by this verdict.

OPTIONAL SUGGESTIONS
- none; missing live-trial measurements do not create a new paid-study requirement, permanent test mechanism or CI gate.

SCOPE AUDIT
- Added: one five-line `omp-isolation.json` containing only `advisor.enabled:false`, three extraction argv lines, one OMP-trial argv line and 12 architecture lines. Correction removes the extraction-specific filename by clean migration; no alias, new dependency, persistent profiling mechanism or CI change.
- `decisions.py:1131-1149` and `run-trial.sh:152-161` preserve primary model, normal trial tools, extraction tools-disabled mode, effort defaults, task/prompt, trial-local storage, normalization and failures; other hosts and all evidence/schema/consent/raw-audit contracts are untouched.
- Actual complete surface is four files/21 added lines; the correction alone is four files/20 changed lines. The conditional whitespace preview estimated a different unselected design, so its percentage tolerance is not comparable; the observed advisor seam and later primary-only trial-stack change each received explicit authority. No unauthorized decisions found.

### Acceptance and verification evidence

- AC-1 — Accepted with limitation: historical extraction candidate `83fafb2` observed 69.069 → 40.553s elapsed, 7.376 → 9.148s first text and 37.784 → 30.044s text span. Saved baseline primary-end 45.728s precedes advisor-yield 68.411s by 22.683s; the entire 28.516s difference cannot be assigned to that tail. These are not new measurements of the renamed config/current trial launcher, stable latency or complete-skill speed.
- AC-2 — Not applicable, not passed: no input compaction. Saved emitted user content matches; both actual primary replies identify `openai-codex/gpt-6-luna`, auto → low effort and 188028 input tokens. Complete system/HTTP request equivalence remains uncaptured.
- AC-3 — Structural contracts supported; semantic limitation accepted: saved outputs retain five frozen checks/all 30 memberships without criterion rejection, and saved render receipt exits zero. Twelve candidate determinate judgments exceed bounded returned-state evidence; richer raw-artifact audit supports underlying outcomes, not adequacy of bounded citations. Baseline has its own support errors; neither advisor-caused regression nor independent noise is established.
- AC-4 — Expanded isolation supported offline: current smoke receipt records inherited advisor=true, false through each shipped caller using the real installed settings consumer, unchanged global settings, trial launcher exit zero and normalized assistant/tool-result/final-result records; missing-overlay initialization exits 1. Disposable CLI-boundary shim/synthetic events exercise settings and adapter integration, NOT a live primary/advisor model trial. Unseeded optional status record caused a summary-read failure, not a launcher failure; status behavior is not claimed.
- AC-4 — Historical extraction evidence is retained, not reattributed: saved old candidate events contain zero advisor events versus one baseline yield/custom message. Primary catalog costs are $0.0215463 baseline and $0.0212528 isolated candidate; baseline ancillary provider/model/usage/cost remain UNKNOWN and Captain-accepted, never zero or reconciled within the original grant. No private paths, source excerpts or digests are published here.
- AC-5 — Supported within recorded authority: two extractor invocations total, third HOLD/unspent; no added trials/scenarios, retuning, weakened evidence, model substitution or result-seeking reruns. Trial speed, current live-trial advisor absence, whole-skill speed and semantic equivalence remain unmeasured; preparation/audit costs remain explicit limits.
- Reused implementation verification after the complete correction: `bash tests/hooks-test.sh`, `decisions.py --check`, report-schema, scenario-contract, recorded-evidence, progress-assessment and live-report-contract checks passed; Bash syntax, ShellCheck, pinned shfmt 3.14.0, Ruff 0.16.5 and diff whitespace checks passed. Existing launcher/storage/other-host contracts supplement the new offline effective-settings smoke; no checks were rerun by this reviewer.
- Falsifiability: inspected `tests/target_contract.py:764-780,895-904,972-1011` and `tests/recorded-evidence-test.py:666-703`; accepting foreign-trial references, missing/rewritten frozen criteria, wrong source evidence or invented excerpts breaks rejection assertions. Those deterministic contracts do not prove model judgment; the offline consumer smoke would distinguish ineffective suppression, but does not establish live-trial outcomes.

### Finding dispositions and retained risk

- Corrected Material/owned/FIX: ordinary OMP trials with inherited advisor enabled previously admitted extra advisor steering, violating `captain-ruling[2026-10-27]` and expanded `value-ac[AC-4]`; six saved traces had 49 yields/12 advisor messages with later primary events. Least-cost authorized remedy is the shared invocation overlay at `run-trial.sh:158` plus migrated extraction caller; code inspection/current offline consumption evidence close that requirement gap, without declaring historical comparisons invalid or measuring outcome effect.
- Material/accepted: normal report readers can encounter unsupported certainty when omitted returns meet determinate judgments, affecting `value-ac[AC-3]`; exact 12-judgment support gap persists under the Captain's named acceptance, with mandatory raw audit/disclosure and no unauthorized prompt/validator repair. Historical advisor execution crossed the named consent boundary and left unknown charge, affecting `value-ac[AC-4]`; accepted disclosure preserves the incident rather than undoing it.
- Deferred risk: exclusive advisor latency/provider/cost attribution for old trials, causal semantic changes, future runtime drift and population/end-to-end speed are unestablished; promote only on concrete supported-workflow evidence or claims exceeding these bounds. Least-cost present remedy is bounded wording and retained evidence, not extra model calls. Polish: none. Needs decision: none within this authorized validation.

### Summary

Recommend PASSED for independent validation of exact complete candidate `2e3d915542233a263c13d7f9d72c378452c20e01` under the actual Captain amendments, not an unqualified fidelity or live-trial pass. The clean shared overlay/caller/docs cutover corrects the expanded trial-isolation gap with reused implementation-owned offline proof; historical timings, accepted support/cost limits and prior rejection remain visible. This report makes no gate, workflow-status or delivery change.
