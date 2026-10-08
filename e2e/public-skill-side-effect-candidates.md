# Public skill side-effect candidates

Recorded: 2026-10-07. Baoyu routing rehearsal completed; other cases remain unrun.

## Purpose and exclusions

Find an earlier skill edit that introduced an unintended instruction interaction,
then test whether Behavior Diff's **What needs your attention** section identifies
it in a parent-to-first-edit comparison. Later corrections establish historical
context; they are not trial inputs or evidence that our replay will reproduce it.

These three repositories are new relative to both prior surveys:

- [Public source catalog](../plans/2026-09-29-public-skill-history-sources.md)
- [Candidate screening and rejections](../plans/2026-09-30-skill-survey.md)

The search excluded all previously surveyed repositories, including parked and
rejected cases, and the Recce-team cases. Do not reintroduce those as new leads.

| Candidate | Disposition | Main limitation |
|---|---|---|
| JimLiu/baoyu-skills: browser routing | Investigate first | Multi-file instructions; historical failure not reproduced |
| netresearch/git-workflow-skill: internal-skill handoff | Backup | Mixed instruction/script change; local fallback may avoid the defect |
| mejasonmejason/execution-coordinator: trigger regression | Hold | Automatic discovery differs from explicit invocation; license unverified |

## 1. Baoyu: a new browser default overrides other routing

Repository: [JimLiu/baoyu-skills](https://github.com/JimLiu/baoyu-skills).
Skill: `skills/baoyu-post-to-x/SKILL.md`.

### Historical pins

- Before: `aa1a967a9f72af37221deb10918cf0b66d942fd9`, verified first parent.
- First edit: [`045fe5e57ec2eabb44ebc7521d71371b86bc4025`](https://github.com/JimLiu/baoyu-skills/commit/045fe5e57ec2eabb44ebc7521d71371b86bc4025).
- Later correction: [`5f753dd5848947522df17d1b54ab07ef4aedce45`](https://github.com/JimLiu/baoyu-skills/commit/5f753dd5848947522df17d1b54ab07ef4aedce45).
  Its parent is `076192d58e4f5cb5f81029421f1cbbacbbc48fda`, not the first edit.

### Intended change and possible consequence

The first edit prefers Chrome Computer Use for X publishing. Its required mode
selection probes Computer Use and selects it when available. The correction
instead honors explicit Chrome-plugin requests before probing Computer Use.
It also restores CDP for Markdown articles with local images, explaining that
placeholder selection and image-block verification are more reliable there.

The instruction conflict and corrective intent are visible in the patches.
Agent override of a user's requested route, or actual image loss, remains an
inference: no contemporaneous failed-run transcript was established. The parent
is CDP-oriented; do not claim it already supported Chrome-plugin requests correctly.

### Proposed bounded experiment

Compare parent with first edit using the same available-tool catalog and task.
Observe actual route selection, stopping before publishing or remote mutation.
An article with local images and no mode preference gives a clearer historical
CDP-to-Computer-Use transition than a plugin request whose parent behavior is
unknown. Neither route selection nor a planned invocation proves image preservation.
A synthetic tool boundary must be labeled as such, not passed off as real browser
execution. Do not preload the expected route or later correction into the agent.

The introducing edit changes `SKILL.md`, `references/articles.md`, and
`references/regular-posts.md`. Preserve all three for a faithful replay; a
single-file projection is a different experiment. The correction also changes
TypeScript, so it is not a pure instruction-only control.

### License and disposition

Current repository licensing is MIT. The root license was added after these
historical edits; the [owner's clarification](https://github.com/JimLiu/baoyu-skills/issues/186#issuecomment-4756309108)
states MIT intent and preserves third-party terms. Do not claim the historical
snapshots already contained that license. Verify notices before copying a bundle.

**Disposition:** strongest routing lead, not a validated side-effect demo.

### 2026-10-07 routing rehearsal

Kent approved one fresh drafting session, six trials (three per side), and one
report extraction using OMP `openai-codex/gpt-6-astra:high`. All completed without
reruns. The parent-to-first-edit comparison included all three changed instruction
files, with the complete local skill bundle available. No later correction or
evaluator finding was supplied to drafting, trials, or extraction.

The fresh drafter used the canonical Behavior Diff skill to prepare a fictional
Markdown article with two local image references. Two fixed synthetic PNGs were
supplied. The environment explicitly simulated Codex on macOS with both browser
routes available, authenticated article access, no profile overrides, and no
injected failures. Actual execution used OMP with `read` and `write` only.
Agents wrote `output/routing.md` describing their selected route, next actions,
checks, and stopping conditions. No browser tools or upstream scripts executed.

| Evidence | Before | After |
|---|---|---|
| Selected preparation route | CDP article script in preview mode, three of three | Chrome Computer Use, three of three |
| Proposed image replacement sequence | Reverse document order, three of three | Placeholder order, three of three |
| Review and publication boundary | Proposed checks, no publication authorized | Proposed checks, no publication authorized |

The generated Summary describes the route change. **What needs your attention**
says: “No additional change needing your decision was found in these trials.”
No image loss, failed selection, failed draft, or overridden explicit browser
preference was demonstrated. The selected historical side effect remains
`inconclusive`; this run establishes neither a catch nor a missed detection.

**Extraction evidence limit:** agents put the detailed plans in `output/routing.md`
and summarized the selected route in their final answers. The existing trace
loader supplies command/path entries and final answers to extraction, not the
contents of those written files. The generated report explicitly notes that the
routing reports themselves are not shown. The primary assistant inspected all six
files afterward, but that inspection is not evidence the extractor saw them.
The detailed insertion/check plans therefore have less report coverage than the
route selections. Do not interpret empty attention as assessment of all artifact
contents. No extra extraction call or report rewrite was performed.

Source/scenario hashes and unchanged inputs were verified. All six routing files
exist; audited draft/trial calls stayed within their fixtures, with trial writes
under `output/`, no tool errors, and empty stderr. Restrictions are tool policy and
instructions, not an OS sandbox. The supervisor shell emitted optional missing
`fig` startup notices, separate from the clean trial stderr.

The generated report's Summary and explanation were inspected in-browser, and an
attention-section screenshot was captured. Raw runs, routing files, and the report
remain outside this repository. Temporary credential database copies were removed.
The comparison used the existing trial, extraction, and rendering components with
directory-scoped `rule.md` evidence for the multi-file patch; no product code changed.

## 2. Netresearch: a boundary fix creates an inaccessible handoff

Repository: [netresearch/git-workflow-skill](https://github.com/netresearch/git-workflow-skill).
Skill: `skills/git-workflow/SKILL.md`.

### Historical pins

- Before: `c964bfd8df79fddfa66be9b5c782e7bcbb99a2a3`, verified first parent.
- First edit: [`85b918cdfb9825d364557789c6d2fc85a311055b`](https://github.com/netresearch/git-workflow-skill/commit/85b918cdfb9825d364557789c6d2fc85a311055b), in [PR #260](https://github.com/netresearch/git-workflow-skill/pull/260).
- Later correction: [PR #334](https://github.com/netresearch/git-workflow-skill/pull/334), starting at
  [`44bb570d5bdd6347c1befadb5b82b644dc1ee92b`](https://github.com/netresearch/git-workflow-skill/commit/44bb570d5bdd6347c1befadb5b82b644dc1ee92b).
- Follow-on correction: [`9a12d5e59ffd2a60f4eb319fce5a7c0f5595c0f2`](https://github.com/netresearch/git-workflow-skill/commit/9a12d5e59ffd2a60f4eb319fce5a7c0f5595c0f2).
  This fixes a stale reference heading and a missed command instruction; do not
  treat `44bb570` alone as the fully corrected version.

### Intended change and possible consequence

The first edit prevents GitLab requests from entering GitHub-only tooling, but
routes them to `netresearch-gitlab`. The correction explicitly identifies that
skill as internal and unavailable to public consumers, replacing the handoff
with a bundled public reference.

This is an affirmative instruction introducing an inaccessible dependency.
However, no public-user trace established an agent stopping on that dependency.
The intermediate skill already mentions a local reference, so an agent may avoid
the bad handoff. The 560-second watcher failure in [issue #250](https://github.com/netresearch/git-workflow-skill/issues/250)
predates the boundary edit and is not evidence of its side effect.

### Proposed bounded experiment

Supply a local GitLab merge-request assessment fixture, frozen discussion data,
and the bundled reference. Ask for a local assessment, not a merge. Observe whether
the agent demands the unavailable skill or proceeds using the public reference.
No forge login, remote writes, or actual merge is needed. This tests a handoff
boundary, not the complete forge workflow, and may remain inconclusive.

The introducing edit changes both `SKILL.md` and `scripts/pr-status.sh`; the
correction also changes command instructions. Preserve scope explicitly rather
than calling a one-file projection a whole-commit replay.

### License and disposition

The [pinned README](https://github.com/netresearch/git-workflow-skill/blob/9a12d5e59ffd2a60f4eb319fce5a7c0f5595c0f2/README.md)
distinguishes MIT code from **CC-BY-SA-4.0 skill content and documentation**.
Preserve attribution, license links, modification notices, and applicable
ShareAlike terms. Do not label the instruction bundle MIT.

**Disposition:** backup lead; causal instruction defect established, behavioral
reproduction and report detection unverified.

## 3. Execution coordinator: a description rewrite loses a trigger

Repository: [mejasonmejason/execution-coordinator](https://github.com/mejasonmejason/execution-coordinator).
Skill: root `SKILL.md`.

### Historical evidence

[PR #14](https://github.com/mejasonmejason/execution-coordinator/pull/14) reports
benchmark results comparing v10 (`941d305`) with merged v11
(`7ef9ea03ae6796a50463a3c99775efa62f855839`). A production-incident query previously
triggered reliably but became inconsistent after the description rewrite.
The correction adds an explicit trigger for identifying the merged PR that broke
production. Upstream reports recovery after the correction.

Correction merge: `4c2397225110dc35a301f3dc204eb0cad88a8252`.
These are upstream-reported measurements, not our reproduced results. The v10 and
v11 benchmark endpoints are not a verified introducing-commit/first-parent pair;
that exact pair still needs isolation before a first-edit experiment.

### Why this is on hold

- Automatic discovery is the observable. Explicitly telling the agent to invoke
  the skill bypasses the failure, so our ordinary replay would test the wrong thing.
- A discovery experiment needs a fixed skill catalog and host loading behavior,
  with an ordinary user request that does not name the target skill.
- The repository license endpoint returned 404 and no root license appeared in
  the inspected listing. Open-source permission was not verified; do not reuse
  its bundle until licensing is resolved.

**Disposition:** useful upstream regression evidence, not approved for a current
Behavior Diff demo.

## Execution and evidence gates

The initial source research ran no model-backed replays. The separately approved
Baoyu rehearsal is recorded above. No upstream scripts or publishing actions ran.
Before any additional live experiment:

1. Resolve licensing, exact source scope, dependencies, and available tool routes.
2. Obtain fresh approval for models, counts, source processing, and cost.
3. Freeze neutral scenarios and the parent-to-first-edit pair. Keep corrections
   and this evaluator record out of drafting, trials, and extraction.
4. Preserve all attempts and distinguish real tool execution from simulation.
5. Evaluate reproduction separately from report detection. A defect absent from
   the trials cannot be called a missed detection or a successful catch.
6. Inspect the generated **What needs your attention** section without rewriting
   it. Record inconclusive outcomes; never retry until the desired failure appears.

Do not promote any of these leads as a successful side-effect detection demo
until both the consequence and the report's explanation are supported by evidence.
