# Execution handoff

The host owns this work. Do not expose helper setup as owner homework. Resolve
Behavior Rehearsal's physical installed skill directory, following any symlink to
its actual location. Load exactly `../behavior-diff/SKILL.md` relative to that
directory: the comparison skill is a sibling in the same installed plugin.
Retain its exact physical base and version for the whole comparison. Never resolve
it from the target repository, `.agents`, the original source checkout or an older
plugin cache, and never silently mix versions. A missing sibling is a concrete
installation prerequisite to resolve or report, not permission to search for a
different copy or invent a substitute runner.

## Handoff proposal

Inspect the change first. When the goal is ambiguous, offer 2–4 distinct outcomes
tailored to it, with a recommended option and a short reason. Ordinary instruction
rehearsal uses controlled external-service simulation to check agent decisions
and safeguards. Real-output quality and live integration are separate goals; require
them only when the owner's explicit question depends on them, not from action
verbs in the production instructions. Do not require technical test design from
the owner. Skip the options for an already clear goal. Combine this clarification
with the run proposal, not a separate questionnaire.

For an invented PR adding archive checksum checks, the options could be:

1. **New checks and existing safeguards (recommended):** does the agent verify
   the archive while preserving recovery and approval before adoption?
2. **New checks:** does the agent detect a checksum mismatch and avoid accepting
   a damaged archive?
3. **Existing safeguards:** do recovery and human approval still work after
   adding checksum verification?

Explain why the recommendation fits the actual change, and let the owner name
another concern. These example options are not a fixed menu for every PR.

Before asking approval, use Behavior Diff to resolve method fit for every material
goal, including the intended new behavior and preserved safeguards. Identify the
claims the scenario will test and any material untested claims. Do not drop goals
to fit available tools or approve a broad question before discovering it requires
a different method. If an option requires unavailable real outputs, explain that
limit and recommend a concrete bounded proposal that distinguishes the behavioral
check from the unresolved real-output claim.

Then state run terms covering the recommended option. If all offered options
can share the same bounded terms, explicitly say so; otherwise identify the
differences before seeking approval. Do not promise unknown terms to avoid an
extra question. Shape the combined message like this synthetic example, replacing
every placeholder with checked facts:

```text
<Include outcome options above only when the goal needs clarification.>
I recommend <option and reason, or the owner's explicit goal>: checking whether
this change helps the agent <owner's outcome>
without losing <preserved safeguard>. I'll compare the old and new instructions
using <test situation>. External services will be simulated with controlled tool
results to check <agent decisions and safeguards>, not <real-output quality or
integration claims>. This will answer <decision question>.
<If the owner's explicit goal requires real outputs, replace the simulation
sentence with the checked real-output method and its dependencies.>
<Name every material untested claim and its consequence for this decision.>

I'll run three attempts with each version, using <preparation/trial model>,
with <named fallback and trigger>, and <assessment model and fallback or none>.
This uses <provider/account> with <cost estimate or explicit quota boundary,
including preparation, probes, retries and fallback execution>. It sends
<specified inputs and evidence> to <provider>; results stay <private location>.
Recovery is limited to <specific allowance>. These terms cover <named options>.
Do you approve? "Approve" accepts <recommended option or explicit goal> and these
run terms. To authorize another covered option, say "approve option <number>".
You can also name a different concern.
```

Name a fallback for each model role, or state that none is approved. A budget
alone never authorizes a different model.

An option number or goal correction alone selects the question, not permission
to spend quota or send data. Ask only for authorization still missing. An explicit
approval of another option can proceed without another approval when its scope,
provider, data and run limits were fully stated and covered. Otherwise present
only the changed terms for approval. If existing authority already covers the
selected goal and every run term, continue without asking again. None of these
replies authorizes adoption or merge.

## Delegate the comparison, retain the journey

Use the selected Behavior Diff skill as the single comparison recipe. It owns
input resolution, requirements and capabilities, route selection, historical
purpose, scenario and shared data, preflight, frozen inputs, existing-runner
execution, evidence audit and claim limits. Follow its linked references as
directed. Do not recreate its commands, validators, launchers or assessment rules
here. Delegation is a responsibility boundary, not a requirement to start another
coordinator or wait for the owner.

Give Behavior Diff the original question, pinned change and available context.
Use its findings to settle the proposal and continue its next applicable step
within authority. Preserve companion-file mappings and disclose the tested scope;
a single-file experiment is not automatically verification of the whole PR.
Do not edit the target change or silently test a repaired version.

The normal handoff asks whether the change helps in the supported current
environment. Use Behavior Diff's existing runner path and default host sandbox.
Do not introduce a technical mode prompt or make a custom launcher a prerequisite.
Shared settings or guidance may support a current-environment observation, not
proof that added rules alone caused it. If the owner explicitly requires stronger
isolation, follow the canonical method; an unavailable required boundary remains a
blocker. Do not weaken the host sandbox or automatically fall back to another
launcher. Historical preparation follows the canonical supplied-history freshness
requirement: a new context with reviewed contemporary inputs, not this conversation
or prior results. It does not require complete hidden-context or per-turn model
attestation unless the owner explicitly requests that stronger claim. Apply the
canonical facet-level checks rather than treating an overall unverified provenance
label as a blanket stop.

Preserve the owner's complete question when selecting capabilities. By default,
ordinary instruction rehearsal uses controlled external-service simulation under
Behavior Diff's canonical method. The production requirement to generate, inspect,
save, call a service or continue a worker does not itself require real production
tools in a decision rehearsal. Test whether the agent makes those decisions and
honors their safeguards against recorded tool results; never present simulated
results as observed real output quality, visual inspection or integration evidence.
A mention of a worker or gate alone does not make a workflow engine a dependency.

When the owner's explicit goal depends on actual outputs, inspection, saving, live
services or real worker continuation, retain those as real dependencies. Resolve
the route from repository facts and required claims, not a previous failed setup.
Distinguish claims about agent decisions from claims about execution quality and
integration before seeking consent. Keep all material untested claims visible;
do not silently narrow the goal or elevate an approved decision goal into a
real-output requirement.

## Authorization, execution and recovery

Owner approval of the handoff proposal, or a request that already authorizes
every term, supplies the bounded run approval required before Behavior Diff's
automatic-launch step. Sending the proposal is not approval. Do not treat Behavior
Diff's normal no-extra-prompt rule as overriding this boundary. Once approved,
carry execution through without another stage-by-stage permission loop. A study
answer or “accept limitations” is never run or merge authorization.

Keep the run handle and private continuation context supplied by the canonical
method. Follow its monitoring and failure-handling contract until live or
uncertain work is resolved. Tell the owner promptly if execution fails, even if a
report opened; explain the practical effect rather than treating an open report
as success.

Behavior Diff owns technical diagnosis, retry and fallback mechanics through
`references/scenario-and-test-data.md` → “Bounded execution recovery” in the
selected skill. The handoff enforces the approved allowance and named models,
costs, provider and data terms.
Before any new model-backed attempt, require remaining authority and a concrete
repair or distinct diagnostic hypothesis that can provide new information.
Preserve failures and what changed; do not repeat an unchanged failed probe.
Do not retune after a null result or present changed conditions as a replacement
for the original comparison.

Route the failed comparison step through its canonical recovery while completing
useful safe non-model diagnosis and independent review. For an approved decision
rehearsal, route a missing native production tool to a canonical supported behavioral
scenario within the approved simulation method and run terms. Do not ask for fresh
consent for an already covered route or make its setup owner homework. A missing
action record blocks the claim that depends on it, not every independent finding.
Label partial coverage as partial; do not hide untested material goals or present
partial evidence as a completed end-to-end comparison.

If an explicit real-output goal is blocked, do not silently replace it with
simulation. Finish permitted independent work, state what remains untested, and
offer a concrete bounded amended proposal: the recommended answerable question,
which original claims it would and would not cover, and only the changed method,
authority or run terms requiring approval. Preserve the original approved scope
until the owner accepts an amendment. Exhausted retry authority is not a reason
to hand setup diagnosis to the owner. Ask only for the missing authority,
capability or fact, with a recommendation and decision consequence.

Model approval is not permission for live-service effects, source edits, global
configuration writes, publication, adoption or merge. Obtain the specific
authority for any required effect before it occurs, and reuse it within its
stated bounds. Do not silently substitute simulation when a real effect is part
of the agreed question. Do not bypass a required boundary to finish a run.

## Interpretation and return

Use Behavior Diff's audited findings and claim limits rather than creating a
second competing behavioral verdict. If its evidence conflicts with a headline
or leaves a required claim unsupported, resolve that through its canonical audit
before synthesizing the recommendation. Keep independent instruction-review
findings distinguishable from observed trial behavior.

Use SKILL.md's action-first conclusion and merge-readiness rules in the first
post-verification answer. Give the recommendation without making the owner ask
whether to merge or what to do next. For a PR, independently gather relevant
normal code review, current CI results and mergeability read-only for the reviewed
head before recommending merge. If any required evidence is missing or a required
check remains unresolved, hold that decision with its specific blocker.

Explain what improved or stayed unchanged and which of the owner's actual
safeguards remained intact. State supported confidence, not guarantees. Bring
remaining uncertainty into the answer when it changes the advice; keep accurate
scope, detailed mappings, minority results, report corrections and recovery
records in linked private evidence otherwise. Do not use default simulation/E2E
disclaimers in place of a practical consequence. A process difference is not
automatically an improvement, equal trials do not establish universal redundancy,
and agent-decision evidence does not establish unobserved service behavior.
A recommendation never authorizes merge or another external effect.
Finish the review before offering optional process feedback.
