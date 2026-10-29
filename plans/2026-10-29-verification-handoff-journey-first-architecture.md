# Verification handoff: prove the journey before refining the architecture

Status: proposal for discussion. The ownership principle below is agreed; the
implementation sequence and design details are proposed, not approved changes.
This document authorizes no code removal, model calls, publication, or merge.

For an illustrated, plain-language introduction, open
[One question. Three clear jobs.](../docs/verification-handoff-explained.html).

## 1. Decision and priority

> The handoff owns the journey. Behavior Diff owns the comparison. The existing
> runner owns execution.

**First prove that a user can hand over a real instruction-change question and
receive an understandable, evidence-backed recommendation without managing the
steps. Refine the internal architecture after observing that journey.**

Recommend direct composition of the existing skills and runner for that first
check. Do not make a new launcher, coordinator, API, or pipeline refactor a
prerequisite. A clean diagram is not evidence that the experience works.

The sequence is:

1. Agree on the intended user journey and its evidence requirements on paper.
2. Approve only the minimum changes needed to exercise that journey.
3. Run one authorized, real end-to-end verification journey.
4. Discuss the observed gaps, including owner coordination and explanation quality.
5. Refine responsibilities or add machinery only where those gaps justify it.

One walkthrough can establish that the path completed under those conditions.
It cannot establish repeatable reliability, faster execution, or support on all
hosts. Those require separate evidence, not a larger first implementation.

## 2. What is wrong with the present direction?

The existing components already contain most of the needed behavior:

- The handoff skill owns the owner's question, authorization, follow-through,
  and a decision-ready recommendation.
- The canonical Behavior Diff skill owns purpose, scenarios, shared data,
  comparison settings, frozen inputs, and evidence interpretation.
- `behavior-diff.sh` owns comparison execution; `run-trial.sh` launches fresh
  trial processes and normalizes their events. Existing posttrial code produces
  analysis and reports.

The boundary is unclear because the handoff also specifies detailed comparison
preparation, environment isolation, host launch choices, and raw-evidence audits.
Two sets of instructions can therefore decide what must happen before a run.
Putting another layer in charge of satisfying those prerequisites increases the
number of ways the journey can stop.

The current working tree additionally contains an experimental macOS Codex
launcher, opt-in environment settings, frozen-setting checks, tests, and related
instructions. It introduces a custom sandbox policy, temporary sign-in copying,
and an exact CLI-version prerequisite. Local mechanical checks do not establish
that this layer is necessary for the user's question or that the complete
handoff works.

This proposal does **not** remove those changes. It proposes keeping that path
out of the first journey candidate, subject to the boundary review in section 7.
The experiment must not silently remain a mandatory handoff prerequisite.

## 3. The user journey we want

### Starting point

Use the existing privately identified application-PR case for continuity. Keep
its identity, input snapshots, session evidence, and results outside this
repository. The example dialogue below is synthetic, not a transcript.

The owner asks:

> Check whether the instruction changes in this PR improve the workflow, and
> tell me what I should do with the change.

The agent should not require an evidence packet, a test scenario, a selected
runner, or instructions to proceed after each phase.

### A. Understand the decision

The handoff identifies the requested change and what decision the owner needs to
make. Behavior Diff resolves the comparison inputs and checks which behaviors
can be evaluated. Existing repository and PR information should answer routine
questions without asking the owner to repeat it.

The agent distinguishes decisions made by an application agent from actual
workflow-engine execution. Mentioning a worker or gate does not create a Go or
Spacedock dependency. An external service is required only when the agreed
question depends on that service actually working.

For a multi-file PR, the tested file mapping and coverage must be explicit. A
single-file experiment is not automatically verification of the whole PR.

### B. Settle authority once, when necessary

If the request already authorizes the question, data disclosure, model use,
trial count, cost or quota boundary, and recovery allowance, continue. Do not ask
for a ceremonial "approve to run."

If authority is incomplete, the handoff presents one compact proposal that says
what the owner will learn, the important limit, and the missing run terms.
Behavior Diff supplies the comparison-specific terms. The handoff communicates
them; it does not ask the user to design them.

This preserves consent rather than promising zero prompts under all conditions.
No phase-by-phase approval is needed within the agreed terms. New provider/data
exposure, greater cost, a changed question, or an external action still needs
its own authority.

### C. Prepare and execute without owner coordination

Behavior Diff prepares the comparison through its existing method:

- Pin the relevant versions and preserve the surrounding common context.
- Derive purpose from the permitted source context, not desired results.
- Prepare a neutral task, sufficient shared data, and private criteria.
- Check that the scenario reaches the behavior being evaluated.
- Check required host capabilities and freeze/verify the inputs.
- Invoke the existing trusted runner path.

The runner creates Before/After workspaces, launches trials, records statuses
and raw evidence, normalizes events, and invokes its existing posttrial work.
The default is three trials per side, not a new count chosen by this proposal.

The handoff remains responsible for following the journey to completion, but
does not construct a second command recipe or launch trials individually.
Behavior Diff interprets run status and evidence through its existing contracts.
There is no new status writer, polling subsystem, or user-facing execution mode.

### D. Handle a problem without abandoning unrelated work

A failure is routed to the component that owns it:

- A scenario that cannot reach the decision belongs to Behavior Diff.
- A host startup or event-recording failure belongs to the execution path.
- A missing decision, permission, or domain fact belongs to the handoff.

The handoff coordinates the response using that component's evidence. It does
not invent replacement execution infrastructure. A new model attempt needs both
remaining authority and a concrete reason it could provide new information.

A missing native image tool does not block a decision-only comparison that uses
an agreed simulation. It does block a claim about actual image production or
inspection when those are required. A missing action record blocks the claim
that depends on that record, not every independent review finding.

Safe non-model diagnosis and independent review continue where useful. Partial
work remains labeled partial; it is not a successful end-to-end comparison.

### E. Explain the decision, not the machinery

Behavior Diff returns the supported findings and their limits. The handoff
combines them with the change review and answers the owner's original question.
It does not create a second competing behavioral verdict.

The owner-facing answer should make these points understandable without opening
a report:

1. Keep the instructions, change a particular rule, or wait for specific evidence.
2. What changed in observed behavior, including an honest unchanged result.
3. What important behavior was preserved, regressed, or not established.
4. What adopting now would leave uncertain and whether that changes the advice.

Commands, traces, file mappings, and failure diagnostics belong in linked private
evidence unless they change the decision. Do not claim time saved without
measurement. Do not ask the owner to explain the report or tell the agent to
finish interpreting it.

The owner then decides what to adopt. A verification recommendation is not
permission to edit, push, publish, or merge.

## 4. Responsibility boundaries

These are logical responsibilities, not a proposal for three new processes.
The handoff and Behavior Diff can run as skills in the same coordinating host;
trial agents remain fresh processes through the existing runner.

| Component | Owns | Delegates; must not duplicate |
| --- | --- | --- |
| Verification handoff | Owner's decision question, available context, authority, follow-through, review synthesis, plain-language recommendation | Scenario design, host launch mechanics, trace normalization, a separate comparison verdict |
| Behavior Diff | Input resolution, experimental purpose, scenario/data/criteria, capability requirements, frozen inputs, comparison interpretation and limitations | Process lifecycle, sandbox implementation, credentials, native-event parsing, report rendering mechanics |
| Existing runner and helpers | Workspaces, host invocation, process lifecycle, native evidence, normalized events, operational status, existing analysis/report operations | User consent, scenario invention, changing the decision question, adoption or merge |

Behavior Diff may use the runner's model-backed analysis. Owning interpretation
does not mean moving analysis mechanics out of the runner. Likewise, handoff
accountability does not mean reimplementing every delegated responsibility.

A report inconsistency goes back through Behavior Diff's evidence-audit process.
Preserve the original report and label any supported correction in the result;
do not silently edit generated findings or let two layers maintain different
answers.

## 5. Proposed handoff contract

This is a checklist for existing information, **not** a new JSON schema, required
file, CLI, or API to implement before the walkthrough.

### Handoff gives Behavior Diff

- The owner's decision question and available intent, clearly distinguished from
  the historical motivation of the selected change.
- The requested source: PR/revisions, explicit snapshots, or local edit.
- Desired coverage and constraints, including behavior that must be preserved.
- Existing authority for models, provider/account, outgoing data, cost/quota,
  trials, and recovery; unresolved authority is identified, never fabricated.
- Excluded effects, such as no source modifications or publication.

Behavior Diff resolves and freezes the experimental inputs. The handoff does
not dictate expected answers or substitute its review conclusions for evidence.
Historical preparation keeps the existing contemporary-source boundary.

### Behavior Diff returns to the handoff

- What was compared, under which conditions, and what the scenario actually reached.
- Observed differences, shared behavior, regressions, and unknowns.
- Execution health separately from behavioral findings.
- Exact run/report references, evidence references, and failed attempts.
- Any remaining prerequisite or authority needed, with its effect on the question.

The result may be useful, null, mixed, or inconclusive. Neither a report file nor
a favorable headline is sufficient proof of a completed, meaningful comparison.

### Behavior Diff delegates to the runner

Reuse `prepare_shared.py` and the documented verify-and-launch recipe. Pass the
verified arguments to the bundled `behavior-diff.sh` from the same selected
version. Keep current configuration, status, native traces, normalized traces,
and report artifacts authoritative. Do not introduce a second launch manifest.

A saved run handle supports diagnosis and continuation planning. It does not
promise resumable execution or exactly-once launch. Do not restart a live or
uncertain run merely because the coordinating conversation was interrupted.

## 6. Design options and tradeoffs

### A. Direct skill composition — recommended for the first journey

The handoff calls on the canonical Behavior Diff instructions; Behavior Diff
uses its existing preparation and runner path. Their interface is the information
in section 5, carried through existing context and artifacts.

**Pros:** smallest new surface; uses the current execution path; avoids another
host-specific prerequisite; keeps one owner for comparison decisions; allows an
E2E check without first designing durable orchestration.

**Cons:** responsibility boundaries are instruction-enforced, not machine-enforced.
The coordinating agent may still skip steps or duplicate judgment. Shared context
can contaminate preparation if historical-source rules are not respected.
Interruption recovery still depends on preserving existing run references.

**Why choose it now:** those are concrete things the first journey can expose.
The recommendation is not that wording alone guarantees correct behavior.

### B. Artifact-centered handoff — possible refinement

Use existing frozen preparation, run status, and evidence references as explicit
handoff points. The handoff reads a bounded comparison result instead of relying
primarily on conversational continuity. Reuse current records before proposing
any new envelope.

**Pros:** easier to inspect what was requested, authorized, executed, and returned;
less dependence on the agent remembering the previous step; clearer recovery
across sessions; better reuse by another caller.

**Cons:** requires agreement on which existing records are authoritative and what
can be reconstructed. A new mandatory artifact can become another prerequisite.
Existing status does not automatically encode all journey-level authority or
support resume. Serializing a contaminated judgment does not make it independent.

**When justified:** the E2E evidence shows lost run references, repeated handoff
reconstruction, or inconsistent return information that simpler instructions
cannot adequately address. Do not rebuild current freeze/status contracts.

### C. A small programmatic journey coordinator — defer

A future local interface could open a journey, record an authorized transition,
and inspect its next action. It would reference Behavior Diff runs rather than
launch hosts or own trial states. This is a design alternative, not a planned
implementation in the first increment.

**Pros:** explicit automation contract; durable authority and attempt history;
multiple callers can coordinate without reconstructing progress from chat.

**Cons:** another state lifecycle, schema, and recovery contract to maintain.
Interrupted launches and concurrent callers need real reconciliation semantics.
Duplicated run status or copied authority can disagree with the source. A state
machine cannot decide whether a scenario is meaningful or an explanation useful.

**When justified:** repeated real multi-caller or restart failures demonstrate a
need for enforced journey transitions. One difficult walkthrough is not evidence
that a new coordinator is necessary.

### Custom Codex isolation is a separate decision

A custom launcher is not an alternative implementation of journey ownership.
It addresses an execution or experimental-control requirement. Its possible
benefit is a verifiable filesystem boundary; its costs include platform/version
coupling, credential lifecycle work, and additional startup failure modes.

Do not retain it merely because it was implemented, or remove a required safety
boundary merely because the implementation is complex. Decide necessity against
the actual comparison claim, as below.

## 7. Context hygiene, safety, and the limits of the first check

Keep three different concerns separate:

1. **Context hygiene:** do not give trials expected answers, private criteria,
   later fixes, or previous outcomes. Use neutral tasks and the supported fresh
   preparation context when historical inputs require it.
2. **Execution safety:** respect the host's supported permissions, restrict effects
   to authorized workspaces/actions, protect credentials, and avoid global
   configuration changes. Never bypass a denied sandbox to obtain a result.
3. **Causal isolation:** establish that the changed instruction, rather than shared
   memory or other guidance, accounts for an observed difference. Fresh processes
   and equal settings alone do not establish this stronger claim.

The first E2E check primarily asks whether the handoff completes a useful
verification journey in the supported user environment. It still requires a
valid, honestly bounded underlying comparison. It does not need to establish
that every host information channel is inaccessible unless the agreed question
or existing contract requires that guarantee.

Before the candidate runs, identify the exact active requirements. The current
handoff explicitly requires stronger isolation for incremental-rule claims, and
the canonical skill requires fresh context for contaminated historical preparation.
This paper does not repeal those requirements. Resolve any conflict explicitly
in the minimum candidate changes; do not just unset a variable and call the
same isolation promise satisfied.

Prefer existing supported host controls. If they cannot satisfy a required
boundary, state the missing capability. A current-environment comparison may be
proposed instead, but changing the original claim needs owner agreement. If no
supported route answers the question, record an E2E blocker; do not build a new
launcher during the walkthrough or label a narrower result as complete.

The instructions may share one comparison method across Claude Code and Codex
without pretending their host controls are identical. The first walkthrough uses
Codex because that is the route being evaluated. It makes no Claude Code runtime
claim and does not remove support for any existing host.

## 8. How to verify the E2E journey first

### Freeze the question before executing

Use one real instruction-change request in an ordinary application repository.
Select the private source and revision pair before preparation, not to manufacture
a favorable result. Capture which skill/script versions form the candidate;
freeze them for the run. No mid-run policy edits or alternate private launcher.

The primary question is:

> Can the owner hand over this verification task and get a useful recommendation
> without coordinating preparation, execution, recovery, or interpretation?

The underlying comparison question remains specific to that instruction change.
Record it separately so journey completion cannot substitute for answering it.

### What counts as a real run

Invoke the actual handoff skill in a fresh host session. Let it use Behavior Diff,
the existing runner, actual trial model calls, recorded actions/results, and the
existing assessment/report path. Do not replace runner/model outputs with authored
fixtures for this acceptance check, or manually feed the handoff a finished report.

A disclosed simulation inside a trial can still be appropriate for an agent-decision
question. That is different from simulating the verification system itself. For
example, observing a decision to request approval does not require a real external
service unless the requested claim includes that service's behavior.

Before live work, present and obtain the missing model/data/cost authority once.
The proposed first comparison uses the normal three trials per side plus required
preparation and assessment. Price or bound the whole journey, including any named
capability probe, fallback, or retry; do not treat six trials as its entire cost.
Do not add a probe run by default. This document is not that run authorization.

### Acceptance criteria

- The requested source and question remain intact. Historical snapshots and any
  companion-file mappings are verified; no unsupported whole-PR claim is made.
- The normal path needs no owner prompts beyond genuinely missing initial terms.
  The owner does not have to say "continue," choose tools, fix paths, or ask the
  agent to interpret its own results.
- No Go/Spacedock setup is required for an ordinary-agent case merely because of
  vocabulary. No live image/service prerequisite is added to a decision-only claim.
- The actual comparison launches through the existing runner. Required trial
  statuses and native evidence establish completion; a report opening is not proof.
- The planned decision situations are reached and have the evidence required by
  their claims. A case that never ran is not counted as preserved or improved.
- Behavior Diff inspects results across both versions, including minority outcomes,
  and separates task behavior from startup, recording, and assessment failures.
- The final explanation contains the recommendation, observed reason, important
  preservation/regression result, and decision-relevant uncertainty in ordinary
  language. Evidence is available but not required reading to understand the advice.
- No unauthorized model calls, data disclosure, global changes, source edits, or
  external actions occur. Null or mixed results do not trigger result-seeking reruns.

A fully executed, assessable comparison may honestly find no difference and still
pass the journey check. Missing required evidence or an unresolved execution
failure means the full journey was not verified, even if recovery and the final
blocker explanation were excellent. Record those successes separately.

### Evidence and review

Keep the real request, authorized terms, frozen inputs, run/status references,
raw and normalized evidence, report, final answer, and necessary continuation
notes private and outside Git trees. Use existing saved records rather than adding
telemetry or an orchestration database. Do not persist extra owner responses by
default or publish private session material in this plan.

Review each owner intervention: necessary authority/domain input, or avoidable
coordination. Inspect the final answer for decision usefulness. Do not require a
new interview, quiz, or owner-debugging exercise to call the work complete.

Use available timestamps to report preparation, execution, and interpretation time
without inventing savings or a speed target. A slow but complete journey is a
latency finding, not permission to replace the runner prematurely.

After the first run, discuss the evidence before another run or wider refactor.
If a genuine failure occurs, retain it and identify the smallest owning-layer fix.
Further paid execution stays inside explicit recovery terms; otherwise request
only the additional authority needed. Do not repeatedly rerun an unchanged setup.

## 9. Proposed changes, only after paper agreement

### Minimum candidate for the journey check

- Make the handoff's delegation and follow-through explicit. Keep plain-language
  decision guidance, reuse of existing authority, and evidence-backed recovery.
- Keep one resolved Behavior Diff version for the entire journey, including when
  the reviewed repository is elsewhere.
- Replace handoff-owned comparison recipes with references to the canonical method.
  Keep actionable orchestration instructions; "delegate" must not become a reason
  for the agent to stop and wait for the owner.
- Remove the experimental launcher's mandatory role from the candidate after
  resolving section 7's requirements. Exercise the normal runner path, not a new
  wrapper. Experimental files may remain parked until the cleanup decision; their
  presence is not approval to select them.
- Make only demonstrated prerequisite fixes needed for this case. Preserve exact
  source content, recorded evidence requirements, and authorized effects.

These are proposed edits, not prerequisites to an elaborate architecture project.
Do not create a general API, resume engine, new manifest, model policy framework,
or second assessment system to run the first journey.

### Refinement after the walkthrough

Use the observed failure location to choose the change:

- Extra owner nudges or unclear advice: fix handoff ownership and presentation.
- Invalid scenarios or contradictory comparison rules: fix canonical Behavior Diff.
- Actual CLI startup, evidence, or lifecycle defects: fix the existing runner adapter.
- Lost cross-session state: first reuse existing records; consider option B only
  if they are insufficient. Consider option C only for demonstrated enforcement needs.

If the custom isolation experiment is retired, remove its whole unused integration
in a focused change: `codex_isolated.py`, `run-trial.sh` opt-in selection,
`prepare_shared.py` isolation-setting freeze checks, corresponding dedicated tests
and CI step, and helper-specific skill/reference/architecture text. Preserve
unrelated source selection, authorization, ordinary-agent routing, and explanation
improvements. Do not reset whole files or discard other working-tree changes.

That cleanup is proposed, not executed here. Update current architecture docs when
behavior changes; this proposal must not be mistaken for implemented architecture.

## 10. Relationship to the existing pipeline plan

The [extensible pipeline plan](2026-10-28-extensible-behavior-diff-pipeline.md)
addresses execution/analysis internals, including future observer/assessor
separation and its own host-isolation gates. This proposal neither revokes those
decisions nor makes their completion necessary for the first handoff walkthrough.

Use the currently implemented runner and posttrial path. Do not claim the future
semantic split is already available. Any later shared architecture work must
reconcile the plans explicitly rather than add another coordinator beside them.

No release, retirement of live mode, or reduction of host support is implied.

## 11. Discussion points and recommended defaults

1. **Which design first?** Recommend A: direct skill composition using existing
   records, with no new mandatory artifact or coordinator.
2. **What must the first E2E establish?** Recommend completion and decision
   usefulness for one real case, with honest comparison limits—not universal
   causal isolation, cross-host parity, or faster execution.
3. **How much owner involvement?** Recommend no execution prompts once terms are
   authorized; ask only for genuinely missing authority or facts.
4. **What happens to the custom launcher?** Recommend keeping it out of the
   candidate after explicit boundary review; decide its clean removal after the
   journey evidence. Do not silently retain it as a fallback.
5. **When do we refine architecture?** After reviewing the first journey's actual
   coordination, correctness, and explanation gaps. No refactor for neatness alone.

## References

- [Current architecture](../docs/architecture.md)
- [Verification handoff skill](../.agents/skills/verification-handoff-prototype/SKILL.md)
- [Current handoff execution instructions](../.agents/skills/verification-handoff-prototype/references/execution.md)
- [Canonical Behavior Diff skill](../plugin/skills/behavior-diff/SKILL.md)
- [Canonical preparation and trusted launch recipe](../plugin/skills/behavior-diff/references/scenario-and-test-data.md)
- [Existing trial adapter](../plugin/skills/behavior-diff/scripts/run-trial.sh)

Source documents describe the current working tree, including experimental edits.
Links are not evidence that this proposal or the next E2E run has been implemented.
