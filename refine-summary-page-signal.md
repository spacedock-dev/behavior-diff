---
title: Refine the summary page to make the main result clear
status: ideation
source: Captain-requested follow-up from case-01-auto-download-audio.md
started: 2026-10-21T10:11:41Z
completed:
verdict:
score:
worktree:
issue:
linear:
pr:
mod-block:
id: dmz5fz1edtpmyc9vx28ez15w
gates:
    version: 1
    records:
        - id: gate:dmz5fz1edtpmyc9vx28ez15w:backlog
          stage: backlog
          attempts:
            - id: gate-attempt:dmz5fz1edtpmyc9vx28ez15w-backlog-1
              briefing:
                id: briefing:dmz5fz1edtpmyc9vx28ez15w:backlog:attempt-1:revision-1
                digest: sha256:c15512c10bb7a53ce28bdec0a02f23d6d046244eef52d83ce23b5c038e6b3ee5
                room-ref: ./refine-summary-page-signal/review/backlog/briefing-1
              resolution:
                type: Resolution
                id: resolution:spacedock:dmz5fz1edtpmyc9vx28ez15w:backlog:1
                briefing: briefing:dmz5fz1edtpmyc9vx28ez15w:backlog:attempt-1:revision-1
                by: person:captain
                at: "2026-10-21T10:11:26.688086Z"
                decision: approve
                reason: Captain approved the presented backlog gate to start ideation only.
              application:
                target-stage: ideation
                state: consumed
        - id: gate:dmz5fz1edtpmyc9vx28ez15w:ideation
          stage: ideation
          attempts:
            - id: gate-attempt:dmz5fz1edtpmyc9vx28ez15w-ideation-1
              briefing:
                id: briefing:dmz5fz1edtpmyc9vx28ez15w:ideation:attempt-1:revision-1
                digest: sha256:70462b0098d1bc3ca99bfb286713d68523d524a559f0dbfc350d64444face72f
                room-ref: ./refine-summary-page-signal/review/ideation/briefing-1
---

Help readers understand the main Before/After result at a glance without
repeated uncertainty and secondary checks overwhelming the summary.

## Problem

The source case identifies a summary-page clarity problem: the main outcome
requires close reading, while repeated caveats distract from it. Improve the
information hierarchy without suppressing a material risk or implying that
untested behavior is safe.

## Proposed approach

Direction for later ideation, not an approved layout: lead with the tested
question and observed Before/After result; consolidate repeated qualifications;
keep important uncertainty visible once and retain access to supporting detail.
Use the existing preview workflow and renderer with evidence held constant.

## Risk evidence

Source: `../spacedock-strategy/projects/behavior-diff/case-01-auto-download-audio.md`,
“What the final demo report showed” and “What we keep and what we stop”.
Read the original in the local strategy checkout when designing. Do not copy
private reports, trial excerpts, or recordings into this state branch. The case
motivates this task; it does not prove additional product value or general safety.

## Expected surface and tolerance

Not estimated at backlog intake. Bound the summary/rendering surface and any
necessary extraction-contract changes during ideation before implementation.

## Acceptance criteria

Draft outcomes to refine with the Captain during ideation:

**AC-1 — The main tested question and Before/After result are understandable from the summary.**
Verified by: interactive comparison of current and proposed rendered summaries
using unchanged evidence; ask the reader to identify the outcome and its scope.
A reader still needing the detailed report to find the primary result fails.

**AC-2 — Repeated caveats no longer crowd out the outcome, without losing material uncertainty.**
Verified by: inspect rendered previews against the underlying evidence; show a
consolidated qualification and a reachable detail path. A missing material limit,
repeated equivalent warnings, or unsupported success claim fails.

## Test plan

Preview before implementation using the repository-required cases. Separate
presentation improvement from changes to evidence generation. Select relevant
renderer/contract checks once the design is approved; no live rerun authorized
by this backlog request.

## Decisions and dependencies

Captain requested backlog capture only; no design, implementation, or delivery
approval. Related task: `verify-overall-skill-behavior-value`; neither task is
blocked on the other. Do not require a whole-skill feature to reduce report noise.

### Feedback Cycles

None; design and review have not started.

## Out of scope

A new simulator, repeated generator tuning, hiding material failures, claims of
full-workflow time savings, and treating this case as proven product success.

## Ideation proposal — awaiting Captain decision

### Reader question and recommendation

Can a reader identify the observed Before/After change, its evidence level,
and what remains unproved without reading the detailed report?

Recommend **observation first, coverage second**. This is a presentation-only
change, not a more optimistic verdict or a new way to choose the main finding.
Keep the existing extracted lead, canonical primary-result identity, and
validated overall check state distinct:

1. **Observed Before / After:** existing comparison heading, evidence-level
   label, compact Before/After cards with every branch and count, then the
   instruction aim with its existing provenance. Remove decorative illustrations
   from this compact comparison. When the lead differs from the canonical
   primary result, show that primary result and its full distribution nearby.
2. **Scope and attention:** keep material cautions, incomplete/mixed evidence,
   unavailable attention, and attention findings visible. Give report-wide
   qualifications one home rather than repeating them in each summary section.
   Do not deduplicate different claims merely because both sound cautious.
3. **What these tests establish:** retain the canonical overall finding and
   grouped check states. Keep every accepted unmet check visible by name.
   Put the full check table, rejection reasons, and unresolved-question detail
   behind one clearly labeled disclosure. Distinguish not settled, not assessed,
   and no check; none becomes a pass. Keep the existing next-action guidance.
4. **Test context and interpretation:** expandable setup/full task, model
   interpretation, and comparison-start context. Keep direct links to the
   unchanged instruction, comparison, explanation, and trial-evidence panels.

“Main result” in this task means the salient observed comparison, not permission
to relabel a secondary process change as the canonical primary outcome.
The prototype explicitly exposes this distinction, including an unchanged
primary result alongside a changed lead. Model wording is retained, not
rewritten into a stronger success claim.

**Simplest alternative:** retain the current five-step order and only collapse
the long check table and unresolved-question list. It requires fewer rendering
changes, but leaves the comparison far down the page and retains repeated
summary explanations. It is available as a separate preview, not recommended.
Any production version of either option must leave accepted failures visible.

### Preserved behavior and non-goals

Preserve tasks, instruction revisions, trial names and membership, choices,
counts and minority branches, raw traces, primary outcome, goal/check mapping,
rejection states, provenance, and all uncertainty. Preserve the existing
not-met precedence over an attractive process change. Detailed evidence remains
reachable; collapsing repeated presentation is not deleting evidence.

Change only hierarchy, compact comparison styling, disclosure defaults, and
placement of existing text. No extraction prompt/schema, assessment rules,
lead-selection rules, scenario generation, runner, model calls, or grading
changes. No compatibility repair by inventing missing findings. No product-wide
success claim, historical side-effect-detection claim, or automatic approval.
The existing whole-skill-value task is independent.

### Preview and observed evidence

Baseline renderer: `9f5461805394ecfa6aa10388588b94355dbfe6e7`.
Current, proposed, and simpler-alternative reports were rendered from the same
loaded report object for each of the three required pinned Recce-Team cases.
The only compared variable is summary HTML presentation; no authored replacement
narrative, trial rerun, extraction call, or paid model call was made.

Local review surface: <http://127.0.0.1:8794/?case=review&variant=compare>.
Cases: `review`, `notes`, `routing`, and supplemental `audio`.
Views: `compare`, `before`, `after`, and `alternative`. The wrapper labels report
versions separately from instruction Before/After and links the original
historical reports separately. All private artifacts remain outside the checkout.
The service is local and temporary; receipts and screenshots are private gate
evidence, not portable repository fixtures.

Observed at a 1440-pixel desktop width, with disclosures closed:

| Case | Current comparison offset | Proposed offset | Current/proposed visible words |
|---|---:|---:|---:|
| Review workflow | 1,441 px | 255 px | 514 / 299 |
| Scratch notes | 1,420 px | 206 px | 562 / 351 |
| Decision routing | 1,420 px | 206 px | 543 / 336 |
| Supplemental audio rerun | 3,996 px | 206 px | 1,714 / 502 |

Offsets are measured from the summary container to the Before/After cards,
not from the page top. These are layout observations, not evidence of improved
human comprehension. The simpler alternative leaves those offsets at
1,412 / 1,390 / 1,390 / 2,365 px respectively.

Chromium exercise covered all four cases at 1440 and 390 pixels: view switching,
reload-stable URLs, disclosure expansion, trial-tab activation, and no document
or wrapper horizontal overflow. The check table scrolls within its container.
A full-width link opened the expected report, keyboard view switching worked,
and a check link revealed its evidence target. Desktop and narrow screenshots
were captured. Supporting-panel DOM content was identical across current and
proposed for every case; frozen-input hashes and original chain choices,
counts, anchors, edit mappings, and membership were unchanged.

**Evidence limitations, not silently repaired:**

- All three first-edit Recce reports contain schema-11 attention assessments that
  the current loader does not accept. Both compared versions correctly show
  unavailable, not an assessed-empty result. Original historical reports remain
  linked; their assessment and the review case's minority branches were inspected.
  Thus these pairs do not prove current-schema rendering of those historical
  attention findings. Their chain, narrative, and explanation are retained.
- The source strategy case's 13-check run is available only as a conversation
  reconstruction whose record says raw trial files are unavailable. It was read
  for context, not passed off as a replayable extraction input. The supplemental
  preview uses the separately saved later raw-evidence audio rerun, with 15 checks,
  and labels that distinction. Neither represents a real external workflow.
- No reader study or real quiz was run. No implementation tests, builds, lint,
  or formatters were run during ideation.

### Implementation boundary, size, and dependencies

One focused implementation PR after design approval, not a separate prototype
product. Expected canonical files are `reporting/render_html.py`,
`reporting/render_markdown.py`, `reporting/content.py`, and
`reporting/report.css` under `plugin/skills/behavior-diff/scripts/`, plus
`tests/presentation_contract.py`, `tests/target_contract.py`,
`tests/report-schema-test.py`, and `docs/architecture.md`.
HTML and Markdown must retain the same conclusions and evidence access even
though native HTML disclosures have no identical Markdown interaction.

[INFERENCE] Estimate: 6–9 files and approximately 300–500 changed lines, with
35% tolerance. Revisit ideation if the work requires extraction/schema changes,
lead-selection changes, additional production components, or more than 675
changed lines. No new dependency, model approval, or permanent preview route
is required. Use the existing renderer, native disclosures, and tab router.

Implementation requires an assigned code worktree and Captain approval of the
hierarchy. Copy only the accepted design into that worktree if a plan artifact is
needed; never copy private preview evidence into it. Retire the losing variants
and owned temporary service after the Captain finishes review. Legacy attention
compatibility is an explicitly separate concern, not silently added to this PR.

### Falsifiable acceptance and verification plan

| Criterion | Finished outcome and falsifying check | Mode |
|---|---|---|
| AC-1: result recognition | Counterbalanced reading of the same four saved cases: four readers each see two current and two proposed reports, each case once; each case/version gets two readers. Ask for the observed change, counts/scope, and whether all expectations passed. Proposed must yield at least 7/8 correct main-result answers, no worse accuracy than baseline, and at least 25% lower median time to a correct answer (60-second cap; wrong answers count as capped). Any plan-as-execution or unqualified-all-pass answer fails the safety criterion. No result is claimed until this is performed with Captain-approved participants. | Interactive, human |
| AC-2: unchanged evidence | Render both versions from identical frozen input; compare serialized report data and all non-summary panels. Synthetic checks cover mixed/minority branches, unchanged primary with changed process, interrupted/missing trials, and no usable comparison. A changed count, membership, outcome identity, or data object fails. | Offline |
| AC-3: visible material uncertainty | Synthetic mixed supported/rejected/unsettled results and an accepted preservation failure must retain their exact states; failure titles and incomplete/mixed evidence must remain visible without expansion. Rejected is not uncertain or passed. All frozen checks and uncovered goals remain reachable. Hiding a failure or implying missing evidence is success fails. | Offline plus interactive |
| AC-4: one summary home | Each report-wide qualification appears once in the default summary; detailed evidence may repeat its necessary local qualification. Every check remains in the expanded table with its original reason and evidence link. Removing a distinct limit to reduce repetition fails. | Offline |
| AC-5: usable navigation and density | At 1440 and 390 pixels, compare/single views and URL reload work, native disclosures are keyboard operable, all evidence links activate and reveal the correct target, and overflow stays inside the check table. In each saved case, proposed comparison offset must be at most 300 px below the summary start on desktop and at least 50% lower than current. Narrow readers can see both complete cards after reaching the summary, without horizontal scrolling. | Interactive |
| AC-6: output/host parity | HTML, artifact HTML, and Markdown preserve the same observation-versus-verdict distinction, failure precedence, counts, and evidence destinations. Synthetic captured-tool, self-reported, and answer-only evidence must not be upgraded by presentation. Mutating one renderer to show a pass or executed action must fail the contract check. | Offline |

After implementation, the verification owner should run
`python3 tests/report-schema-test.py` (including its presentation and target
contracts), `python3 tests/report-source-test.py`,
`python3 tests/report-ci-context-test.py`, and
`bash tests/live-report-contract.sh`, plus repository-required formatting/static
checks. Add meaningful synthetic assertions for the accepted hierarchy, rather
than merely changing snapshots or checking that prose exists.
Repeat the saved-case browser exercise; legacy attention rendering remains an
explicit limit unless separately authorized evidence resolves it.

### Captain decision needed

Approve the observation-first hierarchy or choose the simpler disclosure-only
alternative. Specifically confirm that a clearly scoped observed change should
lead while overall check coverage remains distinct, accepted failures stay
visible, and full secondary detail is expandable. Acknowledge the legacy-attention
and original-audio evidence limits; neither authorizes a model rerun.
Approve the proposed reader-comprehension threshold before implementation.
No design acceptance, implementation authorization, or product-value success
has been inferred from this ideation exercise.

## Stage Report: ideation

- DONE: Recommend a bounded summary design and simplest alternative, identifying preserved meaning, changed behavior, affected files, size tolerance, dependencies, and non-goals.
  The ideation proposal bounds a renderer-only cutover, a disclosure-only alternative, 6–9 expected files, and explicit return-to-ideation triggers.
- DONE: Demonstrate realistic current/proposed previews using the required saved cases and unchanged evidence; preserve material uncertainty and show the main result clearly without live model reruns or private evidence commits.
  All three required cases plus a separately labeled audio rerun were exercised at desktop/narrow widths; comparison offsets fell, supporting panels and branch fields stayed identical, and legacy attention remains explicitly unavailable with original reports linked.
- DONE: Define falsifiable offline and interactive acceptance checks, including reader comprehension against baseline, and commit an ideation stage report with evidence and the Captain decision needed before implementation.
  AC-1 through AC-6 specify thresholds and falsifiers; browser/renderer evidence is recorded above, while human comprehension and production checks remain unexercised.

### Summary

Recommend showing the observed comparison first and separating it from overall
check coverage, with material limitations visible and full secondary checks
expandable. The preview demonstrates reduced reading density, not improved human
comprehension; Captain approval is still required, and saved-evidence compatibility
limits are explicitly preserved rather than repaired or concealed.
