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
3. Derive the scenario and test data from those expected outcomes using only
   information available at the selected modification. Apply the preparation
   checks below, then freeze the scenario, shared data, tool environment, model
   settings, and approved trial count before execution.
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

## Intention-driven scenario and test data

Use this preparation sequence:

**Intent → required capabilities and observable outcomes → necessary assumptions
→ a bounded set of ordinary and edge cases covering those capabilities → shared
scenario and test data → Before/After evidence → per-case assessment.**

Unlike exploring unspecified side effects, this experiment has a known target:
the behavior the modification is meant to achieve. Deliberately include cases
needed to exercise that target. Prioritize conditions that distinguish achieving
the outcome from merely following a new step, within the approved trial budget.
This is bounded intention coverage, not an exhaustive failure-condition suite.

For each selected outcome, preparation must record:

- The contemporaneous intent it tests and why the condition is relevant.
- What the agent must actually do to produce the outcome.
- Which initial facts and tool capabilities the environment supplies.
- The independent assessment ground truth, kept outside the agent's workspace.
- What remains outside the experiment's scope.

Do not pre-complete the capability under test. If the intent requires discovering
information, start before that discovery and let the agent choose and perform
the necessary queries. Do not replace discovery with an immediately readable,
precomputed findings report. Legitimate query results may contain the answer;
the requirement is to preserve the work being tested, not to hide useful facts
or force an arbitrary command sequence.

Build coherent underlying facts from which assessment expectations can be
checked independently. A frozen tool adapter may expose those facts through
queries, but must clearly distinguish simulated responses from real operations.
Verify that relevant queries are supported before execution; missing harness
capabilities are not evidence of an instruction defect.

The neutral task must not instruct the agent to satisfy the assessment criteria
or reveal the expected findings. The preparation model may know the intended
outcome; each trial receives only its historical instructions, task, and normal
environment access.

### Select edge cases by intention coverage

Different update categories exercise functional coverage; they do not by
themselves challenge the assumptions needed to achieve the intended outcome.
The previous discovery replay covered functional categories under coherent,
complete query results. It did not explicitly select an edge condition.

For the next experiment, an isolated preparation session must:

1. Derive the main expected outcome and its necessary assumptions from the
   contemporary change and normal operating context.
2. Identify plausible conditions that challenge those assumptions. Select a
   bounded set by relevance, plausibility, assessability, and additional coverage
   of the main intent. Do not impose a one-edge-case limit or fill a quota with
   redundant cases. Record the capability-to-case mapping, selection rationale
   and uncovered capabilities before execution. This does not predict a later
   incident or claim exhaustive failure coverage.
3. Combine compatible ordinary and edge cases in one coherent project and task.
   Both variants receive the identical dataset. Each case need not cover the
   whole intent; their union should exercise its main capabilities. Conditions
   that contradict or obscure one another require separation, not an incoherent
   fixture. Additional scenarios or trial sets require separate cost approval.
4. Keep the correct underlying facts and assessment criteria outside trial
   access. Let the agent acquire evidence through supported queries; do not
   place a prepared findings list in its workspace.
5. Define success, contradiction, and insufficient-evidence criteria separately
   for every case. A successful overall answer must not conceal a missed case.
   Record cross-case cues and interactions; combined cases are not causally
   independent.

Preparation receives this generic method, not a suggested failure mechanism,
later corrections, previous fixtures, or previous outcomes. Case and method
selection remain hindsight-informed even with isolated preparation.

All required tool capabilities must work before trials. A deliberately modeled
environmental limitation must be distinguished from accidental harness failure;
failure alone does not establish an instruction defect. Conflicting observations
also require a justified ground truth before treating either choice as wrong.

Keep the approved trial count unchanged. A richer scenario can still increase
tokens per trial. Use a new private run directory, preserve the first result,
and do not change the selected cases after seeing trial outcomes. Report
raw-log assessments separately if the unmodified report cannot assess the
required evidence; do not silently repair its conclusions.

### Explicit environment preconditions

Before freezing any scenario, map each expected outcome to the environmental
facts it depends on. Record where each necessary fact is exposed to the agent,
how it is checked, and which source is authoritative. Assessment-only knowledge
must not silently supply an environmental premise absent from the trial.

When an outcome depends on time, define a scenario-wide assessment timestamp
and timezone. Distinguish it from evidence capture dates and the host's wall
clock. Give both variants the same neutral as-of instruction and require all
simulated clock responses and assessment calculations to agree. Do not include
the expected recommendation in that instruction. Scenarios without temporal
requirements need no artificial timestamp.

Preflight must reject missing or inconsistent required premises before spending
trial calls. This verifies the environment contract, not whether the agent
follows it; inspect actual evidence use afterward. Other premises, such as
permissions or repository state, need their own explicit representation rather
than being presumed from the intended answer.

The corrective release-age replay will retain the frozen scenario, data,
historical instructions and criteria, adding only an explicit shared assessment
time and its environment validation. It is a controlled harness correction
after inspecting an earlier outcome, not a fresh blind case or independent
replication. Preserve both runs and do not reinterpret the earlier ambiguity
as a failure. This experiment does not yet change the shipped plugin workflow.

### Preparation lesson and next experiment

A scenario can follow the modification's intent yet test too little. Supplying
an already-computed findings list tests whether the agent uses those findings,
not whether it can discover them. Observable success must cover the capability
claimed, not only its final reporting step.

The next historical replay will apply this preparation method in an isolated
session before considering a permanent product change. It will receive only the
selected change's contemporary sources and these general design requirements,
not later fixes, previous fixtures, outcomes, or a suggested failure mechanism.
Keep the historical skill bundle and trial budget fixed so the new preparation
does not become a hindsight-guided attempt to manufacture a finding.

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

### 2026-10-15: dependency-audit discovery replay

Privacy-safe case label: historical dependency-audit change. The comparison
used the complete original and modified skill folders, including references.
Preparation received only the selected change's contemporary sources and the
general intention-driven method, not later corrections or previous trial data.
The shipped product was not modified.

**Intent and assumption.** Discover remaining dependency updates beyond the
existing bot PRs and provide advisory recommendations. Before execution,
preparation selected cross-ecosystem discovery and evidence-backed update
classification as observable outcomes.

**Setup.** One synthetic npm/Python project, with ordinary patch, major, and
security-relevant minor updates. The task explicitly requested a read-only
audit using the new audit-only entry point. Project files contained raw
manifests and configuration, not prepared findings. Version and advisory data
were accessible only through simulated query tools; independent ground truth
remained outside trial inputs. Model: `openai-codex/gpt-6-astra:high`; three
Before and three After attempts.

**Observations.** Both sides queried the available sources and identified all
three updates and the security advisory in every attempt. Before recommended
an independent security change; After consistently proposed bundling the
security minor and routine patch without delaying the fix, with the major
handled separately. Neither side changed project files. A recoverable
empty-path read error occurred in each After attempt; required query evidence
was subsequently obtained.

**Assessment.** The raw-log audit supports the intended discovery outcome in
this bounded environment, but Before already achieves it under the explicit
audit request. This does not establish an incremental discovery improvement.
The task differs from the earlier empty-queue continuation experiment, so
cross-run differences cannot be attributed to data preparation alone.
No later field failure was reproduced. Frozen responses do not validate live
package-manager behavior, registry freshness, or untested dependency surfaces.

**Report limitation.** The unmodified report describes behavior differences,
but its target and attention assessments are unavailable. Query response
bodies did not reach extraction. Prepared criteria and ground truth also
remained in a separate assessment companion, not the product extractor.
Comparison against ground truth was therefore a separate raw-log audit, not
an automatic correctness verdict from the report.

**Decision relevance.** The evidence does not justify claiming that this edit
newly enables discovery in the tested scenario. It supports a narrower claim
about recommendation policy. No actual reviewer acceptance decision was
observed.

**Next step.** Before presenting this method as an automated validation
workflow, address assessment access to the required query evidence and
pre-recorded outcome criteria. Further experiments require separate approval;
do not retrofit a known later failure into this run.

The approved eight model sessions used 522,194 reported tokens, including
287,872 cache-read tokens. These totals include preparation and extraction,
exclude orchestration, and are not a billing statement. Raw evidence and
reports remain private and outside this repository.

### 2026-10-15: combined ordinary and release-age edge replay

Privacy-safe case label: the same historical dependency-audit change. A fresh
preparation session used only contemporary sources and the generic combined
method. It selected an explicit release-age exception from the modified skill,
not a mechanism supplied from the later correction.

**Setup and expected outcomes.** One npm project contained two compatible
non-security minor updates. Registry facts and the simulated clock established
ages of 31 days and two days. Preparation expected routine follow-up for the
ordinary release and one-cycle deferral for the recent release. Facts were
available through queries, not a prepared findings file. The model and
three-Before/three-After count were unchanged. This task, data and selected
condition differ from the preceding experiment.

**Ordinary observation.** All six attempts discovered both updates and
recommended routine follow-up for the established release. Neither side
modified project files.

**Edge observation.** Before recommended both updates without an age condition
in all three attempts. Two After attempts queried the clock, identified the
two-day age at the recorded snapshot, and requested fresh checks before
grouping. They also said the waiting period had since elapsed. The remaining
After attempt did not query the clock and said neither update required an
age-based deferral. This is variation in evidence use and recommendation
framing, not a demonstrated one-in-three correctness failure.

**Validity gap.** The harness labeled the clock as a recorded synthetic
response but did not establish it as the authoritative date for the requested
recommendation. Historical-snapshot and present-day recommendations are
different readings. The preparation's defer-now criterion therefore cannot
cleanly establish an instruction defect. Both packages also shared a namespace,
and answers invoked family grouping, coupling ordinary and edge handling.
This preparation flaw should have been caught before running trials.

**Assessment and decision relevance.** The method produced an intent-linked
edge condition and exposed differing handling worth inspecting. It has not
yet established a real unmet user expectation or reproduced the later field
failure. All successful query returns were checked against the frozen world;
the report still lacks target and attention assessments, so this conclusion
comes from the separate raw-log audit.

**Next step.** Establish scenario-wide time semantics before any separately
approved repeat of a time-dependent test. Do not retune this run or count a
harness ambiguity as a discovered skill bug. Explicit audit requests and the
query catalog still limit claims about unguided behavior.

Eight model sessions used 435,985 reported tokens, including 214,016 cache-read
tokens. No additional model run was made after inspecting the outcome. Raw
evidence remains outside the repository; the shipped product was not changed.

### 2026-10-15: explicit-clock corrective replay

The frozen combined case, original purpose, queries, historical skill bundle
and assessment criteria were retained byte-for-byte. No new preparation model
call was made. The only behavioral input correction was a shared environment
instruction establishing 2026-02-20T12:00:00Z as the authoritative assessment
instant, rather than a historical snapshot to reinterpret as present-day advice.
No expected recommendation was included in that instruction.

**Environment verification.** A private machine-readable contract and no-model
preflight check reject missing exposure of the assessment time, inconsistent
clock responses, or changes to the frozen case and purpose. The check rejected
the original environment and passed after the correction. Both host RPC states
and all six recorded trial system prompts contained the same instruction.
This is experimental harness verification, not a shipped plugin feature.

**Observed outcomes.** All six attempts used the intended assessment date,
identified the established release as 31 days old and the recent release as two
days old, and recommended delaying the recent release. Before framed the delay
as a precaution; After applied the explicit seven-day rule. No clock query is
required when the authoritative time is already in the system context.

All attempts identified the established release as eligible. Before scheduled
it first in all three attempts. Two After attempts did likewise, but one
recommended waiting to group both packages as a family. Shared namespace versus
actual package interdependence was interpreted differently. That is an observed
planning difference, not a demonstrated defect or an independent ordinary-case
failure.

**Assessment.** The selected intention and release-age exception were observed
under the corrected environment; Before also achieved these outcomes. The
experiment did not demonstrate an unmet user expectation or the later field
failure. The result is consistent with resolving the earlier time ambiguity,
but these stochastic trials do not establish a causal effect size or general
reliability.

All recorded query returns matched the frozen data, and no project files changed.
The unmodified report's target and attention assessments remain unavailable;
the outcome assessment above comes from the separate raw-log audit. Report
Summary and Trial evidence navigation were checked in a browser.

Seven model sessions used 367,352 reported tokens, including 195,200 cache-read
tokens. No extra trial or extraction was run. Keep these results separate from
fresh blind preparation; they are a disclosed correction after an earlier
experiment. Further model runs require separate approval.

### Next preparation: coverage-driven cases

The next replay will remove the one-edge-case selection limit. A fresh isolated
preparation session will decompose the contemporary intent into capabilities
and select a small, nonredundant case set within one shared scenario and the
existing trial count. It must justify the coverage of the main goal rather than
concentrating every case on one downstream decision.

Required environment premises must be explicit and consistent before execution.
State time or other necessary context neutrally, without naming the rule trigger
or suggesting a recommendation. In the explicit-clock replay, Before changed
from recommending both updates to deferring the fresh release after a paragraph
that mentioned publication timestamps. This possible cue effect is not causally
established, but limits attributing the outcome to the historical skill.

Freeze per-case ground truth outside trial inputs and audit every case, including
unsupported conclusions and uncertainty. Use only contemporary source material
for preparation; do not supply later repairs, previous fixtures, results, or a
specific failure mechanism. Richer coverage may increase tokens even with the
same number of trials. No further run is authorized by this note alone.

### 2026-10-15: coverage-driven multi-case replay

With fresh approval, an isolated preparation session selected five complementary
cases from contemporary intent and historical source only. Later repairs,
previous fixtures, and previous results were excluded. One shared synthetic
project and an explicit assessment instant were used for Before ×3 and After ×3.
Expected outcomes remained outside trial inputs.

| Case | Before observations | After observations |
| --- | --- | --- |
| Ordinary eligible patch | 3/3 found and recommended | 3/3 found and recommended |
| Python security update outside configured automation | 3/3 found the affected installed version and fixed target | 3/3 found and prioritized the fix |
| Exact PR coverage versus a different target version | 3/3 distinguished the existing patch from the remaining major upgrade | 3/3 excluded the exactly covered target and retained the major-upgrade recommendation |
| Explicit package ignore | 3/3 identified the ignore; proposed reviewing the policy rather than silently overriding it | 3/3 explicitly skipped the update |
| Two-day-old routine release | 2/3 included it in routine follow-up; 1/3 left it to team policy | 3/3 deferred it under the seven-day rule |

This provides evidence of policy adoption and correct behavior on the selected
cases, not an observed unmet intention. Before also found the inventory and
security findings under the explicit audit request. The new waiting policy was
not present in Before, so its differing recommendations are not baseline bugs.
No later historical failure was reproduced.

The environment deliberately exposed a supported-command catalog, complete-tree
scope, and provisioned installations matching manifests. It did not exercise
real package-manager execution, stale caches, hidden manifests, or unreliable
services. These bounds helped make the cases assessable but limit discovery
claims. Multiple cases improve stated coverage; they do not guarantee that the
unselected failure mechanism is covered.

All 108 successful command responses matched frozen records; no writes were
attempted. One After trial recovered from an empty-path read error. Findings
above come from auditing all six raw final answers and tool records, not treating
review-mode pass counters as correctness scores. The standard report rendered
11 decision comparisons, seven diverging; browser loading succeeded, but a
screenshot timed out and trial-panel visibility was not confirmed.

Eight model sessions consumed 672,693 reported tokens, including 414,464 cache
read tokens. This is recorded model usage, not a billing total. The richer case
set kept six trials but did not keep token consumption constant. Raw evidence
and reports remain local and uncommitted.

### Next experiment: edge cases in scenario and test data

Use the following preparation logic, without supplying later repairs or earlier
experiment fixtures and results to the isolated preparation session:

1. Identify intent from the contemporary change description and historical
   before/after instructions. Distinguish stated goals from inferred goals.
2. Define observable outcomes needed to satisfy that intent.
3. Generate natural scenarios with complementary ordinary and edge cases.
   No individual case must cover every condition. Do not leak expected answers.
4. Generate underlying project inputs and queryable data for those scenarios.
   Challenge important assumptions about information reliability, completeness,
   freshness and agreement where relevant to the contemporary source. Select
   multiple plausible, nonredundant edge conditions rather than only clean
   happy-path data. Do not prescribe a known later failure mechanism.
5. Validate and freeze the world, premises and per-case assessment criteria.
   Ground truth must be coherent; secondary observations may legitimately differ
   because of time, scope or source limitations. Replace the earlier blanket
   requirement that independently checkable inputs must agree with this
   distinction. Define why each discrepancy exists and provide usable ways to
   investigate it. Keep ground truth and expected findings outside trial inputs.
6. Run both instruction versions against identical tasks and data. Assess each
   case separately against intent, recording failures, successes and insufficient
   evidence rather than requiring a difference.

Combine compatible cases into one shared scenario and dataset where practical.
Keep Before ×3 and After ×3 for this replay; richer data may increase token usage.
The experimental preparation harness implements this proposal, not a shipped
product feature. A retrospective reproduction and independent first-change
discovery are different claims; this run seeks the latter and must exclude
follow-up history from preparation. Neither broad coverage nor a passing result
establishes that all failure conditions have been tested.

### 2026-10-15: complementary data-edge replay

The revised isolated preparation generated a new shared project with five cases:
ordinary Node/Python patches; a declared Python dependency absent from the local
inventory plus an unavailable audit executable and working advisory fallback;
an action's older published release versus newer resolving tags; a two-day-old
release; and a mature major migration. No later repair or previous fixture/result
was supplied to preparation. The generated source discrepancies were checked
against coherent ground truth before running Before ×3 and After ×3.

| Case | Observed result |
| --- | --- |
| Ordinary patch discovery | Both versions found and recommended both patches in 3/3 trials |
| Partial Python inventory and missing audit tool | Both versions found the omitted declared dependency, matched its advisory and recommended urgent remediation in 3/3 |
| Release listing versus action tags | Both versions resolved the references and avoided a false freshness update in 3/3 |
| Recent release | Before 3/3 discussed adoption without the new seven-day deferral; After 3/3 deferred |
| Mature major | Both versions recommended separate migration work in 3/3 |

The generation principle produced information-scope discrepancies and a usable
fallback, rather than exclusively agreeing observations. However, no unmet
After intention was observed on these selected cases. This is not reproduction
of the later historical incident, nor proof that complete audit discovery works.
The README explicitly explains the developer/deployment inventory distinction,
and the supported-command catalog guides discovery. Those cues limit claims
about independently recognizing hidden source limitations. This run does not
exercise actual caches, workspace enumeration, or SHA-pinned action updates.

All 111 successful tool invocations returned their frozen command responses,
including the deliberate command-not-found response. One After trial recovered
from an empty-path read error; no writes were attempted. All six raw final
answers were audited separately from the standard report's ten decision
comparisons, three diverging. Review-mode pass counters are not correctness
scores. No browser visual verification was performed for this run.

Eight model sessions reported 627,420 tokens, including 413,824 cache-read tokens;
this is usage, not billing. Evidence remains local. The owner also granted
standing approval for requested Behavior Diff runs in this repository, including
the established model/data handling scope, without repeated cost confirmations.
That approval does not authorize publication of private data.

### Case narrative and investment decision

The historical change added an audit intended to discover maintenance needs
beyond existing automation. A later field incident exposed incomplete discovery
and an unjustified all-current conclusion; a follow-up repair strengthened
information-source verification and coverage. Updates published after the audit
must be distinguished from actual misses.

The replay series observed rule adoption, but did not independently surface the
later failure from first-change inputs. Explicit fixture cues and the command
catalog also limit claims about discovering hidden source limitations.

This case supports the existence of intention/effect gaps, not the hypothesis
that the current method reveals owner-unnoticed gaps early. Stop further tuning
of this replay merely to obtain a successful example. A hindsight-informed
regression test would answer a different question.

Validate change assumptions remains unsupported as a new core product goal by
this experiment series. Failure to prove universal impossibility is not a reason
to continue investing. Reopening this line requires new evidence or a specific,
testable methodological rationale, not another appeal to insufficient edge cases.
The full narrative and private source links are saved locally outside the repo;
no private incident details or transcripts are included here.

### Next selected case: review-instruction refactor

Three additional candidate narratives were saved privately: publication behavior
after an instruction refactor, incomplete review-state closure after automated
repairs, and a repair subagent's missing required report. The first has directly
verified historical output artifacts; the second may be answered by ordinary
static review; the third requires actual multi-agent lifecycle evidence.

The selected replay tests the original refactor before/after, not the later
repair. Preparation receives only the contemporary selected skill and historical
reference dependency closure. It must choose its scenario and cases without
the later incident, repair, or prior fixtures. Preservation goals inferred from
existing contracts must remain labeled inferred.

Publication is recorded locally with exact submitted bodies and events; no
GitHub write occurs. The simulator permits arbitrary content, including repeated
content, and does not enforce the expected publication policy. Its smoke check
verified exact file-body capture, literal-body capture, updates, and rejection
of ambiguous inputs and unsafe paths. A completed comparison will be assessed
from actual publication records, not just the final answer's claimed actions.

### 2026-10-15: original review-refactor replay

An isolated preparation session selected a mixed Python/TypeScript/React review
task from the original refactor and its historical reference closure. It did
not receive the later publication repair or incident. The generated task
explicitly requested local issue-comment and formal-review artifacts, but did
not prescribe different bodies or mention duplication. This makes the
publication boundary reachable without independently testing artifact selection.

Before and After each completed three trials. All six found the four primary
seeded code defects and recorded one detailed issue comment plus one distinct
REQUEST_CHANGES review. None copied the complete issue-comment body into the
formal review. The historical duplicate-publication failure was not reproduced.
After's detailed reviews were more concise; this is not evidence of improved
defect discovery, since Before found the same primary defects.

Formal reviews still included findings summaries and verification limits rather
than only a short status pointer: 706–1,001 characters across the six trials,
with all three After reviews spanning seven lines. This narrower output-policy
deviation must not be relabeled as the historical full-body duplication.
Before wrote review-body files; After passed literal publication bodies. The
dedicated simulator changes the command/file handling compared with real gh
publication, limiting conclusions about the original copy/reuse mechanism.

The audit checked all twelve submitted bodies, all six final answers, and all
111 successful query responses against frozen records. Each trial recovered
from an empty-path read error. No real GitHub writes occurred. No project source
was edited; only Before created local review-body artifacts. Actual Skill
invocation, subagents, checkout, test execution and network behavior were not
available in trials. Reading bundled security guidance is not evidence of
executing the security skill. No browser visual verification was performed.

Eight model sessions reported 2,392,126 tokens, including 1,751,424 cache-read
tokens; orchestration is excluded and this is not a billing total. The larger
historical guide closure increased context consumption. No additional model
rerun was started.

Model limitation: preparation, all six trials, and extraction used
openai-codex/gpt-6-astra with high reasoning through OMP, not a verified
historical execution stack. Non-reproduction is an observation about that
model and simulator, not evidence that a contemporary Claude agent would
avoid the failure. The exact historical model/version remains unverified.
The user requests a representative trial model such as sol rather than
gpt-6-astra; Opus 4.6 was suggested as a historical possibility, not established
provenance. A model comparison should keep the scenario and data frozen and
record the resolved model/version and host separately. Changing the host or
publication tools at the same time would not isolate the model effect.

Conclusion: this run does not support first-change detection of the later
publication failure, despite directly reaching the publication step. It does
not invalidate the verified historical incident. Do not tune the scenario
toward that incident and present a resulting reproduction as blind discovery.

### Sol model comparison of the frozen review-refactor replay

The historical execution model is unknown; this comparison does not attempt
to reconstruct it. The user selected sol for a new execution of the existing
scenario. The product selector resolved to gpt-6.1-sol, also available on OMP.
Trials retain OMP, high reasoning, the local publication tool and all other
runtime settings. This isolates the requested model substitution rather than
claiming execution through the standard Codex host.

No new scenario or data generation call was made. Before launch, the original
and new freezes matched on task, plan, purpose, source, material manifests,
assessment companion, system prompts, command catalog and both variant trees.
Only model.py differed among the recorded runtime input hashes. The original
run remains intact. All six fresh trials completed with gpt-6.1-sol confirmed
in raw assistant messages. A separate Sol extraction generated the report.

The direct publication audit found complete body duplication in zero of three
Before trials and one of three After trials. In that After trial, both raw tool
calls and the publication ledger contain the same 2,659-character body.
Another After review repeats detailed findings but is not byte-identical;
it is not counted as complete duplication. All six final answers identify the
four principal seeded defects. No source files were modified.

This reproduces the historical symptom in one simulated After execution without
redrafting the scenario or injecting the later repair into the trial inputs.
It provides a concrete behavioral preservation failure under this selected
model. Three trials per side do not establish a reliable incidence rate or
general detection capability. The case was selected retrospectively, and the
model was changed after a negative run; this is not a prospective discovery.
The local publishing tool and explicit request for both artifacts remain limits.

Raw evidence and report detection differ: the generated report does not flag
the duplicate body. Its summary says complete After publication bodies are
unavailable to assessment, calls published concision unassessable, and has no
attention item. Its bounded evidence handoff must not be confused with the
complete raw publication ledger audited here. Thus the simulation exposed the
symptom, but the current automatic report did not deliver that finding.

The audit checked all twelve publication bodies and six final answers,
verified the duplicate against raw tool arguments and body hashes, and matched
115 successful command responses to the frozen catalog. Five trials recovered
from an empty-path read error; one also requested absent instruction files.
Seven sessions used 2,303,924 tokens, including 1,730,176 cache-read tokens;
parent orchestration is excluded and this is not a billing total.

Verification tracking: DRC-4899. Sources, reports and detailed audit records
remain private local artifacts; no live GitHub publication occurred.

Accepted milestone: the simulation reproduced the historical duplicate-publication
symptom. Retain this as positive reproduction evidence: zero of three Before
trials versus one of three After trials with identical publication bodies.
Automatic report detection remains a separate, unmet outcome. Do not discard
the reproduction because the report missed it, or describe the reproduction
as a completed automatic warning capability.

### Sol comparison of the complementary dependency data-edge replay

The user requested checking whether trial model choice contributed to the
earlier non-reproduction. The review-refactor model comparison provides a
specific rationale for this check, not evidence that one model is generally
stronger or that dependency discovery must fail under Sol.

Reuse the last complementary data-edge preparation: ordinary patches, a
declared Python dependency absent from local inventory, an unavailable audit
tool with a working advisory fallback, differing release/tag scope, a recent
release, and a mature major upgrade. No new scenario-generation call or
later-repair input is introduced. Holding those inputs fixed tests model
choice without conflating it with newly generated data.

The selector resolved to gpt-6.1-sol. Retain OMP, high reasoning and the frozen
query simulator; the standard Codex host is not under test. Before launch,
task, plan, purpose, source, material manifests, assessment companion, command
catalog, system prompts and both variant trees matched the earlier run.
Only model.py differed among runtime hashes. Before and After each run three
fresh trials. Report extraction also uses Sol; model comparisons of behavior
will therefore rely on raw trial evidence, not only generated report wording.

All six trials completed with gpt-6.1-sol confirmed in raw responses. Direct
audit of tool records and final answers found the following:

| Case | Before | After |
| --- | --- | --- |
| Ordinary Node/Python patches | Found and recommended both in 3/3 | Found and recommended both in 3/3 |
| Missing-local Python dependency and unavailable audit | Found the declared dependency and high-severity alert in 3/3; disclosed audit limits | Same in 3/3 |
| Published release versus resolving action tags | Verified both refs and avoided a false freshness update in 3/3 | Same in 3/3 |
| Two-day-old release | 1/3 recommended routine adoption with checks; 2/3 discussed optional soak/review | Deferred under the new seven-day rule in 3/3 |
| Mature major release | Recommended separate migration work in 3/3 | Same in 3/3 |

No trial declared everything current or omitted the selected missing-local
dependency. The later historical discovery failure was not reproduced with Sol.
This model-only comparison does not support attributing the earlier negative
result to the use of Astra. It does not establish model equivalence or complete
discovery: the README still explains the inventory/deployment distinction,
the command catalog guides investigation, and real caches, workspace enumeration
and SHA-pinned action updates remain outside the frozen scenario.

The audit verified 119 successful command returns against the frozen catalog,
including modeled command failures. One After trial recovered from an
empty-path read error; no files changed in any trial. The Before freshness
recommendations are not violations of a waiting rule absent from that version.

The generated report contains ten decision comparisons, three diverging, and
no attention item. Its main contrast is the new mandatory release-age deferral,
not a discovery failure. The extractor reports omitted release metadata; the
direct audit above used complete frozen tool responses rather than treating
the report's evidence window as the complete record.

Seven sessions used 536,093 tokens, including 321,792 cache-read tokens; parent
orchestration is excluded and this is not a billing total. The scenario was
reused without another preparation call. The report and raw evidence remain
private local artifacts. DRC-4899 also tracks this requested model comparison.
