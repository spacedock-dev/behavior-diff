# Scenario and test data

Read this file before you run a comparison whose task needs shared files that
the runner's project base does not contain. It explains how to deliver an
already selected dataset to every Before and After trial. It does not generate
a scenario or data. Step 2 of `SKILL.md` still drafts the task, and the user
supplies or approves the files.

## When to deliver shared data

The runner builds each trial from the project base. In a Git project, the base
is `git archive HEAD`. Outside Git, the base is a copy of the folder. Apart from
the selected instruction, untracked and uncommitted Git files do not enter trials.

Use shared-data delivery only when all of these conditions are true:

- The task needs common files that are not in the project base.
- Every Before and After trial must receive the same files.
- The comparison changes exactly one instruction file.

If the task needs no extra files, use the normal step 3 command instead.

Do not use this path for:

- Spacedock workflow comparisons. They use the fixtures in
  [spacedock-duo.md](spacedock-duo.md).
- State that the scratch baseline cannot hold. See [Limits](#limits).

If a required setup is not supported, tell the user before launch. Do not run a
narrower experiment silently.

Never write, stage, stash, or commit files in the user's checkout to make data
reach the trials.

## Prepare the inputs

1. **Shared data.** Put the trial inputs in a data directory outside the
   project. The helper copies this tree into the same relative paths in the
   trial project. Include only files that every trial may read. Never include
   the purpose, source metadata, expected answers, grading criteria, or
   evaluator notes. Review every file before preparation. The helper rejects
   unsafe file types and paths. It does not scan contents for secrets or
   private text.
   Shared paths replace matching base files. Record the intended deviations
   from the original project, including any replaced base files, in private
   preparation notes outside the trial inputs before staging.
2. **Private context.** Keep the purpose file, the source file, and evaluator
   notes in a private directory with mode `0700`, outside the project, the data
   directory, and the stage. Give each file mode `0600`. If the project already
   contains such a file, pass its project-relative path with `--exclude`. This
   applies to a tracked file in a Git project and to any file in a non-Git
   folder. You cannot exclude the selected instruction file.
3. **Stage path.** Choose a stage path that does not exist yet. It must be
   outside the project and the data directory.

Set these values. Use absolute paths:

```bash
SKILL_DIR=<this skill's base directory>
PROJECT=<Git repository root, or the smallest non-Git folder with the file>
TARGET=<instruction path relative to PROJECT>
DATA=<reviewed shared-data directory outside PROJECT>
PRIVATE=<private 0700 directory with purpose.json and optional source.json>
STAGE_PARENT=$(mktemp -d "${TMPDIR:-/tmp}/behavior-diff-stage.XXXXXX")
ROOT=$STAGE_PARENT/stage
```

Then prepare the stage:

```bash
python3 "$SKILL_DIR/scripts/prepare_shared.py" prepare \
  --project "$PROJECT" --file "$TARGET" --data "$DATA" --output "$ROOT"
```

Optional arguments:

- `--before-file <file>` supplies the Before content: a user-supplied original,
  user-given before/after files, or one entry that you selected from the hook
  baseline store. The helper always reads this file as content, even if its
  name ends in `-ABSENT`. If the file is inside the project, the helper excludes
  it from the stage automatically.
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

Run `verify` immediately before launch:

```bash
python3 "$SKILL_DIR/scripts/prepare_shared.py" verify "$ROOT"
```

`verify` compares the scratch commit, the archived files, the working files,
and the frozen Before file or absent marker with `freeze.json`. Its read-only
Git checks use the launch environment, including ordinary global/system
configuration. Archive transformations such as `tar.umask` removing executable
bits must fail verification, not silently change trial inputs. If `verify`
exits with a nonzero status, do not launch. Prepare a new stage.

Run verification and launch in the same shell environment. The helper rejects
Git repository, index, object-store, discovery and injected-config overrides
(such as `GIT_DIR`, `GIT_INDEX_FILE`, and `GIT_CONFIG_COUNT`) because the existing
runner would inherit them. Remove those overrides before preparing or launching;
do not bypass the failure. Ordinary user Git hooks/configuration remain existing
runner behavior, not a safety guarantee provided by this helper.

Run the existing runner from the scratch project, with `$ROOT/home` as Behavior
Diff home. Use the same `--agent`, `--model`, and `--fast` choices as step 3.
The last line adds `--before-file` only when `$ROOT/before` exists. It expands
to nothing for an absent Before, in Bash and zsh:

```bash
before_args=()
if [ -f "$ROOT/before" ]; then
  before_args=(--before-file "$ROOT/before")
fi
python3 "$SKILL_DIR/scripts/prepare_shared.py" verify "$ROOT" &&
(cd "$ROOT/project" &&
  BEHAVIOR_DIFF_HOME="$ROOT/home" \
    "$SKILL_DIR/scripts/behavior-diff.sh" --agent <current-host> \
    --file "$TARGET" --task "<task>" \
    --purpose-file "$PRIVATE/purpose.json" \
    ${before_args[@]+"${before_args[@]}"})
```

Pass only `$ROOT/before` as `--before-file`, and only when it exists. Never
pass the original Before path or a hook-store entry to a staged run. For a
historical comparison with verified provenance, also append
`--source-file "$PRIVATE/source.json"`.

Source provenance must name the original repository and the original Before
and After commits. Verify it in the original checkout as step 1 describes.
Never read provenance from `$ROOT/project` or derive it from a scratch commit.
In the report, the Before label shows `$ROOT/before` or states that the file
did not exist, and the After label shows the stage path. These labels are
local names, not original revisions.

## Freeze discipline

- After `verify` passes, treat the stage, task, purpose, and source as frozen.
  Stop any preparation worker before launch. No agent may edit
  `$ROOT/project/`, `$ROOT/before`, `$ROOT/home/baselines/`, `freeze.json`, or
  the runner and its scripts.
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
