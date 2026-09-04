# Release Behavior Diff Skill Design

## Goal

Add a repository-local maintainer skill named `release-behavior-diff`. It releases one stable Behavior Diff version from `main` without letting the Claude Code and Codex plugin versions drift.

The skill defaults to the next patch version. A user can provide an explicit higher `X.Y.Z` version for a minor or major release.

## Scope

Create:

```text
.agents/skills/release-behavior-diff/
├── SKILL.md
└── scripts/
    └── bump-version.py
```

The skill is for repository maintenance. It is not part of the installable plugin under `plugin/`.

## Non-goals

- Do not create a new GitHub Actions release workflow.
- Do not change the existing marketplace updater or Release workflow.
- Do not support prerelease tags, build metadata, or non-SemVer versions.
- Do not open a pull request. This workflow commits and pushes `main` directly.
- Do not edit historical plans or the fixed sample versions in `tests/release-workflow-test.sh`.
- Do not roll back a pushed release commit automatically.

## Trigger and input

The skill triggers when a maintainer asks to release Behavior Diff, publish the next Behavior Diff version, bump its patch version, or create a `vX.Y.Z` release.

Input is optional when the current manifest version already has a GitHub
Release:

- No version: increment the current patch number. For example, `0.3.3`
  becomes `0.3.4`.
- Explicit `X.Y.Z`: use it only when it is a stable SemVer value greater
  than the current version.

Before starting a new bump, inspect the release for the current manifest
version. If it is missing, enter recovery mode and release the current
version instead of incrementing again. In recovery mode, an omitted version
or the explicit current version is valid; an explicit higher version is
rejected until the pending version is released.

The GitHub tag and release name are always `vX.Y.Z`. The manifest value never
includes the `v` prefix.

## Chosen architecture

Use a short `SKILL.md` for orchestration and one deterministic Python helper for version calculation and file updates.

```text
user request
    |
    v
SKILL.md preflight
    |
    v
bump-version.py [X.Y.Z]
    |  validate + update three active files
    v
repository checks
    |
    v
signed commit -> push main -> gh release create vX.Y.Z
    |
    v
watch existing Release workflow -> verify release
```

A skill-only implementation would require each agent to rebuild fragile search-and-replace commands. A manual-dispatch GitHub Action would be larger than the requested local workflow and would duplicate the existing release-on-publish automation.

## Preflight

Run every preflight check before changing a file:

1. Confirm the repository is `spacedock-dev/behavior-diff`.
2. Confirm the current branch is `main` and the working tree is clean.
3. Confirm `git` and `gh` are available and `gh auth status` succeeds.
4. Fetch `origin/main` and fast-forward local `main` with `git pull --ff-only origin main`.
5. Confirm both plugin manifests contain the same stable `X.Y.Z` version.
6. Check whether GitHub Release `v<current-version>` exists.
7. If it exists, calculate or validate the requested higher version and
   confirm neither its Git tag nor GitHub Release exists.
8. If it does not exist, enter recovery mode for the current version. Do not
   edit, commit, or bump again. If its tag already exists, verify that the tag
   points to a commit on `main` whose two manifests match the current version.
   If its tag does not exist, use the current remote `main` commit as the
   release target.

Stop at the first failed check. Do not stash, reset, force-push, delete tags, or repair unrelated repository state.

## Deterministic updater

Run from the repository root:

```text
python3 .agents/skills/release-behavior-diff/scripts/bump-version.py [X.Y.Z]
```

The helper:

1. Parses both plugin manifests with the Python standard library.
2. Requires their current versions to match stable `X.Y.Z`.
3. Calculates the next patch when no argument is present, or validates one explicit higher version.
4. Updates only:
   - `plugin/.claude-plugin/plugin.json`;
   - `plugin/.codex-plugin/plugin.json`;
   - the active manifest-version assertions and messages in `tests/live-report-contract.sh`.
5. Verifies each expected old value occurred exactly once in each manifest and four times in the active shell-test block before replacing it.
6. Parses both updated manifests again and confirms host parity.
7. Prints only the new plain version to stdout on success.

The helper performs no Git or GitHub operation. It fails before writing if validation fails. It builds all three new file contents in memory before replacing any file.

## Verification

After the updater succeeds, verify the new version and repository behavior:

```bash
python3 -c '<parse both manifests; require equality and the selected version>'
docker run --rm -v "$PWD:/mnt" -w /mnt \
  mvdan/shfmt:v3.14.0 -d -i 2 -ci .
bash tests/hooks-test.sh
python3 plugin/skills/behavior-diff/scripts/decisions.py --check
bash tests/live-report-contract.sh
bash tests/release-workflow-test.sh
git diff --check
```

Add a deterministic self-check for `bump-version.py` using temporary synthetic copies. It covers automatic patch calculation, an explicit higher version, malformed or mismatched manifest versions, a same/lower explicit version, and a stale active test contract. Wire this self-check into deterministic CI.

No check may invoke an AI model or publish a release.

## Commit and push

After every check passes:

1. Confirm the diff contains only the two manifests and `tests/live-report-contract.sh`.
2. Commit with DCO sign-off:

   ```text
   chore: bump plugin version to X.Y.Z
   ```

3. Capture the commit SHA.
4. Push with `git push origin main`. Never force-push.
5. Confirm `refs/heads/main` on origin equals the captured SHA.

## GitHub Release

Create the release at the exact pushed commit:

```bash
gh release create "vX.Y.Z" \
  --repo spacedock-dev/behavior-diff \
  --target "<commit-sha>" \
  --title "Behavior Diff vX.Y.Z" \
  --generate-notes
```

Using the commit SHA avoids a race where `main` moves between the push and tag creation.

Recovery mode uses one of two commands:

- No existing tag: use the normal command above with the current remote
  `main` commit as `--target`.
- Existing tag without a release: first verify the tag target, then create
  the release with `--verify-tag` instead of moving or recreating the tag.

Then find and watch the existing `Release` workflow run for that commit. This workflow validates the tag, runs deterministic CI, and updates the marketplace. Report a release as complete only after the workflow passes and `gh release view vX.Y.Z` confirms the tag and URL.

## Failure behavior

- Preflight failure: change nothing.
- Updater or verification failure: do not commit, push, tag, or release. Leave the focused version diff for inspection and report the failed command.
- Commit failure: do not push or release.
- Push rejection: do not force-push. Fetch and report that `main` moved.
- Release creation failure after a successful push: report that the version commit is on `main` but the release is missing. A retry must create the same `vX.Y.Z`; it must not bump again.
- Release workflow failure: keep the published release and report the failed workflow URL. Do not delete the release or tag automatically.

## Final output

On success, report:

- old and new versions;
- release tag and URL;
- pushed commit SHA;
- Release workflow result;
- marketplace update result.

On failure, report the last completed state so a retry can continue safely.

## Acceptance criteria

- The skill is discoverable as `release-behavior-diff` from the repository.
- Default invocation increments only the patch number.
- An explicit higher stable version is supported.
- Both host manifests and the active version contract change together.
- No historical version example changes.
- Verification finishes before commit and push.
- Every release commit has a DCO sign-off.
- The remote push is non-force and targets `main`.
- GitHub Release `vX.Y.Z` targets the exact pushed commit.
- The existing Release workflow is watched through completion.
- Partial failures never cause a second version bump or automatic rollback.
