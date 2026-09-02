---
name: behavior-diff-retro
description: Write a retro for a finished behavior-diff or behavior-diff-live run — where the time went, what broke, what the evidence can and cannot support — and feed the lessons back into Behavior Diff. Use for "behavior diff retro", "retro this run", "retro the experiment", after any behavior-diff run finishes.
---

# Behavior-diff retro

After a run of `behavior-diff` (headless) or `behavior-diff-live`
(subagents), write the retro while the session still remembers what
happened, and feed durable lessons into `RETRO_NOTES.md` at the runs
root (`${BEHAVIOR_DIFF_HOME:-~/.behavior-diff}`). When the current repo
is the Behavior Diff repo, use the repo's own `RETRO_NOTES.md` instead and
follow its commit rules.

## Steps

1. **Pick the run.** The one just finished in this session, or the run dir
   the user names under the runs root. Read its artifacts: report.md,
   grades.tsv, decisions.json, stderr logs, saved agent reports.

2. **Write `retro.md` INTO that run dir**, answering — honestly, with the
   experimenter's own mistakes included:
   - Where the wall-clock went: agent work vs experimenter overhead
     (fixture discovery, relaunches, report wrangling, format inventions).
   - What ran more than once, and whether each rerun was a decision or an
     accident.
   - Fixture and setup failures: what broke, what error-by-error learning
     should have been a script or a precheck.
   - Tooling steps missed or misused: was the reporting pipeline used?
     were skills followed? what did the skill text fail to say?
   - Evidence boundaries actually hit: trial count, self-reported vs
     captured actions, extractor variance, confounds the subjects found.
   - Findings about the REAL target repo that surfaced incidentally: keep
     only those that affect behavior-diff experiments (fixture traps,
     broken verbs, red baselines). Do not file external issues for them
     unless the user asks.

3. **Feed back.** Append one dated entry to the `RETRO_NOTES.md` named
   above: 3-8 bullets of durable, tool-level lessons with a pointer to
   the run dir. Tooling lessons only — never real code excerpts or
   transcript quotes. In the Behavior Diff repo, run its privacy check
   before committing.

4. **Propose, don't apply.** Turn the lessons into a short list of
   concrete Behavior Diff improvements (file-level: which skill text, which
   script, which label) and give it to the user as proposals. Do not change the
   skills or scripts without their go.
