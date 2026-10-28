---
name: verification-handoff-prototype
description: Carries an instruction change from one owner-approved handoff proposal through review and Behavior Diff verification to a decision-ready recommendation. Use when the owner wants to hand off verification of a change or PR without coordinating the agent's next steps.
---

# Verification handoff prototype

Own verification through a decision-ready result. Success means less owner
coordination, not completion of a checklist. This maintainer skill orchestrates
Behavior Diff; it does not replace its preparation, runner or evidence contracts.
Use the same workflow on Claude Code and Codex. OMP may load this source explicitly.
Resolve bundled files relative to this loaded skill, never the target repository.

## Ownership and authority

- The owner has three touchpoints: the request, one handoff proposal, and the
  adoption decision. Skip the proposal when the request already confirms the
  question and authorizes every run term. Any other owner input is an exception.
- Own discovery, planning, tool selection, preflight, execution, bounded recovery
  and interpretation. Never ask the owner to select evidence IDs, design tests,
  debug the harness, choose a fallback model, ask what a report means or remind
  you to take the next agreed step.
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

## Workflow

1. **Understand the change and route it without model calls.** Load the
   available `behavior-diff` skill. Inspect the selected diff, relevant unchanged
   rules and available discussion. Pin revisions and source paths. Then settle the
   route with deterministic checks: fixture fit, file mapping, host
   authentication, model availability and isolation, as
   [execution handoff](references/execution.md) describes. Do not require the
   owner to assemble an evidence packet or confirm a route the repository answers.
2. **Send one handoff proposal.** In one message, propose the intended outcomes,
   preserved requirements, tested scope and route, plus the run terms above, with
   explicit/inferred sources and a recommendation. Distinguish added rule value
   from reliability in the owner's current environment. Keep study questions out.
   Reuse confirmation and authorization already given. A goal correction requires
   reassessing affected evidence and resending only the changed terms.
3. **Review, then prepare verification.** Inspect instructions and saved evidence.
   Review completion is not verification completion. For changed agent behavior,
   proceed directly to preparing the Behavior Diff comparison. Existing evidence
   can satisfy the question only when revisions, conditions and coverage match;
   explain that conclusion. Report a material ambiguity without editing the source
   or silently testing a repaired version. Keep the agreed question.
4. **Preflight before spending.** Follow the execution handoff. Own fixture
   preparation, host compatibility, isolation, scenario reach and confound checks.
   A blocker with an in-scope route is work to do, not a stopping point. Ask again
   only when preflight needs terms outside the approval.
5. **Run and assess.** After approval, launch and follow through to raw actions,
   returns and artifacts. Monitor status after each launch and handle failed runs
   as the execution handoff describes. Separate setup failures, missed cases and
   unavailable assessment from behavioral failures. Never rerun merely to obtain
   a difference.
6. **Return a decision-ready result.** Lead with retain, revise or hold and why.
   State what changed versus Before, what stayed intact, what remains unknown, and
   whether additional instructions showed added value. Disclose how files were
   mapped and any generated-report claim you corrected. Link inspectable evidence
   after the conclusion. Equal outcomes mean no observed added benefit under
   these conditions, not proof that a rule is universally unnecessary. Simulated
   behavior does not prove real-service reliability. Do not wait for the owner
   to ask what the report means.

## Adoption questions

Merge is the owner's decision, not a verification outcome. When asked whether to
merge, restate the retain/revise/hold result and name the merge-readiness checks
that did and did not run, such as code review, CI and mergeability. A summary of
intended changes is not a code review. Do not upgrade the recommendation under a
leading question. Do not merge.

When the owner asks whether the journey needed them, answer from the session:
list each owner input and whether it was necessary, without agreeing to a framing
the record contradicts.

## Completion and blockers

Finish with the bounded question answered, or an evidence-backed blocker naming
what failed, what was tried, what remains unverified and the smallest recommended
resolution. Stop only when no in-scope route exists. Missing capability is not
permission to fake a worker or shrink scope. An intermediate review, helper
result or successful process exit is not completion. Keep the exact run handle
and private continuation context for interrupted work.

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
