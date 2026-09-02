#!/usr/bin/env bash
set -euo pipefail

here=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
updater=$here/../.github/scripts/update-marketplace.sh
release_workflow=$here/../.github/workflows/release.yml
ci_workflow=$here/../.github/workflows/ci.yml
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

fail() {
  printf 'FAIL: %s\n' "$1" >&2
  exit 1
}

require_literal() {
  local literal=$1
  local file=$2
  local message=$3
  grep -Fq -- "$literal" "$file" || fail "$message"
}

make_index() {
  cat >"$1" <<'JSON'
{
  "name": "spacedock",
  "plugins": [
    {
      "name": "other-plugin",
      "source": {"ref": "stable"},
      "version": "1.0.0"
    },
    {
      "name": "behavior-diff",
      "source": {
        "source": "git-subdir",
        "url": "https://github.com/spacedock-dev/behavior-diff.git",
        "path": "plugin",
        "ref": "main"
      },
      "version": "0.3.1"
    }
  ]
}
JSON
}

printf '[release] Update one marketplace entry\n'
index=$tmp/marketplace.json
make_index "$index"
"$updater" "$index" 0.3.2
jq -e '
  [.plugins[] |
    select(.name == "behavior-diff" and
           .version == "0.3.2" and
           .source.ref == "v0.3.2")] |
  length == 1
' "$index" >/dev/null || fail 'Behavior Diff entry was not updated'
jq -e '
  [.plugins[] |
    select(.name == "other-plugin" and
           .version == "1.0.0" and
           .source.ref == "stable")] |
  length == 1
' "$index" >/dev/null || fail 'unrelated entry changed'

printf '[release] Keep repeated updates unchanged\n'
cp "$index" "$tmp/expected.json"
"$updater" "$index" 0.3.2
cmp -s "$tmp/expected.json" "$index" || fail 'second update changed the index'

printf '[release] Reject invalid versions and entry counts\n'
make_index "$tmp/invalid-version.json"
if "$updater" "$tmp/invalid-version.json" v0.3.2 >/dev/null 2>&1; then
  fail 'updater accepted a version with v prefix'
fi

make_index "$tmp/missing.json"
jq '.plugins |= map(select(.name != "behavior-diff"))' \
  "$tmp/missing.json" >"$tmp/missing.tmp"
mv "$tmp/missing.tmp" "$tmp/missing.json"
if "$updater" "$tmp/missing.json" 0.3.2 >/dev/null 2>&1; then
  fail 'updater accepted a missing Behavior Diff entry'
fi

make_index "$tmp/duplicate.json"
jq '.plugins += [.plugins[] | select(.name == "behavior-diff")]' \
  "$tmp/duplicate.json" >"$tmp/duplicate.tmp"
mv "$tmp/duplicate.tmp" "$tmp/duplicate.json"
if "$updater" "$tmp/duplicate.json" 0.3.2 >/dev/null 2>&1; then
  fail 'updater accepted duplicate Behavior Diff entries'
fi

printf '[release] Keep GitHub Release and security invariants\n'
require_literal 'workflow_call:' "$ci_workflow" \
  'CI is not reusable from the release workflow'
require_literal 'types: [published]' "$release_workflow" \
  'release workflow does not use the published event'
require_literal "if: \${{ !github.event.release.prerelease }}" \
  "$release_workflow" 'release workflow does not skip prereleases'
require_literal 'uses: ./.github/workflows/ci.yml' "$release_workflow" \
  'release workflow does not reuse deterministic CI'
require_literal 'needs: ci' "$release_workflow" \
  'marketplace update is not gated by CI'
require_literal 'plugin/.claude-plugin/plugin.json' "$release_workflow" \
  'release workflow does not validate the Claude manifest'
require_literal 'plugin/.codex-plugin/plugin.json' "$release_workflow" \
  'release workflow does not validate the Codex manifest'
require_literal 'git merge-base --is-ancestor HEAD origin/main' \
  "$release_workflow" 'release workflow does not require a main commit'
require_literal "MARKETPLACE_DEPLOY_KEY: \${{ secrets.MARKETPLACE_DEPLOY_KEY }}" \
  "$release_workflow" 'release workflow does not use the deploy-key secret'
require_literal "update-marketplace.sh\" \"\$INDEX\" \"\$VERSION\"" \
  "$release_workflow" 'release workflow does not call the tested updater'

printf 'ok — release workflow contract passed\n'
