#!/usr/bin/env bash
# One behavior-diff trial: launch the chosen agent inside a variant copy and
# write DIR/trace.jsonl in the claude stream-json shape every reader
# (grader, render.py, decisions.py) consumes. Codex events are normalized:
# command_execution items become assistant tool_use lines, the last
# agent_message becomes the result line.
#
# Usage: run-trial.sh --agent claude|codex --model M --dir DIR \
#          --task-file FILE [--allowed CLAUDE_TOOL_LIST] [--trace-dir DIR]
# The agent runs with cwd DIR; trace.jsonl/stderr.log land in --trace-dir
# (default: DIR).
set -euo pipefail
agent="" model="" dir="" task_file="" allowed="" trace_dir=""
while [ $# -gt 0 ]; do
  case "$1" in
    --agent) agent=$2; shift 2 ;;
    --model) model=$2; shift 2 ;;
    --dir) dir=$2; shift 2 ;;
    --task-file) task_file=$2; shift 2 ;;
    --allowed) allowed=$2; shift 2 ;;
    --trace-dir) trace_dir=$2; shift 2 ;;
    *) echo "run-trial: unknown argument $1" >&2; exit 2 ;;
  esac
done
case "$agent" in claude|codex) ;; *) echo "run-trial: --agent must be claude or codex" >&2; exit 2 ;; esac
[ -n "$model" ] && [ -d "$dir" ] && [ -f "$task_file" ] || {
  echo "run-trial: --model, --dir, --task-file required" >&2; exit 2; }
task=$(cat "$task_file")
trace_dir=$(cd "${trace_dir:-$dir}" && pwd)
cd "$dir"

# BEHAVIOR_DIFF_TRIAL tells this plugin's own hooks to stay silent inside a
# trial — otherwise a user-scope install would nudge itself recursively.
export BEHAVIOR_DIFF_TRIAL=1

if [ "$agent" = claude ]; then
  claude -p "$task" --model "$model" \
    ${allowed:+--allowedTools "$allowed"} \
    --output-format stream-json --verbose > "$trace_dir/trace.jsonl" 2> "$trace_dir/stderr.log" || true
else
  # Codex has no per-tool allowlist; the workspace-write sandbox scoped to
  # this variant copy is the equivalent containment.
  codex exec --ephemeral --skip-git-repo-check -s workspace-write \
    -m "$model" --json "$task" < /dev/null > "$trace_dir/codex-raw.jsonl" 2> "$trace_dir/stderr.log" || true
  jq -c 'select(.type == "item.completed"
                and (.item.item_type // .item.type) == "command_execution")
         | {type: "assistant", message: {content: [{type: "tool_use",
            name: "Bash", input: {command:
              (.item.command // "" | sub("^/bin/[a-zA-Z]+ -lc "; ""))}}]}}' \
    "$trace_dir/codex-raw.jsonl" > "$trace_dir/trace.jsonl"
  jq -s -c '[.[] | select(.type == "item.completed"
                          and (.item.item_type // .item.type) == "agent_message")
             | .item.text]
            | {type: "result", result: (last // "")}' \
    "$trace_dir/codex-raw.jsonl" >> "$trace_dir/trace.jsonl"
fi
