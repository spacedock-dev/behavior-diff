# Optional Jev assistance

This is an outer-skill advisory step shared by Claude Code and Codex, for both
headless and live comparisons. It does not change trials, extraction, grading,
or report JSON/HTML. Never invoke it inside a trial or extraction call.

## Decide whether to use it

Proactively look for an unresolved semantic decision that Jev could help with:
rank candidate evidence for inspection, classify a finding, assess whether
observations support a criterion, or evaluate competing hypotheses. These are
opportunities, not a quota. Keep deterministic checks in code. If no useful
opportunity exists, make no call and disclose that reason.

Inspect only whether `TYPESAFE_API_KEY` is present/nonblank in the current
process, without displaying its value. Do not enumerate the environment, search
credentials or dotfiles, source profiles, or ask for a key in conversation.
The helper validates that named variable internally. Missing configuration leaves
the existing evidence assessment available; do not install dependencies.

A token is not permission to spend money or send data. Before each new Jev scope,
name **TypeSafe/Jev**, the payload category, decision purpose, request/state count,
and cost ceiling, and obtain explicit approval. Reuse approval within those
bounds, not per question. Approval for the comparison's assessment provider does
not cover TypeSafe. Without approval, continue the existing assessment and say
approval was absent, not that no useful opportunity existed. Automatic trial
launching never overrides this separate boundary.

## Prepare a bounded request

Use sanitized observations with stable local IDs, not raw conversations, full
traces, secrets, or private case notes. Generalized frozen goals and criteria
must remain within the approved data scope; sensitive content requires specific
approval or a safe fixture. Do not revise frozen inputs after seeing judgments.
Create scratch input/output outside the project and trial copies: directory
mode `0700`, files mode `0600` before writing. Remove scratch files when finished;
never commit payloads, credentials, or outputs, or create a persistent cache.

Use the documented [HTTP question shapes](https://docs.typesafe.ai/api/system-one):
Choice for classification/criterion support, Score for relevance ranking, Noul
for a hypothesis's probability. Give each question complete instructions; IDs
are association keys, not instructions. Include insufficient-evidence outcomes
where relevant. Keep reached/missed/unknown separate from criterion support.

One frozen state, all useful independent questions: one `judge` operation.
For example, this synthetic packet asks two independent questions together:

```json
{
  "operation": "judge",
  "state": {"observation_id": "check-a", "check_exit": 1},
  "questions": {
    "criterion": {
      "type": "choice",
      "instructions": "Does the recorded check support successful execution?",
      "criteria": {
        "supports": "Successful execution is recorded",
        "contradicts": "Failure is recorded",
        "insufficient": "Execution outcome is missing"
      }
    },
    "hypothesis": {
      "type": "noul",
      "instructions": "Does the observation support the hypothesis that execution failed?"
    }
  }
}
```

Multiple candidates/states under shared questions: one `judge_batch` operation,
replacing `state` with a nonempty keyed `states` object. For ranking, use a shared
Score rubric (ordered descriptive `criteria` array) for all candidates. The
helper sends one POST per state, at most four concurrently, returning results by
original state key. It does not claim an HTTP multi-state batch endpoint. Never
fan out per question or repeat judgments of the same frozen input.

## Execute and handle the result

On both hosts use their shell tool with the same bundled Python helper:

```text
python3 <behavior-diff-skill-base>/scripts/jev.py <private-request.json>
```

The helper uses only Python's standard library. It reads `TYPESAFE_API_KEY`, trims
surrounding whitespace and rejects internal whitespace/control/non-ASCII bytes.
`TYPESAFE_DEFAULT_MODEL` defaults to `jev-latest` and must name a `jev-` model.
Only `https://api.typesafe.ai/v1/systemone` is supported. A set
`TYPESAFE_BASE_URL` other than exactly `https://api.typesafe.ai` safely skips;
there is no custom-endpoint support, proxy routing, redirect, automatic retry,
or alternate model/provider. Each request has a 30-second transport timeout.
Input and response bodies are bounded to 256 KiB each.

Read the JSON status, not just the exit code:

- `ok`: validated typed `answers`, actual returned `model`, and token `usage`.
- `unconfigured`: missing/blank key; no request, no answers, exit zero.
- `unavailable`: invalid configuration; no request, no answers, exit zero.
- `failed`: invalid input/provider response or transport/HTTP failure; exit one.
  Reasons are sanitized categories, never raw provider errors or payloads.

Batch output has `results` keyed by original state ID. A failed item has no
answers; successful siblings remain usable. The batch exits nonzero if any item
fails. Handle nonzero as optional assistance failure, not comparison failure:
continue the existing evidence assessment. Do not retry without a new authorized
attempt or switch providers. Keep partial and skipped results visible.

If an orchestration host exposes native `judge`/`judge_batch`, use it only when
its actual binding proves Jev identity and excludes non-Jev fallback. OMP Eval
availability alone does not establish that; use this helper otherwise. Neither
Claude Code nor Codex is assumed to provide Eval. Trial-host adapters stay unchanged.

## Check and disclose

Judgments are evidence, not proof or permission. Check important conclusions
against tests, recorded observations, or primary sources. Keep disagreement and
the stronger evidence visible. Ranking orders inspection; it never drops minority
or contradictory evidence. Do not change frozen goals, cases, memberships,
extracted decisions, or saved reports to fit a judgment. Confidence is uncertainty,
not an acceptance threshold. Approval-bound actions stay unauthorized without the
user's approval, even if every judgment favors them.

Add one ordinary sentence to the final response, not a report panel:

- Useful: “Jev ranked the evidence and flagged a possible contradiction; the
  recorded command confirmed it, so I treated that criterion as unmet.”
- No useful opportunity: “Jev was not used: the remaining checks were deterministic.”
- Other skip/failure: name the actual configuration, approval, or provider reason
  and say the existing evidence assessment was used.

Name corroboration honestly when Jev confirmed rather than changed a decision.
Never imply that an unperformed or failed evaluation succeeded.
