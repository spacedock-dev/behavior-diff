# Background Behavior Diff run progress

Status: implemented locally; verified with synthetic processes and deterministic checks.

Tracking: [DRC-4878](https://linear.app/recce/issue/DRC-4878/monitor-background-behavior-diff-runs-with-persistent-status).

## Goal and agreed scope

A Behavior Diff run can execute in the host agent's background while the agent
works on something else. Both the human and the agent must be able to learn what
that specific run is doing without reconstructing its logs.

Implement:

- Unique run IDs and isolated run directories.
- Short console messages at lifecycle milestones.
- Persistent, machine-readable status.
- A read-only status command with human, JSON, and terminal watch views.
- Discovery of multiple active runs without silently choosing the latest one.

Preserve parallel execution across runs and within each run. The default remains
three trials per side; three simultaneous runs can therefore launch 18 trials,
followed by their assessment calls. Monitoring must not introduce a queue or
change spending, concurrency, model selection, trial semantics, or findings.

Not in scope: a browser dashboard, server, host-specific notification extension,
retry mechanism, cancellation command, concurrency manager, cost estimator,
telemetry, or GitHub Action implementation. No paid model calls are needed to
implement and verify this feature.

## Current implementation and constraints

Use the canonical [runner](../plugin/skills/behavior-diff/scripts/behavior-diff.sh),
[trial launcher](../plugin/skills/behavior-diff/scripts/run-trial.sh),
[extractor](../plugin/skills/behavior-diff/scripts/decisions.py), and
[renderer](../plugin/skills/behavior-diff/scripts/render.py).

At planning time:

- The runner creates `diff-YYYYmmdd-HHMMSS` with `mkdir -p`. Two runs started in
  the same second under the same home can share a directory. Replace this with
  atomic unique-directory allocation, retaining the readable timestamp prefix.
- It launches `2 × trials` background workers, prints one start message, and
  waits. Grades are generated after all workers finish.
- Trial CLI failures are caught rather than propagated directly. A nonempty
  final result produces `REVIEW`; otherwise the trial is `BLOCKED`. These are
  completeness states, not judgments of correctness.
- Claude writes its canonical trace while running. Codex, Pi, and OMP write raw
  streams and normalize them after execution. Missing canonical traces during
  those trials do not mean no work is happening.
- Extraction is best-effort. `decisions.py` can return normally without producing
  an assessment. A report may still be rendered using recorded evidence.
- The existing [command frontend](../bin/behavior-diff) takes a rule file and
  applies/restores it. It is not a subcommand-based status CLI; do not silently
  change that contract.

## User and agent experience

Immediately after a run is allocated, print its ID, directory, target, and exact
commands for checking and watching it. The skill retains that handle when it
starts the runner using the host's existing background-execution facility.

Proposed interface, bundled beside the runner:

```text
python3 scripts/status.py RUN_DIR
python3 scripts/status.py RUN_DIR --json
python3 scripts/status.py RUN_DIR --watch
python3 scripts/status.py --list [--active] [--json]
```

Paths in actual launch messages must resolve from any working directory. `RUN_DIR`
is explicit; listing uses `BEHAVIOR_DIFF_HOME` or its existing default. Do not
introduce ambiguous implicit `--latest` selection. List rows identify runs by ID,
project, target, and start time. Preserve the distinction between confirmed-active
and uncertain runs; `--active` should retain unfinished uncertain entries rather
than hide potentially live work.

A hypothetical human view:

```text
Behavior Diff · example-skill/SKILL.md
Stage       Running trials
Before      3 of 3 finished
After       2 of 3 finished
Remaining   After trial 3
Elapsed     4m 18s
Report      Not ready yet
```

Show preparing/running/finished trials and explicit problems where known. Never
label a finished trial as a pass. Do not show an overall percentage or ETA: trial
durations differ and assessment/rendering still remain after trials finish.

Milestones cover preparing, trials, checking trial results, comparing evidence,
rendering, and termination. Emit changes, not a repeated log line on every watch
refresh. Include the run ID in milestone lines so merged logs remain intelligible.

The agent queries JSON when the user asks or a next decision requires it. It must
not repeatedly poll while other useful work remains. Host completion notifications
can prompt the final response where supported; do not promise an automatic chat
notification on hosts that do not deliver one. Human watch is a separate read-only
process; closing it must not stop or block the runner.

## Persisted state and ownership

Use a versioned, bounded metadata schema, separate from `report-data.json`. A
progress-format change must not require changing the report schema or evidence.

Recommended ownership:

- The runner owns `RUN_DIR/status.json`: identity, stage, timestamps, recorded
  lifecycle, expected trials, owner identity, and report outcome.
- Each trial worker owns its own status sidecar under its trace directory, outside
  its project copy. Parallel workers never rewrite the shared run record.
- The assessment producer owns `RUN_DIR/assessment-status.json`, recording its
  outcome explicitly without racing the runner's record.
- The status reader combines those records into the same human/JSON view. This
  avoids a global lock, daemon, or shared runs index. Listing scans run directories.

Use temporary files plus atomic replacement within the same directory. Readers
must not observe partially written JSON. Component updates are independent, not a
transaction across all workers: retain per-record timestamps and an observation
time rather than pretending every row was captured at exactly the same instant.

State should include only what is needed to answer operational questions:

- Schema version, run ID, project/target identity, host/model, requested trial count.
- Start/update/end times and current phase.
- Per-trial preparation/execution/normalization/finished state, captured process
  exit when known, and final-result presence when validated.
- Recorded run lifecycle and separately observed liveness.
- Report availability/location, and explicit assessment outcome/reason.

Exclude task/purpose text, answers, tool payloads, stderr content, credentials, and
full environment dumps. Paths and model names are still local metadata, not a
license to publish these records. Keep sidecars out of the agent's variant project
and use private filesystem permissions.

## Truthful completion and interruption semantics

Keep these independent:

1. A trial process ended.
2. Usable trial evidence was recorded.
3. Evidence assessment is available.
4. A report was produced.
5. The orchestrating process completed or stopped.

A report with missing assessment is a useful partial result, not an automatic
success or a lost run. Conversely, runner exit code zero alone is not enough to
assert complete analysis. Record explicit producer outcomes; do not infer causes
from the presence of `decisions.raw.txt`, scrape prose logs, or treat the existence
of a JSON filename as proof its contents are usable.

Normal exits and catchable interruptions should leave terminal status. Preserve
existing trial and extraction failure behavior while recording the actual outcome.
Do not silently change workflow exit codes as part of this observability feature.

For an abrupt kill or a disconnected host:

- Distinguish last recorded state from current observations. A stale record that
  says running is not proof the process is still alive.
- Where local liveness is checked, identify the actual process using host/boot
  context and process-start identity, not PID alone. Handle PID reuse and Bash
  subshell identity correctly; retain Bash 3.2/macOS and Linux compatibility.
- If identity cannot be checked reliably, show `Status uncertain` plus the last
  recorded update. Do not manufacture a failure or success.
- An ended controller does not prove all trial children ended. Preserve known
  child states and flag uncertainty or surviving work honestly.
- No output for a long time does not mean stuck. If showing output activity,
  inspect raw-stream metadata rather than repeatedly parsing full traces; label
  it last output, not a health heartbeat or model reasoning progress.

No heartbeat service is required by this design. Prefer observed process identity
and truthful uncertainty over adding a second process that claims runner health.

## Reader behavior and errors

- Normal status queries are read-only and bounded by metadata, not log size.
- Query exit success means status was read, not that the comparison succeeded.
- Missing/invalid/unsupported status yields an explicit diagnostic, never a
  fabricated active or completed run. Handle a missing worker record during
  preparation without crashing the whole query.
- Older runs without progress metadata remain readable as reports; status says
  progress is unavailable. Do not retrospectively invent lifecycle history.
- Watch redraws on meaningful changes, uses modest bounded refreshes, and exits
  on a recorded terminal state or confirmed owner loss. On unverifiable liveness,
  visibly show uncertainty; user interruption stops the watcher only.
- Human output must work without ANSI/TTY support. JSON output contains no prose
  banners or ANSI sequences and reports the same facts as the human view.
- Monitoring errors must be visible and must not be mislabeled as model failures
  or alter recorded evidence. A broken/closed console observer must not become a
  control channel that terminates an otherwise viable run.

## Implementation sequence

1. Read current source and relevant callers/tests before edits. Freeze a small
   schema and the status CLI above; implement atomic writers and the reader with
   synthetic fixtures. Reuse existing dependency/runtime conventions.
2. Allocate collision-safe run directories, expose the handle before expensive
   execution, and instrument runner milestones. Invalid CLI requests before a run
   exists may still fail through ordinary stderr; do not claim task drafting by
   the parent agent is part of the runner's measured progress.
3. Record worker lifecycle and actual CLI outcomes, including preparation failures
   before `run-trial.sh` starts. Preserve normalization, grades, and trace content.
4. Record assessment/render outcomes explicitly. Keep report creation, assessment
   availability, and terminal run status separate, including fallback reports.
5. Add listing, human watch, local liveness observations, and interruption handling.
   Verify concurrent reads/writes and concurrent runs before documenting success.
6. Update the canonical [skill](../plugin/skills/behavior-diff/SKILL.md) so all
   hosts retain the run handle and know how to check it without busy-polling.
   Update [README](../README.md) and [architecture](../docs/architecture.md),
   including the execution flow/status artifacts, in the same feature change.

Do not add host-specific skill copies, a second report renderer, or an implicit
model run. A later GitHub Action can consume the same JSON contract but is not part
of this implementation.

## Acceptance and verification

Use deterministic synthetic fixtures/stub host executables. The repository's CI
must never invoke real model CLIs/APIs. No saved private demo evidence belongs in
committed tests.

Required observable cases:

- Two runs start simultaneously in the same home, create different IDs, and
  maintain separate statuses, traces, and reports. Neither run serializes the other.
- One run's trial completion updates while other trials remain running; Before and
  After counts do not bleed across workers or runs.
- Query and watch work from another directory/new process and while the parent
  agent continues other work. Closing watch leaves the run alive.
- Claude-style streamed traces and delayed normalized Codex/Pi/OMP traces produce
  truthful progress. Quiet raw output never becomes an automatic failure.
- Trial preparation failure, nonzero CLI exit, missing final result, extraction
  skipped/failed, and rendering failure remain distinguishable.
- A fallback report is linked when available without claiming assessment success.
- Catchable interruption, abrupt owner loss, PID reuse, and unverifiable host
  identity cannot leave a confident false running/success status.
- Readers tolerate atomic updates and report corrupt/unsupported metadata honestly.
  Old run directories without status do not acquire invented history.
- Paths with spaces, non-TTY output, private metadata boundaries, and per-run
  environment overrides behave correctly.
- Existing report outputs, grades, model selections, and parallelism retain their
  previous semantics.

After implementation, exercise the actual runner and status/watch commands using
controlled synthetic host processes: observe partial progress, both concurrent
runs, and terminal/partial-report states. Tests alone are not the runtime smoke.
Run the relevant deterministic suite and formatters from the repository guides.
Independent review is required before creating/updating a PR; use the existing
review/fix/re-review workflow if requested. No live model-cost approval is implied
by agreement on this plan.

## Completion boundary

This document records the agreed direction and concrete implementation defaults.
No further product decision is needed to begin. Resolve small technical details
from repository conventions; surface a material change to scope or execution
semantics rather than hiding it in implementation.

## Implementation verification

- Concurrent actual runner smoke used stub Claude and OMP hosts, then Pi and
  Codex. Same-second starts produced isolated runs; partial trial completion was
  visible from another working directory, and stopping watch left workers alive.
- Failure smokes distinguished nonzero host exit, missing final result, invalid
  trace normalization, project preparation failure, unavailable assessment, and
  renderer failure. Fallback reports retained their existing behavior.
- TERM recorded interruption; SIGKILL produced observed owner loss without
  claiming surviving workers had ended. Metadata contracts passed on macOS and
  Linux, including PID reuse, uncertain ownership, and container PID 1.
- The existing deterministic suite and Python/Bash formatting checks passed.
  No live model calls were made; these checks establish monitoring behavior, not
  model quality or report conclusions.
