---
commissioned-by: spacedock@0.27.2
entity-type: skill_commit_case
entity-label: case
entity-label-plural: cases
id-style: sd-b32
state: .spacedock-state
stages:
  # Stage names must match ^[a-z0-9][a-z0-9-]*[a-z0-9]$ (kebab-case lowercase, no underscores or spaces); `status --validate` rejects others.
  defaults:
    worktree: false
    concurrency: 2
  states:
    - name: candidate
      initial: true
    - name: intent
      gate: true
      feedback-to: candidate
    - name: run
      fresh: true
    - name: verification
      fresh: true
      gate: true
      feedback-to: run
    - name: done
      terminal: true
---

# Replay public skill commits with Behavior Diff, and check whether the report makes the commit's real intent easy to see

Each case is one Before → After commit pair of a public skill, picked from
[`plans/2026-09-29-public-skill-history-sources.md`](../../plans/2026-09-29-public-skill-history-sources.md).
First we read the commit and its related PR comments and write down the
author's intent. That is the **ground truth**. Then we replay the commit with
the Behavior Diff skill exactly as a user would: the Before revision is
committed in a scratch fixture repo, the After revision is an uncommitted
edit, and the skill drafts its own scenario and runs it. Last, a fresh verifier
uses Jev to compare both the scenario Behavior Diff drafted and its report
against the ground truth. The output of this workflow is evidence about the
Behavior Diff skill, not about the upstream skill: a `missed` result is a
valid, useful finding.

```
candidate ─► intent ─────────► run ──────────────────► verification ─► done
             commit + PR        Behavior Diff skill     Jev compares:
             comments →         drafts its OWN task     ① BD's task   vs ground truth
             GROUND TRUTH       (never sees the         ② BD's report vs ground truth
             [gate]             ground truth) [fresh]   [gate, fresh]
  reject at intent       → back to candidate
  reject at verification → back to run
```

For every gated stage, add `- **Gate content:**` to its stage subsection and state the evidence needed for that decision. This rule also applies to custom stages and template variants.

## File Naming

Each case lives as either:

- a flat markdown file `{slug}.md` (default — use this unless the case produces many artifacts), or
- a folder `{slug}/` containing `index.md` as the canonical entity file. The `intent` stage converts each case to this form (`git mv {slug}.md {slug}/index.md`) and writes the ground truth to `{slug}/ground-truth.md`, outside `index.md`, so a worker that reads the case file does not see it. The `run` stage stores the Behavior Diff report in `{slug}/report/`.

Slugs are lowercase, hyphens, no spaces, and name the skill plus the After
commit prefix. Example: `openai-skill-installer-49f948f.md`. The status scanner
recognizes both forms; `--set` and `--archive` resolve the slug either way, and
folder entities archive as a whole folder into the workflow's archive directory.

## Schema

Every case file has YAML frontmatter. Fields are documented below; see **Case Template** for a copy-paste starter.

### Field Reference

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique identifier, format determined by id-style in README frontmatter |
| `title` | string | Human-readable case name (skill + After commit prefix) |
| `status` | enum | One of: candidate, intent, run, verification, done |
| `source` | string | Where this case came from (plan section, history link) |
| `started` | ISO 8601 | When active work began |
| `completed` | ISO 8601 | When the case reached terminal status |
| `verdict` | enum | PASSED or REJECTED — set at final stage. PASSED = the case finished with a trustworthy `catch` value (any value, including `missed`). REJECTED = the case was dropped (not replayable, license hold, broken run). |
| `score` | number | Priority score, 0.0–1.0 (optional) |
| `worktree` | string | Worktree path while a dispatched agent is active, empty otherwise |
| `issue` | string | GitHub issue reference (e.g., `#42` or `owner/repo#42`). Optional cross-reference, set manually. |
| `pr` | string | GitHub PR reference. Set when a PR is created for this entity's worktree branch. |
| `repo` | string | Canonical upstream repository, `owner/name` |
| `skill_path` | string | Path of the changed instruction file in the After commit |
| `before_sha` | string | Full Before SHA (first parent of the After commit unless the plan says otherwise) |
| `after_sha` | string | Full After SHA |
| `pr_ref` | string | Upstream PR that introduced `after_sha` (`owner/repo#N`), or `none` |
| `scenario_match` | enum | `on-target`, `near`, `off-target` — Jev's verdict on Behavior Diff's drafted task vs the ground truth |
| `catch` | enum | `caught`, `partial`, `missed`, or `inconclusive` — Jev's verdict on the report vs the ground truth |
| `report` | string | Report copy on the local-only state branch (`{slug}/report/report.html`) |
| `run_dir` | string | Original runner output directory under `~/.behavior-diff/runs/` (raw trials stay there) |

### ID Style

The `id-style` frontmatter setting controls the operator-facing ID strategy:

- `sequential`: `id` is required and stores the next zero-padded numeric value from `status --next-id`, counting active and archived entities.
- `sd-b32`: `id` is required and stores the full stable 24-character lowercase SD-B32 stored ID from `status --next-id --id-seed <slug-or-title>`. SD-B32 is Spacedock Base32: SHA-256 digest material formatted with Spacedock's human-safe alphabet `0123456789abcdefghjkmnpqrstvwxyz`. Status tables show shorter display/address prefixes computed from active plus archived entities. `status --boot` reports `ID_STYLE: sd-b32`, `NEXT_ID: {candidate}`, and `MIN_PREFIX: 2`.
- `slug`: `id` is optional; the effective ID is the entity slug. `status --next-id is not applicable for id-style: slug` because the slug comes from the title.

SD-B32 display/address prefixes can lengthen after another branch adds a colliding prefix, while stored IDs remain stable. Use `status --validate` before trusting workflow state and `status --resolve <ref>` to resolve slugs, stored IDs, or sd-b32 address prefixes.

Copyable README frontmatter examples:

```yaml
id-style: sequential
```

```yaml
id-style: sd-b32
```

```yaml
id-style: slug
```

SD-B32 examples:

| Workflow size | Stored `id` examples | Display/address examples |
| --- | --- | --- |
| 10s of entities | `4k9q2m7x8c3v9r5t6w2p0n1h`, `8t5n0p2w6j9r4c8x1m7q3v5k` | `4k`, `8t` |
| 100s of entities | `9m2c7v4xq8j3h6t0p5w1r8n2`, `9m2cq8j3h6t0p5w1r8v7x4kn` | `9m2c7`, `9m2cq` |
| 1000s of entities | `v7k3q9x2m5c8h6t0p1w4r8n2`, `v7k3qrv5t9p3j6n2w8c4x1mk` | `v7k3q9`, `v7k3qr` |

Generated IDs make concurrent and offline creation safer because creators do not share a central counter. Migration from existing sequential workflows is manual migration in this release: validate the target style, update README/entity frontmatter deliberately, and defer rewrite automation to a separate tracked task.

## Stages

### `candidate`

The holding bucket. The captain or first officer adds a commit pair from the
plan with `repo`, `skill_path`, `before_sha`, and `after_sha` filled. No worker
runs here: the first dispatch for a case is the `intent` stage, which checks
the candidate first.

### `intent`

A worker first checks that the case is a replayable, single-file behavior
change. If it is, the worker reads the upstream commit and its related PR
discussion and writes down the author's intent. That text is the **ground
truth** the Behavior Diff output is later compared against. The captain
approves it, and the cost of the coming run, before any model money is spent.

- **Inputs:** The plan entry for this skill (repo, license, skill path, observed pair, requirements and limits); the upstream commit and its first parent, fetched with `git fetch --depth 2` into a scratch directory outside this repo; the PR that introduced it, found with `gh api repos/<repo>/commits/<after_sha>/pulls`, including its description, review comments, and linked issues.
- **Outputs:**
  - **Step 1 — candidate checks**, in a `## Candidate checks` section. Stop after this step and recommend REJECTED if any check fails.
    - `before_sha` confirmed equal to `git rev-parse <after_sha>^`.
    - Changed-file list from `git diff --name-only <before_sha> <after_sha> -- <skill dir>`. If more than one instruction file changed, record which one is under test and why the others do not matter, or fail the check.
    - License recorded with a link; custom, mixed, or missing licenses fail the check.
    - A Jev Noul judgment (via `typesafe:typesafe-ai`): "Does this patch change what an agent would do, rather than wording, formatting, or packaging?" Probability recorded; below 0.5 fails the check.
  - **Step 2 — ground truth.**
    - `pr_ref` set to the PR (`owner/repo#N`), or `none` if the commit has no PR.
    - The case converted to folder form, and the ground truth written to `{slug}/ground-truth.md` (never into `index.md`): two to four claims on what agent behavior the author meant to change, and the situation where the change matters (the decision moment). Each claim is labeled [said] or [inferred] and cites its source: commit message, patch line, or PR comment link. Supporting detail (PR lookup, reviews, companion PRs) goes in a `## Sources` section of the same file, not in the claims.
    - `index.md` names the file (`Ground truth: see ground-truth.md`) and holds no ground-truth text.
    - A clear split between what the sources **say** and what the worker **infers**. With no PR and a one-line commit message, most of it is inference — say so and mark the ground truth "weak".
    - The planned run settings in a `## Planned run settings` section of `index.md` (never in `ground-truth.md`, which the `run` worker does not read): host and model (per the `run` stage's host rule) and the trial count (default 3+3 headless).
- **Gate content:** Show the candidate checks (with the Jev probability), the ground truth with its sources, the said-vs-inferred split, `pr_ref`, and the planned run settings. The captain checks that the ground truth is fair to the author and approves the run spend.
- **Good:** Every fact is checked against git, not copied from the plan; the single-file check is code, never a judgment call. Every ground-truth claim traces to a commit line or PR comment. Uncertainty is stated, not smoothed over.
- **Bad:** Running or installing any upstream script or hook. Admitting a multi-file commit as if it were single-file. Copying the plan's summary as the ground truth. Guessing intent from the patch alone when a PR discussion exists. Writing a test scenario here — Behavior Diff drafts that itself.

### `run`

A fresh worker runs the Behavior Diff skill on the commit exactly as a user
would, and lets the skill draft its own scenario. The worker reads `index.md`
only and never opens `{slug}/ground-truth.md`.

- **Inputs:** `repo`, `skill_path`, `before_sha`, `after_sha`, and the approved run settings in `index.md`. **Not** `ground-truth.md`.
- **Outputs:**
  - A scratch fixture git repo outside this repo: the Before revision (`git show <before_sha>:<skill_path>`) committed at the path the host loads repo skills from, then the After revision written over it as an uncommitted edit. No upstream install, no upstream scripts.
  - Host matches the skill's home host: Codex skills (e.g. `openai/skills`) run with `--agent codex` at `.agents/skills/<name>/SKILL.md`; others run with `--agent claude` at `.claude/skills/<name>/SKILL.md`. A Codex run starts a full-access `codex exec` session, which Claude Code's permission check blocks unless the captain has added an allow rule (see **Local setup**). Without that rule, stop and ask the captain; the fallback is the Claude host, recorded in the body as a captain-directed plan change.
  - The user-level skills and plugins the trial host loaded, listed in the body. They are not removed for the pilot; the list lets the verifier spot interference.
  - The `behavior-diff:behavior-diff` skill invoked from inside that fixture, in a separate headless session. The neutral prompt already answers the skill's real-incident question, because a headless session cannot be answered mid-run: `/behavior-diff:behavior-diff Run a behavior diff on my uncommitted SKILL.md change. If you need a real incident: none — draft the task from the diff.` Do not suggest a task.
  - The exact `--task` text the skill drafted, copied into a `## Drafted scenario` section.
  - A check that each side loaded the intended revision (the report's git diff matches `git diff <before_sha> <after_sha> -- <skill_path>`).
  - `report.html`, `report.md`, and `decisions.json` copied from the runner output into `{slug}/report/` on the state branch. The raw `before-*` / `after-*` trial folders are not copied.
  - `report` and `run_dir` set, plus a short plain summary of the decision diff in `index.md`.
- **Good:** The skill runs unassisted, so the result shows what a real user would get. A blocked or inconclusive run is recorded as-is with its reason.
- **Bad:** Opening `ground-truth.md` or the plan's notes before or during the run. Editing the skill's drafted task. Copying raw trial folders, or committing any report to `main`. Re-running until the result looks good.

### `verification`

A fresh verifier agent — one that did not write the ground truth or run the
trials — uses Jev to compare Behavior Diff's output against the ground truth.
The captain approves the verdict.

- **Inputs:** `{slug}/ground-truth.md`, `## Drafted scenario` in `index.md`, and the report copy in `{slug}/report/`. Jev state uses `report.md` and `decisions.json`, not `report.html`, so the verdict judges the report's text content, not its page layout.
- **Outputs:**
  - **Judge ① — scenario.** A Jev Choice call via `typesafe:typesafe-ai`. State: the ground truth and the drafted task. Question: "Does this task put the agent in the situation where the author's change matters?" Options: `on-target`, `near` (related situation, but the changed rule may not decide the outcome), `off-target`. Every option's probability recorded; `scenario_match` set to the top choice.
  - **Judge ② — report.** A Jev Choice call. State: the ground truth and the report's decision diff and flow diff summary. Question: "Does this report make the author's intended behavior change easy for a reader to see?" Options: `caught`, `partial` (visible but mixed with noise or only on some trials), `missed`, `inconclusive` (the run was blocked or never reached the decision moment). Every probability recorded; `catch` set to the top choice.
  - Any top probability below 0.6 → that verdict marked "uncertain" for the captain.
  - Both calls, their questions, and every probability written in a `## Jev judgment` section of `index.md`.
  - One or two plain sentences on what made the intent easy or hard to see. This is the feedback for the Behavior Diff skill. An `off-target` scenario with `missed` points at task drafting; an `on-target` scenario with `missed` points at the report.
- **Gate content:** Show the ground truth, the drafted task, both Jev choices with all probabilities, the report path, and the one-line feedback. The captain accepts or rejects back to `run`.
- **Good:** Both judge calls are Jev, not the verifier's own opinion. `missed` and `off-target` are reported plainly.
- **Bad:** Rewriting the ground truth to fit the report. Replacing a Jev call with free-text judgment. Treating `missed` as a failed case.

### `done`

Terminal. `completed` is set. `verdict: PASSED` when `catch` is trustworthy
(any value), `REJECTED` when the case was dropped. The body keeps why.

## Workflow-specific rules

The FO/ensign operating contract already governs generic stage semantics and proof discipline: prefer the cheapest check that can fail, prove by exercising rather than re-reading, and fix success criteria before gathering evidence. The rules below add only this workflow's specifics.

- **Every judge call uses Jev.** Whenever the first officer or a worker must make a judgment, load the `typesafe:typesafe-ai` skill and ask Jev a typed question (Noul, Choice, or Score) instead of deciding in free text. This covers the stage judgments (is this a behavior change? does the report catch the intent?) and the first officer's own checks: whether each acceptance criterion is met, whether each stage-output checklist item is done, and the PASSED/REJECTED recommendation shown at a gate. Ask one Noul per AC or checklist item, with the item text and its evidence as state. Record every question and probability in the case body. Exact facts (SHAs, changed-file lists, file equality, command exit codes) stay in code. The final gate decision stays with the captain.
- **Ground truth never leaks into the run.** The ground truth is written before the run, in its own file `{slug}/ground-truth.md`, so the dispatch's "read the case file" step does not expose it. The `run` worker never opens that file, and it starts the Behavior Diff skill in a separate headless session given only a neutral prompt. The skill drafts its own task, unassisted.
- **Before/After come from git, not installs.** Both revisions are read with `git show`; the fixture repo holds Before as HEAD and After as an uncommitted edit. Upstream scripts and hooks are untrusted and never run.
- **Model cost is approved first.** No Behavior Diff run happens before the captain approves the `intent` gate. CI never runs any of this.
- **The state branch is local-only.** `spacedock-state/skill-history-replay` holds case files and report copies, so it falls under `AGENTS.md` invariant 4. The state checkout is its own clone whose `origin` is the local bare repo `~/.behavior-diff/replay-state.git`; Spacedock's normal state sync pushes there, and that is expected. Never push it to a network remote and never merge it into `main`. The main repo's `pre-push` hook refuses any push of this branch to a non-local URL; do not bypass it with `--no-verify`. Raw trial folders stay under `~/.behavior-diff/runs/`. Fixtures are synthetic.
- **One to two commits per skill.** Do not add more than two cases for the same skill until each existing case for it is `done`.

## Local setup

This workflow runs on one machine. A fresh clone has the README but no state,
and needs this one-time setup before `spacedock claude` can run it:

```bash
# 1. Private bare repo that acts as the state checkout's origin
git init --bare ~/.behavior-diff/replay-state.git

# 2. State checkout: a clone of that bare repo at the gitignored state path
git clone ~/.behavior-diff/replay-state.git docs/skill-history-replay/.spacedock-state
#    (first time only: create the orphan branch spacedock-state/skill-history-replay
#     there, seed it, and push it to the bare repo)
```

3. Guard in the main repo. Save this as `.git/hooks/pre-push` and make it
   executable (`chmod +x`). It refuses to push the state branch to any
   network remote. Pushes to a local path, and pushes of every other branch,
   pass through unchanged.

```bash
#!/usr/bin/env bash
# Local-only guard: the skill-history-replay state branch holds Behavior Diff
# reports (AGENTS.md invariant 4). It may go to a local path, never a network remote.
url="$2"
case "$url" in /* | file://*) exit 0 ;; esac
while read -r local_ref _ remote_ref _; do
  case "$local_ref $remote_ref" in
    *spacedock-state/skill-history-replay*)
      echo "pre-push: refusing to push spacedock-state/skill-history-replay to $url (local-only, holds reports)" >&2
      exit 1
      ;;
  esac
done
exit 0
```

The state checkout must be its own clone, not a linked worktree of the main
repo: Spacedock syncs state with the checkout's `origin`, and a linked
worktree shares the main repo's GitHub `origin`.

Also needed: a `TYPESAFE_API_KEY` for Jev, and the Behavior Diff plugin
installed on the trial host. Codex-host runs also need the captain to add a
Claude Code allow rule for the full-access session, for example
`Bash(codex exec -s danger-full-access --skip-git-repo-check --json:*)` in
`.claude/settings.local.json`. That rule lets a nested agent run without a
sandbox, so remove it when it is not in use.

## Workflow State

Workflow state is read by the first officer at boot. To view current state, dispatch the first officer or run it directly:

```
spacedock claude
```

## Case Template

```yaml
---
id:
title: Skill name @ after-prefix
status: candidate
source:
started:
completed:
verdict:
score:
worktree:
issue:
pr:
repo:
skill_path:
before_sha:
after_sha:
pr_ref:
scenario_match:
catch:
report:
run_dir:
---

What this commit pair is and why it was picked from the plan.

## Acceptance criteria

Each AC names a property of the finished case (not a stage action) and how it is verified.

**AC-1 — Before and After are the real commit pair.**
Verified by: `git rev-parse <after_sha>^` equals `before_sha`, and the report's git diff for `skill_path` matches `git diff <before_sha> <after_sha> -- <skill_path>`. A wrong SHA or a cached skill copy makes this fail.

**AC-2 — Both verdicts are recorded Jev judgments against a ground truth written before the run.**
Verified by: `{slug}/ground-truth.md` exists and was committed before the `run` stage's first commit, and `index.md` has a `Drafted scenario` section and a `Jev judgment` section with every option's probability for both calls; `scenario_match` and `catch` equal the top options. A missing probability table, or a verdict that differs from Jev's top choice, fails this.
```

## Commit Discipline

- Commit status changes at dispatch and merge boundaries
- Commit case body updates when substantive
