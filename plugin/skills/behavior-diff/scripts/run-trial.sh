#!/usr/bin/env bash
# One behavior-diff trial: launch the chosen agent inside a variant copy and
# write DIR/trace.jsonl in the claude stream-json shape every reader
# (grader, render.py, decisions.py) consumes. Codex, Pi, and OMP events are
# normalized into assistant tool_use lines plus one final result line.
#
# Usage: run-trial.sh --agent claude|codex|pi|omp --model M --dir DIR \
#          --task-file FILE [--allowed CLAUDE_TOOL_LIST] [--trace-dir DIR]
# The agent runs with cwd DIR; trace.jsonl/stderr.log land in --trace-dir
# (default: DIR).
set -euo pipefail
agent="" model="" dir="" task_file="" allowed="" trace_dir=""
while [ $# -gt 0 ]; do
  case "$1" in
    --agent)
      agent=$2
      shift 2
      ;;
    --model)
      model=$2
      shift 2
      ;;
    --dir)
      dir=$2
      shift 2
      ;;
    --task-file)
      task_file=$2
      shift 2
      ;;
    --allowed)
      allowed=$2
      shift 2
      ;;
    --trace-dir)
      trace_dir=$2
      shift 2
      ;;
    *)
      echo "run-trial: unknown argument $1" >&2
      exit 2
      ;;
  esac
done
case "$agent" in claude | codex | pi | omp) ;; *)
  echo "run-trial: --agent must be claude, codex, pi, or omp" >&2
  exit 2
  ;;
esac
[ -n "$model" ] && [ -d "$dir" ] && [ -f "$task_file" ] || {
  echo "run-trial: --model, --dir, --task-file required" >&2
  exit 2
}
task=$(cat "$task_file")
trace_dir=$(cd "${trace_dir:-$dir}" && pwd)
cd "$dir"

# BEHAVIOR_DIFF_TRIAL tells this plugin's own hooks to stay silent inside a
# trial — otherwise a user-scope install would nudge itself recursively.
export BEHAVIOR_DIFF_TRIAL=1

normalize_pi_omp_json() { # $1 = raw Pi or OMP JSONL
  local raw=$1
  jq -c '
    select(.type == "tool_execution_start")
    | {type: "assistant", message: {content: [{
        type: "tool_use",
        name: .toolName,
        input: ((.args // {})
          | if (has("file_path") or has("command")) then .
            elif has("path") then . + {file_path: .path}
            else .
            end)
      }]}}
  ' "$raw" >"$trace_dir/trace.jsonl"

  jq -s -c '
    [.[]
      | select(.type == "message_end" and .message.role == "assistant")
      | [.message.content[]? | select(.type == "text") | .text]
      | join("")]
    | {type: "result", result: (last // "")}
  ' "$raw" >>"$trace_dir/trace.jsonl"
}

if [ "$agent" = claude ]; then
  claude -p "$task" --model "$model" \
    ${allowed:+--allowedTools "$allowed"} \
    --output-format stream-json --verbose >"$trace_dir/trace.jsonl" 2>"$trace_dir/stderr.log" || true
elif [ "$agent" = codex ]; then
  # Codex has no per-tool allowlist; the workspace-write sandbox scoped to
  # this variant copy is the equivalent containment.
  codex exec --ephemeral --skip-git-repo-check -s workspace-write \
    -m "$model" --json "$task" </dev/null >"$trace_dir/codex-raw.jsonl" 2>"$trace_dir/stderr.log" || true
  jq -c 'select(.type == "item.completed"
                and (.item.item_type // .item.type) == "command_execution")
         | {type: "assistant", message: {content: [{type: "tool_use",
            name: "Bash", input: {command:
              (.item.command // "" | sub("^/bin/[a-zA-Z]+ -lc "; ""))}}]}}' \
    "$trace_dir/codex-raw.jsonl" >"$trace_dir/trace.jsonl"
  jq -s -c '[.[] | select(.type == "item.completed"
                          and (.item.item_type // .item.type) == "agent_message")
             | .item.text]
            | {type: "result", result: (last // "")}' \
    "$trace_dir/codex-raw.jsonl" >>"$trace_dir/trace.jsonl"
elif [ "$agent" = omp ]; then
  printf '%s\n' "$task" | omp -p \
    --mode json --no-session --no-title --cwd "$dir" \
    --model "$model" --tools read,bash,grep,glob \
    --approval-mode yolo \
    >"$trace_dir/omp-raw.jsonl" 2>"$trace_dir/stderr.log" || true
  normalize_pi_omp_json "$trace_dir/omp-raw.jsonl"
else
  printf '%s\n' "$task" |
    PI_SKIP_VERSION_CHECK=1 PI_TELEMETRY=0 \
      pi -p --mode json --no-session --model "$model" \
      --tools read,bash,grep,find,ls \
      >"$trace_dir/pi-raw.jsonl" 2>"$trace_dir/stderr.log" || true
  normalize_pi_omp_json "$trace_dir/pi-raw.jsonl"
fi
