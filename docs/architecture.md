# Behavior Diff architecture

Behavior Diff is a local agent plugin that compares behavior before and after
an instruction-file change. It connects a user request, controlled agent trials,
evidence analysis, and a report. The user decides whether the observed change
meets their intent.

The installable source lives in [`plugin/`](../plugin/), with manifests for
Claude Code and Codex. Skills define the agent workflow. Shared Bash and Python
scripts handle execution, evidence, and reporting.

## System flow

```text
+---------------------------------------------------------+
| User in Claude Code or Codex                            |
| Direct request or accepted edit-hook suggestion         |
+----------------------------+----------------------------+
                             v
+---------------------------------------------------------+
| Skill preparation (LLM; reference recipe)               |
| Change intent + preservation -> capabilities/premises   |
| -> neutral task + ordinary/bounded edge data + private  |
| case criteria; reuse sufficient project data            |
| Review scenario, checks and required recorded sources; |
| freeze task, data, purpose, record, sources + settings   |
| prepare_shared.py freezes one complete private handoff  |
| Staged data or direct project -> verify -> runner args  |
+----------------------------+----------------------------+
                             v
+---------------------------------------------------------+
| Runner: default 3+3 trials                              |
| behavior-diff.sh builds independent Before/After copies |
| run-trial.sh runs the same task/model in each copy      |
+----------------------------+----------------------------+
                             v
+---------------------------------------------------------+
| Saved evidence                                          |
| Snapshots, calls + returned content, answers, grades     |
+----------------------------+----------------------------+
                             v
+---------------------------------------------------------+
| Evidence analysis                                       |
| decisions.py: frozen checks + calls/returns + answers    |
| Validate identities; isolate check evidence failures    |
| reporting/: derive scoped assessment + linked evidence |
+----------------------------+----------------------------+
                             v
+---------------------------------------------------------+
| Presentation                                            |
| render.py -> consistent HTML, Markdown, structured JSON |
| Observation-first Summary; details retain evidence      |
+----------------------------+----------------------------+
                             v
+---------------------------------------------------------+
| Skill result explanation (separate from the report)     |
| Optional approved Jev advice -> primary-evidence check  |
| audit_evidence.py -> original calls/returns/artifacts   |
| reached / missed / unknown; intent supported /          |
| contradicted / insufficient evidence; run health apart; |
| report agreement or gap disclosed; user decides         |
+---------------------------------------------------------+
```

```text
Runner -----------------> status.json
Trial workers ----------> before-N/status.json, after-N/status.json
Assessment producer ----> assessment-status.json
                                  |
                                  v
                        status.py (read-only)
                        snapshot / JSON / watch / list
```

Trial execution and decision extraction call models through agent CLIs.
Report assembly and rendering run locally without model calls.

Purpose and the reviewed scenario record travel in run configuration directly to
analysis, never in the trial task or project copies. Raw preparation notes remain
private. Recorded tool calls and returns travel from trials to analysis; the
collector does not retrieve current source files.

Historical source provenance takes a separate path: the skill verifies the
original repository, revision pair, and any PR/MR associations, then passes
`--source-file` to the runner. `source.py` validates the supplied URLs and hashes;
the runner freezes normalized metadata in `config.json`. It is report context,
not trial or assessment instructions. Neither validation nor rendering queries
the forge or infers provenance from a temporary fixture repository.

```text
Explicit source file -----+
                          +--> frozen config --> report header
Otherwise CI context -----+
```

Without explicit source provenance, `ci_context.py` projects whitelisted
GitHub Actions environment/event fields or GitLab CI variables into validated
repository and workflow PR/MR links. The runner freezes `ci_context` in run
configuration; the renderer never reads live CI state. Source provenance takes
precedence. CI context supplies no Before/After commit IDs and is not added to
trial or assessment prompts. Malformed optional context degrades to a
repository-only header or no context, without blocking the comparison.

## 1. Plugin entry points and hooks

The user can request the skill directly. The plugin can also suggest it after
an agent edits `CLAUDE.md`, `AGENTS.md`, or `SKILL.md`.

The [hook configuration](../plugin/hooks/hooks.json) connects host events to
scripts in [`plugin/scripts/`](../plugin/scripts/):

- `rules-edit-backup.sh` saves Before content for untracked instruction files
  before supported edits. Tracked files normally use Git HEAD instead.
- `rules-edit-detect.sh` records edited paths and asks the host agent to offer
  Behavior Diff after the current task.
- `rules-edit-remind.sh` provides a fallback reminder without a duplicate offer.

Hooks supply baselines and discovery, not trial execution. A hook suggestion
requires explicit user acceptance. Hook failures do not block the host session.

## 2. The skill owns the experiment

[`SKILL.md`](../plugin/skills/behavior-diff/SKILL.md) guides the host agent to
select the changed file and prepare the comparison from the change's intent. The
agent itself designs the scenario and any test data; the
[skill reference](../plugin/skills/behavior-diff/references/scenario-and-test-data.md)
holds the detailed recipe. In short, the agent derives the intended change and
the behavior it must preserve, the capabilities and premises that behavior
needs, a neutral task that starts before the tested work, coherent ordinary and
bounded edge-case data, and private per-case criteria. It reuses sufficient
project data instead of generating more. It asks the user only when a material
requirement cannot be reached otherwise. The task must not reveal the expected
behavior. The instruction change must remain the only source of that guidance.

Before launch, the skill preflights the real host environment and freezes the
task, data, criteria, purpose, source revisions, and execution settings. It then
runs the existing runner with the default trial counts; more edge cases add
coverage within those trials rather than more runs. When common files must be
added or private paths excluded, the skill delivers reviewed data through a
frozen stage (see [Shared-data delivery](#shared-data-delivery)). It owns scenario
quality and interpretation, not filesystem copying or report formatting.

After the run, the skill explains the result separately from the automatic
report: per private case it reads raw actions, returns, and artifacts, then
states whether each case was reached, missed, or unknown, and whether the intent
is supported, contradicted, or lacks evidence. Run health stays separate from
requirement failures. The coverage is bounded to the designed cases; it does
not prove the absence of unknown side effects.

Before execution, the skill records distinct concise goals and their provenance
(`session`, `commit`, or `diff`; `explicit` or `inferred`) in a reviewed purpose
file. It uses available conversation context, not transcript-store searches.
Historical comparisons use the relevant commit history; absent motivation falls
back to a labeled diff inference. Raw conversation and unrelated private details
are excluded. Purpose is the question, not evidence of success. The user-facing
consent covers bounded source returns reaching assessment; filtering cannot
certify arbitrary prose as free of private information.

For historical comparisons, the skill records full Before/After commit hashes
and the original repository's HTTPS URL. It includes PR/MR numbers, titles, URLs,
and side associations only when verified. Missing associations are omitted.
Ordinary uncommitted edits retain file labels rather than invented commit links.
HTML presents the repository and related requests on one compact line, followed
by linked revisions; local comparison labels are collapsed. Markdown and
structured report JSON retain the same source provenance. Existing saved runs
without source metadata remain renderable with their original labels.

For its own user-facing result summary, the host invokes an installed Humanizer
skill when available. Otherwise it writes concise, natural technical prose
itself. This prose-only step preserves evidence qualifiers, counts, citations
and links, exact quotes, code, and excerpts. It never edits saved report artifacts.
Both canonical skills orient the conversation summary around the task, the
changed skill's role when relevant, and the tested decision point. They explain
unfamiliar names by their evidenced function, without guessed expansions or
author motives, and preserve shared behavior, mixed branches, and evidence limits.
Matching action flows do not imply matching final answers or a missed decision
point. The skills inspect answers separately and distinguish unchanged behavior
with the target situation reached, not reached, or unknown from the evidence.
Only an evidenced missed situation warrants that explanation and a sharper task.

Both host skills load the shared [Jev contract](../plugin/skills/behavior-diff/references/jev.md)
before result assessment. The outer skill may send approved, sanitized observations
to TypeSafe via `scripts/jev.py`, a standard-library helper shared by both hosts.
`judge` groups independent questions in one POST; `judge_batch` submits keyed
states under the same questions with at most four concurrent requests. It validates
typed answers, returned Jev identity and usage, preserving per-state failures.
The official HTTPS endpoint is fixed; configuration errors skip safely, provider
failures are sanitized, and there are no redirects, retries, or provider fallbacks.
Credentials stay in the named environment variable, not arguments or report config.

This is separate from extraction: no new report artifact or extraction call.
The skill owns provider/data/cost approval, minimum payload selection, checking
judgments against primary evidence, and final-response disclosure. Advice cannot
authorize actions or rewrite frozen inputs/reports. Missing configuration or
failed assistance uses the existing assessment. Hermetic tests exercise helper
plumbing; live host usefulness and instruction compliance require manual approval.

## 3. The execution layer produces comparable trials

[`behavior-diff.sh`](../plugin/skills/behavior-diff/scripts/behavior-diff.sh)
coordinates one comparison. It resolves the Before version from an explicit
file, Git HEAD, or a hook baseline. It creates one project copy per trial and
installs the appropriate instruction version.

For Git projects, copies start from `git archive HEAD`. Only the selected
instruction change enters the After copies. Other uncommitted edits stay out.
Without a usable Git HEAD, the runner copies the folder instead.
The front door anchors relative purpose-file paths to the invocation directory
before entering the repository. The runner freezes that file for assessment and
removes its project-local copy from trial inputs. It rejects snapshot parent
symlinks before removal or launching that trial, so exclusion cannot delete an
external file through a baseline symlink.

[`run-trial.sh`](../plugin/skills/behavior-diff/scripts/run-trial.sh) runs one
fresh agent process inside one copy. The default comparison runs three trials
per side concurrently, with the same task and model. The adapter supports
Claude, Codex, Pi, and OMP. It suppresses recursive plugin hooks and converts
host events into a common `trace.jsonl` format.
OMP trials apply the shared `omp-isolation.json` process-local config overlay
with `advisor.enabled: false`, so inherited advisors cannot join or steer them.
Normal trial tools, the primary model and reasoning settings, trial-local storage,
and native trace normalization are unchanged; user configuration is not edited.
Claude, Codex, and Pi do not use this OMP advisor subsystem.

The trace contains paired tool actions and recorded returns plus a final answer.
Claude's stream is retained; Codex command output and Pi/OMP tool results keep
their call identities during normalization. Raw host logs and stderr remain
available where captured. After trials finish, `grades.tsv` records `REVIEW`
for a normalized final answer, otherwise `BLOCKED`. Analysis and report loading
also inspect saved native status: a nonzero CLI exit, interruption or unfinished
worker overrides a normalized final answer. Older runs without status retain
their recorded grading. Completion is not correctness.

Trial and extraction models have separate roles. Claude defaults to Opus for
trials and Sonnet for extraction. Codex uses Sol and Luna, respectively.
`codex_model.py` resolves Codex selectors to concrete IDs. Both trial variants
use the same resolved ID. [Model selection](../README.md#trial-and-extraction-models)
describes overrides and Pi/OMP behavior.

### Background progress

Each comparison receives an atomically allocated, timestamp-prefixed unique run
directory. The runner prints that handle and absolute status/watch commands at
startup. Independent comparisons and their trials remain concurrent.

`progress.py` writes private, versioned operational metadata with atomic file
replacement. The runner owns `status.json`; each worker owns its trial's
`status.json` outside `project/`; `decisions.py` owns `assessment-status.json`.
There is no shared index or lock. These records contain lifecycle and process
identity, not prompts, answers, tool payloads, or environment dumps.

`status.py` reads those bounded records without parsing evidence or changing the
run. Human and JSON views distinguish recorded state from observed local process
liveness. Host/boot and process-start identity protect against PID reuse;
unverifiable identity is uncertain, not a failure. Controller loss does not
prove that its workers stopped. Per-record timestamps and observation time make
the independent snapshots explicit.

Trial completion, final-result presence, assessment availability, and report
availability are separate facts. Extraction can be skipped or fail while a
fallback report remains available. A completed trial is never labeled a pass.
Watch is an independent reader; closing it cannot cancel execution. Older runs
without metadata remain readable reports, but have no reconstructed progress.

### How Before/After scenarios are built

A scenario combines a task, project state, and an instruction version.
The skill prepares the task. The runner constructs the project state and
instruction versions without asking a model to rewrite either version.

1. **Choose the Before instruction.** The runner uses `--before-file` first.
   Otherwise, an existing target in Git HEAD supplies the Before version.
   The remaining case uses the newest hook baseline. A baseline marked `ABSENT` means
   the Before copy must not contain the file. Without a baseline, the runner
   stops rather than inventing an original.
2. **Build a fresh base for every trial.** In a Git project, `git archive HEAD`
   exports committed files into `before-N/project/` or `after-N/project/`.
   These are full copies, not branches or worktrees. Outside Git, a folder copy
   excludes `.git` and Behavior Diff storage.
3. **Install the instruction version.** Before retains the HEAD version,
   receives the explicit/baseline file, or removes the file for `ABSENT`.
   After always receives the selected file from the working directory.
   All other initial project files remain the same between sides.
4. **Run the same task independently.** Each copy gets a new Git repository
   and an initial snapshot commit. `run-trial.sh` receives that project directory,
   the shared `task.md`, and the selected model. The runner starts all trials
   as background processes and waits before analysis.

`run-trial.sh` gives every host a trial-local `BEHAVIOR_DIFF_HOME` at
`<trial>/behavior-diff-home`, outside `project/`. Nested comparisons and hook
baselines cannot populate the orchestrator's run directory or another trial's
store through the inherited variable. This applies to Claude Code, Codex, Pi,
and OMP; it isolates storage defaults, not filesystem access.

Each side contains `N` independent copies, not one shared directory:

```text
                  +-----------------------------+
                  | Common project base         |
                  | Git HEAD or folder copy     |
                  +--------------+--------------+
                                 |
               +-----------------+---------------+
               v                                 v
+-----------------------------+   +-----------------------------+
| Before: before-1..N/project |   | After: after-1..N/project   |
| Resolved Before instruction |   | Working-tree instruction    |
| or no file for ABSENT       |   | Selected file only          |
+-----------------------------+   +-----------------------------+
```

For example, a tracked instruction edit produces this initial state:

| Input | Before | After |
| --- | --- | --- |
| Project files | Git HEAD | Git HEAD |
| Selected instruction | HEAD version | Working-directory version |
| Task | Shared `task.md` | Shared `task.md` |
| Trial model | Selected model | Same selected model |
| Agent context and files | Fresh for each trial | Fresh for each trial |

The run keeps `task.md` and `config.json` at its root. Each `before-N/` and
`after-N/` directory contains `project/`, `trace.jsonl`, and `stderr.log`.
The configuration records the target path, task description, Before/After labels,
validated `purpose`, and nullable `scenario_record`. `--scenario-file` requires
purpose and is validated by `scenario.py` / `reporting/scenario.py` before model
discovery. Both context files are frozen before trials and excluded from trial
copies, including when supplied from within the source project. The scenario
record holds a summary, rationale, conditions, limitations and goal-linked checks;
it cannot contain trial outcomes. Every goal must have a check.
Uncommitted setup files do not enter Git-based trials. Required task state must
already exist in the base project, in a deliberately prepared fixture, or in a
shared-data stage.

### Shared-data delivery

The private helper
[`prepare_shared.py`](../plugin/skills/behavior-diff/scripts/prepare_shared.py)
delivers a reviewed data directory to every trial without changing the user's
checkout or adding runner options. It only delivers and verifies: the skill
designs the data, and the helper does not generate data, launch models, or infer
provenance. The optional private `--handoff` descriptor names task, purpose,
scenario, optional source, notes, required references, custom tools and settings.
It reuses the existing input readers and freezes those inputs plus shipped
mechanics; no executable is selected or run from JSON. Direct `freeze` requires
this descriptor and keeps the original project path, inventorying the effective
Git archive plus selected After, not unrelated working edits.

```text
Project base (Git HEAD or folder copy) --+
Reviewed data directory -----------------+--> stage/project: scratch commit
Selected Before (HEAD, file, or absent) -+     + After in the working tree
   minus --exclude paths                       stage/before: present Before
                                               stage/home: ABSENT marker
                                               stage/freeze.json
Private handoff + context --------------------> complete context/tool inventory
                                                       |
                       verify, then behavior-diff.sh from stage/project
                       with BEHAVIOR_DIFF_HOME=stage/home
                       and --before-file stage/before when present
Direct project ------------------------> freeze -> same verify/runner handoff
```

`prepare` resolves Before in the runner's order: an explicit file, the target
in Git HEAD, then the newest hook baseline. Only a store entry can mean
`ABSENT`. It copies the base, the data, and the selected Before into a new
scratch Git repository and commits them. The repository has no remote, and its
hooks and signing are off. The helper then writes After into the working tree.
A present Before, from HEAD or a file, is also frozen as the stage's `before`
file outside the scratch project. The skill passes that file to the runner
with `--before-file`, so the report labels Before with the frozen file rather
than a scratch commit. An absent Before has no such file; it receives a marker
in the stage's `home/baselines/`, and the runner resolves it there. The
existing runner then builds every trial from the scratch commit, unchanged.

The helper rejects links, special files, Git internals, submodules, unsafe or
colliding paths, data that replaces the instruction or an excluded path, and
inputs over `BEHAVIOR_DIFF_COPY_CAP_KB`. The caller excludes in-project purpose,
scenario, source, and evaluator files with `--exclude`. `prepare` also requires
`git archive` of the scratch commit to match the expected files. Therefore,
`.gitattributes` rules such as `export-ignore`, `export-subst`, or filters that
change archived files fail before launch.

`freeze.json` records the original project and commit, the target, the Before
mode, the scratch commit, exclusions, and the content and executable bit of
every archived and working file. `verify` compares the stage, including the
frozen Before file or absent marker, with this record immediately before
launch. The freeze detects changes. It is not a sandbox, and the stage files
are not read-only. Source provenance still names the original repository and
revisions, never scratch commits. Runs and reports stay under the stage's
`home/runs/`.

`verify --json` returns the complete inventory and validated runner arguments,
project and home. The skill inspects that handoff once and launches the fixed
existing runner only after re-verification in the same environment. Semantic
capability probes, source closure and privacy review remain with the agent;
digests cannot prove that a probe ran or succeeded.

The local [`audit_evidence.py`](../plugin/skills/behavior-diff/scripts/audit_evidence.py)
indexes every expected trial and every original normalized/native JSONL event
with exact line, byte and tool-part pointers, preserving duplicate identities,
missing/malformed/unsafe states, native errors, stderr and artifact locations.
Ignored/untracked artifacts are included without following links; their presence
does not establish authorship. Original byte pages have no assessment eligibility
filter or total source budget. This private navigation path neither changes
report/extractor contracts nor judges completion or any private case. The outer
agent still audits all cases in all trials against raw returns and artifacts.

### Trial execution sequence

One trial is shown below. The coordinator repeats this sequence for all
`2 x N` trials, with concurrent execution.

```text
behavior-diff.sh        run-trial.sh          Agent CLI
       |                     |                     |
       |-- start ----------->|                     |
       |                     |-- task + model ---->|
       |                     |< host events -------|
       |                     |                     |
       |                     | capture/normalize trace.jsonl
       |< process ends ------|
       |
       | wait for all 2 x N trials
       | write grades.tsv
       | call decisions.py, then render.py
       v
```

## 4. The analysis layer separates observations from interpretation

The modules below live in the skill's [`scripts/`](../plugin/skills/behavior-diff/scripts/) directory.

- **Model-based interpretation:** `decisions.py` reads the task, trial actions,
  final answers, numbered instruction-diff hunks, frozen purpose, and bounded
  recorded returns. Extractor prompts travel over stdin, not command-line
  arguments, so large comparisons do not hit the operating system's per-argument
  size limit. The same extraction call defines observable target criteria,
  required evidence, and per-trial outcomes (`met`, `not_met`, `uncertain`, or
  `unassessable`), alongside choices, primary task result, narrative, and attention.
  Criteria cover every purpose goal and use the same question on both sides.
  Correction, new/changed behavior, and preservation are supported separately.
  With frozen purpose, the same call also returns `purpose_summary`: one or two
  short plain sentences restating the goals. It is optional copy, accepted only
  beside frozen goals and dropped alone when malformed. It never replaces those
  goals or adds criteria, outcomes, or evidence.
  New raw branches supply `trials`,
  not aggregate counts. The script requires each completed trial exactly once
  per side of every row, derives `n`, and retains both in `decisions.json`.
  Foreign, duplicate, incomplete, or missing assignments invalidate the row.
  Count-only raw extraction is not accepted; saved normalized report evidence
  remains renderable. Membership validation cannot prove classification truth.
  Each trial summary names its exact Before/After records and separates answers
  and plans from recorded actions. The inferred aim cites instruction hunks
  independently of trial outcomes. The script validates references and exact
  choice coverage; invalid interpretation does not discard valid observations.
  OMP extraction uses the same bundled `omp-isolation.json` process-local
  `--config` overlay as OMP trials, with `advisor.enabled: false`. An inherited
  OMP advisor otherwise adds a separate model/provider review and headless
  shutdown wait. The override preserves the extraction prompt, model, reasoning
  settings, inherited context, and validation without editing user configuration.
  Claude, Codex, and Pi extraction do not use this OMP subsystem.
  This is not a replacement for the skill's required raw-evidence audit.
  Report narrative uses installed Humanizer prose guidance in the same
  extraction call, with concise, natural technical prose as the fallback.
  The extractor receives the guidance in its prompt; it does not invoke skill
  tools. No additional model call, dependency, installation, or download is
  required. Humanizer applies only to prose, preserving schema, trial
  memberships, counts, citations, evidence qualifiers, exact quotes, code,
  and source excerpts. Deterministic assembly and rendering do not humanize
  saved output or post-edit HTML.
  Before returning the extraction JSON, the extractor refines authored questions,
  labels, explanations, and findings into concrete, case-specific language.
  Frozen scenario checks are excluded from this prose refinement: their IDs,
  goals, wording, modes and evidence requirements must remain exact. For those
  checks the model supplies only row links and per-trial outcomes. Validation
  rejects missing, extra or rewritten checks even when every goal still has
  another criterion. Without a record, criteria are assessor-written after the
  trials and labeled accordingly. Refinement preserves evidence qualifiers and
  exact excerpts; it does not rewrite rendered artifacts.
  Discovery reads only `humanizer/SKILL.md` in the invoking repository's skill
  roots, then the user's. Claude checks `.claude/skills` before `.agents/skills`
  at each scope; other extraction hosts use `.agents/skills`. Emitted prompts
  use `CLAUDECODE` presence to select Claude's roots, otherwise the shared roots.
  The first usable UTF-8 skill document supplies guidance; unavailable or invalid
  files use the fallback. Discovery does not scan trial snapshots or load the
  instruction file under comparison as Humanizer guidance.
  Discovery requires a nonblank `target_file`. Self-reported live runs also
  record `compared_source_paths`: resolved absolute paths for the original
  target, scratch instruction copies, and external baseline sources. The list
  must include the resolved original target; `target_file` stays project-relative
  for snapshot diff lookup. Live extraction runs from the original project root.
  These sources are excluded even when display labels
  are descriptive rather than paths. Missing, malformed, or unresolvable source
  provenance selects plain-language fallback without reading installed skills.
- **Deterministic assembly:** `reporting/load.py` reads saved evidence and
  compares recorded command sequences. `reporting/instruction.py` supplies the
  instruction diff. `reporting/content.py` derives shared wording and evidence
  limits. `reporting/target.py` validates purpose, criteria, exact completed-trial
  membership, trial-local source references, and contiguous final-answer excerpts.
  Source consistency needs a final-answer excerpt and readable recorded sources
  matching every frozen `source_requirements` group for that check. Alternatives
  within a group are OR; groups are AND. Descriptor matching constrains provenance,
  not semantic truth. A trustworthy captured call can establish that a call was
  made even when its return was omitted; it cannot establish source agreement.
  Sensitive, duplicate, self-reported and overflow records do not supply determinate
  proof. Bad evidence rejects only its check: the definition and validator reason
  remain, with empty outcome and row-reference arrays. Accepted checks survive.
  Raw model output cannot author these rejection notes. Missing, duplicate or
  rewritten definitions still invalidate the whole target; `decisions.target_rejection`
  is reserved for that global failure. Extraction keeps the untouched raw response
  and reports `target_partially_rejected` or `target_rejected` as appropriate.
  With a scenario record, the complete frozen check set is mandatory. The report
  loader binds it to configuration, not model output; a conflicting persisted
  record or purpose invalidates the assessment without dropping observations.
  `reporting/summary.py` derives scoped findings from validated checks and native
  trial health. It distinguishes unmet requirements, no added benefit, preservation,
  incomplete baselines and inconclusive outcomes. Incomplete records remain in
  coverage denominators; rendering does not fill gaps from private audits.
  `reporting/trial_summary.py` validates bounded plain-text trial summaries
  against exact positional record identities; duplicates and invalid entries
  are omitted without losing raw evidence. `reporting/explanation.py` validates
  the immutable middle-layer explanation: headline, overview, annotated
  Before/After steps with practical meaning, unchanged claims, limits, and
  optional exact final-answer excerpts. Step and claim citations are nonempty,
  unique decision-row references, remapped when extraction sorts or drops rows.
  Unchanged claims cannot cite diverging rows. Excerpts must be contiguous,
  bounded text from the exact named trial on the declared side; formulas and
  code retain their source formatting. Invalid optional extraction is omitted
  without discarding valid comparisons. Canonical report-data parsing rejects
  invalid persisted explanation data. Extraction and loading share
  `read_trial_trace` so they read the same source fields.
  `reporting/attention.py` validates unique row references, exact branches,
  evidence kinds, and independent relationship/evidence-status fields. A changed
  distribution can support an observed or hypothetical consequence. An unchanged
  row reaches attention only when linked to a target criterion with an observed
  unmet outcome on both sides, labeled as a pre-existing target problem.
  Counts come from canonical rows. Malformed bundles become unavailable, never
  an assessed-empty result. No finding quota applies.
  These modules build schema-v19 `ReportData`, including nullable
  `metadata.source` and `metadata.ci_context`. Older versions are
  rejected; regenerate reports from their saved run evidence with `render.py`.
  Saved decisions without optional context, flow starts, or a purpose summary
  still render, without inventing those explanations.
  Purpose, scenario records, bounded evidence, limits, and assessments persist
  with decisions and report data; rendering does not reread current source files
  or infer new claims.
  Decision branches also retain validated trial memberships: exact coverage of
  completed trials on each side, matching counts, and no duplicate or foreign
  identities. Legacy aggregate-only branches show unavailable attribution;
  counts never imply trial identities. Incomplete trials remain in Trial evidence
  but do not enter the extractor's completed-trial branch assignments.

Command flow comes from recorded events. Decision comparisons come from model
interpretation of those events and answers. The report keeps these sources
distinct. Links between decisions and edits do not prove causality.

### Recorded evidence bounds

`reporting/evidence.py` selects only recorded read/search/list returns and
conservatively recognized read-only shell commands. Stable IDs use the trial
name and recorded tool-call ordinal. Source descriptors retain supplied ranges;
excerpt ranges are character offsets in returned text, **not file line numbers**.
Text blocks are joined with newlines; images are not sent as text evidence.

Codex keeps the raw shell wrapper alongside its command-flow display text.
The collector structurally decodes recognized shell command arguments without
execution; wrapped simple reads remain eligible, while compound commands,
redirections, substitutions, and non-read commands remain excluded.
Recorded `gh pr view`, `gh pr diff` and unambiguous `gh api` GET returns are
eligible through supported shell/execution adapters, including namespaced `exec`
tools. API request-body flags, mutating methods, compound commands, errors and
sensitive content remain excluded. This selects already-recorded text; it never
invokes `gh` or fetches a source.

Limits are 4,096 Unicode characters per excerpt, 16,384 per trial, 131,072 per
run, and 128 tool records per trial. Selection uses the saved `grades.tsv`
inventory (directory fallback only without that inventory) and reserves a share
of the remaining run budget for every remaining trial in lexical order. Within
each trial, readable returns matching frozen source requirements share the budget
first; incidental reads share the remainder. Within each group, unused space from
short returns is redistributed, with recorded order breaking one-character ties.
Without frozen requirements, all readable returns share the budget as before.
Each excerpt takes leading characters. Required-source priority prevents incidental
guide reads from shrinking a small required source, but it does not remove bounds:
required sources can still be truncated when they exceed the budget.
Overflow, missing returns, tool errors, non-text omissions, and truncation remain
explicit. Missing assessment content does not prove the agent never received it.
Questions about what a draft says use output evidence; checking those claims
against implementation is a separate source-consistency criterion. An observable
output result neither proves accuracy nor becomes unknown when sources are missing.

Known sensitive paths and recognized quoted or unquoted credential assignments,
including JSON keys, omit the entire return; email patterns also exclude returns.
The path exclusion also recognizes Git revision/path delimiters, so reading a
sensitive file through `git show REV:path` does not bypass that boundary.
These filters are not a guarantee against arbitrary private prose. No automatic source
retrieval is authorized. Deterministic checks enforce shape and references, not
semantic truth, causal attribution, or live extractor adherence.

## 5. The presentation layer returns evidence to the user

`render.py` passes the same `ReportData` to `reporting/render_markdown.py` and
`reporting/render_html.py`. It writes four artifacts:

| Artifact | Purpose |
| --- | --- |
| `report.html` | Local browser report with Summary, Understand the change, Behavior diff, Flow diff, Instruction changes, and Trial evidence tabs. |
| `report.md` | Markdown version for reading and sharing after review. |
| `report-data.json` | Structured, versioned report data. |
| `report-artifact.html` | Embeddable HTML body. |

The default Summary has four numbered sections in one reading column:
observed Before/After; scope and attention; what the tests establish; and
expandable test context and interpretation. Compact cards retain every branch
and count, without decorative illustrations. The recorded aim follows the cards.
A separate validated-result badge precedes the existing comparison heading;
an unmet requirement retains canonical finding precedence. Neither a changed
comparison nor a missing assessment is a pass of the instruction's goals.
Material cautions, report-wide qualifications, incomplete evidence, and attention
findings stay visible. The canonical finding, grouped check states, and every
unmet check's full title precede one disclosure containing the full check table,
rejection diagnostics, and unresolved or uncovered requirements. Next-action
guidance remains visible. Setup, full task, model interpretation, and comparison
starts expand separately. HTML and Markdown use the same hierarchy and evidence
destinations; the other five tabs retain their content and navigation roles.

The blind human-evaluation exporter validates this four-section DOM and projects
only observations, primary-result context, comparison starts, interpretation,
cautions, and attention evidence. Aim, assessment, setup, and next-action
guidance remain excluded. Unknown layouts fail closed rather than using a
legacy-layout fallback; saved already-built quiz artifacts remain unchanged.

The assessment conclusion is derived from validated target checks, not narrative prose.
An unmet After requirement remains unmet when Before made the same mistake.
All-met checks distinguish an already-correct baseline from an observed improvement;
an interrupted or uncertain Before cannot prove improvement. Preservation and
answer-only scope remain explicit. Unknown requirements never become passes,
and no report automatically approves or blocks a change.

Structured `summary.state`, `meaning`, `checks` and `next_action` carry the same
conclusion used by HTML and Markdown. Each check retains complete outcome
distributions, interpretation and evidence scope. **Understand the change**
repeats that conclusion and labels the original model explanation separately.
Criterion links open its source excerpts and per-trial evidence.

Frozen purpose remains distinct from observed success. A valid `purpose_summary`
is a labeled paraphrase; full goals and provenance remain in **Instruction changes**.
The method section uses the saved task, model, trial inventory and evidence limits.
When a reviewed scenario record exists, it also shows the setup summary, why the
data challenges the aim, planned conditions and limitations. Private preparation
notes are not report inputs. Missing records stay explicitly unrecorded rather
than being reconstructed from outcomes. Frozen checks remain visible as not
assessed when assessment is missing or rejected; setup is never proof of success.
Rejected checks keep their canonical positions, reasons and **Not assessed**
distributions. They cannot support attention findings or claims about evidence
that was inspected. Accepted After misses remain primary despite unrelated
rejections; accepted positives plus rejected checks stay inconclusive.

The evidence section retains Before/After branches, their counts, primary-result
context, attention findings, and optional model why/context/caution claims.
`reporting/illustrations.py` supplies fixed SVG shapes; model output never supplies
markup. Context must describe evidence, not invent a source conflict. Starts
require complete trial membership; a recorded action before a final answer does
not establish other causal ordering. Missing source evidence does not erase
supported observations, but observations alone do not prove a requirement was met.
The presentation retains the complete observation subtree rather than replacing
it with an abstract: Before/After cards, counts, primary outcome, model explanation,
cautions and attention findings. A separate qualification warns that retained
model interpretations do not override missing, rejected or partial assessments.
Deterministic check groups make supported results and unresolved coverage visible
together; no new model call or authored case-specific finding is used to render.

The blind human-evaluation projection retains only this observation section and
evidence limits. It excludes the assessment-derived headline, expected criteria,
method and next actions because they can reveal the keyed edit. Its neutral
heading is not a replacement finding. Source prose and claims remain unchanged.
In HTML explanatory prose, `reporting/version_names.py` emphasizes clear **Before**
and **After** version references without changing their text or surrounding font
size. It leaves ordinary temporal openings and ambiguous references plain.
Quoted/code spans, identifiers, URLs, recorded outputs, and frozen instruction
text stay untouched. This is deterministic presentation, not a model judgment;
Markdown and stored report data remain unchanged. Blinded HTML exports retain
the safe emphasis while preserving their existing evidence and privacy boundaries.
The method section keeps one-scenario/noncausal notices visible; evidence retains
the model caution. Uncertain or unassessable checks remain explicit in the
assessment table even without authored caution. Later revisions are mentioned
only when supplied evidence supports their context. HTML and Markdown retain
unmet requirements even for an unchanged target. Missing assessments remain
unavailable; native interruptions cannot be promoted to improvements.
These checks preserve structure and provenance, not interpretation correctness.
Understand the change starts with the shared conclusion and labeled interpretation.
For source-checking edits, extraction explains the input claim, source facts and actual
Before/After deliverables without inventing a conflict. Source reads, self-review
claims, and output consistent with a source remain distinct observations.
Criterion reasoning, exact excerpts, source availability, and trial consistency
are available in closed disclosures in both formats.
First-use meanings for roles, objects, acronyms, and tables come only
from supplied evidence, not guessed expansions, authority, or unread contents.
Narrative preserves overlap and separates source mandates from observed
responses: an added-instruction disclosure mandate is not an approval mandate,
and a model-added approval request is not new when Before already requests it.
An instruction's gate is distinct from an observed gate, which may already appear
in Before. These are extraction policies, not deterministic semantic guarantees;
the existing validator checks references, choice coverage, and evidence anchors.
Explanation validation additionally checks bounded narrative, row citations,
unchanged-row status, and exact example excerpts; it does not prove semantic
interpretation truth. Legacy comparison ranking is only a fallback when no validated
narrative selects an observed behavior.
When the selected lead differs from the canonical primary result, primary status
and full distributions remain beside the cards even with a target assessment.
Changed explanations, citations, or presentation must not be described as changed
actions. When a fallback comparison lead is not the primary task result,
`content.primary_result_context` exposes the primary status and full
distribution beside those cards in both formats. Missing or incomplete evidence
cannot become an unchanged-result claim. The primary-result block remains
derived presentation, not a separate serialized report field.
The primary-result block is context, not a second navigation choice.
**Understand the change**, linked from the Summary's context section, opens the
top-level explanation tab. This middle layer explains the specific distinction,
its practical implications, important unchanged behavior, consistency and
minorities, and concrete limits, with links to decision rows and named trials.
Annotated Before/After steps support workflow timing, formulas/code, keep/delete,
wording, and unchanged choices without assuming every change is a workflow.
Timing is shown only when established by the evidence. Examples are selected
exact excerpts, not raw transcript dumps. Both formats retain the same
explanation and source links; only HTML adds the visual walkthrough.
Behavior diff, Flow diff, Instruction changes, and Trial evidence remain
separate top-level tabs. Unavailable explanations link to retained evidence
instead of inferring a no-difference claim or making a new model call.
The general change explanation retains its completeness guard; incomplete
records do not erase supported target assessments of other completed trials.
Target coverage names unassessed records separately from observed failures.
Plans are not presented as executions. The second Summary section gives concise
consequences, actions, and essential evidence limits with one section-level detail link.
Findings linked to unmet After criteria come first. If no finding covers an
unmet criterion, a deterministic item retains its outcome distribution and
acceptance question without inventing a cause or explanation. Other findings
follow in saved order. Assessed-empty and unavailable assessments remain distinct;
neither suppresses an observed target failure.
Attention action labels retain trace provenance: self-reported actions are
explicitly not independently captured command evidence. HTML, Markdown, and
blind Summary exports preserve this qualification.
The section link opens supporting attention details inside Understand
the change, preserving the original explanation steps. Details hold the full
branch pictures, applicability, reasoning, counts, named trials, cited context,
and uncertainty. Raw comparisons stay inside closed **Check the evidence**
disclosures. The extractor explains what the reviewer gains while distinguishing
more informative review notes from more accurate deliverables. It never claims
that a source check or a changed explanation proves the intended fix worked.
HTML dismissal changes only DOM state: **Not relevant here** is reversible with
**Show again**, resets on reload, and does not hide content in print.
Markdown retains the same findings, branch labels, counts, and explanation
without SVG illustrations or interactive dismissal.
Saved decisions without interpretations show explicit availability notices;
rendering never requests new explanations.

The scenario disclosure explains the simulated situation, instruction versions,
trial setup, and supplied expectation (or its absence). A nested disclosure
holds the full original scenario prompt, closed by default.
The loader stores `content.task` separately from the scenario description,
preferring the run's `task.md` over a capsule copy. Missing task text remains
unavailable rather than treating a description as the prompt. Shared
`content.scenario_sections` supplies both HTML and Markdown; rendering adds
no inferred setup details.

Instruction changes has its own tab, linked from the Summary's goal. It begins
with the complete recorded goals and their provenance when available, otherwise
the saved `intent`, labeled as a likely aim or supplied expectation.
Rendering does not infer missing explanations or claim confirmed author intent.
Both output formats retain one complete diff. `content.instruction_edit_counts`
counts changed lines across validated hunks; `content.instruction_hunk_label`
names blocks by section and line range. Selecting a block highlights only its
changed lines and scrolls to its stable anchor. Missing or unparseable diffs
do not acquire invented counts.

All six tabs remain available. Missing extraction and uncaptured command flow
have explicit unavailable states, with links to the retained trial evidence.
Flow groups only identical complete command sequences within each side.
Trial evidence aligns the saved Before/After lists by position into numbered
groups, not paired executions. Missing sides are explicit. A short saved
takeaway, Before/After descriptions, and optional caveat precede each group's
full answers. Missing summaries stay unavailable; rendering does not infer them
from aggregate decisions. Final answers remain visible; shared disclosures
expand supporting details and commands on both
sides. Group and individual-record anchors remain available. Per-comparison
trial links expose the available groups without inventing individual attribution.
Printing opens every disclosure and restores screen state afterward.

The runner attempts to open the HTML report. The skill summarizes observed
differences and evidence limits in the conversation. Missing extraction does
not prevent a report of commands and answers. Saved evidence can be rendered
again without new trials or model calls.

### How the HTML report is generated

The runner calls the renderer after decision extraction:

```bash
python3 "$scripts/render.py" "$run" "$run" "$model" "$run/config.json"
```

Here, `$scripts` is the bundled scripts directory and `$run` is the saved run.
The second directory argument supplies scenario assets, such as a fallback
`rule.md`. The standard runner uses the run directory for both arguments.

All output formats share `ReportData`. Only the HTML branch uses
`report.css` and the document wrapper:

```text
+-----------------------------------------------------+
| Saved run: configuration, grades, traces, snapshots |
| decisions.json: comparisons, explanation, attention |
+--------------------------+--------------------------+
                           |
                           v
           load_report() + evidence validation
                           |
                           v
                    +------------+
                    | ReportData |
                    +------+-----+
                           |
                           +--> to_json() -> report-data.json
                           |
                           +--> render_markdown() -> report.md
                           |
                           +--> render_artifact(report, css)
                                      |
                                      +--> report-artifact.html
                                      |
                                      +--> render_document()
                                                 |
                                                 v
                                             report.html
```

1. **Load evidence.** `load_report()` reads `config.json`, `grades.tsv`, each
   trial's `trace.jsonl`, and optional `decisions.json`. It groups trials by
   Before/After and extracts actions and final answers.
2. **Recover the instruction diff.** `reporting/instruction.py` reads the
   target file from `before-1/project/` and `after-1/project/`.
   Python's `difflib.unified_diff` produces the added and removed lines.
   The report therefore uses saved trial files, not the current source project.
3. **Build one report object.** The loader computes command comparisons and
   assembles metadata, results, decisions, instruction diff, and trial evidence
   into `ReportData`. Its schema checks the structure before rendering.
4. **Build the HTML body.** `render_artifact(report, css)` creates HTML from
   that object and inlines `reporting/report.css`. Python functions build the
   Summary, instruction changes, behavior comparisons, command flow, and shared
   trial evidence sections. Unavailable evidence does not remove a tab.
   Evidence text is HTML-escaped, so recorded code and answers remain text.
5. **Create the page.** `render_document(artifact)` adds the HTML document
   wrapper, character encoding, and viewport metadata. `render.py` writes the
   body to `report-artifact.html` and the full document to `report.html`.
   It also serializes `ReportData` to JSON and renders Markdown separately.

HTML is not converted from Markdown, and a model does not write the page.
The page includes JavaScript for evidence links, expand/collapse controls, and
printing. It opens as a local file without an application server. Styles are
inline, but the page also references Google Fonts.

## Manual human evaluation

The repository-local
[`run-behavior-diff-human-evaluation`](../.agents/skills/run-behavior-diff-human-evaluation/SKILL.md)
skill is a maintainer workflow, not part of the installable plugin or edit hooks.
It uses the existing trial/extraction/rendering pipeline without changing summary
wording:

```text
Manual request + fresh live-cost approval
  -> fixed recce-team upstream + pinned main + fresh random sample
  -> five synthetic fixtures and patch-grounded four-option questions
  -> frozen inputs/key + current local implementation fingerprint
  -> unchanged local runner: 3 Before + 3 After per case
  -> saved report HTML -> blinded Summary excerpts
  -> loopback quiz -> first human submission -> score and full-report reveal
     OR saved-evidence v1 export -> synthetic local site emulators
        -> private multi-response export -> frozen-key scores + validity assessment
```

`evaluate.py` owns sampling, source/fixture validation, input freezing, guarded
live execution, and provenance. `quiz.py` projects the original saved HTML without
model calls and owns the local quiz server and scoring. `hosted.py` owns the
allowlisted v1 package and private multi-response analysis, dispatched through
`evaluate.py export-package` / `hosted-results`. It verifies saved evidence,
copies exact blinded HTML, and retains provenance in a private session receipt;
packages and response exports stay outside both working trees. The contract and
commands live in the skill's [workflow reference](../.agents/skills/run-behavior-diff-human-evaluation/references/workflow.md#hosted-package-v1).
Prepared historical cases also include reviewed `purpose.json` from commit or
diff context, hashed with the frozen inputs. Existing evaluation sessions without
that required file fail preparation/frozen-input validation rather than acquiring
post-result purpose. Their previously saved reports remain readable under the
report-format policy above.
The separate site repository owns Firebase runtime/admin tooling; this repository
has no deployment credentials or live Firebase path. Agent instructions own
scenario design, question truth, and interpretation; structural validation is
not a semantic judgment of the options.

Each new session samples five eligible single-existing-skill-file changes from
`DataRecce/recce-team`, never a handpicked commit list or another repository.
The helper records the source tip, seed, exclusions, HEAD, and source-content
fingerprint, including uncommitted implementation changes. Questions freeze
before trials; attempts cannot be silently retried or replaced after results.
The Claude-only read-only launcher disables external tools and suppresses the
runner's automatic report opening so the quiz stays blind.

The server binds only to loopback and serves an explicit public allowlist.
Instruction intent/diff, the full scenario, and source metadata stay private
before submission. The answer key is server-side; the first complete submission
unlocks original reports and commit links. Saved sessions remain available for
analysis after the checkout changes. A score out of five measures this reader's
answers to these questions, not product-wide accuracy or execution correctness.

Hosted packages intentionally expose only the minimal frontend answer mapping;
this is inspectable trust-based scoring, unlike the server-side key in local mode.
The analyzer checks the immutable manifest/hash and private session mapping,
recomputes each score from the original frozen key, and retains every original
UID record and site build. Duplicate names are advisory and never merged.
All-case semantic validity remains a separate saved-evidence assessment, not an
automatically revised score or denominator. Current implementation approval covers
synthetic local emulators only. An explicit publication-policy update and review
of actual outgoing content remain required before uploading any private session;
blinding and private repository visibility are not publication permission.

## Local verification handoff prototype

The repository-local [maintainer skill](../.agents/skills/verification-handoff-prototype/SKILL.md)
owns the verification handoff, separate from the installed plugin:

```text
Selected change + project context
  -> host proposes goals -> owner confirms/corrects material scope
  -> instruction and saved-evidence review
  -> Behavior Diff preparation + compatibility/isolation preflight
  -> bounded live-run approval if missing -> execute + audit evidence
  -> decision-ready recommendation -> owner adoption decision (no automatic merge)
```

The host owns planning, preparation, bounded recovery and interpretation, without
requiring owner reminders between stages. It delegates comparison mechanics to
Behavior Diff's existing contracts, not a second runner. It checks fixture fit,
scenario reach and environment confounds before launch; unsupported capabilities
remain blockers rather than silently reduced scope. Paid runs and private-data
handoffs need explicit bounded authority. Global configuration is not a write target.
Evaluation responses never authorize PR operations.

Explicit replay-only requests use saved evidence without new trials. Optional
`replay.py` owns private snapshots, correction invalidation, confirmed revisions
and read-only root-scoped citations for that subset. Its fixed-evidence mode is
not a fresh-run status. Unchanged support survives correction; missing/changed
citations become gaps. Private packets stay outside Git trees; synthetic fixtures
exercise helper mechanics only. No helper schema or production runner changed.
Owner effort reduction requires an actual walkthrough, not deterministic checks;
feedback is optional after delivery. Historical experimental purpose stays frozen.

## Local state and system boundaries

State lives under `${BEHAVIOR_DIFF_HOME:-~/.behavior-diff}/`:

- `baselines/`: Before content for instruction files without a Git baseline.
- `nudge/`: session state that prevents repeated hook suggestions.
- `runs/`: each comparison's task, configuration, project copies, traces,
  completion grades, extracted decisions, and generated reports.
- `human-evaluations/`: private source snapshots, frozen scenarios/questions,
  original reports, quiz projections, and human submissions for manual evaluations.

A shared-data run uses its own stage instead: `project/` (the scratch base),
`before` (a present Before version), `home/` (its `BEHAVIOR_DIFF_HOME`, with
any `ABSENT` marker and its runs), and `freeze.json`. The stage stays after the
run because it holds the reports.

The runner prepares copies without changing the source project. Separate
working directories are not a universal security sandbox. Tool restrictions
depend on the host, and permitted shell commands can have side effects.

Reports stay local, but trial and extraction inputs go to the selected model
provider. Reports can contain private code and answers. CI uses deterministic
checks and synthetic evidence, never live model runs.
