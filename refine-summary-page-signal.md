---
title: Refine the summary page to make the main result clear
status: implementation
source: Captain-requested follow-up from case-01-auto-download-audio.md
started: 2026-10-21T10:11:41Z
completed:
verdict:
score:
worktree: .worktrees/spacedock-ensign-refine-summary-page-signal
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
              resolution:
                type: Resolution
                id: resolution:spacedock:dmz5fz1edtpmyc9vx28ez15w:ideation:1
                briefing: briefing:dmz5fz1edtpmyc9vx28ez15w:ideation:attempt-1:revision-1
                by: person:captain
                at: "2026-10-21T10:36:38.984122Z"
                decision: approve
                reason: Captain approved the observation-first hierarchy and verification plan, including six proposed criteria replacing the two seed drafts; no acceptance outcome is inferred as passed.
              application:
                target-stage: implementation
                state: consumed
---

Help readers understand the main Before/After result at a glance without
repeated uncertainty and secondary checks overwhelming the summary.

## Problem

The source case identifies a summary-page clarity problem: the main outcome
requires close reading, while repeated caveats distract from it. Improve the
information hierarchy without suppressing a material risk or implying that
untested behavior is safe.

## Proposed approach

Approved observation-first hierarchy: lead with the observed Before/After result;
consolidate report-wide qualifications while keeping material uncertainty visible.
Keep canonical check conclusions distinct and supporting detail reachable. Use
the existing renderer with frozen evidence; no extraction or lead-selection change.

## Risk evidence

Source: `../spacedock-strategy/projects/behavior-diff/case-01-auto-download-audio.md`,
“What the final demo report showed” and “What we keep and what we stop”.
Read the original in the local strategy checkout when designing. Do not copy
private reports, trial excerpts, or recordings into this state branch. The case
motivates this task; it does not prove additional product value or general safety.

## Expected surface and tolerance

See the approved implementation boundary and revised 8–11-file, 450–700-line
estimate below; 35% tolerance, with further scope changes returning to ideation.

## Acceptance criteria

Captain-approved criteria (the detailed falsifying checks and modes are retained
in “Falsifiable acceptance and verification plan” below):

- **AC-1 — Result recognition:** four approved readers, counterbalanced across
  four saved cases, two reports per version per reader and two readers per
  case/version; proposed achieves at least 7/8 correct main-result answers,
  no worse accuracy, and at least 25% lower median time (60-second cap, including
  wrong answers). Any plan-as-execution or unqualified-all-pass answer fails safety.
- **AC-2 — Unchanged evidence:** identical frozen inputs, serialized data and
  non-summary panels; preserve counts, membership and outcome identity, including
  minority branches, unchanged primary, interrupted/missing trials and no comparison.
- **AC-3 — Visible material uncertainty:** exact supported/rejected/unsettled
  states; accepted failures and incomplete/mixed evidence visible without expansion;
  every frozen check and uncovered goal reachable; missing evidence is never success.
- **AC-4 — One summary home:** each report-wide qualification appears once by
  default, with every original check reason/link available and no distinct limit lost.
- **AC-5 — Usable navigation and density:** desktop 1440 px and narrow 390 px;
  compare/single views, reload, keyboard disclosures and evidence navigation work;
  comparison offset at most 300 px and at least 50% below baseline on desktop;
  both narrow cards complete without horizontal scrolling, table overflow contained.
- **AC-6 — Output/host parity:** HTML, artifact HTML and Markdown preserve
  observation/verdict distinction, failure precedence, counts and destinations;
  captured-tool, self-reported and answer-only evidence is never upgraded.

## Test plan

Exercise unchanged saved cases at desktop and narrow widths; run deterministic
renderer, source/context, live-report-contract, blind-export, and formatting checks.
Keep presentation fidelity separate from the still-unperformed four-reader test.
No live model rerun is authorized.

## Decisions and dependencies

2026-10-21: Captain approved the observation-first hierarchy, renderer-only scope,
and all six ideation acceptance criteria, replacing the seed drafts above. This
approval does not establish acceptance success; human comprehension remains untested.
Related task: `verify-overall-skill-behavior-value` remains independent.

2026-10-21: During implementation, the blind human-evaluation exporter was found
to require the old five-step DOM. Captain explicitly selected “Approve narrow
migration”, relayed by the FO through the worker channel. Scope now includes only
`.agents/skills/run-behavior-diff-human-evaluation/scripts/quiz.py` DOM extraction
and `tests/human-evaluation-quiz-test.py`: preserve blinding and fail-closed
unknown-shape validation, with no questions, schema, evidence changes, or shims.
This decision precedes consumer mutation. No model calls, human responses,
push, PR, merge, or legacy-attention compatibility repair are authorized.

### Feedback Cycles

No correction cycle yet. Design approval and the narrow exporter migration decision
are recorded above; independent validation follows the implementation report.

## Out of scope

A new simulator, repeated generator tuning, hiding material failures, claims of
full-workflow time savings, and treating this case as proven product success.

## Ideation proposal — Captain-approved 2026-10-21

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

[INFERENCE] Original estimate: 6–9 files, approximately 300–500 changed lines,
35% tolerance (675-line ceiling). Captain-approved narrow consumer migration
adds the two paths named above; revised estimate: 8–11 files, 450–700 changed
lines, same 35% tolerance (945-line ceiling). Extraction/schema, lead-selection,
any further production component, or changes beyond that ceiling return to
ideation. No new dependency, model approval, or permanent preview route.

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

### Captain decision recorded

Captain approved observation first, distinct canonical check coverage, visible
accepted failures and material limits, expandable secondary detail, and all six
criteria including the four-reader threshold. Legacy-attention and original-audio
limits remain explicit. Approval is not a human-comprehension or product-value
result. The later narrow blind-export migration authorization is recorded above.

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

## Stage Report: implementation

- DONE: Implement the Captain-approved observation-first summary hierarchy in the assigned worktree, preserving outcome identity, branches, counts, failure precedence, material uncertainty, and evidence destinations across HTML and Markdown; migrate callers and remove obsolete presentation paths.
  Commit `c0350114e29cead0ff3d319dee106cc1b7c53364`; compact observations lead, primary result remains distinct, accepted failure titles stay visible, full checks/context expand, and obsolete summary derivations/styles are removed.
- DONE: Exercise the implemented surface against the approved saved-case preview at desktop and narrow widths, run relevant deterministic checks and formatting after edits, update architecture documentation, and report exact revision and verification evidence without live model calls or private evidence commits.
  Four frozen cases at 1440/390 px, final deterministic suite and formatting passed; `docs/architecture.md` describes the hierarchy and blind-export projection; private receipt directory is named below.
- DONE: Replace the seed draft acceptance criteria with the approved six ideation criteria in the task record, map each to actual evidence or an explicit unmet requirement (including the four-reader human comprehension check), and commit a complete implementation stage report for independent validation.
  The six criteria above replace the seed drafts; evidence and the unmet human requirement are mapped below without changing thresholds.

- SKIPPED: AC-1 — Result recognition.
  UNMET: no Captain-approved four-reader counterbalanced study or human responses exist; 7/8 accuracy, baseline non-inferiority, 25% timing improvement, and safety thresholds remain untested.
- DONE: AC-2 — Unchanged evidence.
  `fidelity.json`: all four serialized inputs remain equal and all five non-summary panels are structurally identical; schema/presentation contracts retain minority counts, missing/interrupted evidence, and primary identity, failing on changed card counts or state.
- DONE: AC-3 — Visible material uncertainty.
  Schema/target/presentation contracts exercise preservation failures and rejected/unsettled states; closed-disclosure assertions require failure titles, cautions, notices and attention to remain outside details, failing if a material result is hidden.
- DONE: AC-4 — One summary home.
  Qualification count and full-check-row contracts pass; the separate repeated implication/lead-distribution paths are removed, while exact check reasons, open goals and evidence links remain in the disclosure.
- DONE: AC-5 — Usable navigation and density.
  Desktop comparison offsets baseline→candidate: review 1441→255, notes 1420→206, routing 1420→206, audio 3996→206 px; every case meets ≤300 px and ≥50% reduction; both widths passed view/reload, keyboard, target-reveal and no-document-overflow checks.
- DONE: AC-6 — Output/host parity.
  HTML/document/Markdown contracts retain derived verdict and evidence level; `mutation-proof.json` rejects 12 synthetic pass/execution upgrades across planned, self-reported, answer-only and captured-tool cases; raw data is unchanged.

- DONE: Captain-authorized blind-export consumer migration.
  `quiz.py` and its tests now allowlist the four-section DOM while excluding aim/assessment/setup/next-action answers; 21 quiz and 12 hosted tests pass, failing on unknown shapes, leaked keys or altered saved receipts. No legacy-layout shim was added.
- DONE: Final deterministic checks and static formatting.
  Passed `report-schema-test.py`, `report-source-test.py`, `report-ci-context-test.py`, `live-report-contract.sh`, quiz/hosted tests, Python compilation, Ruff format check (147 files), Docker shfmt check, and `git diff --check`; report contracts reject malformed provenance and distinguish unavailable from assessed-empty attention.
- DONE: Preserve scope and private evidence boundaries.
  Ten code files, +380/−395 = 775 changed lines, within the revised 945-line ceiling; no extraction/schema/lead-selection change, new dependency, paid call, private artifact commit, push, PR or merge.
- SKIPPED: Historical compatibility repair and original-audio reconstruction.
  The three Recce schema-11 attention assessments still render unavailable; current-schema attention is covered synthetically. Supplemental audio is the later 15-check rerun, not the original 13-check reconstruction; neither proves external workflow success.

### Summary

Implemented the approved hierarchy and the separately Captain-authorized blind-export migration on `spacedock-ensign/refine-summary-page-signal` at `c0350114e29cead0ff3d319dee106cc1b7c53364`. Candidate evidence is ready for independent validation, but AC-1 remains explicitly unmet and no product-value or comprehension improvement is claimed.

Private receipts, unchanged-input comparisons, mutation results and screenshots: `/var/folders/h_/tb6bynfj41g1dcvpb2472vrh0000gn/T/summary-signal-implementation-m51wk0hw/` (`receipt.json`, `fidelity.json`, `browser-layout.json`, `browser-wrapper.json`, `browser-final-interaction.json`, `mutation-proof.json`, `desktop-audio.png`, `narrow-notes.png`). The owned port-8795 verification service and browser tab were stopped; the earlier ideation service was not touched.
