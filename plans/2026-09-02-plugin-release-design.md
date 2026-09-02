# Behavior Diff Plugin Release Design

**Goal:** Publish stable Behavior Diff versions through GitHub Releases and update the Spacedock marketplace automatically to install the released tag.

## Current state

- Behavior Diff has deterministic GitHub Actions CI for pull requests and pushes to `main`.
- The Claude Code and Codex plugin manifests both have version `0.3.2`.
- The repository has no Git tags or GitHub Releases yet.
- The marketplace entry has version `0.3.2`, but its source still follows Behavior Diff `main`.
- Behavior Diff has no Actions secrets.
- Subspace updates the same marketplace with a write-enabled SSH deploy key.

## Release contract

A maintainer publishes a GitHub Release in `spacedock-dev/behavior-diff`.

A stable release must meet every rule below:

- The Release is not a draft or prerelease.
- The tag uses `vX.Y.Z`, with three numeric parts and no suffix.
- The tagged commit is on Behavior Diff `main`.
- `plugin/.claude-plugin/plugin.json` has version `X.Y.Z`.
- `plugin/.codex-plugin/plugin.json` has the same version.
- The repository's deterministic CI passes for the released tag.

Drafts do not produce a `published` event. Prereleases trigger the workflow but skip all release jobs. They never update the stable marketplace entry.

GitHub Releases hosts the tag and its normal source archives. Behavior Diff does not build or upload a separate release asset because the marketplace installs the `plugin/` subdirectory from Git.

## Data flow

```text
Publish stable GitHub Release
          |
          v
Validate tag, main ancestry, manifests, and CI
          |
          v
Clone spacedock-dev/marketplace with a deploy key
          |
          v
Update behavior-diff version and source.ref
          |
          v
Validate JSON, commit with sign-off, push marketplace main
```

The marketplace entry changes as one unit:

```json
{
  "name": "behavior-diff",
  "source": {
    "ref": "vX.Y.Z"
  },
  "version": "X.Y.Z"
}
```

The updater must find exactly one `behavior-diff` entry. It must reject a missing or duplicate entry. Running it again with the same version must leave the file unchanged.

## Repository changes

### Reusable CI

Add `workflow_call` to `.github/workflows/ci.yml`. The release workflow calls the same `Format` and `Unit` jobs used by pull requests and `main`. It does not copy those checks into a second workflow.

### Release workflow

Add `.github/workflows/release.yml` with a `release.published` trigger.

The workflow:

1. Skips prereleases.
2. Runs the reusable CI workflow.
3. Checks out the released tag with full Git history.
4. Validates the stable tag format, `main` ancestry, and both manifest versions.
5. Clones the marketplace through SSH.
6. Runs the marketplace updater.
7. Checks the generated diff and JSON.
8. Creates a signed commit with the `github-actions` identity when a change exists.
9. Pushes to marketplace `main` without force.

The workflow has read-only `contents` permission in Behavior Diff.

### Marketplace updater

Add `.github/scripts/update-marketplace.sh` as a small deterministic command. It accepts the marketplace index path and release version. It validates inputs, updates `version` and `source.ref`, validates the result, and replaces the JSON file atomically.

Keeping this logic outside workflow YAML makes it executable in local tests and keeps the workflow focused on orchestration.

### Tests

Add `tests/release-workflow-test.sh` and run it from the existing Unit job.

The test covers:

- Updating version and tag reference together.
- Preserving unrelated marketplace entries.
- A second run producing no change.
- Rejecting an invalid version.
- Rejecting a missing Behavior Diff entry.
- Rejecting duplicate Behavior Diff entries.
- The workflow trigger, prerelease guard, manifest checks, CI dependency, and deploy-key use.

The existing Bash syntax and formatting checks include the new scripts.
`AGENTS.md` and `CODING_GUIDELINES.md` add the release contract to the full
deterministic suite so local and CI verification stay aligned.

### Operator documentation

Add a short release section to the existing README:

1. Update both plugin manifests to the same version.
2. Merge the version change and wait for `main` CI.
3. In GitHub, create a Release with tag `vX.Y.Z` targeting `main`.
4. Publish it as a stable release.
5. Confirm the release workflow and marketplace commit.

The same README change removes the outdated claim that the marketplace entry
is not live. It also removes product text that says Behavior Diff shows model
cost, waits for approval, and advertises standard or fast run counts. The
replacement says the comparison starts once its task is known, without
exposing internal run modes or trial counts.

## Authentication

Use one SSH deploy key dedicated to this integration.

- Add its public key to `spacedock-dev/marketplace` with write access.
- Store its private key as the `MARKETPLACE_DEPLOY_KEY` Actions secret in `spacedock-dev/behavior-diff`.
- Do not use a personal access token.
- Do not reuse another repository's deploy key.
- Do not commit or print private key material.

The workflow writes the key to a temporary file with mode `600`, uses strict GitHub host-key checking, and removes the temporary SSH directory on exit.

## Failure behavior

- A tag, ancestry, manifest, CI, JSON, or secret failure stops before any marketplace commit.
- A concurrent marketplace change can make the push fail. The workflow does not force push. Rerunning the failed job retries against current marketplace `main`.
- If marketplace already points to the released version and tag, the workflow exits successfully without a commit.
- Because the trigger is `release.published`, a failed workflow does not hide or delete the GitHub Release. Marketplace remains on its last good release.
- Published tags are immutable. Correct a bad release with a new patch version rather than moving the tag.
- If a marketplace release must be withdrawn, revert the marketplace commit separately and publish a corrected patch release.

## Rollout

1. Merge the release-process change to Behavior Diff `main`.
2. Provision the dedicated deploy key in both repositories.
3. Publish the first GitHub Release as `v0.3.2`, targeting the release-process commit on `main`.
4. Confirm the workflow changes marketplace `version` to `0.3.2` and `source.ref` to `v0.3.2`.
5. Confirm a clean rerun creates no marketplace commit.

## Alternatives considered

### Tag-push workflow

This matches Subspace. It validates before creating the GitHub Release, so an invalid release never becomes visible. It was not selected because the preferred operator flow is the GitHub Release UI.

### Manual workflow dispatch

A workflow form could accept a version, validate `main`, and create the tag and Release. It gives strong guardrails but duplicates the GitHub Release UI and adds more workflow logic.

### Personal access token

A fine-grained token could update marketplace. It was not selected because it is tied to a person and normally grants a wider permission surface than one repository deploy key.

## Non-goals

- Building binaries or custom release archives.
- Updating a prerelease or edge marketplace channel.
- Publishing from branches other than `main`.
- Moving or overwriting published tags.
- Creating a general release framework for other plugins.
