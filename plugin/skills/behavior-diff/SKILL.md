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

The skill owns judgment. It finds the change, freezes its purpose, drafts the
decision-moment task, selects the current trial stack and model, and explains
the evidence.

The scripts own repeatable mechanics. They build variants, run trials,
normalize traces, grade completeness, extract decisions, and render the report.

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

2. **Draft the task.** `--task` must recreate the decision moment governed by
   the changed rule, whether the goal is correction, addition, or preservation:
   - Ask the user for the real request from the incident that motivated
     the rule, and reuse it when they have one.
   - Never leak the expected behavior into the task. The changed rule must
     be the only place the guidance exists — if the task itself says what
     "good" looks like, both variants will comply and the diff shows
     nothing.
   - When the rule fires mid-task, start the task at the decision point:
     "You already did X (it is in the tree); decide/report Y."

3. **Run it as soon as the task is known.** Do not ask the user to confirm
   the file, task, cost, or run mode. Do not mention trial counts, cost, or
   full versus fast modes during normal execution.
   First satisfy the privacy and sensitive-content approval boundary above;
   automatic execution never overrides it.

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
  local under the runs root above.
- The report quotes the user's real code. Never publish it anywhere
  without the user reviewing it first.
- Do not edit the user's instruction file yourself — this skill only
  measures a change the user already made.
