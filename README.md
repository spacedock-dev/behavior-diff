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

### Trial and extraction models

Scenario execution and decision extraction use separate model defaults:

| Host | Scenario trials | Decision extraction |
| --- | --- | --- |
| Claude Code | `opus` | `sonnet` |
| Codex | `sol` | `luna` |

`sol` and `luna` are Behavior Diff selectors, not native Codex aliases.
The runner reads `codex debug models` and selects the newest visible stable
`gpt-<version>-sol` or `gpt-<version>-luna` by numeric version. It resolves the
trial selector once before launching trials. All Before and After trials use
that exact ID, and the report displays it. Extraction resolves its own selector
and records that model separately.

Use `--model <exact-id>` to pin a trial version without catalog discovery.
`--extract-agent` and `--extract-model` override extraction. An explicit
extraction host wins; otherwise a `sol` or `luna` extraction selector selects
Codex. With no overrides, Claude and Codex extraction stay on the trial host.
They do not silently switch hosts when extraction fails.

A missing, malformed, or empty family catalog stops trial selection before
any trials start. An extraction discovery failure leaves the trial evidence
available without a decision diff. Use a Codex CLI that supports
`codex debug models`, or provide an explicit model ID.

Standalone `decisions.py`, without a selected host, tries Codex/Luna and can
fall back to Claude/Sonnet if Codex is absent or its model call fails.
Discovery errors stop extraction; explicitly selected hosts never switch.

Live Claude and Codex trials use the same model roles. If the host cannot
select the trial model, the skill uses the headless runner instead. Live
extraction stays in-session and is skipped if its model cannot be selected.
Pi and OMP headless trials still require exact model IDs; OMP live trials
retain the parent session's model.

Family selectors can resolve to newer versions on later runs. Use explicit
IDs when comparisons across runs must retain the same model version.

## Read the report

A **run** compares the instruction versions. A **trial** is one agent execution on
one side. Each run creates a local HTML report with six tabs:

- **Summary** tells a four-part numbered story: the intended change, what the
  evidence shows, what needs your attention, and what this means. Illustrated
  Before/After cards retain every observed branch and its trial count, and
  distinguish plans, answers, and recorded actions. The primary result stays
  visible when a secondary comparison leads the story.
  **What needs your attention** explains relevant tradeoffs with pictures,
  consequences, applicability, and possible actions. An expected tradeoff can
  matter too. An assessed-empty result is distinct from an unavailable
  assessment; neither hides the underlying comparisons.
  **See why this matters** opens the detailed attention explanation.
  **Full scenario and expected behavior** contains the setup and nested full
  prompt; complete evidence limits remain in their own disclosure.
- **Understand the change** preserves the original explanation. Attention detail
  adds reasoning, all branch counts with links to supporting trials, cited
  context, and uncertainty instead of repeating the Summary pictures and actions.
  Count-only saved evidence explicitly marks trial attribution unavailable.
  Optional **Check the evidence** disclosures link to raw comparisons.
  **Not relevant here** hides a Summary finding's body for this report session;
  **Show again** or reloading restores it. This does not change the evidence.
- **Instruction changes** shows the saved aim, filename, line counts, and
  complete instruction diff. **Likely aim** marks an inferred interpretation;
  **Supplied expectation** marks an explicit expectation. Missing explanations
  stay unavailable. Section or line-range links select a diff block, highlight
  its changed lines, and scroll to it without hiding the rest of the diff.
  Related edits are interpretations, not causal proof.
- **Behavior diff** shows an ordered, two-lane comparison. Before and After
  behaviors align at each comparison in the model-extracted order, with all
  trial counts visible. Mixed behaviors stay within each comparison, not in
  connected branches.

  Amber marks changed comparisons, teal marks unchanged or matching
  proportions, and gray marks unavailable comparisons. The info popup beside
  the heading separates comparison status, decision role, and evidence source.
  Blue identifies actions, violet the primary result, and indigo answer
  details; teal identifies recorded-command sources and amber final-answer
  sources. Labels and colors do not mean success or failure.

  Open a comparison to inspect its question, source, notes, related edits,
  and supporting **Trial 1 / Trial 2 / Trial 3** links. Each is a separately
  spaced link to a complete Before/After trial group; links wrap on narrow screens.
  The report states when individual-trial
  attribution is unavailable. **Expand all** and **Collapse all** control
  comparison disclosures. The comparison order is not an execution path.
- **Flow diff** groups only identical complete recorded command sequences,
  retaining counts and links to every contributing trial. Different paths
  remain separate. A table also compares command-category combinations.
  Without captured command evidence, the tab explains why flow is unavailable;
  it does not infer commands from answers or self-reported actions.
- **Trial evidence** aligns Before on the left and After on the right within
  each numbered group, including on mobile. **What changed** gives a short
  takeaway, one sentence per side, and a caveat only when needed. These
  model-written summaries describe that group's records, not aggregate counts.
  Full final answers remain visible below. Shared supporting-detail and command
  disclosures open both sides
  together; **Show both** and **Hide both** control a whole group. Missing
  records remain explicit. Trial numbers align records for reading, not paired
  execution: Before and After trials are independent.

Printing includes all tabs and disclosure content, with legends below their
headings. The screen's disclosure states are restored afterward.

Start with the instruction edit and the prominent comparisons. **Final result**
still means the primary result identified by the model, not the highest-ranked
comparison. **Final answer** is the recorded answer text. **Action** comparisons
come from recorded commands or self-reported actions; **Answer detail** comparisons
come from the final answer. Wording differences alone do not establish an action change.

In Summary and Behavior diff, counts such as **3 of 3 trials** refer to trials,
not repeated actions within one trial. For new extractions, the model assigns
named trials to behaviors; code derives counts from complete, unique membership
on each side. Those assignments remain in `decisions.json` for auditing.
This validates bookkeeping, not whether a trial was classified correctly.
Separate row counts do not show a complete sequence within one trial.
**Changed** compares extracted behavior proportions. **Unchanged** is shown for
complete, unanimous same-behavior evidence; matching proportions without that
evidence are labeled **Same proportions**. **Unavailable** means extracted
states cannot support a comparison. A consistent change requires a different
unanimous behavior on each side, at least two trials per side, and complete trial
evidence. This is an observed
pattern, not statistical significance. Single-trial, blocked, missing, and mixed
evidence is not promoted as a consistent change.

In Flow diff, progression preserves command order and repeated commands. Before
and After trials are independent. Empty records and blocked trials remain visible.
Recorded commands do not prove successful execution.

The command-category table groups each trial into one category combination.
Category order is not execution order. Matching categories can contain different
commands or files, so matching patterns do not establish unchanged behavior.

Follow **View behavior comparisons** to Behavior diff, or inspect the trial records
for original commands and answers. Markdown retains the five sections, story,
counts, complete instruction diff, and grouped trial evidence without illustrations.

The existing extraction call identifies the primary result, possible explanations,
and related instruction-diff hunks. It first recovers observed choices, then
interprets their relationship to the supplied edit. **Related edit** links are
labeled as model interpretation, not causal proof or knowledge of author intent.
The same call supplies optional plain-language Summary text: a takeaway, short
scenario, Before/After descriptions, and supported implications or cautions.
The writing instructions require concrete actor/action/object contrasts, parallel
Before/After descriptions, and a clear distinction between changed decisions or
actions and changed explanations, citations, or presentation. The decisive
contrast belongs in the headline and cards, not only in an additional finding.
It also interprets the edit's likely aim, citing instruction-diff hunks rather
than inferring intent from trial outcomes. **Edit goal** shows one sentence
with an **Inferred** badge and an edit link; the info popup explains the source
and its limits. Supplied expected behavior takes precedence and is labeled
**Supplied expectation**, not attributed to the author.
Without either source, the aim is marked unavailable; the instruction diff
remains accessible. These observations do not establish that a goal was met.
Equivalent meanings should use identical choice labels. Summary counts come
from the decision rows, not a second estimate. Code validates references and
choice coverage; it cannot prove that model-written explanations are true.
With complete evidence, a validated narrative can lead with any row whose choice
proportions change, even if it is mixed or is not the primary result. Selecting
that row does not change the primary-result identity. Evidence ranking is the
fallback when narrative is missing or unsupported; unchanged or matching-proportion
rows must still qualify under that ranking. Mixed results keep their full counts
and cautions. Structural validation does not prove a narrative's interpretation.
The renderer owns HTML, colors, and a fixed set of SVG illustrations.
A named unchanged targeted behavior applies only to the observed scenario.
Missing links do not mean the edit had no effect. A changed result is not an
automatic success or failure.
Before and After use neutral borders. PASS and FAIL colors indicate grades
against the supplied expectation, not a judgment that After is better.
Instruction diff colors still mark added and removed lines.

Mixed results show the choices and their trial counts. Missing, blocked, or
incomplete evidence produces an insufficient-evidence result. Without an
identified primary result, the report labels its comparisons as reported answers.
It does not guess the final result.

Expected behavior is labeled as supplied, or explicitly unavailable. The evidence
limits state trial counts, provenance, and grading limits. Self-reported actions
remain distinct from captured tool calls.

The structured `report-data.json` uses schema version 8, including per-group
`decisions.trial_summaries`, visual `summary`, sourced instruction `intent`,
saved `content.task`, optional narrative, and `edit_hunks`.
The task comes from the run's `task.md`, or the capsule's copy
when absent from the run. A scenario description never replaces missing task text.
Regenerate reports from their original run artifacts;
older report-data files are not accepted. `render.py` needs the run directory,
capsule directory, recorded model label, and original configuration. Rendering
does not run trials or call a model.

Old `decisions.json` observations can be re-rendered with the new layout.
Without narrative, the Summary uses original choice text and marks explanations
unavailable. Missing trial summaries, aim interpretations, and edit mappings
remain unavailable. Trial summaries are produced in the existing extraction
call; rendering never substitutes an overall conclusion for a trial's summary.
To obtain them, explicitly rerun extraction on saved evidence after approving
its model cost; no new trials are needed. Rendering never triggers extraction.
The extractor stores the exact `instruction_diff` with its mappings. External
`--emit-prompt` also saves `decisions.prompt.json` so `--ingest` retains the emitted
diff's provenance. Invalid or stale mappings and inferred aims are omitted
without discarding observed choices. Rendering never invents replacements.

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

See [Technical architecture](docs/architecture.md) for the execution flow,
component boundaries, and report-generation pipeline.

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

The examples cover changed and unchanged results, action changes, answer details,
mixed results, blocked trials, missing comparisons, and self-reported evidence.
They include a mixed primary-result headline competing with a unanimous secondary
action, a non-primary headline competing with a changed outcome, added command
categories, and mixed command patterns.
Each example links to HTML and Markdown reports.

The gallery and deterministic report checks share `tests/report_fixtures.py`.
They use the real decision-ingest and report-render commands with authored
synthetic inputs. No plugin installation, credentials, or model calls are needed.
These examples verify reporting, not model behavior or instruction effectiveness.
For live agent journeys, see [`e2e/README.md`](e2e/README.md).

Each command builds fresh reports outside the repository. After changing the
report code or fixtures, run the command again to see the change.

## Manually evaluate summary quality

From this checkout, ask your coding agent:

> Run a Behavior Diff human evaluation.

The local
[`run-behavior-diff-human-evaluation`](.agents/skills/run-behavior-diff-human-evaluation/SKILL.md)
skill prepares five blind, four-option questions using randomly sampled skill
changes from **`DataRecce/recce-team`**. Every new evaluation pins the current
upstream `main` and records a fresh random seed. It uses this checkout's current
Behavior Diff code, including uncommitted changes—not the installed plugin.

The skill requires private-repository access through authenticated `gh` and fresh
approval for 30 Claude Code trials plus extraction. Trial execution is a
read-only local replay; it does not post to GitHub or change Linear issues.
Both Claude Code and Codex maintainer sessions can invoke the workflow; its
trial stack is explicitly Claude Code.

The localhost quiz hides instruction diffs, stated intent, and commit metadata
until submission. It preserves generated summary wording, collects confidence
and insufficient-evidence feedback, saves the first complete submission, then
reveals the correct answers and full reports. To analyze a completed session,
ask the agent to **analyze the human evaluation results**.

All private artifacts remain under `~/.behavior-diff/human-evaluations/`, outside
the checkout. The workflow is manual only; CI runs synthetic helper tests, never
live evaluations. Five cases are diagnostic evidence, not an overall accuracy
estimate. See the skill's [protocol](.agents/skills/run-behavior-diff-human-evaluation/references/workflow.md)
for sampling eligibility, preparation, consent, and scoring.

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
