---
name: behavior-diff-live
description: Run a before/after behavior diff inside the current session using subagents — one trial per variant, the main agent prepares the decision-moment scenario and watches both runs. Use for "live behavior diff", "behavior diff with subagents", "quick behavior diff", or experiment runs where the user wants to adjust the scenario and see progress.
---

# Behavior diff — live (subagent variant)

The sibling `behavior-diff` skill shells out to `behavior-diff.sh`: fresh
headless `claude -p` sessions where the variant's CLAUDE.md loads exactly
like production, three trials, rendered report. This variant trades that
fidelity for observability: **one trial per variant, run as subagents**
launched and watched by you, with the scenario prepared — and adjustable —
in conversation.

State this evidence boundary in every summary: subagents do not auto-load
the variant's CLAUDE.md; they are told to read and follow it, which is
weaker instruction delivery than the headless runner. And one trial per
side is a single sample — report what happened; never say "consistently",
and treat the decision diff as a sketch until the headless 3+3 confirms it.


**Spacedock workflow rule?** If the changed file is a spacedock workflow
doc (the repo contains `cmd/spacedock`, or the user says spacedock / FO /
ensign / gate), read `references/spacedock-duo.md` in the sibling
`behavior-diff` skill's directory (both skills install together) before
designing the run — it decides between the single-role path and
the two-agent duo cycle, and forbids hand-built fixtures.

**Host note:** this variant orchestrates two parallel subagents, which
Claude Code provides. On a host without subagent dispatch (Codex), run
the two trials sequentially yourself in fresh contexts, or prefer the
sibling `behavior-diff` skill — its runner gives stronger evidence
anyway and takes `--agent codex`.

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

4. **Launch both subagents in ONE message** (so they run concurrently),
   one per variant, identical prompts except the directory. Dispatch
   both with NO model override: the trials must run as the same model
   as the main agent, because the experiment measures what THIS agent
   would do — a trial on another model measures a different agent.
   Each prompt:
   - work only inside <dir>; never modify any file, never touch anything
     outside it, never run networked or destructive commands;
   - first read the project instruction files there (CLAUDE.md,
     AGENTS.md) and follow them as your project instructions;
   - then the task;
   - end the report with two sections: `ANSWER` (what you would tell the
     user) and `ACTIONS`.
     Under `ACTIONS`, list every task tool action completed before report delivery
     in order. Write one numbered line per tool action as
     `<Tool>: <target or command>`. Never group several actions on one line.
     Include reads and searches, not only commands.
     Do not include the final delivery SendMessage in `ACTIONS`.
   - when finished, DELIVER the report by calling SendMessage with
     `to: "main"` — a report left as plain final text gets stuck.
   Never tell either subagent it is being compared, which variant it is,
   or what the rule change is.

5. **While they run**, relay progress and early divergence to the user —
   that visibility is the point of this variant. A silent agent is usually
   thinking, not dead: file mtimes and process lists misdiagnose it. Never
   relaunch a trial for silence alone; ping it with SendMessage first.

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

   Then extract the decision diff as a subagent of THIS session — never
   by spawning `codex exec` or `claude -p`:
   - Run `decisions.py <run dir> --emit-prompt` (it sits beside
     `render.py` in the sibling `behavior-diff` skill's directory) and
     save its stdout as `<run dir>/reports/extractor-prompt.txt`.
   - Dispatch ONE fresh subagent as `model: "sonnet"` — extraction
     reads two short trial logs and replies with JSON, so it does not
     need the session's model; the `--extractor-label` below keeps
     stamping whichever model actually ran. Never a fork: a forked agent
     inherits this session's context, which contains the rule diff,
     and a tool-holding one could read the run dir; either breaks the
     extractor's blindness. Its prompt is this fixed two-line preamble
     followed by the emitted prompt verbatim:

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
   - If decision extraction succeeded, use the flow-diff shape: steps both
     took in order, the first divergence, each side's path, and both final
     answers quoted.
   - If decision extraction was skipped after two failed attempts, do not
     invent a decision diff or flow. Instead,
     summarize each side's ordered self-reported actions,
     quote both final answers, and repeat the visible extractor-skip note.
   - Label it "1 trial per side — single-sample evidence; actions
     self-reported".

## Boundaries

- Never modify the user's repo; the diff under test is their own
  uncommitted edit, and it stays uncommitted.
- Both variants must differ by exactly the target file — verify before
  launching.
- No PASS/FAIL banner, no verdict language: one trial per side shows a
  difference or it doesn't, nothing more.
