# Public Skill Change Stats

Date: 2026-10-13

This note ranks the most-changed skills in the public skill repositories that
the [skill history replay workflow](../docs/skill-history-replay/README.md)
uses. Use it to pick heavily edited skills for replay cases.

## Sources

The repository list has two parts:

- the 18 repositories in the catalog of
  [`2026-09-29-public-skill-history-sources.md`](2026-09-29-public-skill-history-sources.md);
- 7 more repositories that only the workflow cases use: `addyosmani/agent-skills`,
  `EveryInc/compound-engineering-plugin`, `kepano/obsidian-skills`,
  `Jeffallan/claude-skills`, `posit-dev/skills`, `blader/humanizer`, and
  `daymade/claude-code-skills`.

Not included:

- `VoltAgent/awesome-agent-skills`: the catalog uses it to find repositories,
  not as a source of skill history.
- `openai/codex`: a case cites one PR there; it is not a skill repository.
- `DataRecce/recce-team`: private.

## Method

Each table comes from the `github-skill-change-stats` skill:

```bash
.agents/skills/github-skill-change-stats/scripts/skill-stats.sh \
  [--sort commits] OWNER/REPO
```

- **Commits** counts every commit that touched a skill folder, once per commit.
- **PRs** counts distinct `#NUMBER` values in main-line commit subjects.
- A skill is the first folder under a `skills/` folder.
- When fewer than half of a repository's commits have a PR number, its table
  is sorted by commits (`--sort commits`). Otherwise it is sorted by PRs.

## Summary

25 repositories were checked. 19 are counted below. The other 6 use a skill
layout that the script cannot count yet (see
[Not counted yet](#not-counted-yet)). `mattpocock/skills` (marked `*`) was
counted with a one-off command instead of the script; see its table.

| Repository | Commits | With PR # | Sorted by | Top 3 skills |
|---|---|---|---|---|
| [EveryInc/compound-engineering-plugin](https://github.com/EveryInc/compound-engineering-plugin) | 1448 | 75% | prs | `ce-plan`, `ce-code-review`, `ce-brainstorm` |
| [coreyhaines31/marketingskills](https://github.com/coreyhaines31/marketingskills) | 1014 | 43% | commits | `ad-creative`, `ai-seo`, `ads` |
| [K-Dense-AI/scientific-agent-skills](https://github.com/K-Dense-AI/scientific-agent-skills) | 760 | 13% | commits | `scientific-slides`, `citation-management`, `literature-review` |
| [obra/superpowers](https://github.com/obra/superpowers) | 684 | 9% | commits | `brainstorming`, `subagent-driven-development`, `using-superpowers` |
| [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills) | 677 | 37% | commits | `security-and-hardening`, `code-review-and-quality`, `performance-optimization` |
| [mattpocock/skills](https://github.com/mattpocock/skills) `*` | 545 | 23% | commits | `wayfinder`, `ask-matt`, `setup-matt-pocock-skills` |
| [huggingface/skills](https://github.com/huggingface/skills) | 350 | 42% | commits | `hf-cli`, `hugging-face-paper-publisher`, `hugging-face-datasets` |
| [cloudflare/skills](https://github.com/cloudflare/skills) | 286 | 43% | commits | `cloudflare`, `workers-best-practices`, `wrangler` |
| [vercel-labs/agent-skills](https://github.com/vercel-labs/agent-skills) | 275 | 24% | commits | `react-view-transitions`, `react-best-practices`, `vercel-optimize` |
| [getsentry/skills](https://github.com/getsentry/skills) | 249 | 45% | commits | `iterate-pr`, `claude-settings-audit`, `create-branch` |
| [Jeffallan/claude-skills](https://github.com/Jeffallan/claude-skills) | 213 | 35% | commits | `devops-engineer`, `test-master`, `flutter-expert` |
| [trailofbits/skills](https://github.com/trailofbits/skills) | 209 | 98% | prs | `second-opinion`, `semgrep`, `semgrep-rule-creator` |
| [expo/skills](https://github.com/expo/skills) | 142 | 75% | prs | `eas-simulator`, `upgrading-expo`, `building-native-ui` |
| [czlonkowski/n8n-skills](https://github.com/czlonkowski/n8n-skills) | 96 | 18% | commits | `n8n-mcp-tools-expert`, `n8n-validation-expert`, `n8n-workflow-patterns` |
| [supabase/agent-skills](https://github.com/supabase/agent-skills) | 96 | 71% | prs | `supabase`, `supabase-postgres-best-practices`, `postgres-best-practices` |
| [remotion-dev/skills](https://github.com/remotion-dev/skills) | 89 | 0% | commits | `remotion-best-practices`, `remotion-markup`, `remotion-interactivity` |
| [hashicorp/agent-skills](https://github.com/hashicorp/agent-skills) | 67 | 71% | prs | `terraform-stacks`, `refactor-module`, `terraform-style-guide` |
| [anthropics/skills](https://github.com/anthropics/skills) | 60 | 98% | prs | `claude-api`, `docx`, `pptx` |
| [kepano/obsidian-skills](https://github.com/kepano/obsidian-skills) | 49 | 32% | commits | `obsidian-bases`, `json-canvas`, `obsidian-markdown` |

## Notes on the tables

The script cannot see renames. Old and new names appear as separate rows.
These renames are confirmed by commit messages:

- `EveryInc/compound-engineering-plugin`: `ce-review` → `ce-code-review`.
- `mattpocock/skills`: `github-triage` → `triage`, `write-a-prd` →
  `to-prd` → `to-spec`, and `prd-to-issues` → `to-issues`.
- `huggingface/skills`: many `hugging-face-*` skills got shorter names in
  "rename skills for simplicity (#99)" on 2026-03-23, for example
  `hugging-face-cli` → `hf-cli`. Also `hf-best-model` → `huggingface-best`.
- `supabase/agent-skills`: `postgresql-best-practices` →
  `postgres-best-practices`.
- `vercel-labs/agent-skills`: `vercel-design-guidelines` →
  `web-design-guidelines`.

These rows are folders that hold skills, not skills:

- `obra/superpowers`: `collaboration`, `debugging`, `meta`, `research`,
  `problem-solving`, `architecture`, and `getting-started`. Until 2025-10 the
  repository used `skills/<category>/<skill>/`.
- `vercel-labs/agent-skills`: `claude.ai` holds `vercel-deploy-claimable`.

## Not counted yet

These repositories do not keep each skill at `skills/<name>/`, so their
tables would be wrong. They are left out until the script finds skills by
their `SKILL.md` files.

| Repository | Where its skills live | What the script did |
|---|---|---|
| [openai/skills](https://github.com/openai/skills) | `skills/.curated/<skill>/` | Counted `.curated` as one skill |
| [microsoft/skills](https://github.com/microsoft/skills) | `.github/plugins/<plugin>/skills/<skill>/` | Skipped the `.github/` paths |
| [daymade/claude-code-skills](https://github.com/daymade/claude-code-skills) | `<skill>/` at the root | Found no skills |
| [posit-dev/skills](https://github.com/posit-dev/skills) | `<skill>/` and `<group>/<skill>/` at the root | Found no skills |
| [garrytan/gstack](https://github.com/garrytan/gstack) | `<skill>/` at the root (69 skills) | Found 4 skills |
| [blader/humanizer](https://github.com/blader/humanizer) | One `SKILL.md` at the root | Missed most changes |

## Tables

### EveryInc/compound-engineering-plugin

HEAD 50532b00 2026-10-11 · 1448 commits · 1100 with a PR number

| # | Skill | PRs | Commits | First change | Last change |
|---|---|---|---|---|---|
| 1 | ce-plan | 155 | 161 | 2026-03-08 | 2026-10-05 |
| 2 | ce-code-review | 153 | 153 | 2026-04-18 | 2026-10-11 |
| 3 | ce-brainstorm | 132 | 137 | 2026-03-08 | 2026-10-05 |
| 4 | ce-work | 117 | 117 | 2026-03-08 | 2026-10-07 |
| 5 | ce-doc-review | 111 | 111 | 2026-04-18 | 2026-10-07 |
| 6 | ce-compound | 96 | 96 | 2026-03-08 | 2026-10-01 |
| 7 | ce-pov | 70 | 70 | 2026-06-29 | 2026-10-07 |
| 8 | ce-ideate | 64 | 66 | 2026-03-16 | 2026-10-01 |
| 9 | lfg | 62 | 64 | 2026-03-08 | 2026-10-05 |
| 10 | ce-setup | 61 | 61 | 2026-04-10 | 2026-10-07 |
| 11 | ce-commit-push-pr | 59 | 59 | 2026-04-18 | 2026-09-11 |
| 12 | ce-compound-refresh | 58 | 75 | 2026-03-12 | 2026-10-01 |
| 13 | ce-debug | 55 | 55 | 2026-04-10 | 2026-10-11 |
| 14 | ce-work-beta | 50 | 50 | 2026-03-22 | 2026-06-26 |
| 15 | ce-optimize | 45 | 45 | 2026-04-12 | 2026-10-01 |
| 16 | ce-resolve-pr-feedback | 45 | 45 | 2026-04-18 | 2026-10-01 |
| 17 | ce-babysit-pr | 44 | 44 | 2026-07-12 | 2026-09-21 |
| 18 | ce-explain | 31 | 31 | 2026-07-02 | 2026-09-22 |
| 19 | ce-sweep | 30 | 30 | 2026-07-03 | 2026-09-18 |
| 20 | ce-review | 27 | 27 | 2026-03-08 | 2026-04-18 |

### coreyhaines31/marketingskills

HEAD 3b84db2 2026-10-12 · 1014 commits · 446 with a PR number

| # | Skill | PRs | Commits | First change | Last change |
|---|---|---|---|---|---|
| 1 | ad-creative | 20 | 40 | 2026-02-17 | 2026-10-12 |
| 2 | ai-seo | 19 | 35 | 2026-02-18 | 2026-10-08 |
| 3 | ads | 14 | 27 | 2026-05-13 | 2026-10-08 |
| 4 | seo-audit | 16 | 25 | 2026-01-16 | 2026-10-08 |
| 5 | copy-editing | 12 | 20 | 2026-01-16 | 2026-10-07 |
| 6 | sales-enablement | 12 | 20 | 2026-02-22 | 2026-10-07 |
| 7 | social-content | 10 | 19 | 2026-01-16 | 2026-04-24 |
| 8 | content-strategy | 14 | 18 | 2026-01-26 | 2026-10-07 |
| 9 | copywriting | 13 | 17 | 2026-01-16 | 2026-10-02 |
| 10 | social | 10 | 17 | 2026-05-13 | 2026-10-07 |
| 11 | cold-email | 7 | 16 | 2026-02-14 | 2026-10-07 |
| 12 | prospecting | 7 | 16 | 2026-05-26 | 2026-10-08 |
| 13 | marketing-plan | 6 | 16 | 2026-05-27 | 2026-10-06 |
| 14 | email-sequence | 12 | 15 | 2026-01-16 | 2026-03-27 |
| 15 | paid-ads | 10 | 15 | 2026-01-16 | 2026-04-21 |
| 16 | programmatic-seo | 10 | 15 | 2026-01-16 | 2026-10-02 |
| 17 | marketing-ideas | 12 | 14 | 2026-01-16 | 2026-08-23 |
| 18 | ab-test-setup | 9 | 14 | 2026-01-16 | 2026-04-03 |
| 19 | competitor-profiling | 7 | 14 | 2026-04-07 | 2026-10-07 |
| 20 | revops | 7 | 14 | 2026-02-22 | 2026-10-08 |

### K-Dense-AI/scientific-agent-skills

HEAD a1043ef 2026-10-12 · 760 commits · 105 with a PR number

| # | Skill | PRs | Commits | First change | Last change |
|---|---|---|---|---|---|
| 1 | scientific-slides | 1 | 20 | 2026-05-27 | 2026-10-01 |
| 2 | citation-management | 2 | 18 | 2026-05-27 | 2026-10-01 |
| 3 | literature-review | 1 | 17 | 2026-05-27 | 2026-10-01 |
| 4 | infographics | 0 | 16 | 2026-05-27 | 2026-10-01 |
| 5 | latex-posters | 0 | 16 | 2026-05-27 | 2026-10-01 |
| 6 | scientific-schematics | 0 | 16 | 2026-05-27 | 2026-10-01 |
| 7 | imaging-data-commons | 2 | 13 | 2026-05-27 | 2026-10-01 |
| 8 | xlsx | 0 | 13 | 2026-05-27 | 2026-10-01 |
| 9 | markitdown | 0 | 12 | 2026-05-27 | 2026-10-01 |
| 10 | pptx-posters | 0 | 12 | 2026-05-27 | 2026-10-01 |
| 11 | database-lookup | 3 | 11 | 2026-05-27 | 2026-10-01 |
| 12 | peer-review | 1 | 11 | 2026-05-27 | 2026-10-01 |
| 13 | clinical-decision-support | 0 | 11 | 2026-05-27 | 2026-10-01 |
| 14 | clinical-reports | 0 | 11 | 2026-05-27 | 2026-10-01 |
| 15 | gget | 0 | 11 | 2026-05-27 | 2026-10-01 |
| 16 | neuropixels-analysis | 0 | 11 | 2026-05-27 | 2026-10-01 |
| 17 | open-notebook | 0 | 11 | 2026-05-27 | 2026-10-01 |
| 18 | scanpy | 0 | 11 | 2026-05-27 | 2026-10-01 |
| 19 | scholar-evaluation | 0 | 11 | 2026-05-27 | 2026-10-01 |
| 20 | rdkit | 2 | 10 | 2026-05-27 | 2026-10-01 |

### obra/superpowers

HEAD bb92a77 2026-10-09 · 684 commits · 67 with a PR number

| # | Skill | PRs | Commits | First change | Last change |
|---|---|---|---|---|---|
| 1 | brainstorming | 5 | 87 | 2025-10-16 | 2026-10-09 |
| 2 | subagent-driven-development | 6 | 64 | 2025-10-16 | 2026-10-09 |
| 3 | using-superpowers | 6 | 36 | 2025-10-16 | 2026-09-18 |
| 4 | writing-plans | 5 | 26 | 2025-10-16 | 2026-09-25 |
| 5 | getting-started | 2 | 17 | 2025-10-09 | 2025-10-11 |
| 6 | executing-plans | 4 | 16 | 2025-10-16 | 2026-10-09 |
| 7 | requesting-code-review | 4 | 16 | 2025-10-16 | 2026-10-09 |
| 8 | systematic-debugging | 5 | 14 | 2025-10-16 | 2026-10-09 |
| 9 | test-driven-development | 2 | 13 | 2025-10-16 | 2026-09-18 |
| 10 | finishing-a-development-branch | 3 | 12 | 2025-10-16 | 2026-08-12 |
| 11 | collaboration | 3 | 10 | 2025-10-09 | 2025-10-11 |
| 12 | using-git-worktrees | 5 | 9 | 2025-10-16 | 2026-07-05 |
| 13 | meta | 3 | 8 | 2025-10-09 | 2025-10-11 |
| 14 | architecture | 2 | 6 | 2025-10-10 | 2025-10-11 |
| 15 | receiving-code-review | 1 | 6 | 2025-10-16 | 2026-07-05 |
| 16 | dispatching-parallel-agents | 0 | 6 | 2025-10-16 | 2026-07-05 |
| 17 | testing-skills-with-subagents | 0 | 4 | 2025-10-16 | 2025-10-18 |
| 18 | debugging | 2 | 3 | 2025-10-09 | 2025-10-11 |
| 19 | problem-solving | 2 | 3 | 2025-10-10 | 2025-10-11 |
| 20 | research | 2 | 3 | 2025-10-10 | 2025-10-11 |

### addyosmani/agent-skills

HEAD 1be8e34 2026-10-10 · 677 commits · 252 with a PR number

| # | Skill | PRs | Commits | First change | Last change |
|---|---|---|---|---|---|
| 1 | security-and-hardening | 13 | 17 | 2026-02-15 | 2026-10-03 |
| 2 | code-review-and-quality | 10 | 16 | 2026-02-15 | 2026-09-27 |
| 3 | performance-optimization | 9 | 15 | 2026-02-15 | 2026-10-02 |
| 4 | spec-driven-development | 10 | 13 | 2026-02-15 | 2026-10-02 |
| 5 | shipping-and-launch | 9 | 13 | 2026-02-15 | 2026-10-03 |
| 6 | frontend-ui-engineering | 8 | 12 | 2026-02-15 | 2026-10-03 |
| 7 | incremental-implementation | 7 | 10 | 2026-02-15 | 2026-08-07 |
| 8 | test-driven-development | 7 | 10 | 2026-02-15 | 2026-08-07 |
| 9 | planning-and-task-breakdown | 7 | 9 | 2026-02-15 | 2026-08-28 |
| 10 | documentation-and-adrs | 6 | 9 | 2026-02-15 | 2026-10-08 |
| 11 | context-engineering | 4 | 9 | 2026-02-15 | 2026-09-05 |
| 12 | debugging-and-error-recovery | 5 | 8 | 2026-02-15 | 2026-07-30 |
| 13 | observability-and-instrumentation | 5 | 8 | 2026-06-09 | 2026-09-04 |
| 14 | constraint-driven-development | 4 | 8 | 2026-07-30 | 2026-09-26 |
| 15 | git-workflow-and-versioning | 6 | 7 | 2026-02-15 | 2026-08-22 |
| 16 | api-and-interface-design | 5 | 7 | 2026-02-15 | 2026-10-02 |
| 17 | idea-refine | 4 | 7 | 2026-02-15 | 2026-06-20 |
| 18 | source-driven-development | 3 | 7 | 2026-04-08 | 2026-07-30 |
| 19 | browser-testing-with-devtools | 5 | 6 | 2026-02-15 | 2026-06-11 |
| 20 | interview-me | 3 | 6 | 2026-05-10 | 2026-08-19 |

### mattpocock/skills

HEAD 49dd158 2026-10-09 · 545 commits · 127 with a PR number

Counted with a one-off command, not the script, because skills live at
`skills/<category>/<skill>/`. A skill is any folder that ever held a
`SKILL.md` (153 folders over the history, 65 names after moves merge by
name). The columns and the commit sort follow the script's rules.

| # | Skill | PRs | Commits | First change | Last change |
|---|---|---|---|---|---|
| 1 | wayfinder | 24 | 48 | 2026-07-01 | 2026-10-07 |
| 2 | ask-matt | 20 | 35 | 2026-06-17 | 2026-10-06 |
| 3 | setup-matt-pocock-skills | 16 | 23 | 2026-04-28 | 2026-10-07 |
| 4 | grilling | 9 | 22 | 2026-05-31 | 2026-10-07 |
| 5 | tdd | 10 | 19 | 2026-02-03 | 2026-10-07 |
| 6 | improve-codebase-architecture | 9 | 19 | 2026-03-13 | 2026-08-19 |
| 7 | teach | 3 | 19 | 2026-05-27 | 2026-10-07 |
| 8 | to-issues | 5 | 15 | 2026-04-17 | 2026-07-07 |
| 9 | to-tickets | 8 | 14 | 2026-07-02 | 2026-10-06 |
| 10 | triage | 8 | 14 | 2026-04-28 | 2026-08-19 |
| 11 | handoff | 5 | 14 | 2026-05-06 | 2026-10-06 |
| 12 | grill-with-docs | 3 | 14 | 2026-04-28 | 2026-08-15 |
| 13 | prototype | 5 | 13 | 2026-05-06 | 2026-08-19 |
| 14 | code-review | 9 | 12 | 2026-07-01 | 2026-10-07 |
| 15 | diagnosing-bugs | 8 | 12 | 2026-05-31 | 2026-10-07 |
| 16 | decision-mapping | 3 | 12 | 2026-06-15 | 2026-07-01 |
| 17 | grill-me | 3 | 11 | 2026-02-25 | 2026-08-15 |
| 18 | to-prd | 2 | 11 | 2026-04-17 | 2026-05-31 |
| 19 | claude-handoff | 6 | 10 | 2026-07-02 | 2026-10-06 |
| 20 | writing-great-skills | 4 | 10 | 2026-06-17 | 2026-07-23 |

### huggingface/skills

HEAD c3ff942 2026-10-08 · 350 commits · 148 with a PR number

| # | Skill | PRs | Commits | First change | Last change |
|---|---|---|---|---|---|
| 1 | hf-cli | 40 | 44 | 2026-03-06 | 2026-10-08 |
| 2 | hugging-face-paper-publisher | 7 | 10 | 2025-12-04 | 2026-03-11 |
| 3 | hugging-face-datasets | 6 | 9 | 2026-01-07 | 2026-03-23 |
| 4 | huggingface-spaces | 7 | 7 | 2026-06-03 | 2026-08-03 |
| 5 | hugging-face-model-trainer | 5 | 7 | 2026-01-07 | 2026-03-11 |
| 6 | hugging-face-evaluation | 5 | 6 | 2026-01-07 | 2026-03-19 |
| 7 | hugging-face-paper-pages | 1 | 6 | 2026-03-13 | 2026-03-17 |
| 8 | hf-best-model | 0 | 6 | 2026-04-20 | 2026-04-20 |
| 9 | hugging-face-cli | 3 | 5 | 2026-01-07 | 2026-03-06 |
| 10 | huggingface-best | 2 | 5 | 2026-04-21 | 2026-08-03 |
| 11 | hugging-face-jobs | 4 | 4 | 2026-01-07 | 2026-03-22 |
| 12 | hugging-face-dataset-creator | 3 | 4 | 2025-12-04 | 2026-01-06 |
| 13 | hugging-face-evaluation-manager | 3 | 4 | 2025-12-04 | 2026-01-06 |
| 14 | hf-cloud-sagemaker-production-defaults | 3 | 3 | 2026-07-07 | 2026-09-10 |
| 15 | hugging-face-tool-builder | 3 | 3 | 2026-01-07 | 2026-03-23 |
| 16 | huggingface-gradio | 3 | 3 | 2026-02-24 | 2026-03-24 |
| 17 | huggingface-llm-trainer | 3 | 3 | 2026-03-23 | 2026-07-06 |
| 18 | huggingface-lora-space-builder | 3 | 3 | 2026-06-08 | 2026-07-16 |
| 19 | huggingface-trackio | 3 | 3 | 2026-03-23 | 2026-07-06 |
| 20 | trl-training | 3 | 3 | 2026-06-08 | 2026-10-01 |

### cloudflare/skills

HEAD 5339598 2026-10-12 · 286 commits · 125 with a PR number

| # | Skill | PRs | Commits | First change | Last change |
|---|---|---|---|---|---|
| 1 | cloudflare | 69 | 96 | 2026-01-28 | 2026-10-12 |
| 2 | workers-best-practices | 6 | 19 | 2026-02-12 | 2026-10-12 |
| 3 | wrangler | 13 | 16 | 2026-01-28 | 2026-10-12 |
| 4 | agents-sdk | 11 | 12 | 2026-01-28 | 2026-10-01 |
| 5 | turnstile-spin | 9 | 12 | 2026-06-04 | 2026-10-13 |
| 6 | cloudflare-one | 5 | 11 | 2026-06-01 | 2026-10-08 |
| 7 | durable-objects | 10 | 10 | 2026-01-28 | 2026-10-01 |
| 8 | cloudflare-one-migrations | 4 | 9 | 2026-06-01 | 2026-10-08 |
| 9 | building-ai-agent-on-cloudflare | 6 | 6 | 2026-01-28 | 2026-04-15 |
| 10 | web-perf | 5 | 6 | 2026-01-28 | 2026-09-05 |
| 11 | cloudflare-email-service | 5 | 5 | 2026-04-15 | 2026-10-01 |
| 12 | building-mcp-server-on-cloudflare | 4 | 4 | 2026-01-28 | 2026-04-15 |
| 13 | sandbox-next | 4 | 4 | 2026-08-07 | 2026-10-01 |
| 14 | sandbox-sdk | 4 | 4 | 2026-02-05 | 2026-08-07 |
| 15 | nextjs-on-cloudflare | 2 | 4 | 2026-09-05 | 2026-10-01 |
| 16 | sandbox-migrate-to-next | 3 | 3 | 2026-08-07 | 2026-10-01 |
| 17 | sandbox-stable | 3 | 3 | 2026-08-07 | 2026-10-01 |
| 18 | basin | 2 | 3 | 2026-09-30 | 2026-10-01 |
| 19 | workers-profiling | 1 | 3 | 2026-10-05 | 2026-10-10 |
| 20 | k2 | 2 | 2 | 2026-09-30 | 2026-10-01 |

### vercel-labs/agent-skills

HEAD 063bee9 2026-08-28 · 275 commits · 67 with a PR number

| # | Skill | PRs | Commits | First change | Last change |
|---|---|---|---|---|---|
| 1 | react-view-transitions | 8 | 73 | 2026-03-29 | 2026-08-28 |
| 2 | react-best-practices | 32 | 46 | 2026-01-13 | 2026-04-14 |
| 3 | vercel-optimize | 7 | 26 | 2026-05-15 | 2026-06-10 |
| 4 | react-native-guidelines | 0 | 12 | 2026-01-25 | 2026-01-25 |
| 5 | composition-patterns | 3 | 11 | 2026-01-25 | 2026-01-28 |
| 6 | claude.ai | 5 | 5 | 2026-01-14 | 2026-03-06 |
| 7 | vercel-design-guidelines | 4 | 4 | 2026-01-04 | 2026-01-14 |
| 8 | vercel-deploy | 0 | 4 | 2025-12-08 | 2025-12-15 |
| 9 | vercel-cli-with-tokens | 3 | 3 | 2026-03-18 | 2026-04-16 |
| 10 | web-design-guidelines | 3 | 3 | 2026-01-14 | 2026-01-16 |
| 11 | react-native-best-practices | 0 | 2 | 2026-01-25 | 2026-01-25 |
| 12 | deploy-to-vercel | 1 | 1 | 2026-03-06 | 2026-03-06 |
| 13 | writing-guidelines | 1 | 1 | 2026-05-25 | 2026-05-25 |

### getsentry/skills

HEAD d18b7aa 2026-09-29 · 249 commits · 114 with a PR number

| # | Skill | PRs | Commits | First change | Last change |
|---|---|---|---|---|---|
| 1 | iterate-pr | 25 | 31 | 2026-01-05 | 2026-08-24 |
| 2 | claude-settings-audit | 25 | 29 | 2026-01-06 | 2026-09-25 |
| 3 | create-branch | 5 | 21 | 2026-02-26 | 2026-05-07 |
| 4 | skill-writer | 15 | 15 | 2026-03-04 | 2026-07-25 |
| 5 | commit | 10 | 15 | 2026-01-05 | 2026-07-15 |
| 6 | pr-writer | 13 | 13 | 2026-03-04 | 2026-07-15 |
| 7 | skill-scanner | 9 | 12 | 2026-02-10 | 2026-09-28 |
| 8 | create-pr | 9 | 10 | 2026-01-05 | 2026-04-07 |
| 9 | blog-writing-guide | 3 | 9 | 2026-02-23 | 2026-04-19 |
| 10 | security-review | 6 | 8 | 2026-01-29 | 2026-09-28 |
| 11 | django-perf-review | 6 | 7 | 2026-01-30 | 2026-09-28 |
| 12 | gha-security-review | 6 | 7 | 2026-03-02 | 2026-09-25 |
| 13 | agents-md | 6 | 6 | 2026-01-10 | 2026-05-04 |
| 14 | gh-review-requests | 4 | 6 | 2026-02-18 | 2026-05-09 |
| 15 | skill-creator | 5 | 5 | 2026-02-06 | 2026-04-07 |
| 16 | django-access-review | 4 | 5 | 2026-02-04 | 2026-09-28 |
| 17 | presentation-creator | 4 | 5 | 2026-03-09 | 2026-05-09 |
| 18 | sred-project-organizer | 3 | 5 | 2026-02-19 | 2026-05-09 |
| 19 | prompt-optimizer | 4 | 4 | 2026-04-19 | 2026-05-04 |
| 20 | code-simplifier | 3 | 4 | 2026-01-31 | 2026-04-19 |

### Jeffallan/claude-skills

HEAD 1be15d8 2026-10-03 · 213 commits · 75 with a PR number

| # | Skill | PRs | Commits | First change | Last change |
|---|---|---|---|---|---|
| 1 | devops-engineer | 10 | 17 | 2025-10-20 | 2026-10-03 |
| 2 | test-master | 10 | 17 | 2025-10-20 | 2026-10-03 |
| 3 | flutter-expert | 9 | 17 | 2025-10-20 | 2026-10-03 |
| 4 | security-reviewer | 9 | 16 | 2025-10-20 | 2026-10-03 |
| 5 | fullstack-guardian | 9 | 15 | 2025-10-20 | 2026-10-03 |
| 6 | code-documenter | 8 | 15 | 2025-10-20 | 2026-10-03 |
| 7 | code-reviewer | 8 | 15 | 2025-10-20 | 2026-10-03 |
| 8 | debugging-wizard | 8 | 15 | 2025-10-20 | 2026-10-03 |
| 9 | react-expert | 8 | 15 | 2025-10-20 | 2026-10-03 |
| 10 | fastapi-expert | 7 | 15 | 2025-10-20 | 2026-10-03 |
| 11 | nestjs-expert | 7 | 15 | 2025-10-20 | 2026-10-03 |
| 12 | architecture-designer | 8 | 14 | 2025-10-20 | 2026-10-03 |
| 13 | django-expert | 8 | 14 | 2025-10-20 | 2026-10-03 |
| 14 | monitoring-expert | 8 | 14 | 2025-10-20 | 2026-10-03 |
| 15 | php-pro | 8 | 14 | 2025-12-14 | 2026-10-03 |
| 16 | feature-forge | 7 | 14 | 2025-10-20 | 2026-10-03 |
| 17 | spec-miner | 7 | 14 | 2025-10-20 | 2026-10-03 |
| 18 | database-optimizer | 9 | 13 | 2025-12-14 | 2026-10-03 |
| 19 | kubernetes-specialist | 8 | 13 | 2025-12-14 | 2026-10-03 |
| 20 | playwright-expert | 7 | 13 | 2025-10-20 | 2026-10-03 |

### trailofbits/skills

HEAD 442fc9d 2026-10-09 · 209 commits · 205 with a PR number

| # | Skill | PRs | Commits | First change | Last change |
|---|---|---|---|---|---|
| 1 | second-opinion | 13 | 13 | 2026-02-10 | 2026-09-16 |
| 2 | semgrep | 12 | 13 | 2026-01-14 | 2026-09-28 |
| 3 | semgrep-rule-creator | 11 | 12 | 2026-01-14 | 2026-09-16 |
| 4 | interpreting-culture-index | 10 | 11 | 2026-01-14 | 2026-09-28 |
| 5 | slicing-code-context | 10 | 10 | 2026-07-29 | 2026-10-09 |
| 6 | yara-rule-authoring | 10 | 10 | 2026-01-30 | 2026-10-09 |
| 7 | codeql | 9 | 10 | 2026-01-14 | 2026-09-16 |
| 8 | let-fate-decide | 9 | 9 | 2026-02-26 | 2026-09-16 |
| 9 | modern-python | 9 | 9 | 2026-01-26 | 2026-09-16 |
| 10 | sarif-parsing | 8 | 8 | 2026-01-14 | 2026-09-16 |
| 11 | aflpp | 7 | 8 | 2026-01-14 | 2026-09-16 |
| 12 | algorand-vulnerability-scanner | 7 | 7 | 2026-01-25 | 2026-09-16 |
| 13 | cairo-vulnerability-scanner | 7 | 7 | 2026-01-25 | 2026-09-16 |
| 14 | graph-evolution | 7 | 7 | 2026-03-31 | 2026-09-16 |
| 15 | solana-vulnerability-scanner | 7 | 7 | 2026-01-25 | 2026-09-16 |
| 16 | supply-chain-risk-auditor | 7 | 7 | 2026-02-26 | 2026-09-16 |
| 17 | trailmark | 7 | 7 | 2026-03-31 | 2026-09-16 |
| 18 | trailmark-structural | 7 | 7 | 2026-03-31 | 2026-09-16 |
| 19 | trailmark-summary | 7 | 7 | 2026-03-31 | 2026-09-16 |
| 20 | testing-handbook-generator | 6 | 7 | 2026-01-14 | 2026-09-16 |

### expo/skills

HEAD d4f4840 2026-10-05 · 142 commits · 107 with a PR number

| # | Skill | PRs | Commits | First change | Last change |
|---|---|---|---|---|---|
| 1 | eas-simulator | 26 | 26 | 2026-07-01 | 2026-10-05 |
| 2 | upgrading-expo | 10 | 16 | 2026-01-14 | 2026-07-07 |
| 3 | building-native-ui | 10 | 15 | 2026-01-20 | 2026-07-07 |
| 4 | expo-module | 10 | 10 | 2026-04-02 | 2026-10-02 |
| 5 | expo-brownfield | 9 | 9 | 2026-05-19 | 2026-10-02 |
| 6 | eas-update-insights | 8 | 8 | 2026-04-23 | 2026-10-02 |
| 7 | expo-dev-client | 8 | 8 | 2026-01-20 | 2026-10-02 |
| 8 | expo-examples | 7 | 7 | 2026-06-18 | 2026-10-02 |
| 9 | expo-native-ui | 7 | 7 | 2026-07-07 | 2026-10-02 |
| 10 | expo-tailwind-setup | 7 | 7 | 2026-01-20 | 2026-08-31 |
| 11 | expo-ui | 7 | 7 | 2026-06-12 | 2026-10-02 |
| 12 | expo-ui-jetpack-compose | 7 | 7 | 2026-02-26 | 2026-06-12 |
| 13 | expo-upgrade | 7 | 7 | 2026-07-07 | 2026-10-02 |
| 14 | native-data-fetching | 7 | 7 | 2026-01-20 | 2026-07-07 |
| 15 | expo-overview | 6 | 7 | 2026-08-20 | 2026-10-02 |
| 16 | eas-app-stores | 6 | 6 | 2026-07-07 | 2026-10-02 |
| 17 | eas-workflows | 6 | 6 | 2026-07-07 | 2026-10-02 |
| 18 | expo-router | 6 | 6 | 2026-07-06 | 2026-10-02 |
| 19 | expo-web-to-native | 6 | 6 | 2026-07-07 | 2026-10-02 |
| 20 | eas-observe | 5 | 5 | 2026-07-07 | 2026-10-02 |

### czlonkowski/n8n-skills

HEAD cb6caa7 2026-10-09 · 96 commits · 18 with a PR number

| # | Skill | PRs | Commits | First change | Last change |
|---|---|---|---|---|---|
| 1 | n8n-mcp-tools-expert | 4 | 38 | 2025-10-20 | 2026-09-03 |
| 2 | n8n-validation-expert | 4 | 22 | 2025-10-20 | 2026-09-16 |
| 3 | n8n-workflow-patterns | 5 | 18 | 2025-10-20 | 2026-09-16 |
| 4 | n8n-node-configuration | 6 | 17 | 2025-10-20 | 2026-09-03 |
| 5 | n8n-code-javascript | 3 | 14 | 2025-10-20 | 2026-09-16 |
| 6 | n8n-code-python | 3 | 12 | 2025-10-20 | 2026-09-16 |
| 7 | n8n-expression-syntax | 3 | 10 | 2025-10-20 | 2026-09-16 |
| 8 | n8n-self-hosting | 1 | 7 | 2026-06-18 | 2026-09-16 |
| 9 | n8n-code-tool | 2 | 4 | 2026-04-21 | 2026-07-06 |
| 10 | n8n-agents | 1 | 4 | 2026-06-18 | 2026-08-29 |
| 11 | n8n-error-handling | 1 | 2 | 2026-06-18 | 2026-09-16 |
| 12 | n8n-subworkflows | 1 | 2 | 2026-06-18 | 2026-08-29 |
| 13 | n8n-binary-and-data | 0 | 1 | 2026-06-18 | 2026-06-18 |
| 14 | n8n-multi-instance | 0 | 1 | 2026-06-18 | 2026-06-18 |

### supabase/agent-skills

HEAD c9be0e9 2026-10-02 · 96 commits · 69 with a PR number

| # | Skill | PRs | Commits | First change | Last change |
|---|---|---|---|---|---|
| 1 | supabase | 18 | 18 | 2026-04-05 | 2026-10-02 |
| 2 | supabase-postgres-best-practices | 17 | 17 | 2026-01-26 | 2026-07-30 |
| 3 | postgres-best-practices | 6 | 17 | 2026-01-19 | 2026-01-26 |
| 4 | using-supabase | 2 | 2 | 2026-01-26 | 2026-01-26 |
| 5 | postgresql-best-practices | 0 | 2 | 2026-01-16 | 2026-01-16 |

### remotion-dev/skills

HEAD 7ba4dcf 2026-10-12 · 89 commits · 0 with a PR number

| # | Skill | PRs | Commits | First change | Last change |
|---|---|---|---|---|---|
| 1 | remotion-best-practices | 0 | 42 | 2026-07-11 | 2026-10-12 |
| 2 | remotion-markup | 0 | 41 | 2026-07-11 | 2026-10-12 |
| 3 | remotion-interactivity | 0 | 39 | 2026-07-11 | 2026-10-12 |
| 4 | remotion-create | 0 | 37 | 2026-07-11 | 2026-10-12 |
| 5 | remotion-maps | 0 | 36 | 2026-07-24 | 2026-10-12 |
| 6 | remotion-captions | 0 | 35 | 2026-07-11 | 2026-10-12 |
| 7 | remotion-docs | 0 | 35 | 2026-07-16 | 2026-10-12 |
| 8 | remotion-render | 0 | 34 | 2026-07-11 | 2026-10-12 |
| 9 | remotion-saas | 0 | 34 | 2026-07-11 | 2026-10-12 |
| 10 | remotion-upgrade | 0 | 34 | 2026-07-19 | 2026-10-12 |
| 11 | remotion-multimedia | 0 | 33 | 2026-07-27 | 2026-10-12 |
| 12 | remotion | 0 | 31 | 2026-01-19 | 2026-07-11 |
| 13 | remotion-studio | 0 | 29 | 2026-08-04 | 2026-10-12 |
| 14 | mediabunny | 0 | 4 | 2026-01-19 | 2026-07-18 |
| 15 | 3d | 0 | 3 | 2026-01-19 | 2026-01-19 |
| 16 | sequencing | 0 | 3 | 2026-01-19 | 2026-01-19 |
| 17 | charts | 0 | 2 | 2026-01-19 | 2026-01-19 |
| 18 | example-animated-shapes | 0 | 2 | 2026-01-19 | 2026-01-19 |
| 19 | example-chat-messages | 0 | 2 | 2026-01-19 | 2026-01-19 |
| 20 | example-counter | 0 | 2 | 2026-01-19 | 2026-01-19 |

### hashicorp/agent-skills

HEAD f706481 2026-09-28 · 67 commits · 48 with a PR number

| # | Skill | PRs | Commits | First change | Last change |
|---|---|---|---|---|---|
| 1 | terraform-stacks | 7 | 14 | 2025-11-20 | 2026-08-10 |
| 2 | refactor-module | 7 | 13 | 2025-11-10 | 2026-08-26 |
| 3 | terraform-style-guide | 7 | 13 | 2025-11-20 | 2026-08-10 |
| 4 | terraform-policy | 5 | 5 | 2026-07-15 | 2026-09-28 |
| 5 | terraform-search-import | 5 | 5 | 2026-03-03 | 2026-08-10 |
| 6 | terraform-test | 4 | 10 | 2025-11-20 | 2026-08-10 |
| 7 | new-terraform-provider | 4 | 5 | 2026-01-14 | 2026-08-10 |
| 8 | build-image | 3 | 4 | 2025-11-21 | 2025-12-16 |
| 9 | generate-template | 3 | 4 | 2025-11-21 | 2025-12-16 |
| 10 | hcp-registry-ops | 3 | 4 | 2025-11-21 | 2025-12-16 |
| 11 | run-acceptance-tests | 3 | 4 | 2026-01-14 | 2026-08-10 |
| 12 | provider-docs | 3 | 3 | 2026-04-01 | 2026-08-10 |
| 13 | provider-test-patterns | 3 | 3 | 2026-03-19 | 2026-08-10 |
| 14 | generate-hcl | 2 | 8 | 2025-11-10 | 2026-01-19 |
| 15 | configure-service-mesh | 2 | 4 | 2025-11-10 | 2025-12-16 |
| 16 | provider-actions | 2 | 3 | 2026-01-26 | 2026-08-10 |
| 17 | aws-ami-builder | 2 | 2 | 2026-01-29 | 2026-08-10 |
| 18 | azure-image-builder | 2 | 2 | 2026-01-29 | 2026-08-10 |
| 19 | push-to-registry | 2 | 2 | 2026-01-29 | 2026-08-10 |
| 20 | windows-builder | 2 | 2 | 2026-01-29 | 2026-08-10 |

### anthropics/skills

HEAD dbd4588 2026-10-09 · 60 commits · 59 with a PR number

| # | Skill | PRs | Commits | First change | Last change |
|---|---|---|---|---|---|
| 1 | claude-api | 31 | 31 | 2026-03-04 | 2026-10-09 |
| 2 | docx | 5 | 5 | 2025-12-01 | 2026-07-16 |
| 3 | pptx | 5 | 5 | 2025-12-01 | 2026-07-16 |
| 4 | skill-creator | 5 | 5 | 2025-12-01 | 2026-04-20 |
| 5 | frontend-design | 4 | 4 | 2025-12-01 | 2026-09-03 |
| 6 | xlsx | 4 | 4 | 2025-12-01 | 2026-07-16 |
| 7 | pdf | 3 | 3 | 2025-12-01 | 2026-02-06 |
| 8 | slack-gif-creator | 3 | 3 | 2025-12-01 | 2026-04-20 |
| 9 | algorithmic-art | 2 | 2 | 2025-12-01 | 2026-04-20 |
| 10 | brand-guidelines | 2 | 2 | 2025-12-01 | 2026-04-20 |
| 11 | canvas-design | 2 | 2 | 2025-12-01 | 2026-04-20 |
| 12 | internal-comms | 2 | 2 | 2025-12-01 | 2026-04-20 |
| 13 | mcp-builder | 2 | 2 | 2025-12-01 | 2026-04-20 |
| 14 | theme-factory | 2 | 2 | 2025-12-01 | 2026-04-20 |
| 15 | web-artifacts-builder | 2 | 2 | 2025-12-01 | 2026-04-20 |
| 16 | webapp-testing | 2 | 2 | 2025-12-01 | 2026-04-20 |
| 17 | academy-guide | 1 | 1 | 2026-08-18 | 2026-08-18 |
| 18 | claude-academy-guide | 1 | 1 | 2026-08-17 | 2026-08-17 |
| 19 | discernment-nudge | 1 | 1 | 2026-08-17 | 2026-08-17 |
| 20 | doc-coauthoring | 1 | 1 | 2025-12-04 | 2025-12-04 |

### kepano/obsidian-skills

HEAD 3ccff53 2026-09-15 · 49 commits · 16 with a PR number

| # | Skill | PRs | Commits | First change | Last change |
|---|---|---|---|---|---|
| 1 | obsidian-bases | 6 | 6 | 2026-01-09 | 2026-04-07 |
| 2 | json-canvas | 4 | 4 | 2026-01-09 | 2026-02-25 |
| 3 | obsidian-markdown | 4 | 4 | 2026-01-09 | 2026-03-22 |
| 4 | defuddle | 2 | 4 | 2026-02-10 | 2026-09-09 |
| 5 | obsidian-cli | 1 | 2 | 2026-02-10 | 2026-02-25 |
| 6 | knap | 0 | 1 | 2026-09-10 | 2026-09-10 |
