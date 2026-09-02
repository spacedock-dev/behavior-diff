#!/usr/bin/env bash
# PostToolUse (Edit|Write|MultiEdit): when the agent edits an instruction
# file (CLAUDE.md / AGENTS.md / SKILL.md), record it for this session so the
# Stop hook can offer /behavior-diff once at end of turn.
# Fail quiet: every exit path is 0 — a broken hook must never block a session.
set -uo pipefail
quit() { exit 0; }

# never fire inside behavior-diff's own trials (run-trial.sh sets this)
[ "${BEHAVIOR_DIFF_TRIAL:-}" = "1" ] && quit
command -v jq >/dev/null 2>&1 || quit

input=$(cat 2>/dev/null) || quit
cwd=$(printf '%s' "$input" | jq -r '.cwd // empty' 2>/dev/null)
path=$(printf '%s' "$input" | jq -r '.tool_input.file_path // empty' 2>/dev/null) || quit
if [ -n "$path" ]; then
  raw=$path
else
  # Codex: file edits arrive as apply_patch with no file_path — the edited
  # paths sit in the patch grammar of tool_input.command, one per directive
  # line, cwd-relative. One patch can touch several files.
  [ "$(printf '%s' "$input" | jq -r '.tool_name // empty' 2>/dev/null)" = "apply_patch" ] || quit
  [ -n "$cwd" ] || quit
  raw=$(printf '%s' "$input" | jq -r '.tool_input.command // empty' 2>/dev/null |
    sed -n -e 's/^\*\*\* Update File: //p' -e 's/^\*\*\* Add File: //p') || quit
fi

paths=()
while IFS= read -r p; do
  [ -n "$p" ] || continue
  case "$(basename "$p")" in
    CLAUDE.md|AGENTS.md|SKILL.md) ;;
    *) continue ;;
  esac
  case "$p" in
    /*) ;;
    *) [ -n "$cwd" ] || continue; p=$cwd/$p ;;
  esac
  paths+=("$p")
done <<< "$raw"
[ "${#paths[@]}" -gt 0 ] || quit

session=$(printf '%s' "$input" | jq -r '.session_id // empty' 2>/dev/null) || quit
[ -n "$session" ] || quit
[[ "$session" =~ ^[A-Za-z0-9._:-]+$ ]] || quit

state_dir=${BEHAVIOR_DIFF_HOME:-$HOME/.behavior-diff}/nudge
mkdir -p "$state_dir" 2>/dev/null || quit
chmod 700 "$state_dir" 2>/dev/null
find "$state_dir" -type f -mtime +7 -delete 2>/dev/null

state=$state_dir/$session.edits
for p in "${paths[@]}"; do
  if ! grep -qxF -- "$p" "$state" 2>/dev/null; then
    printf '%s\n' "$p" >> "$state" 2>/dev/null
  fi
done

# Whisper to the agent once per session: when the work is done, ask the user
# (Route B — the agent asks; the hook never blocks). The whisper suppresses
# the Stop-time fallback line, so mark that it was sent.
whispered=$state_dir/$session.whispered
[ -f "$whispered" ] && quit
: > "$whispered" 2>/dev/null || quit
files=
for p in "${paths[@]}"; do
  if [ -z "$files" ]; then files=$p; else files="$files, $p"; fi
done
ctx="An instruction file was just edited in this session: $files. When the current task is complete, ask the user whether to run the behavior-diff skill on this change before they commit — use the AskUserQuestion tool if it is available (options: 'Run behavior-diff' / 'Skip'); otherwise ask in one plain sentence. Ask once. If the user declines or does not answer, drop the subject. Never run behavior-diff without an explicit yes."
jq -n --arg ctx "$ctx" \
  '{hookSpecificOutput: {hookEventName: "PostToolUse", additionalContext: $ctx}}'
quit
