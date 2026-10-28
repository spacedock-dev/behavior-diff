# Scenario and test data

Read this file before drafting the task for any comparison. It is the single
recipe for preparing the scenario, shared data, and private assessment
criteria from the change's intent, for preflighting and freezing them, and for
delivering shared files to every Before and After trial. You, not a script,
prepare the scenario and data; `prepare_shared.py` only stages and verifies
files you prepared and reviewed.

Spacedock workflow comparisons use the fixtures in
[spacedock-duo.md](spacedock-duo.md) for delivery; still derive their task and
criteria with the recipe below.

## Prepare from intent

Use the contemporary change, relevant unchanged instructions and references,
and available owner context. A supplied real request is usable, but not required.
For a historical comparison, exclude later fixes, later incidents, earlier
fixtures, and trial results; do not mine host transcripts. If the orchestrator
already knows later history or previous outcomes, derive historical purpose and
prepare the inputs in a fresh context that inherits none of that conversation.
Supply only the selected contemporary instruction versions, required references,
available contemporary owner context or commit message, and this generic method.
Use a supported fresh session or isolated subagent; if unavailable, stop and
report the missing isolation prerequisite before deriving or freezing purpose.
If case selection or tooling was informed by hindsight, still disclose that
limit: isolation does not remove historical selection bias.

1. **Goals.** Start from the frozen purpose goals. Name new behavior and
   behavior that must survive the change. Mark preservation goals as inferred
   unless stated.
2. **Capabilities and premises.** For each goal, list what the agent must
   observe, decide, or produce. For each capability, list the environment
   facts it depends on (files, query results, tools, permissions, repository
   state, time), where the trial can reach each fact, and which source is
   authoritative. Assessment-only knowledge must not stand in for a premise
   missing from the trial. If an outcome depends on time, set one as-of
   timestamp and timezone, give both variants the same neutral as-of statement,
   and make every simulated clock and calculation agree.
3. **Task.** Write a natural user request that starts before the tested work
   and reaches the changed rule. It defines starting state and scope only. It
   must not state the expected answer, the rule, a findings list, or a
   historical mistake. If both variants would comply because the task says
   what good looks like, rewrite it. Start mid-workflow only when skipped work
   is outside the capabilities being tested and the starting state is coherent.
4. **Data.** If the project base already exercises the capabilities, reuse it
   and add nothing. Otherwise build one coherent dataset: ordinary inputs plus
   a bounded set of plausible edge cases that challenge the goals'
   assumptions. Choose cases by relevance, plausibility, assessability, and
   added coverage of the intent; do not fill a quota or add redundant cases.
   Combine compatible cases; cases that contradict or obscure each other need
   separation, which is a separate comparison, not an incoherent fixture. Let
   the agent acquire facts through supported files or queries; do not replace
   discovery with a prepared findings list. Query returns can contain legitimate
   task facts, but assessment conclusions stay private. Any local tool or adapter
   must accept both correct and incorrect actions, record the actual submitted
   arguments or artifacts, and not enforce the desired result. Extra scenarios
   or trial sets require separate approval.
5. **Private notes.** Outside every trial input, in the private `0700`
   directory, record with mode `0600`: the goal → capability → premise →
   case mapping; why each case was selected; evidence that establishes whether
   each condition was reached, missed, or remains unknown; for each agreement
   check, the trial-reachable sources whose returned content must ground it;
   separate criteria for supported, contradicted, or insufficient-evidence
   outcomes for every case; cross-case cues and interactions; capabilities left
   untested; task wording or tool design that makes one action easier; and
   deviations from the original project, including replaced base files.
   Combined cases are not independent experiments. These are notes, not a
   schema, and never enter trials, the task, `--purpose-file`, or
   `--scenario-file`.
6. **Scenario record.** From the private notes, write a sanitized, structured
   record to the same private directory with mode `0600`. It tells the
   assessment and the report reader how the frozen task and data test each
   goal, and it fixes the checks the assessment must answer. Use this contract:

       {"summary":"Synthetic orders include one refund that conflicts with the ledger.","rationale":"The conflict tests whether the agent verifies totals against the ledger before reporting them.","conditions":["One synthetic refund appears in orders but not in the ledger."],"limitations":["Only one conflicting record is included."],"checks":[{"id":"reads-ledger","goal":1,"text":"The agent reads the ledger before reporting totals.","mode":"new","required_evidence":"A recorded read of the ledger file.","evidence_kind":"recorded_action"},{"id":"totals-match-ledger","goal":1,"text":"The reported total agrees with the ledger.","mode":"new","required_evidence":"The reported total and the recorded ledger return.","evidence_kind":"source_consistency"}],"source_requirements":[{"check":"totals-match-ledger","any_of":["*data/ledger.csv*"]}]}

   - `summary` (at most 400 characters): what the trials faced, neutrally.
   - `rationale` (at most 1,200): why this data challenges the goals'
     assumptions.
   - `conditions` (one to eight, at most 300 each): situations the data sets
     up.
   - `limitations` (zero to eight, at most 300 each): untested capabilities,
     interacting combined cases, modeled limits, task or tool wording that
     makes one action easier, and any hindsight in case selection.
   - `checks` (one to sixteen): each check is one observable criterion for one
     goal. `goal` is the 1-based position in the frozen purpose; every goal
     needs at least one check. `id` is a unique, stable plain identifier of at
     most 80 characters. `mode` is `correction`, `new`, `change`, or
     `preservation`. `text` and `required_evidence` are at most 600
     characters; `required_evidence` names what decides the check.
   - `evidence_kind` names exactly one kind of evidence: `recorded_action` for
     a recorded tool call such as a required code read, `output` for content
     of the final answer, and `source_consistency` for a final answer that
     must agree with recorded returned content. Split a compound requirement
     into separate checks. For example, "reads the code and reports the value
     it finds" becomes a `recorded_action` check for the read, an `output`
     check for the report, and a `source_consistency` check for agreement.
   - `source_requirements` (zero to thirty-two groups): frozen configuration
     that binds every `source_consistency` check to the recorded sources that
     must ground it. It is not part of a check definition, and the assessment
     never restates or edits it. Each group is `{"check":"<id>","any_of":[...]}`
     and names only a `source_consistency` check; every such check needs at
     least one group, and the list is `[]` when there is none. Groups for one
     check all apply (AND); the one to eight patterns inside a group are
     aliases (OR), for example the same file read with a read tool, `cat`, or
     `git show`, or the same record fetched with `gh api`. A `met` or
     `not_met` agreement outcome needs every group matched by a cited,
     readable recorded return. Otherwise the report rejects that check alone
     and shows it as not assessed; an absent required source never becomes a
     pass or a fail. A matched source shows only that the right return was
     available, not that the assessment interpreted it correctly.

     Derive the groups before trials from the prepared data and the check
     itself: which trial-reachable source is authoritative for the claim the
     check judges. Never derive or revise them from trial outcomes. A pattern
     is a case-sensitive glob (`*` and `?` only, no brackets, at most 200
     characters) over the captured descriptor: the tool name followed by its
     recorded JSON arguments, such as `Read {"file_path": "...", ...}` or
     `Bash {"command": "gh api repos/..."}`. It matches the descriptor, never
     the returned content or a model explanation. Anchor each pattern on a
     distinctive project-relative path, endpoint, or identifier and wrap it
     in `*`, for example `*data/ledger.csv*`. Patterns appear in the report:
     never include absolute or user-specific paths, private hosts, or names.
     The validator rejects tool-name-only, common-word, bare-extension, and
     wildcard-only patterns, and patterns that name a sensitive source.
     Captured returns come only from read and search tools, simple `cat`,
     `head`, `tail`, `grep`, `rg`, `ls`, and `wc` commands, `git show`,
     `git diff`, `git log`, `gh pr view`, `gh pr diff`, and `gh api` GET
     requests without fields, input, headers other than Accept, or another
     method. Pipelines, compound commands, sensitive sources, and
     descriptors cut at 240 characters never satisfy a requirement.
     Matching returns share each trial's existing recorded-content budget
     before incidental reads, so keep required sources small; many large
     required returns can still exhaust that budget.

   Use plain text: no Markdown, links, or control characters. Generalize
   private detail as for purpose: no names, credentials, private URLs, source
   excerpts, raw notes, or later history. Never record outcomes, per-trial
   results, or claims that a past problem was detected. The complete handoff
   validates this record against the frozen purpose using the shared readers.
   The runner validates it again before any model call and excludes the file
   from trial copies. The record, not the notes, goes to the assessment
   provider and appears in the report. The assessment fills outcomes for
   exactly these checks; it cannot add, drop, or reword one. When the purpose
   is `null`, write no record and omit `--scenario-file`.

Ask the user only when a material requirement cannot be reached from the
change, project, or conversation. Do not require an incident or an existing
eval.

## Preflight

Before spending trial calls, check the actual environment the trials will use,
under the host's intended permissions:

- The selected After bytes and the Before content or verified absence are
  available; every reference required by either version is in the trial base.
  Exactly the selected instruction differs between variants.
- Exercise the required reads, queries, local tests, artifact writes and safe
  action recording in scratch copies under the intended host tools and
  permissions. Confirm consistent facts and authoritative sources, including
  time when needed. Confirm that each source requirement names a source the
  trial can reach through a captured read form listed in step 6. Do not assume
  subagent dispatch or approvals exist.
- Represent relevant branch/remote state, permissions and existing user work
  explicitly. Use safe local artifacts for modeled publication; never include
  credentials or perform real external effects merely to test an instruction.
- Private context (purpose, scenario record, source, notes, criteria) must not
  enter the trial base. The runner removes the specified purpose, scenario, and
  source files, but does not find arbitrary evaluator files. Stage with
  `--exclude` for other private paths; use reviewed existing task data when no
  new data is needed. If safe staging is unsupported, stop rather than silently
  leak.

Run probes in scratch copies only. A probe may exercise discovery queries to
check the environment, but must not deposit its findings in trial inputs or
change the original project or frozen stage. The trial still performs discovery
itself. If a required capability or premise is missing, stop and report it.
Do not substitute a generic simulator or fabricate approvals. A deliberately
modeled limitation is part of the scenario; an accidental harness failure is not.

## Freeze

Freeze purpose before drafting, as `SKILL.md` requires. After semantic preflight,
write one private `handoff.json` (0600 in a 0700 directory) naming the reviewed
files and settings. All paths below are absolute except trial-relative
`references` and trial-relative custom `tools`; external tools use absolute paths.
Keep this descriptor and all context files outside the project, shared data and
stage. They never enter trials. Example (synthetic paths; use your actual files):

```json
{
  "task_file": "/private/scratch/task.txt",
  "purpose_file": "/private/scratch/purpose.json",
  "scenario_file": "/private/scratch/scenario.json",
  "notes_file": "/private/scratch/notes.md",
  "references": ["docs/guide.md"],
  "tools": ["tools/read_records.py"],
  "settings": {"agent": "codex", "reasoning": "unknown", "preparation_model": "current"}
}
```

`source_file` is optional and only names verified historical provenance.
Omit `scenario_file` for null purpose. Settings accept `agent`, optional
`model`, `extract_agent`, `extract_model`, `vocab`, and boolean `fast`, plus
descriptive `reasoning` and `preparation_model`. Preserve the current host;
Pi and OMP need their exact model. Preserve model/extraction overrides; absent
overrides retain the defaults in `SKILL.md`. Reasoning is recorded, not inferred
or configured by this helper. Include every required reference and custom tool;
the agent still reviews closure, privacy and actual capability probes. Hashing
a probe record does not establish that a capability worked.

For shared data/exclusions use `prepare --handoff` below. Otherwise use
`freeze --project "$PROJECT" --file "$TARGET" --output "$ROOT" --handoff
"$PRIVATE/handoff.json"`; this keeps the existing project path without staging.
It freezes the effective Git archive plus selected After (not unrelated working
edits), or the non-Git folder. Direct freeze cannot apply exclusions: use staging
when private project files must be removed. Both operations validate existing
purpose/scenario/source contracts and freeze context, notes, tools, settings and
Before. Neither executes commands from JSON or launches models.

Inspect `python3 "$SKILL_DIR/scripts/prepare_shared.py" verify "$ROOT" --json`
once for the complete readable inventory and runner arguments. Reuse this handoff,
not bespoke inventories or a second parent review. Any mismatch stops launch.

Keep the default three trials per side, or `--fast` only when the user asked.
More cases do not add runs; a richer scenario may still use more tokens per
trial. Stop preparation workers before launch. Keep the first result. Do not
change cases, data, criteria, or the scenario record after seeing outcomes, and
do not rerun to produce a finding.

## Assess the result

Use the local raw locator, never the assessment collector as the audit boundary:

```bash
python3 "$SKILL_DIR/scripts/audit_evidence.py" "$RUN_DIR"
python3 "$SKILL_DIR/scripts/audit_evidence.py" "$RUN_DIR" \
  --file before-1/trace.jsonl --offset 0 --length 65536
```

The inventory includes every expected trial, missing/unsafe/malformed states,
every original JSONL event and tool part with line/byte/JSON-pointer locations,
duplicate identities, native terminal/error events, stderr and all project
artifacts, including ignored and untracked files. Artifact presence does not
establish authorship; initial files are included too. Read original byte pages
until the relevant return/artifact is complete; there is no assessment eligibility
filter or total source budget. A bounded page is not the whole return. Preserve
host truncation/error flags and missing returns as evidence limits. The index
does not attribute ambiguous returns, infer completion from text or judge cases.
Keep output private and local, outside trial projects; never send this unfiltered
inventory or its raw pages to another provider without the applicable consent.

After the run, read raw trial evidence: actions, tool returns, and produced
artifacts, not only final answers. For every case in every trial, separately
record whether the condition was reached, missed, or unknown and whether its
intended outcome was supported, contradicted, or lacked sufficient evidence.
Then assess each goal without hiding missed cases or minority outcomes.
Check each trial's status, CLI exit and available native host terminal events
before treating normalized final text as a completed answer. A failed turn can
leave only an earlier progress message in that field. Keep interruptions,
provider errors and harness failures separate from requirement failures.
Nonempty error or progress text is not completion; a child's successful return
does not prove its caller finished the workflow.
Before and After can behave identically while After still fails its new goal;
report the unmet After goal alongside the unchanged behavior. State where this
raw assessment agrees or disagrees with the automatic report, including each
frozen scenario check it shows, and disclose untested capabilities. Never edit
an existing report to match the audit.

## When to deliver shared data

The runner builds each trial from the project base. In a Git project, the base
is `git archive HEAD`. Outside Git, the base is a copy of the folder. Apart from
the selected instruction, untracked and uncommitted Git files do not enter trials.

Use shared-data delivery when the comparison changes exactly one instruction
file, every Before and After trial must receive the same files, and either the
task needs files that are not in the project base or private context in the
project base must be kept out of trials.

If neither applies, use direct `freeze --handoff` instead.

Do not use this path for:

- Spacedock workflow comparisons. They use the fixtures in
  [spacedock-duo.md](spacedock-duo.md).
- State that the scratch baseline cannot hold. See [Limits](#limits).

If a required setup is not supported, tell the user before launch. Do not run a
narrower experiment silently.

Never write, stage, stash, or commit files in the user's checkout to make data
reach the trials.

## Historical comparison inputs

A PR or commit request supplies the comparison source; it does not require an
uncommitted edit. Resolve the source repository, exact revisions and selected
instruction path before local-edit discovery. Follow the source-isolation rule
above before deriving purpose or designing a scenario.

Prepare a private scratch project from the pinned After revision, not the user's
working tree. Materialize the selected Before instruction from the pinned Before
revision into a separate file outside that project. Preserve exact bytes; pass it
as `--before-file` to the preparation helper. The scratch project's selected
instruction is After. Keep the original checkout, index, branch and unrelated
modifications untouched. Obtain source provenance from the original repository,
not the scratch project. No dedicated PR flag or synthetic local edit is needed.

The ordinary runner compares one instruction while holding the surrounding
project constant. Retain references needed by either version and document the
common project context and any reviewed shared-file replacements. If companion
instructions also changed, do not claim that swapping one file tests the entire
PR. Use a supported content-preserving assembly or replay fixture with explicit
mapping and scope; if it cannot represent the requested comparison, report that
specific limitation rather than silently dropping changes. Do not substitute an
empty file for an absent historical instruction; use a supported absence fixture
or report that prerequisite. Missing revisions, ambiguous baselines and unsupported
capabilities are real blockers; a clean working tree is not.

After resolving the inputs, continue the same purpose, scenario, preflight,
freeze, authorization and launch procedure. Historical preparation does not
authorize extra runs, private-data disclosure, source changes or PR operations.

## Prepare the inputs

1. **Shared data.** Put the trial inputs in a data directory outside the
   project. The helper copies this tree into the same relative paths in the
   trial project. Include only files that every trial may read. Never include
   the purpose, scenario record, source metadata, expected answers, grading
   criteria, or evaluator notes. Review every file before preparation. The
   helper rejects unsafe file types and paths. It does not scan contents for
   secrets or private text.
   Shared paths replace matching base files; record them in the private
   notes. When staging only to exclude private context, the data directory
   holds reviewed existing project data that the task needs.
2. **Private context.** Keep the purpose file, the scenario record, the source
   file, and evaluator notes in a private directory with mode `0700`, outside
   the project, the data directory, and the stage. Give each file mode `0600`.
   If the project already contains such a file, pass its project-relative path
   with `--exclude`. This applies to a tracked file in a Git project and to any
   file in a non-Git folder. You cannot exclude the selected instruction file.
3. **Stage path.** Choose a stage path that does not exist yet. It must be
   outside the project and the data directory.

Set these values. Use absolute paths:

```bash
SKILL_DIR=<this skill's base directory>
PROJECT=<Git repository root, or the smallest non-Git folder with the file>
TARGET=<instruction path relative to PROJECT>
DATA=<reviewed shared-data directory outside PROJECT>
PRIVATE=<private 0700 directory with purpose.json, scenario.json, and optional source.json>
STAGE_PARENT=$(mktemp -d "${TMPDIR:-/tmp}/behavior-diff-stage.XXXXXX")
ROOT=$STAGE_PARENT/stage
```

Then prepare the stage:

```bash
python3 "$SKILL_DIR/scripts/prepare_shared.py" prepare \
  --project "$PROJECT" --file "$TARGET" --data "$DATA" --output "$ROOT" \
  --handoff "$PRIVATE/handoff.json"
```

Optional arguments:

- `--before-file <file>` supplies the Before content: an exact file extracted
  from the selected historical revision, a user-supplied original, explicit
  Before/After files, or a selected hook baseline. The helper reads it as content,
  even if its name ends in `-ABSENT`. If it is inside the project, the helper
  excludes it from the stage automatically.
- `--exclude <relative-path>` keeps one project path out of the stage. Repeat
  the option for each path.

Without `--before-file`, the helper selects Before in the same order as the
runner:

1. The target in Git HEAD, if HEAD contains it.
2. Otherwise, the newest hook baseline under
   `${BEHAVIOR_DIFF_HOME:-~/.behavior-diff}/baselines/`. Run `prepare` in the
   user's normal environment. Do not set `BEHAVIOR_DIFF_HOME` to the stage.
   Only a store entry ending in `-ABSENT` means that Before has no file.

An untracked target is not treated as absent. If no baseline exists, the
helper stops. Ask the user for the original content and pass it with
`--before-file`, as step 1 of `SKILL.md` describes. The helper also refuses
identical Before and After content.

On success, `prepare` prints the stage path and does these things:

- It creates `$ROOT/` with mode `0700`. The stage contains `project/`, `home/`,
  a private `freeze.json` with mode `0600`, and `before` when Before exists.
- It commits the common base, the shared data, and the selected Before version
  in a new scratch Git repository in `$ROOT/project/`. The repository has no
  remote, and its hooks and commit signing are off.
- It puts the After instruction in the scratch working tree.
- For a present Before, from Git HEAD or a file, it also freezes the Before
  content as `$ROOT/before`, outside the scratch project. The runner receives
  this file with `--before-file`.
- For an absent Before, it writes no `$ROOT/before`. It writes an `-ABSENT`
  marker under `$ROOT/home/baselines/` instead. The existing runner reads this
  marker through `BEHAVIOR_DIFF_HOME`.
- It confirms that `git archive` of the scratch commit reproduces the expected
  base exactly. If `.gitattributes` rules such as `export-ignore`,
  `export-subst`, or a filter change the archived files, `prepare` fails.
- It records the scratch commit and the content and executable bit of every
  file in `freeze.json`.

The helper never changes the original project or the data directory. It
copies the data, so later changes to the data directory do not affect the
stage.

If `prepare` exits with a nonzero status, the helper removes the incomplete
stage. Stop. Correct the inputs, then prepare a new stage path. Do not edit
files in a stage by hand.

## Verify, then run

Verification immediately before launch compares the complete handoff:

`verify` compares the effective project, Before or verified absence, context,
notes, declared settings and tool implementations with `freeze.json`. Its
read-only Git checks use the launch environment, including ordinary global/system
configuration. Archive transformations such as `tar.umask` removing executable
bits must fail verification, not silently change trial inputs. A nonzero exit
stops launch; correct inputs only before results and freeze a new private root.

Run verification and launch in the same shell environment. The helper rejects
Git repository, index, object-store, discovery and injected-config overrides
(such as `GIT_DIR`, `GIT_INDEX_FILE`, and `GIT_CONFIG_COUNT`) because the existing
runner would inherit them. Remove those overrides before preparing or launching;
do not bypass the failure. Ordinary user Git hooks/configuration remain existing
runner behavior, not a safety guarantee provided by this helper.

Use this fixed trusted runner invocation after inspecting the handoff. The helper
provides the arguments, project and home; do not build a second argv recipe or
execute a JSON-selected executable. Verification failure raises before launch.
This works for both staged and direct projects on Claude Code and Codex:

```bash
python3 - "$SKILL_DIR" "$ROOT" <<'PY'
import os, subprocess, sys
from pathlib import Path
scripts = Path(sys.argv[1]) / "scripts"
sys.path.insert(0, str(scripts))
from prepare_shared import verify
handoff = verify(sys.argv[2], as_json=True)
raise SystemExit(subprocess.call(
    [str(scripts / "behavior-diff.sh"), *handoff["argv"]],
    cwd=handoff["project"],
    env={**os.environ, "BEHAVIOR_DIFF_HOME": handoff["home"]}))
PY
```

The handoff includes only the frozen `$ROOT/before` when Before exists; absent
Before keeps the verified hook marker. Purpose/scenario go only to assessment
and reports, source only to report configuration, notes to neither. The runner
also validates and excludes its specified context files. Invocations outside
this skill without purpose retain labeled diff-only inference; without a
scenario record the assessment authors its criteria and labels that origin.

Source provenance must name the original repository and the original Before
and After commits. Verify it in the original checkout as step 1 describes.
Never read provenance from `$ROOT/project` or derive it from a scratch commit.
In the report, the Before label shows `$ROOT/before` or states that the file
did not exist, and the After label shows the stage path. These labels are
local names, not original revisions.

## Freeze discipline

- After `verify` passes, treat the complete handoff as frozen: the stage,
  task, purpose, scenario record, source, notes, and settings as frozen. See
  [Freeze](#freeze). No agent may edit `$ROOT/project/`, `$ROOT/before`,
  `$ROOT/home/baselines/`, `freeze.json`, or the runner and its scripts.
- To change the data, prepare a new stage and run a new comparison. Never
  prepare a new stage or edit data to turn a negative or inconclusive result
  into a finding. Keep and report the first results.
- The freeze detects changes before launch. It is not a sandbox. Trial agents
  can read and run what their host permits, and the stage files are not
  read-only. Separate directories do not protect against a hostile process.

## Reports and status

Runs from a stage land under `$ROOT/home/runs/<run-id>/`. Keep `$ROOT` after
the run. Deleting it deletes the reports and the freeze record. Use the run
directory that the runner prints with `status.py`. To list stage runs with
`--list`, set `BEHAVIOR_DIFF_HOME="$ROOT/home"`.

## Limits

- Exactly one instruction file differs between Before and After. All other
  initial files are the same on both sides.
- In a Git project, the base is HEAD. Other uncommitted work does not enter the
  stage. Trials do not receive the original Git history, branches, or remotes.
- Total input bytes are limited by `BEHAVIOR_DIFF_COPY_CAP_KB` (default
  `204800`, which is 200 MiB). Every trial copies the stage, so keep it small.
- The helper rejects symbolic links, special files, Git internals, submodules,
  unsafe or absolute paths, case-colliding paths, and file/directory
  collisions. It also rejects data that would replace the selected instruction
  or an excluded path.
- Changing the selected instruction's executable bit is unsupported; shared data
  files retain their executable bits.
- The stage keeps file content and the executable bit. It does not keep other
  permissions, ownership, timestamps, or empty directories.
- Live services, credentials, writable external systems, and multi-file
  instruction versions are not delivered.
- The helper does not detect secrets. The caller reviews every shared file.
- No path provides a filesystem sandbox. See [Freeze discipline](#freeze-discipline).
