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
| Skill orchestration                                     |
| Select edit, scenario/model; freeze purpose/provenance   |
+----------------------------+----------------------------+
                             v
+---------------------------------------------------------+
| Trial execution                                         |
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
| decisions.py: purpose + bounded returns + trial answers |
| Same extraction: target criteria, outcomes, narrative   |
| reporting/: validate evidence links; assemble reports   |
+----------------------------+----------------------------+
                             v
+---------------------------------------------------------+
| Presentation                                            |
| render.py -> HTML, Markdown, and structured JSON        |
| Skill explains evidence; user reviews the change        |
+---------------------------------------------------------+
```

Trial execution and decision extraction call models through agent CLIs.
Report assembly and rendering run locally without model calls.

Purpose travels in run configuration directly to analysis, never in the trial
task or project copies. Recorded tool returns travel from trials to analysis;
the collector does not retrieve current source files.

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
select the changed file and prepare a scenario at the relevant decision point.
The task must not reveal the expected behavior. The instruction change must
remain the only source of that guidance.

The skill selects the trial host and model, calls the runner, and explains the
result. It owns scenario quality and interpretation, not filesystem copying or
report formatting.

Before execution, the skill records distinct concise goals and their provenance
(`session`, `commit`, or `diff`; `explicit` or `inferred`) in a reviewed purpose
file. It uses available conversation context, not transcript-store searches.
Historical comparisons use the relevant commit history; absent motivation falls
back to a labeled diff inference. Raw conversation and unrelated private details
are excluded. Purpose is the question, not evidence of success. The user-facing
consent covers bounded source returns reaching assessment; filtering cannot
certify arbitrary prose as free of private information.

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

The trace contains paired tool actions and recorded returns plus a final answer.
Claude's stream is retained; Codex command output and Pi/OMP tool results keep
their call identities during normalization. Raw host logs and stderr remain
available where captured. After trials finish, `grades.tsv` records `REVIEW`
for a final answer, otherwise `BLOCKED`: completeness, not correctness.

Trial and extraction models have separate roles. Claude defaults to Opus for
trials and Sonnet for extraction. Codex uses Sol and Luna, respectively.
`codex_model.py` resolves Codex selectors to concrete IDs. Both trial variants
use the same resolved ID. [Model selection](../README.md#trial-and-extraction-models)
describes overrides and Pi/OMP behavior.

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
The configuration records the target path, scenario, Before/After labels, and
validated `purpose`. `--purpose-file` is frozen before trials and excluded from
trial copies, including when supplied from within the source project.
Uncommitted setup files do not enter Git-based trials. Required task state must
already exist in the base project or in a deliberately prepared fixture.

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
  recorded returns. The same extraction call defines observable target criteria,
  required evidence, and per-trial outcomes (`met`, `not_met`, `uncertain`, or
  `unassessable`), alongside choices, primary task result, narrative, and attention.
  Criteria cover every purpose goal and use the same question on both sides.
  Correction, new/changed behavior, and preservation are supported separately.
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
  Questions name the actual action or claim and its relevant condition or limit;
  conclusions state what each side did and what cannot be confirmed. This pass
  is required with or without Humanizer, within the existing extraction call.
  It preserves criterion scope and polarity, canonical label matches, evidence
  qualifiers, and exact excerpts; it does not rewrite rendered artifacts.
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
  A determinate source-consistency judgment requires both a readable recorded
  return and an output excerpt; unavailable or omitted content cannot supply proof.
  `reporting/summary.py` leads with valid target assessments, including unchanged
  or mixed outcomes, instead of ranking incidental changes ahead of the target.
  Without a valid target assessment, it explicitly says assessment is unavailable
  and retains underlying comparisons. Task completion remains separate.
  Incomplete records stay visible in the coverage denominator.
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
  These modules build schema-v12 `ReportData`; saved schema-v11 reports migrate
  explicitly with unavailable target assessment and readable legacy observations.
  Older decisions lacking the new attention fields show unavailable attention.
  Purpose, bounded evidence, limits, and assessments persist with decisions and
  report data; rendering does not reread current source files or infer new claims.
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

Limits are 4,096 Unicode characters per excerpt, 16,384 per trial, 131,072 per
run, and 128 tool records per trial. Selection uses the saved `grades.tsv`
inventory (directory fallback only without that inventory) and reserves a share
of the remaining run budget for every remaining trial in lexical order. Within
each trial, readable returns share the character budget, redistributing unused
space from short returns; recorded order breaks one-character remainder ties.
Each excerpt still takes leading characters. Earlier guide reads cannot exhaust
the budget before every later source return. This is fair coverage, not a
relevance ranking: needed facts can still fall outside retained prefixes.
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

The default Summary tells a four-part numbered story: the edit's aim, the
scenario's observations, what needs attention, and what this means.
The goal is one sentence with a compact
source label and edit link; an info popup holds the source caveat. Supplied
expectations and inferred aims remain distinct; neither becomes proof of
author intent or goal completion. Markdown retains the caveat as plain text.
`reporting/illustrations.py` supplies fixed SVG shapes for the Before/After
comparison. Model output supplies text and selectors, never markup.
The edit illustration uses an original solid open-end wrench with a compact head
and slim handle, not third-party artwork. Check its silhouette in both card
palettes when changing its geometry.
The Summary headline describes supported observed behavior. A target-assessment
status never replaces it; missing source evidence must not hide observations
that final answers or recorded actions support. Without a usable narrative,
the heading introduces the Before/After comparison without inventing a finding.
One illustrated Before/After pair shows observed behavior, with the appropriate
answer, plan, captured-action, or self-reported-action provenance. Extraction
prefers observations relevant to the purpose, including an already-correct baseline,
over incidental differences. Separate, unlinked assessment rows retain every
question and its complete outcome distribution. Changed Yes/No proportions are
bold; mixed results retain all counts, and unknown results are not treated as No.
The rows label `unassessable` outcomes “Not enough evidence”, scoped to their
question rather than promoted to the headline. Excluded recorded evidence is not
the same as evidence never captured. The report does not automatically approve edits.
The existing narrative `why` field supplies a short conclusion in “What this means”.
When purpose is available, extraction connects the observed outcome to that purpose:
an already-correct baseline, a remaining problem, preservation, or a mixed result.
It also names when the scenario did not exercise the intended problem or source
content is insufficient. Additional wording or source reads alone cannot establish
that the intended fix worked. The conclusion allows up to 480 characters, with
supporting comparison references; the separate caution remains capped at 240.
HTML and Markdown retain this conclusion even for an unchanged target. An absent
conclusion is explicitly unavailable; incomplete trial evidence suppresses it.
These checks preserve structure and provenance, not interpretation correctness.
Understand the change starts with readable explanations. For source-checking edits,
extraction explains the input claim, relevant recorded source facts, and actual
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
When target assessment is available, task-completion context stays in the detailed
comparisons rather than adding another Summary block; mixed primary results still
appear in the Summary's evidence-limit notices.
Changed explanations, citations, or presentation must not be described as changed
actions. When a fallback comparison lead is not the primary task result,
`content.primary_result_context` exposes the primary status and full
distribution beside those cards in both formats. Missing or incomplete evidence
cannot become an unchanged-result claim. The primary-result block remains
derived presentation, not a separate serialized report field.
The primary-result block is context, not a second navigation choice.
**Understand the change**, under the Summary's evidence section, opens a new
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
Plans are not presented as executions. The third Summary section shows relevant
tradeoffs with Before/After pictures, every branch count, a consequence,
applicability, an action, and explicit evidence limits. Expected tradeoffs can
qualify; differences alone do not. There is no separate Other findings category
or fixed finding cap. Assessed-empty and unavailable states use different wording.
Attention action labels retain trace provenance: self-reported actions are
explicitly not independently captured command evidence. HTML, Markdown, and
blind Summary exports preserve this qualification.
One **See why this matters** link opens an additive attention section inside
Understand the change, preserving the original explanation steps. Unlike the
Summary cards, this section separates model reasoning, every branch's count and
named supporting trials, cited context, and uncertainty. It does not repeat the
pictures, consequence, or action guidance. Optional **Check the evidence**
disclosures contain raw comparison links. The existing extraction prompt asks
for supported reasoning beyond the Summary, not invented detail or paraphrase.
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
with the saved `intent`, labeled as a likely aim or supplied expectation.
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

## Local state and system boundaries

State lives under `${BEHAVIOR_DIFF_HOME:-~/.behavior-diff}/`:

- `baselines/`: Before content for instruction files without a Git baseline.
- `nudge/`: session state that prevents repeated hook suggestions.
- `runs/`: each comparison's task, configuration, project copies, traces,
  completion grades, extracted decisions, and generated reports.
- `human-evaluations/`: private source snapshots, frozen scenarios/questions,
  original reports, quiz projections, and human submissions for manual evaluations.

The runner prepares copies without changing the source project. Separate
working directories are not a universal security sandbox. Tool restrictions
depend on the host, and permitted shell commands can have side effects.

Reports stay local, but trial and extraction inputs go to the selected model
provider. Reports can contain private code and answers. CI uses deterministic
checks and synthetic evidence, never live model runs.
