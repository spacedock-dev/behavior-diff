# Behavior-check retro notes

Durable, tool-level lessons fed back from experiment retros (the
`behavior-diff-retro` skill appends here). Full retros live in each run
dir under `runs/` (gitignored); this file carries only what future runs
need.

## 2026-08-21 — spacedock 0eac880, behavior-diff-live (runs/live-20260821-2050)

- Fixture discovery must happen before experiment time: five error-by-error
  round trips against the spacedock binary burned most of an 80-minute run.
  Recipe captured in that run's fixture-build.md; script it (make-capsule.sh).
- A rule that governs a HANDOFF cannot be tested one side at a time —
  faking the other side's output is what kept breaking. Sequence rules need
  a two-agent harness comparing whole cycles.
- Reports stuck in five of eight runs → report delivery now lives in the
  launch prompt (SendMessage to main). A silent agent is usually thinking;
  mtime polling misdiagnoses it.
- The live variant's actions are self-reported, not captured traces. Reports
  must say so. At n=1, decision diffs must carry the caution and remain sketches
  until repeated runs. One earlier run called 8/8 decisions "diverging" on
  byte-identical outcomes.
- Scope experiments by rule, not by commit: a commit carrying two rules
  makes every report show both, and the reader must be told which one the
  scenario tests.
- Generic flow buckets (inspect/read/search/tests/run) cannot see
  spacedock-shaped divergence; a domain vocabulary (gate prepare, gate
  record, state commit, dispatch, entity-body write) would show forks
  without a model call.

### Spacedock quirks that affect behavior-diff fixtures (recorded, not filed)

- `spacedock gate --help` advertises `gate validate`, which does not exist
  (exits 2) — caused a voided FO pair via a bogus decode error.
- `internal/status TestClassifierPrecisionRecallOnLiveCorpus` walks up six
  parents to the live corpus: from a nested checkout it escapes into the
  implementation worktree, and its expected value lives untracked — a clone
  cannot reproduce it. Fixture ACs must not cite it.
- `skills/integration TestSurveyCodexPresenceThroughSync` is red at base
  commit 0eac880 — fixture ACs citing "all tests green" are instantly false.
- An entity minted flat that later gains a gate room becomes a hybrid
  flat-plus-folder shape: `status --validate` exits 0 VALID but warns.
  Agents notice and chase it; keep fixtures in one shape.

## 2026-08-31 — engram f4138f5, behavior-diff-live (runs/live-20260831-174709)

- Simulated scenarios are valid when the user approves the same task and state
  for both variants. Check the decision fork before launch. This fork was weak
  because the existing smallest-change rule gave the same final choice.
- The two agents used different self-reported action schemas. One agent listed
  each read, search, and command. The other agent grouped actions together.
  Use one shared schema before comparing their actions.
- Self-reported traces are not actual commands. Label them as self-reported
  actions, and do not pass prose actions to the shell-command classifier.
- The current source already uses `decisions.py -> render.py -> open`. The
  installed cache had stale content under the same version, so the version
  alone did not identify the code that ran.
- Before and After labels must be configurable. Fixed labels gave the wrong
  meaning for a comparison between a parent commit and its target commit.
- One added aggregate action changed the extractor output. Treat an n=1
  decision sketch as sensitive to reporting detail, not as a direct measure of
  behavior.

## 2026-09-01 — building a vague-rule demo fixture (8 variants, ~58 trials)

Eight fixture variants were built and measured before one worked. The seven
that failed all failed for reasons worth keeping, because each looks like a
good design on paper.

- **Diligence rules cannot be demoed.** "Double-check", "be careful", "check
  it properly", "don't say it's clear unless it is" — the untreated agent is
  already diligent, so there is nothing for the rule to move. Across the
  failed variants the baseline never once missed the planted problem.
- **You cannot make thoroughness costly for an agent with a shell.** A
  40-ticket queue with one mismatched refund amount was meant to make
  per-item checking expensive. The plain agent wrote a `grep | sed` pipeline,
  compared all 40 in one step, and found it. Scale does not create
  temptation; the agent scripts it away.
- **A written policy closes the fork a vague rule needs.** A refund queue
  with a policy defining "standard refund" produced identical behavior on
  both sides: the three non-standard requests break a stated condition, so
  holding them is the *correct* answer, not a judgment call.
- **`demo-invoice-review` works because its rule orders the skip.** "Do not
  open the full procedure" makes the divergence happen. A vague rule cannot
  do that by definition, so its divergence has to come from the agent's own
  judgment — which needs a fork with no right answer.
- **What finally worked was a presentation rule.** "Use ASCII to visualize
  content when explaining concepts" changed the shape of the answer (1 of 6
  before trials drew a diagram, 6 of 6 after) while both sides read the same
  records and reached the same cause. Nothing breaks, and that is the point:
  the demo shows *what your rule did*, not that it caught a bug.

Process lessons, both of which cost real runs here:

- **Do not write the story before the numbers.** Three fixtures were built,
  documented across four surfaces, and committed before being measured; all
  three were later deleted. Build minimally, run 3+3, document only what the
  run showed.
- **Never read a trace mid-run, and check the detector before trusting it.**
  One trial sampled before it finished was reported as a miss when it had
  caught the problem. Separately, a regex counting only box-drawing
  characters reported 1 of 3 when the real answer was 3 of 3 — two trials had
  drawn their timelines with plain spacing. Both errors were caught, but only
  by reading the answers in full.
- **`--fast` mis-set the emphasis.** At one trial per side this fixture read
  as "the diagram appeared but the plain-English half barely moved"; at 3+3
  the drawing is what is unanimous. Use `--fast` to show shape in a demo,
  never to characterise an effect.
