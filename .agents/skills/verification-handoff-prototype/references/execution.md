# Execution handoff

The host owns this work. Do not expose helper setup as owner homework. Resolve
this handoff skill's physical location before choosing Behavior Diff. If it
belongs to a Behavior Diff source checkout, load that checkout's canonical
`plugin/skills/behavior-diff` source, even when the reviewed project is elsewhere.
Otherwise load the discovered installed Behavior Diff skill. Retain its exact
base and version for the whole comparison; never silently mix versions.
Missing tooling is a concrete prerequisite to resolve or report, not permission
to invent a substitute runner.

## Handoff proposal

Explain what the owner will learn before listing run terms. Use one message
shaped like this synthetic example; replace every placeholder with checked facts:

```text
I recommend checking whether this change helps the agent <owner's outcome>
without <preserved risk>. I'll compare the old and new instructions using
<test situation>. This will tell us <decision behavior>, but won't establish
<live-service reliability or other excluded claim>.

I'll run three attempts with each version, using <preparation/trial model>,
with <named fallback and trigger>, and <assessment model and fallback or none>.
This uses <provider/account> with <cost estimate or explicit quota boundary,
including preparation, probes, retries and fallback execution>. It sends
<specified inputs and evidence> to <provider>; results stay <private location>.
Recovery is limited to <specific allowance>. Do you approve this comparison?
```

Name a fallback for each model role, or state that none is approved. A budget
alone never authorizes a different model.

## Prepare a meaningful comparison

- Follow Behavior Diff's historical source isolation, purpose derivation, scenario
  preparation, freeze and launch contracts. Keep this conversation's review
  conclusions and prior results out of a fresh historical scenario preparer's
  context. Current review goals never rewrite historical experimental intent.
- For a PR, prepare supported Before/After file inputs or isolated replay fixtures
  from pinned revisions. Preserve companion-file mappings and disclose the tested
  scope. Never flatten a multi-file change into an unsupported whole-PR claim.
- State privately what observation would distinguish added value, preservation,
  regression and insufficient evidence. Inspect existing requirements first;
  Before may already require the desired behavior. Do not weaken Before.
- Use neutral tasks and sufficient shared data. Do not supply the new instruction
  as a task hint. Verify that each planned case can reach its decision point;
  an earlier approval stop can make a later case unreachable. Do not bypass a
  preserved approval gate to force coverage.

## Route by the behavior that must execute

Distinguish an application's runbook decisions from actual workflow-engine state
or inter-agent handoffs. Decide from the target repository, not from words in its
instructions: a workflow engine is under test only when the repository contains
its source, configuration or state, or the owner says it runs one. A mention of a
worker, gate or Spacedock is not evidence that a Go project is needed. When
Behavior Diff directs you to its Spacedock reference, inspect the rule and fixture
prerequisites before invoking its builder. Do not apply a source-repository
fixture to an unrelated application repository.

If the repository does not run the engine, the ordinary-agent decision comparison
is the correct route, not a narrowed scope; propose it without first reporting a
blocker. If the repository does run it and the loaded skill's fixture cannot
represent the requested behavior, report that contract/capability mismatch with a
recommended resolution. Do not replace a real worker handoff with a scripted
reply; narrowing away a real handoff requires owner approval. Do not ask the owner
to diagnose the mismatch.

A multi-file change must keep its file mapping. If the runner accepts only one
target, a combined file is a disclosed test construction: state it in the
proposal and result, and do not present it as the repository layout.

Choose capabilities from the question, not from a previous failed setup. For a
question about agent decisions, a disclosed local service simulation may be
sufficient; real image generation is not automatically a prerequisite for testing
whether the agent requests a cover and waits for approval. If the question includes
image quality, actual saving, live services or real worker continuation, preserve
those requirements. After scope is approved, changing the evidence method in a way
that loses a required claim needs owner approval. Complete independent checks
where possible without presenting partial coverage as the full comparison.

## Check compatibility and confounds before launch

Inspect effective subprocess settings, not just the interactive session's model.
Check host/model compatibility, available tool semantics, authentication and
output locations without printing secrets. Use documented process-local settings
and disposable locations; do not change the owner's global configuration,
permissions, trust entries or memory. Check automatic host writes too. If the host
cannot respect that boundary, stop before launching and explain the prerequisite.

For incremental rule value, isolate unrelated memory and instruction injection
and prevent direct tool reads of those sources. For current-environment reliability,
keep the intended environment equal across variants and disclose shared guidance.
Prefer the isolated comparison for a question about whether added rules help;
do not make the owner discover this distinction after seeing results. Record the
boundary and verify it with harmless probes. Disabling injection alone is not
filesystem isolation. Any model-backed probe belongs in the approved run budget.
Do not claim complete isolation if a relevant channel cannot be checked.

Run the fresh historical preparer as a host subprocess with its own isolated
context. Use an in-session subagent only when the host verifiably gives it no
injected session memory. For macOS Codex decision comparisons, use the bundled
`codex_isolated.py` launcher described in Behavior Diff's
`references/scenario-and-test-data.md`. Do not reuse an old private launcher or
write a new wrapper. Use one selected Behavior Diff version for preparation and
trials; an older installation without the helper is a version prerequisite, not
evidence that the repository needs Go or live image generation.

The helper uses one outer sandbox and checks its file-access boundary before
starting Codex. It isolates the host home and temporarily copies existing sign-in
credentials, so disclose that in the proposal. It cleans up the temporary runtime
on completion or a handled interruption. Never print credentials or change global
host settings. If the host cannot start the helper's sandbox, preserve its error;
use the host's explicit permission mechanism when allowed, not an unconfined
fallback. A sandbox failure is about that execution environment, not the PR.

The supported evidence path is Codex shell commands, command returns and workspace
artifacts. Use local adapters for approved decision simulations. Missing native
image-tool events do not establish that shell actions cannot be recorded.
Do not require real artwork saving for a decision-only question. If the approved
question requires actual image generation, inspection or a real service, those
capabilities remain separate preflight requirements; never silently simulate them.
File existence establishes an artifact, not that the agent inspected it.

On other hosts, use their documented isolation rather than claiming this macOS
helper applies. If no supported path can preserve the required boundary, report
that limitation and finish independent checks. A model-backed capability probe
still requires explicit authorization; non-model checks do not prove agent
compliance or live-service reliability.

Follow Behavior Diff's preflight and frozen-handoff helpers rather than rebuilding
their validators. Simulation checks prove the fixture's mechanics, not that a
real website or workflow engine works. Run a real-service check only with its
specific authorization; do not replace the agreed question with a simulation.

## Authorization, execution and recovery

Owner approval of the handoff proposal, or a request that already authorizes
every term, supplies the bounded run approval required before Behavior Diff's
automatic-launch step. Sending the proposal is not approval. Do not treat Behavior
Diff's normal no-extra-prompt rule as overriding this boundary. Once approved,
carry execution through without another stage-by-stage permission loop. A study
answer or “accept limitations” is never run or merge authorization.

Keep the printed run handle, frozen inputs, exact host/model settings and failed
attempts. In the launch message, say that the runner opens its report by itself
when the run ends. Check status right after launch and keep monitoring while the
run or any trial is live or uncertain (`pending`, `preparing`, `running`,
`normalizing`, `uncertain`); zero completed trials in those states is normal, not
a failure. When the run ends or its runner is lost (`owner_lost`) with any trial
not `finished`, tell the owner at once, even if the report is already open, and
name each failed phase or trial state that status reports. Say that no model ran
only when startup errors and empty native traces show it; a failure during
normalization can follow model output. Preserve that run, diagnose its
outputs, and relaunch only within the retry allowance. Repair routine local setup
without editing the target change or global settings. On rate limiting or model
unavailability, retry once, then switch to the named fallback and record the
switch; never idle on repeated failures. A fallback switch relaunches the whole
comparison on one model, does not consume the startup retry, and is a new
comparison rather than a mix of models. Without a named fallback, send one
bounded proposal. Do not retune after a null result. A changed scenario or
isolation condition is a new comparison, not a replacement result.
When an attempt fails, separate the affected capability from the rest of the
question. Inspect the failed phase and native evidence; continue safe non-model
diagnosis and independent review within the existing authority. Before another
paid attempt, make a concrete in-scope local repair or state a distinct diagnostic
hypothesis and what the probe would distinguish. In either case, require remaining
authorization and perform applicable non-model checks first. Preserve original
failures and record exactly what changed. Do not repeat an unchanged failed probe.

A missing action record blocks claims about that action, not every possible
finding. Inspect supported recording and artifact sources without treating an
agent's final answer as proof of execution. If required evidence cannot be
captured, stop that comparison rather than spending the remaining trial budget
on unassessable runs. Report available findings as partial.

Exhausted probe/retry authority does not require the owner to diagnose the setup.
Finish permitted non-model work, then request only the missing authority with
the repair, expected information and bounded cost. If no safe repair or supported
route exists, explain the remaining capability gap and its decision consequence.
Do not run indefinitely, weaken isolation, or change the approved question.

## Interpretation and return

Audit raw actions, returns and artifacts for each case, including minority results.
If automated assessment is rejected, retain the report and distinguish a documented
raw-evidence assessment from the unavailable automated result. Never re-label it
as an automatic pass. Distinguish rule effects from pre-existing instructions,
shared memory, task hints and environment failures. Check the generated headline
against raw decisions; a wording difference is not a changed outcome. Correct it
in your assessment without editing the report.

Use SKILL.md's ordinary-language decision guidance for the owner-facing answer.
Keep the full goal-by-goal audit, source mapping, minority results, report
corrections and recovery record in linked private evidence. State any limitation
that affects adoption in the answer itself. Recommend retain/revise/hold at the
tested scope; never merge or turn that result into a merge recommendation.
A process change without an outcome change is not automatically an improvement.
Do not infer universal redundancy from equal trials or promise live reliability.
Finish the handoff before offering optional process feedback.
