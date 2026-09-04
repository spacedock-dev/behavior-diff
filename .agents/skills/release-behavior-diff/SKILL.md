---
name: release-behavior-diff
description: Release a stable Behavior Diff version from main. Use whenever a maintainer asks to release or publish Behavior Diff, bump its patch version, create a Behavior Diff vX.Y.Z GitHub Release, or recover a pushed version whose release is missing.
---

# Release Behavior Diff

Release one stable version without letting the Claude Code and Codex plugin
manifests drift. This workflow intentionally commits and pushes `main`
directly. Never open a pull request for the version bump.

An explicit version is optional. Without one, release the next patch. With one,
accept only a higher stable `X.Y.Z` version. Never accept a leading `v`, a
prerelease, or build metadata.

## Preflight

Complete every check before changing a file.

1. Require `git`, `gh`, `python3`, Docker, and `uvx`. Run `gh auth status`.
2. Run `gh repo view --json nameWithOwner --jq .nameWithOwner`. Require
   `spacedock-dev/behavior-diff`.
3. Require `git branch --show-current` to return `main` and
   `git status --short` to return no output. Stop rather than stash, reset,
   switch branches, or repair unrelated state.
4. Run `git fetch origin main --tags`. Compare `git rev-parse HEAD` with
   `git rev-parse origin/main`.
   - If equal, continue.
   - If local `HEAD` is an ancestor of `origin/main`, run
     `git pull --ff-only origin main`, then require equality and a clean tree.
   - If local is ahead or the branches diverged, stop.
5. Read both plugin manifests and validate their versions:

```bash
current=$(python3 <<'PY'
import json
import re
from pathlib import Path

paths = [
    Path("plugin/.claude-plugin/plugin.json"),
    Path("plugin/.codex-plugin/plugin.json"),
]
versions = [json.loads(path.read_text()).get("version") for path in paths]
if versions[0] != versions[1]:
    raise SystemExit("plugin manifest versions differ")
pattern = r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)"
if not isinstance(versions[0], str) or not re.fullmatch(pattern, versions[0]):
    raise SystemExit("plugin version is not stable X.Y.Z")
print(versions[0])
PY
)
```

6. Check the current release:

```bash
gh release view "v$current" --repo spacedock-dev/behavior-diff
```

If it exists, use **new-version mode**. If the command fails, treat the release
as missing only when its diagnostic explicitly says `release not found` or
reports HTTP 404. Any authentication, network, API, or other error stops the
release.

If the current release is missing, use **recovery mode**. Release `current`
without editing, committing, or incrementing again. Reject an explicit version
other than `current` until recovery completes.

## New-version mode

Choose `new` without changing a file. If the user supplied a version, store its
exact text in `requested`. Otherwise leave `requested` unset. Run:

```bash
new=$(CURRENT="$current" REQUESTED="${requested-}" python3 <<'PY'
import os
import re

current = os.environ["CURRENT"]
requested = os.environ["REQUESTED"]
pattern = r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)"
current_parts = tuple(map(int, current.split(".")))
if requested:
    if not re.fullmatch(pattern, requested):
        raise SystemExit("requested version must be a higher stable X.Y.Z")
    target = tuple(map(int, requested.split(".")))
else:
    target = current_parts[0], current_parts[1], current_parts[2] + 1
if target <= current_parts:
    raise SystemExit("requested version must be a higher stable X.Y.Z")
print(".".join(map(str, target)))
PY
)
```

Check both remote objects before mutation.
`git ls-remote --tags origin "refs/tags/v$new"` must succeed with no output.
`gh release view "v$new"` must fail with an explicit not-found result. Any
existing tag, existing release, or other command error stops the release.

Now run the updater:

```bash
if [[ -n ${requested-} ]]; then
  updated=$(python3 .agents/skills/release-behavior-diff/scripts/bump-version.py "$new")
else
  updated=$(python3 .agents/skills/release-behavior-diff/scripts/bump-version.py)
fi
```

Require `updated` to equal `new`. The updater rejects invalid, equal, lower, or
mismatched versions.

The updater may change only:

- `plugin/.claude-plugin/plugin.json`
- `plugin/.codex-plugin/plugin.json`
- `tests/live-report-contract.sh`

Run every check before committing:

```bash
VERSION="$new" python3 <<'PY'
import json
import os
from pathlib import Path

claude = json.loads(Path("plugin/.claude-plugin/plugin.json").read_text())
codex = json.loads(Path("plugin/.codex-plugin/plugin.json").read_text())
if claude != codex or claude.get("version") != os.environ["VERSION"]:
    raise SystemExit("updated plugin manifests do not match the selected version")
PY
docker run --rm -v "$PWD:/mnt" -w /mnt \
  mvdan/shfmt:v3.14.0 -d -i 2 -ci .
uvx ruff@0.16.5 format --check --diff .
bash tests/hooks-test.sh
python3 plugin/skills/behavior-diff/scripts/decisions.py --check
bash tests/live-report-contract.sh
bash tests/release-workflow-test.sh
python3 .agents/skills/release-behavior-diff/scripts/bump-version.py --check
git diff --check
```

Require `git status --short` to name only the three allowed files. Commit with
DCO sign-off:

```bash
git add plugin/.claude-plugin/plugin.json \
  plugin/.codex-plugin/plugin.json tests/live-report-contract.sh
git commit --signoff -m "chore: bump plugin version to $new"
```

Set `sha=$(git rev-parse HEAD)`.

## Recovery mode

Set `new=$current` and start with `sha=$(git rev-parse origin/main)`. Do not run
the updater or create a version commit.

Check the remote tag with
`git ls-remote --tags origin "refs/tags/v$new"`. An empty successful result
means no tag; use the new-tag release command below. A command error stops the
release.

If the tag exists without a release:

1. Run `git fetch origin "refs/tags/v$new:refs/tags/v$new"`.
2. Set `tag_sha=$(git rev-list -n 1 "v$new")`.
3. Require `git merge-base --is-ancestor "$tag_sha" origin/main` to succeed.
4. Read both manifests at the tag with
   `git show "v$new:plugin/.claude-plugin/plugin.json"` and
   `git show "v$new:plugin/.codex-plugin/plugin.json"`. Require both versions
   to equal `new`.
5. Set `sha=$tag_sha` and use the existing-tag release command below.

## Push and publish

In new-version mode, push with `git push origin main`. Never force-push. Require
this command to print `sha`:

```bash
git ls-remote origin refs/heads/main | cut -f1
```

If push is rejected or the returned SHA differs, stop. Do not create a release.
Recovery mode performs no push.

Create a new tag and release at the exact selected commit:

```bash
gh release create "v$new" \
  --repo spacedock-dev/behavior-diff \
  --target "$sha" \
  --title "Behavior Diff v$new" \
  --generate-notes
```

When recovery mode found an existing valid tag, create only the missing
release:

```bash
gh release create "v$new" \
  --repo spacedock-dev/behavior-diff \
  --verify-tag \
  --title "Behavior Diff v$new" \
  --generate-notes
```

## Watch the release workflow

Wait at most one minute for the Release workflow run to appear:

```bash
run_id=
for attempt in $(seq 1 12); do
  run_id=$(gh run list \
    --repo spacedock-dev/behavior-diff \
    --workflow Release \
    --commit "$sha" \
    --limit 1 \
    --json databaseId \
    --jq '.[0].databaseId // empty')
  [[ -n $run_id ]] && break
  sleep 5
done
if [[ -z $run_id ]]; then
  echo "Release workflow did not appear for $sha" >&2
  exit 1
fi
gh run watch "$run_id" --repo spacedock-dev/behavior-diff --exit-status
```

Inspect the final jobs:

```bash
gh run view "$run_id" \
  --repo spacedock-dev/behavior-diff \
  --json jobs,url,conclusion
```

Require overall success and successful `ci / Unit`, `ci / Format`, and
`marketplace` jobs. Then verify all final state:

1. `gh release view "v$new" --repo spacedock-dev/behavior-diff --json tagName,url,isDraft,isPrerelease`
   reports the exact tag, a URL, `isDraft: false`, and `isPrerelease: false`.
2. Fetch `v$new` and require `git rev-list -n 1 "v$new"` to equal `sha`.
3. Report old and new versions, commit SHA, release URL, Release workflow URL
   and conclusion, and marketplace job conclusion.

## Stop states

- Failure before push: do not push or release. Leave a focused local version
  diff or commit and report the failed command.
- Push rejection: never force. Fetch and report that remote `main` moved.
- Push success followed by release failure: report that the version commit is
  on `main` but its release is missing. Retry the same version in recovery
  mode; never bump again.
- Workflow failure: keep the release and tag. Report the workflow URL and the
  failed job. Never delete or recreate release state automatically.
- Never invoke an AI model as part of release verification.
