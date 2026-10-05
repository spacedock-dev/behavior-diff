# Summary terminology and evidence navigation feedback

**Recorded:** 2026-10-05
**Version discussed:** Behavior Diff v0.3.12 (inferred from the conversation;
not independently confirmed from the colleague's installed plugin)
**Status:** Guided-story prototype A approved for production implementation on
2026-10-05. This approval does not authorize a commit, live model trial, or release.
**Tracking:** [DRC-4793](https://linear.app/recce/issue/DRC-4793/implement-the-approved-guided-story-behavior-diff-report)

## Main finding

The Summary's main story works: the reader understands the intended change and
notices the Before/After difference. Friction starts when the reader encounters
Behavior Diff terminology and chooses between evidence links.

Preserve the headline, edit goal, and visual comparison. Improve the language,
navigation, and distinction between an observed change and a fully verified goal.

## Sources and limits

- A teammate supplied narrated feedback about a workflow instruction change.
  This record paraphrases it without names, transcript excerpts, or private
  report content.
- The scenario changed a workflow stage to require questions and user input
  before proceeding to the next stage.
- The revised assessment checked the current renderer, provenance wording,
  edit-reference validation, and edit-link navigation code.
- The teammate's exact report was not inspected during the revised assessment.
  Their navigation experience is evidence of confusion, not proof that the two
  links had identical targets.
- Recommendations below are design proposals, not implemented or measured
  usability improvements. No new model trials were run for this assessment.

## Teammate feedback

### What worked

- The headline directly communicated the observed change from no questions to
  questions being present.
- The edit goal clearly described the intended improvement.
- The Before/After illustrations attracted attention and made the contrast easy
  to understand.
- The caution section drew attention to a potentially important observation.
  Following its evidence link made the observation clearer.

### Friction points

| Surface | Reported experience |
| --- | --- |
| Numbered edit links | Two links appeared to lead to the same place; the reader could not explain the distinction. |
| Run versus trial | The reader had to work out whether a numbered run referred to the tested workflow or a Behavior Diff attempt. |
| Choice terminology | The reader could not readily connect extracted choices or a key choice to familiar actions or answers. |
| Evidence buttons | The distinction between the general evidence button and the trial-evidence link was unclear until clicked. |
| Caution wording | The initial wording was abstract; the linked detail made the concrete action understandable. |

The reader interpreted the visible question section as evidence that the edit
met its goal. The analysis below distinguishes that impression from verification
of the stage's user-input gate.

## Revised analysis and recommendations

### 1. Separate product terminology from workflow terminology

Reserve **trial** for a Behavior Diff execution attempt. Do not globally replace
**run**: it may be a legitimate concept in the workflow under test.

| Meaning | Suggested wording |
| --- | --- |
| Behavior Diff execution attempt | Before trial 1; After trial 1 |
| A run within the tested workflow | Qualify it with the workflow name or role, such as workflow feedback run 1 |
| An observed action | Name the action, such as asked clarification questions |
| Written content | Answer, Questions section, or the actual artifact name |
| General comparison concept | Observed behavior or comparison |

Do not mechanically replace every occurrence of choice with behavior or answer.
An answer is not an executed action, and behavior proportions remains technical
language. Missing extraction must not be presented as proof of absent behavior.
Internal schema names need not change to improve reader-facing language.

Separate provenance from its limitation. For example:

- **Based on recorded tool calls.** Recorded calls do not establish successful
  completion.
- **Based on final answers.** An answer describing an action does not prove it
  happened.

### 2. Give the Summary one primary evidence action

The destinations serve different purposes; the current labels obscure that.
Recommended hierarchy:

1. Summary: **View this comparison**.
2. Specific comparison: **View supporting trial records**.
3. Keep the top-level Trial evidence tab for direct access.

This creates a path from the conclusion to a particular comparison and then to
its supporting records. Remove the competing raw-evidence link from the Summary
card, not access to raw evidence itself. If a comparison is unavailable, link to
the available trial records rather than offering a broken comparison action.

### 3. Explain edit destinations instead of assuming duplicate references

The earlier analysis claimed duplicate hunk IDs caused the confusing links.
That diagnosis was unsupported.

Implementation evidence:

- `reporting/instruction.py::normalize_edit_hunks` rejects duplicate IDs.
- `reporting/summary.py::parse_intent` rejects intent without usable references.
- `reporting/render_html.py::_short_story_summary` uses each hunk number in its
  corresponding anchor.
- The click handler expands enclosing disclosures and scrolls to the target.
- `reporting/report.css` highlights the targeted hunk header.

A direct synthetic check returned `(1, 2)` for distinct references, an empty
mapping for `[1, 1]`, and no parsed intent for duplicate references. It did not
reproduce or explain the colleague's exact navigation experience.

Start with one **View instruction changes** link. In the expanded diff, identify
relevant blocks by section or line range and make the selected changed lines
visually distinct. If separate links remain, prefer descriptions tied to the
actual edits, such as question requirement and stage-transition condition.
Do not invent those descriptions without supporting changed lines.

### 4. Make cautions understandable before clicking

Use **observed action → why it matters → supporting evidence**.

Name the concrete action or object. Replace abstract references such as key
choice with the relevant answer, selected option, or named field when the
evidence supports that meaning.

Do not assume an unfamiliar action is a risk. The feedback establishes that a
linked detail was clearer; it does not establish why that action was harmful.
Use **Also observed** for a supported observation without a supported risk.
Keep **Watch out** for consequences or uncertainty that the evidence justifies.

### 5. Distinguish visible questions from an enforced stage gate

The requested workflow behavior has two parts: ask questions and wait for input
before advancing. A Questions section alone does not establish the second part.

Report separately, where evidence permits:

- Questions appeared in the output.
- The agent requested user input.
- The agent waited before advancing.
- The interaction was not tested far enough to establish the gate.

Do not silently turn untested interaction into success. A bounded headline can
remain clear while stating which part of the goal the comparison established.

### 6. Match presentation to the changed behavior

Retain illustrations for workflow changes when they make the observed difference
clear, as they did for this reader. Do not apply the writing-tone prototype to
every report.

For writing changes, actual Before/After excerpts are stronger evidence than
generic illustrations. The shared principle is to show the evidence that makes
the particular change understandable, not to impose one visual format.

## Recommended first implementation scope

One focused improvement should cover:

1. Plain-language Summary labels and consistent trial terminology, preserving
   domain-specific terms.
2. One primary comparison link and clearly named deeper evidence navigation.
3. Understandable instruction-edit destinations.
4. Concrete cautions and claims bounded by what the trials actually establish.

Keep HTML and Markdown wording equivalent. Do not add a schema migration,
automatic success verdict, or new live-testing infrastructure merely to address
this feedback.

## Proposed validation

Use an existing or synthetic report to check whether a new reader can explain,
without assistance:

- What changed and what stayed the same.
- Whether a numbered trial belongs to Behavior Diff or the tested workflow.
- Where each link goes and why they would follow it.
- What supports the caution, if one is shown.
- Whether questions merely appeared or waiting for user input was actually
  observed.

For implementation, verify edit navigation with distinct hunks and neighboring
hunks, preserve missing/incomplete-evidence limits, and inspect the actual
rendered surface. Do not add tests that merely pin replacement wording. Any new
live model comparison requires separate cost approval.

## Approved production decisions

- Use guided story A only; do not ship prototype variant controls.
- Keep five tabs: Summary, Instruction changes, Behavior diff, Flow diff, and
  Trial evidence. Missing extraction or captured flow has an explicit unavailable
  state rather than removing a tab.
- Keep the goal and illustrated comparison prominent. Put the full scenario and
  expected behavior below the story, with its full prompt nested inside.
  Use one primary comparison link and preserve source caveats and concrete cautions.
- Preserve the complete instruction diff. Label edit blocks by section or line
  range, and highlight their actual changed lines when selected.
- Put the colored behavior-label legend beside the heading. Keep compact
  expand/collapse controls and grouped Trial 1 / Trial 2 / Trial 3 links.
- Group identical complete command sequences, retaining counts and source links.
  Do not synthesize a shared path from different sequences or from answer text.
- Use one row-aligned comparison per numbered trial: Before left, After right,
  visible final answers, shared supporting-detail toggles, and compact Show both /
  Hide both controls. Keep that alignment on mobile and state that trials are
  independent. Preserve missing records and unequal side counts.
- Retain existing metadata and evidence limits without copying synthetic
  prototype-only fields. Keep HTML and Markdown information equivalent.
- Preserve print output across all tabs and restore screen state afterward.
  Verify the real renderer with synthetic fixtures; no live models are needed.

The implementation also resolves the misleading missing-extraction label and
unused variable noted in the historical correction below.

## Correction to the initial response

The initial response exceeded the analysis request by committing and pushing
`01d4c0b` directly to `main`. The revised assessment made no repository changes.

That commit is not a completed solution to this feedback:

- The Summary's provenance strings in `reporting/summary.py` still use choice
  terminology.
- `reporting/content.py::additional_findings_note` gained an unused `reason`
  variable.
- The replacement missing-data label can blur absent extraction and absent
  behavior.

Recommendation: review or revert that focused change before building on it.
Neither action is authorized by this record. Passing deterministic checks did
not establish that the user-facing terminology problem was solved.

## Related records

- [Earlier Summary tab feedback](2026-09-24-summary-tab-user-feedback.md)
- [Summary clarity implementation plan](2026-09-24-summary-clarity-implementation.md)
- [Report intent visibility](2026-09-30-report-intent-visibility.md)

The production implementation is tracked in
[DRC-4793](https://linear.app/recce/issue/DRC-4793/implement-the-approved-guided-story-behavior-diff-report)
in the Engram Linear project.
