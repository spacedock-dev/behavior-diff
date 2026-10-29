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

## Explain the decision in ordinary language

Write for the owner of the workflow, not the maintainer of the test tool. Apply
this to proposals, progress messages, blockers and the final answer. Lead with
what you recommend doing to the change and why, using the owner's task as the
subject. Explain what benefit was observed, what risk remains, and whether that
risk changes the recommendation. The owner must not need to open a report to
understand the decision.

Use short, natural paragraphs. Translate retain/revise/hold into a concrete action:
"keep these instructions", "change this rule", or "wait for evidence about this
behavior". Name what is on hold; a failed test is not a reason by itself to reject
the PR. Distinguish intended benefits from demonstrated benefits. Do not turn
missing evidence into reassurance.

Keep commands, trace formats, sandbox details, source mappings and diagnostic
history in linked evidence unless they change the owner's decision. Explain
technical limits by their practical consequence. Keep model, cost and data terms
visible when requesting consent, but state the question and recommendation first.
Progress messages should say what changed, whether the result is affected, and
what you are doing next; do not narrate every debugging step. Use the available
Humanizer guidance in embedded mode without installing it or changing evidence.

## Workflow

1. **Understand the change and route it without model calls.** Resolve and load
   the `behavior-diff` skill using the source-selection rule in
   [execution handoff](references/execution.md). Inspect the selected diff,
   relevant unchanged rules and available discussion. Pin revisions and source
   paths. Then settle the route with deterministic checks: fixture fit, file
   mapping, host authentication, model availability and isolation, as
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
6. **Return a decision-ready result.** Follow the explanation guidance above.
   Recommend retain, revise or hold in ordinary language, naming the change and
   the reason. Explain what improved versus Before, what stayed intact, and what
   remains uncertain in terms of the owner's workflow. Say what adopting now
   would leave unverified and whether to change the PR, wait, or leave it alone
   while verification continues. Put file mappings and report corrections in the
   linked evidence; bring any correction that changes the recommendation into
   the answer. Equal results do not prove a rule unnecessary, and simulated
   behavior does not prove real-service reliability.

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

Finish with the bounded question answered, or an evidence-backed blocker after
the execution handoff's recovery steps. A failed attempt or exhausted model-call
allowance stops further paid execution, not safe non-model diagnosis or useful
independent review. Finish that work before returning. Respect an explicit
owner instruction to stop all work.

Do not end with "fix the runner" as owner homework. Explain what the failure means
for the change, what remains unknown, what you tried, and the specific permission,
capability or unavailable fact needed next. When only new run authority is
missing, recommend a bounded check and explain what repair makes it worth trying.
Keep the run handle and private continuation context. Never bypass isolation,
invent evidence, silently narrow scope, or repeat unsuccessful attempts merely
to avoid returning a legitimate blocker.

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
