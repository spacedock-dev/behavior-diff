# Summary tab user feedback

**Recorded:** 2026-09-24
**Version discussed:** Behavior Diff v0.3.6
**Status:** Feedback recorded. The user approved implementation on 2026-09-24.
**Plan:** [Summary clarity implementation](2026-09-24-summary-clarity-implementation.md).

## Main finding

The Summary shows useful evidence, but readers need time to separate the final
result from how the agent reached it. Readers notice the headline and tables
before they read the small explanatory text.

Each table needs to explain its purpose through its heading and labels. Small
text can add detail, but it cannot carry the main explanation.

## Sources and limits

- A colleague provided feedback after a real trial of a skill for PR descriptions.
  This record paraphrases that feedback without names or transcript excerpts.
- An independent subagent reviewed the published Summary for a synthetic invoice
  example as a first-time user. Its reactions were simulated, not measured user
  feedback.
- The main agent inspected the same Summary and supporting trial evidence.
- The two cases differ. The colleague saw the same result with a changed process.
  The simulated review examined a changed verdict and changed process.
- This record concerns the Summary tab. It does not establish usability findings
  for the separate Decision diff or Flow diff tabs.

## Colleague feedback: same result, different process

### Task and instruction change

The colleague used a simple skill for PR descriptions. The edit added rules to
exclude out-of-scope work and changes discussed during the session.

The headline clearly communicated that the result stayed the same while the
process changed. The colleague then wanted to understand that process change.

### Reading sequence

1. Read the headline and understood that the result stayed the same.
2. Looked at the first Before/After table and saw matching values.
3. Looked for the process change mentioned in the headline.
4. Found another table under Behavior change and noticed differences.
5. Returned to the small text to understand the purpose of each table.
6. Needed another read to connect the terms outcome, decision evidence, and
   decision distribution.

### Points of confusion

- The first table did not immediately identify itself as the final-result
  comparison. The second table did not immediately resolve the distinction.
- Outcome and decision terminology appeared together without a clear connection.
- The sentence about counts describing each step was unclear. A count could mean
  trials with a behavior, actions within one trial, or steps.
- The reader found the explanatory text only after studying the tables.

### Positive feedback

- The main headline worked for the same-result, changed-process case.
- The tables attracted attention and made Before/After comparison possible.
- The Behavior change explanation became understandable after a closer read.

## Simulated review: changed result and process

### Overall reaction

The reviewer found useful evidence but needed to assemble the main story from
separate sections. Confidence increased after reading the instruction diff and
limits, but the reading effort also increased.

The synthetic example showed HOLD before and APPROVE after, with three trials
on each side. The behavior comparison also showed a change in payment-history
checks.

The reviewer wanted to inspect that behavior change before judging the instruction
edit. The Summary supported investigation, not an automatic correctness decision.

### Points of confusion

- The headline, `Reported answers changed in these trials`, was less informative
  than the verdict comparison in the first row.
- Terms such as `answer dimensions` and `mixed task outcomes` interrupted the
  explanation. The verdicts agreed within each side.
- Five result rows appeared before the Scenario. The reader needed to scroll to
  understand the task and the instruction change.
- Changes in answer wording received similar visual weight to an omitted check.
  Those differences did not have equal practical importance.
- Some row labels sounded like instructions rather than observations.
  `Withholding the full procedure` was particularly hard to interpret.
- The model explanation used `determines` for a causal claim. The Model
  interpretation label helped, but the verb still sounded conclusive.

### Positive feedback

- Before/After columns and trial counts made differences concrete.
- Labels such as `from the reply` and `from a command` distinguished evidence types.
- Evidence links provided routes to the decisions and trial results.
- The expandable instruction diff supplied context without leaving Summary.
- Evidence limits correctly restricted the conclusions that the reader could draw.

## Combined priorities

| Priority | Problem | Proposed direction |
| --- | --- | --- |
| 1 | Result and process tables are hard to distinguish. | Give each table a direct heading that names its purpose and change status. |
| 2 | Technical terms interrupt understanding. | Use result and behavior consistently in the main explanation. |
| 3 | Count meaning is unclear. | Explain the unit beside the table, not only in a later note. |
| 4 | Readers must assemble the main story. | Put the result, important behavior change, and task context near the top. |
| 5 | Some statements imply more certainty than the evidence supports. | Separate observations, model explanations, and open questions. |

The headline needs case-specific wording. It worked for the colleague's case,
but it was too general in the synthetic invoice example.

The tables and evidence links remain useful. These findings support clearer
content and labels, not a complete redesign.

## Proposed wording direction

Use two questions throughout the Summary:

- **Result:** What did the agent return?
- **Behavior:** What did the agent do?

For a same-result, changed-process case, possible wording is:

> **Same result, different process**
>
> The final result stayed the same. The agent changed how it completed the task.

Possible table headings are:

- **Final result — unchanged**
- **Behavior — changed**

For a count based on model extraction, explain its meaning directly:

> **3 of 3 trials** means the model identified this behavior in all three trials.
> It does not mean three actions within one trial.

Keep the distinction between individual observations and complete trial sequences.
Counts for separate rows do not establish a complete path through an individual
trial.

Prefer observation labels such as **Review verdict**, **Reason given**, and
**Records inspected** over abstract decision questions in the Summary.

Keep model explanations separate from observed changes. Preserve evidence limits
and do not infer that a behavior change is an improvement.

## Questions for the next design

- Can a reader identify the result and process tables without reading the notes?
- Does the headline state the concrete change, or clearly state that the result
  stayed the same?
- Can a reader explain what each count measures?
- Does the Summary distinguish important behavior changes from answer wording?
- Does it explain the task before technical caveats interrupt the main story?
- Can a reader distinguish observations from model explanations?
- Does it identify useful evidence to inspect without inventing a correctness
  judgment?

## Scope of this record

The planned wording work also includes behavior and flow comparisons. This record
captures the available Summary feedback only. Those separate views need their own
user review before this feedback can support conclusions about them.

No product behavior, report wording, or release state changed as part of this
record.
