---
title: Reduce full Behavior Diff skill execution time on Claude Code and Codex
status: validation
source: Captain request to improve the complete native-host skill rather than OMP advisor configuration
started: 2026-10-27T13:28:15Z
completed:
verdict:
score: 0.95
worktree: .worktrees/spacedock-ensign-speed-up-canonical-skill
issue:
linear: https://linear.app/recce/issue/DRC-5000/reduce-end-to-end-behavior-diff-skill-execution-time-on-claude-code
pr:
mod-block:
id: n2m85xea3h2q75xk6gzjebwm
gates:
    version: 1
    records:
        - id: gate:n2m85xea3h2q75xk6gzjebwm:backlog
          stage: backlog
          attempts:
            - id: gate-attempt:n2m85xea3h2q75xk6gzjebwm-backlog-1
              briefing:
                id: briefing:n2m85xea3h2q75xk6gzjebwm:backlog:attempt-1:revision-1
                digest: sha256:75e0a81279bf5edea45629dd0d61689ef0564c3cd24c8f31994d034d7fcf7be2
                room-ref: ./review/backlog/briefing-1
              resolution:
                type: Resolution
                id: resolution:spacedock:n2m85xea3h2q75xk6gzjebwm:backlog:1
                briefing: briefing:n2m85xea3h2q75xk6gzjebwm:backlog:attempt-1:revision-1
                by: person:captain
                at: "2026-10-27T13:27:52.697425Z"
                decision: approve
                reason: The Captain explicitly requests refactoring the complete Behavior Diff skill to reduce execution time under Claude Code or Codex; this accepts starting design, not an unknown design or merge.
              application:
                target-stage: ideation
                state: consumed
        - id: gate:n2m85xea3h2q75xk6gzjebwm:ideation
          stage: ideation
          attempts:
            - id: gate-attempt:n2m85xea3h2q75xk6gzjebwm-ideation-1
              briefing:
                id: briefing:n2m85xea3h2q75xk6gzjebwm:ideation:attempt-1:revision-1
                digest: sha256:fe91f070491e9fc4b2e75f44d27e20ca43dbe9f244c284057511e7869141c5d4
                room-ref: ./review/ideation/briefing-1
              resolution:
                type: Resolution
                id: resolution:spacedock:n2m85xea3h2q75xk6gzjebwm:ideation:1
                briefing: briefing:n2m85xea3h2q75xk6gzjebwm:ideation:attempt-1:revision-1
                by: person:captain
                at: "2026-10-27T14:00:52.680365Z"
                decision: approve
                reason: 'Captain approved the bounded shared refactor and accepted the complete assembled-instruction projection for the review benchmark, explicitly not original filesystem reference-loading fidelity; AC-1/AC-2 review evidence is scoped to that projection. Captain separately authorized one direct startup trial, then two replacement outer executions only after it succeeds, within the existing US$20 working budget: maximum eight outer sessions,49 trial launches including12 failed startups andone diagnostic, andsix extractions total; no automatic retries or push/PR/merge authority.'
              application:
                target-stage: implementation
                state: consumed
---

Reduce elapsed time from a user's comparison request through the final evidence-audited response when the canonical Behavior Diff skill runs in Claude Code or Codex.

## Problem

The previous OMP-only advisor change does not satisfy the requested end-to-end skill improvement. A recorded outer orchestration spent approximately 85.5% of its selected interval outside the runner, primarily in model/tool round trips for preparation, preflight and raw-evidence audit. That is a targeting clue, not a measured Claude Code or Codex result.

## Proposed approach

Recommend one shared mechanical path, not an OMP advisor change: extend `prepare_shared.py` to freeze the complete reviewed handoff and add a small local raw-evidence locator. The outer Claude Code or Codex skill still authors purpose, task, scenario, data and checks, exercises required capabilities, reviews privacy/reference closure, and judges every case. The runner, extraction, report format, default trials and models remain unchanged.

1. **Author once.** Freeze purpose before scenario drafting as today. Write the existing task/purpose/scenario/source/notes files and reviewed shared files once; do not introduce another scenario schema or generate their meaning in Python. A private path/settings descriptor names those files, required references, custom tool files and the intended existing runner arguments.
2. **Materialize and freeze together.** Reuse `prepare_shared.py` staging, archive comparison, exclusions, Before resolution and permission guards. An optional private input descriptor lets preparation also validate purpose/scenario/source through their existing Python readers, hash the complete handoff and return one readable inventory plus structured runner-argument handoff. A freeze-only operation supports the existing direct-project path without forcing shared-data staging. The descriptor and inventory stay outside trial projects; nothing launches models or executes commands from JSON.
3. **Verify once immediately before launch.** Extend verification to compare task, purpose, scenario, optional source, notes/criteria, required references, tool implementations and settings as well as the existing project/Before freeze. For a direct Git project, inventory the effective archive plus selected After, not unrelated uncommitted work. Reject mutation/missing inputs, preserve verified absence, and hand the unchanged runner arguments to the existing launch in the same shell environment. Keep semantic capability probes in disposable scratch copies; hashing a probe record does not establish that the capability worked. Avoid a second parent-authored validator or a second scenario review by merely repeating the same reads.
4. **Collect locations, not conclusions.** A private `audit_evidence.py <run-directory>` reads existing trial/status/native logs and produces a navigable inventory of raw calls, returns, terminal events and produced/changed artifacts, with exact file/line or byte locators and omission/error states. It must not use the assessment collector's eligible-read/content budgets as the audit boundary. Index every expected trial, including missing/interrupted ones; preserve duplicate identities and malformed events without inventing attribution. Paginated original-return access and artifact locations let the outer skill inspect every private case in every trial without regenerating extraction scripts. Reuse `read_trial_trace`, `trial_interruption` and progress readers where their contracts fit; do not turn report-ready final text into terminal proof. Raw bytes remain authoritative and private; the helper makes no support/reach verdict, uploads nothing and never rewrites reports.

Make the canonical skill a short ordered handoff to the existing detailed preparation/audit reference, removing duplicate command construction and ad hoc inventory instructions. Keep privacy/consent, early-purpose freeze and historical-isolation stops visible before their affected reads or writes. Detailed source provenance is loaded only for historical comparisons; Jev and Humanizer behavior is preserved, not used as a speed shortcut.

**Simplest alternative:** shorten and deduplicate instructions only, retaining current helper boundaries. This has less code risk, but leaves the task/scenario/notes/tooling inventory and raw-return navigation as repeated model-authored work. Prefer the bounded helper extension because those mechanical gaps are present in the current implementation; native savings remain unproven.

## Risk evidence

Native Codex baselines must precede product changes. Capture phases, agent/tool turns, actual attempts and final raw-evidence audit, not only report rendering or extraction duration. No speed claim from OMP-only measurements.

Existing mechanisms to reuse: `prepare_shared.py:172-176,243-437` inventories content/mode, stages without modifying originals, validates archives and verifies launch inputs; `purpose.read_purpose`, `scenario.read_scenario` and `source.read_source` already enforce the public input contracts. Existing `tests/shared-data-test.py` contains isolated CLI boundary coverage and a manual `--runner-smoke` path with fake Claude/Codex binaries. These are inspected implementation/test mechanisms, not test results from this stage.

One throwaway deterministic exercise ran here against shipped evidence readers using synthetic data only: a `python3 tools/read_state.py` return of 26,029 characters was omitted by `collect_run_evidence` as `not an eligible recorded read`; `read_trial_trace` retained no returned content. A line/byte locator recovered the entire original return exactly, while a separate synthetic native `turn.failed` event remained available independently of normalized final text. This falsifies the report-only/bounded-collector shortcut and supports an unfiltered local locator; it does not prove the proposed production helper, semantic audit quality or native speed. The temporary fixture was automatically removed; no suite, model call or product edit ran.

## Expected surface and tolerance

Bound the implementation to seven files: `plugin/skills/behavior-diff/SKILL.md`, its `references/scenario-and-test-data.md`, `scripts/prepare_shared.py`, new `scripts/audit_evidence.py`, `tests/shared-data-test.py`, `tests/recorded-evidence-test.py`, and `docs/architecture.md`. Reuse validators/status readers without changing their contracts; manifests, runner/trial adapters, extraction prompts, report schemas and CI stay untouched. Update the architecture flow and responsibilities in the same change.

Estimate [INFERENCE]: about 740 changed lines (+600/-140; net +460), tolerance ±35% in changed-line volume (481–999) and one file (6–8 files). Exceeding that surface or changing protected semantics returns to the ideation gate, not silent expansion. One independent product PR based on main `8067a1cb10d7056226589020ffec83e506890045`, after baseline capture and design acceptance; PR #55 remains separate. No additional infrastructure PR or permanent benchmark artifact.

## Acceptance criteria

- **AC-1** Native Codex completes the same three pinned Recce-Team case requests through final raw-evidence audit on both versions, with reduced aggregate end-to-end wall time; report every paired case and phase without hiding slower, incomplete or inconclusive results. Verified by: private native Codex session traces and timing ledger. A candidate no faster overall or a runner-only measurement fails this value criterion. One paired observation per case limits generalization.
- **AC-2** The refactor preserves frozen purpose/scenario/data and reference closure, three trials per side, identical pinned models/settings, privacy exclusions and all-case raw evidence auditing. Verified by: actual frozen inputs, trial projects, statuses, source returns/artifacts and complete audit results. Missing a case or silently reducing delivery or audit invalidates speed acceptance.
- **AC-3** Deterministic mechanics reject stale, invalid or privacy-unsafe preparation and preserve evidence needed to distinguish reached/missed/unknown and supported/contradicted/insufficient. Verified by: exercised helper CLI smoke and relevant isolated boundary tests, including negative paths; prose-presence or forwarding-only tests are insufficient.
- **AC-4** Canonical Claude Code and Codex instructions use the shared improved path; callers, required references and concise architecture documentation agree. Verified by: complete consumer review and actual Codex changed-path execution, with any unexercised Claude-specific runtime limit explicit.

## Test plan

**Native user-value evidence (manual, benchmark owner only).** Use the three default real cases in `e2e/README.md`, not synthetic substitutes or saved reports. Pair main `8067a1cb10d7056226589020ffec83e506890045` with the exact candidate revision: six complete fresh outer Codex skill executions, 36 trials and six extractions, no retries. Pin outer/trials to `gpt-6.1-sol`, extraction to `gpt-6-luna`, and hold host configuration, reasoning settings when available, neutral case requests, contemporary instruction sources and sanitized environment premises constant. The outer skill performs its complete preparation, launch and final raw audit; do not pre-supply a finished scenario to hide preparation time.

For each pair, record native session start through final evidence-audited response, preparation/preflight/runner/audit phases, tool/model turns, attempted/completed trials and cost. Report each duration and candidate-minus-baseline delta plus aggregate totals; preserve slower, failed and inconclusive cases. Independent scenario generation can differ across the two outer executions: retain frozen input digests and coverage mappings per execution, disclose those differences, and distinguish model/data variation from mechanical savings. One pair per case cannot establish causality or a general speed distribution. No all-three-case value acceptance while a required case is held or missing; no promise of a percentage speedup.

**Historical cases and delivery.** Use runbook pins: review `72aa54640948d19932252518a7396643b7064c37` → `eea5e28a41489c24df5e47a61cb07e63c997928b`; TDD `b91299d649932278954985024f82e5654b7e2bef` → `a15d7e0df2fb99f5aecf788e35b9d67745b84b08`; decision `a15d7e0df2fb99f5aecf788e35b9d67745b84b08` → `ceb846c086d0729a0002b79b08c2abb197f571ce`. Fresh agents get only contemporary sources/required references, neutral requests and sanitized fixtures, never this evaluator runbook, later corrections, old results or conversations. Historical selection bias remains disclosed; this is performance verification, not a claim of detected historical defects.

TDD and decision retain matching reference closure with unrelated changed skills absent or constant. Review requires both historical `SKILL.md` and `reference/operations.md` plus `pr-review-response` and its required references. The benchmark owner reports 20 closure files, with two changing files; the existing runner can vary only one. An unchanged standalone operations path cannot select the matching version on both sides, and rewriting historical reference directives changes the source. Therefore exact original filesystem delivery is unavailable in this path.

**Recommended gate choice:** accept review as an explicitly scoped assembled-instruction projection, not an exact two-file filesystem replay. Preserve all matching source fragments byte-for-byte, including both changing files and required reference content, with explicit original-path/revision/fragment mapping. Read the assembled source as a whole rather than claiming its old cross-file paths still resolve; keep the same assembly and reading environment across both Behavior Diff versions. This changes the instruction-loading environment and may affect trial behavior or timing. Captain acceptance must explicitly bind AC-1/AC-2's review-case evidence to this projection; no actor may silently reinterpret matching reference closure as original-path fidelity.

Do not retain contradictory old operations, silently insert redirects, or omit closure content. If the Captain requires original filesystem fidelity instead, hold review until separately authorized folder-capable delivery exists; no all-three-case speed acceptance is possible meanwhile. The prior paired-fixture/`rule.md` extraction route preserves two-file layout but bypasses the canonical runner and cannot substitute for a complete native outer-skill measurement. Do not add a production multi-file feature or second pipeline solely for this benchmark. Review remains held until the projection decision; valid single-file baselines can proceed independently, and no baseline outcomes are claimed here.

**AC mapping and concrete falsifiers.**

- **AC-1 — manual/native:** the private timing ledger and full native traces must show all three complete pairs through final audit with lower aggregate wall time. Excluding preparation/audit, hiding a slower case, using a different stack or a non-improving aggregate fails this value check.
- **AC-2 — offline plus manual/native:** compare actual project snapshots, inventories, source-path mapping, statuses and case-by-trial audit coverage with frozen inputs and approved delivery. A leaked private notes file, stale companion, missing case, changed model/count, post-result input change or outcome inferred only from an answer invalidates acceptance. This checks preservation within each run; independently generated paired scenarios are not falsely called byte-identical.
- **AC-3 — offline:** extend existing isolated helper tests and run the shipped CLI, including the manual fake-host `--runner-smoke` path for both hosts. Exercise each context-file/settings/tool mutation, missing reference, purpose/scenario mismatch, symlink/path escape, Git redirect/archive transformation and absent-Before boundary. For the audit CLI, exercise an adapter return excluded from assessment, long/truncated return, duplicate IDs, missing/malformed logs, native failure with nonempty progress text, ignored/untracked output and symlink escape. Require original-byte locators or explicit missing/unsafe states, not invented successful evidence. Removing mutation rejection, applying assessment budgets to raw navigation, or treating that failed turn as complete must fail these checks.
- **AC-4 — offline consumer review plus manual/native:** inspect the entire canonical workflow/direct references and exercise the changed path in actual Codex, preserving the existing direct-project, staged-data and Spacedock-specific routes. Fake-host exercises cover mechanical Claude argument delivery, not live Claude instruction compliance; disclose that live Claude is unexercised within the approved Codex scope. A stale caller, duplicate inventory recipe or host-only shortcut fails compatibility acceptance.

Implementation owns the relevant checks from repository policy after changes land, including shared-data/recorded-evidence/scenario/purpose/source contracts, selected fake-host smoke, existing live-report contracts, Bash/Python formatting and Markdown whitespace checks as applicable. The independent reviewer remains read-only and does not duplicate execution. Keep all benchmark scripts/data/traces/results outside Git; no CI/model gate, new provider or report rewrite.

## Decisions and dependencies

Captain explicitly requested this complete native-host refactor and selected starting implementation in the original request; this supplies backlog selection, not an unknown design or merge approval. Fresh US$20 working benchmark budget approved, with token-derived monitoring and in-flight-request cap limitation disclosed. Captain separately approved only the pinned private Recce-Team skill files and necessary historical references to OpenAI through Codex plus fresh sanitized fixtures; no private conversations, customer data, credentials, later corrections or historical reports. No OMP or Jev benchmark calls. No authority to push, create/update PR, merge or release this new change.

**Ideation decision requested:** accept the bounded shared-helper/progressive-instruction design and its estimate, and separately accept or reject review-case content assembly with its explicit filesystem-fidelity limitation before that live case starts. No implementation approval, performance result, review acceptance or delivery permission is inferred from this report. Baseline evidence is pending with the separate benchmark owner.

🧠 Kent's brain recommends: keep scenario and evidence judgment with the outer skill, and package only repeated freeze/handoff and raw-navigation mechanics (confidence: high).
Why: this targets the observed round-trip burden with the smallest shared change while preserving the evidence needed to reject a misleading speedup.

### Feedback Cycles

## Out of scope

OMP advisor configuration; changing models, trial counts or evidence standards as a speedup; report presentation redesign; source-purpose hindsight; new CI lanes, standing gates, permanent benchmark infrastructure; unrelated workflow repair; automatically modifying PR #55.

## Stage Report: ideation

- DONE: Recommend the smallest shared refactor that removes native-host preparation/preflight/audit round trips while preserving every privacy, purpose, coverage and raw-evidence boundary; no OMP-only substitute.
  Proposed approach bounds the existing helper extension and local raw locator; models, trial count, semantic preflight/audit, consent and historical isolation remain unchanged. Savings are a hypothesis, not a measured result.
- DONE: Give bounded affected files, user-value AC mapping, concrete falsifiers and a native Codex paired benchmark plan across the three required real cases, resolving companion-file delivery honestly.
  Seven-file estimate with ±35% changed-line tolerance; AC-1–4 map to external offline/native evidence. Review assembly is explicitly a source-content projection requiring gate acceptance; review live case stays held, not omitted.
- DONE: Exercise only the riskiest deterministic helper mechanism if needed; cite proven existing mechanisms otherwise. Return a concise committed ideation report and no product edits or model-backed benchmark calls.
  Synthetic locator exercise recovered 26,029 returned characters absent from both assessment excerpts and report trace reader; existing staging/parsers/tests are cited without claiming a suite pass. Only this state entity is changed and committed.

### Summary

Recommend extending shared preparation/freeze mechanics and indexing original raw evidence instead of reducing experiment scope or delegating judgment to another model. Native performance proof remains with the benchmark owner; the Captain must decide the review-case assembly fidelity limitation before that case can run, and no product implementation or new delivery authority is implied.

## Stage Report: implementation

- DONE: Implement the approved shared preparation/freeze and raw-evidence-navigation path in the assigned worktree, migrate canonical skill/reference callers and update concise architecture documentation, preserving all protected behavior.
  Signed candidate `c090d028b9bf2c565dbf227d5b6eecbd443cca24` extends shared preparation/direct freeze with validated private context and runner arguments, indexes original raw evidence/artifacts, and migrates canonical callers and architecture; runner, models, trial count and report/extractor contracts remain unchanged.
- DONE: Exercise the shipped helper CLIs and relevant negative privacy/staleness/raw-evidence boundaries, run applicable deterministic checks and formatting once after changes, fix owned failures, and record exact evidence without source-text or forwarding-only tests.
  The commands and falsifiable claims below passed against the shipped helpers; new permanent tests use synthetic consumer-visible boundaries, not wording or forwarding assertions.
- DONE: Deliver a DCO-signed exact candidate and complete criterion-mapped implementation report; coordinate frozen native baseline/candidate timing with the independent benchmark owner, with no unapproved models, hidden scope reduction or speed claim before valid paired evidence.
  Candidate identity and offline evidence were handed to NativeCodexBaseline with paid launches explicitly held; that owner confirms zero valid complete native baselines and no independent candidate execution yet.

### Exercised evidence

- `python3 tests/shared-data-test.py --runner-smoke` — 35 passed: shipped prepare/freeze/verify plus fake Claude/Codex runner/adapters exercise complete handoffs, 3+3 delivery, private exclusions, stale context/settings/tools/references, invalid scenarios, archive/Git redirects, symlinks and absent Before. Removing mutation rejection or delivering excluded notes would fail these checks.
- `python3 tests/recorded-evidence-test.py` — 25 passed: raw CLI reconstructs original adapter returns beyond assessment eligibility/budgets, retains duplicate/malformed/missing evidence and native failure despite progress text, and accesses ignored/untracked artifacts while rejecting link/path escape. Filtering raw returns or following the escape would fail.
- `python3 tests/scenario-contract-test.py` — 10 passed; `python3 tests/purpose-handoff-test.py` — 4 passed; `python3 tests/source-provenance-test.py` — 9 passed: shared input contracts still reject invalid/mismatched records and preserve protected purpose/source behavior.
- `python3 tests/report-source-test.py` and `bash tests/live-report-contract.sh` passed: source provenance, captured/self-reported prompt/report behavior and invalid-configuration handling remain compatible; no extractor schema or prompt changes.
- `uvx ruff@0.16.5 format plugin/skills/behavior-diff/scripts/prepare_shared.py plugin/skills/behavior-diff/scripts/audit_evidence.py tests/shared-data-test.py tests/recorded-evidence-test.py` completed; `uvx ruff@0.16.5 format --check --diff .` passed for 154 files; `git diff --check` passed.
- `docker run --rm -v /Users/kent/Dev/InfuseAI/Spacedock/behavior-diff/.worktrees/spacedock-ensign-speed-up-canonical-skill:/mnt -w /mnt mvdan/shfmt:v3.14.0 -d -i 2 -ci .` passed. All checks ran after implementation; no model-backed check or paid call ran.

### Acceptance and limits

- AC-1: UNVERIFIED. Zero valid complete native baselines and no candidate native run; no end-to-end timing comparison or speedup claim. Required native paired performance evidence remains an open gate, not a passing offline result.
- AC-2: Offline preparation/privacy/reference delivery and default trial mechanics passed the synthetic checks; complete real-case frozen inputs and all-case semantic raw audits remain UNVERIFIED with the held native benchmark.
- AC-3: Exercised shipped helper CLI boundaries and original-byte reconstruction passed as detailed above. Index presence is navigation, not a completion, attribution or requirement verdict.
- AC-4: Canonical Claude/Codex callers and architecture use the shared path; fake-host smoke exercises both adapters. Actual changed-path Codex execution and live Claude instruction compliance remain UNVERIFIED; Spacedock-specific fixture delivery remains intentionally unchanged.
- Surface: seven approved files, authored 979 changed lines before formatting; formatted +1002/-226 = 1,228 exceeds the 999-line estimate ceiling. FO explicitly authorized mechanical formatter expansion within unchanged behavior/file scope; no claim of staying within tolerance.
- Sequencing: FO lifted its own baseline-before-edit hold after independently freezing the old archive; this was an FO-owned sequencing correction, not a new Captain ruling or a waiver of native performance evidence.
- DCO: this candidate and this report use signed-off, path-scoped commits. Earlier already-pushed unsigned FO state history remains preserved; it was not repaired or represented as signed. No code push, PR, merge, release, provider switch or sandbox bypass was performed.

### Summary

Completed the shared mechanical refactor and its offline CLI, safety and formatting evidence without changing the approved models, trial counts, privacy boundaries or semantic audit ownership. The exact candidate is ready for independent review; native performance and real-case preservation remain explicitly unverified and must not be inferred from the passing synthetic checks.
