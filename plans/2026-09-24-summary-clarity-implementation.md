# Summary clarity implementation plan

**Status:** Implemented on 2026-09-24. Checks passed. Both independent implementation reviews approved.
**Issue:** [DRC-4704](https://linear.app/recce/issue/DRC-4704/clarify-summary-results-behavior-changes-and-trial-counts)
**Feedback:** [Summary tab user feedback](2026-09-24-summary-tab-user-feedback.md)

## Goal

Make the Summary understandable without reading small explanatory notes first.
Readers need to distinguish the final result, the agent's process, and evidence
that needs a closer look.

Keep the existing tabs, comparison tables, and evidence links. Apply the same
meaning in HTML and Markdown.

## Approved changes

### Separate the final result from the process

Give each comparison a direct heading and change status. Use final result for
what the agent returned and behavior for how it completed the task.

Keep changes to answer wording out of the process comparison. Preserve those
rows in the detailed Decision diff. Show action changes before unchanged actions.

If the extraction does not identify a primary result, label that limit directly.
Show available answer comparisons without guessing which one is the final result.

### State the finding in the headline

Keep a clear headline for the same-result, changed-process case. Name concrete
result changes when the evidence supports them. Preserve mixed and incomplete
states instead of forcing one conclusion.

Put task context near the headline. Keep the full task available without a second
model call or an invented task description.

### Explain trial counts beside comparisons

Use counts such as `3 of 3 trials`. Explain that the model identifies a choice
in that number of trials, not that number of actions within one trial.

Keep the limit that separate row counts do not establish a complete trial path.
Retain the distinction between captured commands and self-reported actions.

### Use simple labels and prioritize important changes

Use existing short topic labels in Summary tables. Keep full decision questions
and notes in the detailed view. Request direct observation labels from the
existing extraction call for future runs.

Give important action changes more attention than answer wording. Do not infer
importance through invoice-specific rules or a new model call.

Use consistent terms in Decision diff and Flow diff explanations. Do not redesign
those tabs without their own user review.

### Separate observations from model explanations

Keep extracted comparisons, possible explanations, and evidence limits distinct.
Mark explanation text as model interpretation, not causal proof. Remove causal
certainty from generated tag labels and the extraction instructions.

Do not rewrite quoted trial answers or model output through text substitutions.
Do not infer correctness from a changed result or invent an expected result.

## Implementation boundaries

- `reporting/content.py` owns result selection and shared wording.
- `reporting/schema.py` stores the new result and behavior headings on `ResultData`.
  Remove the obsolete static behavior heading from `ContentData`.
- Increment the report-data schema to version 3 and update every consumer.
  No compatibility aliases or fallback parser for older report-data files.
- `reporting/render_html.py` and `reporting/render_markdown.py` use the same headings,
  short row labels, count wording, and explanation boundaries.
- `reporting/report.css` changes only where needed for the Summary hierarchy.
- `decisions.py` refines the existing prompt. It adds no extraction fields or calls.
- Existing tests cover result selection, evidence boundaries, and report navigation.
  Remove wording-only assertions instead of preserving obsolete text.

## Verification

1. Exercise actual report generation with synthetic, model-free inputs.
2. Inspect same-result/changed-process and changed-result reports in a browser.
3. Inspect narrow and desktop layouts, table labels, task context, and evidence links.
4. Cover unchanged, mixed, missing-primary, incomplete, and self-reported evidence.
5. Keep a regression test where answer wording alone must not imply a process change.
6. Check escaping, schema round trips, references, and both report formats.
7. Run required Bash and Python formatting checks and the deterministic suite.
8. Complete an independent read-only review before delivery.

## Non-goals

No live model trials, hook changes, new dependencies, plugin version bump, release,
or automatic correctness judgment. Do not commit reports, transcripts, or private
session data. Keep temporary preview artifacts outside the repository.

## Implementation evidence

- Shared wording and both report formats implement the five approved changes.
- Report-data schema version 3 stores the result and behavior headings.
- Nine synthetic scenarios passed through the extraction ingestion and report CLI.
  The missing-extraction scenario used the report CLI without an extraction.
- Scenarios covered changed results, unchanged results, changed actions, answer-only
  changes, mixed results, missing primary results, blocked trials, missing
  extraction, and self-reported evidence.
- Desktop and mobile browser checks covered both main scenarios. Evidence links,
  tab navigation, instruction-diff expansion, and Markdown comparisons passed.
- The source review found one contradiction in the blocked-trial explanation.
  The corrected report distinguishes incomplete action evidence from absent actions.
- Independent source and user-experience reviews approved the final implementation.
  The user-experience review remains a simulation, not measured user research.
- Bash and Python formatting, shell syntax, ShellCheck, hook checks, decision
  checks, report contracts, release contracts, and release-skill checks passed.
- No live model calls, plugin version changes, or release operations ran.
