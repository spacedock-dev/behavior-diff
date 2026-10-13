---
name: github-skill-change-stats
description: Ranks the skills in one or more GitHub repositories by how often they changed, with PR count, commit count, and first and last change dates. Use when asked which skills in a repo are modified most, for skill change statistics across GitHub repos, or to pick heavily edited skills to study.
---

# GitHub skill change stats

Produce one Markdown table per repository. The bundled script does the
counting; do not rebuild its `git log` commands by hand.

## Run

1. Collect the repositories as `OWNER/REPO` or `https://github.com/OWNER/REPO`.
2. Run, from the repository root:

   ```bash
   .agents/skills/github-skill-change-stats/scripts/skill-stats.sh \
     [--top N] [--cache DIR] OWNER/REPO...
   ```

   `--top` defaults to 20 rows. The script makes a blob-less clone with no
   checkout under `--cache` (default `$TMPDIR/github-skill-change-stats`) and
   fetches again on later runs. It is read-only toward GitHub.
3. If a clone fails (private repo, typo), the script prints `Skipped: clone
   failed.` for that repository and continues. Report it as skipped. Do not
   retry with other credentials unasked.

## What the numbers mean

- **Skill**: the first directory under any `skills/` directory. A skill that
  moved (for example from `plugins/x/skills/foo/` to `skills/foo/`) merges by
  name. Paths under top-level dot directories such as `.agents/` and
  `.claude/` are maintainer skills and are skipped.
- **Commits**: commits in all history that touched the skill, once per commit.
- **PRs**: distinct `#NUMBER` values in main-line commit subjects (squash
  `(#123)` or `Merge pull request #123`) that touched the skill. A direct push
  with no number adds no PR, so read PRs together with the header line
  `N commits · M with a PR number`.
- **Rows are sorted** by PRs, then commits.

## Check before reporting

The script cannot see renames. Look for a row whose last change is old and
whose name resembles a newer row (for example `ce-review` → `ce-code-review`,
`document-review` → `ce-doc-review`). Report likely renames as a note under
the table; do not add their numbers together without saying so.
A `skills/<name>/` that holds shared files rather than a skill (for example
`skills/guides/`) can also appear; note it rather than dropping it silently.

## Report

Lead with the top three skills per repo in one plain sentence each, then the
tables, then the rename and non-skill notes. Keep the script's columns.
