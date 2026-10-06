---
name: run-behavior-diff-human-evaluation
description: Run a private, five-question human evaluation of the current local Behavior Diff summaries using randomly sampled skill commits from DataRecce/recce-team. Use when a maintainer asks for a human evaluation, a blind report quiz, or to evaluate current summary ability; also use to resume, export saved evidence, or analyze local or hosted responses.
---

# Human evaluation of Behavior Diff

Manually run five real comparisons, then ask a human to identify each change
from four shuffled statements. This is a repository-maintainer skill, not
plugin payload. Never trigger it from hooks, CI, or a scheduled job.

## Start or resume

1. For **analyze/resume/export**, use the requested private session's saved
   evidence. Never create fresh trials to answer a request about an existing
   result. Read [the workflow](references/workflow.md) first. Hosted export is
   a local handoff, **not publication permission**: an explicit publication-policy
   update and review of actual outgoing content remain required before upload.
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

## Saved-evidence hosted handoff

Keep the loopback workflow above as a separate supported mode. To export a
saved, frozen, built evaluation without model calls:

```bash
python3 "$EVAL" export-package "$SESSION" \
  --evaluation-id reviewed-cohort --title "Reviewed evaluation" \
  --out "$PRIVATE_EXTERNAL_ROOT/quiz-package"
```

Use a new destination outside both working trees, separate from the private
session; no symlinks or overwrites. The helper verifies frozen inputs and saved
report/quiz receipts, copies the exact blinded summaries, and exports only the
minimal frontend key. It retains provenance privately in the session. Follow
[the v1 contract and approval gate](references/workflow.md#hosted-package-v1).
Do not upload private sessions under the current policy. Synthetic local
emulator compatibility checks do not grant deployment or publication permission.

For a private response export from the site maintainer tooling:

```bash
python3 "$EVAL" hosted-results "$SESSION" \
  --package "$PRIVATE_EXTERNAL_ROOT/quiz-package" \
  --responses "$PRIVATE_EXTERNAL_ROOT/responses.json"
```

Output is private analysis JSON on stdout, including original records, recomputed
scores, and duplicate-name advisories. Never commit it. All UIDs remain separate;
names/emails do not prove identity or independent participants. Assess **all five
cases** using the saved-evidence validity protocol below, not only missed answers.
The helper marks semantic validity `not-assessed`; it does not invent a judgment.
Retain each original keyed score and denominator independently of that assessment.

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
