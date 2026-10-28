# Execution handoff

The host owns this work. Do not expose helper setup as owner homework. Load the
available Behavior Diff skill once and retain its exact base and version. In a
Behavior Diff development checkout, use its canonical `plugin/skills/behavior-diff`
source; elsewhere use the discovered installed skill. Never silently mix versions.
Missing tooling is a concrete prerequisite to resolve or report, not permission
to invent a substitute runner.

## Handoff proposal

Settle the route before writing the proposal, so it does not stop on a fixture
question the repository already answers. Use one message shaped like this
synthetic example:

```text
Question: does the change make the agent <intended outcomes> while keeping
<preserved requirements>? Route: ordinary-agent Before/After comparison of
<mapped files> against a local simulated <service>. Not tested: <live services>.
Run: 3 Before + 3 After trials, at most one startup retry. Models:
preparation and trials <primary>, or <fallback> if <primary> is rate limited
or unavailable; assessment <assessment model>, no fallback approved.
Provider/account: <host, sign-in type>. Cost/quota: <estimate or boundary,
including one fallback relaunch>.
Outgoing data: pinned instruction files and fixture data to <provider>; no new
provider.
Recommendation: approve as proposed.
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
injected session memory. If Behavior Diff provides no isolation for the host, use
a disposable launcher in the private run root, for example a wrapper first on
`PATH` that applies process-local flags disabling memory and plugins and denies
reads of memory stores and the original checkout. Prefer the host's existing
sign-in. If a private host home is unavoidable, disclose it in the proposal, keep
any credential copy mode 0600 inside the mode-0700 run root, never print it, and
delete it when the run ends or is interrupted. Verify the launcher with harmless
non-model probes before model use, keep it with the evidence, and record it in
the result. Never change the owner's global host settings instead.

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
Stop repeated unsuccessful recovery with a concrete blocker.

## Interpretation and return

Audit raw actions, returns and artifacts for each case, including minority results.
If automated assessment is rejected, retain the report and distinguish a documented
raw-evidence assessment from the unavailable automated result. Never re-label it
as an automatic pass. Distinguish rule effects from pre-existing instructions,
shared memory, task hints and environment failures. Check the generated headline
against raw decisions; a wording difference is not a changed outcome. Correct it
in your assessment without editing the report.

Deliver the recommendation without requiring “what does the report mean?”:
what question was tested; added benefit observed or not demonstrated; regressions
and preserved behavior; decisive evidence; unresolved scope and its decision impact.
A process change without an outcome change is not automatically an improvement.
Recommend retain/revise/hold at the tested scope; never merge, and do not turn
that result into a merge recommendation. Do not infer universal redundancy from
a few equal trials or promise the next real run will succeed. Finish the
verification handoff before offering optional process feedback; never operate the
PR in response to that feedback.
