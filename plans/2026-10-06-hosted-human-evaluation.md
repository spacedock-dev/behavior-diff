# Hosted human evaluation

**Recorded:** 2026-10-06

**Status:** Firebase direction approved for planning. Participants provide a name or
email with their answers. No implementation, deployment, or publication performed.

## Decision

Use a static evaluation frontend, Firebase Anonymous Authentication, and Cloud
Firestore. Calculate the score in the frontend and collect submissions directly in
Firestore. Replace the earlier custom Python/SQLite, Formspree, and GitHub Issues
proposals; none is part of this design.

```text
Local evaluation skill
  Prepare -> freeze -> trials -> reports -> reviewed quiz package
                                      |
Private site repo: local maintainer import command
                                      |
                                      v
Firestore: frozen quiz content + availability metadata
                                      |
                                      v
Static frontend loads quiz; anonymous session established automatically
  Read -> answer -> enter name or email -> Submit
                                      |
                                      v
Firestore: validate rules -> create private submission -> acknowledge
                                      |
                                      v
Frontend shows score and confirmation

Maintainer: Firebase Console / local export -> scoring and validity analysis
```

No personal token, registration form, GitHub issue confirmation, custom backend service,
or Cloud Function is needed. Firebase is the managed submission backend.

## Participant experience

1. Open the evaluation page. Firebase establishes an anonymous session automatically;
   no authentication details are requested from the participant.
2. Read the five blinded summaries and select answers, confidence, and any
   insufficient-evidence flags or notes.
3. Enter one required **Name or email** field. Do not require both. Explain that it
   identifies the response to the evaluation maintainers and is not shown publicly.
4. Click **Submit**. Preserve answers on failure and allow retry.
5. Show the calculated score and confirmation only after Firestore acknowledges the
   saved response. An offline/local pending write is not confirmation of receipt.

Do not use the contact field to create an account or send email. Contact for another
purpose needs separate consent. A name/email is self-reported, not verified identity
or proof of team membership. Do not silently collect an additional device fingerprint.

## Minimal data model

```text
evaluations/{version}
  schemaVersion
  contentHash
  caseIds
  title
  open
  closesAt

evaluations/{version}/cases/{caseId}
  stem
  options
  correctOption
  summaryHtml            approved, sanitized blinded excerpt

evaluations/{version}/submissions/{anonymousUserId}
  respondent             one bounded name-or-email string
  contentHash
  siteBuild
  answers                five option selections with stable question IDs
  confidence
  insufficientEvidence
  notes
  clientScore
  submittedAt            server timestamp
```

An immutable evaluation version identifies the questions, option order, displayed
summaries, and scoring key. Changed content requires a new version. Keep the existing
frozen option order initially.

Use the anonymous Firebase UID as the submission document ID, not a name or email.
One document per UID/version prevents overwriting a saved response for that session.
Clearing browser state can create another UID; this is not one-person/one-response
enforcement. Do not merge responses solely because their names or emails match.

Allow a participant to retrieve their own submission to recover from refresh or a
lost acknowledgement. If a retry finds an existing response, show the saved receipt
rather than replacing it. Preserve original records during analysis.

## Security Rules and abuse boundaries

Rules must deny access by default and explicitly allow:

- Reading approved quiz metadata and case documents, including the minimal
  correct-option mapping accepted for frontend scoring.
- Creating a submission only at the authenticated user's UID for an existing, open
  evaluation before its deadline.
- Only the expected fields and bounded, correctly typed values, including all five
  distinct question answers and a nonempty bounded respondent field.
- Reading one's own submission, but not listing or reading other people's responses.
- No participant updates or deletes after creation.

Administrative access is restricted through Firebase/Google Cloud permissions.
Service-account credentials must never enter frontend code. Configure Firebase App
Check to reduce unauthorized-client abuse, and monitor quotas and billing. App Check
and anonymous authentication do not prove team membership or eliminate all abuse.

Do not use permissive test-mode rules in deployment. Verify rules with deterministic
emulator checks, including cross-user access, malformed input, duplicate creation,
closed evaluations, and unauthorized changes to evaluation metadata.

## Scoring and interpretation

The frontend includes the answer key and calculates a score. Participants can inspect
that key through browser tools; this is an accepted trust-based design, not enforced
blinding. Do not describe client-side hiding as an access restriction.

Store the score as `clientScore` and retain the raw answers. Recompute scores locally
against the frozen key rather than trusting browser-provided totals. Keep the original
keyed score separate from all-case question-validity analysis. Do not rewrite keys or
exclude weak questions retroactively to improve results.

Anonymous IDs and self-reported names do not establish independent participants.
Five cases and their respondent scores do not estimate overall product accuracy.

## Repository ownership

The evaluation site lives in the separate private repository
[`DataRecce/behavior-diff-evaluation`](https://github.com/DataRecce/behavior-diff-evaluation).
The local origin now uses `git@github.com:DataRecce/behavior-diff-evaluation.git`.
The destination repository's private visibility was verified on 2026-10-06.

- **This repository:** the canonical evaluation skill, local trial generation,
  blinded-package export, and local analysis. Do not copy the skill into the site repo.
- **Private site repository:** the static frontend, Firebase configuration without
  secrets, Firestore rules, and deployment workflow.
- **Firebase:** published quiz content, availability metadata, submission records,
  and respondent identifiers. Responses are never committed to either repository.

Connect the repositories through a small versioned quiz-package contract. The local
skill exports approved content; a maintainer command in the site repo imports it into
Firestore. The frontend reads that content at runtime without running models or
depending on a checkout of the plugin. Keep each evaluation version immutable.
Review packages before upload; private repository status is not blanket approval to
upload private source evidence or session artifacts. Packages stay outside Git.

The private repository hosts the site's source. Website access control remains a
separate deployment requirement, as described below. The repository exists;
site implementation and publication have not been performed under this plan.

## Updating quizzes across repositories

### Separate website releases from quiz publication

Deploy website code from the private site repo only when UI, Firebase integration,
or rules change. Ordinary quiz updates are Firestore content updates, not Git commits,
Pages deployments, cross-repository workflows, or new application releases.

```text
Behavior Diff repo                         Private site repo
Local skill generates frozen evaluation
         |
Export approved quiz package ------------> Local maintainer import command
                                          Validate + upload closed evaluation
                                                    |
                                                    v
                                               Firestore
                                                    |
                                          Preview on existing website
                                                    |
                                          Open evaluation; share its URL
```

The import command runs on the maintainer's machine using Google administrative
credentials. It is not an API endpoint or a participant tool. Do not embed those
credentials in the package, frontend, or Git history.

### Package contract

Export a small directory outside both working trees:

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

- `manifest.json`: schema version, immutable evaluation ID, title, ordered case IDs,
  producer version, and file digests. Keep private run paths and source provenance
  in a local mapping, not the hosted manifest.
- `questions.json`: stable case/option IDs, stems, option text, and the minimal correct
  option mapping required for accepted frontend scoring. Do not export the original
  answer-key file with its private rationales, source links, or patches.
- Summary files: exact approved blinded projections from the saved reports. No new
  model prose, full report pages, arbitrary scripts, or external resources.

The exporter owns the contract; the site's importer supports explicit contract
versions and rejects unsupported ones. Use small synthetic contract fixtures for
compatibility checks. No shared live repository checkout or copied skill is needed.

The importer validates IDs, exactly five cases, four unique options per case, valid
correct-option references, hashes, file allowlists, and payload sizes. Reject symlinks,
escaping paths, executable markup, and oversize content. Parse summaries using a
strict HTML allowlist and render them in an isolated, non-scriptable surface; do not
treat a hash match as proof that HTML is safe.

Store one case per Firestore document rather than one potentially large report
document. Enforce conservative per-case and total limits before any upload; do not
truncate excerpts to fit. This keeps the first version within Firestore document and
batch limits without adding Cloud Storage.

### Publication steps

Command names here describe proposed interfaces, not existing commands:

1. **Generate locally in the Behavior Diff repo.** Use the existing freeze/run/build
   workflow and its live-cost approval gates. Preserve failed or unchanged cases;
   publication is not permission to rerun until a preferred result appears.
2. **Export and review.** Produce the package from saved evidence. Review the actual
   summaries, questions, frontend answer mapping, and outgoing metadata for publication.
   Record the package hash and its private source-session mapping locally.
3. **Import from the site repo:** `quiz import <package-directory>`.
   Validate everything first. Atomically create the evaluation and five case documents
   with `open=false`. Reject an existing version rather than overwriting it. On an
   uncertain network result, inspect the saved version/hash before attempting recovery.
4. **Preview:** open `/evaluations/<version>/` on the existing site. It shows the real
   content with submissions disabled. A closed quiz is not secret: authorized content
   readers can still fetch it. Review must happen before upload.
5. **Open:** `quiz open <version> --closes-at <time>`.
   Verify stored content against its hash and the frontend contract, then enable
   collection. Share the version-specific URL. The site reads `open` and `closesAt`;
   Security Rules enforce them independently of the browser.
6. **Close and analyze:** `quiz close <version>`, then
   `quiz export-responses <version> --out <private-path>`.
   Close writes through Firestore rules even for already-open tabs. Export responses
   privately and pass them to the local Behavior Diff analysis workflow.

These commands belong to the private site's Firebase administration tooling. The
Behavior Diff skill only needs export instructions and the handoff contract; it does
not acquire deployment credentials or Firebase-specific publishing implementation.

Use a synthetic evaluation in a separate test project to test actual submission.
Do not send scoring smoke-test answers into a real evaluation.

### Content lifecycle and changes

- **New quiz:** publish a new immutable version at a new URL. Multiple versions may
  remain accessible; a landing page may list open versions without a separate catalog.
- **Question, option, key, or summary correction:** close the affected version and
  preserve it and its responses. Never edit content in place or reinterpret existing
  submissions against a new key. Correcting frozen questions must follow the existing
  protocol for a new evaluation; publishing alone does not bypass that requirement.
- **Frontend-only bug fix:** deploy site code separately and record `siteBuild` on
  every response. If the change alters what readers see or how they answer, close
  the current cohort and use a distinct evaluation version; do not silently pool it.
- **Bad publication:** close collection and remove the quiz from open listings.
  Preserve the version for private audit. If sensitive material was exposed, disable
  content access/remove hosted payloads under the incident procedure; closing
  submissions alone does not revoke reads or erase browser caches.
- **Deployment rollback:** restore compatible site code, not an old answer key over
  existing submissions. Unknown package schemas produce an unavailable notice.

Only `open` and `closesAt` are normally mutable for an existing evaluation. Browser
clients cannot modify metadata or cases. Administrative tools must enforce content
immutability too, because administrative credentials bypass client Security Rules.
Submissions carry the evaluation version, content hash, and site build; rules require
the submitted hash to match the registered version. This identifies the stated
content version but is not cryptographic proof of what a participant actually read.

### Access and operational boundaries

Allow anonymous authenticated clients to read only the approved quiz metadata/cases,
and their own submission. Keep case content separate from respondent data so opening
quiz reads never grants collection-wide response access. Minimal correct-option data
is intentionally readable for frontend scoring; private source rationales remain local.

This adds no custom backend, build-time model calls, cross-repo secret sharing, release
asset store, or manual database editing. Firebase handles runtime reads and writes.
Verify quotas and costs, rule behavior, and publication credentials before launch.
Private hosting and strict team-membership limitations in the next section still apply.

## Team privacy and hosting

The first intended audience is the team, but distribution to teammates is not technical
access control. A private GitHub repository does not automatically make GitHub Pages
private. Restricted Pages requires an eligible GitHub Enterprise Cloud project-site
configuration. Verify actual site visibility before publishing any private material.

Anonymous Firebase authentication does not inherit GitHub Pages access permissions.
If strict team-only backend access is required, add a trusted organizational identity
or authorization mechanism; a typed company email is not sufficient. This design
otherwise collects trust-based responses with private storage and abuse protections.

The existing [skill](../.agents/skills/run-behavior-diff-human-evaluation/SKILL.md)
uses private `DataRecce/recce-team` source material. Its
[protocol](../.agents/skills/run-behavior-diff-human-evaluation/references/workflow.md)
currently requires local storage. Hosting requires an explicit publication-policy
update and review of the actual outgoing content; this plan does not approve uploading
existing private sessions. Blinding alone is not sanitization.

Keep raw traces, source snapshots, patches, full reports, and local provenance out of
the published package. Do not commit private reports or submissions to this repository.
Deploy only approved static artifacts; CI must not execute live trials or extraction.

Names/emails and notes are personal data. Show a short purpose/access notice before
submission, restrict maintainer access, and choose a retention/deletion period before
launch. Apply it to local exports as well as Firestore. Anonymous Auth account cleanup
must not be assumed to delete stored submissions. Publish only approved aggregates.

## Implementation scope

1. Add an allowlisted quiz-package export and a site-owned Firestore import/open/close
   workflow. Load quiz content dynamically in the existing frontend.
2. Add automatic anonymous authentication and the Name or email field.
3. Submit directly to Firestore with pending, success, failure, and resume handling.
4. Deploy restrictive Firestore rules and configure App Check and operational limits.
5. Add a local export/import path for multi-respondent validation, score recomputation,
   duplicate assessment, and existing question-validity analysis. Firebase Console is
   sufficient for initial manual inspection; no custom administrator UI is needed.

Retain the current local workflow as a separate supported mode. The existing
[quiz implementation](../.agents/skills/run-behavior-diff-human-evaluation/scripts/quiz.py)
provides reusable projection, validation, and scoring logic; its loopback server is
not part of online collection. Update the skill/protocol and architecture documentation
when the approved hosted behavior is implemented.

## Verification before launch

Use synthetic cases and an isolated Firebase test project:

- Verify exported content, actual hosting visibility, and absence of private artifacts.
- Exercise the real page through automatic authentication, response entry, Firestore
  acknowledgement, score display, refresh, and local analysis of the saved record.
- Test network failure, offline pending writes, lost acknowledgements, retries, and
  submission closure without losing entered answers or falsely confirming receipt.
- Verify cross-user isolation, immutable submissions, field bounds, and server times.
- Demonstrate that changing a client score does not change locally recomputed results.
- Verify the notice, private handling of respondent identifiers, and deletion procedure.

No Firebase project, credentials, deployment, live submissions, or integration tests
have been created for this plan. Provider capabilities were checked in documentation;
the proposed integration remains unimplemented.

## Sources

- [Firebase anonymous authentication](https://firebase.google.com/docs/auth/web/anonymous-auth)
- [Firestore field validation and access rules](https://firebase.google.com/docs/firestore/security/rules-fields)
- [Firebase App Check and its limitations](https://firebase.google.com/docs/app-check)
- [GitHub Pages visibility](https://docs.github.com/en/enterprise-cloud@latest/pages/getting-started-with-github-pages/changing-the-visibility-of-your-github-pages-site)

Documentation checked on 2026-10-06.
