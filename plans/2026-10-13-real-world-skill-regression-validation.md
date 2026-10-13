# Real-world skill regression validation

Status: proposed workflow. This document does not authorize live model runs,
create tracker issues, or change the product.

## Goal

Evaluate whether Behavior Diff can help skill maintainers identify unintended
losses of existing capabilities when a skill is modified.

The central question is:

> When a modification achieves its intended improvement, can Behavior Diff also
> identify an important existing capability that the modification unintentionally
> weakens?

This is more specific than explaining a PR and narrower than promising automatic
discovery of every unknown side effect. A useful result must concern an outcome
that a user needs, not merely a different sequence of agent actions.

## Two scenario sets

Run both scenario sets against the Before and After versions of each selected
change.

| Scenario set | Purpose | Comparison question |
| --- | --- | --- |
| Existing-capability scenarios | Represent tasks the skill already needs to support | Does After still achieve the important outcomes that should be preserved? |
| Modification-target scenarios | Exercise the improvement intended by the selected PR | Does After improve the problem or add the capability that motivated the change? |

Existing-capability scenarios form a stable baseline across a sequence of changes.
They are not necessarily exhaustive. Record which capabilities they cover and
which remain untested.

An existing capability is an expected task outcome, not an exact copy of the
Before answer. Before may itself be wrong. Intentional changes to the skill's
contract must not be classified as regressions simply because behavior differs.

## Workflow

### 1. Select skills with observable, meaningful outcomes

Consider both the internal skill pool and public skill repositories. Modification
frequency provides candidate changes, but is not sufficient for selection.

Use the maintained
[Public Skill Change Stats](2026-10-13-public-skill-change-stats.md)
as the starting inventory for public candidates rather than repeating repository
discovery. Use internal skill history separately; the public inventory excludes
the private skill pool.

Treat the inventory as a prioritization aid, not a count of behavioral changes:
its PR counts come from distinct PR numbers in main-line commit subjects, and
commit counts cover changes anywhere in a skill folder. Account for the documented
rename splits, category-folder rows, and unsupported layouts. Inspect actual PR
diffs before shortlisting a change; an absent or low count is not proof of inactivity.

Prefer skills for which:

- The purpose and important task outcomes can be stated clearly.
- Representative tasks and the necessary inputs are available.
- Historical instruction versions and required dependencies can be reconstructed.
- A maintainer or informed user can judge which outcomes must be preserved.
- The execution environment can be controlled without unavailable private systems.

Start with a small set rather than scanning or running every repository. A proposed
starting point is one internal skill and one public skill, subject to suitability.
Do not assume that newer or more frequently modified skills are better cases.

### 2. Establish the existing-capability baseline

Before using candidate PR details to design tests, have an agent inspect the
pre-change skill, its relevant references, documentation, and available usage
examples. For historical work, use sources from that version rather than silently
importing current instructions.

The agent proposes representative tasks. A maintainer or user confirms:

- The capability each task exercises.
- The observable outcome that matters.
- Acceptable variations in how the agent achieves that outcome.
- Conditions under which a result is wrong or cannot be judged.

Freeze these tasks and expectations before executing comparisons. Derive them from
the skill's purpose and usage, not from a later corrective PR. Label synthetic
inputs as synthetic; real instruction history does not make a synthetic task a
historical reproduction.

### 3. Analyze PRs and shortlist candidate changes

Have an agent inspect the selected skill's relevant PRs within a declared history
window. For each candidate, record:

- The stated modification goal and its source; label inferred goals as inferred.
- The instruction, reference, or supporting-code changes involved.
- Existing capabilities that might be affected and why.
- Whether the change can be reconstructed and exercised.
- The reason for selecting or excluding it.

Prioritize changes to execution order, stopping conditions, tool permissions,
evidence sources, delegation, or task scope. These are risk hypotheses, not proof
of a side effect. Do not select solely by a later PR's fix title.

Use a complete behavior change as the comparison unit. Default to the pre-merge
and merged PR states. Use individual commits when they represent a complete,
separable change, not an unfinished intermediate state. Split mixed changes only
when the resulting comparison remains faithful to the source.

Keep the selection record, including exclusions and comparisons with no observed
problem. Risk-selected cases cannot establish an overall regression rate across
all skill modifications.

### 4. Prepare the modification-target scenarios

For each selected PR, derive tasks from its intended improvement. Define success
before seeing trial results, and confirm that the task reaches the relevant
situation without telling the trial agent how it is expected to behave.

Keep these tasks separate from the fixed existing-capability set. A target task
may become a retained capability scenario for later changes after explicit review;
do not silently rewrite the baseline to fit observed results.

### 5. Freeze the comparison and approve execution

Record the exact Before and After revisions, scenario versions, model, runtime
configuration, relevant environment, and planned trial count.

Keep the same task, model, inputs, permissions, and external conditions on both
sides. Preserve version-matched references and supporting scripts when the change
requires them. If the available runner cannot reproduce the necessary change
scope, record the limitation rather than substituting a SKILL.md-only comparison
and claiming that it represents the full PR.

Distinguish the changed source bundle from unrelated environmental differences.
Use independent trial copies and retain raw evidence. Decide repetition and retry
rules before execution; do not rerun until a desired result appears.

Obtain explicit approval for the live model scope and cost before launching runs.
Do not execute untrusted repository scripts or grant external write access merely
to make a case runnable. All live comparisons remain outside deterministic CI.

### 6. Run Behavior Diff on both scenario sets

For each selected change:

1. Run Before and After on the existing-capability scenarios.
2. Run Before and After on the modification-target scenarios.
3. Retain the reports, trial answers, tool evidence, and execution status.

Keep live artifacts outside the repository. Do not commit private reports,
transcripts, credentials, or session data.

### 7. Assess task outcomes separately from report findings

First inspect what happened in the trials against the predefined expectations.
Then determine whether the Behavior Diff report accurately identified it.

| Trial outcome | Interpretation |
| --- | --- |
| Intended improvement; tested existing capabilities preserved | Positive evidence for this change within the tested scope |
| Different behavior; required outcomes still achieved | Behavioral variation, not necessarily a harmful side effect |
| Required existing outcome worsened unexpectedly | Regression candidate requiring investigation |
| Intended improvement absent | Modification-target failure; not automatically a side effect |
| Situation not reached, unstable results, or insufficient execution evidence | Inconclusive |

A regression candidate needs evidence that the affected outcome should have been
preserved, actually worsened, and is plausibly attributable to the change rather
than uncontrolled inputs or ordinary model variation. Obtain maintainer or user
judgment where intent is ambiguous.

Separately classify the report as identifying an evidenced problem, missing an
evidenced problem, raising an unsupported concern, or being unavailable or
insufficient for assessment. A completed trial is not a correctness verdict, and
a generated report is not proof that assessment succeeded.

No triggered regression means the case does not measure whether the report would
have detected one. Report or extraction failure must not be recorded as an absence
of side effects.

## Avoid hindsight leakage

Keep two kinds of investigation distinct:

- **Detection-oriented evaluation:** freeze candidate-selection inputs, scenarios,
  expectations, and the report before consulting later corrective changes. Do not
  give trials or report analysis the hypothesized failure as an answer to find.
- **Retrospective reproduction:** use a known later correction to investigate an
  earlier problem. Label the case accordingly; reproducing a known defect is not
  evidence that it was discovered in advance.

If the investigator already knows the later correction, disclose that knowledge.
Do not call the investigation blind. A historical replay with withheld information
can support a detection hypothesis, but is not an actual prospective discovery.

## Evidence and claim boundaries

For each comparison, retain a private case record containing the source revisions,
selection rationale, scenario provenance, preserved-outcome expectations, execution
configuration, observed outcomes, report findings, and unresolved limitations.

The most relevant side-effect case has all of the following:

1. An existing outcome is independently established as important to preserve.
2. Before achieves that outcome, while After demonstrably weakens it.
3. The degradation is not an intended contract change.
4. The comparison provides evidence connecting the degradation to the modification.
5. Behavior Diff identifies the degradation without being supplied the answer.

Whether the PR's intended improvement also succeeds is a separate result. A change
can fail its target and introduce a regression at the same time.

A preserved baseline is useful scoped evidence, not proof that the skill has no
side effects. A collection of clear reports is not, by itself, evidence that users
make better decisions. Once the workflow yields credible comparisons, evaluate
whether maintainers find them useful enough to justify the additional effort and
model cost.

## Next planning decisions

Before execution, choose the initial skills and history window, confirm the
representative tasks with an informed user, and agree on model configuration,
trial counts, resource limits, and stopping rules. This plan does not preselect a
successful demo or authorize an open-ended search for one.
