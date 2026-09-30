# Report intent visibility

**Recorded:** 2026-09-30
**Version discussed:** Behavior Diff v0.3.7
**Status:** Implemented following user approval on 2026-09-30.
**Source:** Skill history replay pilot, `docs/skill-history-replay/README.md`.

## Main finding

A Behavior Diff report shows what differed between Before and After. It does
not show which difference matches the instruction edit. A reader must connect
the two alone, using the file diff that sits collapsed at the bottom of the
report.

In the pilot, two public skill commits were replayed. A fresh verifier wrote
the author's intent from the commit and its PR, then judged each report. Both
reports scored `partial`, and both were uncertain.

| Case | Scenario | Report catch | Weak spot |
| --- | --- | --- | --- |
| Hugging Face `huggingface-datasets` @ `b3df145` | on-target 0.97 | partial 0.52, caught 0.48 | Report: the headline buries the intended change |
| Cloudflare `workers-best-practices` @ `42839d0` | on-target 1.00 | partial 0.58, missed 0.30 | Task: Before already caught every planted mistake |

## How a reader meets each report

### Hugging Face

The author's intent: stop using `npx parquetlens` for SQL, and use
`hf datasets sql` instead.

```
1. Headline      "Final result varies across trials"            noise (local hf crash)
2. Final table   top-10: models 3/3  vs  models 1, datasets 1, none 1   noise
3. Behavior table
     Table choice       models 3/3       vs  models 2, datasets 1     noise
     SQL interface      parquetlens 3/3  vs  hf datasets sql 3/3      <- the intent
     Selected columns   ...              vs  3 different sets         noise
     Failure recovery   retried 3/3      vs  DuckDB 3/3               side effect
     Access checks      none 3/3         vs  token check 1/3          side effect
4. Explanations  about table choice and rankings; the tool switch is not named
5. File diff     collapsed; shows the removed "Querying Datasets" section
```

The intent is in the report. It is row 2 of the second table, and it is the
strongest signal in the run: a clean 3/3 to 3/3 flip. But the headline, the
first table, and the explanations all lead with noise. Nothing tells the
reader that this row matches the edit.

### Cloudflare

The author's intent: list concrete Workers mistakes, such as `Math.random()`
tokens and hardcoded secrets, so the agent flags them.

```
1. Headline      "Final result unchanged; answer details changed"
2. Final table   Do not ship 3/3  vs  Do not ship 3/3
3. Behavior      "unavailable"
4. Explanations  fix snippets, method checks, ranking order
5. Decision rows session IDs, auth comparison: flagged on both sides
6. File diff     collapsed; "Workers Pitfalls" -> "Anti-Patterns to Flag"
```

The evidence honestly shows no effect on the targeted behavior, because the
task was too easy. The report does not say that plainly. "Final result
unchanged" does not tell the reader which behaviors stayed the same, or that
they were the behaviors the edit targets.

## Gaps

| Gap | Seen in | Effect on the reader |
| --- | --- | --- |
| The headline comes from the final answer, not from the rows that changed cleanly | Hugging Face | Noise is the first thing read |
| No link between a diff hunk and the decision row it explains | both | The reader must find the matching row alone |
| A clean flip (3/3 to 3/3) looks the same as a noisy split (2/1) | Hugging Face | The strongest signal does not stand out |
| The file diff sits at the bottom, collapsed | both | The reader sees results before knowing what changed |
| "No change on the targeted behavior" is not stated | Cloudflare | "Unchanged" hides which behaviors stayed the same |

## Proposed changes

1. **Say what the edit changed first.** Put a one- or two-line summary of the
   instruction diff above the results. The reader knows what to look for
   before reading any table.
2. **Rank rows by signal strength.** A row where each side is unanimous and
   the choice flips (Before X 3/3, After Y 3/3) goes first and is marked as a
   strong signal. Rows with split counts go under an "unstable" group.
3. **Link rows to diff hunks.** Show which part of the diff each strong row
   relates to, for example "SQL interface: removed `## Querying Datasets`".
   The reader sees the edit and its effect side by side.
4. **State the no-effect case plainly.** When the behaviors an edit targets
   are the same on both sides, say so by name. For example: "The behaviors
   this edit names (session IDs, secret comparison) were the same on both
   sides."

Changes 1 and 2 need no new model call: the diff is already in the report,
and the counts are already extracted. Changes 3 and 4 need the report to
relate a diff hunk to a decision. That is a model judgment, so it must be
labeled as interpretation, like the existing "Model explanations".

## Expected effect on the pilot

- **Hugging Face:** with changes 1 and 2, the tool switch becomes the first
  strong signal. A re-render and re-verify on the same trials should show
  whether `catch` moves from `partial` to `caught`. No new trials are needed.
- **Cloudflare:** a new report layout alone should not change the verdict.
  Its problem is the task, not the report. Change 4 would make the
  "no effect here" result explicit. A new run with a harder task is still
  needed to test the edit itself.

## Out of scope

- Changing how Behavior Diff drafts its task. The Cloudflare finding
  (planted mistakes too obvious) belongs in a separate task-drafting note.
- An automatic verdict. The report stays evidence for a human reader.
- Knowing the author's intent. The report can only point from the edit to
  the behavior that changed; it cannot see the commit's PR.

## Implementation decisions

- Use **Consistent changes across observed trials**, not a statistical “strong
  signal” claim. Require different unanimous choices, at least two trials per
  side, and complete evidence. Group split and incomplete choices separately.
- Summarize the diff's own changed headings or lines and line counts. Do not add
  a model call or infer the author's intent to write that summary.
- Extend the existing extraction call with numbered diff hunks. Keep observation
  extraction separate from the interpreted relationship to the edit. Validate
  hunk references and bind them to the exact diff supplied to the extractor.
- Preserve primary-result identity and original comparison anchors when changing
  presentation order. Name mapped unchanged behavior only with unanimous,
  complete evidence; equal mixed distributions are not an all-trials no-effect result.
- Stored raw runs can be re-rendered without new trials or model calls. Existing
  extractions gain layout and ranking changes, but need a new, approved extraction
  to acquire semantic edit links. Do not infer those links during rendering.
- Report-data schema 4 records hunk references. Regenerate older report-data
  from raw run artifacts rather than maintaining a parallel legacy schema.

## Verification

Both pilot runs were re-rendered from temporary local copies of their saved
evidence, without changing the original runs or calling a model. Old extractions
retain their observations and explicitly lack edit mappings. No new `catch`
judgment or claim of improved verifier scores was made.

Synthetic report cases exercise a unanimous tool switch amid mixed results and
unchanged targeted findings. Deterministic checks cover ranking, original row
identity, invalid/stale mappings, incomplete trials, and report-data round trips.
Browser verification exercises the rendered reports and cross-tab hunk links.

An Improvement issue with the `behavior-diff` label remains required. The Linear
integration and a local Linear CLI were unavailable during implementation.
