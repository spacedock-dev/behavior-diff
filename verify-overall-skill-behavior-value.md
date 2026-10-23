---
title: Verify the value of overall-skill Before/After behavior comparison
status: implementation
source: Captain-requested follow-up from case-01-auto-download-audio.md
started: 2026-10-23T14:17:49Z
completed:
verdict:
score:
worktree: .worktrees/spacedock-ensign-verify-overall-skill-behavior-value
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
        - id: gate:pyjt2hqwf2ncmfgdr9xhxk29:ideation
          stage: ideation
          attempts:
            - id: gate-attempt:pyjt2hqwf2ncmfgdr9xhxk29-ideation-1
              briefing:
                id: briefing:pyjt2hqwf2ncmfgdr9xhxk29:ideation:attempt-1:revision-1
                digest: sha256:a00de97629ad05f6f151f617fa33136e73902c5c9564248432d881a2458b6965
                room-ref: ./verify-overall-skill-behavior-value/review/ideation/briefing-1
              resolution:
                type: Resolution
                id: resolution:spacedock:pyjt2hqwf2ncmfgdr9xhxk29:ideation:1
                briefing: briefing:pyjt2hqwf2ncmfgdr9xhxk29:ideation:attempt-1:revision-1
                by: person:captain
                at: "2026-10-23T14:26:38.933452Z"
                decision: approve
                reason: Captain approved local saved-evidence audit and one interactive reader evaluation. Safe findings in task state; private evidence stays local. No product code, PR, live model calls, or external disclosure. Native omp execution remains task-authorized.
              application:
                target-stage: implementation
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

Captain requested this hypothesis as a backlog task and subsequently approved
ideation. Only the design is authorized, not product implementation, live model
runs, or disclosure of private sources. Native omp execution is authorized for
this task only; it does not establish general runtime-adapter support.
Keep accepted verification evidence in its existing private home and reference
it here rather than copying source material or reports into tracked state.
Related task: `refine-summary-page-signal`; summary clarity and added scenario
value are separate questions, with no assumed execution dependency.

### Feedback Cycles

Initial ideation prepared on 2026-10-23; Captain review remains pending.

## Out of scope

Exhaustive skill coverage, a full simulator, repeated generator tuning, a new
product feature before validation, proven time-saving claims, or calling the
source case a confirmed demonstration of additional product value.

## Ideation proposal: audit saved evidence before adding a scenario

### Recommendation and actual question

Recommend a local, saved-evidence audit followed by one reader session, not a new
generator run or product feature. The user needs to decide whether the changed
skill is suitable for its next normal use: what required work still completes,
where legitimate human intervention remains, and what still needs verification.
An overall-goal scenario is one possible way to obtain that evidence, not the
outcome itself. A successful local segment cannot guarantee the next real run.

Kent's brain recommends: reuse saved evidence and test one concrete reader
decision before authorizing additional trials (confidence: high).
Why: this is the smallest reversible step that can reject added value without
new model cost, external effects, or a larger simulator.

Separate three claims throughout: what each instruction version requires; what
the recorded agents actually did; and whether those observations help the reader.
Neither a broader task description nor a longer report establishes the last two.

### Evidence inspected and current limits

References below are repository-root coordinates, not attachments. `memo/` and
the sibling strategy checkout require authorized local access; they are not
portable public evidence. Follow their existing archive links privately.

- E1: `../spacedock-strategy/projects/behavior-diff/case-01-auto-download-audio.md`,
  sections “The test question”, “Product value check”, “Results”, and “Limits”.
  This establishes the open user question, not demonstrated extra product value.
- E2: `../spacedock-strategy/projects/behavior-diff/index.md`, assumptions and
  current state; and `memo/cases/podcast/2026-10-21-project-goal-scenario-experiment-handoff.md`,
  current experiment section. The later correction explicitly prioritizes actual
  execution evidence over scenario novelty and preserves the existing workflow.
- E3: `memo/cases/podcast/2026-10-22-project-goal-preparation-result.md`.
  The first overall-goal preparation narrowed the intended scope. Its preparation
  result is not an executed whole-workflow comparison; later adaptations must not
  be relabeled as that untouched design.
- E4: `memo/cases/podcast/2026-10-22-download-metadata-run-result.md`.
  The saved standard comparison has assessment and environment limitations.
  Completion of the host process does not establish requirement completion.
- E5: `memo/cases/podcast/2026-10-22-evidence-prototype-experiment.md` and its linked
  external `report-prototype.md` and `private/coverage-spec.md`, read locally.
  These provide an existing manual evidence artifact and explicit scope limits,
  not a verified automatic product or a recorded reader-value outcome.
- E6: `plugin/skills/behavior-diff/references/scenario-and-test-data.md`,
  preparation, preflight, freeze, assessment, and limits; `docs/architecture.md`,
  scenario construction and shared-data delivery. These define the existing
  mechanism and prevent claiming unsupported multi-file or real-service coverage.

The saved records describe distinct runs with different scopes/settings. They
cannot be pooled into one baseline or stitched into a continuous successful run.
The identity of the final demo described in E1 is not reconciled to the different
saved run described in E2. Do not silently pick either as the canonical baseline.
This ideation inspected records and the existing prototype, not every raw trial;
their behavioral findings remain attributed, not independently reverified here.
No reader response demonstrating incremental value was established in these
inspected artifacts. AC-1 and AC-2 therefore remain open verification outcomes.

### Bounded overall-goal task and baseline

Proposed representative boundary: one ordinary work item, beginning at the normal
post-input processing entry in the historical workflow, before the changed handoff,
and ending at the first required final human-review gate. Include intermediate
processing, artifact checks, downstream preparation, state recording, and the
review boundary where required by the two source versions. Do not start with the
changed operation or a required intermediate artifact already completed.

Illustrative neutral request, not a frozen trial prompt:
“Continue this work item from its recorded state using the workflow, update its
records, and tell me what remains.”
The source-only preparer must establish the exact entry, mandatory intermediate
steps, and legal stop from both versions before execution. This is a bounded
overall-goal path, not the entire skill lifecycle or every branch.

The change-focused baseline A is the original narrower handoff comparison,
including all evidence it already exposes beyond the edited step. Freeze its
actual task and coverage from a reconciled saved run, not from its name.
The candidate G is evidence for the larger normal path above. Existing
download-to-review artifacts are reusable checkpoints, not proof that G has run.
Missing earlier steps or required terminal work stay explicitly unverified.

For the user's decision baseline, first record what a diff review and the existing
quick check already establish. Then compare A with A plus relevant overall-goal
evidence. This distinguishes value over the narrow scenario from value over what
the user already knows. Do not count known success a second time.

### Smallest falsifiable comparison and simpler alternative

1. Audit only the saved case records needed for this question. Privately freeze
   each run's identity, source versions and companion-file mapping, task, data,
   host, exact model, reasoning settings, tool semantics, report origin, and
   available raw actions/returns/artifacts. Unknown fields remain unknown.
2. Build one private evidence-gap table using the existing requirements:
   requirement/source; Before/After reached, missed, or unknown; evidence pointer;
   supported, contradicted, or insufficient; remaining verification. Preserve
   minority outcomes and separate tool failure from skill behavior.
3. If saved evidence answers the required question, use it unchanged. If the
   matched A/G comparison is unavailable, label the scenario-method hypothesis
   inconclusive. A separate reader assessment of the available evidence can
   still proceed, but cannot establish that overall-goal generation is superior.
4. Ask the reader the same questions before and after the added evidence. Keep
   the original reports unchanged, with the same access to source evidence in
   both conditions. Use private notes and existing artifacts, not a new UI or
   rewritten summary that confounds scenario scope with presentation.
5. Only if an important question still lacks execution evidence, propose one
   bounded gap comparison for separate approval. Do not rerun merely to change
   a null result, repair the first design's reputation, or increase check counts.

Simpler alternative: review the diff and use a plain local evidence checklist on
the existing narrow run, retaining necessary manual verification. This avoids
new scenario preparation. Prefer it if it answers the same decision question at
lower preparation and reading cost. A new plain-agent simulation is not required
to test this alternative and would itself need model/content approval.

### Reader evaluation and frozen result rules

Freeze these rules before the reader session or any new evidence collection.
This is an informed single-owner case study, not a blind benchmark: prior
familiarity is disclosed, and no general accuracy or time-saving claim follows.
Do not use the unrelated five-case summary quiz to answer this question.

Before revealing additional evidence, record the reader's accept/fix/hold
decision, the reason, required steps believed preserved, unresolved questions,
and specific checks the reader would still perform. Afterward ask:

- What changed, what stayed required, and what was actually observed?
- Which cited observation changes or supports your decision, and why?
- Which particular verification step can now be omitted or narrowed, if any?
- What remains unverified, and what would still block the next real use?

Score answers against source requirements plus auditable recorded evidence,
not a facilitator's preferred outcome. Track factual fidelity, scope awareness,
remaining verification, preparation burden, and reading effort separately.
Confidence alone, extra words, more checks, and finding any bug are not success.

| Outcome | Predeclared condition |
| --- | --- |
| Supported for this case | Valid relevant evidence resolves at least one baseline uncertainty, and the reader correctly cites it to support/change a decision or remove/narrow one named verification step, without dropping a necessary safety check or claiming untested coverage. |
| Unsupported for this case | Comparable, sufficient evidence is available and understood, but it adds no decision-relevant understanding or justified reduction of verification beyond the baseline; or the simpler alternative gives the same benefit with less burden. |
| Inconclusive | Identity/settings are not comparable, a required step is unobserved, artifacts/tooling are insufficient, the reader cannot judge, or only presentation/familiarity differs. Name the missing prerequisite rather than forcing a verdict. |

An unchanged accept decision can still be supported by newly justified
preservation evidence. Identical Before/After behavior is not automatically
success or failure. A false assurance is a value failure when traceable to a
valid tested presentation; otherwise retain the validity problem as inconclusive.
No novel coverage is required to justify useful repeated verification, but
duplicate evidence cannot establish incremental scenario value by itself.

### Preserved semantics, controls, and consent

Keep the historical instructions and required references intact. The default
runner varies one instruction file; any multi-file assembly must retain an
explicit source mapping and disclose its tested scope. Do not claim that the
existing shared-data helper natively varies multiple files.

Within each comparison hold task, initial state, tools, clock, host/model/effort,
permissions, and capture method constant; only the instruction version changes.
Across A and G record the intended task/entry differences and hold shared
conditions constant. Unmatched archived settings permit descriptive reuse, not
a causal attribution to the broader scenario.

Preserve legitimate Before manual handoffs, safe fallback on unclear input,
artifact protection/verification, downstream requirements, and human review.
If continuing past a Before handoff is necessary, approve and freeze the same
conditional synthetic human response policy before trials. Never invent approval
after observing a stop. No real publication or external-service action is needed.
Checkpoint evidence never proves continuous execution across its missing links.

Any later historical preparation needs a fresh source-only context that cannot
see this evaluation or old outcomes. If isolation is unavailable, stop before
preparation. Validate required tool capabilities and read isolation locally under
the intended permissions before requesting live execution; do not build a full
simulator when existing adapters cannot support the boundary.

Current authorization covers ideation only. Reader participation and any next
stage need their own approval. Any live proposal must name exact host/models,
purpose, source/data disclosure, extraction calls, and monetary cap beforehand.
Planning ceiling for one approved gap comparison is the existing default three
Before plus three After trials and at most one extraction, with no automatic
retry; preparation calls, if needed, must be listed separately. This is not run
authorization or a dollar estimate. A second comparison exceeds this proposal.

### Surface, tolerance, dependencies, and acceptance mapping

Current surface: this task body and its Stage Report only, approximately 200
added lines with a 50-line tolerance. No product files, API, schema, CLI, report
navigation, tests, or changelog behavior change. No implementation PR is proposed.
The next approved step remains a private audit and one reader session; retain
only a safe aggregate outcome and references in task state. New UI work would
require separate design/preview approval and the existing saved-case workflow.

Dependencies: authorized local source/archive access, reconciled baseline
identity, readable actions/artifacts and matching source requirements, and a
reader willing to record the before/after decision. A fresh clone lacks private
archives; report that prerequisite, never silently replace them with synthetic
evidence. Related summary-clarity work is not a prerequisite.

No offline mechanism spike was needed for ideation: existing file reads, saved
reports and private notes suffice for the proposed audit/reader method. This does
not certify future adapter compatibility; exercise it only if a live gap study
is approved. No build, test, lint, formatter, model evaluation, or trial ran here.

- AC-1, offline then interactive: the reconciled evidence-gap table and reader
  comparison distinguish A from added overall-goal evidence under the rules
  above. External check: trace each claimed added observation to its raw artifact
  and confirm it was not already in A. Missing reach or a renamed narrow scenario
  falsifies a claimed coverage gain. E1-E6 justify the design, not its success.
- AC-2, interactive: retained before/after reader responses identify whether the
  added evidence improves a grounded decision or understanding. External check:
  audit the cited observation and any removed verification step against source
  requirements; unsupported confidence or no incremental benefit fails the
  support criterion. A negative or inconclusive outcome completes verification.

Captain decision needed: approve the saved-evidence audit and reader evaluation,
not a feature or live run. Keep baseline identity unresolved until its artifacts
are reconciled. No paid work is necessary to make this next decision.

## Stage Report: ideation

- DONE: Read the cited local auto-download-audio case and relevant existing evidence; define the user's actual question and a bounded representative overall-goal task versus the change-focused baseline, without asserting exhaustive coverage or exposing private content.
  Evidence: E1-E5, including the later experiment correction and existing private prototype; safe scope and evidence limits are recorded above, with no raw content copied.
- DONE: Recommend the smallest falsifiable comparison and simplest alternative, with frozen support/refutation/inconclusive criteria, reader evaluation, preserved semantics, non-goals, dependencies, proposed surface/size/tolerance and any required consent; reuse saved evidence before proposing live calls.
  Evidence: the proposal uses a saved-evidence audit plus one reader session, with explicit baseline validity and live-run approval boundaries.
- DONE: Record an ideation Stage Report mapping AC-1 and AC-2 to external evidence and remaining decisions. Exercise only safe offline uncertain mechanisms if needed; no paid model calls, product implementation, publishing or new report UI. Supported, unsupported and inconclusive results are valid; no positive-result requirement.
  Evidence: AC-1 maps to raw-artifact reach/contrast checks; AC-2 maps to reader responses and justified verification changes; neither outcome is claimed complete.
- SKIPPED: Offline mechanism exercise.
  No new execution mechanism is introduced; future adapter capability remains an explicit preflight dependency rather than an assumed proof.

### Summary

Recommended reusing existing execution evidence before generating an overall-goal
scenario; later local records already narrow what can honestly be claimed.
The design and falsifiable reader-value criteria are ready for Captain review,
while baseline reconciliation, reader evaluation, and any live work remain
separately gated. Only safe task state is committed; no product change or
external publication is part of this stage.
