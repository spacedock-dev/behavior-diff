#!/usr/bin/env bash
set -euo pipefail

usage() {
  printf 'usage: %s <marketplace.json> <X.Y.Z>\n' "${0##*/}" >&2
  exit 2
}

[[ $# -eq 2 ]] || usage
index=$1
version=$2

if [[ ! -f $index ]]; then
  printf 'marketplace index not found: %s\n' "$index" >&2
  exit 1
fi

if ! command -v jq >/dev/null; then
  printf 'required command not found: jq\n' >&2
  exit 1
fi

if ! [[ $version =~ ^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$ ]]; then
  printf 'release version must use X.Y.Z: %s\n' "$version" >&2
  exit 1
fi

count=$(jq '[.plugins[] | select(.name == "behavior-diff")] | length' "$index")
if [[ $count -ne 1 ]]; then
  printf 'expected one behavior-diff marketplace entry, found %s\n' "$count" >&2
  exit 1
fi

tmp=$(mktemp "${index}.tmp.XXXXXX")
trap 'rm -f "$tmp"' EXIT
jq --arg version "$version" '
  (.plugins[] | select(.name == "behavior-diff") | .version) = $version |
  (.plugins[] | select(.name == "behavior-diff") | .source.ref) = ("v" + $version)
' "$index" >"$tmp"

jq -e --arg version "$version" '
  [.plugins[] |
    select(.name == "behavior-diff" and
           .version == $version and
           .source.ref == ("v" + $version))] |
  length == 1
' "$tmp" >/dev/null

mv "$tmp" "$index"
trap - EXIT
