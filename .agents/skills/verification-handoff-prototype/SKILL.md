---
name: verification-handoff-prototype
description: Operates a local conversational handoff-to-decision replay with corrected goals and scoped evidence. Use when an owner explicitly requests the verification handoff prototype with a supplied change, context and local evidence packet; not for ordinary Behavior Diff trials.
---

# Verification handoff prototype

Answer whether the owner can hand off verification work and decide from credible
evidence. This is a maintainer prototype, not the installed Behavior Diff skill.
Use these same instructions on Claude Code and Codex; OMP may load this source
path explicitly. Do not infer installed discovery or Spacedock adapter support.

## Prerequisites and boundaries

Use Python 3.10+ and the bundled `scripts/replay.py`; no dependencies or service.
Read only the supplied change, discussion/documents and explicit case root.
Do not search transcript stores, unrelated archives or the related reader study.
Read private evidence only with permission; never send it to a new model/service,
copy it into a tracked tree, launch a trial, change source evidence or publish it.
Explain: fixed-evidence replay, not fresh verification, latency measurement or
first-time intent inference. Disclose familiarity with the known case. Historical
purpose remains frozen: corrected replay goals do not rewrite experimental intent.
The production skill's automatic-launch and frozen-purpose contracts are unchanged.

For an offline demonstration use `fixtures/synthetic.json`, explicitly invented.
For the real walkthrough prepare the private packet yourself from permitted local
sources, with source coordinates, reused labels, provenance and limits. If missing,
report that prerequisite; never substitute synthetic findings for the real case.

## Conversation

1. Before showing results, use the supplied context to propose the modification
   intent, preserved requirements, bounded evidence-review plan and limits. Label
   each goal explicit or inferred with its source. Ask only about material
   uncertainty: recommend a bounded option, allow none-of-the-above/free correction.
   Do not ask the owner to select evidence IDs, design tests or repair mappings.
2. Capture the owner's usual verification approach and remaining question in their
   own words during this same walkthrough. Do not assume their bottleneck or invent
   a response. Record observations privately only with consent; no raw transcript
   persistence by default. The helper stores only goals, reviewed bindings and choice.
3. Initialize the snapshot with your proposed goals. Apply exact owner corrections,
   then confirm the current revision only after actual confirmation. Do not treat
   a helper success as owner consent. Continue directly to evidence review/results
   without requiring another “please continue”. A correction clears that goal's
   support, confirmation and prior decision; unchanged goals retain their support.
4. Review records against each *current exact requirement*. Bind supported or
   contradicted observations only with scoped citations, a reason and scope.
   Matching words do not establish semantic equivalence. Missing support stays
   unverified with a concrete next verification step; do this mapping yourself.
5. Request the confirmed result. Lead with findings, reasons, limits and decision
   consequences, then offer exact read-only evidence entries. Distinguish
   preservation, case reach, environmental blockers and recovery. Name reused versus
   synthetic evidence; distinguish saved authors' interpretations from inspected
   action/return/artifact slices. Do not claim whole-flow/service coverage from a slice.
6. Let the owner inspect evidence, correct again, accept the stated limits, revise,
   or request a bounded additional-verification proposal. Record only that choice;
   “accept” never adopts, merges, changes files, runs models or contacts a service.
7. With consent, privately record each actual takeover, trigger, work, observable
   attention/wait burden, and necessary owner choice versus avoidable agent work.
   Ask what decision is now possible, what still needs checking and which remaining
   burden is most costly versus their baseline. Select the next experiment from
   that answer. Negative/inconclusive value is valid; praise is not value evidence.

## Helper protocol (host-operated, not owner homework)

Create a private directory outside **all** Git trees (mode 0700); snapshot files
are mode 0600. Keep private packets there too. Run from the repository root:

```sh
python3 .agents/skills/verification-handoff-prototype/scripts/replay.py \
  --state "$PRIVATE/session.json" --root "$CASE_ROOT" <<'JSON'
{"action":"init","goals":[{"id":"review","text":"Stop for human review.","basis":"inferred","reference":"Supplied change","next":"Inspect the final stop and adoption actions."}]}
JSON
```

One JSON action on stdin per invocation, one JSON result on stdout; errors go to
stderr with exit 1. Every action except `init` and read-only `show` requires `revision`.
Use `show` to recover it; stale calls fail rather than silently rebase. Commands:

- `correct`: `id`, exact `text`; `replace`: complete `goals` list, clears all support.
- `bind`: `id`, `status` (`supported`/`contradicted`), `origin` (`reused`/`synthetic`),
  nonblank `reason`, `scope`, and `citations` list of `{path,start,end}` objects.
  Paths are relative to the supplied root; line ranges inclusive, at most 120.
- `confirm`, then `result`: no extra fields. Changed/missing citations become gaps.
- `evidence`: `citation` object; prints numbered source lines without execution.
- `decide`: `choice` (`accept`/`revise`/`request-verification`); requires the current
  result. Any correction returns to confirmation/review; never relabel old results.

Keep the runnable private packet and a concise walkthrough handle for gate review,
not a fabricated owner transcript. Helper smoke/tests establish mechanics only;
AC-1/AC-2 need actual owner interaction and AC-3 remains owner-dependent.
