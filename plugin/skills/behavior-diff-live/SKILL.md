---
name: behavior-diff-live
description: Run a before/after behavior diff inside the current session using subagents — one trial per variant, the main agent prepares the decision-moment scenario and watches both runs. Use for "live behavior diff", "behavior diff with subagents", "quick behavior diff", or experiment runs where the user wants to adjust the scenario and see progress.
---

# Behavior diff — live (subagent variant)

The sibling `behavior-diff` skill shells out to `behavior-diff.sh`: fresh
headless sessions where the variant's instruction file loads like production,
three trials, and one rendered report. This variant trades that fidelity for
observability: **one trial per variant, run as subagents** launched and watched
by you, with the scenario prepared and adjustable in conversation.

State this evidence boundary in every summary: subagents do not auto-load
the variant's instruction file. They are told to read and follow it, which is
weaker instruction delivery than the headless runner. One trial per side is
one sample. Report what happened, never say "consistently", and treat the
decision diff as a sketch until the headless 3+3 confirms it.


**Spacedock workflow rule?** If the changed file is a spacedock workflow
doc (the repo contains `cmd/spacedock`, or the user says spacedock / FO /
ensign / gate), use Spacedock fixtures.
Spacedock fixtures are isolated before/after test repos. The real Spacedock
binary creates their workflow state. Do not create this state by editing files.
Before designing the run, read
`references/spacedock-duo.md` in the sibling `behavior-diff` skill's
directory (both skills install together). It chooses the single-role or
two-agent path. Create the fixtures with `make-spacedock-fixtures.sh` from
the sibling skill's bundled `scripts/` directory.

**Host dispatch:**

- Claude Code launches two parallel subagents. Each result uses `SendMessage`.
- OMP launches one `task` batch with two task items.
  Results return to the parent automatically. Do not ask an OMP task agent
  to call `SendMessage`.
- Pi has no built-in subagent dispatch. Use the sibling headless skill with
  `--agent pi` and the exact Pi model.
- On Codex without dispatch, run two fresh contexts in sequence or use the
  sibling headless skill with `--agent codex`.

## Steps

1. **Find the change.** As in behavior-diff: `git status --porcelain` in
   the user's repo → the modified instruction file (ask if several, stop
   with an explanation if none). Read `git diff -- <file>`.
   When the file is untracked or the folder is not a git repo, the
   "before" content is a file instead of HEAD: the newest entry under
   `${BEHAVIOR_DIFF_HOME:-~/.behavior-diff}/baselines/` for that path
   (the plugin's backup hook saves it there before the first edit), or a
   file the user names. No baseline and no user file: explain that there
   is no "before" to compare against, and stop. Read the change with
   `diff <before> <file>`.

   Before preparing trials, follow the purpose/provenance and privacy rules in
   step 1 of the [headless skill](../behavior-diff/SKILL.md#steps). Freeze the
   private purpose JSON outside the original project and both scratch copies.
   Validate it with `python3 <behavior-diff scripts>/purpose.py <purpose file>`.
   Keep its canonical JSON for assessment; never include purpose, its path,
   or raw session context in either trial prompt. Do not revise it after results.

2. **Build the variants** in a scratch dir, never in the user's repo:

       for v in before after:
         mkdir -p $work/$v && git -C <repo> archive HEAD | tar -x -C $work/$v
       cp <repo>/<file> $work/after/<file>          # After only
       (git init + add + commit inside each copy, so git stays contained)

   In a non-git folder, replace the `git archive HEAD` line with a plain
   folder copy (`tar -C <repo> --exclude .git -cf - . | tar -x -C $work/$v`)
   for both variants; if the `~/.behavior-diff` home sits inside the
   folder, exclude it too. Every variant is a full copy, so copy from the
   smallest folder that holds the file.

   Whenever the "before" side is a file — a hook baseline from
   `${BEHAVIOR_DIFF_HOME:-~/.behavior-diff}/baselines/` or a user-given
   original — rather than HEAD, put the contents in place after building
   the two copies, in every world: `cp <before> $work/before/<file>` and
   `cp <repo>/<file> $work/after/<file>`. This includes an untracked file
   inside a git repo: `git archive HEAD` contains no untracked file, so
   BOTH copies need their version put in place. In a non-git folder the
   copies already hold the After content and only `$work/before/<file>`
   changes. When the resolved before is the store's `*-ABSENT` marker
   (the file did not exist before the edit), delete `$work/before/<file>`
   instead of copying anything.

   Verify with `diff` that the two copies differ by exactly that file.

3. **Prepare the decision moment with the user.** Same task rules as
   behavior-diff: reuse the real incident request; never leak the expected
   behavior — the changed rule must be the only place the guidance exists;
   start the task at the decision point. If the experiment needs extra
   state (half-done work, a failing log, staged files), apply it
   IDENTICALLY to both copies. Show the user the final task and any
   injected state, and get their go before launching.

4. **Launch both trials with the host path above.** The two prompts must be
   identical except for the directory. Choose the trial model separately
   from the extraction model:
   - Claude Code: use `model: "opus"` for both trial subagents.
   - Codex: resolve `sol` once with
     `python3 <behavior-diff scripts>/codex_model.py sol`, then select that
     exact ID for both fresh contexts or subagents.
   - OMP: retain the main agent's model without an override.

   Honor an explicit user trial-model override, using it on both sides.
   Record the model used, not the main agent's model by assumption. If the
   host cannot select the requested trial model, explain that limitation
   and use the sibling headless skill instead; never silently substitute.

   Claude Code sends both prompts in one parallel dispatch. Add this delivery
   rule to each Claude prompt: when finished, call `SendMessage` with
   `to: "main"`. A report left as plain final text gets stuck.

   OMP sends both prompts in one `task` batch. Results return to the parent
   automatically. Do not add a `SendMessage` rule.

   Each trial prompt must:
   - work only inside <dir>; never modify any file, never touch anything
     outside it, never run networked or destructive commands;
   - first read the project instruction files there (CLAUDE.md,
     AGENTS.md) and follow them as project instructions;
   - then handle the task;
   - end the report with two sections: `ANSWER` (what it would tell the user)
     and `ACTIONS`.
     Under `ACTIONS`, list every task tool action completed before report delivery
     in order. Write one numbered line per tool action as
     `<Tool>: <target or command>`. Never group several actions on one line.
     Include reads and searches, not only commands.
     Do not include the final delivery SendMessage in `ACTIONS`.
     OMP has no separate delivery action to list.

   Never tell either trial it is being compared, which variant it is, or what
   the rule change is.

5. **While they run**, relay progress and early divergence to the user.
   That visibility is the point of this variant. A silent agent is usually
   thinking, not dead. File mtimes and process lists misdiagnose it. Never
   relaunch a trial for silence alone. Use the host's agent messaging path
   before treating it as stuck.

6. **Render through the Behavior Diff pipeline — do not invent a report format.**
   Build `${BEHAVIOR_DIFF_HOME:-~/.behavior-diff}/runs/live-<stamp>/`
   with, per variant, a
   `before-1/` / `after-1/` dir containing a synthesized `trace.jsonl`:
   one line per self-reported action
   `{"type":"assistant","message":{"content":[{"type":"tool_use","name":"Bash","input":{"command":"<action>"}}]}}`
   and a final line `{"type":"result","result":"<the ANSWER text>"}`.
   Add `grades.tsv` (`before-1\tREVIEW\t-` etc.), `task.md`, and a
   `config.json` with `"mode": "review"`, `"vocab": "generic"`,
   `"trace_source": "self-reported"`, and honest label notes. Use
   `"before_label": "current file"` and `"after_label": "your change applied"`
   by default. For an agent-built comparison, replace both defaults with
   snapshot-specific notes that say what each snapshot contains; never call
   an agent-built snapshot an uncommitted user change. Keep a `sub` that
   states honestly: actions are SELF-REPORTED
   by each agent, not captured traces, one trial per side. Save both raw
   trial reports under `runs/live-<stamp>/reports/`.

   Set `config.json`'s `purpose` to the canonical JSON frozen before the trials
   (`null` when no safe purpose was available), not a new inference from answers.
   These synthesized traces contain self-reported actions, not captured source
   returns. Do not invent tool-return content or reread current files to fill
   that gap. Assess observable final-answer criteria where supported; source
   consistency remains unassessable without recorded content.

   Record comparison provenance separately from these display labels:
   - Keep `target_file` relative to the original project and its Before/After
     copies, so instruction diffs still read each snapshot's file.
   - Set `compared_source_paths` to a nonempty JSON array of resolved absolute
     paths. Include the original project's `target_file`, both scratch
     instruction paths, and any external baseline or other source instruction
     used to build the variants. For an absent Before file, include its intended
     resolved path. Invoke extraction from the original project root.
   - Preserve these fields when updating config. The extractor excludes all
     listed sources from Humanizer discovery, including symlink destinations.
     Missing or invalid provenance uses plain-language fallback instead of
     loading an installed skill that could be the instruction under comparison.

   If Codex ran the two trials sequentially because the host has no subagent
   dispatch, append "decision diff skipped: host has no subagent dispatch"
   to `config.json`'s `sub`. Skip the extraction bullets below and continue
   with `render.py`. Do not invent a decision diff or start another CLI.

   On hosts with dispatch, extract the decision diff as a subagent of THIS
   session — never by spawning `codex exec` or `claude -p`:
   - Run `decisions.py <run dir> --emit-prompt` (it sits beside
     `render.py` in the sibling `behavior-diff` skill's directory) and
     save its stdout as `<run dir>/reports/extractor-prompt.txt`.
   - Dispatch ONE fresh extraction subagent. Claude Code uses
     `model: "sonnet"`; OMP retains its existing Sonnet extraction selection.
     Codex resolves `luna` with
     `python3 <behavior-diff scripts>/codex_model.py luna` and selects the
     exact returned ID. Honor an explicit user extraction-model override.
     Resolve a Codex family selector once and reuse the result for any retry.
     If discovery fails or the host cannot select the extraction model,
     append "decision diff skipped: extraction model unavailable" and the
     reason to `config.json`'s `sub`, then continue with `render.py`.
     Never silently replace the requested model or start another inference CLI.
     Extraction reads the emitted trial evidence and numbered instruction hunks,
     then replies with JSON. It does not need the trial model; the
     `--extractor-label` below stamps whichever model actually ran.
     Never a fork: inherited session context or additional tool reads could
     introduce evidence outside the emitted prompt. The hunks are supplied
     deliberately for interpreted edit links, not as instructions to follow.
     Its prompt is this fixed two-line preamble followed by the emitted prompt verbatim:

         Answer directly; do not use any tools.
         Reply with the JSON only.

   - Save the raw reply as `<run dir>/reports/extractor-reply-1.txt`,
     then run `decisions.py <run dir> --ingest <reply file>
     --extractor-label subagent:<model>` (`<model>` = the model the
     extraction subagent ran as).
   - If the ingest exits nonzero, retry ONCE: one more fresh subagent,
     same prompt, reply saved as `extractor-reply-2.txt`, ingest again.
     If that also fails, ship the raw-actions-and-final-answers report.
     Do not invent a flow. Append "decision diff skipped: extractor reply
     unparseable (2 subagent attempts)" to `config.json`'s `sub` so the
     extractor-skip note is visible on the page, name the saved reply files
     in the summary, and do NOT fall back to `codex exec` or `claude -p` —
     that would reintroduce the external-CLI dependency this flow removes.

   Then run `scripts/render.py` and immediately `open` the report.html
   it prints — never make the user ask for the page. The renderer
   stamps the decision diff with a one-trial caution (n=1 cannot
   separate a rule effect from run-to-run variation; it has called 8/8
   decisions "diverging" on byte-identical outcomes), so present it as
   a fast sketch to be confirmed by the headless 3+3, never as
   findings.

7. **Summarize in conversation.**
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
   - If decision extraction succeeded, answer the recorded target question first.
     Retain unchanged, mixed, and unassessable outcomes; do not call an unchanged
     target mistake a successful fix. Then explain relevant observed paths and
     quote the actual answers. Do not promote incidental differences over the goal.
   - If decision extraction was skipped because the host has no subagent
     dispatch, the extraction model is unavailable, or two attempts failed,
     do not invent a decision diff
     or flow. Instead, summarize each side's ordered self-reported actions,
     quote both final answers, and repeat the visible extractor-skip note.
   - For identical action flows or unchanged behavior, follow the unchanged-result
     guidance in step 4 of the [headless skill](../behavior-diff/SKILL.md#steps).
     Keep self-reported actions distinct from captured execution evidence.
   - Label it "1 trial per side — single-sample evidence; actions
     self-reported".

## Boundaries

- Never modify the user's repo; the diff under test is their own
  uncommitted edit, and it stays uncommitted.
- Both variants must differ by exactly the target file — verify before
  launching.
- No PASS/FAIL banner or automatic acceptance verdict. One sample per side can
  support a scoped observation against available evidence, not reliability or
  causation; source consistency cannot be inferred from self-reported reads.
