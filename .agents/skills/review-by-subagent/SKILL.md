---
name: review-by-subagent
description: Runs independent subagent review, fixes material findings, and repeats until approved; records review rounds and later findings on the PR before merge. Use when the user says "review-by-subagent", "review by subagent", asks for subagent review, or provides new dogfood or verification findings after review.
---

# Review by subagent

Treat the request as a review-and-fix workflow, not a report-only review.
Follow repository-root `AGENTS.md`, `CODING_GUIDELINES.md`, and
`REVIEWER_GUIDELINES.md`. The reviewer policy governs finding authority and verdicts;
this skill governs the loop. Keep this maintainer skill outside the plugin payload.

## Scope the review

1. Identify the requested changes or PR from the conversation and repository tools.
   For a named PR, read its description, base/head SHAs, commits, and changed files.
   For local changes, include relevant staged, unstaged, and untracked files, using
   the user's specified base or HEAD for uncommitted work. Inspect branch commits
   when the request concerns a branch. Ask only if materially different scopes
   remain plausible; do not ask for a base already established by the PR.
2. Record the scope, exact revisions or local snapshot, user requirements, and
   applicable specification. Exclude unrelated work. For PR work, verify the local
   checkout represents the PR head before editing; preserve unrelated local changes.
   Never reset, discard, force-push, or absorb someone else's work to make it match.
3. Give reviewers the requirements, diff command/revisions, changed-file list,
   relevant untracked files, standards, and available verification evidence.
   Include unresolved findings and their disposition in subsequent rounds.

## Review, fix, and repeat

4. Launch an independent read-only subagent with the review role when available.
   For substantial changes, use separate Standards and Spec reviewers in parallel.
   Give each a bounded review brief and require the full output structure from
   `REVIEWER_GUIDELINES.md`: verdict, material findings, decisions required,
   optional suggestions, and scope audit. Require concrete locations, authority,
   reachable triggers, consequences, and remedies. Reviewers must not edit files
   or run builds, tests, formatters, or live model journeys; the primary agent owns
   verification. A tool failure or incomplete reviewer response is not approval.
5. Read every result. For a PR, append the round's results as described below.
   If any reviewer returns `REVISE`, inspect the cited evidence and fix all material
   findings within the authorized scope without waiting for another user prompt.
   Reviewer suggestions alone do not authorize new features or mechanisms. If a
   finding is unsupported, explain the evidence to the reviewer and request a
   corrected verdict; never silently override `REVISE` or treat disagreement as
   approval. Handle `NEEDS DECISION` by asking for the specific unresolved choice.
6. Verify the fixes using relevant deterministic checks and an actual smoke run
   where required. Add regression coverage for observable bugs when practical.
   Preserve privacy, evidence semantics, host parity, and live-cost approval rules.
   Keep corrections local until their independent review is approved. For PR
   fixes, any local commits must include only scoped changes and a DCO sign-off.
7. Dispatch another independent read-only review of the updated complete scope,
   not just a verbal claim that fixes were made. Include the prior findings,
   corrective diff, new revision/snapshot, and verification results. A reviewer
   may be reused with this updated context, but must examine the correction.
   Repeat steps 5–7 until every required reviewer explicitly returns `APPROVE`
   for the same latest revision/snapshot and required verification passes.
   Do not stop after the first review, first fix, or an arbitrary number of rounds.
8. After approval, confirm the remote PR head has not changed since scoping.
   If it changed, reconcile safely and review the updated complete scope again.
   Commit approved scoped fixes with DCO sign-off if needed, push normally, and
   confirm the published head matches the approved local snapshot. Record that
   head in a final PR comment. Do not create or merge a PR unless requested.
   Local-only reviews require no commit or push.
   If tools, access, required checks, publication, or a user decision block progress,
   report the exact blocker and pending findings, not approval or completion.
   Never repeat unchanged work without new evidence.

## Findings after approval

When new dogfood or verification evidence arrives after approval, assess it before
claiming the review is complete or carrying out a requested merge. Do not rerun
models automatically; existing consent and cost limits still apply.

Append a follow-up PR comment even if the code has not changed. Identify the
reviewed head/base, the tested revision or local snapshot, the new observation,
its evidence limits, and whether it affects the reviewed change. Distinguish
observed behavior from an inferred cause; do not attribute evidence from another
revision to the PR head without checking its relevance.

| Finding | Disposition |
|---|---|
| Confirmed defect introduced by the PR | Fix, verify, and repeat the existing independent review loop before merge. |
| Pre-existing defect | Record why it is pre-existing and whether it is addressed in scope or deferred; do not expand scope silently. |
| Model error with uncertain cause | Record the observation and uncertainty without claiming the PR caused it or dismissing it as harmless. |
| Known limitation | State what remains unverified and record the user's decision to proceed or investigate. |

Apply `REVIEWER_GUIDELINES.md` to materiality; an uncertain observation does not
automatically invalidate approval. If evidence undermines the approval, return it
to the reviewer with the full scope. Keep material findings in the fix-and-review
loop; ask for a decision when proceeding with an unresolved risk or limitation.
A merge request made before disclosure is not acceptance of a later finding.

Before merge, check that every new finding has a disposition in the PR, required
fixes are verified and independently approved, and any required user decision is
recorded. Report missing gates rather than merging. Preserve earlier comments;
append corrections and follow-up commits instead of rewriting the review history.
For local-only work, record the same information in chat.

Example: a late trial changes "before fixing" to "before proposing a fix."
Record that timing difference, assess its relevance to the reviewed change, and
record the disposition. Do not leave the PR with only the earlier green review.

## PR comments

Append a new comment for each completed review round, including `REVISE` rounds;
retain earlier comments as history. For local-only reviews, report in chat instead.
Use `gh pr comment <PR> --body-file <file>` or the repository's GitHub tool.

Each review-round comment must include:
- Reviewed head SHA (and base SHA), round number, and each reviewer's verdict.
  For local corrections, also identify the commit or patch snapshot and mark it
  unpublished until pushed. Posting review comments does not publish code fixes.
- The reviewer's material findings, decisions, optional suggestions, and scope audit,
  quoted or faithfully summarized. Attribute them to independent AI subagents;
  do not impersonate a human approval or claim a GitHub approval was submitted.
- Fix disposition and follow-up commit when available; distinguish pending fixes
  from completed ones. The next round can record fixes to the preceding round.
- Checks actually run by the primary agent, their results, and unverified limits.

For post-approval findings, use the follow-up fields above rather than inventing
a new review round or reviewer verdict. Include the disposition, completed versus
pending actions, and user decision where required.

Check the posting result and retain the comment URL. If it fails, report that
publication is incomplete. Remove private evidence before posting; preserve the
finding with a safe description and state what detail was withheld.

## Completion

Return the final verdict, reviewed revision, resolved findings, verification,
remaining evidence limits, and PR/comment links where applicable. Approval does
not authorize merging. Keep unrequested commits out of local-only reviews.

Example: `review-by-subagent PR #31` means review the PR, post the findings, fix
material issues, verify and re-review locally until approved, then push the
approved fixes. Comment on every round and the final published revision.
It does not mean merge PR #31.
