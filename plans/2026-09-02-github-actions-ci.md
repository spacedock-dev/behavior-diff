# GitHub Actions CI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> superpowers:subagent-driven-development (recommended) or
> superpowers:executing-plans to implement this plan task-by-task. Steps use
> checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add deterministic GitHub Actions checks for Bash and Python formatting
and the existing unit contracts, without any LLM execution.

**Architecture:** Add one workflow with independent `format` and `unit` jobs.
The format job runs pinned `shfmt` and Ruff versions. The unit job puts failing
`claude` and `codex` stubs first on `PATH`, then runs only syntax checks and the
three existing deterministic contracts.

**Tech Stack:** GitHub Actions, Ubuntu, Bash 3.2-compatible scripts, Python 3,
`shfmt` 3.14.0, Ruff 0.16.5.

---

## Scope and constraints

- Create only `.github/workflows/ci.yml` for CI.
- Run CI for pull requests and pushes to `main`.
- Give the workflow read-only repository permission.
- Do not inject repository secrets or API keys.
- Never run `behavior-diff.sh`, `run-trial.sh`, `tests/nudge-e2e.sh`, or a live
  journey under `e2e/` in CI.
- Never let CI invoke a real `claude` or `codex` executable.
- Keep Bash and Python formatting in the same `format` job, but in separate
  steps with separate failure output.
- Keep deterministic contracts in the `unit` job.
- Use `git commit --signoff` for every implementation commit.

## Files

- Create: `.github/workflows/ci.yml`
- Modify: `.gitignore`
- Modify: `AGENTS.md`
- Modify: `CODING_GUIDELINES.md`
- Format mechanically:
  - `bin/behavior-diff`
  - `plugin/scripts/*.sh`
  - `plugin/skills/behavior-diff/scripts/*.sh`
  - `tests/*.sh`
  - all Python files under `plugin/`, `tests/`, and `e2e/`

---

### Task 1: Normalize the existing formatter baseline

**Files:**

- Modify mechanically: all shell files listed above
- Modify mechanically: all Python files under `plugin/`, `tests/`, and `e2e/`

- [ ] **Step 1: Make sure that the worktree contains no unrelated changes**

Run:

```bash
git status --short
```

Expected: the worktree is clean.

- [ ] **Step 2: Apply the pinned Bash formatter**

Run from the repository root:

```bash
docker run --rm \
  -u "$(id -u):$(id -g)" \
  -v "$PWD:/mnt" \
  -w /mnt \
  mvdan/shfmt:v3.14.0 \
  -w -i 2 -ci .
```

Expected: `shfmt` rewrites shell files in place. It must not change Markdown,
JSON, or Python files.

- [ ] **Step 3: Apply the pinned Python formatter**

Run:

```bash
uvx ruff@0.16.5 format .
```

Expected: Ruff formats every Python file and exits 0. The exact changed-file
count depends on the baseline.

- [ ] **Step 4: Check the formatter baseline**

Run:

```bash
docker run --rm \
  -v "$PWD:/mnt" \
  -w /mnt \
  mvdan/shfmt:v3.14.0 \
  -d -i 2 -ci .

uvx ruff@0.16.5 format --check --diff .
```

Expected: both commands exit 0 and print no formatting diff.

- [ ] **Step 5: Run the deterministic behavior checks after formatting**

Run:

```bash
bash tests/hooks-test.sh
python3 plugin/skills/behavior-diff/scripts/decisions.py --check
bash tests/live-report-contract.sh
```

Expected:

```text
ok — all hook self-checks passed
decisions.py self-check ok
ok — live report contract passed
```

- [ ] **Step 6: Check whitespace and Python syntax**

Run:

```bash
git diff --check
python3 -m py_compile \
  plugin/skills/behavior-diff/scripts/decisions.py \
  plugin/skills/behavior-diff/scripts/render.py
```

Expected: both commands exit 0 with no output.

- [ ] **Step 7: Commit the mechanical formatting separately**

Run:

```bash
git add \
  bin/behavior-diff \
  plugin/scripts \
  plugin/skills/behavior-diff/scripts \
  tests

git commit --signoff -m "style: normalize shell and Python formatting"
```

Expected: the commit message contains a `Signed-off-by:` trailer. The commit
contains formatting only.

---

### Task 2: Document the formatter commands

**Files:**

- Modify: `.gitignore`
- Modify: `AGENTS.md:50-65`
- Modify: `CODING_GUIDELINES.md:134-147`

- [ ] **Step 1: Add formatter checks to `AGENTS.md`**

In the `## Verification` section, add these commands before the deterministic
suite:

```bash
docker run --rm -v "$PWD:/mnt" -w /mnt \
  mvdan/shfmt:v3.14.0 -d -i 2 -ci .
uvx ruff@0.16.5 format --check --diff .
```

State that the first command checks Bash formatting and the second checks all
Python files.

- [ ] **Step 2: Add formatter checks to `CODING_GUIDELINES.md`**

Replace the verification example with:

```bash
docker run --rm -v "$PWD:/mnt" -w /mnt \
  mvdan/shfmt:v3.14.0 -d -i 2 -ci .
uvx ruff@0.16.5 format --check --diff .
bash -n \
  bin/behavior-diff \
  plugin/scripts/*.sh \
  plugin/skills/behavior-diff/scripts/*.sh \
  tests/*.sh
shellcheck \
  bin/behavior-diff \
  plugin/scripts/*.sh \
  plugin/skills/behavior-diff/scripts/*.sh \
  tests/*.sh
python3 -m py_compile \
  plugin/skills/behavior-diff/scripts/decisions.py \
  plugin/skills/behavior-diff/scripts/render.py
bash tests/hooks-test.sh
python3 plugin/skills/behavior-diff/scripts/decisions.py --check
bash tests/live-report-contract.sh
git diff --check
```

Keep the existing rule that agents must report unavailable checks instead of
substituting weaker checks.

- [ ] **Step 3: Ignore local Python bytecode**

Add these entries to `.gitignore`:

```gitignore
__pycache__/
*.pyc
```

This keeps local `py_compile` verification from dirtying the worktree.

- [ ] **Step 4: Check the documentation change**

Run:

```bash
git diff --check
```

Expected: exit 0 with no output.

---

### Task 3: Add the GitHub Actions workflow

**Files:**

- Create: `.github/workflows/ci.yml`

- [ ] **Step 1: Create the workflow with two jobs**

Create `.github/workflows/ci.yml` with this complete content:

```yaml
name: CI

on:
  pull_request:
  push:
    branches:
      - main

permissions:
  contents: read

concurrency:
  group: ci-${{ github.workflow }}-${{ github.event.pull_request.number || github.ref }}
  cancel-in-progress: true

env:
  CI: "1"
  ANTHROPIC_API_KEY: ""
  CLAUDE_CODE_OAUTH_TOKEN: ""
  OPENAI_API_KEY: ""

jobs:
  format:
    name: Format
    runs-on: ubuntu-latest
    timeout-minutes: 5
    steps:
      - name: Check out repository
        uses: actions/checkout@v5

      - name: Check Bash formatting
        run: |
          docker run --rm \
            -v "$PWD:/mnt" \
            -w /mnt \
            mvdan/shfmt:v3.14.0 \
            -d -i 2 -ci .

      - name: Check Python formatting
        uses: astral-sh/ruff-action@v4.1.0
        with:
          version: "0.16.5"
          args: "format --check --diff"
          src: "."

  unit:
    name: Unit
    runs-on: ubuntu-latest
    timeout-minutes: 5
    steps:
      - name: Check out repository
        uses: actions/checkout@v5

      - name: Block LLM executables
        run: |
          mkdir -p "$RUNNER_TEMP/no-llm"
          for command in claude codex; do
            cat >"$RUNNER_TEMP/no-llm/$command" <<'EOF'
          #!/usr/bin/env bash
          printf 'LLM invocation is forbidden in CI\n' >&2
          exit 97
          EOF
            chmod +x "$RUNNER_TEMP/no-llm/$command"
          done
          echo "$RUNNER_TEMP/no-llm" >>"$GITHUB_PATH"

      - name: Check shell syntax
        run: |
          bash -n \
            bin/behavior-diff \
            plugin/scripts/*.sh \
            plugin/skills/behavior-diff/scripts/*.sh \
            tests/*.sh

      - name: Check Python syntax
        run: |
          python3 -m py_compile \
            plugin/skills/behavior-diff/scripts/decisions.py \
            plugin/skills/behavior-diff/scripts/render.py

      - name: Run hook unit checks
        run: bash tests/hooks-test.sh

      - name: Run decision unit check
        run: python3 plugin/skills/behavior-diff/scripts/decisions.py --check

      - name: Run report contract checks
        run: bash tests/live-report-contract.sh
```

- [ ] **Step 2: Confirm that the workflow has no model-backed command**

Read the complete workflow. The only `claude` and `codex` occurrences must be:

- the empty credential environment variable names;
- the two failing wrapper names in `Block LLM executables`.

The workflow must not call:

```text
behavior-diff.sh
run-trial.sh
tests/nudge-e2e.sh
claude -p
codex exec
```

- [ ] **Step 3: Run the exact local equivalents of both jobs**

Run:

```bash
docker run --rm \
  -v "$PWD:/mnt" \
  -w /mnt \
  mvdan/shfmt:v3.14.0 \
  -d -i 2 -ci .

uvx ruff@0.16.5 format --check --diff .

bash -n \
  bin/behavior-diff \
  plugin/scripts/*.sh \
  plugin/skills/behavior-diff/scripts/*.sh \
  tests/*.sh

python3 -m py_compile \
  plugin/skills/behavior-diff/scripts/decisions.py \
  plugin/skills/behavior-diff/scripts/render.py

bash tests/hooks-test.sh
python3 plugin/skills/behavior-diff/scripts/decisions.py --check
bash tests/live-report-contract.sh
git diff --check
```

Expected: every command exits 0. The three test commands print their normal
success messages. No command starts a model-backed process.

- [ ] **Step 4: Commit the workflow and documentation with sign-off**

Run:

```bash
git add .github/workflows/ci.yml AGENTS.md CODING_GUIDELINES.md
git commit --signoff -m "ci: add deterministic format and unit checks"
```

Expected: the commit message contains a `Signed-off-by:` trailer.

- [ ] **Step 5: Push and watch the first CI run**

Run:

```bash
git push
gh run watch "$(gh run list --workflow ci.yml --limit 1 \
  --json databaseId --jq '.[0].databaseId')"
```

Expected: the `Format` and `Unit` jobs both pass. No other CI job exists.

---

## Final verification checklist

- [ ] `.github/workflows/ci.yml` has only `format` and `unit` jobs.
- [ ] Bash formatting uses `shfmt` 3.14.0.
- [ ] Python formatting uses Ruff 0.16.5 with `format --check --diff`.
- [ ] The unit job blocks real `claude` and `codex` executables.
- [ ] The unit job runs only deterministic syntax and contract checks.
- [ ] No live journey or model-backed runner appears in a CI command.
- [ ] `AGENTS.md` and `CODING_GUIDELINES.md` state both formatter commands.
- [ ] Both implementation commits include DCO sign-off trailers.
- [ ] The GitHub Actions run shows only `Format` and `Unit`, both green.
