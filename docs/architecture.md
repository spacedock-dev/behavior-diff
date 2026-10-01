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
| decisions.py: model-based decision extraction           |
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
  choices, counts, a primary result, supported implications, links to edits, and
  optional plain-language Summary text in the same call. The script validates
  references and exact choice coverage before it writes `decisions.json`.
  Invalid Summary text is discarded without losing valid decision evidence.
- **Deterministic assembly:** `reporting/load.py` reads saved evidence and
  compares recorded command sequences. `reporting/instruction.py` supplies the
  instruction diff. `reporting/content.py` derives shared wording and evidence
  limits. `reporting/summary.py` validates narrative and selects the visual lead,
  retaining mixed-result, incomplete-evidence, and single-trial cautions.
  Together they build the format-neutral schema-v5 `ReportData` defined in
  `reporting/schema.py`. Summary counts come from existing decision rows.

Command flow comes from recorded events. Decision comparisons come from model
interpretation of those events and answers. The report keeps these sources
distinct. Links between decisions and edits do not prove causality.

## 5. The presentation layer returns evidence to the user

`render.py` passes the same `ReportData` to `reporting/render_markdown.py` and
`reporting/render_html.py`. It writes four artifacts:

| Artifact | Purpose |
| --- | --- |
| `report.html` | Local browser report with Summary, Decision diff, Flow diff, and Trial evidence views. |
| `report.md` | Markdown version for reading and sharing after review. |
| `report-data.json` | Structured, versioned report data. |
| `report-artifact.html` | Embeddable HTML body. |

The default Summary pairs a short takeaway with illustrated Before/After cards.
`reporting/illustrations.py` supplies fixed SVG shapes; model output supplies
text and icon selectors, never markup. Plans are not presented as executions.
Longer evidence lives in expandable details. Markdown uses the same summary
without illustrations. Saved decisions without narrative use original choices
and an explicit availability notice; rendering never requests new explanations.

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
   Summary, decision comparisons, command flow, and expandable trial evidence.
   Decision diff appears only with extracted decisions. Evidence text is
   HTML-escaped, so recorded code and answers appear as text rather than markup.
5. **Create the page.** `render_document(artifact)` adds the HTML document
   wrapper, character encoding, and viewport metadata. `render.py` writes the
   body to `report-artifact.html` and the full document to `report.html`.
   It also serializes `ReportData` to JSON and renders Markdown separately.

HTML is not converted from Markdown, and a model does not write the page.
The page includes JavaScript for evidence links, expand/collapse controls, and
printing. It opens as a local file without an application server. Styles are
inline, but the page also references Google Fonts.

## Local state and system boundaries

State lives under `${BEHAVIOR_DIFF_HOME:-~/.behavior-diff}/`:

- `baselines/`: Before content for instruction files without a Git baseline.
- `nudge/`: session state that prevents repeated hook suggestions.
- `runs/`: each comparison's task, configuration, project copies, traces,
  completion grades, extracted decisions, and generated reports.

The runner prepares copies without changing the source project. Separate
working directories are not a universal security sandbox. Tool restrictions
depend on the host, and permitted shell commands can have side effects.

Reports stay local, but trial and extraction inputs go to the selected model
provider. Reports can contain private code and answers. CI uses deterministic
checks and synthetic evidence, never live model runs.
