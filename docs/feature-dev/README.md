---
commissioned-by: spacedock@0.27.3
entity-type: implementation_task
entity-label: task
entity-label-plural: tasks
id-style: sd-b32
state: .spacedock-state
stages:
  defaults:
    worktree: false
    concurrency: 2
  states:
    - name: backlog
      initial: true
      gate: true
    - name: ideation
      gate: true
    - name: implementation
      worktree: true
      context-sections:
        - Review-finding disposition
        - Repository execution policy
    - name: validation
      worktree: true
      fresh: true
      feedback-to: implementation
      gate: true
      context-sections:
        - Review-finding disposition
        - Repository execution policy
    - name: done
      terminal: true
---

# Behavior Diff feature development

Turn an approved feature request into a verified, independently reviewed, merged
change. The Captain controls product direction; the first officer (FO) carries
routine execution between decisions. Each implementation task normally delivers
one independently mergeable PR. Larger features share an accepted plan and use
explicitly ordered dependent tasks. Shuttle-mode workers perform stage work.

## Authority

Read the repository's [AGENTS.md](../../AGENTS.md),
[CODING_GUIDELINES.md](../../CODING_GUIDELINES.md),
[REVIEWER_GUIDELINES.md](../../REVIEWER_GUIDELINES.md), and
[ISSUE_GUIDELINES.md](../../ISSUE_GUIDELINES.md). These remain authoritative;
this README defines process, not a second copy of repository policy.

## File Naming

Tasks live in the resolved state checkout, not beside this README. Default to
`short-task-title.md`; use `short-task-title/index.md` only when sibling artifacts
are necessary. Slugs are lowercase and hyphenated. Folder tasks archive as a unit.
Never store private runs, reports, transcripts, credentials, or customer data on
the state branch. A separate branch is not private storage.

## Schema

### Field Reference

| Field | Type | Description |
| --- | --- | --- |
| `id` | string | Stable 24-character SD-B32 identifier, minted by `spacedock new` |
| `title` | string | Human-readable task title |
| `status` | enum | backlog, ideation, implementation, validation, done |
| `source` | string | Request or issue that authorized the work |
| `started` | ISO 8601 | When active work began |
| `completed` | ISO 8601 | When merged delivery reached terminal status |
| `verdict` | enum | PASSED or REJECTED; validation recommendation, PASSED at successful completion |
| `score` | number | Optional priority from 0.0 to 1.0 |
| `worktree` | string | Assigned code worktree; retained across stages until terminal cleanup |
| `issue` | string | Optional GitHub issue reference, used by the PR mod's Closes line |
| `linear` | string | Optional Linear issue URL; do not put it in the GitHub issue field |
| `pr` | string | PR reference managed by the PR merge mod |
| `mod-block` | string | Mod-owned pending lifecycle action |

Record dependencies, accepted decisions, evidence references, and the accepted
plan in the task body. Never invent frontmatter state fields for runtime handles.

### ID Style

This workflow uses `id-style: sd-b32`: SHA-256-derived IDs encoded with Spacedock's
human-safe alphabet `0123456789abcdefghjkmnpqrstvwxyz`. Stored IDs have 24 lowercase
characters. Display prefixes start at two characters and can lengthen when active
or archived IDs collide; the stored ID does not change.

Use `spacedock new` to mint and write a task atomically. `status --next-id
--id-seed` is a preview, not a reservation. Validate state before trusting manually
edited records; resolve a displayed prefix through `status --resolve` before use.

Other supported identity designs are `id-style: sequential` (zero-padded numeric
IDs) and `id-style: slug` (filename identity, optional ID). Changing style requires
a deliberate migration of active and archived tasks, not an automatic rewrite.

## Stages

### `backlog`

The FO records a real request; the Captain chooses whether design should start.
No invented feature tasks are created to make a pilot look active.

- **Inputs:** Request, source issue, known dependencies, and repository scope.
- **Outputs:** Desired user benefit, included and excluded scope, priority, dependencies, and the evidence needed to begin design.
- **Good:** A concrete user problem with an identifiable owner and deliverable.
- **Bad:** Turning an optional review suggestion, release ritual, or workflow maintenance into an unauthorized feature.
- **Gate content:** Outcome, scope, dependencies, and recommendation to start or hold. An explicit request to implement can supply selection approval; record it through the gate lifecycle rather than asking the same question again. It does not approve an unknown design or merge.

### `ideation`

A worker develops the selected task's approach for the Captain's decision.

- **Inputs:** Selected request, applicable contracts, current implementation, existing evidence, and related plans.
- **Outputs:** Recommended approach and simplest relevant alternative; preserved and changed behaviors; non-goals; affected files and estimated change size with tolerance; dependencies and PR breakdown; acceptance criteria and verification plan. Exercise an unverified risky mechanism or explain which proven mechanisms make a spike unnecessary.
- **Good:** Each criterion names a finished outcome, an external falsifiable check, and whether verification is offline or interactive. At least one measures user value against a baseline.
- **Bad:** Starting implementation from an unresolved product choice, treating prose presence as runtime proof, or creating permanent infrastructure merely to automate a human judgment.
- **Gate content:** Recommendation, evidence, tradeoff, and decision needed. For report hierarchy/navigation/comparison changes, use the existing preview skill and required saved cases; hold evidence constant, show a realistic preview, and record the accepted design before implementation. Rejected designs remain in ideation for revision.

Keep preliminary design in the task body. When an accepted plan or preview must
be written into the code tree, perform that write in the assigned implementation
worktree before further implementation; request targeted preview approval if it
was not already obtained. Do not write code-branch artifacts from the state checkout.

### `implementation`

A worker builds the approved scope in the assigned feature worktree.

- **Inputs:** Approved approach, acceptance criteria, preview decisions, repository rules, and authorized correction assignments.
- **Outputs:** Complete minimal candidate; migrated callers and removed obsolete paths; relevant contracts/fixtures/docs updated; actual check and smoke-run evidence with revision identity and limits; disposition proposals for any findings before corrective mutation.
- **Good:** Observable behavior matches the approved outcome and preview; uncertainty is explicit and changes stay within scope.
- **Bad:** Compiling scaffolds presented as complete, unrelated cleanup, fabricated test results, silent scope expansion, or private evidence committed to any branch.

Use Review-finding disposition before corrective edits. In-scope FO-authorized
fixes do not require another Captain prompt. Changed product meaning, acceptance
criteria, compatibility promises, or scope require a design decision first.

### `validation`

An independent worker evaluates the complete candidate without editing it.

- **Inputs:** Exact candidate revision, full changed scope including relevant untracked files, accepted plan and preview, acceptance criteria, prior findings, and implementation verification evidence.
- **Outputs:** Independent review in the repository's required format; evidence mapping for every criterion; comparison of the actual surface to the approved preview; explicit uncertainty and finding dispositions. Route corrections to implementation and obtain independent re-review of the corrected complete candidate.
- **Good:** Demonstrated violations cite authority, a reachable trigger, observable harm, and the least-cost remedy. Existing successful evidence is reused when it covers the unchanged candidate; missing or invalidated checks are run by the implementation owner.
- **Bad:** Reviewer edits, reviewer-run builds/tests/formatters, optional suggestions treated as requirements, stale-revision approval, or a renderer check presented as proof of model behavior.
- **Gate content:** User outcome, actual result/preview, checks actually run, criterion evidence, reviewer verdicts, unresolved risks, and the delivery recommendation. Captain approval or an explicit recorded delegation is required. Rejection routes to implementation; a changed product decision returns to ideation through the supported lifecycle, never an ad-hoc status flip.

Use the local `review-by-subagent` skill for the complete review/fix/review loop.
Reviewers stay read-only; implementation owns verification and corrections.
Keep fixing material findings within authorized scope until required reviewers
approve the same current revision or a concrete blocker requires a decision.
Append each review round and later relevant findings to an existing PR. Independent
approval precedes PR creation or update. New evidence undermining approval reopens
validation; previous merge permission is not acceptance of an undisclosed risk.

### `done`

The PR merge mod confirms landed delivery and archives the completed task.

- **Inputs:** Approved current revision, required verification, explicit delivery authority, and observed merged PR state.
- **Outputs:** Confirmed merge reference, completion timestamp, PASSED verdict, and archived task with safe evidence references and finding dispositions.
- **Good:** Actual merged delivery, not an approval or push mistaken for completion.
- **Bad:** Manual terminal flags, an automatic release, or silent local-merge fallback.

## Review-finding disposition

Every finding enters this checkpoint when it arrives during implementation, validation, a detached audit, consequential FO quick work, or a correction routed from a rejected gate.

1. The reviewer owns observation, not task ownership or authorization.
2. The worker preserves the finding, investigates without candidate mutation, records the four evidence fields, and proposes materiality, task ownership, and disposition separately. Its `actor:ensign` round Resolution is advisory.
3. The FO sends a distinct `fix`, `decline`, `hold`, or `route for decision` authorization through the runtime's addressable-worker boundary.
4. The validator recommends `PASSED` or `REJECTED`; a new finding re-enters step 1.
5. Only the captain changes approved scope, accepted value, thresholds, tolerance, or acceptance criteria.
6. After revise is selected, rejection routing transports the evidence, workflow classifications, authorized dispositions, and concrete assignment unchanged; it never re-triages.

Before FO authorization, candidate bytes and Git HEAD stay unchanged, no candidate commit is made, and no reviewer rerun starts. Read-only file/history inspection, non-mutating reproductions, existing tests, and adversarial work in a throwaway checkout are allowed. After authorization, perform only that disposition; `hold` and `route for decision` forbid mutation and rerun. Changed evidence re-enters the checkpoint, and an unobservable runtime authorization means hold and re-consult.

The four evidence fields are released user and normal workflow; observable harm; affected value AC or non-negotiable boundary; and trigger evidence. Field 3 uses `value-ac[AC-N]`, `captain-ruling[YYYY-MM-DD]`, or `contract[repo/relative/path#anchor]` plus a nonblank claim; `none:` plus a rationale cannot establish Material.

- **Material:** all four fields establish supported-workflow harm to a value AC or protected boundary.
- **Deferred risk:** the trigger is hypothetical, unsupported, unobserved, or outside current promises; record its promote-to-material condition.
- **Polish:** no current user-visible loss or protected boundary is at risk.
- **Needs decision:** the task cannot own the required scope, product, or compatibility decision.

Materiality and task ownership are independent. Owned Material is eligible for an FO-authorized fix; out-of-scope Material holds unchanged as Needs decision. Deferred risk or Polish may be declined only after FO authorization.

After reviewer and worker entries and FO consultation, the First Officer appends the workflow-defined Cycle line directly from the authorized package. Then the First Officer invokes `${SPACEDOCK_BIN:-spacedock} gate record --round` with the canonical Briefing/log before reviewer re-run or next-gate preparation. The neutral recorder retains those bytes and advances `review-round`; it applies no gate or status change, and it does not parse classifications or project workflow prose. A workflow correction round may use `- Cycle {N}: {verdict} — {reviewer/loop}; surface {files}/{LOC} vs estimate {declared} ({P}%); AC {unchanged | narrowed: <note>}`. Compare `git diff --numstat "$(git merge-base main HEAD)"..HEAD` with the ideation estimate; beyond declared tolerance or on narrowed AC, require a captain-visible design reset. Cycle 3 escalates.

## Workflow-specific rules

The FO/ensign operating contract already governs generic stage semantics and proof discipline: prefer the cheapest check that can fail — a shipped guard's run, an existing mechanical check, a one-off falsifiable exercise recorded in the report, then the captain's judgment — with new standing enforcement as the last resort rather than the default; prove by exercising rather than re-reading; and reject any AC whose only proof is a review of its own prose. Tasks in a commissioned development workflow inherit these rules from the contract their FO loads at boot; the rules below add only the dev-shape specifics.

- **Repo-mutation worktree layer.** `implementation` and `validation` run in a worktree against the codebase, and `validation` is `fresh` so an independent agent checks the AC. PR state lives on the `pr` field, managed by the `pr-merge` mod — there is no `pr_open` or `awaiting_merge` stage.
- **No prose-grep over instruction files.** A string, substring, or regex match over an instruction file the model reads (the FO/ensign contract, this README, a skill) never proves a behavioral claim. The matched text was written by the same implementer the check polices, so it asserts only that the file contains what we put in it. A valid paraphrase fails it and an inverted clause passes it. To settle a case, ask whether the expected value comes from outside the file under test; if it does not, the check is a tautology and is banned. A check that binds two independent values that can diverge, such as the plugin manifest's version sharing a major.minor with the binary's version, is legitimate and is not prose-grep. Prose-greps are one-off validation evidence, never committed tests. A grep whose output is pasted into the validation report is legitimate external evidence for that run; the same grep committed as a test is banned — it re-asserts that the file contains what we wrote and cannot fail. What such a grep may be evidence FOR is bounded by honesty, not by category: presence or absence is an existence fact, and a grep establishes it soundly when that fact is itself the claim. When it is not — when the claim is about what a program or an agent actually does, and the words being present says nothing about that — the grep is misleading, and the answer is to express the claim in a form that can be exercised, not to let a grep that technically passes stand in for proof it cannot give.
- **Evidence must be able to fail.** Each AC's cited evidence names the concrete change that would flip it — the falsifying edit. An author who cannot name what would make the evidence fail has not shown it can fail, and the criterion does not count.
- **Opt-in proof disciplines (copy into the `validation` stage when commissioning).** These are recommended dev-shape practices, not universal — a non-development workflow's acceptance proof may legitimately be a published artifact, a metric, or a human review. Adopt the ones the mission needs by folding them into the `validation` stage's Outputs and Bad lists:
  - **Test-first authoring** — for a code or fixture deliverable, write the failing test first, watch it fail for the right reason, then write the minimum code to pass. The test is what the gate judges.
  - **External-proof acceptance criteria** — each AC's evidence must come from a check outside the task body (a test, a command's output or exit code, a file the change produces, on-disk state). Reject self-referential ACs whose only proof is review of the task's own prose; if nothing ships, the decision belongs in the roadmap, not a terminal dev task.
  - **Detached adversarial audit** — for high-stakes surfaces (a front-door launcher, status/guard mutation paths, shipped contract/scaffolding, CI/release machinery), run a read-only audit on a throwaway checkout that tries to refute the validation with an edit the deliverable's own tests should catch. `Material:` findings route back through the validation→implementation feedback flow; "refuted nothing material" is a valid recorded outcome. The audit also fires on AC provenance: when an AC's expected value is derived from the same package's production functions or constants, run the adversarial-edit check on it — that provenance is the tautology tell. Scope it to that provenance form; the broader equality/byte-identity form over-fires on ordinary unit tests.
  - **Live scenario for runtime claims** — when an AC's truth is what an agent or model *does* at runtime, prove it with a scripted live scenario graded on durable before→after state plus observed output, with a negative case that reds the grade. Mark the AC `Verified by: live <ci-run:<id> | session:<path>>`; an offline proxy or a contract-text check proves the watcher or the words, never the runtime behavior.

  The generic rationale for each — why a prose-only proof never satisfies a behavioral claim — lives in the FO/ensign contract; the disciplines above are the dev-shape applications a captain opts into.

- **Declaring a posture (optional).** A workflow that wants a single findable answer to "how much engineering does this project want?" may declare it here: project maturity (prototype / product), default test depth, infra-addition policy (may a worker add a CI lane or lint unasked?), and review-finding priority. This is a place to write an existing posture down, not a new required concept — omit it unless the workflow benefits from a stated posture.


## Repository execution policy

- Follow the linked repository guides and use existing maintainer skills instead of duplicating their procedures.
- Keep Claude Code and Codex product behavior equivalent. omp orchestration support does not introduce a new Behavior Diff trial host.
- Update architecture documentation when execution flow, responsibilities, model roles, or report artifacts change.
- Choose verification from the changed behavior and its risks. Exercise the actual changed surface; distinguish deterministic contracts, authored previews, raw evidence audits, and live model observations.
- Use saved real cases when required and available; missing private evidence is a gap, not permission to invent an equivalent. Do not reflexively repeat live journeys after every feedback message.
- Live journeys require applicable consent and remain outside deterministic CI. FO judgment-call cost approval is not blanket approval for unrelated live trials or disclosure.
- Keep normal work moving after approval. Escalate scope, product, compatibility, acceptance changes, and concrete blockers rather than routine mechanics.
- Present recommendation, result/evidence, tradeoff, and decision needed. Progress names actual work or blockers, not merely stage counts.
- Record decisions, dependencies, reviewed revisions, and safe evidence references durably. History is context, not new authority. Do not assume session handles survive a restart.
- The PR mod manages delivery, not permission: present its actual draft and honor its explicit push/PR approval guard. Gate approval alone is not push/PR permission. Merge requires explicit authority; failure never authorizes local merge. Release remains a separate request using `release-behavior-diff`.
- Two independent tasks may run concurrently; dependent PRs remain ordered. No new permanent test mechanism, dependency, or CI gate without scope authority.

## Judge-assisted decisions

Use available `judge()` or `judge_batch()` for bounded evidence support,
materiality, and authorized routing assessments. Give the requirement and relevant
evidence, include an uncertain outcome, and batch independent questions. Use
commands for facts such as exit status, revision identity, and merge state.

Judge supplies assessment; the FO owns authorized action. A result cannot replace
independent review, change scope, or approve a Captain-reserved decision. Missing
or conflicting evidence requires investigation or escalation. Use the configured
provider; TypeSafe/Jev availability is not assumed. API-cost approval covers these
FO judgments, not unrelated journeys or private-data disclosure. Keep raw session
payloads out of tracked state.

## omp runtime prerequisite

Before dispatch in omp, read [the omp execution requirements](runtime/omp.md).
This is a compatibility guard, not an adapter implementation. The plugin-shipped
FO remains authoritative for its lifecycle. If its loaded adapter cannot execute
using available tools, stop before real dispatch and report the precise gap.
Adapter-selection or transport implementation changes belong in Spacedock, not
in this repository's product or a hidden workflow shim.

## Workflow State

The README and mod live on the code branch. Mutable tasks live in the linked,
gitignored `.spacedock-state` checkout on orphan branch
`spacedock-state/feature-dev` in the same repository. Routine transitions do not
change the code branch. State commits and pushes obey the same privacy rules.
The initial state is deliberately empty until the Captain selects real work.

```bash
spacedock status --workflow-dir docs/feature-dev --validate
spacedock status --workflow-dir docs/feature-dev
spacedock status --workflow-dir docs/feature-dev --next
```

On a fresh clone, restore the state checkout with `spacedock state init` using
this workflow directory. In a supported Claude runtime, start with
`spacedock claude` and select this workflow. In omp, invoke the installed
first-officer skill for `docs/feature-dev` and satisfy the runtime prerequisite;
there is no verified `spacedock omp` launcher in version 0.27.3.

## Task Template

Use this structure as authoring guidance, replacing instructional prose with the
real request. Mint the ID with `spacedock new --workflow-dir docs/feature-dev`;
do not hand-write a previewed ID. Omit unsupported claims rather than inventing
requirements. Record the source of Captain decisions without private excerpts.

```markdown
---
title:
status: backlog
source:
started:
completed:
verdict:
score:
worktree:
issue:
linear:
pr:
mod-block:
---

Describe the requested user benefit.

## Problem

Record the supported workflow and its current limitation.

## Proposed approach

Record the recommended approach and simplest relevant alternative.

## Risk evidence

Cite the observed exploratory result or explain why proven mechanisms suffice.

## Expected surface and tolerance

Record estimated files, net lines, tolerance, and changed semantics at ideation.

## Acceptance criteria

Write each criterion as a finished outcome with a `Verified by:` clause naming
external evidence and what concrete change would make that check fail. Mark
verification offline or interactive; include a value-measuring baseline.

## Test plan

Name applicable checks, actual-surface exercise, and any live consent needed.

## Decisions and dependencies

Link the accepted plan, prerequisite tasks, and scoped Captain approvals.

### Feedback Cycles

The FO records authorized correction rounds here through the lifecycle contract.

## Out of scope

State exclusions that prevent reviewer suggestions from expanding the task.
```

## Commit Discipline

- Every commit, including state commits, requires a DCO sign-off.
- Commit state changes at dispatch and merge boundaries; commit substantive task updates.
- Implementation commits belong on the assigned feature branch. Do not absorb unrelated user changes.
- Push, PR creation/update, merge, and release have distinct approval requirements.
- Never commit private runs, reports, transcripts, or credentials, including to orphan state branches.
