# Human evaluation protocol

Use this protocol only for an explicitly requested manual evaluation. It tests
how well a person can identify a skill change from generated behavior summaries.
It does not grade the upstream skills or estimate overall model accuracy.

## Session and sampling

The helper always clones `https://github.com/DataRecce/recce-team.git`, pins
`main`, and inspects its reachable nonmerge history. It never runs upstream
scripts, hooks, installers, or GitHub workflows. Each eligible commit must:

- Have one parent and modify exactly one existing `SKILL.md`.
- Have no companion change in that skill's directory.
- Contain a non-whitespace change in the instruction file.

The sample unit is a commit, not a skill. Five are drawn without replacement
from a freshly seeded random ordering. A repeated skill is allowed and must
be disclosed; do not swap it out to make results look more varied. Changes
outside the selected skill directory are not replayed. The inference scope
is the isolated instruction-file change, not the entire upstream commit.

`session.json` records the source tip, seed, candidates, exclusions, selected
pairs, and local implementation identity. Reports measure the checkout's
current code, including uncommitted changes; the helper captures HEAD plus a
content fingerprint. A frozen session cannot silently use changed inputs.

The default private storage is `~/.behavior-diff/human-evaluations/` with a
unique session directory. Never put it in a working tree, publicly served
folder, or shared/network-synced artifact directory. Do not upload snapshots,
questions, answer keys, reports, or submissions to issue trackers. Track the
method, consent, and aggregate findings instead. The hosted handoff below does
not relax this policy: an explicit publication-policy update and content review
are required before any private material is uploaded. This implementation is
limited to synthetic local emulator use; no deployment or publication is approved.

## Case preparation

Each `case-N/` initially contains `before.md`, `after.md`, and `patch.diff`.
Read the complete affected workflow and directly relevant references at the
pinned parent revision. Do not inspect unrelated private company material.

1. **Check replayability before results exist.** Formatting-only changes,
   inseparable companion changes, or workflows that cannot be represented
   safely with local records may be rejected with a specific reason. Use:

   ```bash
   python3 "$EVAL" replace "$SESSION" --case 1 --reason "Concrete pre-run reason"
   ```

   Replacement uses the next unused member of the original random ordering,
   not a chosen SHA. It is allowed only before freezing and before authored
   case artifacts. A redundant rule, an unchanged result, or poor prose is
   not grounds for rejection. If five eligible cases cannot be prepared,
   report that limitation rather than inventing cases or changing repositories.
2. **Prepare `fixture/`.** Create a synthetic Git repository whose committed
   target is byte-for-byte `before.md`. Use the original relative skill path
   so relative references still work. Add only the synthetic task records and
   necessary pinned reference text. Use a local synthetic Git identity and
   a signed-off fixture commit. Then replace only the target with `after.md`;
   it must be the only uncommitted change. No symlinks, upstream hooks,
   credentials, real issue contents, or source repository `.git` directory.
3. **Write `scenario.json`.** It has `file` (the relative target path) and
   `task` (the exact shared prompt). Explicitly ask the agent to read the
   target skill and local records. Start at the decision point, request its
   decision or draft, and state that commands, external services, edits, and
   posting are unavailable. Do not state the expected answer. Trial tools
   are restricted to Read/Grep/Glob; skill auto-discovery is disabled.
   Also write `purpose.json` beside `scenario.json`, never inside `fixture/`.
   Derive concise distinct goals from the selected commit message and patch,
   not this maintainer session or subsequent commits. Use the canonical
   Behavior Diff contract:

   ```json
   {"goals":[{"text":"Preserve the required source check after removing an example.","source":"commit","basis":"explicit","reference":"Commit selected revision: message"}]}
   ```

   Use `basis:"inferred"` when the goal is an inference rather than an explicit
   message statement. Without a usable commit reason, use `source:"diff"` and
   `basis:"inferred"`; use `null` if no safe meaningful goal can be derived.
   Keep separate goals separate (at most eight, text <=1,200 characters,
   reference <=240), and use neutral references without private quoted text.
   Exclude secrets, names, emails, private identifiers/URLs, raw messages, and
   unrelated context. Review this derived content too: summarization is not
   guaranteed sanitization. This file is frozen with the other case inputs,
   passed only as `--purpose-file`, and never added to the task or trials.
4. **Write `question.json` before seeing live results.** The shape is:

   ```json
   {
     "stem": "Which statement describes the Before/After contrast in this scenario?",
     "scope": "The decision this scenario can expose; identify the relevant patch section.",
     "options": [
       {"statement": "First candidate contrast.", "correct": true, "rationale": "Before: source support. After: changed rule. Scenario: triggering facts. Contrast: anticipated observable difference and limits."},
       {"statement": "Second candidate statement.", "correct": false, "rationale": "Why the patch contradicts or does not introduce it."},
       {"statement": "Third candidate statement.", "correct": false, "rationale": "Why this is false for the selected change."},
       {"statement": "Fourth candidate statement.", "correct": false, "rationale": "Why this is false for the selected change."}
     ]
   }
   ```

   This is a schema example, not ready-to-use question content. Author four
   concrete, similarly specific statements with exactly one patch-grounded
   contrast that the scenario can expose. The keyed statement must distinguish
   anticipated After behavior from Before; a statement true of both sides is
   not a discriminating answer, even if it accurately describes After.
   Avoid bundled claims outside the scenario, trivia, obvious nonsense,
   uniquely repeated keywords, or an answer longer than all the distractors.
   A clarification-only change can target a stated reason, condition, or timing;
   do not claim it changes the action or outcome. Check each rationale against
   both complete source sides and the patch, independently of the report.
5. **Complete the prefreeze contrast audit.** Before authorizing `freeze`,
   record these four checks in the keyed option's existing `rationale`:

   - **Before:** cite the relevant source section and say whether the keyed
     behavior is already required, permitted, or illustrated there. Check
     surrounding rules and relevant references, not only removed patch lines.
   - **After:** cite the changed rule and identify the precise added or changed
     condition, timing, next step, or explanation. Separate explicit wording
     from an inference about how a trial might respond.
   - **Scenario:** identify the local facts and decision point that activate
     that rule. State what the read-only task can and cannot demonstrate.
   - **Contrast:** state what observable Before/After difference would support
     the keyed statement and what would instead make it an unchanged or
     both-sides match. A difference must concern the whole statement, not merely
     a keyword appearing in After.

   Have the maintainer review all four checks before freezing all five cases.
   Revise an unsupported or both-sides statement, or its scenario, only during
   preparation, without seeing live results. Do not replace a sampled commit
   because its rule is redundant or its expected contrast is weak. If no
   defensible contrast can be authored, report the design limitation before
   live execution rather than inventing a difference.
6. **Freeze all cases.** `freeze` validates input structure, shuffles options,
   writes the private answer key and public questions, and records input hashes.
   The existing schema is unchanged: `scope` bounds the claim and the keyed
   `rationale` holds the audit. The deterministic helper enforces structure and
   immutability, **not semantic contrast**; a successful freeze does not prove
   that the question discriminates. The audit is a required maintainer gate.
   After freezing, do not edit fixtures, questions, or the key. Start a new
   evaluation if the design must change; retain the abandoned session and why.
   Once results exist, a weak or absent contrast is evidence, never grounds to
   reject, resample, retry, or change the keyed answer.

Scenario design is model-assisted maintainer work, not a claim that the installed
Behavior Diff plugin independently drafted the scenario. When delegating, keep
scenario workers separate from the quiz options and final answer key.

## Consent and live execution

Request fresh approval for 30 Claude Code trial executions plus five extraction
calls and any additional model-assisted preparation. Explain that private skill
text, reviewed derived purpose, and bounded recorded read/search tool returns
go to the configured provider; purpose and evidence excerpts may appear in local
reports. Conservative exclusions cannot detect all private prose or secrets.
If safe generalization loses an essential purpose or source fact, obtain
specific approval for that content or use a safe fixture before execution.
Record the approval in the tracking issue; never assume a previous session's
approval applies. `--approve-live` is the operator's attestation of that approval,
not a substitute for asking.

The helper launches the unchanged local `behavior-diff.sh`, selecting Claude
`opus` for trials and Claude `sonnet` for extraction. A local wrapper disables
user customizations, hooks, MCP, commands, writes, and network tools. This is a
read-only decision/output replay, not a production integration test. Either
Claude Code or Codex can orchestrate this skill, but this workflow intentionally
uses the same Claude trial stack; do not silently substitute another host.

Run all cases sequentially with `run SESSION --approve-live`, or dispatch
separate cases with `--case N` after freezing. Each case has its own output root.
The normal runner executes six trial processes per case. Do not launch many
cases concurrently without considering the provider's rate limits.

The runner's automatic opening of the full report is suppressed until the
human submits the quiz; use only the quiz URL before submission.

An attempt is recorded before launching. Do not rerun until a favorable result
appears. Preserve failures and missing extraction. If the runner cannot produce
a report, report the incomplete case and its saved diagnostics; do not substitute
a synthetic report or another commit. Never invoke a live runner from CI.

Check `runner.log`, run evidence, and the original trial traces. Verify exact
Before/After target bytes, nonempty results, target reads, actual model identity
where retained, and tool restrictions. A REVIEW grade is neutral, not a failure.
Do not represent an answer describing an action as evidence of execution.

## Quiz and scoring

`build` creates blinded excerpts from the original saved report HTML. It retains
the generated headline, evidence, Before/After cards, meaning, Other findings,
and limits. It removes instruction intent/diff, full scenario/expected behavior,
commit metadata, and links to unblinded evidence. It must not rewrite report
prose or synthesize missing summaries. The projection fails if the report shape
is no longer recognized; update it deliberately alongside a report redesign.

`serve SESSION --port 0` prints an available loopback URL. Only public quiz assets
are served before submission. The answer key stays on the server. Check desktop
and narrow browser views, including expanded findings, without answering the
human's quiz. Test submissions belong in a separate synthetic session.

The human chooses one of four options, supplies confidence, and can flag
insufficient evidence or add a note. The first complete submission is saved;
refreshing or submitting again does not replace it. Correct answers, rationales,
source commit links, and the full reports become available afterward. Keep the
service running until the human finishes; restart `serve` to resume later.

`results SESSION` reads the saved submission without a model call. Report the
original score out of five, confidence, insufficient-evidence count, and comments.
Then complete the question-validity assessment below for all cases, not just
misses. Do not infer comprehension from keyword matching or score alone. Preserve
the first submission and score; do not rescore after changing a question,
excluding weak cases, or revealing the answers. These instructions apply when
analyzing older sessions too; never retrofit their questions or frozen rationales.

## Hosted package v1

`export-package` and `hosted-results` are local, deterministic commands. They
never run models, contact Firebase, or publish content. The loopback `build`,
`serve`, and `results` workflow remains supported unchanged. Exporting a blinded
projection does not establish that it is safe or approved to publish. Before any
real upload, obtain an explicit publication-policy update, review the actual
outgoing summaries/questions/answer mapping/metadata, and verify hosting access,
purpose/access notice, and retention/deletion policy. A private site repository,
closed quiz, anonymous authentication, or typed team email is not access approval.

### Export saved evidence

```bash
python3 "$EVAL" export-package "$SESSION" \
  --evaluation-id reviewed-cohort --title "Reviewed evaluation" \
  --out "$PRIVATE_EXTERNAL_ROOT/quiz-package"
```

The session must already be frozen and built. The CLI checks the original frozen
inputs, saved answer-key identity, full report digests, and public build receipts.
It also verifies that the saved summaries are the original blinded projections;
it copies their exact UTF-8 bytes, not new prose, regenerated styles, or full
report pages. It retains the frozen A–D option order. Missing extraction remains
missing; export does not authorize retrying, replacing, rebuilding, or hiding cases.

The destination must not exist. Its parent must already exist, have no symlink
components, and be outside both `behavior-diff` and `behavior-diff-evaluation`
working trees. The package must also be separate from the private session.
Files are exclusively created with mode 0600 inside mode-0700 directories.
An existing destination or a previously exported evaluation ID in this session
is rejected rather than overwritten. The private mapping lives at
`SESSION/hosted-exports/EVALUATION_ID.json`; it records the package hash, manifest,
original session and source-case mapping, and answer-key/build digests. Never ship
that file. The package contains only:

```text
quiz-package/
  manifest.json
  questions.json
  summaries/
    case-1.html
    case-2.html
    case-3.html
    case-4.html
    case-5.html
```

The exporter owns this v1 contract; the site's importer validates it independently.
Both reject symlinks and unexpected entries. No source paths, commits, rationales,
patches, traces, full reports, source URLs, or respondent data enter the manifest
or questions. Saved summary wording is not rewritten or redacted automatically;
the publication review must inspect it for sensitive material.

- `manifest.json` has exactly `schemaVersion` (integer 1), `evaluationId`, `title`,
  `caseIds`, `producerVersion`, and `files`. The ID matches
  `[a-z0-9][a-z0-9-]{0,63}`. Title is nonblank and at most 200 characters; producer
  version is nonblank and at most 120. `caseIds` is ordered `case-1` through
  `case-5`, mapped from the frozen numeric IDs 1–5.
- `questions.json` is an array in that same order. Each entry has exactly
  `{id, stem, options, correctOption}`. Options are exactly four ordered
  `{id, text}` entries with IDs `A`, `B`, `C`, `D`; `correctOption` is one of those.
  Stem and option text are nonblank strings of at most 2000 characters.
- `files` maps exactly `questions.json` and the five summary paths to lowercase
  SHA-256 digests. Question JSON is hashed semantically: UTF-8 JSON with object
  keys recursively sorted lexicographically, no whitespace or trailing newline,
  unescaped Unicode, and integer numeric values. Arrays retain order. Summary
  hashes cover raw UTF-8 bytes. `contentHash` is SHA-256 of the canonical manifest;
  it is returned by the command and recorded privately, not an extra manifest key.
  JSON files may have different insignificant whitespace.
- Limits are 256 KiB per summary, 64 KiB questions, 16 KiB manifest, and 2 MiB
  total package bytes. Reject rather than truncate. The site's importer also
  parses a strict HTML/CSS allowlist compatible with `quiz.py` projections,
  rejecting resources, scripts, events, URLs, escaped CSS, and executable markup.
  Hash agreement is not a safety check. The frontend uses non-scriptable sandboxed
  summary iframes with a restrictive content security policy.

The minimal correct-option mapping is intentionally shipped for frontend scoring.
Participants can inspect it; this is accepted trust-based scoring, not enforced
blinding. Local mode still keeps its answer key server-side until submission.
The site owns immutable closed import, inspection, open/deadline, close, and private
response export; this skill owns no credentials or Firebase deployment tooling.
Content changes require a new evaluation ID and the existing fresh-evaluation
protocol, never an in-place key/summary correction or retrospective rescore.

### Analyze hosted responses

After closing collection, the site's maintainer command exports a private file.
Keep it outside both working trees and follow the launch retention/deletion policy.
Pass the original exported package and private session to:

```bash
python3 "$EVAL" hosted-results "$SESSION" \
  --package "$PRIVATE_EXTERNAL_ROOT/quiz-package" \
  --responses "$PRIVATE_EXTERNAL_ROOT/responses.json"
```

The site export has exactly `{schemaVersion, evaluationId, contentHash, manifest,
exportedAt, responses}`; version is integer 1 and timestamps include a timezone.
Each response is exactly `{uid, submission, recomputedScore}`. Submission fields
are exactly `schemaVersion`, `evaluationId`, `respondent`, `contentHash`,
`siteBuild`, `answers`, `confidence`, `insufficientEvidence`, `notes`,
`clientScore`, and `submittedAt`. Every answer/confidence/flag/note map contains
all five stable case IDs. Answer values are A–D, confidence is low/medium/high,
flags are booleans, notes are strings up to 2000 characters, and scores are
integers 0–5. Respondent is trimmed, nonblank, at most 200 characters; site build
is nonblank and at most 120. The timestamp is the saved server time in ISO format.

The analyzer verifies frozen session inputs, the original saved build, exact
package allowlist and content, the local provenance receipt, and export/submission
version/hash identity. It rejects malformed records or duplicate UIDs instead of
silently dropping them. It recomputes every keyed score from the frozen key using
the local scoring path, trusting neither `clientScore` nor exported
`recomputedScore`; discrepancies are reported alongside the unchanged originals.
It never writes a local submission or modifies response, package, or session files.
Output is private JSON on stdout; diagnostics go to stderr with exit status 2.

Preserve every UID and its `siteBuild`, notes, confidence, and evidence flags.
Matching trimmed, case-folded respondent names are advisory only: do not merge,
remove, or assume independent participants. The output lists all five cases as
`not-assessed`, with private evidence/summary locations. Complete the following
semantic validity assessment for **all cases**, including correct responses.
Keep its observations and counts separate from original keyed scores; never change
the key, omit weak cases, publish a revised denominator, or pool changed cohorts
silently. No submissions means zero responses, not an invented score.

### Synthetic compatibility fixture

The deterministic hosted test file reuses the existing authored report gallery
and synthetic Git history. To create a persistent package through the production
export command, use a fresh external directory (no real sessions or trials):

```bash
python3 tests/human-evaluation-hosted-test.py \
  --export-synthetic "$PRIVATE_EXTERNAL_ROOT/fresh-synthetic-fixture"
```

The argument must not exist. It creates `session/` and `package/`, prints the
production export result, and grants no publication permission. Import only its
synthetic package into the site's loopback demo emulators for compatibility smoke.
Run `python3 tests/human-evaluation-hosted-test.py` for deterministic contracts.

## Question validity assessment

After submission, use only saved evidence. For every case, compare the frozen
keyed statement and rationale with both complete source sides, the patch,
scenario, original Before/After trial answers, and the blinded summaries that
the human saw. Record the assessment in private analysis notes alongside the
session, without editing hashed inputs, reports, the answer key, or submission.
No new model run is needed or authorized by this assessment.

Separate two judgments:

1. **Observed contrast:** does the whole keyed statement distinguish After from
   Before in the saved answers?
   - **Observed delta:** the answers support the stated Before/After distinction.
     Name the changed condition, timing, next step, or explanation and any trial
     variability; do not turn a partial pattern into a universal claim.
   - **Unchanged / both-sides match:** the keyed behavior is present on both
     sides, or the scoped behavior is unchanged. Explicitly label the question
     **non-discriminating in this run**, even if the key is source-supported or
     the human selected it correctly.
   - **Not observed / contradicted:** usable answers do not show the forecast
     contrast or instead show a different direction. Preserve that result.
   - **Inconclusive:** missing, blocked, or inconsistent evidence prevents a
     supported distinction. Name the missing evidence; do not infer a delta.
2. **Summary exposure:** do the blinded summaries faithfully expose the supported
   distinction? Separate omitted operative rules or timing from factual errors,
   scenario undercoverage, and question ambiguity. A delta visible only in full
   traces does not prove the human could infer it from the quiz excerpt.

Cite private evidence locations and describe what each side actually says.
Assess correctly answered cases as well as misses. Retain the raw keyed score
out of five and qualify non-discriminating, unobserved, or inconclusive cases in
the analysis. Do not count an unchanged match as evidence of successful delta
comprehension, or its missed key as evidence of poor comprehension. Report
validity counts separately from the score; do not publish a revised denominator
or retroactively choose a different correct option.

### Synthetic table-and-wait example

Suppose Before already documents a blast-radius table, and After adds a rule to
disclose that table before applying a change. In saved trials, both responses
show the table, but only After explicitly says it will wait before proceeding.
The keyed statement “After shows a blast-radius table” is a both-sides match,
not an observed delta. Preserve its original score and mark it non-discriminating.
The supported observed contrast is the stated wait/next-step difference, not
the presence of the table. A future question can target that timing distinction
only if its source-and-scenario audit supports it, and must be frozen before
its own trials; do not rewrite this session's key using the example.

Keep source intent separate from observed behavior: a disclosure-before-action
rule does **not** by itself require literal user approval. If After says it
will wait for approval, report that as observed response wording, not as an
explicit source requirement unless the source actually contains that requirement.
A stated wait is not evidence that any command executed or approval was obtained.

A random guess averages 1.25/5. Five possibly correlated cases cannot establish
product-wide accuracy. Separate summary readability/fidelity from scenario
coverage and quiz ambiguity. An absence of observable difference is useful
evidence. Later wording comparisons need fresh cases or an independent reader
because this human now knows these answers.
