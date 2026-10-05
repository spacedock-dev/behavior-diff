---
name: preview-behavior-diff-summary
description: Builds temporary, synthetic Behavior Diff summary comparisons using the existing renderer. Use when previewing report hierarchy or navigation changes, comparing outcome-first and rule-first cards, or requesting a before/after UI prototype without live model calls.
---

# Preview Behavior Diff summaries

Compare presentations of the same evidence before changing production behavior.
This is a maintainer workflow, not plugin payload or a human-evaluation run.

## Quick start

From the repository root:

```bash
python3 tests/report-demo.py --serve --port 0
```

Open the printed loopback URL. The existing gallery uses synthetic fixtures,
shipped ingestion, and the shipped renderer; it makes no model calls. Keep the
server running for review. Ctrl+C stops it and removes its temporary directory.

## Prepare the comparison

1. State the reader's question and the presentation decision being tested.
   Example: “Can the reader see the changed retry interval without expanding
   Other findings?” Distinguish report-version labels from instruction
   Before/After labels inside each report.
2. Read `tests/report-demo.py`, `tests/report_fixtures.py`, and the affected
   renderer/summary contract. Choose representative synthetic evidence. Include
   mixed branches or an unchanged result when they matter to the decision.
   Never copy private evaluation reports or source excerpts into the checkout.
3. Build paired reports in a fresh temporary directory outside the checkout.
   Use the existing fixture builder, ingest command, and renderer invocation
   from `build_reports` in `tests/report_fixtures.py`; inspect current signatures
   rather than copying an old invocation. For a throwaway driver, put `tests`
   on Python's import path and restrict the fixture catalog to the selected
   scenario before calling `build_reports` on an empty directory.
4. Copy that generated scenario into two sibling variant directories. Preserve
   task, instruction versions, trial names, traces, chain choices/memberships,
   and primary outcome. For a narrative comparison, change only the selected
   summary row and its supported narrative in each `extraction.json`, then run
   the same shipped `decisions.py --ingest` and `render.py` commands in each copy.
   Do not alter counts or hide minority branches to improve the illustration.
5. If comparing renderer implementations instead, feed identical saved inputs
   to each renderer revision. Do not change renderer and authored narrative at
   once unless explicitly comparing both; name every changed variable.
   Reject invalid narratives rather than bypassing ingestion validation.

## Present and verify

6. Create a temporary HTML wrapper around the two rendered reports, not a new
   renderer. Offer side-by-side and full-width views with shareable
   `?variant=compare`, `?variant=before`, and `?variant=after` states. Keep a
   visible switcher and clearly label the two presentation versions.
7. State on the page: “Authored synthetic illustration; no model was called.”
   Do not call an authored baseline a historical report. Show unchanged evidence
   and remaining uncertainty, including plans versus executed actions.
8. Serve only the temporary root on loopback, for example:

   ```bash
   python3 -m http.server 8767 --bind 127.0.0.1 --directory "$PREVIEW_ROOT"
   ```

   Set `PREVIEW_ROOT` to the fresh directory from step 3; select another local
   port if occupied. Use a managed persistent service while awaiting feedback.
9. Open the actual page in a browser. Exercise view switching, URL reload,
   full-width links, and expanded findings. Check desktop and narrow layouts,
   including iframe overflow and the visibility of operative details. Capture
   a screenshot when available; if capture fails, report the limit separately
   from successful DOM and interaction checks. Do not submit a real quiz.
10. Share the URL and explain the single decision to review. An authored preview
    proves presentation of supplied content, not extractor adherence or improved
    comprehension. Live extraction and human evaluation require their own
    approved workflows; do not launch either as part of this skill.

## Finish

Record the accepted presentation and rationale in the tracking issue or commit
message. Stop the preview service and remove only its owned temporary directory
when the user has finished reviewing; do not stop unrelated evaluation servers.
Implement the accepted change in canonical production files and add meaningful
synthetic regression coverage where needed. Delete the comparison wrapper and
losing variants rather than shipping a permanent prototype route. No new test
is needed merely to assert this skill's wording.
