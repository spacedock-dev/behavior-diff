# Extensible Behavior Diff pipeline

Status: design approved by Kent; implementation started. Independent specification
and standards reviews approved the corrected proposal. Approval is not runtime
verification or permission to publish, run paid evaluations, or retire live mode.

## Decision

Keep agent-authored preparation and Bash/Python headless execution. Separate
observation from goal assessment in fresh, restricted model contexts. Use a small
in-code pipeline registry with explicit dependencies and persisted artifacts;
do not introduce a workflow DSL or dynamic plugin framework.

The approved illustrated explanations remain available:
- [Simple design](../docs/behavior-diff-design.html)
- [Refactoring plan, benefits, and detailed contracts](../docs/behavior-diff-refactoring.html)

## Responsibilities

1. Host prepares the scenario, shared data, purpose, and frozen checks. Private
   case notes remain local. The coordinator validates preparation, not invents it.
2. Runner executes before/after trials with identical implementation, task, model
   selection, and trial counts. Only compared instruction snapshots differ.
3. Evidence indexing preserves local raw inventory, source IDs, and locations.
4. Observer receives a neutral, filtered, bounded evidence view selected without
   goals, diff, private criteria, or source requirements. Recorded instruction
   reads may reveal the change; disclose that limitation, not perfect blindness.
5. Assessor receives observations, goals/diff, and a separately filtered/bounded
   requirement-prioritized evidence view. Missing proof is not a negative verdict.
   Preserve labeled inferred-goal fallback for standalone runs without purpose.
6. Deterministic rendering reads persisted results. Host audits private cases
   locally and records attributed findings/corrections, not an unsaved competing
   verdict. The user decides whether to adopt the instruction change.

## Mandatory contracts

- Each pipeline stage declares required/optional inputs, output ownership, and
  terminal outcome. Validate unknown dependencies, cycles and duplicate ownership
  before effects. Execution failure is distinct from behavioral goal failure.
- Trial collection records all worker outcomes, including interrupted/failed
  trials. Preserve analysis with at least one complete trial per side; disclose
  unequal samples. Required failed observation blocks assessment. Rendering takes
  optional analysis results and still exposes evidence/status after failures.
- One writer owns each coordinator, trial, or analysis status record. Readers
  aggregate a logical view; concurrent workers never overwrite one shared file.
- Completed analysis artifacts are write-once. Explicit corrections append parent
  hash, author, reason, evidence references and changed fields, including narrative.
  Reject stale parents/invalid references; render the latest revision visibly and
  preserve the original. No automatic retries or report-file hand editing.
- Models receive only privacy-filtered bounded excerpts within existing consent.
  Unfiltered audit pages/private notes stay local. Broader provider disclosure
  requires explicit consent. Export only permitted sanitized host findings.
- Observer launches outside project/run directories in a fresh empty working
  directory, with file tools and automatic instructions/settings/MCP disabled.
  Fail closed if unsupported. Preserve existing provider fallback only if it meets
  identical isolation and records actual host/model; introduce no new fallback.
- Both Claude Code and Codex must pass real-host isolation checks before cutover
  ships. Failure on either requires a user decision, not reduced host support.
- Historical combined decisions remain readable through a labeled legacy-data
  loader, never fabricated as fresh observations. Migrate preview tooling away
  from old ingestion commands without paid re-extraction or executable aliases.

## Implementation sequence

1. Define artifact/stage contracts and validate dependencies with real deterministic
   operations. No placeholder handlers or new coverage feature.
2. Migrate existing execution mechanics without changing experimental meaning.
   First coherent increment introduces the coordinator and real post-trial
   operations while retaining snapshot/concurrent-worker lifecycle behavior.
   Remaining trial ownership migration stays explicit, not claimed complete.
3. Split observation/assessment/model invocation. Verify payload neutrality and
   host launch controls. Prove extension using real handlers after they exist.
4. Integrate separated artifacts, revisions, schemas and legacy report reading.
5. Migrate every consumer, including host skills, fixture ingestion, progress,
   human evaluation, preview, retro, Spacedock Duo, history replay, README, CI and
   dogfood Action. Remove obsolete extraction paths only at coherent cutover.

The first implementation increment is mechanical. It does not claim the new
semantic separation or isolation is implemented. Subsequent phases stay pending
until their own acceptance checks pass. Keep incomplete cutover work unreleased.

## Verification and release gates

Use shipped entry points with hermetic host stubs; verify dependency validation,
partial failures, concurrent status ownership, interruption handling, reports and
exit behavior. Run relevant deterministic suites and formatters after integration.
Stub checks do not prove real host isolation or model interpretation.

Before semantic cutover: approved real-host isolation checks on both default hosts,
separately approved/priced evaluation of quality/cost/latency, dogfood Action cost
review, and explicit approval to retire behavior-diff-live. Preserve existing
released live functionality until that gate; do not add a permanent forwarding
alias. Paid runs, commits, pushes, PRs, merges and releases require their respective
authorizations. No speed, cost or accuracy improvement is promised without evidence.

## First increment implementation record

Implemented the pipeline contracts and the real grading → existing combined
extraction → rendering coordinator. Bash still owns snapshot preparation,
concurrent trials, terminal run status and interruption cleanup. The coordinator
writes a separate status record; readers aggregate it without changing run owner
or terminal-state authority. Extraction failure remains compatible with rendering
an evidence-only report. No observation/assessment split is claimed yet.

Repeated execution refuses existing stage records or declared outputs, including
failed records. Dependency-aware explicit reruns remain pending rather than
exposing a partial retry API. Completed stages must produce regular nonsymlink
declared output files; invalid outputs fail the stage and optional consumers may
continue. Future semantic migration and all release gates above remain pending.

### Verification of the first increment

- Pipeline contract tests: 14 passed.
- Assessment lifecycle tests: 10 passed; progress/status contracts passed.
- Full hook checks passed, including Pi/OMP extraction model propagation.
- Shipped runner smoke with deterministic Claude/Codex stubs: 36 passed.
- Repository Python formatting (161 files), Bash formatting, Bash runner syntax,
  and whitespace checks passed.

The first smoke run had one nested-Claude frozen-stage verification failure
without an explanatory diagnostic. The assertion now includes verifier output;
the focused diagnostic and two subsequent full smoke suites passed. Root cause
of that initial failure remains unknown; this is not claimed as a fixed bug.

The mechanical migration initially bypassed the prior PATH-based Python child
launch boundary. Restoring that boundary and passing the new adapter through the
existing harness preserved its actual extraction/model assertions; hook checks
then passed. These results prove deterministic orchestration, not live model
quality, observer isolation, or the future semantic split.
