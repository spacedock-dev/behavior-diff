# Behavior Diff: progress and product review

Status: project summary with independent antagonist-review corrections incorporated.
A pause in feature development is under consideration, not recorded here as a
finalized decision. This document does not authorize implementation, experiments,
publication, or changes to project status.

## Summary

Behavior Diff has demonstrated an executable method for rehearsing instruction
changes. The evidence reviewed for this summary does not establish whether its
packaged workflow provides enough additional value over asking an agent to perform
the same method directly. That question remains unresolved, not disproved.

Older evaluation results were not comprehensively reviewed for this summary.
Absence of comparative evidence in this review is not a finding that no relevant
historical evidence exists.

## Original goal

Help a user understand the consequences of changing an agent's instructions:

- Does the agent follow the new instruction?
- Does it preserve behavior the user already relies on?
- Does the change introduce unwanted side effects?
- Should the user adopt or merge it?

The method runs the same task against Before and After instructions and examines
observed behavior rather than relying only on a review of the instruction text.
Controlled simulation can examine decisions and approval boundaries without
repeatedly performing expensive, inconvenient, or irreversible external actions.
It does not establish the quality or reliability of an untested real service.

## What was built

| Area | Implemented capability |
|---|---|
| Plugin | Claude Code and Codex installation, instruction-edit detection, and comparison entry points |
| Comparisons | Separate Before/After workspaces, shared inputs, repeated trials, and concurrent execution |
| Preparation | Scenarios and data derived from intended changes and behavior to preserve |
| Evidence | Recorded actions, tool returns, outputs, source revisions, frozen inputs, and validation |
| Analysis | Model-assisted behavior assessment and locally generated HTML, Markdown, and structured JSON |
| Operations | Progress monitoring, failure records, deterministic tests, release automation, and marketplace publication |
| Guided journey | `behavior-rehearse`, covering review, preparation, execution, recovery, and recommendations |

The script-backed `behavior-diff` workflow and agent-driven `behavior-diff-live`
workflow remain distinct approaches. `behavior-rehearse` provides a guided entry
point, not a separate comparison engine. The latest release completed in the
reviewed work was v0.4.13.

## How the product evolved

### From showing differences to answering a decision

Report iterations moved toward observed behavior, intended outcomes, preserved
safeguards, and accessible supporting evidence. They distinguished unchanged
behavior from insufficient evidence and aimed to make conclusions understandable
without requiring the reader to inspect every trace.

Human-evaluation tooling was also built: blind comprehension quizzes, hosted
packages, and response analysis. The existence of this tooling is not itself
proof of usability or comparative product value.

### From a comparison tool to an agent-owned journey

The verification-handoff prototype evolved into `behavior-review`, then
`behavior-rehearse`. Its intended experience is:

1. Understand the verification goal, offering concrete options when needed.
2. Establish the necessary bounded approval and reuse it within its scope.
3. Review the change and execute the comparison without stage-by-stage reminders.
4. Handle recoverable problems without making setup the user's responsibility.
5. Return an action-first recommendation, with decision-relevant risks visible
   and detailed evidence available separately.

A recommendation does not authorize a merge or another external action.

## Findings from the reviewed walkthroughs

There was positive feedback that a guided journey fit the intended goal, although
it still required more approvals than desired. In these walkthroughs, the user
prioritized an actionable recommendation over reading a report. These are bounded
observations, not findings about all users or evidence of broader demand.

The walkthroughs also exposed recurring friction:

- Refusing simulation because a production tool was unavailable.
- Inferring unnecessary workflow-engine dependencies.
- Refusing valid historical PR comparisons.
- Requiring the user to coordinate stages the agent should own.
- Explaining technical limitations without giving a clear action.
- Failing to start preparation or complete permission recovery.
- Producing assessment citations that required additional raw-evidence auditing.

Several refusal, preparation-evidence, and workflow problems were corrected.
Subsequent startup problems showed that consistent hands-off operation remained
unestablished. A failed launch is not evidence that the compared instruction
change causes bad behavior.

## What the evidence supports

A reviewed fresh coordinator completed preparation, repeated Before/After trials,
assessment, raw-evidence audit, and a final recommendation without parent
intervention. Trial processes finished with successful exit codes. This establishes
execution completion, not that every desired behavioral outcome passed.

Some automated checks were rejected and required inspection of raw evidence.
Rejected assessments are not automatically behavioral failures, and manual auditing
does not turn the original automated assessment into an all-checks-passed result.

The reviewed successful journey also exposed substantial preparation cost. The
agent generated and validated case-specific simulation machinery, while the trial
workers already ran concurrently. This is a measured case, not a general latency
benchmark. Proposed speed improvements were evaluated conceptually; that discussion
did not implement or demonstrate a performance improvement.

## Product question and comparator

The reported product objection is that a user could ask an existing agent to
follow the same concept instead of using a dedicated product. The underlying
stakeholder discussion was not reviewed directly; no fuller rationale is attributed
to its participants here.

The comparator needs a definition. Asking an agent to comment on instructions is
not equivalent to asking it to execute controlled Before/After trials and audit
the resulting evidence. The relevant alternative should include the work and
oversight required to perform the same rehearsal.

Keep three questions separate:

| Level | Question |
|---|---|
| Method | Can behavioral rehearsal reveal useful differences? |
| Implementation | Can the plugin execute that method reliably and efficiently? |
| Guided journey | Does the packaged experience improve the user's decision enough to justify its cost? |

Behavior Diff provides concrete mechanisms beyond a prompt, including snapshots,
frozen inputs, repeated trials, evidence validation, and persistent reports. Those
mechanisms are not, by themselves, proof of user value. Conversely, an agent's
ability to reproduce the concept is not proof of an equivalent user experience.

The reviewed record contains observed costs for Behavior Diff but no matched
measurement of the direct-agent alternative's cost and reliability. It therefore
supports uncertainty, not a demonstrated preference for either approach.

## Independent mentor review

An independent antagonist review requested corrections to the initial summary:

- Bound comparative-value claims to the evidence actually reviewed.
- Include positive feedback without generalizing one user's preferences.
- Separate advice to pause from an evidentiary conclusion or finalized decision.
- Define the unresolved comparator and avoid inferring a stakeholder's full view.
- Distinguish trial-process completion from passing behavioral outcomes.

Those corrections were incorporated and the revised wording was approved. The
approval concerns accuracy and balance, not product validation or a decision to
pause development.

## Strategic interpretation

A reversible pause in feature development is a reasonable resource-allocation
option while comparative value remains unresolved. It is not the only sensible
choice established by this record, nor proof that the product lacks value.

Preserving the released implementation, existing evaluations, and open product
question would retain the ability to revisit that choice. This summary does not
require a new study or prescribe additional development.

If work resumes, the rationale should identify the user benefit being pursued
and the evidence relevant to it. A matched comparison with an agent performing
the same method could be informative; another successful Behavior Diff run alone
would not settle differentiation. This is advice, not a mandatory restart gate.

## Privacy

This record omits personal names, private project identities, session identifiers,
local filesystem paths, private links, transcript excerpts, and raw run artifacts.
Findings are paraphrased and limited to what is needed for the product review.
