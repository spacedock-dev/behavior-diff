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
| Select instruction change, scenario, agent, and model   |
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
| Snapshots, traces, answers, and completion grades       |
+----------------------------+----------------------------+
                             v
+---------------------------------------------------------+
| Evidence analysis                                       |
| decisions.py: trial assignments -> counts and summaries |
| reporting/: deterministic comparison and report data    |
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

## 3. The execution layer produces comparable trials

[`behavior-diff.sh`](../plugin/skills/behavior-diff/scripts/behavior-diff.sh)
coordinates one comparison. It resolves the Before version from an explicit
file, Git HEAD, or a hook baseline. It creates one project copy per trial and
installs the appropriate instruction version.

For Git projects, copies start from `git archive HEAD`. Only the selected
instruction change enters the After copies. Other uncommitted edits stay out.
Without a usable Git HEAD, the runner copies the folder instead.

[`run-trial.sh`](../plugin/skills/behavior-diff/scripts/run-trial.sh) runs one
fresh agent process inside one copy. The default comparison runs three trials
per side concurrently, with the same task and model. The adapter supports
Claude, Codex, Pi, and OMP. It suppresses recursive plugin hooks and converts
host events into a common `trace.jsonl` format.

The trace contains tool actions and a final answer. Raw host logs and stderr
remain available where captured. After all trials finish, the coordinator
writes `grades.tsv`: `REVIEW` for a trace with a final answer, otherwise
`BLOCKED`. This checks completeness, not correctness.

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
The configuration records the target path, scenario, and Before/After labels.
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
  final answers, and numbered instruction-diff hunks. A separate model extracts
  choices with named trial assignments, a primary result, supported implications,
  links to edits, plain-language Summary text, the edit's likely aim, and short
  per-group trial summaries in the same call. New raw branches supply `trials`,
  not aggregate counts. The script requires each completed trial exactly once
  per side of every row, derives `n`, and retains both in `decisions.json`.
  Foreign, duplicate, incomplete, or missing assignments invalidate the row.
  Count-only raw extraction is not accepted; saved normalized report evidence
  remains renderable. Membership validation cannot prove classification truth.
  Each trial summary names its exact Before/After records and separates answers
  and plans from recorded actions. The inferred aim cites instruction hunks
  independently of trial outcomes. The script validates references and exact
  choice coverage; invalid interpretation does not discard valid observations.
- **Deterministic assembly:** `reporting/load.py` reads saved evidence and
  compares recorded command sequences. `reporting/instruction.py` supplies the
  instruction diff. `reporting/content.py` derives shared wording and evidence
  limits. `reporting/summary.py` validates narrative and selects the visual lead.
  With complete evidence, a validated narrative may select any row with changed
  choice proportions, including mixed or non-primary rows, without changing the
  primary-result identity. Evidence ranking is a fallback, not a veto on these
  narratives; unchanged or matching-proportion rows still need to qualify under
  that ranking. Incomplete evidence suppresses narrative. Mixed-result and
  single-trial cautions remain visible.
  It also derives the story's aim from supplied expected behavior or a
  validated inference whose stored diff matches the current instruction diff.
  `reporting/trial_summary.py` validates bounded plain-text trial summaries
  against exact positional record identities; duplicates and invalid entries
  are omitted without losing raw evidence. Extraction and loading share
  `read_trial_trace` so they read the same source fields.
  Together these modules build schema-v8 `ReportData` in `reporting/schema.py`.
  Summary counts come from existing decision rows.

Command flow comes from recorded events. Decision comparisons come from model
interpretation of those events and answers. The report keeps these sources
distinct. Links between decisions and edits do not prove causality.

## 5. The presentation layer returns evidence to the user

`render.py` passes the same `ReportData` to `reporting/render_markdown.py` and
`reporting/render_html.py`. It writes four artifacts:

| Artifact | Purpose |
| --- | --- |
| `report.html` | Local browser report with Summary, Instruction changes, Behavior diff, Flow diff, and Trial evidence tabs. |
| `report.md` | Markdown version for reading and sharing after review. |
| `report-data.json` | Structured, versioned report data. |
| `report-artifact.html` | Embeddable HTML body. |

The default Summary tells a numbered story: the edit's aim, the scenario's
observations, and their meaning. The goal is one sentence with a compact
source label and edit link; an info popup holds the source caveat. Supplied
expectations and inferred aims remain distinct; neither becomes proof of
author intent or goal completion. Markdown retains the caveat as plain text.
`reporting/illustrations.py` supplies fixed SVG shapes for the Before/After
comparison. Model output supplies text and selectors, never markup.
The edit illustration embeds the ISC-licensed Lucide wrench at its original
24×24 proportions, scaled uniformly within the card. Its full copyright,
permission notice, and disclaimer live in the bundled source and travel with
the SVG as an HTML comment in exported reports; no icon package or runtime
fetch is needed. Check its silhouette in both card palettes when changing it.
Summary and trial-summary instructions require concrete, parallel descriptions
of the same subject, with the decisive contrast and any unchanged decision
explicitly stated. Summary selection prefers the observed changed operative rule
(conditions, timing, scope, or prerequisites) over its downstream outcome, including
mixed comparisons. Material intervals, deadlines, units, and gates belong in the
main cards, not only Other findings. Each card detail must hold for every named trial
in its selected branch; counts or citations from other rows cannot supply membership.
An instruction's gate is distinct from an observed gate, which may already appear
in Before. These are extraction policies, not deterministic semantic guarantees;
the existing validator checks references, choice coverage, and evidence anchors.
No schema field or keyword-based semantic check is added; fallback ranking is unchanged.
Changed explanations, citations, or presentation must not be described as changed
actions. When the selected lead is not the primary
result, `content.primary_result_context` exposes the primary status and full
distribution beside the cards in both formats. Missing or incomplete evidence
cannot become an unchanged-result claim. This is derived presentation, not a
new serialized report field; schema v8 is unchanged.
The primary-result block is context, not a second navigation choice. One
**View behavior comparisons** link opens Behavior diff for the selected
comparison and the primary result; unavailable evidence links to trial records.
Plans are not presented as executions. `content.additional_findings` selects
at most three compact comparisons; full comparisons stay in Behavior diff.
Markdown shares the same story and findings without illustrations.
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

All five tabs remain available. Missing extraction and uncaptured command flow
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
| Optional decisions.json                             |
+--------------------------+--------------------------+
                           |
                           v
                     load_report()
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
```

`evaluate.py` owns sampling, source/fixture validation, input freezing, guarded
live execution, and provenance. `quiz.py` projects the original saved HTML without
model calls and owns the local quiz server and scoring. Agent instructions own
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
