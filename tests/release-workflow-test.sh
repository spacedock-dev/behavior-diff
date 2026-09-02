#!/usr/bin/env bash
set -euo pipefail

here=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
updater=$here/../.github/scripts/update-marketplace.sh
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

fail() {
  printf 'FAIL: %s\n' "$1" >&2
  exit 1
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

printf 'ok — release workflow contract passed\n'
