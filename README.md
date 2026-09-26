# Behavior Diff

**Test changes to your agent instructions before you trust them.**

Behavior Diff shows whether a change to `CLAUDE.md`, `AGENTS.md`, or a skill
changes what an agent does. It runs the same task with and without your change,
then gives you a before-and-after report.

A rule can sound clear and still change nothing. It can also fix one case but
cause a new problem somewhere else. Behavior Diff lets you review evidence
before you commit the rule.

## Why use Behavior Diff?

Agent instruction files shape decisions, tool use, and final answers. Text
review can show whether a rule sounds clear. It cannot show what the agent will
do.

Behavior Diff runs the change as a controlled experiment. You see whether the
rule changes the process or result before you share it.

## What you can compare

- Whether the agent reached the situation that the rule targets.
- Where the before and after runs took different paths.
- Which commands, tools, and evidence each run used.
- Whether the final answers changed.
- Whether the change was consistent across repeated runs.

Behavior Diff does not label a rule as good or bad. You compare the evidence
with the behavior that you want.

## When it helps

Use Behavior Diff when you:

- Add a rule after an agent made the wrong choice.
- Change a shared `CLAUDE.md` or `AGENTS.md` file.
- Edit a skill trigger or workflow instruction.
- Remove or simplify a rule and want to find regressions.
- Want evidence before your team adopts an instruction change.

## Install

Behavior Diff installs as a plugin on Claude Code and Codex. The commands below
install the public marketplace release.

Pi and OMP are trial stacks, not plugin hosts in this change. Run their
headless trials from a Behavior Diff source checkout and pass an exact model.

| Surface | Claude Code | Codex | Pi | OMP |
| --- | --- | --- | --- | --- |
| Marketplace plugin install | Yes | Yes | No | No |
| Headless trial stack | Yes | Yes | Yes, with `--model` | Yes, with `--model` |
| Live trial dispatch | Parallel subagents | Fresh sequential contexts or headless | No built-in dispatch. Use headless. | One parallel `task` batch |

### Claude Code

```bash
claude plugin marketplace add spacedock-dev/marketplace
claude plugin install behavior-diff@spacedock
```

Restart Claude Code after installation.

### Codex

```bash
codex plugin marketplace add spacedock-dev/marketplace
codex plugin add behavior-diff@spacedock
```

Enable hooks in `~/.codex/config.toml`:

```toml
[features]
hooks = true
```

Start one interactive Codex session after installation. Approve each Behavior
Diff hook when Codex asks. Codex does not ask for hook approval during
`codex exec`.

Codex uses a cached copy of each plugin. Run the install command again after a
Behavior Diff update:

```bash
codex plugin add behavior-diff@spacedock
```

## Use Behavior Diff

1. Edit one instruction file. Keep the change uncommitted.
2. Ask Claude Code or Codex to run Behavior Diff on the change.
3. Review the report before you commit the instruction.

For example:

```text
Run behavior diff on my AGENTS.md change.
```

In Claude Code, you can also run:

```text
/behavior-diff
```

Behavior Diff finds the changed instruction file and uses your request as the
comparison task. Once the task is known, it runs the comparison and opens the
report.

## Read the report

A **run** compares the instruction versions. A **trial** is one agent execution on
one side. Each run creates a local HTML report with up to four tabs:

- **Summary** opens first. It states the finding and task, then separates the
  final result from the agent's behavior. Each comparison has a change status,
  trial counts, and evidence links. Model explanations and evidence limits follow.
- **Decision diff** starts with a concise finding and one list of comparisons.
  Each step shows its topic, status, and role. Changed choices and the final result
  have short Before/After summaries. Mixed or partial choices retain their counts.
  Open a step to inspect its full question, choices, counts, sources, and trial links.
  Several steps can stay open. Direct links open the matching step, and
  **Expand all** shows all comparison evidence. Printing includes all evidence.
  Markdown keeps each comparison fully expanded. Comparison order does not
  represent recorded execution or proven causality.
- **Flow diff** starts with each side's recorded command progression. Identical
  recorded sequences share a path with counts and links to their trial evidence.
  A separate table compares command-category combinations. This tab appears only
  when the run captured tool calls.
- **Trial evidence** shows each trial's recorded commands or self-reported actions
  and its final answer. Before and After trials are independent, even when their
  numbers match. Side labels and trial counts remain visible on mobile.

Start with the headline. **Final result** is the primary result identified by the
model. **Final answer** is the agent's recorded answer text. **Behavior** compares
the actions found in the evidence. The same result can come from a different
process. Changes in answer wording alone do not establish an action change.

In Summary and Decision diff, counts such as **3 of 3 trials** refer to trials,
not repeated actions within one trial. A model extracts these counts from the
evidence. Separate row counts do not show a complete sequence within one trial.
**Changed** and **Unchanged** compare choice proportions. **Unavailable** means
that the extracted choices cannot support a comparison.

In Flow diff, progression preserves command order and repeated commands. Before
and After trials are independent. Empty records and blocked trials remain visible.
Recorded commands do not prove successful execution.

The command-category table groups each trial into one category combination.
Category order is not execution order. Matching categories can contain different
commands or files, so matching patterns do not establish unchanged behavior.

The Summary uses short labels. Follow each label to its full comparison in
Decision diff. Inspect the trial records for the original commands and answers.
The Markdown report contains the same comparisons and evidence links.

The existing extraction call identifies the primary result and possible
explanations. These explanations are model interpretations, not causal proof.
A changed result is not an automatic success or failure.
Before and After use neutral borders. PASS and FAIL colors indicate grades
against the supplied expectation, not a judgment that After is better.
Instruction diff colors still mark added and removed lines.

Mixed results show the choices and their trial counts. Missing, blocked, or
incomplete evidence produces an insufficient-evidence result. Without an
identified primary result, the report labels its comparisons as reported answers.
It does not guess the final result.

Expected behavior appears only when supplied. The evidence limits state the
trial counts, provenance, and grading limits. Self-reported actions remain
distinct from captured tool calls.

The structured `report-data.json` uses schema version 3. Regenerate reports
from their run artifacts to use this format. Older report-data files are not accepted.

If both sides follow the same path, the task can miss the situation that the
rule targets. Use a task that starts closer to the decision that you want to
change.

## What stays local

Behavior Diff runs each side in a separate copy of the project. The after side
contains only the instruction change that you selected. Other uncommitted files
do not enter the experiment.

Reports stay on your machine under:

```text
${BEHAVIOR_DIFF_HOME:-~/.behavior-diff}/runs/
```

A report can quote code and agent output from your project. Review the report
before you share it.

## How Behavior Diff works

Behavior Diff creates two copies of the same project state:

1. The **before** copy uses the committed instruction file.
2. The **after** copy adds only your uncommitted instruction change.

It gives both copies the same task and starts fresh agent sessions.

The runner records tool calls, commands, evidence, decisions, and final answers.
It converts those traces into a common flow format, compares the two sides, and
builds the HTML report. It does not use a model to declare a winner.

The plugin also watches edits to `CLAUDE.md`, `AGENTS.md`, and `SKILL.md`.
After you finish the current task, the agent can use that task to run Behavior
Diff on the instruction change.

## Preview synthetic reports

From a repository checkout, use Python 3.10 or newer to build a local gallery:

```bash
python3 tests/report-demo.py --serve --port 8767
```

Open the printed URL. The server listens only on `127.0.0.1`. Press `Ctrl+C`
to stop it and remove its temporary files. If the port is busy, use `--port 0`
to select an available port.

To build reports without a server:

```bash
python3 tests/report-demo.py
```

This command prints a local file URL and keeps the temporary directory.
Remove that directory when you no longer need the reports.

The eleven examples cover changed and unchanged results, action changes, answer
details, mixed results, blocked trials, missing comparisons, and self-reported
evidence. Two examples show added command categories and mixed command patterns.
Each example links to HTML and Markdown reports.

The gallery and deterministic report checks share `tests/report_fixtures.py`.
They use the real decision-ingest and report-render commands with authored
synthetic inputs. No plugin installation, credentials, or model calls are needed.
These examples verify reporting, not model behavior or instruction effectiveness.
For live agent journeys, see [`e2e/README.md`](e2e/README.md).

Each command builds fresh reports outside the repository. After changing the
report code or fixtures, run the command again to see the change.

## Release

1. Update both plugin manifests to the same `X.Y.Z` version.
2. Merge the version change to `main` and wait for CI.
3. Create a GitHub Release with tag `vX.Y.Z`, targeting `main`.
4. Publish it as a stable release, not a prerelease.
5. Confirm the Release workflow pins the marketplace entry to `vX.Y.Z`.

The release workflow rejects tags that do not match both plugin manifests or
do not point to a commit on `main`. Drafts and prereleases do not update the
stable marketplace.

### Repository layout

- `plugin/` contains the installable plugin, skills, hooks, and runner.
- `e2e/` contains synthetic scenarios for manual product checks.
- `tests/` contains deterministic checks and a synthetic report gallery.
- [`e2e/README.md`](e2e/README.md) explains the demo and live-check fixtures.
- [`AGENTS.md`](AGENTS.md) and
  [`CODING_GUIDELINES.md`](CODING_GUIDELINES.md) contain contributor guidance.
