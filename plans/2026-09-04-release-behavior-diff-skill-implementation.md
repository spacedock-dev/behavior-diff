# Release Behavior Diff Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> `subagent-driven-development` (recommended) or `executing-plans` to implement
> this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a repository-local skill that safely bumps or resumes a stable
Behavior Diff release, pushes `main`, creates GitHub Release `vX.Y.Z`, and
waits for the existing Release workflow.

**Architecture:** A deterministic Python helper validates and updates the two
plugin manifests plus the active version contract. `SKILL.md` owns repository,
Git, GitHub, recovery, and reporting steps. The current Release workflow
remains the only marketplace publisher.

**Tech Stack:** Agent-skill Markdown, Python standard library, Bash, Git,
GitHub CLI, GitHub Actions.

---

## File structure

```text
.agents/skills/release-behavior-diff/
├── SKILL.md
└── scripts/
    └── bump-version.py
```

- `SKILL.md` is the repository-maintainer workflow and safety contract.
- `bump-version.py` calculates or validates one stable version and updates
  exactly three active files.
- `.github/workflows/ci.yml` compiles and runs the helper self-check.
- `CODING_GUIDELINES.md` keeps the documented local commands equal to CI.

### Task 1: Build the deterministic version updater

**Files:**
- Create: `.agents/skills/release-behavior-diff/scripts/bump-version.py`

- [ ] **Step 1: Create the updater with self-checks written before production
  behavior**

Create the file with the imports, error type, fixture builder, and `_check()`.
The self-check calls `_bump()` before that function has been implemented, so
its first run fails at the intended boundary.

```python
#!/usr/bin/env python3
import json
import re
import sys
import tempfile
from pathlib import Path
from typing import Optional, Tuple

VERSION_RE = re.compile(r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$")
MANIFESTS = (
    Path("plugin/.claude-plugin/plugin.json"),
    Path("plugin/.codex-plugin/plugin.json"),
)
CONTRACT = Path("tests/live-report-contract.sh")


class ReleaseError(ValueError):
    pass


def _fixture(root: Path, claude: str = "0.3.2", codex: str = "0.3.2") -> None:
    for relative, version in zip(MANIFESTS, (claude, codex)):
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            '{\n  "name": "behavior-diff",\n  "version": "' + version + '"\n}\n'
        )
    contract = root / CONTRACT
    contract.parent.mkdir(parents=True, exist_ok=True)
    contract.write_text(
        "[[ $(jq -r '.version' \"$claude_manifest\") == 0.3.2 ]] ||\n"
        "  fail 'Claude manifest version is not 0.3.2'\n"
        "[[ $(jq -r '.version' \"$codex_manifest\") == 0.3.2 ]] ||\n"
        "  fail 'Codex manifest version is not 0.3.2'\n"
    )


def _expect_error(root: Path, requested: Optional[str], message: str) -> None:
    before = {path: (root / path).read_text() for path in (*MANIFESTS, CONTRACT)}
    try:
        _bump(root, requested)
    except ReleaseError as error:
        assert str(error) == message
    else:
        raise AssertionError("invalid release version was accepted")
    assert {path: (root / path).read_text() for path in before} == before


def _check() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        _fixture(root)
        assert _bump(root, None) == "0.3.3"
        assert json.loads((root / MANIFESTS[0]).read_text())["version"] == "0.3.3"
        assert json.loads((root / MANIFESTS[1]).read_text())["version"] == "0.3.3"
        assert (root / CONTRACT).read_text().count("0.3.3") == 4

    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        _fixture(root)
        assert _bump(root, "0.4.0") == "0.4.0"

    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        _fixture(root, codex="0.3.1")
        _expect_error(
            root,
            None,
            "plugin manifest versions differ: Claude 0.3.2, Codex 0.3.1",
        )

    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        _fixture(root, claude="01.2.3")
        _expect_error(
            root,
            None,
            "manifest version must use stable X.Y.Z: 01.2.3",
        )

    for requested, message in (
        ("v0.3.3", "version must use stable X.Y.Z: v0.3.3"),
        ("0.3.2", "new version must be greater than 0.3.2: 0.3.2"),
        ("0.3.1", "new version must be greater than 0.3.2: 0.3.1"),
    ):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _fixture(root)
            _expect_error(root, requested, message)

    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        _fixture(root)
        contract = root / CONTRACT
        contract.write_text(contract.read_text().replace("0.3.2", "0.3.1", 1))
        _expect_error(
            root,
            None,
            "active version contract does not match 0.3.2",
        )

    print("bump-version.py self-check ok")
```

End the file temporarily with:

```python
if __name__ == "__main__":
    _check()
```

- [ ] **Step 2: Run the self-check and verify RED**

Run:

```bash
python3 .agents/skills/release-behavior-diff/scripts/bump-version.py
```

Expected: fail because `_bump` is not defined.

- [ ] **Step 3: Implement stable-version parsing and exact file updates**

Add these functions above `_fixture`:

```python
def _version(value: object, field: str) -> Tuple[int, int, int]:
    if type(value) is not str or VERSION_RE.fullmatch(value) is None:
        raise ReleaseError("{0} must use stable X.Y.Z: {1}".format(field, value))
    return tuple(int(part) for part in value.split("."))


def _manifest(path: Path) -> Tuple[str, str]:
    try:
        text = path.read_text()
        data = json.loads(text)
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise ReleaseError("invalid plugin manifest {0}: {1}".format(path, error))
    version = data.get("version") if type(data) is dict else None
    _version(version, "manifest version")
    return version, text


def _contract_lines(version: str) -> Tuple[str, ...]:
    return (
        "[[ $(jq -r '.version' \"$claude_manifest\") == {0} ]] ||".format(version),
        "  fail 'Claude manifest version is not {0}'".format(version),
        "[[ $(jq -r '.version' \"$codex_manifest\") == {0} ]] ||".format(version),
        "  fail 'Codex manifest version is not {0}'".format(version),
    )


def _replace_once(text: str, old: str, new: str, field: str) -> str:
    if text.count(old) != 1:
        raise ReleaseError("{0} does not match {1}".format(field, old))
    return text.replace(old, new)


def _bump(root: Path, requested: Optional[str]) -> str:
    claude, claude_text = _manifest(root / MANIFESTS[0])
    codex, codex_text = _manifest(root / MANIFESTS[1])
    if claude != codex:
        raise ReleaseError(
            "plugin manifest versions differ: Claude {0}, Codex {1}".format(
                claude, codex
            )
        )

    current = _version(claude, "manifest version")
    if requested is None:
        target = (current[0], current[1], current[2] + 1)
        new_version = ".".join(str(part) for part in target)
    else:
        target = _version(requested, "version")
        if target <= current:
            raise ReleaseError(
                "new version must be greater than {0}: {1}".format(claude, requested)
            )
        new_version = requested

    old_manifest_token = '"version": "{0}"'.format(claude)
    new_manifest_token = '"version": "{0}"'.format(new_version)
    new_claude = _replace_once(
        claude_text, old_manifest_token, new_manifest_token, str(MANIFESTS[0])
    )
    new_codex = _replace_once(
        codex_text, old_manifest_token, new_manifest_token, str(MANIFESTS[1])
    )

    contract_path = root / CONTRACT
    contract_text = contract_path.read_text()
    new_contract = contract_text
    for old, new in zip(_contract_lines(claude), _contract_lines(new_version)):
        if new_contract.count(old) != 1:
            raise ReleaseError(
                "active version contract does not match {0}".format(claude)
            )
        new_contract = new_contract.replace(old, new)

    updates = (
        (root / MANIFESTS[0], new_claude),
        (root / MANIFESTS[1], new_codex),
        (contract_path, new_contract),
    )
    for path, text in updates:
        path.write_text(text)

    updated_claude, _ = _manifest(root / MANIFESTS[0])
    updated_codex, _ = _manifest(root / MANIFESTS[1])
    if updated_claude != new_version or updated_codex != new_version:
        raise ReleaseError("updated plugin manifest versions do not match")
    return new_version
```

Replace the temporary entry point with:

```python
def main(argv=None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if args == ["--check"]:
        _check()
        return 0
    if len(args) > 1:
        print("Usage: bump-version.py [X.Y.Z]", file=sys.stderr)
        return 2
    try:
        print(_bump(Path.cwd(), args[0] if args else None))
    except (OSError, UnicodeError, ReleaseError) as error:
        print("release version error: {0}".format(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run the self-check and verify GREEN**

Run:

```bash
python3 .agents/skills/release-behavior-diff/scripts/bump-version.py --check
```

Expected:

```text
bump-version.py self-check ok
```

- [ ] **Step 5: Verify the helper does not change the real repository during
  self-check**

Run:

```bash
git diff --exit-code -- \
  plugin/.claude-plugin/plugin.json \
  plugin/.codex-plugin/plugin.json \
  tests/live-report-contract.sh
```

Expected: exit `0` with no output.

- [ ] **Step 6: Commit the updater**

```bash
git add .agents/skills/release-behavior-diff/scripts/bump-version.py
git commit --signoff -m "feat: add deterministic release version updater"
```

### Task 2: Wire updater checks into deterministic CI

**Files:**
- Modify: `.github/workflows/ci.yml:77-94`
- Modify: `CODING_GUIDELINES.md:155-163`

- [ ] **Step 1: Add the helper to Python syntax checks**

Add this path before the existing plugin Python paths in both files:

```text
.agents/skills/release-behavior-diff/scripts/bump-version.py
```

The CI block becomes:

```yaml
      - name: Check Python syntax
        run: |
          python3 -m py_compile \
            .agents/skills/release-behavior-diff/scripts/bump-version.py \
            plugin/skills/behavior-diff/scripts/decisions.py \
            plugin/skills/behavior-diff/scripts/render.py \
            plugin/skills/behavior-diff/scripts/reporting/*.py
```

- [ ] **Step 2: Add the deterministic self-check**

After the release workflow check in `.github/workflows/ci.yml`, add:

```yaml
      - name: Run release skill unit check
        run: >-
          python3
          .agents/skills/release-behavior-diff/scripts/bump-version.py
          --check
```

After `bash tests/release-workflow-test.sh` in `CODING_GUIDELINES.md`, add:

```bash
python3 .agents/skills/release-behavior-diff/scripts/bump-version.py --check
```

- [ ] **Step 3: Run syntax and self-checks**

```bash
python3 -m py_compile \
  .agents/skills/release-behavior-diff/scripts/bump-version.py \
  plugin/skills/behavior-diff/scripts/decisions.py \
  plugin/skills/behavior-diff/scripts/render.py \
  plugin/skills/behavior-diff/scripts/reporting/*.py
python3 .agents/skills/release-behavior-diff/scripts/bump-version.py --check
```

Expected: both exit `0`; the self-check prints its one success line.

- [ ] **Step 4: Commit CI coverage**

```bash
git add .github/workflows/ci.yml CODING_GUIDELINES.md
git commit --signoff -m "test: check release skill version updates"
```

### Task 3: Write the local release skill

**Files:**
- Create: `.agents/skills/release-behavior-diff/SKILL.md`

- [ ] **Step 1: Write minimal frontmatter and purpose**

Start with:

```markdown
---
name: release-behavior-diff
description: Release a stable Behavior Diff version from main. Use whenever a maintainer asks to release or publish Behavior Diff, bump its patch version, create a Behavior Diff vX.Y.Z GitHub Release, or recover a pushed version whose release is missing.
---

# Release Behavior Diff

Release one stable version without letting the Claude Code and Codex plugin
manifests drift. This workflow intentionally commits and pushes `main`
directly; never open a pull request for the version bump.
```

- [ ] **Step 2: Add the preflight and state decision**

State these rules directly:

```markdown
## Preflight

Complete every check before changing a file.

1. Confirm the repository is `spacedock-dev/behavior-diff`, the branch is
   `main`, and `git status --short` is empty. Stop rather than stash, reset,
   switch branches, or repair unrelated state.
2. Require `git` and `gh`; run `gh auth status` before edits.
3. Run `git fetch origin main` and require local `HEAD` to equal
   `origin/main`. If local main is only behind, run
   `git pull --ff-only origin main`; otherwise stop.
4. Read both plugin manifests. Require equal stable `X.Y.Z` versions.
5. Check `gh release view "v$current" --repo spacedock-dev/behavior-diff`.


Treat only an explicit "release not found" result as missing. Any authentication,
network, API, or other `gh` failure stops the release.
If the current release exists, start a new release. Use the explicit stable
version from the request, or omit the helper argument for the next patch.
The explicit version must be higher than current.

If the current release is missing, enter recovery mode. Release the current
version without editing, committing, or incrementing again. Reject an
explicit different version until recovery completes.
```

- [ ] **Step 3: Add normal bump and verification steps**

````markdown
## New version

Before mutation, capture
`git ls-remote --tags origin "refs/tags/v$new"`. An empty successful result
means no tag; any command error or non-empty result stops. Require
`gh release view "v$new" --repo spacedock-dev/behavior-diff` to return an
explicit "release not found"; any other result stops.

Run one matching deterministic updater command from the repository root:

```bash
# Default next-patch release:
new=$(python3 .agents/skills/release-behavior-diff/scripts/bump-version.py)

# Explicit higher stable version:
new=$(python3 .agents/skills/release-behavior-diff/scripts/bump-version.py "$requested")
```

Capture its one-line stdout as `new`. Never pass `vX.Y.Z`.

Run every check before commit:

```bash
VERSION="$new" python3 -c \
  'import json, os; from pathlib import Path; a=json.loads(Path("plugin/.claude-plugin/plugin.json").read_text()); b=json.loads(Path("plugin/.codex-plugin/plugin.json").read_text()); assert a == b; assert a["version"] == os.environ["VERSION"]'
docker run --rm -v "$PWD:/mnt" -w /mnt \
  mvdan/shfmt:v3.14.0 -d -i 2 -ci .
bash tests/hooks-test.sh
python3 plugin/skills/behavior-diff/scripts/decisions.py --check
bash tests/live-report-contract.sh
bash tests/release-workflow-test.sh
python3 .agents/skills/release-behavior-diff/scripts/bump-version.py --check
git diff --check
```

Confirm `git status --short` names only both plugin manifests and
`tests/live-report-contract.sh`. Commit with DCO sign-off:

```bash
git add plugin/.claude-plugin/plugin.json \
  plugin/.codex-plugin/plugin.json tests/live-report-contract.sh
git commit --signoff -m "chore: bump plugin version to $new"
```
````

- [ ] **Step 4: Add push, release, and recovery commands**

````markdown
## Push and publish

Capture `sha=$(git rev-parse HEAD)`. Push with `git push origin main`; never
force-push. Require `git ls-remote origin refs/heads/main` to return `sha`.

For a new tag, run:

```bash
gh release create "v$new" \
  --repo spacedock-dev/behavior-diff \
  --target "$sha" \
  --title "Behavior Diff v$new" \
  --generate-notes
```

In recovery mode, set `new` to the current manifest version and use remote
`main` as `sha`. If `v$new` does not exist, use the command above. If the tag
exists without a release, fetch it, set `tag_sha` to
`git rev-list -n 1 "v$new"`, require `tag_sha` to be an ancestor of
`origin/main`, require both manifests at the tag to equal `new`, set
`sha=$tag_sha`, then run:

```bash
gh release create "v$new" \
  --repo spacedock-dev/behavior-diff \
  --verify-tag \
  --title "Behavior Diff v$new" \
  --generate-notes
```
````

- [ ] **Step 5: Add workflow watch and failure states**

Use this bounded wait for the Release run:

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

Inspect
`gh run view "$run_id" --json jobs,url,conclusion`. Require overall success,
`ci / Unit`, `ci / Format`, and `marketplace` job success. Verify the release
with `gh release view "v$new" --json tagName,url,isDraft,isPrerelease` and
verify the fetched tag resolves to the selected SHA.

Add explicit stop states:

```text
before push failure -> no commit/push/release beyond completed local work
push rejection -> never force; report that main moved
push success + release failure -> retry the same version; never bump again
workflow failure -> keep release/tag; report workflow URL; never delete them
```

The final success message reports old/new version, commit SHA, release URL,
Release workflow conclusion, and marketplace job conclusion.

- [ ] **Step 6: Read the complete skill for command and state consistency**

Check that:

- no path points into `plugin/skills/`;
- no command uses `--force` or deletes a tag/release;
- normal and recovery paths cannot both run;
- no failure after push can return to the bump step;
- `v` appears only in Git tag/release values, never manifest values;
- every state-changing GitHub command names the repository;
- the skill never claims success before checking the Release workflow.

- [ ] **Step 7: Commit the skill**

```bash
git add .agents/skills/release-behavior-diff/SKILL.md
git commit --signoff -m "feat: add Behavior Diff release skill"
```

### Task 4: Verify and review the complete skill

**Files:**
- Verify only; fix only validated findings.

- [ ] **Step 1: Run repository formatting and syntax checks**

```bash
docker run --rm -v "$PWD:/mnt" -w /mnt \
  mvdan/shfmt:v3.14.0 -d -i 2 -ci .
uvx ruff@0.16.5 format --check --diff .
bash -n \
  .github/scripts/*.sh \
  bin/behavior-diff \
  plugin/scripts/*.sh \
  plugin/skills/behavior-diff/scripts/*.sh \
  tests/*.sh
python3 -m py_compile \
  .agents/skills/release-behavior-diff/scripts/bump-version.py \
  plugin/skills/behavior-diff/scripts/decisions.py \
  plugin/skills/behavior-diff/scripts/render.py \
  plugin/skills/behavior-diff/scripts/reporting/*.py
```

Expected: all commands exit `0` with no diff or diagnostics.

- [ ] **Step 2: Run the full deterministic suite**

```bash
bash tests/hooks-test.sh
python3 plugin/skills/behavior-diff/scripts/decisions.py --check
bash tests/live-report-contract.sh
bash tests/release-workflow-test.sh
python3 .agents/skills/release-behavior-diff/scripts/bump-version.py --check
git diff --check
```

Expected: all checks exit `0`. No command invokes an AI model or GitHub
release mutation.

- [ ] **Step 3: Confirm scope and safety**

Verify the full diff changes only:

```text
.agents/skills/release-behavior-diff/SKILL.md
.agents/skills/release-behavior-diff/scripts/bump-version.py
.github/workflows/ci.yml
CODING_GUIDELINES.md
plans/2026-09-04-release-behavior-diff-skill-design.md
plans/2026-09-04-release-behavior-diff-skill-implementation.md
```

Confirm both real plugin manifests remain at the current released version.
The helper self-check must leave the working tree unchanged.

- [ ] **Step 4: Run required skill quality review**

Give `.agents/skills/release-behavior-diff/SKILL.md`, its helper, the design,
and this plan to the read-only `skill-reviewer`. Require it to check trigger
clarity, normal/recovery state separation, exact command safety, failure
re-entry, direct-main intent, DCO, non-force push, exact-SHA tag creation,
workflow monitoring, and final evidence.

Do not run live skill evals: their realistic behavior would push `main` and
publish a GitHub Release. The deterministic helper self-check plus read-only
skill review is the safe verification method.

- [ ] **Step 5: Fix validated findings and re-run checks**

Use the same reviewer after any fix. Do not weaken a stop condition to satisfy
a style preference.

- [ ] **Step 6: Commit review fixes if needed**

```bash
git add .agents/skills/release-behavior-diff/SKILL.md \
  .agents/skills/release-behavior-diff/scripts/bump-version.py \
  .github/workflows/ci.yml CODING_GUIDELINES.md
git commit --signoff -m "fix: harden Behavior Diff release skill"
```

If no file changes are needed, create no empty commit.

- [ ] **Step 7: Present branch completion options**

The user selected direct `main` work. Report the commits and checks, then ask
before pushing the skill commits to `origin/main`. Creating this skill must
not invoke it or publish another release.
