# Reviewer guidelines

Use this policy for each independent review of a plan, design, implementation,
test, document, or pull request in this repository.

A reviewer evaluates correctness, safety, and necessity. A review does not
authorize new product or maintenance scope. The review is read-only.

This guide adapts the reviewer policy from the private Engram repository.

## Review authority

Read these sources before a review:

1. The user request and explicit user decisions.
2. The accepted specification, plan, or acceptance criteria.
3. The complete artifact, including relevant untracked files.
4. [AGENTS.md](AGENTS.md), [CODING_GUIDELINES.md](CODING_GUIDELINES.md), and
   applicable local contracts.

The latest explicit user decision overrides an older request, specification,
or plan. Repository invariants remain active unless the current task changes
them explicitly.

A material finding must map to one of these authorities:

- an explicit user requirement or decision;
- an accepted specification or acceptance criterion;
- a repository invariant or documented standard;
- a demonstrated risk in supported behavior.

For a demonstrated risk, give a reachable trigger and concrete impact. Common
practice, personal preference, theoretical completeness, or a request for more
coverage is not authority.

## Material findings

For each material finding, state:

- severity and exact file, line, or section;
- governing requirement;
- evidence and reachable trigger;
- observable failure;
- least-cost remedy.

If evidence is missing or a risk is hypothetical, put the item under
`OPTIONAL SUGGESTIONS`. It cannot block approval.

Use `REVISE` only for a demonstrated violation of existing authority.

## Scope decisions

Treat these items as scope expansions:

- permanent infrastructure or test mechanisms;
- new dependencies, platforms, versions, or CI gates;
- persistent catalogs, generated artifacts, or recurring workflows;
- new supported behavior or maintenance obligations.

If the artifact does not contain authority for an expansion, report a material
scope finding. Use removal as the least-cost remedy.

If work depends on an unresolved scope choice, put it under
`DECISIONS REQUIRED`. State the risk, alternatives, initial cost, recurring
cost, and the decision that the user must make.

A reviewer recommendation is input to the decision. It is not approval.

## Review priorities

Review in this order:

1. Privacy leaks or consent violations.
2. Regressions to `AGENTS.md` invariants.
3. Unsafe writes, path handling, or fail-open behavior.
4. Violations of the user request or accepted specification.
5. Contradictory or ambiguous agent instructions.
6. Claude Code and Codex incompatibility.
7. Missing regression evidence.
8. Readability and style.

For a prose defect, quote the exact sentence and state the behavior that an
agent can derive from it. For a code defect, state the triggering input or
state and the observable failure.

## Review output

Use this structure:

```text
VERDICT: APPROVE | REVISE | NEEDS DECISION

MATERIAL FINDINGS
- severity, location, authority, evidence, observable failure, least-cost remedy

DECISIONS REQUIRED
- decision, risk, alternatives, initial cost, recurring cost

OPTIONAL SUGGESTIONS
- benefit, cost, and why the suggestion is not blocking

SCOPE AUDIT
- permanent mechanisms added
- permanent mechanisms removed
- unauthorized decisions found
```

Write `none` under an empty section.

- Use `REVISE` if a material finding remains.
- Use `NEEDS DECISION` if no material finding remains but an authorized scope
  choice is unresolved.
- Otherwise, use `APPROVE`.

Reviewer findings are inputs. The primary agent must check each finding against
its authority. A finding does not become a requirement by itself.
