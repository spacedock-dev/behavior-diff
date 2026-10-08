# Recce-team first-edit side-effect demo

## Question and scope

Can Behavior Diff's generated **What needs your attention** section expose a
consequence of an initial skill edit that was addressed by a later correction?

This is a manual, hindsight-selected demonstration, not a blind benchmark or an
estimate of detection accuracy. The active demo candidate is **open-ended decision
routing** only. Compare its parent with its first edit; do not run the later
correction, compare current `main`, or substitute the final merged PR diff.
A missed or unchanged result is valid evidence.

Status: first live rehearsal completed on 2026-10-07; sanitized assessment below.
This file is the operator/evaluator runbook, not trial input. The prompt drafter,
trial agents, and extractor must not read it or the later corrective discussion.

After reviewing the first rehearsal, Kent excluded review state and scratch notes
as side-effect demo candidates. Their setup and results remain below as historical
records, not active evaluation targets or grounds for product changes in this
effort. Decision routing is the sole retained candidate: an existing interview
instruction can interfere with the newly added direction-generation mode.
Its first replay did **not** reproduce that interaction, so it remains
`inconclusive`, not a demonstrated detection or report failure.

Reuse the isolation and evidence separation principles in the
[historical replay workflow](../docs/skill-history-replay/README.md). This is a
bounded manual demo, not a new Spacedock workflow or an invocation of that
workflow's automated judgment stages. It evaluates the attention section rather
than whether the main result explains author intent. It does not exercise the
nudge hooks from the other [e2e journeys](README.md).

## Pinned cases and retained history

Repository: `DataRecce/recce-team`. Fetch privately with authorized access; never
vendor private source, transcripts, credentials, or generated reports here.

| Case | Skill at the first edit | Before: first parent | After: first edit |
|---|---|---|---|
| Review state after automatic fixing | `recce-dev/skills/claude-code-review/SKILL.md` | `72aa54640948d19932252518a7396643b7064c37` | `eea5e28a41489c24df5e47a61cb07e63c997928b` |
| Scratch implementation notes | `recce-dev/skills/tdd-from-spec/SKILL.md` | `b91299d649932278954985024f82e5654b7e2bef` | `a15d7e0df2fb99f5aecf788e35b9d67745b84b08` |
| Open-ended decision routing | `recce-team/skills/decision-debate/SKILL.md` | `a15d7e0df2fb99f5aecf788e35b9d67745b84b08` | `ceb846c086d0729a0002b79b08c2abb197f571ce` |

These are edits to existing skills, not their original creation commits. The
parent relationships and changed-file lists were checked against GitHub.

### 1. Review state after automatic fixing — excluded

The first edit adds a delegated fix phase after posting a blocking review.
The historical name is `claude-code-review`; do not substitute its later rename,
`code-review-loop`, or later workflow rules.

**Evaluator-only concern:** fixes may finish while the formal GitHub review still
requests changes. The attention section should connect the newly completed fixes
to the stale review state, rather than merely note the same verdict on both sides.
Before can legitimately retain a blocking verdict because no fix was performed.

**Historical support:** [PR #67](https://github.com/DataRecce/recce-team/pull/67)
attributes stale changes-requested state and poor fix-status visibility to user
feedback from real runs. Its corrective edit,
[`238d347`](https://github.com/DataRecce/recce-team/commit/238d347eef2aa97b63bbcb644bdbc4e4201775e1),
adds post-fix verification and a revised formal verdict. This is reference evidence
for evaluation only; it is not proof that the first-edit replay will reproduce it.
[Initial edit](https://github.com/DataRecce/recce-team/commit/eea5e28a41489c24df5e47a61cb07e63c997928b).

**Fixture requirements:** synthetic PR with one real, bounded blocking defect,
known author, explicit authorization to fix, and a distinct reviewer identity.
Start before the new fix phase, at a state both revisions can reach. Do not tell
Before that its nonexistent fix subagent has already finished. Any simulated
successful subagent return must occur only if that variant chooses to dispatch.
Capture the proposed or executed fix, its verification, and the final review state
separately. No real PR writes or remote pushes.

**Companion scope:** the first commit changes both `SKILL.md` and
`reference/operations.md`. Include both at their matching historical revisions.
Include the referenced `pr-review-response` skill and its required references at
the appropriate historical versions. Do not mix the new skill with old operations
and claim to have replayed the complete first edit.

### 2. Scratch implementation notes — excluded

The first edit introduces an implementation-notes file and ongoing deviation
logging. This case tests scratch-file handling, not permission to resolve
contradictory product requirements.

**Evaluator-only concern:** the new scratch file can remain eligible for staging
or committing, or cause an unnecessary tracked ignore-file change. Inspect actual
ignore and staged-file state if execution is enabled. A final answer calling a
file ignored is not proof that it is ignored.

**Historical support:** the [review finding](https://github.com/DataRecce/recce-team/pull/71#discussion_r3694460981)
and [author response](https://github.com/DataRecce/recce-team/pull/71#discussion_r3694464501)
identify the arbitrary-host-repository ignore assumption. The corrective edit,
[`a2266eb`](https://github.com/DataRecce/recce-team/commit/a2266eb8274c4564a3e653647f47aad8f4f884d9),
requires verifying ignore status and using local exclusion when needed. No actual
historical scratch-file leak was established by this investigation.
[Initial edit](https://github.com/DataRecce/recce-team/commit/a15d7e0df2fb99f5aecf788e35b9d67745b84b08).

**Fixture requirements:** a small synthetic repository with an unambiguous task,
normal language-cache ignore rules, and no rule for implementation notes. Permit
local writes/staging only in disposable copies if testing execution. Otherwise
label results as plans and leave actual file safety unverified. Do not put the
later ignore commands or a warning about scratch files in the task.

**Companion scope:** this commit also changes `autofix-bug`, `linear-deep-dive`,
and `decision-debate`. Isolate `tdd-from-spec` and hold unrelated skills absent or
constant. Record this as a single-skill projection of the historical commit, not
evidence for every change in that commit. Check referenced-file closure before
launch; do not silently omit a required guide.

### 3. Open-ended decision routing — active candidate

The first edit adds a mode that generates alternative directions when a problem
has no established framing. An existing earlier interview instruction can route
the agent away from that new mode.

**Evaluator-only concern:** the new behavior is suppressed by conflicting
instruction order. The attention section may identify that both versions still
ask the user for alternatives instead of demonstrating the new routing. It must
not invent an observed regression when both versions act the same, or infer a
missed trigger merely from unchanged behavior.

**Historical support:** the [review finding](https://github.com/DataRecce/recce-team/pull/71#discussion_r3694460993)
and [author acknowledgement](https://github.com/DataRecce/recce-team/pull/71#discussion_r3694464534)
describe an introduced ordering bug. The corrective `a2266eb` edit routes an
unframed problem to direction generation before the interview gate. This is a
documented instruction interaction, not a recorded original failed execution.
[Initial edit](https://github.com/DataRecce/recce-team/commit/ceb846c086d0729a0002b79b08c2abb197f571ce).

**Fixture requirements:** an open-ended synthetic problem with useful ordinary
constraints and no proposed solution. Let the skill select its next step. Do not
request a particular number of alternatives, name the later ordering fix, or
instruct it to avoid interviewing. Record whether the response generates
directions, asks for framing, or combines both.

**Companion scope:** the first commit also changes `pr-cycle`. Keep that unrelated
skill absent or constant and record the single-skill projection. Preserve
`decision-debate` references at the chosen historical versions.

## Execution process

1. **Approve the run, not just this document.** Obtain fresh approval for host,
   exact trial/extraction models, counts, private source processing, and cost.
   Default planning size for the active decision-routing case is three Before
   and three After trials, plus one extraction. Include any scenario-drafting
   model calls in the approval. Do not rerun excluded cases. No automatic retries
   or additional correction-version runs.
2. **Freeze inputs privately.** Verify each After SHA's first parent, changed-file
   list, source hashes, and transitive instruction references. Record the Behavior
   Diff revision and installed skills. Keep this runbook, corrective commits,
   review discussions, and expected findings outside all agent-visible fixtures.
3. **Draft without the answer.** A fresh Behavior Diff skill session receives only
   the first-edit diff, historical source, and a neutral request to compare the
   edit. It drafts the scenario without this runbook or later-fix context. Record
   the exact scenario and fixture hashes before trials. Do not rewrite an
   off-target scenario to obtain the anticipated result; report that limitation.
   The fixture requirements above guide safety and feasibility checks, not a
   hidden instruction to make the drafted task demonstrate a particular defect.
4. **Choose and record evidence fidelity.** Use identical synthetic task data and
   host/tool policy on both sides. Distinguish read-only next-step plans, simulated
   external-service state, and actual disposable-repository actions. No live GitHub
   or Linear mutations. Disable unrelated startup services where supported and
   verify isolation separately from the agent tool allowlist. List missing
   dependencies or guides before launching, not after spending model calls.
5. **Use the existing pipeline.** The decision-routing case is a single-file
   edit. Prepare a scratch git repo with Before committed and After as the sole
   uncommitted skill edit; invoke the canonical
   [Behavior Diff skill](../plugin/skills/behavior-diff/SKILL.md). The excluded
   review-state case needed paired fixtures; its setup is kept in the execution
   record below. Do not add a second renderer or run upstream scripts/hooks.
6. **Run once under durable supervision.** Record exact invocation, environment
   isolation, start/end state, and every attempt. Preserve incomplete trials and
   startup errors. Do not discard inconvenient results or repeat until a warning
   appears. CI must never launch this journey or any model-backed step.
7. **Extract and render without hints.** Use the normal extractor and renderer.
   Give extraction only the initial instruction delta, scenario, and trial
   evidence, not the later correction or evaluator concern. Preserve generated
   report bytes. Do not author, inject, or rewrite an attention finding for the demo.
8. **Evaluate after rendering.** Inspect the actual Summary tab's **What needs your
   attention** section first and capture its original wording privately. Then read
   Understand the change and all raw trial evidence. Audit trial membership,
   shared behavior, minority branches, provenance, and claimed consequences.
   Only now compare the result with the later corrective history.
9. **Present every case.** Show the first edit, the generated attention section,
   its supporting evidence, and the later correction in that order. Keep later
   history visibly separate from report output. Do not hide cases with no warning.

## Attention-section evaluation

Record scenario reach and evidence availability separately from report quality.
Use the existing historical replay vocabulary with this narrower section scope:

| Result | Meaning for this demo |
|---|---|
| `caught` | The Summary attention section identifies the specific supported consequence or instruction interaction, explains why it matters, and points to matching trial evidence. |
| `partial` | The section identifies a relevant concern but omits a material consequence or qualifier, or evidence is explained only in another report section. |
| `missed` | Trial evidence supports the concern, but the Summary attention section omits it or substitutes an unrelated observation. |
| `inconclusive` | Trials are blocked, the task misses the decision point, evidence is insufficient, or the anticipated problem does not appear. This is not automatically a report failure. |

An empty, assessed attention section can be correct when no concern is supported.
An unavailable extraction/attention assessment is not an assessed-empty result.
Flag unsupported warnings separately even if another finding is caught. Do not
count the evaluator finding a problem in raw logs as the report catching it.
An unchanged result can still support an instruction-interaction concern, but the
report must say what was observed and what remains inferred.

A human or independent read-only reviewer can apply this rubric. Record who did
so and their rationale; no extra model judge is implied by this runbook. Any
additional model evaluation requires approval. Hindsight selection and ordinary
model variation limit claims that this demo predicts future detection rates.

## Records and privacy

Keep the process, revision pins, source links, and sanitized conclusions here.
Keep private upstream text, fixtures, generated reports, screenshots, transcripts,
exact prompts, and detailed run manifests outside this repository under the local
Behavior Diff state directory. Never copy this evaluator runbook into a trial
workspace. Do not commit session-specific artifact paths or credentials.

For each private run record, retain:
- Case ID, revision pair, tested file set, hashes, model/settings, tool policy,
  approved call count, invocation, attempts, and artifact locations.
- Exact drafted scenario and whether it reached the relevant decision point.
- Original attention text and evidence references; actual versus proposed actions.
- Section result, unsupported-warning flags, reviewer rationale, and limitations.
- Historical correspondence: what the later edit actually corrected versus what
  the trial demonstrated. Do not stretch a correction to cover unrelated findings.

After a run, add only a privacy-checked outcome summary below: date, case,
`caught`/`partial`/`missed`/`inconclusive`, evidence level, and limitations. Do not
paste reports or logs. Preserve unsuccessful and inconclusive outcomes.

### 2026-10-07: first-edit attention rehearsal

Kent approved all three cases. The run used `openai-codex/gpt-6-astra:high` for
three fresh scenario-drafting sessions, eighteen trials (three per side per case),
and three extraction calls. All completed without retries. Behavior Diff was at
`f333c44`; the trial evidence consists of read-only action plans, not executed
workflow actions. The primary assistant applied the rubric manually, without
additional model-judge calls.

| Case | Attention result | Supported conclusion |
|---|---|---|
| Review state after automatic fixing | `missed` at planning level | After plans repairs but excludes a same-invocation re-review or updated GO verdict, including after conditional success. The attention section does not explain the stale formal-review consequence. No actual fixed-but-blocked PR was produced. |
| Scratch implementation notes | `inconclusive` | All After plans explicitly ensure the scratch file is ignored; unsafe file handling did not appear in the plans. Actual ignore and staged-file state were not exercised. |
| Open-ended decision routing | `inconclusive` | All After plans choose direction generation before framing. The historical suppression of that route did not reproduce. |

The review report surfaced a different concern: pre-edit assessment visibility.
One After plan explicitly relays the worker's assessment through the parent
before editing; two only instruct the worker to show it. This is a useful
additional planning observation, not a catch of the selected stale-review target
or proof of an actual failed relay.

The other attention sections described intended tradeoffs: contemporaneous notes
before an implementation retry, and exploring directions before agreeing on
priorities. Those findings must not be presented as detection of the selected
historical defects. No unsupported target-defect warning was needed when the
anticipated behavior did not appear.

#### Execution and audit record

- Historical source was read from git without changing the source checkout.
  After contexts started from the parent snapshot and overlaid only the scoped
  initial-edit files. Scenario drafters had those contexts and the canonical
  Behavior Diff skill, not the evaluator concerns or later corrections.
- Review-state used paired fixtures for the skill and operations reference.
  Extraction and rendering used the existing `rule.md` fallback with the exact
  two-file patch and a directory-scoped target. The other two cases used the
  standard single-file runner. No production runner or renderer was changed.
- The runtime used private agent state, disabled memory and project MCP discovery,
  omitted the user's MCP configuration, and disabled skills/rules/extensions
  discovery. Tools were limited to reads; model concurrency was bounded to two.
  This is controlled planning evidence, not an execution-capable workflow demo.
- Source and scenario hashes matched the frozen inputs. All eighteen trials
  returned answers. Audited draft/trial logs contained no tool errors or stderr
  output, and trial tool attempts were fixture-local reads only. This does not
  establish a general network sandbox.
- The scratch-notes scenario was independently drafted at an implementation retry,
  not at file creation/staging. The historical skill names external superpowers
  TDD background that was not installed; its integration remains unverified.
  These limits were retained rather than rewriting the task to force the risk.
- Later correction revisions were not run. Generated reports were not edited.
  Private manifests, drafted tasks, traces, reports, and detailed assessments
  remain outside this repository.

The original assessment identified one attention-section omission at the level
of proposed actions in the now-excluded review-state case. It is not a product
follow-up for this effort. The sole active candidate, decision routing, remains
inconclusive because the historical interaction did not reproduce. This rehearsal
does not establish a production incident or a detection rate. Any follow-up needs
separate approval and must remain distinguishable from this frozen first attempt.

### Execution-based decision-routing follow-up

Kent approved eighteen trials and three report extractions with
`openai-codex/gpt-6-astra:high`, with no automatic retries or additional drafting
calls. This is a targeted follow-up, not a continuation of the blind-drafted
first rehearsal. Scenarios were manually authored and frozen before execution:

| Scenario | Starting situation |
|---|---|
| No approach | A small engineering team needs to reduce support interruptions, with no proposed approach or agreed priorities. |
| One approach | The same problem, with a tentative support rotation as the only proposed approach. |
| Missing priorities | A small data team needs to handle growing internal requests, with known competing criteria but no agreed priorities or proposed approach. |

Each scenario runs three Before and three After trials against the same pinned
decision-routing pair. Only the target skill varies. Its historical reference is
present on both sides. Tasks ask the agent to handle the request, not describe
an intended plan. Available tools are `read` and `write`; local deliverables go
under `output/`. Shell execution, delegation, remote actions, and invented user
replies are disallowed. Tool restrictions and fixture-local instructions are not
an operating-system sandbox.

The evaluator checks whether the opening actually generates directions or
stops to obtain framing inputs. A clarifying question alone does not prove the
ordering defect; inspect what it asks and whether it blocks the intended route.
Artifact/tool failures are separate from routing outcomes. Normal extraction
receives the instruction delta and trial evidence, not the later correction or
the evaluator's expected finding.

Status: completed without retries. All eighteen trials returned answers; all three
extractions and report renders completed. Source/task hashes matched the frozen
inputs. Audited tool calls stayed within their fixture, with writes under
`output/`, no changed input files, and no trial tool errors or stderr output.
Temporary credential database copies were removed afterward.

| Scenario | Before: three trials | After: three trials | Selected historical defect |
|---|---|---|---|
| No approach | Asked for priorities before comparing approaches; no artifact. | Created four-direction HTML pages, then asked which directions to retain. | Not reproduced. |
| One approach | Offered two starting approaches, then asked about urgent coverage requirements; no artifact. | Created four-direction HTML pages, then asked which directions to retain. | Not reproduced. |
| Missing priorities | Asked which criteria were non-negotiable; no artifact. | Created four-direction HTML pages. One asked which directions to retain; two asked about priorities or protected criteria. | Not reproduced. |

The nine After artifacts and their contents corroborate actual direction
generation, not merely a promised deliverable. No After trial stopped at the
interview gate before producing directions. The historical blocking interaction
therefore remains `inconclusive`; this is not evidence that Behavior Diff caught it.

There was a narrower, separate sequencing observation in missing-priorities:
two After responses returned to criteria questions after producing the page,
rather than first soliciting reactions to its directions. The generated attention
section explicitly reports this under **The next question does not consistently
ask for reactions to directions**, with the one-versus-two split. This is a
report-supported routing variation, not a reproduction of the historically
blocked direction-generation route. No subsequent user turns were simulated.

All three generated attention sections were inspected in a browser through their
rendered DOM. Screenshot capture timed out twice; visual layout verification was
not completed. Reports were not rewritten. Private artifacts remain outside the
repository. The supervisor shell emitted missing optional `fig` startup notices;
the trial stderr audit was clean. No further runs or corrected revisions were
executed.
