# Behavior Diff — agent rules

Behavior Diff compares agent behavior before and after an instruction-file
change. The repository contains an installable Claude Code and Codex plugin,
its deterministic test harness, and synthetic end-to-end fixtures.

`AGENTS.md` is the single source of truth for repository instructions.
`CLAUDE.md` only imports this file. Do not duplicate rules in `CLAUDE.md`.

## Required guides

- Follow [CODING_GUIDELINES.md](CODING_GUIDELINES.md) for agent-skill Markdown,
  Bash, Python, testing, and review conventions.
- Follow [ISSUE_GUIDELINES.md](ISSUE_GUIDELINES.md) for issue type, priority,
  and milestone rules.
- Every independent reviewer must follow
  [REVIEWER_GUIDELINES.md](REVIEWER_GUIDELINES.md).

These files adapt the guidelines from the private Engram repository. This file
is authoritative when a Behavior Diff rule differs from an Engram rule.

## Invariants

1. **Canonical source.** `plugin/` is the installable plugin. Its `skills/`
   directories are the canonical skill source. Do not add a mirrored copy.
2. **One product, two hosts.** Keep Claude Code and Codex behavior equivalent.
   Keep `plugin/.claude-plugin/plugin.json` and
   `plugin/.codex-plugin/plugin.json` at the same version.
3. **No marketplace manifest.** The shared `spacedock-dev/marketplace`
   repository owns the marketplace entry. Do not add one here.
4. **Privacy.** Never commit runs, reports, transcripts, credentials, customer
   names, or other session data. All committed fixtures must be synthetic.
5. **Deterministic CI only.** CI must never invoke `claude`, `codex`, a model
   API, `behavior-diff.sh`, `run-trial.sh`, or a live e2e journey. CI runs only
   static checks and deterministic unit or contract tests.
6. **Product name.** Use **Behavior Diff** in product prose. Keep
   `behavior-diff` for commands, plugin names, skill names, and paths.
7. **Clean cutover.** Migrate all callers when a contract changes. Remove the
   old path or wording instead of adding a compatibility alias.

## Repository layout

- `plugin/` — plugin manifests, hooks, skills, and bundled scripts.
- `bin/behavior-diff` — local command for applying and comparing one rule.
- `tests/` — deterministic shell and Python contract checks.
- `e2e/` — synthetic fixtures and manual live journeys.
- `.agents/skills/` — repository-maintainer skills, not plugin payload.
- `RETRO_NOTES.md` — durable tool lessons with no transcript excerpts.

## Verification

Check Bash and Python formatting from the repository root:

```bash
docker run --rm -v "$PWD:/mnt" -w /mnt \
  mvdan/shfmt:v3.14.0 -d -i 2 -ci .
uvx ruff@0.16.5 format --check --diff .
```

The first command checks Bash formatting. The second checks all Python files.
For the full deterministic suite, run:

```bash
bash tests/hooks-test.sh
python3 plugin/skills/behavior-diff/scripts/decisions.py --check
bash tests/live-report-contract.sh
bash tests/release-workflow-test.sh
```

For Markdown-only changes, also run `git diff --check`. Do not replace these
checks with a model run.

Live journeys under `e2e/` are manual evidence. Run them only when the user asks
and approves the model cost.

## Commits and reviews

- Every commit must include a DCO sign-off. Use `git commit --signoff`.
- Keep commits focused. Do not mix unrelated cleanup with a behavior change.
- Before a pull request, run the relevant deterministic checks and complete an
  independent read-only review under `REVIEWER_GUIDELINES.md`.
- If a required check or reviewer is unavailable, report the missing gate. Do
  not substitute a weaker check.

## Additional agent entry point

[CLAUDE.md](CLAUDE.md) imports this file for Claude Code. It contains no other
repository rules.
