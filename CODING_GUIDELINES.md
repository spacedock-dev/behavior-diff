# Coding guidelines

Behavior Diff production code includes agent-skill Markdown, Bash, and Python.
Treat wording, ordering, error handling, and test evidence as executable
behavior. The invariants in [AGENTS.md](AGENTS.md) override this guide.

This guide adapts the applicable rules from the private Engram repository.
Engram-only Reflection and Tricorder rules are not part of this repository.

## General principles

- Make the smallest change that satisfies the requirement. Do not include
  unrelated cleanup or refactoring.
- Preserve privacy and consent boundaries. Never add real transcripts, session
  data, reports, digests, credentials, customer names, or private data.
- Prefer explicit behavior over cleverness. Safety-sensitive paths must fail
  closed when inputs, dependencies, versions, or state are uncertain.
- Keep Claude Code and Codex behavior equivalent. Label a host-specific path
  and provide its counterpart, or explain why no counterpart is valid.
- Update the nearest contract or fixture for each behavior change. A prose-only
  change can still cause a production regression.
- Use the least expensive check that covers the demonstrated risk. Keep fast,
  deterministic checks in CI. Keep model-backed checks manual.

## Agent-skill Markdown

### Structure and discovery

- Put each skill in a lower-case, hyphenated directory with a `SKILL.md` file.
- Keep YAML frontmatter minimal. Make `name` match the skill directory. Make
  `description` state the situations and requests that trigger the skill.
- Keep the core workflow in `SKILL.md`. Move detailed schemas, background, and
  variant-specific material into directly linked reference files.
- Keep one source of truth for shared rules. Link to a rule instead of copying
  wording that can drift.
- Bundle a script when repeated work needs deterministic behavior. Do not ask
  an agent to recreate fragile shell commands from prose.
- Keep maintainer documents outside packaged skill directories unless a skill
  needs the document at runtime.

### Instruction design

- Use direct instructions. Use numbered steps when order matters.
- For safety-sensitive work, name the allowed commands, inputs, write targets,
  approval gates, and stop conditions.
- Define ambiguous terms at first use. Name the actor, target, and scope.
- State exclusive modes and state changes explicitly. A later paragraph must
  not weaken an earlier `must`, `only`, or `never`.
- Put prerequisites and consent before reads. Put previews before writes,
  approval before apply, and verification after apply.
- Specify observable results: output shape, persistent files, exit behavior,
  and the final user message.
- Use synthetic, redacted examples. Keep lines near 80–100 characters when
  code, tables, or URLs do not prevent it.

### Skill change checklist

For each `SKILL.md` change:

1. Read the complete affected workflow and its direct references.
2. Find duplicated wording, versions, validators, fixtures, and host-specific
   counterparts that the change can affect.
3. Check the change against every invariant in `AGENTS.md`.
4. Update the report-format version if the required report shape changes.
5. Run the relevant deterministic contract checks.
6. If model-backed evidence is necessary, run it manually with user approval.
   Do not put it in CI.

A text-presence check does not prove that two instructions agree. Read both
producer and consumer instructions when one step consumes another step's
output.

## Source code

- Follow the existing language, repository, and formatter conventions.
- Prefer direct control flow and precise names.
- Give each module and function one clear purpose.
- Make dependencies explicit. Avoid hidden global state and import-time side
  effects.
- Keep mutable state local and short-lived.
- Separate computation from input, output, and external state when practical.
- Preserve failures and add useful context. Never discard a failure.
- Write comments only for rationale, invariants, hazards, or non-obvious
  constraints.
- Add an abstraction only when it removes real duplication or isolates a known
  variation.
- Remove obsolete code after all callers use its replacement.
- Test observable behavior, boundaries, and failure modes.

## Bash

- Start executable scripts with `#!/usr/bin/env bash` and use
  `set -euo pipefail` near the top.
- Support macOS Bash 3.2 and current Ubuntu Bash unless the script checks and
  documents a newer minimum version.
- Use lower-case `snake_case` for local variables and functions. Use upper-case
  names for exported environment variables and constants.
- Quote parameter expansions unless splitting or glob expansion is intentional
  and documented.
- Prefer `[[ ... ]]` for conditions, `(( ... ))` for arithmetic, and `printf`
  for controlled output.
- Reject unknown options, missing values, invalid enums, and surplus arguments.
- Check required commands and files before work starts. Parse structured data
  with a suitable parser such as `jq`.
- Write diagnostics to standard error. Keep contract output machine-readable.
- Do not hide failures with broad `|| true`. Handle an allowed nonzero status
  next to the command.
- Create scratch directories with `mktemp -d` and install a cleanup trap.
- Never build a destructive target from an unchecked variable or broad path.
- Avoid `eval`, parsing `ls`, sourcing untrusted files, and running text from
  untrusted input.

## Python

- Use the Python standard library unless the requirement justifies a dependency.
- Keep scripts import-safe. Put command execution behind a `main()` function.
- Parse and validate external JSON before using its fields.
- Write diagnostics to standard error and return a nonzero status on failure.
- Keep generated output deterministic for identical inputs.

## Tests

- Keep tests hermetic. Use temporary homes and repositories, explicit fixtures,
  and cleanup traps.
- Mark fixtures as synthetic and use invented data.
- Run the shipped script. Do not test a modified copy.
- Cover observable success, invalid input, missing dependencies, stale state,
  path escape, cleanup, output, and exit status where they apply.
- Keep ShellCheck suppressions narrow, adjacent, and justified.
- Keep real model boundaries closed in deterministic tests. Remove credentials
  and put harness-owned `claude` or `codex` stubs first on `PATH` when a test
  must exercise command discovery.

## Verification before handoff

Run the checks relevant to the changed files. Do not claim checks that did not
run.

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

For the complete deterministic suite, use the commands in `AGENTS.md`.

## Review before pull requests

Before an agent creates or updates a pull request:

1. Finish the intended change and run the relevant checks.
2. Ask an independent, read-only reviewer to inspect the complete change.
3. Require the reviewer to follow
   [REVIEWER_GUIDELINES.md](REVIEWER_GUIDELINES.md).
4. Fix each confirmed material finding or record the user's acceptance.
5. Repeat the review if a correction changes the result.
6. Create or update the pull request only after an `APPROVE` verdict.

If an independent reviewer is unavailable, stop before creating or updating
the pull request and report the missing gate.
