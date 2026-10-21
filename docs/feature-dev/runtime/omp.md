---
commissioned-by: spacedock@0.27.3
---

# omp execution requirements

This document defines the required compatibility check, not a replacement for
Spacedock's shipped first-officer adapter. Read it before dispatch in omp.

## Current support boundary

Spacedock 0.27.3 dispatch accepts `claude`, `codex`, or `pi`; it has no `omp` host.
The shell can inherit `CLAUDECODE=1` while the agent exposes omp-native tools.
The shipped Claude adapter expects Agent/SendMessage; the Pi adapter describes
subagent/intercom. Neither name alone proves those tools exist in omp.

Do not change environment variables to pretend a host is supported. Do not invent
`--host omp`, a launcher, or a transport mapping. README prose cannot change the
plugin's adapter selection. Proper adapter changes belong in Spacedock separately.

## Required capability mapping

Check the current tool schemas, not stale session history or CLI detection alone.

| Operation | Required omp behavior |
| --- | --- |
| Stage spawn | Native `task` with an available ensign; preserve the generated assignment, identity, stage checklist, and worktree |
| Independent review | Separate read-only reviewer with exact candidate revision, complete scope, requirements, and verification evidence |
| Correction authorization | Address the recorded worker with `write agent://id`; preserve the explicit fix/decline/hold/decision package |
| Completion | Consume automatic completion delivery; use `wait` only when otherwise blocked, never polling as proof |
| Isolation | Operate on the assigned branch/path; no second automatic isolation or unapproved patch application |
| Judgment | Available typed judge helper with relevant evidence and uncertainty; no transfer of Captain authority |
| Resume | Reload durable state and approvals; verify or replace worker identities rather than assuming handles survive |
| Shutdown | Use only documented current-host lifecycle operations and preserve required evidence before cleanup |

Children do not inherit the conversation. Supply the accepted task, repository
rules, exact paths, revision, and authorizations. Do not replace a generated
Spacedock assignment with an abbreviated home-grown task.

## Disposable verification before real dispatch

A compatibility mapping must be supported by the installed adapter and exercised
in a disposable synthetic repository before dispatching real feature work:

1. Generate an assignment for the selected supported host without touching this
   workflow's real state or code branch.
2. Spawn through the actual native transport and observe its real completion.
3. Exercise a worker consultation and explicit correction authorization.
4. Verify resulting files and stage report at the assigned path, branch ownership,
   and absence of writes to the parent checkout.
5. Exercise a recorded approval boundary without treating reviewer or Judge
   output as Captain authorization.

If the loaded adapter has no supported mapping, stop before this dispatch; record
that the transport smoke is blocked, not passed. A successful status command,
JSON dispatch build, or Judge call alone does not prove agent lifecycle support.
Do not retry a failed commissioning pilot automatically. Report the exact failure
and current workflow state for the Captain's decision.

## Initial compatibility status

The CLI host schema and native Judge call were exercised during design. No
end-to-end omp dispatch mapping was established. Real feature dispatch is held
until the compatibility check succeeds. This file installs no adapter and makes
no claim of verified omp lifecycle support.
