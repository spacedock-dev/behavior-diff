#!/usr/bin/env bash
# Stop: once per session, if an instruction file was edited this session and
# still has uncommitted changes, tell the user to run /behavior-diff.
# One line only — the Stop surface prefixes every output line with "Stop says:",
# so a blank line or second paragraph renders as garbage (measured in tricorder).
# Fail quiet: every exit path is 0. No control keys, ever — this must never
# block or redirect a turn.
set -uo pipefail
quit() { exit 0; }

[ "${BEHAVIOR_DIFF_TRIAL:-}" = "1" ] && quit
command -v jq >/dev/null 2>&1 || quit

input=$(cat 2>/dev/null) || quit
[ "$(printf '%s' "$input" | jq -r '.stop_hook_active // false' 2>/dev/null)" = "true" ] && quit
session=$(printf '%s' "$input" | jq -r '.session_id // empty' 2>/dev/null) || quit
cwd=$(printf '%s' "$input" | jq -r '.cwd // empty' 2>/dev/null)
[ -n "$session" ] || quit
[[ "$session" =~ ^[A-Za-z0-9._:-]+$ ]] || quit

state_dir=${BEHAVIOR_DIFF_HOME:-$HOME/.behavior-diff}/nudge
state=$state_dir/$session.edits
[ -f "$state" ] || quit

# Route B: if the detect hook whispered the ask-the-user instruction to the
# agent this session, the agent owns the question — a second line here would
# duplicate it right after the user answered. If the live check ever shows
# whispers going undelivered, remove this suppression.
[ -f "$state_dir/$session.whispered" ] && quit

# Claim before speaking: the rename makes a second Stop in this session (or a
# racing one) find nothing, so the offer happens at most once per session.
spoken=$state.spoken
mv "$state" "$spoken" 2>/dev/null || quit

# Keep only files that still have uncommitted changes — behavior-diff needs an
# uncommitted edit to diff. A failed git check errs toward reminding.
pending=()
while IFS= read -r f; do
  [ -n "$f" ] || continue
  if [ -n "$cwd" ] && command -v git >/dev/null 2>&1; then
    dirty=$(git -C "$cwd" status --porcelain -- "$f" 2>/dev/null) || dirty="unknown"
    [ -n "$dirty" ] || continue
  fi
  pending+=("$f")
done < "$spoken"
[ "${#pending[@]}" -gt 0 ] || quit

if [ "${#pending[@]}" -eq 1 ]; then
  what=$(basename "${pending[0]}")
else
  what="${#pending[@]} instruction files"
fi
msg="📊 $what changed this session — run /behavior-diff before committing to see whether the edit actually changes agent behavior."
jq -n --arg m "$msg" '{systemMessage: $m}'
quit
