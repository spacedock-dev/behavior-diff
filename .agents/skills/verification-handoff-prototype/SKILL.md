---
name: verification-handoff-prototype
description: Carries an instruction change from owner-confirmed goals through review and authorized Behavior Diff verification to a decision-ready recommendation. Use when the owner wants to hand off verification of a change or PR without coordinating the agent's next steps.
---

# Verification handoff prototype

Own verification through a decision-ready result. Success means less owner
coordination, not completion of a checklist. This maintainer skill orchestrates
Behavior Diff; it does not replace its preparation, runner or evidence contracts.
Use the same workflow on Claude Code and Codex. OMP may load this source explicitly.
Resolve bundled files relative to this loaded skill, never the target repository.

## Ownership and authority

- Own discovery, planning, tool selection, preflight, execution, bounded recovery
  and interpretation. Never ask the owner to select evidence IDs, design tests,
  debug the harness or remind you to take the next agreed step.
- Ask only for material goal corrections, unavailable domain facts, or missing
  authority. Each interruption states the concrete decision, recommendation and
  consequence. Continue useful independent work while awaiting that answer.
- Before paid trials, obtain approval covering purpose, trial count, model/provider,
  cost estimate or explicit budget, and outgoing data. Reuse approval within that
  scope; changes to scope or budget need new approval. Editing this skill is not
  run approval. Do not send private evidence to a new provider without consent.
- No source edits, global configuration writes, publication, adoption or merge are
  implied. Accepting findings or answering a study question records a decision
  only. A separate explicit operational request must name the action and target;
  clarify ambiguous replies in an evaluation context before external action.
- Keep private inputs/results outside Git trees. Do not search transcript stores
  or unrelated studies unless explicitly requested. Do not persist raw owner
  responses by default. Familiarity and reused evidence must be disclosed.

## Workflow

1. **Understand the change.** Inspect the selected diff, relevant unchanged rules
   and available discussion. Pin revisions and source paths; prepare historical
   inputs through Behavior Diff's supported provenance and isolation procedure.
   Do not require the owner to assemble an evidence packet.
2. **Confirm the question once.** Propose concise intended outcomes, preserved
   requirements and bounded scope with explicit/inferred sources. Distinguish
   added rule value from reliability in the owner's current environment. Reuse
   prior confirmation; ask only about material uncertainty. Keep study questions
   out of this gate. Goal corrections require reassessing affected evidence.
3. **Review, then prepare verification.** Inspect instructions and saved evidence.
   Review completion is not verification completion. For changed agent behavior,
   proceed directly to preparing a Behavior Diff comparison; do not wait for
   “now run Behavior Diff.” Existing evidence can satisfy the question only when
   revisions, conditions and coverage match; explain that conclusion. Report a
   material ambiguity without editing the source or silently testing a repaired
   version. Preserve the agreed question unless the owner explicitly changes it.
4. **Preflight before spending.** Load the available `behavior-diff` skill and
   follow [execution handoff](references/execution.md). Own fixture preparation,
   host compatibility, scenario reach and confound checks. Present any missing
   run authorization as one concrete bounded proposal, not an open-ended menu.
5. **Run and assess.** Once preflight and authorization are satisfied, launch and
   follow through to raw actions, returns and artifacts. Separate setup failures,
   missed cases and unavailable assessment from behavioral failures. Recover
   within the approved boundary; never rerun merely to obtain a difference.
6. **Return a decision-ready result.** Lead with retain/revise/hold and why. State
   what changed versus Before, what stayed intact, what remains unknown, and
   whether additional instructions showed added value. Link inspectable evidence
   after the conclusion. Equal outcomes mean no observed added benefit under
   these conditions, not proof that a rule is universally unnecessary. Simulated
   behavior does not prove real-service reliability. Do not wait for the owner
   to ask what the report means. Do not merge.

## Completion and blockers

Finish with the bounded question answered, or an evidence-backed blocker naming
what failed, what was tried, what remains unverified and the smallest recommended
resolution. Missing capability is not permission to fake a worker or shrink scope.
An intermediate review, helper result or successful process exit is not completion.
Keep the exact run handle and private continuation context for interrupted work.

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
