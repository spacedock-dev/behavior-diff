# Answer the skill-change question before presenting secondary differences

**Recorded:** 2026-10-08

**Status:** Implemented; canonical presentation, deterministic acceptance coverage,
and remaining model-evidence limits are recorded below.

**Scope:** Refine how Behavior Diff answers the owner's question about an instruction
edit, especially when the relevant behavior is already correct Before. The first two
commits of Recce-team PR #12 motivate this plan. The final commit provides a contrasting
case where preserving behavior is the desired result.

## Reader and decision

The reader is a PR owner explaining a skill change to teammates who already know what
the skill does. The report is their presentation material. It should help them explain:

- Why the instruction needs to change.
- What the proposed edit requires.
- What happened to the behavior the edit was meant to address.
- Which consequences or uncertainties matter before accepting the edit.

Do not turn this into an explanation of how Behavior Diff works. Do not require the owner
to assemble the answer from incidental differences, execution-completeness labels, and
raw trial logs. The report must support an honest conclusion, not justify every edit.

## Historical context

Source: [DataRecce/recce-team PR #12](https://github.com/DataRecce/recce-team/pull/12).

Skill: `recce-team/skills/release/publish-changelog.md`. It turns selected product updates
into customer-facing release notes, following writing guidance and a review workflow.

The incident concerned an export improvement. A developer's summary implied unrestricted
exports, but the implementation still imposed format-specific row limits. A release-note
draft overstated the feature, and a reviewer caught it. The proposed instruction changes
make source verification an explicit prerequisite to writing customer claims.

These are generalized design notes, not historical fixtures. Keep private source excerpts,
original discussions, generated drafts, reports, traces, and detailed run provenance
outside this repository. Future committed previews and tests must use synthetic content.
PR #40 is a separate deferred candidate and is not part of this commit sequence.

### Commit sequence

| Revision | Instruction change | Question to evaluate |
|---|---|---|
| Baseline `8d850c3d` | Version before PR #12 | What does the existing skill already do? |
| First `68ca666c` | Adds reading the source PR before drafting and a writing rule requiring verification against PR details and code changes. Includes an incident-specific example. | Does adding source verification prevent an unsupported customer promise? |
| Second `08c2ff13` | Explicitly requires comparing the summary with implementation evidence, identifying discrepancies, extracting verified facts, and grounding the draft in them. | Does explicit cross-checking improve how conflicting source information is handled? |
| Final `e14115ed` | Removes the incident-specific examples while retaining general verification guidance. Also removes the explicit sentence directing the agent to note mismatches. | Does the relevant accuracy survive the removal? |

The second commit refines the first fix; it is not evidence that the first fix was tried
and failed. The final edit is not a perfectly isolated example-only ablation.

### Original reasons, intended fixes, and post-change concerns

Keep three kinds of information separate: the historical reason for the commit, a
remaining instruction-design concern addressed by the next commit, and differences
observed in the later replay. A follow-up commit is not proof of a newly reproduced
failure. An After-only observation is not proof that the patch caused it.

#### First commit: `68ca666c`

**Original reason:** The historical changelog draft overstated export capabilities.
The existing workflow moved from selected release items into writing without an
explicit source-verification step. This motivation comes from the PR incident context;
the commit itself introduces the verification requirement.

**Purpose of the change:** Require consulting the source PR before drafting and checking
behavior claims against PR details and code changes. Ground the customer explanation
in the actual feature, including its limits and exceptions.

**Concern remaining after the patch:** The source PR summary can itself overstate the
feature. The first edit requires source inspection, but does not explicitly explain
how to resolve disagreement between the summary and implementation. This is the gap
the second commit addresses. It is a remaining ambiguity, not a new defect demonstrated
to have been introduced by the first patch.

**Post-change observations in the replay:** The export claims remained accurate.
Some After drafts added scope qualifications, while an After draft omitted an improvement
metadata tag that Before included. The tag difference warrants checking only if that tag
is required or affects the publishing workflow; neither downstream breakage nor causation
was established. The report's overstatement of a row-count wording contrast is an
assessment issue, not an issue caused by the patched release-writing skill.

#### Second commit: `08c2ff13`

**Original reason:** The commit message and diff explicitly address discrepancies between
PR titles or summaries and implementation details. Consulting a misleading summary is
not enough to prevent an overstated customer claim.

**Purpose of the change:** Make comparison and conflict resolution explicit. Extract
verified facts from implementation evidence and use those facts when drafting, rather
than treating the summary as sufficient authority.

**Concern remaining after the patch:** The instructions contain examples tied to the
specific export incident. The final commit's stated purpose is to teach a general
principle instead of a one-off scenario. That is a maintainability/generalization concern,
not evidence that the example caused a new runtime failure. Whether the example biases
results or is needed for other tasks remains untested.

**Post-change observations in the replay:** Correct limits and the important exception
were preserved. The supported non-primary-key query case was named less consistently
After, while clipboard behavior was disclosed more consistently. Omitting an explicit
inclusion is not the same as claiming the query type is unsupported. These are changes
in written coverage with an uncertain relationship to the patch, not demonstrated
regressions in conflict resolution.

#### Final commit: `e14115ed`

**Original reason:** The commit message states that the export-specific examples should
be removed so the skill teaches general verification principles rather than one scenario.

**Purpose of the change:** Retain the verification requirement while removing the specific
example. The diff also removes the explicit instruction to note mismatches, so the
comparison must assess the combined edit rather than attribute everything to the example.

**Concern to check after the patch:** Does accurate qualification survive without the
example and mismatch-note sentence? Does the agent lose an important restriction or stop
making relevant discrepancies visible? These are evaluation questions, not established
new failures.

**Post-change observations in the replay:** The targeted accuracy was preserved. An After
draft omitted the clipboard limitation, and another omitted the improvement metadata tag.
Those observations do not establish expanded copying support, publishing failure, or
causal regressions. No subsequent historical defect caused by this final edit has been
established in this investigation.

### How to carry this context into the report

For each proposed edit, distinguish:

1. **Original problem and provenance:** what motivated the author, with a source link.
2. **Proposed resolution:** what the instruction now requires.
3. **Observed outcome:** whether the target problem remains, improves, or was already absent.
4. **Remaining or additional concerns:** distinguish a pre-existing gap, an observed
   post-change difference, a hypothetical risk, and an established regression.
5. **Acceptance decision:** what the owner should verify or decide before keeping the edit.

Never label a concern as a new issue generated by the patch without supporting evidence.
If the evidence only shows a difference after the edit, say that and retain the uncertainty.
Historical motivation should not be replaced by an inferred purpose reconstructed from
whichever output difference happens to be most visible.

## Report gaps at commit time

The replay above had information a normal run does not have. Behavior Diff normally runs
when the owner is about to commit an edit. At that moment the diff and the current session
history usually show why the owner made the edit, but nobody knows what later commits
will fix. Nobody has a ground-truth answer for the task either. The gaps below apply to
that normal run.

| # | Gap | Current behavior | Required change |
|---|---|---|---|
| 1 | The edit's purpose does not reach the report. | Extraction infers intent from the changed lines alone. The skill runs in the session where the owner made the edit, but none of that session's context reaches the report. The renderer can already show a supplied `expected` value from `config.json` (`intent_context` in `reporting/content.py`), but `behavior-diff.sh` always writes `null` (line 225), and `build_prompt` in `decisions.py` never passes it to extraction. | The skill infers the purpose without asking the owner. For an uncommitted edit, it uses the diff and the current session history. When the edit has a commit message, it uses the commit history instead of session history, because the session that made a committed edit has usually ended and the current session log does not contain it. It passes the inferred purpose and its source to the runner, into `config.json`, and into the extraction prompt. The report labels it as inferred and names the source. |
| 2 | The Summary does not answer the target question. | The headline selects the most prominent observed difference. When the target behavior is unchanged, a secondary difference leads. | Assess the observable target on each side when evidence permits; preserve mixed and unassessable outcomes. Support correcting, introducing, changing, and preserving behavior. |
| 3 | Attention cannot report a mistake present on both sides. | Attention selects only rows whose choice distributions changed. | Allow attention for the targeted mistake when both sides still make it. |
| 4 | Concern categories do not separate the kinds of concern. | Relationship is `expected`, `additional`, or `unclear`. | Keep relationship-to-purpose separate from evidence status: pre-existing problem, observed difference, or hypothetical consequence. Do not imply causation from occurrence After. |
| 5 | The report cannot check output against what the agent read. | Extraction sees read paths, not returned content. | Provide bounded recorded tool-returned content with provenance and omission status, not silent post-trial rereads. When evidence is insufficient, say what cannot be assessed. |

Gaps 2 and 3 depend on gap 1: the report must know the target mistake before it can
answer whether it happened. The "pre-existing gap" category in gap 4 also depends on
gap 1. Gaps 1 and 5 change the extraction input contract. Gaps 2 to 4 change extraction
guidance, validation, and rendering.

Constraints for gaps 1 and 5:

- **No purpose found.** If the session or commit history does not show why the edit was
  made, fall back to intent inferred from the diff alone, as today. The report says the
  purpose came from the diff only. Gap 2 then answers about the diff-inferred behavior,
  or says the target question is not assessable.
- **Keep the purpose out of the trials.** The inferred purpose goes only to extraction and
  the report. It must never enter `--task` or any trial input. Skill step 2 already forbids
  leaking expected behavior into the task; if trials see the purpose, both sides follow it
  and the comparison shows nothing.
- **Pass a purpose, not the session.** The skill infers one or two sentences of purpose
  from the session history. It does not pass session text to the runner or extraction,
  and the report never quotes the session. Session history can contain secrets, customer
  names, or unrelated work.
- **Committed edits.** Skill step 1 finds only uncommitted edits. Today, a commit message
  is available only in a `--before-file` run or a historical replay. Decide whether
  Behavior Diff should also accept a committed edit directly; this plan does not add that
  run mode.
- **Both hosts.** Claude Code and Codex must infer the purpose the same way. Check how each
  host exposes the current session history before implementation.
- **Bound the file content in gap 5.** Decide before implementation which files qualify
  (for example, only files the trials actually read), a per-file and total size limit, and
  how to omit secrets or private data. The content is sent to the extraction model and
  excerpts can appear in the report. Keep treating it as untrusted evidence, never as
  instructions.

Some edits aim to keep behavior rather than prevent a mistake, such as the final commit's
example removal. For those edits, gap 2 asks whether the behavior the owner wants to keep
survived: "already avoided" becomes "preserved", and "worse" becomes "lost". "Fixed" and
"still present" do not apply.

These replay-only items are not report requirements:

- Checking customer claims against authoritative product facts. A normal run has no
  ground truth. Gap 5 checks consistency with what the agent read instead.
- Classifying drafts as accurate or overstated. Gap 2 asks whether the targeted mistake
  happened instead.
- Using later commits to identify what the edit got wrong.
- Labeling conclusions as manually verified. A normal run has no manual check step.

The provenance link in item 1 of "How to carry this context into the report" is also
replay-only. In a normal run, the provenance is the diff and the session history, or the
commit history when a commit message exists.

## Findings from the comparisons

The adjacent-commit comparisons used the same reconstructed writing task, frozen source
material, and model. Complete draft text was available for inspection. This was a replay
based on the incident, not the original writing session or a live product export test.

### First commit: no demonstrated incremental accuracy benefit

Both variants produced the correct export limits and preserved the relevant exception.
The historical overstatement did not reproduce in Before. Source inspection was already
observed on both sides.

The report instead led with a distinction about qualifying row-count labels. That
interpretation overstated the contrast: some Before wording already qualified availability.
Other promoted findings concerned scope details and metadata rather than the target error.

**Design finding:** An accurate baseline must remain central. A secondary wording change
must not become a substitute success story because the intended behavior was unchanged.
Check semantic equivalence before declaring a qualification newly present.

### Second commit: no demonstrated improvement in resolving the conflict

Both variants produced customer claims consistent with implemented limits rather than the
unrestricted summary. The report led with variability in whether a supported query type
was named, and attention findings also discussed clipboard disclosure.

Those are observable editorial differences, but they do not establish that the stronger
cross-checking instruction improved conflict resolution or caused the omissions/additions.

**Design finding:** Show how each draft treats the conflicting claim. Do not make the
reader infer this from a comparison of other details included in the release note.

### Final commit: preservation can answer the question

The important export limits and exception remained correct after removing the examples.
That is limited evidence supporting this cleanup in the tested scenario. It does not mean
all draft details were unchanged or establish general reliability on other features.

**Design finding:** Preserved accuracy should lead when preservation is the owner's goal.
Secondary omissions should not displace that result merely because they are differences.

## Information the first-commit replay report should provide

This section and the next describe the PR #12 replay, where later history supplies the
product facts. In a normal run, replace authoritative product facts with the content the
agent read (gap 5). Replace the accuracy classes with whether the targeted mistake
happened (gap 2).

Question: **Does requiring source verification prevent an unsupported customer promise?**

Present the evidence chain in this order:

1. **Problematic input claim.** Identify the claim the agent could incorrectly repeat.
2. **Authoritative product facts.** Show the implemented limits and relevant exceptions,
   with source references and an explicit indication of whether those sources were available
   to the assessment. A PR summary must not serve as the ground truth it is being checked against.
3. **Actual Before and After claims.** Show concise, contextual excerpts from the generated
   release note, including relevant titles and descriptions as well as the body. Do not
   substitute the agent's self-assessed review result for the customer-facing text.
4. **Outcome across trials.** Distinguish accurate qualification, unsupported overstatement,
   ambiguous wording, and insufficient evidence. Preserve minority outcomes and uncertainty.
   Missing a number alone is not necessarily an inaccurate claim.
5. **Supporting source inspection.** Show relevant reads separately. Reading a file does not
   prove its facts were applied correctly, and a stated intention to read is not an actual read.

The conclusion for the observed comparison should be that both variants avoided the target
error; no additional accuracy benefit was demonstrated. Task completion is useful context,
not the answer to this correctness question.

## Information the second-commit replay report should provide

Question: **Does explicit cross-checking improve resolution of conflicting source claims?**

Make the conflict visible rather than merely listing consulted files:

- The summary's claim and the contradictory implementation facts, with provenance.
- The relevant customer-facing claim produced by each version.
- Whether each draft repeats the misleading claim, qualifies it accurately, or remains ambiguous.
- Any explicit discrepancy explanation in the agent's final review, labeled as its explanation.
  Do not present it as access to internal reasoning or proof of which source caused its choice.
- Whether important restrictions elsewhere in the draft remain intact.

The conclusion for the observed comparison should be that both variants produced wording
consistent with the implementation; explicit cross-checking had no demonstrated incremental
accuracy benefit here.

Both variants contain incident-specific guidance. Correctness on this matching example
cannot establish that either version resolves unfamiliar discrepancies reliably.

## What needs your attention

Use the existing promotion gate: a supported distinction, a meaningful consequence, and a
useful decision. Attention should inform acceptance of the instruction edit, not become a
list of optional editorial improvements.

Decision-relevant examples for these questions include:

- The unsupported promise persists after the proposed fix.
- The body states the restriction, but the title or description still overpromises.
- A corrected limit accompanies the loss of an important exception.

Also make **the baseline already handles the target problem** prominent as the primary
result or its decision implication. Do not force that unchanged finding into a side-effect
card or treat a lack of improvement as evidence that the instruction is generally useless.
This does not conflict with gap 3. When both sides avoid the targeted mistake, the Summary
says so. When both sides still make it, attention reports it.

Coverage, clipboard, and metadata differences may remain in supporting detail. Promote one
only when evidence and workflow context explain a meaningful consequence for the reader.
Do not invent downstream harm, assume a missing detail makes a draft false, or infer that
an edit caused a difference merely because it occurred After. Conversely, a serious observed
risk may merit attention even when its causal relationship to the edit remains uncertain;
state that uncertainty rather than hiding the risk.

An assessed-empty attention section is valid. Do not impose a finding quota.

## Evidence availability and limits

The current extraction evidence in these runs identified source reads but did not include
the returned source-file contents. Complete final drafts were included. That supports
comparison of written claims but does not independently establish product truth from read
paths alone. A separate manual source check must remain distinguishable from model extraction.

Gap 5 is the normal-run requirement: give assessment bounded content the agent read,
with provenance, so it can check output against that content. Before implementation,
inspect the current evidence contract and choose the format. This is a design direction,
not an approved schema or permission to fetch more private data automatically.

If that content is unavailable, say consistency cannot be checked.
Do not fill the gap using the instruction's example, the PR headline, or the agent's own
claim that its draft passed review.

Keep the purpose inferred from session or commit history separate from intent inferred
from the diff alone, and name each source. Keep observed output, agent
explanation, assessor interpretation, and causal claims separate. A repeated pattern in a
small sample does not establish causation or general effectiveness.

### Agreed decision 1: assess only what the evidence supports

Use the available evidence to answer as much of the owner's question as possible.
Before assessing the outputs, identify the observable criterion and the evidence
needed to judge it. An inferred purpose identifies the question; it does not prove
the outcome.

Distinguish an agent's claim that it checked a source, a recorded source read, and
an output demonstrably consistent with the relevant source facts. Do not treat
these as equivalent.

When evidence is missing, contradictory, or insufficient, state what was observed,
which part cannot be determined, and why. Do not guess a success or failure.
Insufficient evidence is not a failed skill, and uncertainty about one claim must
not erase other conclusions the evidence does support.

### Agreed decision 2: preserve mixed outcomes

Assess each trial against the same observable criterion and retain the Before and
After distributions, including minority outcomes and trials with insufficient
evidence. Do not force mixed results into one pass/fail verdict or call a problem
fixed when it remains in an After trial.

Describe the observed difference and any remaining problem directly. Apply the same
rule to adding or changing a behavior and to preserving existing behavior, not
only to correcting mistakes. Keep unavailable assessments distinct from observed
failures. Small-sample counts describe these trials, not long-term reliability or
proof that the edit caused the change.

### Agreed decision 3: preserve the evidence the agent actually received

Use recorded tool-returned content as trial evidence. Do not silently reread files
afterward and present their current contents as information the agent saw.

Retain the trial identity, source, returned portion or range, and any truncation
or redaction applied before assessment. Include bounded excerpts with per-excerpt
and total size limits, exclude sensitive content, and clearly mark omissions.
Missing assessment content does not establish that the agent never received it.

Any separately retrieved source content must be labeled as an additional source
check, not original trial evidence. This decision does not authorize automatic
additional retrieval. Exact size limits, excerpt-selection rules, and sensitive
content handling remain implementation-design decisions to resolve before coding.

### Agreed decision 4: separate relationship from evidence status

Assess a finding's relationship to the instruction edit separately from what the
evidence establishes. An explicitly requested behavior, an additional behavior,
or a behavior with an unclear relationship can each have observed or hypothetical
consequences.

Distinguish pre-existing problems, observed differences, and possible consequences.
Appearing After does not establish that the edit caused the behavior or that it is
harmful. Explain these distinctions in plain language; do not require readers to
understand a classification system. This clarifies gap 4: concern categories must
not replace relationship-to-purpose labels as if they described the same dimension.

### Agreed decision 5: capture purpose before observing results

Before running the comparison, prepare a concise purpose statement from the current
conversation and diff, or the relevant commit history for a historical comparison.
Record its provenance and distinguish explicit owner intent from inference. When
only the diff supports a purpose, label it as diff-inferred; do not invent missing
motivation. Preserve distinct goals rather than merging them into one vague outcome.

Pass purpose to assessment and report generation only, never as an added instruction
in the task or other trial inputs. Do not revise the purpose after seeing results to
fit a convenient difference. Exclude secrets and unrelated private details from the
derived statement as well as keeping raw session history out of the handoff.

### Agreed decision 6: review synthetic previews before production changes

Prepare clearly labeled, authored synthetic previews using the existing report
renderer, without model calls or private source material. Review the presentation
before changing the production report pipeline.

Cover an already-correct baseline, a targeted mistake that persists on both sides,
mixed After outcomes, insufficient evidence, preservation after cleanup, and an
important additional concern. Each preview must make clear what is changing, what
the evidence shows, and what the team should consider before accepting the edit.

The owner reviews whether the target answer is prominent and attention is
decision-relevant rather than dominated by incidental differences. Preview approval
validates presentation of authored evidence, not extraction quality or real-world
effectiveness. Follow the existing synthetic summary preview workflow; do not
create a second production renderer.

## Proposed presentation direction

Retain the existing four-part Summary; change evidence selection and emphasis before adding
new report sections:

- **The intended change:** the edit-specific question and its purpose, attributed appropriately.
- **What the evidence shows:** the answer about the target behavior, including accurate shared
  behavior when unchanged. Link the answer to input content and actual output claims.
- **What needs your attention:** only decision-relevant consequences or uncertainties.
- **What this means:** what the comparison supports about accepting the edit, and what remains
  unestablished. Do not turn this into automatic PR approval.

Use **Understand the change** for the fuller input/source/output explanation, preserved
restrictions, trial variation, and source-access limits. It should add reasoning and evidence,
not repeat the Summary cards. Keep lower-priority differences available in detailed comparisons.

## Acceptance criteria

A reader should be able to answer, without reconstructing raw logs:

1. What problem does this particular commit aim to address?
2. Which task input and content the agent read set up that problem?
3. What did the Before and After agents actually do and say?
4. What happened to the targeted behavior in each trial, including mixed and
   unassessable outcomes? Did a problem remain, a requested behavior appear, or a
   behavior intended to survive remain present? Do not force a single pass/fail label.
5. What matters before accepting the edit, and why?
6. Which conclusions are observed, inferred (and from which source), or unavailable?

Before changing report hierarchy or presentation, prepare synthetic previews under the
repository's report-presentation guidance and agree on the reader's question. Include an
already-correct baseline, a remaining overstatement, a corrected claim with a lost exception,
missing read content, and preservation after example removal. These are
future synthetic coverage cases, not claims about outcomes observed in this history.

Do not change the task or evaluation question after seeing results to manufacture a success.
Do not require a visible difference when the question is whether useful behavior survives.

## Implementation handoff

The six agreed decisions are the implementation requirements. The historical replay
is motivation and evidence of reporting weaknesses, not a fixture to tune against.
Earlier implementation-location references are investigation pointers; verify them
against the current code before editing.

Proceed in this order:

1. **Approve the presentation.** Use the `preview-behavior-diff-summary` workflow
   to build the six cases in agreed decision 6 with the existing renderer. Keep
   paired evidence constant, label authored content, and verify the actual browser
   surface. Record approval before changing production presentation.
2. **Freeze the data contracts.** Trace purpose from skill to runner/config to
   extraction and report; trace recorded tool results through host normalization.
   Specify purpose/provenance, observable criteria, per-trial assessment and evidence
   references, omission status, and independent concern dimensions. Keep the same
   criteria across Before and After. Specify handling for absent purpose, conflicting
   evidence, incomplete trials, and unavailable extraction without manufacturing an
   assessed-empty result.
3. **Resolve bounded-evidence mechanics.** Document exact per-excerpt and total
   limits, deterministic selection/truncation rules, and sensitive-content handling.
   These details are not yet decided. Resolve them before implementing collection;
   do not claim generic automatic redaction guarantees removal of every secret.
   Preserve provenance for excluded content without reproducing sensitive values.
4. **Implement the input handoff.** Capture purpose before trials, keep it out of
   trial inputs, and supply only approved bounded evidence to assessment. Preserve
   supported host behavior, including Claude Code, Codex, Pi, and OMP. No new
   committed-edit invocation mode or additional model call is required by this plan.
5. **Implement assessment and presentation together.** Update extraction guidance,
   schema/validation, ingestion, and report selection so the target answer leads,
   mixed results stay visible, and a persistent target problem can reach attention.
   Apply relationship and evidence-status distinctions without presenting model
   judgments as causal proof. Add detail in Understand the change rather than
   duplicating Summary cards.
6. **Verify the complete path deterministically.** Exercise synthetic inputs through
   ingestion and rendering, including the six preview situations. Cover purpose
   isolation, missing/partial evidence, range and omission provenance, mixed trial
   membership, and unchanged target problems. Verify host normalization contracts.
   Run the relevant repository checks and inspect the actual rendered report;
   authored previews do not prove a live extractor follows the new guidance.
7. **Finish the cutover.** Update affected callers, contract fixtures, and
   `docs/architecture.md` in the same implementation change. Keep the canonical
   renderer, remove temporary preview scaffolding after review, and document any
   intentional handling of previously saved report data. Do not silently retain an
   obsolete competing assessment path.

Implementation is complete only when the owner's target question, actual trial
evidence, assessment limits, and decision-relevant attention remain connected across
the complete report. Passing schema checks or changing narrative wording alone is
not sufficient. Live validation, if later requested, needs separate approval.

## Related plans and non-goals

This applies the consequence-first selection policy in
[Balanced reporting of additional behavior changes](2026-10-07-balanced-side-effect-reporting.md)
and complements
[Agent-assisted evidence investigation](2026-10-06-agent-assisted-evidence-investigation.md).

The documentation-only planning step did not authorize model runs or implementation.
The owner subsequently requested implementation and approved the six synthetic
target-first previews before production changes. Those previews used no model calls.
Later, separately approved historical trials informed the presentation refinements
below. Their private inputs, outputs, and reports remain outside this repository.

## Implementation record

Tracking: [DRC-4835](https://linear.app/recce/issue/DRC-4835/answer-the-skill-change-target-before-secondary-report-differences).

- **Presentation approved:** Keep the four-part Summary. Its headline and one
  illustrated Before/After pair explain observed behavior, including unchanged
  behavior. Show assessment questions separately as compact, unlinked text rows.
  Emphasize changed Yes/No proportions without hiding mixed or unassessable counts.
  Use “Not enough evidence” only for the affected check, never as the main headline.
  Understand the change starts with readable explanations; raw excerpts and
  trial-level records are collapsed. Authored preview approval is not evidence
  of live extractor quality.
- **Purpose-linked conclusion:** “What this means” connects observations to the
  reason for the edit. It distinguishes an already-correct baseline, a remaining
  problem, preservation, mixed results, and a scenario that did not exercise the
  intended problem. Additional detail in a draft is not proof of improved accuracy
  or conflict resolution. Evidence limits must not erase supported observations.
- **Purpose:** `--purpose-file` carries up to eight distinct concise goals with
  session/commit/diff provenance and explicit/inferred basis. The runner validates
  and freezes it before trials, excludes the file from trial copies, and supplies
  purpose only to extraction/reporting. Historical evaluation preparation records
  and freezes a reviewed commit/diff purpose file.
- **Evidence:** Recorded returns only; 4,096 Unicode characters per excerpt,
  16,384 per trial, 131,072 per run, and 128 tool records per trial. The saved trial
  inventory determines membership. The remaining run budget is shared across
  remaining trials in lexical order; within each trial, readable returns share
  the character budget, redistributing unused shares from shorter returns.
  Excerpts retain source descriptors, returned-character offsets, status, and
  omission reasons. Known sensitive sources and credential/email patterns omit
  whole returns; this cannot guarantee removal of arbitrary private prose.
- **Assessment:** Each criterion identifies its purpose goal, mode, required
  evidence, supporting comparisons, and complete trial membership. Outcomes
  distinguish met, not met, uncertain, and unassessable. Source-consistency
  judgments require recorded source content and an exact final-answer excerpt.
  References are trial-local; omitted content cannot substantiate a judgment.
- **Attention:** Relationship to purpose remains independent of evidence status.
  Unchanged target mistakes can be promoted when the criterion records an unmet
  outcome on both sides. Invalid assessment stays unavailable, not assessed-empty.
- **Saved data:** Report schema 12 persists purpose, bounded evidence, limits,
  and assessment. Schema 11 reports remain readable with explicitly unavailable
  target assessment. Old decisions without the new attention contract show
  unavailable attention. Historical evaluation sessions without a frozen purpose
  file must be prepared again; purpose is never reconstructed after results.
- **Synthetic coverage:** The canonical report gallery includes all six situations.
  Deterministic contracts cover provenance, membership, evidence boundaries,
  incomplete runs, legacy loading, and purpose isolation. Actual browser checks
  cover target headlines/counts, persistent-problem attention, source/output
  excerpts, minority-trial navigation, and desktop/narrow layouts.

Architecture and exact component responsibilities are documented in
[`docs/architecture.md`](../docs/architecture.md). Remaining evidence limit:
authored fixtures establish the contract and presentation, not whether a live
extractor will correctly interpret arbitrary source claims.

## Acceptance recheck after presentation feedback

The approved presentation now uses the canonical HTML and Markdown pipeline,
not a separate preview renderer. The human-evaluation quiz accepts the new
assessment table while retaining source-hiding and fail-closed HTML validation.

| Reader requirement | Implemented response | Verification |
|---|---|---|
| Why this edit? | Frozen purpose, explicit/inferred basis, and provenance remain separate from observed outcomes. | Purpose validation and Git/copied-project trial-isolation contracts. |
| What input and sources set up the problem? | Human explanation connects the input claim, recorded source facts, and actual deliverables; raw records remain expandable. | Authored source-conflict and missing-source cases; exact-excerpt and provenance contracts. |
| What did Before and After do? | One behavioral comparison with real branch memberships and correct answer/plan/action provenance. Assessment status never substitutes for that illustration. | Canonical gallery and browser checks, including plans and incomplete evidence. |
| What happened to the targeted behavior? | Separate question rows preserve all trial outcomes, including mixed, unknown, and unassessed records. Only supported Yes/No proportion changes receive emphasis. | Target assessment and HTML/Markdown consumer regressions. |
| What matters before acceptance? | Purpose-linked conclusion and decision-relevant attention distinguish existing problems, observed differences, and hypothetical consequences. | Persistent-problem, additional-concern, and corrected-limit/lost-exception cases. |
| What remains unknown? | Scoped source omissions and scenario limits coexist with supported observations; missing interpretation is explicit. | Missing-source, incomplete-trial, invalid-assessment, and legacy-data contracts. |

All six agreed synthetic situations remain covered. A seventh case corrects the
main limit while falsely restricting a supported query type, covering the lost
exception required by the acceptance criteria. This is an explicit contradictory
claim, not an assumption that an omitted detail is false.

Verification passed: hooks, extraction self-checks, live-report contracts,
release-workflow contracts, human-evaluation workflow/quiz/hosted checks, purpose
validation, recorded-evidence checks, Bash formatting, and Python formatting.
Browser checks exercised the canonical reports, collapsed/expanded evidence,
changed-result emphasis, narrow layouts, and preserved evidence provenance.
The quiz path was also exercised with a synthetic report, preserving mixed
assessment counts while hiding original purpose provenance.

Independent review identified five input-boundary defects, now corrected:
recognized quoted credential keys and sensitive Git revision paths are excluded;
supported Codex shell wrappers retain simple recorded reads; relative purpose
paths stay relative to the caller; and purpose removal rejects snapshot parent
symlinks instead of following them outside the copy. Dedicated regressions fail
on the reviewed code and pass on the corrections. The wrapper tests also retain
exclusions for compound commands, redirections, substitutions, and non-read commands.

The new front-door regression also exposed a pre-existing macOS-only `mktemp`
form in Linux CI. The backup now uses an explicit six-X temporary-file template,
preserving the same restoration and cleanup path on both hosts.

### What this verification does not establish

- These checks establish reporting behavior and evidence contracts. They do not
  prove that a model's judgment is semantically correct merely because its
  references and quoted excerpts are valid.
- Later presentation and conclusion examples use unchanged historical trial
  evidence. Authored conclusion examples remain labeled; they are not evidence
  that the revised extraction prompt generated those words.
- An already-correct baseline cannot demonstrate correction of an unreproduced
  historical mistake. A task without the relevant source conflict cannot
  establish better conflict resolution. Preservation applies only to the
  behavior and scenario actually checked.
- Bounded excerpts can omit facts the trial agent received. The report must
  distinguish that omission from evidence that the agent never saw a source.
  Sensitive-content filtering also cannot guarantee removal of arbitrary
  private prose.

The implementation addresses the reporting gaps. Stronger claims about the
skill's effectiveness require suitable scenarios and adequate evidence; the
report must state the limit when those prerequisites are absent.
