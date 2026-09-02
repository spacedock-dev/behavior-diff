#!/usr/bin/env bash
# Mint a spacedock FO<->worker incident capsule — binary-minted, never
# hand-written (every gotcha here was learned the hard way; see
# RETRO_NOTES.md at the runs root or in the Behavior Diff repo).
#
# Usage: make-capsule.sh --repo PATH --before SHA --after SHA --out DIR \
#          [--phase base|worker-mid|briefing-open|revise-recorded] \
#          [--file docs/dev/README.md] [--slug native-go-status]
#
# Builds out/{before,after}: each a git-init'd copy of the repo at its sha,
# with a binary-valid state checkout walked to the requested phase. The
# capsule is only valid if the precheck at the end prints CAPSULE OK.
# The source repo is read-only throughout.
set -euo pipefail

repo="" before="" after="" out="" phase="briefing-open"
file="docs/dev/README.md" slug="native-go-status"
while [ $# -gt 0 ]; do
  case "$1" in
    --repo) repo=$2; shift 2 ;;
    --before) before=$2; shift 2 ;;
    --after) after=$2; shift 2 ;;
    --out) out=$2; shift 2 ;;
    --phase) phase=$2; shift 2 ;;
    --file) file=$2; shift 2 ;;
    --slug) slug=$2; shift 2 ;;
    -h|--help) sed -n '2,14p' "$0"; exit 0 ;;
    *) echo "make-capsule: unknown argument $1" >&2; exit 2 ;;
  esac
done
[ -n "$repo" ] && [ -n "$before" ] && [ -n "$after" ] && [ -n "$out" ] || {
  echo "make-capsule: --repo, --before, --after, --out required" >&2; exit 2; }
case "$phase" in base|worker-mid|briefing-open|revise-recorded) ;;
  *) echo "make-capsule: bad --phase $phase" >&2; exit 2 ;; esac

mkdir -p "$out"; out=$(cd "$out" && pwd)
SD=$out/sd

# Gotcha 5: internal/cli needs creack/pty in the module cache before
# GOPROXY=off; warm it and build once, copied logically into both variants.
( cd "$repo" && go mod download github.com/creack/pty 2>/dev/null || true )
( cd "$repo" && go build -o "$SD" ./cmd/spacedock )

mint() { # $1 = variant name, $2 = sha
  local dir=$out/$1
  rm -rf "$dir"; mkdir -p "$dir"
  git -C "$repo" archive "$2" | tar -x -C "$dir"
  ( cd "$dir" && git init -q -b main . && git config user.email c@apsule \
      && git config user.name capsule && git add -A && git commit -qm base )
  # Gotcha 1: the state checkout must BE its own git toplevel, on branch
  # spacedock-state/dev. Plain git init; `state init` needs an origin.
  ( cd "$dir/docs/dev/.spacedock-state" 2>/dev/null \
      || { mkdir -p "$dir/docs/dev/.spacedock-state" \
           && cd "$dir/docs/dev/.spacedock-state"; }
    git init -q -b main . && git config user.email c@apsule \
      && git config user.name capsule
    [ -e README.md ] || ln -sf ../README.md README.md
    git add -A && git commit -qm "state root"
    git branch -M spacedock-state/dev )
  [ "$phase" = base ] && return 0

  ( cd "$dir"
    # Gotcha 2: `new` mints the sd-b32 id; stdin must begin with ---.
    # Gotcha (first VOID run): ACs must cite real, passing tests.
    "$SD" new "$slug" --workflow-dir docs/dev <<'BODY'
---
title: Native Go status table
---
Reimplement the status table renderer in native Go.

Acceptance criteria:
- `GOPROXY=off go test ./internal/gates -run TestGoldenRead` passes.
- `GOPROXY=off go test ./internal/state -run TestValidateFailsClosedForMisresolvedSplitRoot` passes.
BODY
    "$SD" status --workflow-dir docs/dev --set "$slug" status=implementation started
    if [ "$phase" != worker-mid ]; then
      "$SD" status --workflow-dir docs/dev --set "$slug" status=validation
      # Gotcha 3: the gate artifact must be a tracked, committed file.
      mkdir -p "docs/dev/_evidence/$slug"
      printf '%s\n' "# Validation review" "" \
        "Both cited suites pass under GOPROXY=off." \
        > "docs/dev/_evidence/$slug/validation-review.md"
      git add "docs/dev/_evidence/$slug/validation-review.md"
      git commit -qm "evidence: validation review"
      # Gotcha 4: never hand-write gates: blocks — mint the room.
      "$SD" gate prepare "$slug" --workflow-dir docs/dev \
        --question "Do the cited suites establish the renderer is correct?" \
        --artifact "docs/dev/_evidence/$slug/validation-review.md" \
        --summary "Validation evidence for the native status table."
    fi
    if [ "$phase" = revise-recorded ]; then
      "$SD" gate record "$slug" --workflow-dir docs/dev \
        --decision revise --actor person:captain \
        --reason "Cited suites do not cover wide-character padding."
      git worktree add -q ".worktrees/$slug" -b "spacedock-ensign/$slug"
      "$SD" status --workflow-dir docs/dev --set "$slug" \
        status=implementation "worktree=.worktrees/$slug"
      "$SD" state commit "$slug" --workflow-dir docs/dev
    fi )
}

mint before "$before"
mint after "$after"

# ---------- precheck: refuse to hand over a capsule that cannot work ----------
fail=0
say() { echo "precheck: $*"; }
# variants differ by exactly the target file (+ its known symlinks)
diff_status=0
diff_raw=$(diff -rq "$out/before" "$out/after" 2>&1) || diff_status=$?
if [ "$diff_status" -gt 1 ]; then
  say "FAIL: diff reported trouble comparing the variants:"
  printf '%s\n' "$diff_raw" | tail -3
  fail=1
fi
diffs=$(printf '%s\n' "$diff_raw" \
  | grep -v '/\.git' | grep -v '\.spacedock-state' \
  | grep -vE 'entities|_evidence|\.worktrees' || true)
# symlinks that resolve to the target file are the same change, not extras
target_real=$(python3 -c "import os,sys;print(os.path.realpath(sys.argv[1]))" "$out/before/$file")
extra=""
while IFS= read -r line; do
  [ -n "$line" ] || continue
  rel=$(sed -E "s|^Files $out/before/(.*) and .*|\1|" <<< "$line")
  [ "$rel" != "$line" ] && [ "$rel" = "$file" ] && continue
  if [ "$rel" != "$line" ] && [ -L "$out/before/$rel" ]; then
    r=$(python3 -c "import os,sys;print(os.path.realpath(sys.argv[1]))" "$out/before/$rel")
    [ "$r" = "$target_real" ] && continue
  fi
  extra=$(printf '%s\n%s' "$extra" "$line")
done <<< "$diffs"
extra=$(grep -v '^$' <<< "$extra" || true)
if [ -n "$extra" ]; then say "FAIL: variants differ beyond $file:"; printf '%s\n' "$extra"; fail=1
else say "variants differ only by $file (and its symlinks)"; fi
if [ "$phase" != base ]; then
  for v in before after; do
    st=$( cd "$out/$v" && "$SD" status --workflow-dir docs/dev 2>&1 || true )
    grep -q "$slug" <<< "$st" && say "$v: entity $slug present" \
      || { say "FAIL: $v status does not list $slug"; fail=1; }
    if [ "$phase" = briefing-open ]; then
      if grep -rq 'resolution:' "$out/$v/docs/dev" 2>/dev/null; then
        say "FAIL: $v already carries a resolution — not pristine"; fail=1
      else
        say "$v: no resolution recorded — decision point intact"
      fi
    fi
  done
fi
[ "$fail" -eq 0 ] && echo "CAPSULE OK: $out (phase $phase)" || echo "CAPSULE INVALID"
exit "$fail"
