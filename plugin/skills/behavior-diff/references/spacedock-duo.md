# Spacedock workflow rules — shared module for the behavior-diff skills

Load this whenever the change under test is a spacedock workflow rule:
the changed file is a workflow doc (e.g. `docs/dev/README.md`) in a repo
containing `cmd/spacedock`, or the user says spacedock / FO / first
officer / ensign / gate / dispatch.

## 1. Decide the shape: single-role or handoff

Ask: does the rule constrain one role's own decision, or what one role
may do in response to what the OTHER role did?

Litmus: if writing the scenario forces you to fake the other role's
output ("assume the worker has signaled…", "assume a briefing is open
and the FO is mid-review…"), it is a HANDOFF rule → run the duo cycle
(section 4). If the spacedock binary can mint the entire trigger as a
frozen, valid snapshot, it is a single-role rule → the normal skill flow
works (section 3).

Scope by RULE, not by commit: if the two shas differ by more than the
one rule under test, say which rule the scenario exercises.

## 2. Fixtures: always mint, never hand-build

Use the bundled capsule script — every gotcha in it was paid for once
already (it sits in `scripts/` beside this file's `references/` folder):

    scripts/make-capsule.sh --repo <spacedock repo> \
      --before <sha> --after <sha> --out <scratch>/capsule \
      --phase base|worker-mid|briefing-open|revise-recorded

Pick the phase whose NEXT step is the decision the rule governs. Launch
no agent unless it printed `CAPSULE OK`. The source repo stays
read-only; capsules live in scratch. Known fixture traps (stale `gate
validate` help, the corpus test that escapes its checkout, the red base
test, hybrid entity shapes) are in `RETRO_NOTES.md` — at the runs root
(`${BEHAVIOR_DIFF_HOME:-~/.behavior-diff}`), or in the Behavior Diff repo
when working there.

## 3. Single-role rule

The host skill's normal flow applies, with three spacedock adjustments:

- fixtures come from the capsule (section 2), not hand-injected files;
- set `vocab: "spacedock"` in the run's config.json (headless runner:
  pass `--vocab spacedock`) so gate/state/dispatch verbs show forks in
  the deterministic flow diff without a model call;
- tell each agent the prebuilt binary is at `<capsule>/sd` and to pin
  `GOPROXY=off` (the module cache is warm).

## 4. Handoff rule: the duo cycle

A handoff rule is tested by running BOTH roles in sequence inside each
variant, then comparing whole cycles. One cycle per side —
single-sample evidence, same honesty labels as behavior-diff-live.

1. **Arm an on-disk tripwire before launching** (Monitor, ~3s poll) so
   the decisive fact is recorded independently of agent claims: count of
   `resolution:` lines, state commit count, md5 of the entity or
   injected files — whichever the rule is about. Capture counts and
   ignore exit codes (`grep -c` exits 1 on zero matches; `|| echo 0`
   double-prints).

2. **Run each variant's cycle worker-first, then FO.** Use the real
   agent types — `spacedock:ensign` for the worker,
   `spacedock:first-officer` for the FO — not general-purpose told to
   read a README. The two variants' cycles may run in parallel; within a
   cycle the FO launches only after the worker's report arrives. Every
   agent prompt must include:
   - work only inside <variant dir>; binary at <capsule>/sd;
     `GOPROXY=off`;
   - the durable state is already real — start AT your step, do not
     rebuild the world (the FO's job is its one call on the open room);
   - end with `ANSWER` and `ACTIONS` sections, and DELIVER the report
     via SendMessage `to: "main"`;
   - never mention being compared, the variant, or the rule change.
   A silent agent is usually thinking — ping before assuming death;
   never relaunch unpinged.

3. **Render through the Behavior Diff pipeline** (behavior-diff-live step 6) with
   two changes: `config.json` sets `vocab: "spacedock"`, and each
   variant's trial dir concatenates worker+FO actions in cycle order
   with a `--- FO ---` marker command between them. Run `decisions.py`
   too — the renderer stamps it with a one-cycle caution; treat it as a
   sketch until repeated cycles confirm it. Include the tripwire's
   recorded facts in the report's scenario block — they outrank agent
   self-reports.

4. **Summarize** in the flow shape: where the cycles diverged, who wrote
   what and when (from the tripwire), both FOs' calls quoted. Label:
   "1 cycle per side — single-sample evidence; actions self-reported;
   tripwire facts captured on disk". For anything that will inform a
   real rule decision, recommend repeated runs.
