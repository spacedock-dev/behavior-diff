---
name: behavior-diff
description: Compare agent behavior before/after an uncommitted change to CLAUDE.md, AGENTS.md, or a skill file. Use for "behavior diff", "test my CLAUDE.md change", "did my rule change the agent's behavior", "before/after check on my rule edit".
---

# Behavior diff

Runs Behavior Diff on a local uncommitted instruction-file change. It starts
fresh headless agent trials with and without the change. The report shows the
git diff, a flow diff, and every trial's commands and final answer. There is
no automatic verdict. The user judges the evidence.

## Ownership

The skill owns judgment. It finds the change, freezes its purpose, prepares
the scenario, shared data, and private assessment criteria from the change's
intent, preflights and freezes the inputs, selects the current trial stack and
model, and explains the evidence against each goal and case.

The scripts own repeatable mechanics. They stage and verify prepared shared
data, build variants, run trials, normalize traces, grade completeness, extract
decisions, and render the report. No script generates a scenario or data.

The runner is bundled with this skill: `scripts/behavior-diff.sh` inside
this skill's base directory. Pass `--agent` for the stack under test:

- Claude Code: `--agent claude`. Trial execution defaults to `opus`.
- Codex: `--agent codex`. The model defaults to `sol`, a Behavior Diff selector.
  The runner resolves the newest visible stable `gpt-<version>-sol` from
  `codex debug models` once before launching trials. Both variants use that
  exact ID, which appears in the report. Pass `--model <exact-id>` to pin a
  version and bypass discovery. A catalog failure stops the run; never
  substitute a model or pass bare `sol` directly to Codex.
- Upstream Pi: `--agent pi --model <exact-current-pi-model>`.
- OMP: `--agent omp --model <exact-current-omp-model>`.

Decision extraction is a separate model call: Claude Code defaults to
`sonnet`, and Codex defaults to `luna`. The runner resolves Luna from the
same catalog by numeric version and records the exact extraction model.
With no overrides, extraction stays on the trial host. Do not inherit the
trial model for Claude or Codex extraction.

Honor `--extract-agent` and `--extract-model` overrides. An explicit extraction
host wins; otherwise a `sol` or `luna` extraction selector selects Codex.
Explicit Codex model IDs bypass discovery. If extraction cannot use the
selected model, present the trial evidence without a decision diff rather
than silently selecting another host or model.

Report narrative is written during that same extraction call. The scripts
include an installed Humanizer skill's prose guidance when available; otherwise
the extractor uses concise, natural technical prose. Extraction does not invoke
skill tools, add a model call, or install or download Humanizer. Report assembly
and rendering remain deterministic.

Never omit the Pi or OMP model. A user-specific default can test a different
agent. Your job is to prepare `--file` and `--task` well. Runs land under
`${BEHAVIOR_DIFF_HOME:-~/.behavior-diff}/runs/`.


**Spacedock workflow rule?** If the changed file is a spacedock workflow
doc (the repo contains `cmd/spacedock`, or the user says spacedock / FO /
ensign / gate), use Spacedock fixtures.
Spacedock fixtures are isolated before/after test repos. The real Spacedock
binary creates their workflow state. Do not create this state by editing files.
Before designing the run, read
`references/spacedock-duo.md` inside this skill's base directory. It chooses
the single-role or two-agent path. Create the fixtures with
`make-spacedock-fixtures.sh` from this skill's bundled `scripts/` directory.

## Steps

1. **Find the change.** In the user's current git repo, run
   `git status --porcelain` and keep only modified instruction files
   (CLAUDE.md, AGENTS.md, SKILL.md, agent-facing README.md). Exactly one
   candidate: use it. Several: ask the user which one. None: explain that
   the change must exist as an uncommitted edit first, and stop.
   Then read `git diff -- <file>` so you understand what rule changed.
   Read the selected instruction and its relevant unchanged references before
   deriving the intent; a diff alone may omit behavior that must be preserved.

   Three cases have no git "before", and each still works:
   - **Untracked file** (git does not know it — e.g. `~/.claude/CLAUDE.md`):
     the plugin's backup hook saved the pre-edit original under
     `${BEHAVIOR_DIFF_HOME:-~/.behavior-diff}/baselines/`, and the runner
     resolves the newest one by itself — run it with the same arguments.
     A parallel session may have saved a newer baseline than the change
     you mean to test; if the report's diff looks too small, pick the
     right entry from that store and pass it as `--before-file`.
     If the runner exits saying no baseline exists, ask the user for the
     original content and pass it as `--before-file <path>`.
   - **User-given before/after files** ("compare A.md and B.md"):
     run with `--file B.md --before-file A.md`.
   - **Non-git folder**: the runner builds both sandboxes from a plain
     copy of the working folder instead of a HEAD snapshot. Every trial
     copies the whole folder, so run from the smallest folder that holds
     the file; the "before" still needs a baseline or `--before-file`.

   In these cases read the change with `diff <before> <file>` instead of
   `git diff`.

   **Historical context boundary.** Before deriving historical purpose, read
   the source-isolation rule in `references/scenario-and-test-data.md`. If this
   session already knows later history or previous trial outcomes, purpose
   derivation and preparation must use the fresh context described there.
   If that isolation is unavailable, stop; disclosure alone is not a substitute.

   **Freeze the purpose before drafting or running trials.** Derive concise,
   distinct goals from the current conversation and the selected diff without
   asking the owner to restate their reason. Use one or two sentences per goal;
   keep separate goals separate, including behavior meant to survive a cleanup.
   On both Claude Code and Codex, use the conversation already available in the
   current context, including supplied summaries; do not open host transcript
   stores, resume other sessions, or infer access to missing turns. The same
   rule applies when orchestrating Pi or OMP.

   For an already-supported historical comparison prepared with
   `--before-file` or isolated replay fixtures, use the relevant selected commit
   message and diff instead of the current session's motives. Do not use later
   commits or trial results to invent the original reason. This does not add a
   committed-edit invocation mode.

   Write only the derived goals to a private scratch JSON file outside the
   project. Create the scratch directory with mode `0700` and the JSON file
   with mode `0600` before writing it; never use a shared or synced directory.
   Use this contract:

       {"goals":[{"text":"Prevent unsupported promises in the draft.","source":"session","basis":"explicit","reference":"Current conversation: owner-stated reason for the selected edit"}]}

   `source` is `session`, `commit`, or `diff`; `basis` is `explicit` when the
   available owner statement or commit message states the goal, otherwise
   `inferred`. Use a neutral reference such as `Current conversation: selected
   edit`, `Commit <sha>: message`, or `Diff: selected instruction change`;
   never quote a conversation or commit message in the reference. If session
   context or commit history supplies no usable reason, infer the observable
   goal from the selected diff alone with `source:"diff", basis:"inferred"`.
   Never invent incident history. A purpose file may be `null` if no safe,
   meaningful goal can be derived. The runner accepts at most eight distinct
   goals, 1,200 characters per goal and 240 per reference, with no control
   characters. Do not merge extra goals just to fit a limit; narrow the selected
   change before running when necessary.

   **Privacy and consent come before the handoff.** A derived goal can still
   expose secrets or private context. Include only the observable behavior of
   this edit, not names, emails, credentials, identifiers, private URLs, source
   excerpts, unrelated work, or raw session text. Generalize the behavior, not
   sensitive values. If safe generalization loses the question, use a neutral
   diff-inferred goal or `null`; never silently send sensitive context.
   Explain before running that the derived purpose and bounded recorded
   read/search tool returns go to the configured assessment provider and may
   appear in local reports. A request to compare an edit permits this limited,
   non-sensitive handoff, not transmission of additional private session data.
   If the run requires sensitive purpose or source content, stop and obtain
   specific approval for that content or a safe fixture; normal automatic
   execution below does not override this boundary. Conservative exclusions
   are not a guarantee that all secrets or private prose will be detected.
   Freeze the file now; never revise goals after seeing Before/After results.

   **Capture source provenance only for a historical comparison.** It applies
   when each instruction version comes from a verified commit of one original
   repository. Exact files and content-preserving assembly of selected source
   fragments are eligible; for assembly, retain the source-path mapping and
   explain the tested scope in the report context. The links identify source
   revisions, not a claim that the whole PR was exercised. Read provenance from
   the original repository, never a sandbox or fixture repository or its
   `origin` remote:
   - `repository_url`: the canonical HTTPS web URL of that repository, such as
     `gh repo view <owner>/<repo> --json url` or `glab repo view <path>`. Never
     include credentials, a port, a query, or a fragment.
   - `before_commit` and `after_commit`: full 40- or 64-hex IDs from
     `git rev-parse --verify <rev>^{commit}` in the original checkout. Confirm
     each one is in the named repository with available host tooling, such as
     `gh api repos/<owner>/<repo>/commits/<sha>` or
     `glab api projects/<url-encoded-path>/repository/commits/<sha>`, or with
     `git branch -r --contains <sha>` on a fetched remote of that repository.
   - `pull_requests` (optional): only GitHub PRs or GitLab MRs that the host
     associates with an exact commit, such as
     `gh api repos/<owner>/<repo>/commits/<sha>/pulls` or
     `glab api projects/<url-encoded-path>/repository/commits/<sha>/merge_requests`.
     Set `applies_to` to `before`, `after`, or `both`. Copy the host's number,
     title, and URL.
   - `forge`: `github` or `gitlab`. It is required for a self-hosted host;
     the runner infers it only for `github.com` and `gitlab.com`.

   Do not install host tooling. If no tool verifies an association, omit that
   PR or MR; never infer one from a branch name or commit message. If the
   repository or either commit cannot be verified, or the instructions include
   changes not present in that side's source revision (such as uncommitted local
   edits), omit the whole source file; never fabricate a commit. Write the JSON
   to the same private scratch directory as the purpose, with mode `0600`:

       {"repository_url":"https://github.com/owner/repo","before_commit":"<40-hex>","after_commit":"<40-hex>","pull_requests":[{"number":123,"title":"Title","url":"https://github.com/owner/repo/pull/123","applies_to":"after"}]}

   A local-edit comparison has no source file. The source is report metadata
   only; it never enters trials or the extraction prompt.

   In GitHub Actions or GitLab CI, the runner automatically captures repository
   and workflow PR/MR links from predefined variables and the GitHub event file.
   Do not prepare a source file merely to add these links. Explicit historical
   source metadata overrides CI context entirely. Workflow context does not
   establish the compared revisions: never substitute `GITHUB_SHA`,
   `CI_COMMIT_SHA`, or `CI_COMMIT_BEFORE_SHA` for the actual comparison inputs.
   Missing PR/MR metadata is omitted; no API lookup or environment dump is needed.

2. **Prepare the scenario and data.** Before drafting anything, read
   `references/scenario-and-test-data.md` inside this skill's base directory
   and follow its preparation recipe. In short:
   - From the frozen goals and the selected diff, list the new and preserved
     behavior, the observable capabilities it needs, and the environment
     premises those capabilities depend on.
   - Write a neutral `--task`: a natural request that starts before the tested
     work and reaches the changed rule. It must not state the expected answer,
     the rule, or a historical mistake; the changed instruction is the only
     place the guidance exists.
   - Reuse project data when it already exercises the capabilities. Otherwise
     prepare one coherent dataset of ordinary inputs plus a bounded set of
     compatible edge cases that challenge the goal's assumptions.
   - Keep per-case criteria, mappings, and omissions in private notes, never
     in the task or trial files.

   Do not require an incident, a real past request, or an existing eval from
   the user. Ask only when a material requirement cannot be reached from the
   change, project, or conversation. For a historical comparison, prepare from
   the contemporary change only, before reading later fixes or results.

3. **Preflight, freeze, then run.** Run as soon as the reference's preflight
   passes and the task, data, criteria, and settings are frozen. Do not ask the
   user to confirm the file, task, cost, or run mode. Do not mention trial
   counts, cost, or full versus fast modes during normal execution.
   First satisfy the privacy and sensitive-content approval boundary above;
   automatic execution never overrides it. If the planned environment cannot
   support a required capability or premise, stop and report it; do not silently
   substitute a narrower test or fabricate approvals. Stop preparation workers
   before launch, and keep the first result: no retuning or reruns to manufacture
   a finding after seeing outcomes.

   Under Claude Code or Codex, preserve the current stack:

       behavior-diff.sh --agent <current-host> --file <file> --task "<task>" --purpose-file <private-purpose.json>

   Under upstream Pi, preserve the exact current model:

       behavior-diff.sh --agent pi --model <exact-current-pi-model> --file <file> --task "<task>" --purpose-file <private-purpose.json>

   Under OMP, preserve the exact current model:

       behavior-diff.sh --agent omp --model <exact-current-omp-model> --file <file> --task "<task>" --purpose-file <private-purpose.json>

   Only add `--fast` when the user explicitly requested it in the current
   request with `fast`, `--fast`, `two runs`, or `one trial per side`:

       behavior-diff.sh --agent <current-host> --file <file> --task "<task>" --purpose-file <private-purpose.json> --fast

   For Pi or OMP, append `--fast` to its model-pinned command.
   Pass the frozen JSON only through `--purpose-file`. The runner validates and
   copies it to report configuration before trials. Never put it in `--task`,
   a trial prompt, a sandbox file, or other trial inputs. If invoking the runner
   without this skill and without purpose, assessment uses labeled diff-only
   inference; there is no implied session context.

   For a historical comparison with verified provenance from step 1, append
   `--source-file <private-source.json>` to the command prepared for that
   comparison, including any `--before-file` or `--fast` it already uses:

       behavior-diff.sh --agent <current-host> --file <file> --task "<task>" --purpose-file <private-purpose.json> --source-file <private-source.json>

   The runner validates the source before trials, excludes the file from trial
   copies, and freezes it in report configuration for the report header. It
   does not look anything up. Never put source details in `--task`, a trial
   prompt, or a sandbox file.

   **Shared data.** When step 2 prepared new shared data, or private context
   in the checkout cannot otherwise be kept from trials, do not run the
   commands above from the user's checkout. Prepare and verify the stage with
   `references/scenario-and-test-data.md`, then run the same runner command
   from `$ROOT/project` with `$ROOT/home` as `BEHAVIOR_DIFF_HOME`, exactly
   as that reference shows. Keep the same agent, model, `--fast`, purpose,
   and source choices. Pass `--before-file` only as the stage's frozen
   `before` file, and only when it exists; never pass the original Before
   path. If preparation or verification fails, stop and report the reason;
   do not launch the run.

   **Keep the run handle.** Use the host's background-execution facility when
   available so other work can continue. Retain the exact run directory printed
   at startup; concurrent comparisons have separate IDs. Share the printed
   status/watch commands with the user when they want to follow progress.

   Query `python3 <skill-base>/scripts/status.py <run-directory> --json` when the
   user asks or your next decision needs progress. Do not repeatedly poll while
   other useful work remains. `--list --active` discovers unfinished runs without
   silently selecting the newest one. Human readers can use the same explicit
   run directory without `--json`, or add `--watch`; closing the watcher does not
   stop the comparison.

   Distinguish finished trials, available assessment, and a generated report.
   A finished trial is not a pass; a report can exist without an assessment.
   Silence is not proof of failure. If process identity cannot be verified,
   report status as uncertain rather than claiming the run is active or failed.
   Use host completion notifications where supported, but do not promise an
   automatic chat notification on hosts that do not provide one.

4. **Present the result.** The runner already opened `report.html` itself — do NOT open it again (that produces a duplicate tab); just summarize.
   Summarize the flow diff honestly:
   - Flows diverge → describe where, in one or two sentences.
   - Flows identical → report that no difference was observed in the
     recorded actions. Check final answers separately for differences
     in decisions, explanations, or proposed next steps.
   - When the relevant behavior is unchanged, check whether the task
     reached the situation the rule targets:
     - If it did, describe the behavior shared by both versions.
     - If it did not, explain what situation was missing and suggest
       a task that reaches it.
     - If the evidence is insufficient, say you cannot determine
       whether the situation was reached.
     Do not infer a missed situation from identical behavior alone,
     or claim that the rule generally works or fails.
   Then assess each private case from raw evidence (actions, tool returns,
   artifacts), not only final answers, as the reference describes. Separately
   record whether its condition was reached, missed, or unknown and whether its
   intended outcome was supported, contradicted, or lacked sufficient evidence.
   Summarize each goal without hiding missed cases. Report interrupted or
   unassessable attempts and harness failures separately from requirement failures.
   Identical Before and After behavior can still fail a goal After added. State
   where your assessment agrees with or differs from the report; do not edit it.
   Orient the reader briefly: say what the agent was asked to do, the changed
   skill's role when relevant, and the decision point tested. Lead with the
   practical supported contrast, not an internal workflow label. At first use,
   explain unfamiliar roles, acronyms, objects, or tables by their concrete
   function in the evidence. Never guess an acronym expansion, unread table
   contents, role authority, or the author's motive.
   Preserve shared checks, unchanged outcomes, minority branches, and evidence
   limits. Distinguish stated plans and answer explanations from completed
   actions; explanation-only differences are not new actions. Separate what the
   source instruction mandates from what the trials show: disclosure of added
   instructions is not itself an approval requirement, and a model-added
   approval request is not new if Before already requested approval.
   Before returning your own user-facing summary, invoke the installed
   `humanizer` skill in embedded mode if the host makes it available. If it is
   unavailable, write concise, natural technical prose yourself: state the
   observed change directly, avoid filler or inflated claims, and retain genuine
   uncertainty. Do not install or download a skill.
   This is a prose-only edit. Preserve counts, evidence qualifiers, citations
   and links, exact quotes, code, and excerpts. Do not change saved artifacts or
   post-edit `report.html`; report narrative belongs to extraction.

## Boundaries

- The runner never modifies the user's repo; reports and traces stay
  local under the runs root above. Staged shared-data runs keep them under
  the stage's `home/runs/`.
- Never write, stage, stash, or commit shared data in the user's checkout.
- The report quotes the user's real code. Never publish it anywhere
  without the user reviewing it first.
- Do not edit the user's instruction file yourself — this skill only
  measures a change the user already made.
