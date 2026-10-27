---
title: Prototype the verification handoff journey
status: implementation
source: Captain request to create a dev-workflow prototype task after journey feedback
started: 2026-10-27T06:19:44Z
completed:
verdict:
score:
worktree:
issue:
linear:
pr:
mod-block:
id: yxy4v1m92t2daz68kmmykqqh
gates:
    version: 1
    records:
        - id: gate:yxy4v1m92t2daz68kmmykqqh:backlog
          stage: backlog
          attempts:
            - id: gate-attempt:yxy4v1m92t2daz68kmmykqqh-backlog-1
              briefing:
                id: briefing:yxy4v1m92t2daz68kmmykqqh:backlog:attempt-1:revision-1
                digest: sha256:8a1a3aca394669d7ee4004ec6816ba1fa445dcaec04f20a049057849a32460f2
                room-ref: ./prototype-verification-handoff/review/backlog/briefing-1
              resolution:
                type: Resolution
                id: resolution:spacedock:yxy4v1m92t2daz68kmmykqqh:backlog:1
                briefing: briefing:yxy4v1m92t2daz68kmmykqqh:backlog:attempt-1:revision-1
                by: person:captain
                at: "2026-10-27T04:58:37.931753Z"
                decision: approve
                reason: Captain explicitly requested dispatch yxy4v1m92t2daz68kmmykqqh again after committing the seed; accepts starting ideation, not an unknown implementation design, paid runs, PR, or merge.
              application:
                target-stage: ideation
                state: consumed
        - id: gate:yxy4v1m92t2daz68kmmykqqh:ideation
          stage: ideation
          attempts:
            - id: gate-attempt:yxy4v1m92t2daz68kmmykqqh-ideation-1
              briefing:
                id: briefing:yxy4v1m92t2daz68kmmykqqh:ideation:attempt-1:revision-1
                digest: sha256:ef7e6a29ab1e9fe99ad79f09881fe3f54bdc26d30e35e60a4584ef6951d52446
                room-ref: ./prototype-verification-handoff/review/ideation/briefing-1
              resolution:
                type: Resolution
                id: resolution:spacedock:yxy4v1m92t2daz68kmmykqqh:ideation:1
                briefing: briefing:yxy4v1m92t2daz68kmmykqqh:ideation:attempt-1:revision-1
                by: person:captain
                at: "2026-10-27T06:40:46.116104Z"
                decision: approve
                reason: 'Captain approved the presented ideation design: isolated repository-local conversational replay skill and Python helper, six-file scope around 490 changed lines with plus/minus 150 tolerance, private real-case evidence packet dependency, direct owner walkthrough, no production skill change, paid trials, code push, PR or merge.'
              application:
                target-stage: implementation
                state: consumed
---

Build an operable conversational prototype of handing post-change verification
to Behavior Diff. The user should understand the change, relevant evidence and
limits, then decide what to do, rather than direct every verification step.
This is a prototype implementation task, not another planning document or a
claim that autonomous verification is already delivered.

## Problem

Existing verification capabilities do not by themselves establish a low-effort
user experience. The user can still need to restate context, specify individual
tests, prompt continuation, or reconstruct findings from raw records. The
requested next deliverable is a prototype that makes these intervention points
observable. Journey direction has received positive feedback; implementation
and design choices still follow the workflow gates.

## Proposed approach

Start with one locally supplied workflow-change case and a conversational
surface; prefer existing host interaction and report components over a new UI.
Provide an actual walkthrough with three connected steps:

1. Handoff: accept the change and available discussion/documents. Propose the
   modification intent and verification goals for confirmation or correction.
   Offer bounded choices only where uncertain; permit none-of-the-above and
   free correction. Do not require the user to design tests from scratch.
2. Verification handoff: show the relevant plan and limits; ask only for missing
   information or decisions that require the user. Carry corrected goals into
   the subsequent result. Demonstrate this transition rather than only narrate it.
3. Decision: present findings, reasons and unverified requirements first, with
   accessible supporting evidence. Let the user decide to accept, revise or
   request further verification. Never perform merge or adoption automatically.

Reuse existing case evidence where appropriate, explicitly labeled as reused.
An evidence-backed replay is acceptable for this prototype; do not pretend it
is fresh execution, autonomous evidence generation or measured live latency.
The simplest alternative is a static storyboard, but it cannot exercise user
corrections or reveal actual takeover points, so it is insufficient alone.
Ideation must choose the smallest executable surface and present it for approval.

## Risk evidence

This request follows a reviewed journey and existing conditional capability
experiments; the question now concerns handoff effort, not proving all
verification capabilities from scratch. Use `intent mismatch` for behavior
that does not match a modification's intent, not `side effect` as a synonym.
Regression testing and simulation are candidate means, not the product goal.
Simulation does not establish real-service compatibility or complete coverage.
Known-answer replay cannot prove first-time intent inference accuracy.

Private source pointers, for local reading only:
- memo/private/2026-10-27-cl-discussion-pack.md
- memo/product/2026-10-26-behavior-review-product-testing-plan.md

These notes may lag later Captain direction: this task's handoff outcome is the
current requested scope. Obtain permitted evidence locally; do not copy private
runs, reports, transcripts, customer identifiers or personal paths into tracked
code or state. Use synthetic fixtures for committed demonstrations. Missing real
case evidence is a reported prerequisite, not permission to invent findings.

## Expected surface and tolerance

Ideation must identify the minimal runnable surface, changed files and size
estimate with tolerance before implementation. A standalone formal UI, new
orchestration platform and automatic remediation system are not assumed.
Report hierarchy changes must follow repository preview requirements.

## Acceptance criteria

Draft outcomes to refine at the ideation gate:

**AC-1 — A user can operate the full handoff-to-decision journey.**
Verified by: interactive walkthrough on the actual prototype, including a
correction of the proposed intent or verification goal and continuation to a
result that respects that correction. A static script or a correction ignored
by later steps fails this check.

**AC-2 — Findings remain evidence-bound and uncertainty is actionable.**
Verified by: exercise a supported result and a result with an unverified
requirement using permitted evidence. The user can locate the relevant support
and distinguish reused evidence from fresh execution. Treating missing evidence
as a pass, fabricating a run, or claiming whole-flow coverage from a slice fails.
No new model-backed run is implied by these prototype exercises.

**AC-3 — The prototype exposes whether verification work was handed off.**
Verified by: an interactive user walkthrough recorded outside tracked state,
comparing the user's usual need to arrange, chase and interpret verification
with actual intervention points in the prototype. Record each takeover, its
reason, necessary user decision versus avoidable agent work, and the user's
ability to decide from the result. Select the next experiment from the most
costly remaining takeover point. A negative or inconclusive value result is
valid; a positive claim based only on praise or the prototype's existence fails.
This evaluation is a Captain-dependent gate; do not invent user responses.

## Test plan

Exercise the actual surface through confirmation, correction, evidence viewing
and an evidence-gap path. Use deterministic synthetic fixtures for offline
checks and local permitted evidence for the user walkthrough. Tests must check
observable behavior, not instruction wording. Keep raw interaction records and
real evidence local; report only privacy-safe outcome summaries in state.
Separate prototype usability evidence from model capability, timing and complete
workflow validation. Fresh model trials, real external operations and private
data disclosure need their own applicable approval. No model calls in CI.

## Decisions and dependencies

- Captain requested task creation now and later execution through Spacedock.
  This does not authorize dispatch, an unknown design, paid runs, push, PR,
  merge or release. Start in backlog.
- Related task: `verify-overall-skill-behavior-value`
  (`pyjt2hqwf2ncmfgdr9xhxk29`). Its scenario-comparison scope is distinct.
  Reuse suitable existing artifacts, avoid overlapping edits, and coordinate
  shared surfaces before implementation; do not block automatically on its
  completion or supersede it without a Captain decision.
- Priority recommendation: High, because the next product discussion needs an
  operable prototype. No arbitrary numeric score or delivery date is assigned.
- Private evidence availability and user walkthrough are explicit dependencies.
  Select the local case and verify availability during ideation.

### Feedback Cycles

No review rounds yet.

## Out of scope

Formal product rename; broad capability research; comprehensive regression-suite
generation; live E2E runs; automatic fixes or merge; new permanent CI gates;
polished multi-case UI; proving simulation is faster or replaces all real E2E;
committing private evidence; changing the related task without approval.

## Ideation proposal: local conversational replay, not automatic verification

### Recommendation and decision needed

Recommend a repository-local maintainer skill with a small Python replay helper,
operated through the owner's existing conversation. It accepts the supplied
change/context and a locally prepared evidence packet, proposes goals with
explicit/inferred provenance, accepts free correction, and presents a result
bound to the confirmed goals. This is an executable, evidence-backed replay,
not a second runner, a static conversation script, or a shipped product feature.

🧠 Kent's brain recommends: approve the local conversational replay prototype
(confidence: medium).
Why: it exercises handing work off in the existing conversation with the smallest
external effect, while keeping missing evidence and owner decisions explicit.

The owner design gate must approve this surface and its replay limitation before
implementation. No design approval, implementation authorization, or usability
success is asserted by this report.

Alternatives considered:

1. A static storyboard is cheaper, but cannot carry an actual correction into
   a subsequent result; use only as illustration, not the deliverable.
2. A standalone Python terminal conversation could exercise deterministic edits
   without a host agent. It would require the owner to operate another surface
   and could offer only authored intent suggestions, rather than use the already
   supplied discussion naturally. It is the simplest executable alternative,
   not the recommended handoff experience.
3. Modify the existing Behavior Diff skill directly. Rejected for this prototype:
   its current Steps 2–3 freeze inputs and launch trials automatically, and its
   frozen purpose must not be rewritten after seeing outcomes. Adding replay and
   mutable conversational goals there broadens production behavior unnecessarily.

### Executable journey and correction boundary

The host-facing entry is an explicit load of the new maintainer skill's source
path, followed by the owner's ordinary handoff request; no installed-plugin
discovery, new user command vocabulary, model selection prompt, or new service
is required. Use the same source instructions and helper on both supported
hosts. OMP can load the explicit local path; this does not assert an upstream
Spacedock OMP runtime adapter.

1. Read only the change, discussion/documents, and case root explicitly supplied
   for this walkthrough. Do not search transcript stores or unrelated archives.
   Propose the modification intent, preserved requirements, and a bounded plan.
   Mark uncertain inferences; ask only about material uncertainty. Offer a
   recommendation, none-of-the-above, and free correction, not a test questionnaire.
2. Before revealing results, record the owner's confirmation or correction in a
   private session snapshot. The host handles meaning and evidence review; the
   helper handles revisions and result projection. Changing a goal replaces its
   exact text, invalidates its old evidence binding and confirmation, and clears
   the old decision. Unchanged goals retain their independent support. Replacing
   all goals invalidates all prior bindings.
3. The host reviews the supplied evidence against the corrected requirement.
   It may bind an observation only with a concrete local source coordinate and
   scope explanation; semantic equivalence is not inferred from matching words.
   A requirement outside the packet remains unverified. The owner must not have
   to choose evidence IDs, write cases, or repair the mapping themselves.
4. Confirm the current goals, then continue without another "please continue"
   prompt. Result generation requires that confirmed revision; stale bindings
   and stale result requests are refused. A later correction returns to this
   boundary rather than relabeling an already-produced result.
5. Lead with what is supported, contradicted, or unverified for the current
   goals, why, and the consequence for the owner's decision. Keep preservation,
   case reach, environmental blockers, and recovery distinct. Each observation
   names its reused/synthetic origin and offers the exact local evidence entry.
   Show an unmapped requirement as an actionable gap, never as a pass.
6. The owner can inspect evidence, correct again, accept the result's limits,
   request revision, or request a bounded additional-verification proposal.
   Record that choice only. No adoption, merge, new trial, or external operation
   follows automatically, including when the owner selects "accept".

The snapshot is not the runner's purpose/scenario file, and does not mutate
archived evidence. Replay goal corrections change the question being asked of
fixed records, not historical experimental intent or causal attribution.
Keep helper state outside the checkout in a mode-0700 directory with mode-0600
files. No transcript persistence by default. Evidence access is read-only and
limited to the explicitly supplied case root; missing files return a visible
gap. Do not put private packets or absolute personal paths in committed fixtures.

### Existing mechanisms, affected files, and size

Canonical source inspected: `plugin/skills/behavior-diff/SKILL.md`, especially
purpose provenance/privacy, automatic launch, frozen-goal rules, and raw-evidence
assessment; plus `docs/architecture.md`. Reuse those distinctions and the current
outer conversational summary pattern, not an installed skill copy or a second
canonical report schema.

Proposed implementation surface, all in the later assigned code worktree:

| File | Responsibility | Estimated changed lines |
| --- | --- | --- |
| `.agents/skills/verification-handoff-prototype/SKILL.md` | Host conversation, consent/replay limits, correction and evidence-review instructions | 90 |
| `.agents/skills/verification-handoff-prototype/scripts/replay.py` | Private snapshot, correction invalidation, confirmed-revision result/evidence projection; Python standard library | 180 |
| `.agents/skills/verification-handoff-prototype/fixtures/synthetic.json` | Invented change/context, supported observation, contradiction, and explicit evidence gap | 60 |
| `tests/verification-handoff-prototype-test.py` | Exercise the actual helper with synthetic inputs and temporary state, not wording-presence assertions | 120 |
| `e2e/README.md` | Single local entry/load instructions and the owner walkthrough boundary | 25 |
| `docs/architecture.md` | Identify this isolated maintainer replay, outside production trial/report flow | 15 |

Planning estimate: about 490 lines, tolerance plus/minus 150 across these six
files; not a delivery guarantee. No new dependency, CI lane, manifests, hooks,
runner flags, product schema, or report renderer changes. One focused PR is the
eventual breakdown; this stage authorizes neither its creation nor a code push.
If the design grows beyond this surface/tolerance, return the scope choice to
the owner rather than quietly adding orchestration.

The shipped report's hierarchy/navigation/comparison remains unchanged.
Therefore no renderer preview is proposed here. Any later renderer redesign
must first use `preview-behavior-diff-summary` and all three required saved cases
with fixed evidence; a conversational replay is not a waiver of that contract.

### Local evidence availability and honest reuse

The case selected is the existing local workflow-change experiment linked from
the task's supplied private discussion and experiment notes. Local reads found:
the before/after source snapshot and source-path mapping; frozen goals, coverage
and fixture specification; an adaptation manifest; a manually authored report;
per-criterion interpretation; execution summaries; and all six trial directories.
A raw action/return slice was inspected for an observed deviation followed by
recovery. These supply a supported-result path and an environmental/unverified
requirement path without new execution. Exact private coordinates remain in
the existing untracked notes, not copied into this report.

This establishes local availability, not a comprehensive re-audit of every
criterion or source byte. Aggregate interpretations remain attributed to their
saved authors except for the inspected raw slice. The report was manually
assembled using a custom execution setup, not delivered by the complete current
Behavior Diff pipeline. Multiple source documents varied; external-service
behavior was simulated; the path ends at a human decision boundary. Do not
claim whole-workflow coverage, production compatibility, general causality,
first-time intent inference, automatic evidence generation, or live latency.

The read-only related-task inspection found a saved-evidence comparison whose
baseline identity remains unresolved and an owner reader interaction awaiting
answers. This prototype uses the explicitly identified local experiment above,
not that disputed baseline or the related task's withheld reader materials.
It does not resolve the scenario-comparison hypothesis, consume its answers,
change its files/branch, or depend automatically on its completion.

Dependencies for implementation/walkthrough: design approval; the assigned code
worktree; Python 3; permitted local case access; a privately prepared evidence
packet preserving source coordinates, scope and reuse labels; and actual owner
participation. A fresh clone runs only the synthetic demonstration. Without the
private packet, the real-case walkthrough is blocked and must say so, not
substitute synthetic findings. Baseline-result familiarity must be disclosed.

### Disposable interaction probe and limits

After assembling this design, one private, synthetic JSON-line interaction
probe exercised the proposed local helper boundary. Command:
`python3 <private-disposable-directory>/probe.py`, with 13 synthetic stdin
actions; exit 0. Observed assertions:

- Exact free-text corrections reached the current result; changed-goal support
  was invalidated and unrelated goal support remained. Keeping the old binding
  or displaying the old goal would fail these assertions.
- Unconfirmed corrections and stale result/binding revisions were refused.
  Accepting the previous revision would fail the probe.
- An explicitly authored supported mapping exposed synthetic replay provenance;
  a second, unmapped correction stayed unverified with a next-verification path.
  Treating missing support as a pass would fail the probe.
- A request-verification decision was recorded without an external action.

This was throwaway mechanism code, not the shipped helper, an actual host
conversation, or owner usability evidence. Its evidence mapping was authored;
it does not establish semantic mapping accuracy, inference quality, host
instruction compliance, or that the owner no longer directs verification.
The probe file and directory were removed after recording these safe outcomes.
No build, lint, formatter, repository test, model trial, or paid extraction ran.

### Acceptance evidence for implementation and owner walkthrough

Keep the task's AC-1–AC-3 unchanged. Their finished outcomes and falsifiers are:

- AC-1, offline then interactive: the implemented helper rejects stale snapshots
  and projects corrected goals, then the owner operates the actual conversation
  from supplied handoff to result, making a real wording/scope correction and
  inspecting its consequence. Record the actual current goal/result association
  privately. A static script, ignored correction, or helper-only pass is not
  acceptance. Offline probe above de-risks the mechanism only; AC-1 remains open.
- AC-2, offline then interactive: exercise the implemented synthetic support,
  contradiction, and missing-evidence paths; then let the owner follow a real
  result's cited support and an unverified requirement in the local packet.
  Record whether the cited action/return/artifact supports that exact claim and
  whether reused versus fresh evidence is clear. A dead citation, final-answer
  claim substituted for execution, hidden recovery, or unknown promoted to pass
  falsifies this outcome. Current evidence availability is not AC-2 completion.
- AC-3, actual owner review: before results, capture the owner's usual approach
  and remaining question in their own words, using supplied context rather than
  requiring a new test plan. Do not assume that arranging tests or reconstructing
  output was their established bottleneck; existing corrections prioritize
  credible evidence for the decision, with speed only an additional benefit.
  During this same walkthrough privately record every takeover, trigger/reason,
  work done, attention/wait burden where observable, and whether it was a
  necessary owner choice or avoidable agent work. Afterward ask what decision
  they can now make, what still needs checking, and which burden remains most
  costly compared with their baseline. Retain actual responses, not predicted
  praise, and select the next experiment from that remaining takeover point.

Owner corrections, missing-context decisions, evidence inspection, gap handling,
and final accept/revise/request-verification choices are the observation points;
do not add a reader study, score threshold, recruitment step, or new gate.
Support for value requires a grounded decision and a concrete account of what
verification work was or was not handed off versus the owner's baseline.
Negative or inconclusive value is valid, but cannot be described as success.
Known-case replay cannot establish first-use inference, faster execution, or
general usability. AC-3 remains Captain-dependent and wholly unperformed here.

## Stage Report: ideation

- DONE: Recommend the smallest operable handoff-to-decision surface and simplest alternative, preserving user corrections and evidence limits; identify affected files, estimated size/tolerance, dependencies and verification.
  Proposal above compares static, terminal, existing-skill and local conversational surfaces; six-file estimate is 490 lines plus/minus 150, with no production cutover.
- DONE: Verify local permitted case evidence availability and exercise the riskiest correction-to-result mechanism in disposable private space; state replay and inference limits without launching paid trials.
  Local source/evidence reads establish availability; one 13-action synthetic probe exited 0, rejecting stale revisions and keeping an unmapped correction unverified; scaffolds removed.
- DONE: Define acceptance evidence for the actual owner walkthrough, including intervention points and an evidence-gap path; write a privacy-safe ideation stage report for the owner design gate.
  AC-1–AC-3 mapping above defines falsifiable offline/interactive checks and the baseline/takeover record; actual owner walkthrough and usability/value findings remain open.

### Summary

Recommend an isolated maintainer conversation with revision-bound replay state,
not a change to the automatic production skill. Permitted local evidence and a
disposable correction probe support taking this design to owner review; they do
not establish usability or authorize implementation.
