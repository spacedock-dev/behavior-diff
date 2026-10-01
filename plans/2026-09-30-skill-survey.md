# Skill survey for replay cases

**Recorded:** 2026-09-30
**Status:** Living shortlist. Update it after each survey round.
**Source list:** [Public skill history sources](2026-09-29-public-skill-history-sources.md), plus two search rounds of smaller and newer repositories.

## Selection filters

A commit pair is usable when all of these hold:

1. Exactly one instruction file changes inside the skill folder.
2. The change alters what the agent does during a task, not only wording.
3. A small local fixture can put the agent at the decision moment. Trials have
   no git history, branches, or remotes, and no logins or network writes.
4. The change is not only advice the agent tells the user, and the skill's job
   is not producing or installing a skill or package.
5. Before's text teaches a different behavior than After's, or After adds a
   rule that a strong model would not follow by default.
6. A commit body, pull request, or issue states the intent.
7. The repository has a clear open-source license.
8. No skill with the same purpose is installed on the trial host.

## Replayed or in the workflow

| Case | Commit | State | Note |
| --- | --- | --- | --- |
| Cloudflare `workers-best-practices` | `42839d0` | done, catch missed | Before already caught the planted mistakes |
| Hugging Face `huggingface-datasets` | `b3df145` | done, catch partial | Report noise sat next to the signal |
| OpenAI `skill-installer` | `49f948f` | dropped | Advice-only change; the real work needs an install |
| posit-dev `r-package-development` | `87093f6` | intent gate | Issue #55: the agent invented issue numbers |
| Matt Pocock `pr` | `35f5926` | intent gate | Evidence section asks for a failing then passing test |
| Microsoft `fastapi-router-py` | `8ae5031` | intent gate | Sync or async handler for a blocking call |
| Matt Pocock `tdd` | `80e9dcc` | intent gate | Refactor after green, or stop |
| daymade `git-safety-net` | `18174c8` | parked | Needs git history in trials; see [git history fixtures](2026-09-30-git-history-fixtures.md) |

## Candidates, not yet seeded

Ranked best first. All are MIT-licensed, and none are installed on the trial host.

| Rank | Skill | Before → After | Intent source | In-task decision |
| --- | --- | --- | --- | --- |
| 1 | addyosmani/agent-skills `planning-and-task-breakdown` | `df1edb2` → `8300e1b` | Issue #518, a real incident: the agent deleted an unfinished `plan.md` | Plan new work over an unfinished plan: overwrite, or stop and ask? |
| 2 | kepano/obsidian-skills `obsidian-bases` | `fa1e131` → `9b736ba` | PR #68, issue #58: Obsidian rejected the taught YAML | Mixed include and exclude filter: sibling keys, or nested? |
| 3 | blader/humanizer (repo-root `SKILL.md`) | `e2e92e7` → `c8e1872` | PR #264, issue #212: a rewrite lost ranking and simultaneity words | Keep "most", "only", and "at once" claims while rewriting? |
| 4 | addyosmani/agent-skills `documentation-and-adrs` | `98967c4` → `0d52faf` | Commit body | New ADR: fixed path and format, or match the existing convention? |
| 5 | EveryInc/compound-engineering-plugin `ce-compound-refresh` | `1f0a77b` → `e806522` | PR #713, a real incident: a deleted doc left 8 dangling links | Check inbound links before deleting a doc? |
| 6 | EveryInc/compound-engineering-plugin `ce-simplify-code` | `71d23d1` → `74624f8` | PR #749 | After a change: run the full suite, or scoped tests? |
| 7 | kepano/obsidian-skills `obsidian-bases` | `4540df8` → `41909ae` | PR #35 | Date math: millisecond division, or `.days`? |
| 8 | Jeffallan/claude-skills `terraform-engineer` | `10fe40c` → `d0e7f4e` | Issue #211 | Apply straight away, or wait for approval? (backup: needs a fake `terraform`) |

Per-candidate risks:

- **1:** A headless trial cannot ask. Score "stopped and reported the conflict" against "overwrote".
- **2 and 7:** Same skill; pick one at a time. Check the output by parsing the YAML.
- **3:** One-line change, so the effect may be small.
- **4:** After also asks the agent to scan open PRs; a trial may try `gh` and fail.
- **5:** Long skill that may start subagents.
- **6:** Name the file in the prompt, because a trial has no git diff.

## Rejected, with reasons

- Superpowers, gstack, Anthropic `skill-creator`, most Matt Pocock skills: installed on the trial host.
- Anthropic `skill-creator`: its job is producing a skill package.
- Supabase scoped tokens, Expo emulator: need a real platform login or device.
- Sentry, Supabase RLS, Vercel, Trail of Bits, HashiCorp, K-Dense, Marketing, n8n: the change spans several instruction files.
- Cloudflare `wrangler`: vendor-specific, and it retrieves live docs on both sides.
- Vercel `react-best-practices` index edit: only adds index lines for rules a model already knows.
- OthmanAdi/planning-with-files, pbakaus/impeccable: the skill is copied across many host folders.
- wshobson/agents, alirezarezvani/claude-skills, sveltejs/ai-tools: no single-skill behavior commits found.
- steipete/agent-scripts, affaan-m/ECC, github/awesome-copilot, dbt-labs/dbt-agent-skills: need GitHub, a vendor tool, or a non-canonical copy.
- NeoLabHQ/context-engineering-kit: GPL-3.0. multica-ai/andrej-karpathy-skills, rohitg00/pro-workflow: no license. tech-leads-club/agent-skills: unclear license.
