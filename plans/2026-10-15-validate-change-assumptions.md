# Validate change assumptions

Status: proposed experimental direction, not a validated product claim or a
change to the shipped workflow. This plan does not authorize model runs; obtain
fresh model-cost and data-sharing approval before each experiment.

## Goal

> We identify the intent behind a change, then use Behavior Diff to check whether
> the agent’s actual before-and-after behavior matches that intent.

Start with what the author expects the modification to accomplish. Compare that
expectation with observed behavior under the original and modified instructions.
The result may support the expectation, contradict it, support only part of it,
or leave it unassessable.

This does not require discovering an unexpected side effect. It also does not
require a failure: evidence that the intended behavior occurs is a valid outcome.
Whether that evidence changes a review decision is a separate question.

## What we want to learn

Can execution evidence help a reviewer check a change assumption that reading the
instruction diff alone does not establish?

Potential findings include:

- Before already achieves the intended outcome; After shows no improvement in
  the tested scenario.
- After follows a new step but still does not achieve the intended outcome.
- After achieves the outcome in the tested conditions, while broader claims
  remain unverified.
- The environment or evidence is insufficient to judge the intended outcome.

Record what decision the evidence could inform, such as accepting the observed
behavior, requesting a correction, narrowing a claim, or requesting further
verification. Distinguish a proposed decision from one a reviewer actually made.
Do not assume that a behavioral difference proves value beyond agent review.

## Experiment approach

1. Select a real instruction change and verify the exact Before and After
   versions, including affected references.
2. Record the intended outcome from the contemporaneous PR description, commit
   message, and diff. Separate explicit intent from inferred intent. Define what
   observable evidence would support or contradict it before running trials.
3. Use the current scenario-generation approach with only information available
   at the selected modification. Freeze the scenario, shared test data, tool
   environment, model settings, and approved trial count before execution.
4. Run Before and After with the same task and data. Change only the selected
   instruction version and its affected references. Keep assessment criteria
   outside the trial inputs.
5. Inspect actual tool calls, returned evidence, relevant artifacts, and final
   answers. Distinguish reading supplied findings from independently discovering
   them, and proposed actions from completed actions.
6. Compare the observations with the recorded intent. State the supported scope,
   remaining uncertainty, and any decision the evidence could inform. Preserve
   neutral and negative results; do not retune the case to obtain a finding.

For historical cases, exclude later fixes, incidents, and prior trial results
from preparation and execution. Use an isolated preparation context when the
orchestrator knows the later history. Disclose hindsight in case selection;
source isolation does not erase that selection bias or pretrained knowledge.

A later corrective commit can corroborate a historical problem, but cannot be
used to design a reproducer and then presented as prospective discovery.

## Evidence limits

Conclusions apply to the tested scenario, data, model, and environment. Matching
intent in a few trials does not establish correctness in all conditions. A
mismatch requires checking whether the test supplied the necessary capabilities
and evidence before attributing it to the instruction change.

Synthetic data can establish behavior on those inputs. It cannot establish live
data discovery, external effects, or real-world reliability that was not tested.
Do not treat an agent's claimed success or a completed process as outcome proof.

## Experiment log

Append future experiment summaries here. Keep raw runs, reports, transcripts,
private source material, and session data outside the repository. Entries must
be privacy-safe summaries, with public source references only where appropriate.
Do not copy private evidence into this plan.

For each experiment, record:

- **Date and change:** public reference or privacy-safe case label; comparison
  boundary and skill scope.
- **Intent and assumption:** author-stated goal, any inference, and observable
  support or contradiction criteria recorded before execution.
- **Setup:** scenario, data provenance, simulated versus real capabilities,
  model, and Before/After trial counts.
- **Observations:** what each side actually did, including variability and
  environment failures; separate observations from interpretations.
- **Assessment:** supported, contradicted, partly supported, or unassessable,
  with the exact scope and evidence limitations.
- **Decision relevance:** what the evidence adds beyond reading the diff;
  distinguish a possible review decision from an observed decision.
- **Next step:** any justified follow-up, without implying approval to run it.

No experiment results have been entered in this log yet.
