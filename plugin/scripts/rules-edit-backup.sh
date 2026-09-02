#!/usr/bin/env bash
# PreToolUse (Edit|Write|MultiEdit): before the agent edits an instruction
# file (CLAUDE.md / AGENTS.md / SKILL.md) that git does NOT track, copy the
# original into the baseline store so behavior-diff still has a "before"
# side. Tracked files need no copy — git HEAD is their baseline. One backup
# per file per session (first edit wins); the copy is skipped when the
# content already equals the newest baseline; a file that does not exist
# yet gets an ABSENT marker; entries older than 30 days are pruned.
# Fail quiet: every exit path is 0 — a broken hook must never block a session.
set -uo pipefail
quit() { exit 0; }

# never fire inside behavior-diff's own trials (run-trial.sh sets this)
[ "${BEHAVIOR_DIFF_TRIAL:-}" = "1" ] && quit
command -v jq >/dev/null 2>&1 || quit

input=$(cat 2>/dev/null) || quit
cwd=$(printf '%s' "$input" | jq -r '.cwd // empty' 2>/dev/null)
path=$(printf '%s' "$input" | jq -r '.tool_input.file_path // empty' 2>/dev/null) || quit
[ -n "$path" ] || quit
case "$(basename "$path")" in
  CLAUDE.md | AGENTS.md | SKILL.md) ;;
  *) quit ;;
esac
case "$path" in
  /*) ;;
  *)
    [ -n "$cwd" ] || quit
    path=$cwd/$path
    ;;
esac
# canonicalize the directory part so the runner resolves the same store key
if dir=$(cd "$(dirname "$path")" 2>/dev/null && pwd -P); then
  path=$dir/$(basename "$path")
fi

# a file git tracks needs no baseline — the runner diffs against HEAD
if [ -f "$path" ] &&
  git -C "$(dirname "$path")" ls-files --error-unmatch "$path" >/dev/null 2>&1; then
  quit
fi

session=$(printf '%s' "$input" | jq -r '.session_id // empty' 2>/dev/null) || quit
[ -n "$session" ] || quit
[[ "$session" =~ ^[A-Za-z0-9._:-]+$ ]] || quit

# store key: the absolute path, percent-encoded into one directory name
# (keep this encoding identical to resolve_baseline in behavior-diff.sh)
enc=$(printf '%s' "$path" | sed 's|%|%25|g; s|/|%2F|g')
store=${BEHAVIOR_DIFF_HOME:-$HOME/.behavior-diff}/baselines
mkdir -p "$store" 2>/dev/null || quit
chmod 700 "$store" 2>/dev/null
find "$store" -mindepth 1 -type f -mtime +30 -delete 2>/dev/null
find "$store" -mindepth 1 -type d -empty -delete 2>/dev/null
dest=$store/$enc
mkdir -p "$dest" 2>/dev/null || quit

# first edit wins: one baseline per file per session
marker=$dest/.session-$session
[ -f "$marker" ] && quit

# shellcheck disable=SC2012 # entry names are our own <ts>-<hash>, mtime = newest
newest=$(ls -t "$dest" 2>/dev/null | head -n 1)
if [ ! -f "$path" ]; then
  # the file does not exist yet — record that "before" is absence
  case "$newest" in
    *-ABSENT) ;;
    *) : >"$dest/$(date +%Y%m%d-%H%M%S)-ABSENT" 2>/dev/null || quit ;;
  esac
  : >"$marker" 2>/dev/null
  quit
fi
if [ -n "$newest" ]; then
  case "$newest" in
    *-ABSENT) ;; # an absence marker never equals a real file
    *) if cmp -s "$dest/$newest" "$path" 2>/dev/null; then
      : >"$marker" 2>/dev/null # unchanged since the newest baseline
      quit
    fi ;;
  esac
fi
hash=$(cksum <"$path" 2>/dev/null | awk '{print $1}')
[ -n "$hash" ] || hash=0
cp "$path" "$dest/$(date +%Y%m%d-%H%M%S)-$hash" 2>/dev/null || quit
: >"$marker" 2>/dev/null
quit
