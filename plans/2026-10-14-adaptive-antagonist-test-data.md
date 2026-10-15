# Adaptive selection of antagonist test data

Status: proposed experiment, not implemented in the product. Recording this plan
is not approval to invoke models. Obtain fresh model-cost and data-sharing consent
before the planned historical evaluation.

## Question and hypothesis

Can Behavior Diff expose potential side effects at the time of an instruction
change by exploring ordinary and antagonist-designed data, then concentrating
repeat trials on the more informative dataset?

Keep the current scenario-generation method. Add a bounded test-data review, not
an exhaustive scenario suite. The hypothesis is that a risk-focused dataset can
reach behavior the ordinary dataset misses, without repeating every dataset three
times. Finding no regression is a valid result; do not tune inputs until one
appears.

This is a bounded sampling experiment related to
[real-world skill regression validation](2026-10-13-real-world-skill-regression-validation.md),
not a replacement for that broader proposal.

## Freeze preparation before execution

1. Select one instruction change and verify its exact Before and After sources.
   For a historical case, stop the available history at the first selected
   modification, not the PR's eventual final state.
2. Use the current Behavior Diff skill to derive purpose and a decision-moment
   scenario from the selected diff, commit description, and contemporaneous repo
   context. Preserve relevant task requirements without adding expected answers.
3. Prepare one ordinary synthetic dataset for that scenario.
4. Have an isolated antagonist review inspect the same sources, scenario, data,
   and actual tool contracts. Ask which legitimate input could expose an
   unintended loss of required behavior. Produce one challenge dataset with an
   explicit hypothesis, source-backed outcome criteria, and feasibility check.
5. Freeze both datasets, the task, tools and budgets, model settings, and routing
   rule below. Keep the review rationale and criteria outside trial inputs.

The task and environment are identical for both datasets. Within each dataset,
Before and After differ only in the selected instruction version. Do not increase
budgets, add tools, or strengthen the task to manufacture a failure. Admit valid
alternative implementations, including combining operations when the task and
schemas allow it. A requirement found only in a source workflow but omitted from
the supplied task cannot silently become an acceptance criterion.

Do not supply later incidents, corrective commits, prior trial results, or an
informed parent's suggested reproducer to preparation. If the orchestrator knows
the later history, use a fresh context with confined source access and memory
disabled. This controls supplied information, not pretrained model knowledge.
Case-selection hindsight must still be disclosed.

## Phase 1: explore both datasets

A comparison pair means one Before trial and one After trial on identical data.
Run one pair with ordinary data and one pair with antagonist data: four trials.

Inspect each pair's raw calls, relevant returns, and final answers. Compare Before
with After **within that dataset**, never ordinary Before with antagonist After.
A finished process or an agent's success claim is not proof of task completion.

## Routing rule

Freeze this decision before running the exploration:

- Select antagonist data if its pair shows a material Before/After difference
  worth confirming: an omitted requirement, wrong decision, changed external
  effect, or a changed operation whose consequence matters to a source-backed
  task requirement. This is a candidate signal, not yet a confirmed regression.
- Otherwise select ordinary data, even when both pairs appear unchanged. Wording,
  verbosity, incidental ordering, or a different but equivalent implementation
  alone are not sufficient reasons to select antagonist data.
- If both pairs have material differences, select antagonist data under this
  policy and retain the ordinary finding in the exploration record. This is a
  predefined tie-break, not a claim that the ordinary finding matters less.
- If a pair lacks usable execution or evidence, mark exploration inconclusive.
  Do not treat tool failures, missing inputs, or assessment failure as "no
  difference" and silently take the ordinary branch. Resolve prerequisites or
  report the blocker; additional paid attempts require fresh approval.

Save the selected dataset, evidence references, and routing reason before starting
repeat trials. Use a bounded comparison for routing; do not generate two full
reports merely to choose a dataset. Record any extra model calls used for review
or routing rather than hiding them inside the trial count.

## Phase 2: repeat only the selected dataset

Run two additional comparison pairs with the selected data, without changing the
task, inputs, tools, model, or criteria. The selected dataset then has three
Before and three After trials, including its initial exploratory pair.

Do not switch datasets after the repeats or revise data to preserve an initial
signal. If the first difference disappears, retain that minority observation and
report that it did not consistently repeat. A valid run does not need a bug.

| Allocation | Before trials | After trials | Total trials |
| --- | ---: | ---: | ---: |
| Ordinary exploration | 1 | 1 | 2 |
| Antagonist exploration | 1 | 1 | 2 |
| Two more pairs on selected data | 2 | 2 | 4 |
| Entire experiment | 4 | 4 | 8 |

Eight trials cost more than one dataset repeated three times (six trials), but
fewer than two datasets each repeated three times (twelve trials). Preparation,
antagonist review, routing, and report extraction have additional token costs.
Trial count alone does not establish token savings.

## Report and evidence

The main report presents the selected dataset's three comparison pairs. Include
a visible exploration note with the other dataset's one pair, its observations,
and why it was not selected. Link both datasets' complete evidence; do not hide a
finding because its dataset was not repeated, or pool different data as repeats.

Distinguish observed differences, their task consequences, and unresolved
questions. Missing attention assessment is not an assessed absence of concerns.
Do not edit a generated report to make its conclusion stronger. If the current
renderer cannot express the exploration note, provide a clearly separate private
companion note and label that manual presentation boundary.

Retain private manifests for exact model inputs, instruction and fixture hashes,
source revisions, preparation and routing decisions, tool schemas, raw sessions,
and actual model/token usage. No run data or transcripts belong in the repo.

## What the experiment can establish

Assess whether antagonist data reached a meaningful additional condition, whether
the routing rule selected useful evidence to repeat, and whether the candidate
consequence persisted. Also record preparation and total model cost.

A single exploratory pair can miss intermittent failures. Three adaptively
selected pairs are not an unbiased estimate of regression frequency. Matching
outcomes do not prove safety. Reproducing a later symptom with hindsight-designed
data does not establish first-change discovery.

The next evaluation should apply this protocol to the selected historical
first-change case. Verify source boundaries and execution prerequisites before
consent; keep case-specific identifiers in the private run manifest. This plan
does not change the installed skill, implement adaptive orchestration, or start
that evaluation.
