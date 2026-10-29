# Optional saved-evidence replay helper

Use this for an explicit fixed-evidence replay or a saved-evidence subset of
Behavior Rehearsal. It does not run Behavior Diff, authorize work, or measure owner effort.
Its `mode` describes fixed evidence only; do not present it as the status of a
fresh comparison. Keep fresh-run receipts and conclusions in that run's artifacts.

Prepare the packet yourself from permitted local sources, retaining coordinates,
provenance and limits. Distinguish saved authors' interpretations from inspected
actions, returns and artifacts. Never substitute invented evidence for missing
real evidence. `../fixtures/synthetic.json` is an explicitly invented demo.

Create a private directory outside all Git trees (0700); snapshots are 0600.
Keep packets outside tracked trees too. Resolve the helper from the loaded skill
base, including when invoked in another repository:

```sh
python3 "$SKILL_BASE/scripts/replay.py" \
  --state "$PRIVATE/session.json" --root "$CASE_ROOT" <<'JSON'
{"action":"init","goals":[{"id":"review","text":"Stop for human review.","basis":"inferred","reference":"Supplied change","next":"Inspect the final stop and adoption actions."}]}
JSON
```

One JSON action on stdin per invocation, one JSON result on stdout; errors go to
stderr with exit 1. Every action except `init` and read-only `show` requires
`revision`. Recover it with `show`; stale requests fail rather than silently rebase.

- `init`: `goals`, each with `id`, `text`, `basis` (`explicit`/`inferred`),
  `reference` and concrete next verification step in `next`.
- `correct`: `id`, exact `text`; `replace`: complete `goals`, clears all support.
- `bind`: `id`, `status` (`supported`/`contradicted`), `origin`
  (`reused`/`synthetic`), nonblank `reason`, `scope`, and `citations` list of
  `{path,start,end}`. Paths are case-root-relative; inclusive ranges max 120 lines.
- `confirm`, then `result`: no extra fields. Confirm only after actual owner
  confirmation of these goals. Missing or changed citations become gaps.
- `evidence`: `citation`; prints numbered source lines without execution.
- `decide`: `choice` (`accept`/`revise`/`request-verification`); requires the current
  result. This records a choice only; it never authorizes adoption or execution.

Apply exact owner corrections and reassess affected bindings. A correction clears
that goal's support, confirmation and prior decision; unchanged goals retain their
support. Do not carry evidence across changed requirements based on matching words.
Keep helper mechanics out of owner questions. Its success cannot establish source
correctness, fresh-run completion, or reduced owner coordination.
