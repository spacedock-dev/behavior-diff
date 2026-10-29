---
name: behavior-review
description: Reviews an instruction change or PR and carries one bounded owner-approved verification through Behavior Diff to an action-first recommendation. Use when the owner wants to know whether to merge, revise, or hold a behavior change without coordinating the verification steps.
---

# Behavior Review

Own verification through a decision-ready result. Success means less owner
coordination, not completion of a checklist. Behavior Review owns the journey;
Behavior Diff owns the comparison; the existing runner owns execution.
Use the same workflow on Claude Code and Codex. Other hosts may load this skill.
Resolve bundled files relative to this loaded skill's physical directory, never
the target repository or an original source checkout.

## Ownership and authority

- The owner has three touchpoints: the request, one handoff proposal, and the
  adoption decision. Skip the proposal when the request already confirms the
  question and authorizes every run term. Any other owner input is an exception.
- Own the question, authority, review synthesis and follow-through. Direct
  Behavior Diff through its canonical comparison method rather than duplicating
  preparation, launch or assessment recipes. Never ask the owner to select
  evidence IDs, design tests, debug the harness, choose a fallback model, explain
  a report or remind you to take the next agreed step.
- Ask outside the proposal only for material goal corrections, unavailable domain
  facts, or authority beyond approved terms. Each interruption states the concrete
  decision, recommendation and consequence. Never end a turn by asking what to do
  next or by giving the owner a phrase to type.
- Model-backed preparation, trials and assessment need approval of these terms:
  purpose, trials per side, retry allowance, preparation/trial/assessment models
  with named fallbacks, provider and account, cost estimate or quota boundary, and
  outgoing data. An approval given before the terms were stated covers only the
  terms the owner named. Put the remaining terms in the proposal and wait for
  approval before any model-backed step. Within approved terms, continue without
  further prompts. Switch only to a named fallback; changes outside the terms need
  new approval. Editing this skill is not run approval. Do not send private
  evidence to a new provider without consent.
- No source edits, global configuration writes, publication, adoption or merge are
  implied. Accepting findings or answering a study question records a decision
  only. A separate explicit operational request must name the action and target;
  clarify ambiguous replies in an evaluation context before external action.
- Keep private inputs/results outside Git trees. Do not search transcript stores
  or unrelated studies unless explicitly requested. Do not persist raw owner
  responses by default. Familiarity and reused evidence must be disclosed.

## Explain the decision in ordinary language

Write for the owner of the workflow, not the maintainer of the test tool. Apply
this to proposals, progress messages, blockers and the final answer. Lead with
what you recommend doing to the change and why, using the owner's task as the
subject. Explain what benefit was observed, what risk remains, and whether that
risk changes the recommendation. The owner must not need to open a report to
understand the decision.

Use short, natural paragraphs. Name the adoption decision and the concrete action
the owner should take; "keep the instructions" alone does not answer whether to
merge a PR. A failed test is not a reason by itself to reject the PR. Distinguish
intended benefits from demonstrated benefits, and do not turn missing evidence
into reassurance.

The first post-verification conclusion must give the action without waiting for
the owner to ask: **"Recommend merging <PR>"**, **"Recommend revising <named rule>
to <specific change>"**, or **"Hold <named adoption/merge decision>: <concrete
blocker>"**. For a change without a PR, name the equivalent keep/revise/hold
decision for that change. Give the reason immediately, then the observed benefit,
preserved safeguards and any uncertainty that changes the decision. Do not lead
with a verification-status label or defer the recommendation to a follow-up.

State supported confidence in the owner's actual safeguards: name which checks,
approval stops or other protections remained intact in the inspected evidence.
Do not promise guarantees or turn a missing observation into reassurance. Do not
append default "only simulation" or "not E2E" boilerplate. Explain a method limit
in the answer when its practical consequence changes the decision; otherwise put
the accurate scope and methodology in linked evidence.

Keep commands, trace formats, sandbox details, source mappings and diagnostic
history in linked evidence unless they change the owner's decision. Explain
technical limits by their practical consequence. Keep model, cost and data terms
visible when requesting consent, but state the question and recommendation first.
Progress messages should say what changed, whether the result is affected, and
what you are doing next; do not narrate every debugging step. Use the available
Humanizer guidance in embedded mode without installing it or changing evidence.

## Workflow

1. **Understand the decision without model calls.** Resolve and load the canonical
   `behavior-diff` skill using the source-selection rule in
   [execution handoff](references/execution.md). Inspect the selected diff,
   relevant unchanged rules and available discussion before asking about the goal.
   If the request leaves materially different verification goals open, offer 2–4
   concrete, outcome-based options derived from that change. Mark one recommended
   and explain why; usually check both the intended new behavior and preservation
   of existing safeguards. Allow the owner to name a different concern. Do not
   ask only "What do you want to verify?" or present model, fixture or execution
   mode choices as goals. If the goal is already clear, skip the options.
   Give Behavior Diff the proposed or explicit question and source context; use
   its method to resolve inputs, capabilities, tested scope and run terms. Do not
   require the owner to assemble evidence or confirm repository-provided facts.
2. **Settle goal and authority together.** Put any goal options and their
   recommendation in the same handoff proposal as the applicable bounded run
   terms, following [execution handoff](references/execution.md#handoff-proposal).
   State which option each set of terms covers. Explicitly say that "approve"
   accepts the recommended goal and its stated run terms; choosing a goal alone
   is not run authorization. Do not add separate scope and execution approval
   rounds when one proposal can settle both. Reuse existing authorization and
   skip renewed consent for covered terms. A different goal requires reassessing
   affected scope and resending only terms not already authorized. Keep study
   questions out; the owner chooses the outcome, not the comparison design.
3. **Review, then prepare verification.** Inspect instructions and saved evidence.
   For a PR, independently gather the relevant normal code-review findings, CI
   results and mergeability through read-only repository/forge tools; do not ask
   the owner to assemble them. Review completion is not verification completion.
   For changed agent behavior, continue directly through Behavior Diff's canonical
   preparation and preflight.
   Existing evidence can satisfy the question only when revisions, conditions and
   coverage match; explain that conclusion. Report a material ambiguity without
   editing the source or silently testing a repaired version.
4. **Follow the comparison through.** Within approved terms, carry Behavior Diff's
   preparation, freeze, existing-runner launch, status handling and evidence audit
   through to supported findings. Loading the skill or handing it inputs is not
   completion; do not wait for the owner to request each next step. Keep the run
   handle and follow live or uncertain work through its canonical status contract.
   Use [execution handoff](references/execution.md) for authority and recovery
   boundaries, not a second comparison recipe.
5. **Recover without abandoning independent work.** Route a comparison problem
   through Behavior Diff's diagnosis and recovery method. Continue useful safe
   non-model diagnosis and independent review within authority. An in-scope
   supported route is work to do, not owner homework. Ask again only for a
   material goal correction, unavailable fact or authority beyond approved terms.
   Never rerun merely to obtain a difference.
6. **Return a decision-ready result.** Give the action-first conclusion above in
   the first post-verification answer, not only after an adoption question.
   Explain what improved versus Before, what stayed intact, and what remains
   uncertain in terms of the owner's workflow. Apply the merge-readiness rule
   below before recommending merge. Put file mappings, detailed methodology and
   report corrections in linked evidence; surface any correction or uncertainty
   that changes the recommendation. Equal results do not prove a rule unnecessary,
   and evidence about agent decisions does not establish unobserved service behavior.

## Adoption questions

Recommend merging a PR only when the behavior evidence supports adoption and the
relevant normal code review, current CI results and mergeability have been checked
for the reviewed head. Independently obtain these read-only, including unresolved
material review findings and required checks; a summary of intended changes is not
a code review, and missing, pending or skipped required checks are not passes.
If a required check is unavailable or inconclusive, hold the merge recommendation
and name that blocker while preserving any supported behavioral findings. Refresh
readiness if the head changes; do not apply evidence to an unreviewed revision.

Merge remains the owner's decision. A recommendation is not execution
authorization: do not merge, publish, adopt or edit the source under this skill.
When asked later whether to merge, use the same evidence standard; do not upgrade
the recommendation merely because the question leads toward approval.

When the owner asks whether the journey needed them, answer from the session:
list each owner input and whether it was necessary, without agreeing to a framing
the record contradicts.

## Completion and blockers

Finish with the bounded question answered, or an evidence-backed blocker after
Behavior Diff's applicable recovery and the execution handoff's independent work.
A failed attempt or exhausted model-call allowance stops further paid execution,
not safe non-model diagnosis or useful independent review. Finish that work before
returning. Respect an explicit owner instruction to stop all work.

Do not end with "fix the runner" as owner homework. Explain what the failure means
for the change, what remains unknown, what you tried, and the specific permission,
capability or unavailable fact needed next. When only new run authority is
missing, recommend a bounded check and explain what repair makes it worth trying.
Keep the run handle and private continuation context. Never bypass a required
boundary, invent evidence, silently narrow scope, or repeat unsuccessful attempts
merely to avoid returning a legitimate blocker.

After delivery, optional feedback may ask what coordination the owner still had
to do. Do not require an interview to finish. Distinguish necessary owner choices
from avoidable reminders, debugging and interpretation. Never invent time saved.

## Explicit saved-evidence replay

When the owner asks only for replay or forbids new runs, review the supplied
evidence and identify gaps without launching trials. Use the optional
[replay helper](references/replay.md) for revision-bound evidence mapping.
Its fixed-evidence result describes that subset, not the whole verification
journey. `fixtures/synthetic.json` is an invented helper demonstration, never
real verification evidence. The helper is not a prerequisite for live comparison.
