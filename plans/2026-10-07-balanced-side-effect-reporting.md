# Balanced reporting of additional behavior changes

**Recorded:** 2026-10-07

**Status:** D picture-first presentation approved for production implementation after
synthetic previews and five fresh-commit comparisons.

**Scope:** How Behavior Diff selects and presents additional behavior changes without
obscuring the user's original question or creating warning fatigue.

**Example skills:** `tdd-from-spec`, `pr-review-response`, and `claude-code-review`
from `DataRecce/recce-team`.

## Decision: prioritize consequences, not novelty

Answer the user's original question first. Promote another finding only when it could
change their decision to keep the instruction edit. A surprising difference is not
necessarily important, and an unchanged headline can hide an important difference.

Do not assume the owner's expectations or call every difference an unintended regression.
Use neutral descriptions and distinguish expected, additional, and unclear changes.
A report with no attention finding is a valid result; finding a concern is not a
success criterion.

The approved Summary has four numbered sections: **The intended change**,
**What the evidence shows**, **What needs your attention**, and **What this means**.
The third section usually contains zero or one decision-worthy finding.

This is not a hard cap: multiple serious risks must remain visible.

## Three visibility levels

| Level | Content | Placement |
|---|---|---|
| Main result | What happened to the behavior the user wanted to change | Summary headline and Before/After comparison |
| Needs your decision | A supported change with a meaningful tradeoff, including relevant expected tradeoffs | Picture-first numbered Summary section |
| Supporting detail | Context, variability, and uncertain implications | Additive attention explanation inside Understand the change; raw comparisons under optional Check the evidence |

Do not promote a minor observation merely because the main behavior was unchanged.
Preserve relevant observations in the evidence even when they do not earn a callout.

## Promotion gate

A normal Summary callout must satisfy all three checks:

1. **Real difference.** Saved Before/After evidence supports the distinction. Check
   existing Before behavior, variation, shared scenario constraints, and missing evidence.
   An instruction diff alone does not prove a behavioral effect.
2. **Meaningful consequence.** The difference changes permission, scope, correctness,
   irreversible actions, or a significant workflow obligation. Mere wording or sequencing
   variation is insufficient without a consequence.
3. **Useful decision.** The reader can accept a tradeoff, clarify the instruction, or
   investigate a specific uncertainty. If no relevant decision can be named, prefer details.

Keep observed behavior, interpretation, and possible consequences separate. Consistency
across three trials does not establish importance, causation, or production frequency.
Distinguish stated plans from actual actions; inspect tool results before claiming execution.

Source intent and behavior are separate: label a difference as directly requested,
an extension beyond explicit wording, or pre-existing behavior where the evidence permits.
Owner confirmation is needed to establish whether an extension is unwanted.

## Three reference examples

These are generalized design examples informed by the saved-evidence investigation, not
bundled evaluation fixtures. Retain original traces, source snapshots, reports, participant
data, and detailed provenance privately outside the repository. Do not copy private source
excerpts into this plan. Any future committed UI preview must use synthetic content.

### 1. `tdd-from-spec`: recordkeeping and requirement-choice authority

**Change being examined:** adding a process for recording implementation deviations and
carrying that record into delivery documentation.

**Observed candidate:** the saved comparison moved from asking the user to resolve a
requirement conflict before implementation to choosing a resolution, implementing it,
and disclosing the choice afterward. The After implementations selected different
numerical policies; original tool results support local commits, not merely drafted plans.

**Decision-worthy consequence:** documentation can make a deviation visible without
establishing who was authorized to choose it. The owner should decide whether conflicting
requirements may be resolved autonomously or require a decision before implementation.

**Presentation:** visible tradeoff callout about decision authority and inconsistent
policy choices, rather than a generic warning about deviations.

**Essential qualification:** the baseline skill already encouraged autonomous progress.
The added logging may reinforce that existing rule; do not claim it newly introduced
all autonomy or contradicted the skill's overall purpose. No production harm is established.

### 2. `pr-review-response`: disclosure becomes a confirmation gate

**Change being examined:** requiring assessment disclosure before fixes so the user can
intercept misclassifications.

**Observed candidate:** After plans explicitly wait for confirmation before fixing,
whereas Before plans disclose the assessment and then name fixing as the next step.
The pattern occurs in two separate saved scenarios for the same instruction change.
The explicit disclosure requirement does not itself specify an affirmative approval gate.

**Decision-worthy consequence:** an extra gate may be useful in interactive review but
may impose an unwanted round trip in an autonomous workflow. Stalled work is a possible
consequence, not an observed result of the read-only replays.

**Presentation:** context-dependent callout. Ask whether the workflow needs the pause;
do not label the pause inherently wrong. Do not pool the two scenarios into a claim of
independent, product-wide reliability.

Illustrative callout, not an implemented report:

> **One tradeoff to consider:** After also waits for confirmation before editing. The
> instruction requires disclosure but does not explicitly require approval.
>
> **Does this workflow need that pause?** If it should continue after disclosure,
> clarify that boundary.
>
> View the compared next steps.

**Related observation:** a reference read deferred until after the checkpoint belongs in
details unless evidence shows it was omitted before the action that requires it. Checking
only Read calls can be misleading when Grep also consulted the reference.

### 3. `claude-code-review`: skepticism and the evidence threshold

**Change being examined:** adding a more skeptical review stance.

**Observed candidate:** an unchanged top-level verdict accompanies promotion of existing
concerns from nonblocking notes to blocking issues. Some additional assertions are stronger
than the supplied evidence, rather than newly discovered defects.

**Decision-worthy consequence:** the edit may change the amount of work demanded from an
author without changing the main defect found. A verdict-only comparison hides this.

**Presentation:** promote a supported change in the work demanded from the author
when it creates a meaningful reader decision, even if stricter review is intended.
Distinguish a possible risk from a demonstrated failure and account for facts
already disclosed in the scenario.

**Essential qualification:** stricter review can be intended. Escalation alone does not
establish a false positive, owner dissatisfaction, or additional actual merge refusal.

## Callout anatomy

Keep a promoted finding short and decision-shaped:

1. Simple Before/After pictures with short labels and every observed branch/count.
2. A plain consequence, without presenting plans as executed actions.
3. When the consequence matters in this workflow.
4. The decision or specific clarification available to the reader.
5. One **See why this matters** link to an added section inside **Understand the change**.

Preserve the original explanation steps. Put raw comparison links under optional
**Check the evidence** there, not directly in the attention Summary.
Do not add Other observations/Other findings or a Back to Summary button.
Distinguish assessed-empty from unavailable attention. Optional **Not relevant here**
and **Show again** controls affect only this open report and reset on reload;
they do not persist acknowledgements or remove evidence.

The detailed attention section must add understanding rather than repeat Summary
cards: reasoning beyond the consequence, exact branch counts and supporting
trial links, relevant unchanged or contrasting context with citations, and
uncertainty. Keep pictures and short action guidance in Summary. Separate model
interpretation from extracted branch evidence; do not invent missing attribution
or additional explanation to fill space.

Avoid generic warning language, speculative chains of consequences, and lists of every
difference. Do not describe an already-visible report finding as something the report missed;
the added value may be interpreting its consequence or checking its evidentiary basis.

## Later option: remember accepted tradeoffs

After relevance filtering works, consider an **Expected for this workflow** acknowledgement.
It should preserve evidence while moving an accepted finding out of the default Summary
for comparable evaluations. Re-surface it when the behavior materially changes.

Acknowledgement must be scoped to the relevant instruction/workflow and behavior; it must
not become a global mute for approval gates, correctness risks, or other categories.
Storage, comparability rules, and re-surfacing criteria are not designed here. Do not add
this mechanism merely to compensate for noisy finding selection.

## Evaluation before implementation

Use the three examples above to prepare synthetic report previews before changing the
report hierarchy, following the repository's report-presentation guidelines.

Check that a reader can:

- Answer the original behavior question without first inspecting secondary findings.
- Understand the concrete decision behind a promoted callout.
- Distinguish requested effects, additional observed effects, and hypothetical harm.
- Find unchanged behavior and trial variability without reading raw logs by default.
- Inspect lower-priority observations when needed.
- See every serious supported risk even when more than one qualifies.

Include a no-callout example and a multiple-serious-findings example. Do not tune the
policy to make every one of the three reference skills produce a warning. Treat lower
warning volume as useful only if meaningful consequences remain visible.

## Non-goals

- No automatic claim that an owner did not anticipate a behavior.
- No automatic rejection of an instruction edit because a side effect exists.
- No warning quota, composite risk score, or exhaustive anomaly list in Summary.
- No new trials, retrospective question changes, report rewrites, or implementation
  changes authorized by recording this plan.

## Related direction

[Agent-assisted evidence investigation](2026-10-06-agent-assisted-evidence-investigation.md)
addresses access to supporting evidence. This plan addresses which additional findings
should interrupt the reader in the first place.
