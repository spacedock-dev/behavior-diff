# Behavior Diff Plugin Release Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> superpowers:subagent-driven-development (recommended) or
> superpowers:executing-plans to implement this plan task-by-task. Steps use
> checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publish stable Behavior Diff versions through GitHub Releases and automatically pin the Spacedock marketplace entry to each released tag.

**Architecture:** A `release.published` workflow reuses the existing deterministic CI, validates the stable release tag and both plugin manifests, then updates marketplace through a dedicated SSH deploy key. A small shell command owns the JSON update so deterministic tests can exercise the release behavior outside GitHub Actions.

**Tech Stack:** GitHub Actions, Bash 3.2, `jq`, Git, GitHub Releases, SSH deploy keys, existing `shfmt` 3.14.0 and Ruff 0.16.5 checks.

---

## Scope and constraints

- Stable GitHub Releases only. Drafts and prereleases never update marketplace.
- Release tags use strict `vX.Y.Z` form and point to a commit on `main`.
- Both plugin manifests must equal `X.Y.Z`.
- Marketplace updates both `version` and `source.ref` in one change.
- Use a dedicated write-enabled deploy key, not a personal access token.
- Never force push, move a published tag, print a private key, or invoke a model in CI.
- Keep Claude Code and Codex plugin versions equal.
- Correct the two approved stale README sections in the same branch.
- Use signed commits for every repository commit.

## Files

- Create: `.github/scripts/update-marketplace.sh`
- Create: `.github/workflows/release.yml`
- Create: `tests/release-workflow-test.sh`
- Modify: `.github/workflows/ci.yml`
- Modify: `AGENTS.md`
- Modify: `CODING_GUIDELINES.md`
- Modify: `README.md`
- Existing design: `plans/2026-09-02-plugin-release-design.md`

---

### Task 1: Add and implement the marketplace updater

**Files:**

- Create: `tests/release-workflow-test.sh`
- Create: `.github/scripts/update-marketplace.sh`

- [ ] **Step 1: Create the failing updater contract**

Create `tests/release-workflow-test.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

here=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
updater=$here/../.github/scripts/update-marketplace.sh
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

fail() {
  printf 'FAIL: %s\n' "$1" >&2
  exit 1
}

make_index() {
  cat >"$1" <<'JSON'
{
  "name": "spacedock",
  "plugins": [
    {
      "name": "other-plugin",
      "source": {"ref": "stable"},
      "version": "1.0.0"
    },
    {
      "name": "behavior-diff",
      "source": {
        "source": "git-subdir",
        "url": "https://github.com/spacedock-dev/behavior-diff.git",
        "path": "plugin",
        "ref": "main"
      },
      "version": "0.3.1"
    }
  ]
}
JSON
}

printf '[release] Update one marketplace entry\n'
index=$tmp/marketplace.json
make_index "$index"
"$updater" "$index" 0.3.2
jq -e '
  [.plugins[] |
    select(.name == "behavior-diff" and
           .version == "0.3.2" and
           .source.ref == "v0.3.2")] |
  length == 1
' "$index" >/dev/null || fail 'Behavior Diff entry was not updated'
jq -e '
  [.plugins[] |
    select(.name == "other-plugin" and
           .version == "1.0.0" and
           .source.ref == "stable")] |
  length == 1
' "$index" >/dev/null || fail 'unrelated entry changed'

printf '[release] Keep repeated updates unchanged\n'
cp "$index" "$tmp/expected.json"
"$updater" "$index" 0.3.2
cmp -s "$tmp/expected.json" "$index" || fail 'second update changed the index'

printf '[release] Reject invalid versions and entry counts\n'
make_index "$tmp/invalid-version.json"
if "$updater" "$tmp/invalid-version.json" v0.3.2 >/dev/null 2>&1; then
  fail 'updater accepted a version with v prefix'
fi

make_index "$tmp/missing.json"
jq '.plugins |= map(select(.name != "behavior-diff"))' \
  "$tmp/missing.json" >"$tmp/missing.tmp"
mv "$tmp/missing.tmp" "$tmp/missing.json"
if "$updater" "$tmp/missing.json" 0.3.2 >/dev/null 2>&1; then
  fail 'updater accepted a missing Behavior Diff entry'
fi

make_index "$tmp/duplicate.json"
jq '.plugins += [.plugins[] | select(.name == "behavior-diff")]' \
  "$tmp/duplicate.json" >"$tmp/duplicate.tmp"
mv "$tmp/duplicate.tmp" "$tmp/duplicate.json"
if "$updater" "$tmp/duplicate.json" 0.3.2 >/dev/null 2>&1; then
  fail 'updater accepted duplicate Behavior Diff entries'
fi

printf 'ok — release workflow contract passed\n'
```

- [ ] **Step 2: Run the test and verify the red state**

Run:

```bash
bash tests/release-workflow-test.sh
```

Expected: failure because `.github/scripts/update-marketplace.sh` does not exist.

- [ ] **Step 3: Implement the marketplace updater**

Create `.github/scripts/update-marketplace.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

usage() {
  printf 'usage: %s <marketplace.json> <X.Y.Z>\n' "${0##*/}" >&2
  exit 2
}

[[ $# -eq 2 ]] || usage
index=$1
version=$2

if [[ ! -f $index ]]; then
  printf 'marketplace index not found: %s\n' "$index" >&2
  exit 1
fi

if ! [[ $version =~ ^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$ ]]; then
  printf 'release version must use X.Y.Z: %s\n' "$version" >&2
  exit 1
fi

count=$(jq '[.plugins[] | select(.name == "behavior-diff")] | length' "$index")
if [[ $count -ne 1 ]]; then
  printf 'expected one behavior-diff marketplace entry, found %s\n' "$count" >&2
  exit 1
fi

tmp=${index}.tmp
trap 'rm -f "$tmp"' EXIT
jq --arg version "$version" '
  (.plugins[] | select(.name == "behavior-diff") | .version) = $version |
  (.plugins[] | select(.name == "behavior-diff") | .source.ref) = ("v" + $version)
' "$index" >"$tmp"

jq -e --arg version "$version" '
  [.plugins[] |
    select(.name == "behavior-diff" and
           .version == $version and
           .source.ref == ("v" + $version))] |
  length == 1
' "$tmp" >/dev/null

mv "$tmp" "$index"
trap - EXIT
```

- [ ] **Step 4: Format and run the focused contract**

Run:

```bash
docker run --rm -u "$(id -u):$(id -g)" \
  -v "$PWD:/mnt" -w /mnt \
  mvdan/shfmt:v3.14.0 -w -i 2 -ci \
  .github/scripts/update-marketplace.sh tests/release-workflow-test.sh
bash tests/release-workflow-test.sh
```

Expected: `ok — release workflow contract passed`.

- [ ] **Step 5: Commit the updater slice**

Run:

```bash
git add .github/scripts/update-marketplace.sh tests/release-workflow-test.sh
git commit --signoff -m "feat: add marketplace release updater"
```

---

### Task 2: Add the stable GitHub Release workflow

**Files:**

- Modify: `tests/release-workflow-test.sh`
- Create: `.github/workflows/release.yml`
- Modify: `.github/workflows/ci.yml`
- Modify: `AGENTS.md`
- Modify: `CODING_GUIDELINES.md`

- [ ] **Step 1: Extend the contract with workflow invariants**

Insert these helpers after `fail()` in `tests/release-workflow-test.sh`:

```bash
require_literal() {
  local literal=$1
  local file=$2
  local message=$3
  grep -Fq -- "$literal" "$file" || fail "$message"
}
```

Insert these paths after `updater=...`:

```bash
release_workflow=$here/../.github/workflows/release.yml
ci_workflow=$here/../.github/workflows/ci.yml
```

Insert this block before the final success line:

```bash
printf '[release] Keep GitHub Release and security invariants\n'
require_literal 'workflow_call:' "$ci_workflow" \
  'CI is not reusable from the release workflow'
require_literal 'types: [published]' "$release_workflow" \
  'release workflow does not use the published event'
require_literal 'if: ${{ !github.event.release.prerelease }}' \
  "$release_workflow" 'release workflow does not skip prereleases'
require_literal 'uses: ./.github/workflows/ci.yml' "$release_workflow" \
  'release workflow does not reuse deterministic CI'
require_literal 'needs: ci' "$release_workflow" \
  'marketplace update is not gated by CI'
require_literal 'plugin/.claude-plugin/plugin.json' "$release_workflow" \
  'release workflow does not validate the Claude manifest'
require_literal 'plugin/.codex-plugin/plugin.json' "$release_workflow" \
  'release workflow does not validate the Codex manifest'
require_literal 'git merge-base --is-ancestor HEAD origin/main' \
  "$release_workflow" 'release workflow does not require a main commit'
require_literal 'MARKETPLACE_DEPLOY_KEY: ${{ secrets.MARKETPLACE_DEPLOY_KEY }}' \
  "$release_workflow" 'release workflow does not use the deploy-key secret'
require_literal 'update-marketplace.sh "$INDEX" "$VERSION"' \
  "$release_workflow" 'release workflow does not call the tested updater'
```

- [ ] **Step 2: Run the contract and verify the red state**

Run:

```bash
bash tests/release-workflow-test.sh
```

Expected: failure because `.github/workflows/release.yml` does not exist and CI has no `workflow_call` trigger.

- [ ] **Step 3: Make the existing CI reusable and include the new test**

Update `.github/workflows/ci.yml`:

```yaml
on:
  workflow_call:
  pull_request:
  push:
    branches:
      - main
```

Add `.github/scripts/*.sh` to the existing `bash -n` command:

```yaml
      - name: Check shell syntax
        run: |
          bash -n \
            .github/scripts/*.sh \
            bin/behavior-diff \
            plugin/scripts/*.sh \
            plugin/skills/behavior-diff/scripts/*.sh \
            tests/*.sh
```

Add this Unit step after the live-report contract:

```yaml
      - name: Run release workflow checks
        run: bash tests/release-workflow-test.sh
```

Add the new command to the full deterministic suite in both `AGENTS.md` and
`CODING_GUIDELINES.md`:

```bash
bash tests/release-workflow-test.sh
```

- [ ] **Step 4: Create the release workflow**

Create `.github/workflows/release.yml`:

```yaml
name: Release

on:
  release:
    types: [published]

permissions:
  contents: read

jobs:
  ci:
    if: ${{ !github.event.release.prerelease }}
    uses: ./.github/workflows/ci.yml

  marketplace:
    if: ${{ !github.event.release.prerelease }}
    needs: ci
    runs-on: ubuntu-latest
    timeout-minutes: 10
    steps:
      - name: Check out released tag
        uses: actions/checkout@v5
        with:
          ref: ${{ github.event.release.tag_name }}
          fetch-depth: 0

      - name: Validate release
        env:
          RELEASE_TAG: ${{ github.event.release.tag_name }}
        run: |
          set -euo pipefail
          if ! [[ $RELEASE_TAG =~ ^v(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$ ]]; then
            printf 'stable release tag must use vX.Y.Z: %s\n' "$RELEASE_TAG" >&2
            exit 1
          fi

          VERSION=${RELEASE_TAG#v}
          CLAUDE_VERSION=$(jq -r '.version' plugin/.claude-plugin/plugin.json)
          CODEX_VERSION=$(jq -r '.version' plugin/.codex-plugin/plugin.json)
          if [[ $CLAUDE_VERSION != "$VERSION" || $CODEX_VERSION != "$VERSION" ]]; then
            printf 'release %s does not match plugin manifests (%s, %s)\n' \
              "$VERSION" "$CLAUDE_VERSION" "$CODEX_VERSION" >&2
            exit 1
          fi

          git fetch origin \
            '+refs/heads/main:refs/remotes/origin/main'
          if ! git merge-base --is-ancestor HEAD origin/main; then
            printf 'released commit is not on main: %s\n' "$RELEASE_TAG" >&2
            exit 1
          fi

          printf 'VERSION=%s\n' "$VERSION" >>"$GITHUB_ENV"

      - name: Publish marketplace entry
        env:
          MARKETPLACE_DEPLOY_KEY: ${{ secrets.MARKETPLACE_DEPLOY_KEY }}
        run: |
          set -euo pipefail
          test -n "$MARKETPLACE_DEPLOY_KEY"

          MARKETPLACE=$RUNNER_TEMP/marketplace
          SSH_DIR=$RUNNER_TEMP/marketplace-ssh
          install -d -m 700 "$SSH_DIR"
          trap 'rm -rf "$SSH_DIR"' EXIT
          printf '%s\n' "$MARKETPLACE_DEPLOY_KEY" >"$SSH_DIR/key"
          chmod 600 "$SSH_DIR/key"
          curl --fail --silent --show-error https://api.github.com/meta |
            jq -r '.ssh_keys[] | "github.com " + .' >"$SSH_DIR/known_hosts"
          test -s "$SSH_DIR/known_hosts"
          export GIT_SSH_COMMAND="ssh -i $SSH_DIR/key -o IdentitiesOnly=yes -o IdentityAgent=none -o StrictHostKeyChecking=yes -o UserKnownHostsFile=$SSH_DIR/known_hosts"

          git clone --depth 1 git@github.com:spacedock-dev/marketplace.git "$MARKETPLACE"
          INDEX=$MARKETPLACE/.claude-plugin/marketplace.json
          "$GITHUB_WORKSPACE/.github/scripts/update-marketplace.sh" "$INDEX" "$VERSION"
          git -C "$MARKETPLACE" diff --check
          if git -C "$MARKETPLACE" diff --quiet -- .claude-plugin/marketplace.json; then
            printf 'marketplace already publishes Behavior Diff %s\n' "$VERSION"
            exit 0
          fi

          git -C "$MARKETPLACE" add -- .claude-plugin/marketplace.json
          git -C "$MARKETPLACE" \
            -c user.name=github-actions \
            -c user.email=actions@github.com \
            commit --signoff -m "behavior-diff $VERSION"
          git -C "$MARKETPLACE" push origin HEAD:main
```

- [ ] **Step 5: Run the focused workflow contract**

Run:

```bash
bash tests/release-workflow-test.sh
```

Expected: `ok — release workflow contract passed`.

- [ ] **Step 6: Validate workflow syntax**

Run:

```bash
docker run --rm -v "$PWD:/repo" -w /repo \
  rhysd/actionlint:1.7.7
```

Expected: no output and exit status 0.

- [ ] **Step 7: Commit the workflow slice**

Run:

```bash
git add .github/workflows/ci.yml .github/workflows/release.yml \
  AGENTS.md CODING_GUIDELINES.md tests/release-workflow-test.sh
git commit --signoff -m "ci: publish releases to marketplace"
```

---

### Task 3: Update operator and product documentation

**Files:**

- Modify: `README.md:43-105`

- [ ] **Step 1: Correct the public usage text**

Remove this sentence from the Install section:

```text
The marketplace entry is not live yet.
```

Replace the outdated paragraph and run-count section at current lines 100-105 with:

```markdown
Behavior Diff finds the changed instruction file and uses your request as the
comparison task. Once the task is known, it runs the comparison and opens the
report.
```

This text must not mention run modes, trial counts, confirmation, or model cost.

- [ ] **Step 2: Add the release operator process**

Append this section before the contributor guidance at the end of `README.md`:

```markdown
## Release

1. Update both plugin manifests to the same `X.Y.Z` version.
2. Merge the version change to `main` and wait for CI.
3. Create a GitHub Release with tag `vX.Y.Z`, targeting `main`.
4. Publish it as a stable release, not a prerelease.
5. Confirm the Release workflow pins the marketplace entry to `vX.Y.Z`.

The release workflow rejects tags that do not match both plugin manifests or
do not point to a commit on `main`. Drafts and prereleases do not update the
stable marketplace.
```

- [ ] **Step 3: Check Markdown and stale wording**

Run:

```bash
git diff --check
grep -nE 'not live yet|model cost|Fast mode|six fresh agent trials|starts only after' README.md
```

Expected: `git diff --check` exits 0. `grep` prints no matches and exits 1.

- [ ] **Step 4: Commit the documentation slice**

Run:

```bash
git add README.md
git commit --signoff -m "docs: document plugin releases"
```

---

### Task 4: Run full deterministic verification and review

**Files:**

- Verify all changed files.

- [ ] **Step 1: Format the new shell files**

Run:

```bash
docker run --rm -u "$(id -u):$(id -g)" \
  -v "$PWD:/mnt" -w /mnt \
  mvdan/shfmt:v3.14.0 -w -i 2 -ci \
  .github/scripts/update-marketplace.sh tests/release-workflow-test.sh
```

Expected: formatter exits 0.

- [ ] **Step 2: Run formatting checks**

Run:

```bash
docker run --rm -v "$PWD:/mnt" -w /mnt \
  mvdan/shfmt:v3.14.0 -d -i 2 -ci .
uvx ruff@0.16.5 format --check --diff .
```

Expected: no shfmt diff and Ruff reports all Python files formatted.

- [ ] **Step 3: Run syntax and workflow checks**

Run:

```bash
bash -n \
  .github/scripts/*.sh \
  bin/behavior-diff \
  plugin/scripts/*.sh \
  plugin/skills/behavior-diff/scripts/*.sh \
  tests/*.sh
python3 -m py_compile \
  plugin/skills/behavior-diff/scripts/decisions.py \
  plugin/skills/behavior-diff/scripts/render.py
docker run --rm -v "$PWD:/repo" -w /repo \
  rhysd/actionlint:1.7.7
```

Expected: all commands exit 0 with no actionlint findings.

- [ ] **Step 4: Run the full deterministic suite**

Run:

```bash
bash tests/hooks-test.sh
python3 plugin/skills/behavior-diff/scripts/decisions.py --check
bash tests/live-report-contract.sh
bash tests/release-workflow-test.sh
claude plugin validate plugin
git diff --check
```

Expected: all four deterministic checks and plugin validation pass.

- [ ] **Step 5: Remove verification bytecode**

Run:

```bash
rm -rf plugin/skills/behavior-diff/scripts/__pycache__
```

Expected: no generated Python bytecode remains.

- [ ] **Step 6: Complete independent read-only review**

Give the reviewer the approved design, current branch diff, `AGENTS.md`, and `REVIEWER_GUIDELINES.md`. Require a GO or evidence-backed findings. Fix every valid finding and rerun the affected checks before proceeding.

---

### Task 5: Provision the dedicated marketplace deploy key

**External state:**

- Add one deploy key to `spacedock-dev/marketplace`.
- Add one Actions secret to `spacedock-dev/behavior-diff`.

- [ ] **Step 1: Confirm no key with the release title exists**

Run:

```bash
gh api repos/spacedock-dev/marketplace/keys \
  --jq '.[] | select(.title == "behavior-diff-release") | .id'
gh secret list --repo spacedock-dev/behavior-diff
```

Expected: no `behavior-diff-release` deploy key and no `MARKETPLACE_DEPLOY_KEY` secret. If either exists, stop and inspect it rather than replacing it silently.

- [ ] **Step 2: Generate, register, and remove the key pair atomically**

Run the following as one shell command so the trap always removes the local key
material:

```bash
set -euo pipefail
KEY_DIR=$(mktemp -d)
trap 'rm -rf "$KEY_DIR"' EXIT
chmod 700 "$KEY_DIR"
ssh-keygen -q -t ed25519 -N '' \
  -C 'behavior-diff marketplace release' \
  -f "$KEY_DIR/id_ed25519"
gh api --method POST repos/spacedock-dev/marketplace/keys \
  -f title='behavior-diff-release' \
  -F key=@"$KEY_DIR/id_ed25519.pub" \
  -F read_only=false
gh secret set MARKETPLACE_DEPLOY_KEY \
  --repo spacedock-dev/behavior-diff \
  <"$KEY_DIR/id_ed25519"
```

Expected: GitHub creates a write-enabled marketplace deploy key and updates the
Behavior Diff Actions secret. The exit trap removes both local key files
whether the command succeeds or fails. Do not print either file.

- [ ] **Step 3: Verify names and permissions only**

Run:

```bash
gh api repos/spacedock-dev/marketplace/keys \
  --jq '.[] | select(.title == "behavior-diff-release") | {title,read_only}'
gh secret list --repo spacedock-dev/behavior-diff
```

Expected: the deploy key is listed with `read_only: false` and the secret name
is listed. No local key material remains.

---

### Task 6: Prepare branch delivery

**Files:**

- Review all branch commits and changed files.

- [ ] **Step 1: Confirm branch and commit state**

Run:

```bash
git status --short --branch
git log --format='%h %s%n%b' origin/main..HEAD
```

Expected: the worktree is clean and every commit contains a `Signed-off-by` line.

- [ ] **Step 2: Present integration options**

Present the normal choices: merge locally, push and create a pull request, keep the branch, or discard it. Do not push or merge without the user's choice.

- [ ] **Step 3: After merge, publish the first release only on request**

The first release should be `v0.3.2` and target the release-process commit on `main`. Publishing it is a separate external action. Do not create the GitHub Release unless the user explicitly asks.
