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

Behavior Diff supports Claude Code and Codex. The commands below are for the
public marketplace release. The marketplace entry is not live yet.

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

Behavior Diff finds the changed instruction file and prepares a neutral task.
It shows you the task and the model cost before it starts. The run starts only
after you approve it.

The standard run starts six fresh agent trials: three without the change and
three with it. Fast mode starts one trial for each side.

## Read the report

Each run creates a local HTML report. The report contains:

- The instruction-file diff.
- The flow of each trial.
- The main decisions that changed.
- The commands and tools that each trial used.
- The final answer from every trial.

Start with the flow difference. Find the first point where the runs separate.
Then compare the evidence and final answers from that point.

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

It gives both copies the same task and starts fresh agent sessions. Standard
mode repeats each side three times. This makes one unusual model response less
likely to control the result.

The runner records tool calls, commands, evidence, decisions, and final answers.
It converts those traces into a common flow format, compares the two sides, and
builds the HTML report. It does not use a model to declare a winner.

The plugin also watches edits to `CLAUDE.md`, `AGENTS.md`, and `SKILL.md`. After
you finish the current task, it can ask whether you want to run Behavior Diff.
It never starts a model run without your approval.

### Repository layout

- `plugin/` contains the installable plugin, skills, hooks, and runner.
- `e2e/` contains synthetic scenarios for manual product checks.
- `tests/` contains deterministic checks that do not call a model.
- [`e2e/README.md`](e2e/README.md) explains the demo and live-check fixtures.
- [`AGENTS.md`](AGENTS.md) and
  [`CODING_GUIDELINES.md`](CODING_GUIDELINES.md) contain contributor guidance.
