# gh-aw original change: one Behavior Diff evaluation

Date: 2026-10-13

## Main takeaway

One restricted historical run produced no actionable risk warning. It did not
establish that the change was safe. The selected scenario needed no new issue,
all completion calls were blocked, and extraction lacked key tool evidence.

The next questions are separate: did scenario selection cover the risky use,
and could the assessment see what the tools actually did?

## Why we chose this case

We want to learn from real histories: an instruction change, an unexpected user
symptom, and a later fix. The question is whether evidence available at the
original change can support a useful warning. Predicting the exact future
incident is not the goal.

This case was selected with knowledge of its later history. It is not a blind,
hindsight-free benchmark. Trial preparation still used restricted historical
inputs. The later events below are background for this note only. They were
not given to preparation, trials, or extraction.

## Public history

- **February 24:** [Issue #18039](https://github.com/github/gh-aw/issues/18039)
  proposed clearer `noop` guidance so agents would not finish without safe
  output. Its motivation came from automated or synthesized analysis, not a
  verified runtime failure rate.
- **February 24:** [PR #18045](https://github.com/github/gh-aw/pull/18045)
  added a shared rule requiring exactly one safe-output tool call. It also
  strengthened `noop` guidance in workflow prompts and documentation.
- **Already present before the change:**
  [smoke-temporary-id.md](https://github.com/github/gh-aw/blob/e750213164c252471a1b1add8d32ebdb8f34ee94/.github/workflows/smoke-temporary-id.md)
  required three issues and a summary comment. Its limits allowed five issues
  and two comments. This was contemporaneous evidence of a workflow needing
  several outputs. This experiment did not give that workflow to the skill.
- **March 23:** A user reported in
  [issue #22364](https://github.com/github/gh-aw/issues/22364) that
  gh-aw 0.62.5 with Codex planned five issues, emitted `missing_tool`, and
  created none. The configured quotas allowed the writes.
- **March 24:** [PR #22576](https://github.com/github/gh-aw/pull/22576)
  changed the rule to at least one call and exposed per-tool limits.

The original incident logs and temporary repository are gone. No same-task
post-fix replay was found. The history supports a plausible instruction
conflict, but does not provide a complete causal replay. A related bot review
appeared about five minutes after the original merge. It discussed adjacent
`noop` conflicts, not a pre-merge warning about the global restriction.

## Earlier exploration was a different test

An earlier controlled Task Miner mock compared the repair pair. Its raw-log
audit showed one call in each Before trial and five in each After trial.
That was separate evidence. Extraction did not verify that result, and it did
not demonstrate predictive success. We did not reuse its fixture or outputs
in the original-change run below.

## This experiment

We verified this original snapshot pair through immutable Git objects:

- Before: `e750213164c252471a1b1add8d32ebdb8f34ee94`.
- After: `fe2713ba4bb447a2e38905f4a47920531bc59cdd`.
- After's only parent is Before. Their UTC times are February 24, 03:52:33
  and 04:25:20.

The diff changed 139 files, including 137 prompt candidates. The normal skill
needed one selected instruction file. We then made a transparent human scope
choice: `actions/setup/md/safe_outputs_prompt.md`, the shared runtime template
referenced by the compiler and copied by setup. This was source-structure
selection, not autonomous product discovery or a supplied behavior hypothesis.
We excluded 136 workflow source prompts, one generated lockfile, and one
reference document.

We used the current local Behavior Diff 0.4.6 without changing product code.
Initial discovery recorded checkout `5b8b692`; preparation verification
recorded `91e370`. The runner and extractor files are identical between these
revisions. Implementation hashes are retained in the local audit. Runtime was
Codex CLI 0.162.1 through the included ChatGPT subscription: `gpt-6.1-sol` for
preparation and trials, and `gpt-6-luna` for extraction.

A fresh context followed the normal skill and drafted one maintenance-triage
scenario. Tests and build passed. A broken tutorial link already had an open
issue. The agent had to decide whether uncovered work needed a new issue.
No expected failure or target outcome was supplied. Source-derived purposes
were frozen before trials and kept out of trial inputs.

Exact instruction bytes were placed in independent trial copies as AGENTS.md.
Tools were offline mocks. Network and outside-file access were restricted.
No later issue, fix, PR comment, prior experiment, or research memory entered
the run. No real GitHub writes occurred. We completed three Before trials,
three After trials, and one extraction. We did not tune or repeat the run.

## What we found

- Both sides chose no new issue in all three trials.
- The standard report selected no attention findings: `attention.findings: []`.
- Both tool checks were marked insufficient evidence on both sides: whether
  exactly one safe-output call occurred, and whether its message explained
  the analysis and reason for no action.
- Raw records show six `noop` attempts, one per trial. All were rejected with
  `MCP tool call requires approval, but approval policy is never`.
- Successful mock deliveries: zero. This was a local runtime blocker, not an
  observed upstream defect.
- The existing normalizer omitted MCP events from extraction. The bounded
  collector also omitted the combined file-read returns as ineligible reads.

The product counts six valid final answers. That does not mean tools succeeded.
Its unedited report says both sides reported rejected no-action records.
A separate raw audit preserves the missing call arguments and errors. We did
not feed that audit back into extraction or rewrite the report.

## What remains open

**Scenario coverage:** the selected scenario tested no-action completion. It
did not test a workflow with several legitimate outputs. This run cannot show
whether normal preparation would find that broader conflict.

**Tool evidence:** blocked calls and omitted events limited assessment even
within the chosen scenario. No warning is an inconclusive result here, not
proof of safety or proof that Behavior Diff cannot find such risks.

Possible next checks are proposals only: assess how historical workflows enter
scenario selection; verify harmless mocks can run; and verify native MCP calls
and returned content reach extraction. No implementation or rerun is approved
by this note.

## Local evidence

The unedited HTML and Markdown reports, raw tool evidence, audit, source
verification, scenario rationale, and frozen-input manifest remain in the
private local experiment directory. Machine-specific paths are omitted.

These artifacts remain local. This note adds no commitment to change the
product, publish evidence, or run another experiment.
