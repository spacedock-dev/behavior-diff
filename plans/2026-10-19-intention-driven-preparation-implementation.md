# Implement intention-driven scenario and test-data preparation

Date: 2026-10-19
Status: PR 1 merged as [#49](https://github.com/spacedock-dev/behavior-diff/pull/49).
PR 2 merged as [#50](https://github.com/spacedock-dev/behavior-diff/pull/50), including
the corrected Claude prompt transport and dogfood CI gate.
PR 3 implements the approved assumption-first report design and assessment
reliability fixes. No new live model runs are authorized for this implementation.

## 1. User request and product decision

Bring the scenario and test-data generation method exercised in our experiments
into the installable Behavior Diff skill.

> We identify the intent behind a change, then use Behavior Diff to check whether
> the agent's actual before-and-after behavior matches that intent.

The target is **Validate change assumptions**, not reliable detection of every
unknown side effect. Include both behavior intended to change and behavior meant
to survive the edit. A new instruction can fail to achieve its purpose even if
Before and After make the same mistake; do not require a behavioral divergence
before acknowledging an unmet After requirement.

The user does not want to write a full evaluation dataset or specify the failure
in advance. The skill should derive a natural scenario and suitable data from
available contemporary context. Multiple relevant edge cases may share one
coherent scenario. This is bounded intent coverage, not exhaustive test generation.

### Already decided

- Preserve the tested generation recipe below; do not invent a new method while
  implementing it.
- Design scenario AND data. A good task with inadequate data may not exercise
  the intended capability.
- Use the user's execution model/configuration for trials. Do not silently
  substitute a stronger model, and keep preparation/extraction roles distinct.
- Freeze inputs before executing; preserve negative and inconclusive results.
- Keep normal trial counts and host parity. Do not multiply trials by edge count.
- A reproduced gap and an automatically reported gap are different milestones.
- Private notes/raw evidence belong outside tracked files (`memo/` is ignored).
  Do not copy private historical skill text or session data into public fixtures.
- Deliver preparation in two independently reviewable PRs, as specified in
  section 9. Complete and verify the scenario/test-data workflow before reopening
  report design.
- Keep the current automatic report during those PRs. The skill's evidence-based
  explanation must disclose coverage and reporting gaps; it must not rewrite
  saved report artifacts to make them agree with a raw-evidence audit.

### Explicitly not established

- Workflow skills are a promising evaluation focus, not proven easier to test.
- More reasoning or more edge cases is not proven to improve detection.
- The proposed main-goal Before/After classifier and automatic reasoning-level
  escalation are **not part of this implementation**. Preservation goals already
  belong to the tested recipe; no new classifier is needed to include them.
- A later corrective PR is selection/validation evidence, never an answer key
  supplied to historical preparation.

## 2. Evidence and reading map

Read these existing artifacts rather than reconstructing the discussion:

1. [Experimental plan](2026-10-15-validate-change-assumptions.md), especially
   **Current generation recipe**, **Select edge cases by intention coverage**,
   **Explicit environment preconditions**, and **Evidence limits**.
2. Its experiment-log sections on changelog verification, historical-model
   comparison, and **Public workflow replay: EveryInc lfg PR #1702**.
3. [Architecture](../docs/architecture.md), sections 2–3: ownership, snapshot
   construction, purpose isolation, and trial/assessment/report distinction.
4. [Public skill inventory](2026-10-13-public-skill-change-stats.md) and
   [historical replay workflow](../docs/skill-history-replay/README.md) only when
   selecting a new validation case. Existing historical workflow constraints do
   not automatically authorize multi-file production support.
5. Repository coding, issue and reviewer guidelines referenced by AGENTS.md.

Local-only supplemental records, if present: `memo/public-workflow-skill-survey.md`
and `memo/everyinc-lfg-1702-experiment.md`. They are not required for implementing
this plan and will not exist in a fresh public clone. Never feed their historical
outcomes into a supposedly blind preparation session.

### What the evidence actually supports

- Changelog experiment: some After configurations read descriptions but did not
  perform newly required source verification. The gap was established from raw
  actions/artifacts, not the automatic report. Before was not subject to that new
  requirement. Another model succeeded on both sides.
- Review-output experiment: one tested model produced identical detailed and
  summary outputs in an After trial; a different model did not reproduce it.
  Reading a reference was not proof of applying it.
- [EveryInc #1702](https://github.com/EveryInc/compound-engineering-plugin/pull/1702):
  isolated preparation generated a bug-fix task with project-state edges. One
  Fable 5.1 low After trial ended normally after the child debugging result,
  skipping required review continuation. Five other trials hit provider limits;
  no complete paired completion-rate comparison exists. Extraction failed.
  The later [#1715](https://github.com/EveryInc/compound-engineering-plugin/pull/1715)
  describes the same symptom but was not tested as a fix.
- That replay used private multi-file/runtime adapters, not the shipped single-
  file CLI. Its driver was edited after launch and its original bytes were not
  retained. Do not copy it into the product or treat it as a reference-quality
  harness. Source/plugin equality and the normal terminal event supported the
  bounded observation, not end-to-end reproducibility of the orchestration.

These results motivate shipping the preparation discipline. They do not establish
reliable automatic detection or a general model ranking.

## 3. Current implementation and the actual gap

Canonical source: `plugin/skills/behavior-diff/SKILL.md` (not the installed copy
in a developer's home directory). One product serves Claude Code and Codex.

At the time of this handoff:

| Surface | Current behavior | Required change or constraint |
|---|---|---|
| Skill Ownership + step 1 | Derives and freezes purpose; already includes preservation goals | Retain purpose format/privacy; connect goals to observable capabilities |
| Skill step 2 | Drafts a decision-moment task; asks for a real incident; may start mid-task | Replace with scenario AND data preparation; no mandatory incident question and no pre-completing discovery |
| Skill step 3 | Runs as soon as task is known | Run only after task, data, environment and assessment notes are checked/frozen |
| Skill step 4 | Explains observed flow and unchanged behavior | Check outcome coverage and actual evidence, including unmet After intent without divergence |
| `scripts/behavior-diff.sh` | Git snapshots use `git archive HEAD`; only selected instruction edit enters After | Newly generated untracked data in the user's checkout will NOT enter Git trials |
| `scripts/run-trial.sh` | Host execution and trace normalization | Do not infer model effort from a model name; do not advertise unsupported execution capabilities |
| `scripts/purpose.py` + runner | Purpose is assessment-only, max eight goals | Do not repurpose this schema as a fixture or expected-answer transport |
| `scripts/decisions.py`, `scripts/reporting/evidence.py` | Separate extraction with bounded evidence | No report schema/extractor redesign in this task; declare when raw audit and report disagree |

The largest implementation trap is a Markdown-only promise to generate data
without arranging for that data to exist identically in every trial. A second
trap is giving the trial a prepared findings list when independent discovery is
what the edit is meant to improve.

## 4. Required preparation logic

### A. Derive and freeze intent

Use the selected instruction diff, relevant unchanged instructions/references,
and available user/PR/commit context. Separate explicit goals from inferred ones.
Retain the existing purpose-file contract and privacy rules.

For a local edit, do not insist on a PR description that does not exist. Use the
current conversation and diff; do not mine unrelated transcripts or memory.
For historical edits, use an isolated preparation context if the orchestrator
knows later history. Supply only the selected contemporaneous source bundle and
this generic method. Historical selection bias must still be disclosed.

Do not ask the user to name the failure or supply a full eval. Reuse a real
request if already supplied. Ask only when a material missing requirement cannot
be established from available context and changes what the experiment means.

### B. Map goals to observable capabilities

For each chosen outcome, record privately:

- Source/basis of the intent, including relevant preservation requirements.
- What the agent must discover, decide, execute or produce.
- Necessary environment premises and where the trial can observe them.
- Evidence for support, contradiction, or insufficient evidence.
- Scope not exercised by this experiment.

A skill's main goal may inform preservation checks. Do not force it into a new
before/after goal classification API or adaptive reasoning policy.

### C. Generate one natural scenario

Define the user task, starting state and scope. Do not tell the trial the expected
answer or suspected historical mistake. A normal request may identify the work,
but should not restate new instruction requirements to make both versions obey.

Start before the capability under test. Starting mid-workflow remains valid only
when earlier work is outside that capability, supplied state is coherent, and
skipped stages are explicitly outside the conclusion.

### D. Generate shared data

Derive ordinary inputs plus a bounded set of edges from necessary assumptions.
Rank by relevance to intent, plausibility, assessability and additional coverage,
not by whether the author later reported that failure.

- Multiple compatible cases can share one dataset; one case need not cover every
  goal. Do not impose a quota or add duplicate cases to inflate coverage.
- Separate incompatible states rather than making a contradictory fixture.
  Do not silently launch extra scenarios to accommodate every candidate.
- Include coherent underlying facts, source materials and queryable observations.
  Do not perform the tested discovery in advance or plant an oracle in the task.
- A legitimate tool response may contain the answer. The objective is preserving
  the required investigation, not hiding useful evidence.
- Synthetic tools must allow both correct and incorrect decisions and record
  actual submissions. They must not enforce the expected outcome for the agent.
- Reuse relevant existing project data when sufficient. Generating data does not
  mean replacing every real project with an unrelated toy task.
- Record cross-case cues, simplifying catalogs, and interactions. Cases combined
  in one trial are not independent experiments.

Antagonist reasoning may propose edges within this preparation step. It is not a
mandatory additional agent or separate paid review pass, and it cannot predict
which edge will become a future incident.

### E. Preflight, then freeze

Before paid trials, exercise the tools and premises needed to answer the task:
relevant reads/queries, artifact writes, local tests, and safe action recording.
Do not confuse an intentionally modeled limitation with an accidental harness
failure. A workflow requiring subagents or approval cannot be validated by a
host that lacks that capability without an explicitly narrower conclusion.

When dates matter, specify a shared assessment time/timezone and coherent tool
responses. Do not patch the clock only after inspecting an unfavorable answer.
When state matters, include permissions, branch/remote status and relevant user
work. Never use real credentials or allow external publishing for fixture actions.

Freeze task, data, instruction versions/references, tool behavior, private
criteria, execution settings and agreed trial budget. No worker may edit a live
launcher or its dependencies. Capture provenance before execution, not afterward.
Fail preflight rather than spend trials on known missing required capabilities.

### F. Execute and assess

Use identical tasks/data/tool access on independent Before/After copies; only the
selected instruction version changes. Keep existing default 3+3 and explicit
fast-mode behavior. More cases can increase tokens within each trial; do not
promise fixed cost simply because the trial count is unchanged.

After execution, distinguish:

1. Did the trial reach each selected condition?
2. Did actual behavior satisfy the corresponding intent?
3. Was the observation interpretable, or interrupted/blocked by the environment?
4. Did the automatic report identify the same finding?

Inspect actions, returned evidence and submitted artifacts, not only narration.
A nonempty provider error is not successful completion. A normal child return is
not completion of its caller. Do not count quota/permission interruption as a
skill defect. Preserve the first results; no retuning/retries to force a finding.

## 5. Materializing data without inventing a new execution platform

Preferred implementation: use existing isolated scratch-repository semantics,
not a new generic tool simulator, fixture DSL, or public CLI mode.

For a comparison needing generated shared files:

1. Prepare a private scratch project from the selected baseline/project state.
   Keep purpose, ground truth, preparation notes and source metadata OUTSIDE it.
2. Materialize the scenario's common data there. This includes any deliberately
   selected contextual working state; record deviations from the user's project.
   Never edit, stage, stash or commit files in the user's real checkout.
3. Make common data part of the scratch baseline that the runner archives.
   Ensure the Before instruction matches the selected real baseline; then apply
   only the selected After instruction in the scratch working tree.
4. Invoke the existing runner from that scratch project. Verify that generated
   files are present and identical in every trial, and that only the instruction
   version differs. Preserve legitimate absent-file and explicit-before semantics.
5. Source provenance must continue to name the original repository/revisions,
   never scratch commits. Source metadata does not imply full-PR coverage.

Do not assume scratch staging solves every environment. Git history, uncommitted
state, dynamic service observations, writable tool permissions, inline skill
loading and multi-file version changes need faithful capabilities. The existing
single-file runner does not automatically provide them. If a required setup is
unsupported, report that before launch; do not quietly omit it or claim full
workflow coverage. General multi-file historical replay is out of scope here.

Prefer documented orchestration using existing supported mechanics. If reliable
shared-file staging needs code, add the smallest private helper under the canonical
skill scripts, with deterministic boundary tests. Do not add new CLI flags or
public schemas by implication; explain any unavoidable contract extension before
implementation. A recipe that never delivers its generated data is not acceptable.

PR 1 delivers this shared-data path for an already selected task and dataset,
including its canonical skill entry point. PR 2 adds the full intent-driven
generation workflow that consumes it. Do not merge an unused helper or describe
the new generator as shipped after PR 1 alone.

## 6. File-level implementation checklist

This checklist describes the cumulative preparation deliverable. Section 9
assigns work to PRs; each PR includes its own documentation and verification.

1. **`plugin/skills/behavior-diff/SKILL.md`**
   - Update Ownership and replace task-only step 2 with the preparation sequence.
   - Replace the mandatory incident question with available-context derivation.
   - Preserve step 1 purpose/provenance boundaries and model selection defaults.
   - Change step 3's readiness condition from task-known to preparation-frozen.
   - Extend step 4's evidence-based summary to selected outcomes and coverage.
   - Keep the main skill readable. Put the detailed recipe in one canonical
     reference such as `references/scenario-and-test-data.md`, explicitly read
     before preparation. Do not maintain two divergent copies of the recipe.
2. **Preparation support, only if needed for actual staging**
   - Reuse current snapshot construction and Spacedock fixture conventions where
     applicable; inspect `references/spacedock-duo.md` before touching that lane.
   - No special-case EveryInc adapter in the product. No unconditional model-call
     additions. No generic mock toolkit disguised as a skill wording change.
3. **`docs/architecture.md`**
   - Update skill responsibilities, the ASCII flowchart and scenario construction
     explanation to include shared data preparation/preflight and private criteria.
   - Keep script/model/report ownership accurate.
4. **`README.md`**
   - Describe intent-driven task/data preparation and bounded coverage, not a
     guarantee of finding side effects or validating every skill goal.
5. **Relevant deterministic tests**
   - Inspect `tests/purpose-handoff-test.py`, `tests/source-provenance-test.py`,
     `tests/hooks-test.sh` and `tests/live-report-contract.sh` for affected contracts.
   - Extend behavior/boundary tests only where implementation changes contracts.
     Do not assert exact skill wording or add tests that merely search source text.
   - Do not repair wording-only tests by repinning new prose.

This planning request does not authorize a plugin version bump, release, commit,
push, or opening PRs. Implementation proceeds in the sequence below when started.
Keep host manifests aligned if a later release changes them.

## 7. Acceptance criteria

| ID | Observable acceptance |
|---|---|
| AC1 | A local modification with no incident report produces a purpose, natural task and deliberate data from available intent without demanding a user-authored eval |
| AC2 | Private preparation records connect each selected case to a capability, premises, evidence criteria and omissions; multiple edges are allowed but not exhaustive |
| AC3 | Both variants actually receive the same generated data and tool observations; generated files do not disappear at git archive or leak into the user's checkout |
| AC4 | Discovery remains executable work; task/project inputs contain no private assessment oracle or later-fix answer |
| AC5 | Environmental requirements are exercised before execution; unsupported capabilities produce an explicit blocked/narrow-scope result, not a fake skill finding |
| AC6 | Dates and permissions are explicit when relevant; supplied facts and expected outcomes are internally consistent |
| AC7 | Existing trial counts, purpose/source isolation and model-role defaults remain intact on Claude Code and Codex; execution model is not silently upgraded |
| AC8 | The result distinguishes reached/missed/unknown conditions, unmet After intent, infrastructure failures and automatic-report coverage |
| AC9 | A frozen run cannot be modified by preparation workers; negative results do not trigger hidden fixture edits or reruns |
| AC10 | A smoke run proves the modified skill prepares usable inputs and the runner consumes them; Markdown edits alone are not completion |

Do not require reproducing the EveryInc historical defect as a release gate.
Generation and execution are stochastic, and that replay was incomplete. Validate
preparation quality and observable contracts rather than guaranteeing a failure.

AC8 is satisfied in the preparation milestone by the canonical skill's
evidence-based result explanation and private assessment notes, using the current
report as a separate artifact. It does not require a new UI, persisted coverage
schema, or extractor contract. Any automatic-report limitation remains explicit.

## 8. Verification and handoff checkpoints

### Deterministic checks

Follow AGENTS.md's current verification commands. Markdown-only work requires
`git diff --check`; if scripts change, run repository formatting checks and the
relevant deterministic suites. CI must not invoke a model CLI or live runner.

For any staging helper, test consumer-visible invariants: shared files arrive in
both variants; original checkout remains unchanged; assessment data stays out;
selected Before/After content is preserved; unsupported/path-escape inputs are
rejected. Use synthetic fixtures only.

### Smoke proof

- First exercise staging with disposable synthetic files and inspect actual
  constructed trial inputs. Use existing deterministic harness conventions.
- Then run the modified canonical skill on a synthetic instruction edit with
  clear intent, an ordinary case and compatible boundary conditions. Check that
  the skill itself generated/prepared the inputs; do not handwrite a perfect
  scenario and call that proof of the new generator.
- Inspect generation and execution separately. Record preparation, trial and
  extraction models/settings, source access, omitted cases and actual artifacts.
- Verify the core mechanics on both supported hosts; state any unavailable live
  host gate instead of claiming parity from one host's output.
- Set concrete time/cost bounds before paid verification. The user has given
  standing approval for requested Behavior Diff experiments in this repository;
  do not repeatedly request the same cost authorization. Sensitive-data sharing,
  new external effects and substantial scope changes still require approval.
- Do not assume previous provider limits have reset; check availability before
  launching. Never replace a requested model to evade a quota. If blocked, finish
  deterministic work and report the missing live verification gate.

Before proposing a PR, obtain an independent read-only review under
REVIEWER_GUIDELINES.md. Review safety, snapshot fidelity and intent leakage as
well as prose clarity. Update docs in the same change; remove obsolete task-only
instructions rather than retaining conflicting alternatives.

### Suggested skills for the next session

- `behavior-diff`: required for live comparisons and model/provenance boundaries.
- `design-an-interface`: if an unavoidable staging API/helper contract is needed;
  compare small designs before adding a new public interface.
- `review` or `review-by-subagent`: independent review when requested/required.
- `diagnose`: investigate actual runtime failures without labeling them as skill
  findings. No need to repeat successful setup or reproduce a reported quota error.

### Final developer delivery

List changed canonical files, what now generates/materializes the data, executed
checks and smoke evidence, remaining limits, and whether the automatic report
actually expressed the raw finding. Do not claim the main-goal escalation arm,
full multi-file replay, or a new automated verdict system was delivered.

## 9. Ordered PR plan

### Delivery boundaries and status

The user deferred report UI design on 2026-10-19. The earlier layout preview is
exploratory, not an accepted design or an implementation dependency. Revisit it
only after observing results from the completed preparation workflow.

| Stage | Deliverable | Dependency | Status |
|---|---|---|---|
| PR 1 | Deliver prepared shared data to real Before/After snapshots safely | None | Merged as #49; deterministic checks, independent review and corrected dogfood CI passed |
| PR 2 | Generate and preflight scenario/data from intent, then execute and explain evidence | PR 1 | Published as #50; independently approved; corrected dogfood CI remains the merge gate |
| Preparation acceptance gate | Verify the integrated workflow against AC1–AC10 | PR 2 | Passed at bounded two-host evidence level; limitations retained below |
| Report design checkpoint | Decide what actual results need the report to communicate | Preparation acceptance gate | Deferred; requires user design review |
| Later report PR(s) | Implement only the agreed assessment/presentation changes | Accepted report design | Not scoped or authorized by this plan |

PR numbers here are sequence labels, not GitHub PR identifiers. Do not split out
tests, docs, or smoke proof into a later PR to make an incomplete feature mergeable.
The acceptance gate is verification of PR 2, not a third implementation PR.

### PR 1 — Deliver shared scenario data safely

**User-visible result:** for an already selected task and dataset, the canonical
skill can arrange an isolated comparison where all trials receive the intended
common files without changing the user's checkout.

**Scope**

- Implement the scratch-project orchestration in section 5 using existing
  supported mechanics. Add a private helper only if necessary for reliable
  staging; agree any unavoidable interface extension before implementing it.
- Wire the path into the canonical skill for tasks that need prepared shared
  files. Put delivery instructions in the canonical scenario/test-data reference
  that PR 2 will extend, not a second competing recipe.
- Preserve real Before/After instruction selection, legitimate absent-file and
  explicit-before semantics, and original source provenance. Exclude purpose,
  expected answers and preparation notes from the trial snapshots.
- Freeze the delivered common inputs before execution. Fail before launch when
  required project state cannot be represented faithfully by the existing runner.
- Update the relevant snapshot/delivery documentation and boundary tests in this
  PR. Do not advertise autonomous intent-driven generation yet.

**Expected files:** canonical skill and preparation reference; a private script
only if needed; relevant snapshot, purpose-isolation and source-provenance tests;
the affected architecture section and README usage explanation.

**Verification and merge gate**

- Exercise the shipped snapshot path with disposable synthetic data and the
  repository's deterministic host stubs. Inspect actual constructed trial inputs,
  not only helper output.
- Establish common-file equality, correct instruction differences, exclusion of
  private assessment material, original-checkout preservation and correct source
  provenance. Cover applicable absent-file, explicit-before, path-escape and
  unsupported-setup boundaries.
- Exercise mechanics for both Claude Code and Codex. A stubbed run proves delivery
  mechanics, not that a model generates good scenarios or follows the skill.
- Run affected deterministic checks and formatting checks, and obtain an
  independent read-only approval under REVIEWER_GUIDELINES.md before opening a PR.

**Not included:** autonomous scenario generation, report changes, a new fixture
DSL, generic tool simulator, public CLI mode, or multi-file historical replay.

**Delivery and verification record**

- Merged as [#49](https://github.com/spacedock-dev/behavior-diff/pull/49).
  Added private `prepare_shared.py` staging/verification and the canonical
  delivery reference without changing the public runner interface.
- The final PR 1 shared-data suite passed 31 checks with `--runner-smoke`.
  It exercised actual snapshots, normal and explicit fast counts, absent and
  explicit Before, private-context exclusion, provenance and original state.
  Boundary regressions cover unsafe paths, unsupported state, frozen-input
  changes, Git environment redirection and archive transformations.
- A late CI failure exposed nested comparisons sharing their orchestrator's
  runs store. Every trial now inherits its own `BEHAVIOR_DIFF_HOME`; actual
  nested-run smoke tests verify the isolation. The old CI logs were unavailable,
  so nesting was not established as that particular run's historical cause.
- Required deterministic checks and independent reviews passed. The corrected
  dogfood run completed six trials, extraction and report publication.
  CI's ordinary helper checks remain model-free; runner smoke remains manual.
- Later approved historical replays inspected raw evidence. The single-file
  replay exercised the new delivery helper; a multi-file replay was explicitly
  a historical control, not helper acceptance evidence. Neither reused fixture
  proves autonomous generation. That proof belongs to PR 2.

### PR 2 — Prepare scenario and data from intent

**User-visible result:** a local instruction edit, without an incident report or
user-authored evaluation dataset, can produce a deliberate scenario and shared
data, preflight/freeze them, run the comparison, and explain the observed outcome.

**Scope**

- Implement the complete recipe in section 4: intent and preservation goals →
  observable capabilities → natural task → coherent ordinary/edge data →
  preflight/freeze → execution → evidence-based interpretation.
- Replace the mandatory incident question and task-known readiness condition.
  Keep discovery as agent work; record selected cases, premises, evidence criteria
  and omissions privately rather than embedding an assessment oracle in inputs.
- Reuse PR 1's delivery path for generated files and existing project data where
  sufficient. Make required date, permission and tool premises explicit.
- Preserve trial counts, host parity and model-role defaults. Keep unsupported
  capabilities visibly blocked instead of silently narrowing the experiment.
- Update the skill's result explanation to cover condition reach, unmet After
  intent, interruptions and raw-evidence versus automatic-report differences.
  Do not redesign the report renderer, extraction semantics or report schema.
  The later user-authorized CI correction below changes prompt transport only.
- Update the full workflow/flowchart and product explanation in the same PR.
  Add or adjust deterministic tests only for changed behavioral contracts.

**Expected files:** canonical skill, its single preparation reference, relevant
existing tests, docs/architecture.md and README.md; PR 1 support only if integrating
the real generator exposes a delivery defect.

**Verification and merge gate**

- Run affected deterministic checks and the repository's required gates.
- Follow section 8's bounded live smoke procedure on a synthetic instruction edit:
  the modified skill itself must generate the scenario/data, not receive a
  hand-authored successful preparation.
- Inspect actual snapshots and trial evidence for an ordinary case and compatible
  boundary conditions. Check preparation separately from execution and extraction.
  An unmet goal or inconclusive trial is valid; reproducing a defect is not a gate.
- Verify both supported hosts, recording unavailable live gates honestly. Do not
  call the integrated workflow complete while required verification is blocked.
- Obtain independent read-only approval before opening the PR. Keep private
  artifacts outside tracked files; public evidence summaries must be synthetic
  or sanitized and must not imply stronger findings than the records support.

**Local implementation and live evidence**

- Canonical skill and its reference now own intent-driven preparation and
  per-case raw assessment. README and architecture describe that workflow.
  Delivery scripts, report schemas and renderer are unchanged.
  A post-publication CI correction sends Claude extraction prompts over stdin
  instead of argv to avoid Linux's per-argument size limit. Prompt contents,
  models, extraction semantics and failure handling remain unchanged.
  Removed affected wording-only assertions instead of pinning the new prose.
- Required deterministic suites passed, including 31 shared-data checks with
  runner smoke. Repository Bash/Python formatting, changed-shell syntax and
  ShellCheck passed. The report contract passed again after the final assertion
  removal.
- A fresh Codex session received only a synthetic local invoice-review edit,
  with no incident, task or dataset. It generated a neutral task, four common
  data files, private goals/case criteria, capability probes and a frozen stage.
  One ordinary match, a previously paid invoice and an ambiguous match shared
  one coherent batch. The operator audited the inputs and additionally proved
  read/CSV/arithmetic/scratch-write capabilities under native trial settings.
- The actual runner consumed those generated inputs in three Before and three
  After attempts. All six initial snapshots had identical common files and
  the correct instruction version; private criteria were absent, all six
  traces recorded the relevant source rows, and the original project remained
  unchanged. Trial selection resolved to `gpt-6.1-sol`; extraction resolved to
  `gpt-6-luna`. Preparation requested `gpt-6.1-sol` separately.
- Five attempts completed: two Before and three After. All five recommended
  the ordinary match, excluded the paid invoice and held the ambiguous match.
  The remaining Before attempt failed with a model-capacity error after
  reading the records. Its outcomes are unassessable, not evidence that the
  instruction edit helped. No trial was retried or model substituted.
- The unchanged automatic report counted the interrupted attempt as valid and
  could not assess source agreement despite the raw traces containing the
  source rows. This is a report/normalization limitation, not a generated-data
  defect. The skill now explicitly checks CLI status and native terminal events
  before treating normalized text as completion. Report fixes remain deferred.
- A separate native Codex continuation executed the revised skill's result
  explanation against the frozen notes and saved evidence. It read native
  terminal events, identified the capacity interruption and both report gaps,
  and assessed condition reach separately from outcomes for every case.
  It found no contradicted goal among completed attempts and made no causal
  improvement claim. This was host explanation, not another extraction or trial.
- Independent round one found a missing historical isolation branch. After the
  frozen local comparison ended, the skill/reference were corrected to require
  fresh context before historical purpose derivation when later outcomes are
  already known. The local-edit smoke does not exercise that historical branch.
- Claude Code initially stopped before its first model call because authentication
  had expired. That startup record was preserved. After the user restored native
  authentication, a fresh Claude preparation generated its own neutral task,
  three CSV files, seven cases and private criteria without an incident or dataset.
  Three ordinary cases and four compatible boundaries shared one batch.
- All six Claude trials completed on `claude-opus-5-5`, with default Sonnet
  extraction. Actual snapshots contained identical common data, correct
  instruction versions and no private criteria; raw returns contained the sources.
  All six recommended the same three invoices totaling $9,315.50 and withheld the
  four questionable invoices. No payments occurred; this shows no added decision
  benefit from the edit on these inputs.
- Native Claude result explanation inspected raw evidence and identified report
  gaps. It also corrected a frozen preparation-note assumption: Write/Edit tools
  were available, although unused. The observed read-only actions support local
  behavior, not a claim that host permissions made writes impossible. Its use of
  “paid” in summary wording means recommended payment, not an executed action.
- Codex preparation/execution used the pre-historical-isolation-fix snapshot;
  its later explanation and the entire Claude smoke used the corrected source.
  Both smoke cases are local edits, not live coverage of historical isolation.
  Two independent reviewers approved the source in round two and the final
  two-host acceptance evidence in round three, including these limitations.

### Acceptance ownership

| Criterion | Primary delivery and proof |
|---|---|
| AC1 — no incident/eval required | PR 2; skill-generated preparation smoke |
| AC2 — capability/case/premise mapping | PR 2; inspect private preparation records |
| AC3 — identical shared inputs | PR 1 delivery proof; repeat with PR 2 generated data |
| AC4 — discovery and oracle isolation | PR 1 exclusion boundaries; PR 2 scenario/data audit |
| AC5 — environmental preflight | PR 1 delivery limits; PR 2 capability-level preflight |
| AC6 — dates, permissions and coherent facts | PR 2 preflight and fixture audit |
| AC7 — counts, roles, isolation and host parity | Both PRs; deterministic mechanics plus PR 2 live gates |
| AC8 — outcome, reach and report distinctions | PR 2 skill explanation; existing automatic report unchanged |
| AC9 — freeze and preserve first results | PR 1 delivery freeze; PR 2 full preparation/execution discipline |
| AC10 — skill prepares, runner consumes | PR 2 integrated smoke using PR 1's proven delivery path |

The two local smoke paths supply bounded evidence for AC1–AC10, not general
reliability or historical-isolation coverage. Preserve the interrupted Codex
attempt, initial Claude authentication failure and permission-note correction.

### Deferred report design checkpoint

After preparation passes the acceptance gate, review the generated scenario,
selected cases, private criteria, trial evidence, current automatic report and
skill explanation together. Identify concrete information gaps before selecting
a layout. Do not assume the earlier assumption-first prototype is the winner.

Keep the existing target assessment as the starting point: goal-linked criteria
and per-trial `met`, `not_met`, `uncertain`, and `unassessable` outcomes. Investigate
whether actual runs require persisted case links, condition-reach records,
preflight/run-health context or raw-audit/report-disagreement records. These are
possible contract changes, not fields authorized for PRs 1–2.

If the agreed design needs new assessment data, scope that producer/validator/
consumer change explicitly before the UI PR. If existing data is sufficient, do
not create an extra schema PR. Preview report hierarchy changes against the saved
real-case evidence required by CODING_GUIDELINES.md; label new-state illustrations
as authored synthetic examples. Keep HTML, Markdown and structured output aligned.
Choose the final number and boundaries of report PRs at that checkpoint.

### PR 3 — Approved assumption-first report

User approval follows private previews of the three required historical examples
and supplemental saved cases. Preview interpretations were authored from audits,
not proof of extractor adherence; do not copy their conclusions into report data.

- Preserve the six-tab report shell. Summary owns five ordered steps: finding;
  expected versus observed; how tested; evidence; next action.
- Keep repository/PR links, compared revisions and model visible in a compact
  metadata strip. Expand full task, reading help and detailed evidence on demand.
- Use “The expected improvement did not happen in these tests” for observed
  unmet requirements. No-gap results require supported coverage; distinguish
  already-correct Before, preservation, uncertain outcomes and incomplete runs.
- Reuse validated target checks, purpose and saved evidence. Repair call-versus-
  return evidence handling, rejection diagnostics and native interruption accounting.
  Do not weaken source-consistency checks or reconstruct private case criteria.
- Keep HTML, Markdown and schema-17 structured conclusions consistent.
  Understand the change labels model interpretation below the same conclusion.
  The blind quiz excludes new assessment/setup/next-action content while retaining
  observed comparisons; no paid evaluation is part of this change.
- Verify deterministic contracts and the shipped renderer on synthetic and saved
  evidence, then complete independent read-only review and open a PR. Saved
  invalid extractions remain unavailable; showing audited historical findings
  automatically requires a separately approved fresh extraction, not UI editing.

Tracking: DRC-4835. The approved prototype is temporary and is not a product route.

### Step-by-step implementation protocol

1. Start only the earliest unblocked PR. Inspect the current implementation and
   relevant experimental recipe before editing; the handoff is not proof that
   files have stayed unchanged.
2. Finish that PR's end-to-end behavior, docs, checks, smoke evidence and independent
   review. Report what it delivers and which milestone criteria remain.
3. Open/commit/push only when requested; use DCO sign-off for every commit. Do not
   merge implicitly. Base dependent work on the accepted predecessor; if stacking
   PRs, declare the base and dependency and merge in order.
4. Track the executable work in the designated Linear project with the
   `behavior-diff` label. PRs 1–2 are Improvements; a separate evidence-only task
   is Verification. Publish the proposed ticket breakdown after user review,
   reuse existing tickets where applicable, and keep blocked work out of High.
5. After PR 2, record the AC1–AC10 gate results. Only then reopen report design
   with the user; no report redesign is required to finish the preparation work.
