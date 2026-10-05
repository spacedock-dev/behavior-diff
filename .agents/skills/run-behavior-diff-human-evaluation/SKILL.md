---
name: run-behavior-diff-human-evaluation
description: Run a private, five-question human evaluation of the current local Behavior Diff summaries using randomly sampled skill commits from DataRecce/recce-team. Use when a maintainer asks for a human evaluation, a blind report quiz, or to evaluate current summary ability; also use to resume or analyze an existing evaluation.
---

# Human evaluation of Behavior Diff

Manually run five real comparisons, then ask a human to identify each change
from four shuffled statements. This is a repository-maintainer skill, not
plugin payload. Never trigger it from hooks, CI, or a scheduled job.

## Start or resume

1. For **analyze/resume**, locate the requested private session under
   `~/.behavior-diff/human-evaluations/`; use its saved evidence. Never create
   fresh trials to answer a request about an existing result.
2. For **new evaluation**, require this repository's checkout, Python 3.9+,
   Git, authenticated `gh` access to `DataRecce/recce-team`, Bash, `jq`, and
   the Claude Code CLI.
   A Claude or Codex maintainer session can orchestrate it; the trial stack
   is explicitly Claude Code with read-only tools, not the orchestrator's
   default host. Read [the workflow](references/workflow.md) before starting.
3. Explain the spend and privacy boundary. Require fresh approval for this
   evaluation: five reports, three Before and three After trials each,
   plus extraction; private skill text is sent to the configured Claude
   provider. Default selectors are `opus` for trials and `sonnet` for
   extraction. Previous sessions' approvals do not authorize this one.
4. Initialize a fresh sample using the bundled helper:

   ```bash
   EVAL=.agents/skills/run-behavior-diff-human-evaluation/scripts/evaluate.py
   SESSION=$(python3 "$EVAL" init)
   ```

   Always use the fixed upstream `DataRecce/recce-team`. The helper pins its
   current `main`, generates a new random seed, and samples five eligible
   commits without replacement. Never handpick commits or reuse a saved
   sample. Independent random samples may overlap; disclose known familiarity.
   Keep SHAs, patches, subjects, and correct options out of human-facing chat.

## Prepare and run

5. Follow [case preparation](references/workflow.md#case-preparation).
   For every case, prepare a neutral synthetic decision-point fixture and
   `scenario.json`, then four patch-grounded options in `question.json`.
   Prefer a fresh scenario worker that cannot see the options/answer key.
   The keyed statement must distinguish the anticipated After behavior from
   Before at that decision point, not merely describe behavior true of both.
   Complete the workflow's prefreeze contrast audit in the keyed rationale;
   source support alone does not establish an observable contrast. Keep
   unchanged or weak results.
6. Freeze all five fixtures and audited questions **before** any live trial:

   ```bash
   python3 "$EVAL" freeze "$SESSION"
   python3 "$EVAL" run "$SESSION" --approve-live
   python3 "$EVAL" build "$SESSION"
   python3 "$EVAL" serve "$SESSION" --port 0
   ```

   Pass `--approve-live` only after step 3's approval. Use a managed long-lived
   service for `serve`; give the human the printed loopback URL. The helper
   uses this checkout's code, including uncommitted changes. Never switch to
   the installed plugin, silently retry a case, or change code mid-evaluation.
7. Check actual trial completions, intended revision reads, and generated
   report artifacts. A blocked or unchanged result is evidence, not grounds
   for replacement. Verify the quiz in a browser without submitting answers.
   Do not use the real session for a scoring smoke test.
8. Deliver the URL and instructions: read the summaries, choose one option
   per case, rate confidence, flag insufficient evidence, and submit once.
   Do not show ground truth until submission. Original reports and commit
   links unlock afterward. Artifacts stay outside the checkout and are
   never attached to a public issue or committed.

## Analyze the human's answers

```bash
python3 "$EVAL" results "$SESSION"
```

If no submission exists, say so; never invent a score. Report correct out of
five, confidence, and insufficient-evidence count. Assess question validity for
**all five cases** against saved Before/After answers, source sides, scenarios,
and blinded summaries using [the workflow](references/workflow.md#question-validity-assessment).
Distinguish an observed delta from an unchanged or both-sides match. Retain the
original score and explicitly qualify non-discriminating questions, whether
answered correctly or incorrectly; do not reinterpret them as comprehension
successes or failures. Separate readability, factual fidelity, scenario coverage,
and quiz ambiguity. An explanation-only change is not necessarily a changed
action or outcome.

Chance averages 1.25/5. Five cases may share a skill; this score is not an
estimate of overall product accuracy. Record methodology and aggregate
findings in the evaluation's tracking issue without private excerpts. Do not
rewrite summaries, edit answers, rerun models, or implement fixes unless asked.
