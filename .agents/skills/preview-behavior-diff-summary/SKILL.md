---
name: preview-behavior-diff-summary
description: Builds temporary Behavior Diff summary comparisons from saved Recce-Team evidence using the existing renderer. Use when previewing report hierarchy or navigation changes, comparing outcome-first and rule-first cards, or requesting a before/after UI prototype without live model calls.
---

# Preview Behavior Diff summaries

Compare presentations of the same evidence before changing production behavior.
This is a maintainer workflow, not plugin payload or a human-evaluation run.

## Quick start

Use the three saved Recce-Team cases (`claude-code-review`, `tdd-from-spec`,
and `decision-debate`) listed in `e2e/README.md` under **Default manual
verification examples**. Read `e2e/recce-team-first-edit-attention.md` for pinned
revisions, evidence records, and limits. Resolve saved inputs privately; never
copy them into the checkout. If inputs are unavailable, report the missing case
and evidence rather than silently replacing it with an invented example.

The synthetic gallery (`python3 tests/report-demo.py --serve --port 0`) remains
available for supplemental edge cases, not the default verification set.

## Prepare the comparison

1. State the reader's question and the presentation decision being tested.
   Example: “Can the reader distinguish completed fixes from the final review
   state?” Distinguish report-version labels from instruction Before/After
   labels inside each report.
2. Read the affected renderer/summary contract and locate saved extraction inputs
   for all three cases. Preserve evidence provenance and original reports.
   Never copy private evaluation reports or source excerpts into the checkout.
3. Build paired reports in a fresh temporary directory outside the checkout.
   Inspect the current shipped `decisions.py --ingest` and `render.py` interfaces
   before invoking them. Use identical saved evidence for both renderer versions;
   do not regenerate trials or extraction for a presentation-only comparison.
4. Preserve task, instruction versions, trial names, traces, chain
   choices/memberships, counts, minority branches, and primary outcome. Do not
   author replacement findings to make a case illustrate the proposed change.
   An explicitly requested authored narrative variant must be labeled as such
   and cannot count as verification of generated findings.
5. If comparing renderer implementations instead, feed identical saved inputs
   to each renderer revision. Do not change renderer and authored narrative at
   once unless explicitly comparing both; name every changed variable.
   Reject invalid narratives rather than bypassing ingestion validation.

## Present and verify

6. Create a temporary HTML wrapper around the two rendered reports, not a new
   renderer. Offer side-by-side and full-width views with shareable
   `?variant=compare`, `?variant=before`, and `?variant=after` states. Keep a
   visible switcher and clearly label the two presentation versions.
7. Label saved-evidence comparisons: “Saved Recce-Team trial evidence;
   presentation comparison, no new model calls.” Identify the case and compared
   renderer revisions. Label any authored narrative separately; do not call it
   historical output. Show unchanged evidence and remaining uncertainty,
   including plans versus executed actions. These cases do not establish
   successful historical side-effect detection.
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
