#!/usr/bin/env bash
# One behavior-diff trial: launch the chosen agent inside a variant copy and
# write DIR/trace.jsonl in the claude stream-json shape every reader
# (grader, render.py, decisions.py) consumes. Codex, Pi, and OMP events retain
# paired tool calls/results plus one final result line.
#
# Usage: run-trial.sh --agent claude|codex|pi|omp --model M --dir DIR \
#          --task-file FILE [--allowed CLAUDE_TOOL_LIST] [--trace-dir DIR] \
#          [--status-file FILE]
# The agent runs with cwd DIR; trace.jsonl/stderr.log land in --trace-dir
# (default: DIR). --status-file names the caller-owned trial status record;
# this script merges only its phase and the host CLI exit code into it.
set -euo pipefail
agent="" model="" dir="" task_file="" allowed="" trace_dir="" status_file=""
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
    --status-file)
      status_file=$2
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
scripts=$(cd "$(dirname "$0")" && pwd)
if [ "$agent" = codex ]; then
  case "$model" in
    sol | luna)
      model=$(python3 "$scripts/codex_model.py" "$model") || exit 2
      ;;
  esac
fi
if [ -n "$status_file" ]; then
  status_file=$(cd "$(dirname "$status_file")" && pwd)/$(basename "$status_file")
fi
task=$(cat "$task_file")
trace_dir=$(cd "${trace_dir:-$dir}" && pwd)
cd "$dir"

# BEHAVIOR_DIFF_TRIAL tells this plugin's own hooks to stay silent inside a
# trial — otherwise a user-scope install would nudge itself recursively.
export BEHAVIOR_DIFF_TRIAL=1

# A skill may start another comparison. Keep its runs and baselines out of the
# orchestrator's home and other trials, including when both share the same HOME.
export BEHAVIOR_DIFF_HOME="$trace_dir/behavior-diff-home"

normalize_pi_omp_json() { # $1 = raw Pi or OMP JSONL
  local raw=$1
  jq -c '
    if .type == "tool_execution_start" then
      {type: "assistant", message: {content: [{
        type: "tool_use", id: .toolCallId,
        name: .toolName,
        input: ((.args // {})
          | if (has("file_path") or has("command")) then .
            elif has("path") then . + {file_path: .path}
            else .
            end)
      }]}}
    elif .type == "tool_execution_end" then
      {type: "user", message: {content: [{
        type: "tool_result", tool_use_id: .toolCallId,
        content: (.result.content // null), is_error: (.isError // false),
        truncated: (.result.details.truncated // false)
      }]}}
    else empty end
  ' "$raw" >"$trace_dir/trace.jsonl"

  jq -s -c '
    [.[]
      | select(.type == "message_end" and .message.role == "assistant")
      | [.message.content[]? | select(.type == "text") | .text]
      | join("")]
    | {type: "result", result: (last // "")}
  ' "$raw" >>"$trace_dir/trace.jsonl"
}

record_status() { # $1 JSON fields; only with --status-file
  [ -n "$status_file" ] || return 0
  # A status write never changes the trial or its exit code. progress.py
  # diagnoses its own failures on stderr.
  python3 "$scripts/progress.py" "$status_file" trial "$1" || :
}

# A failing host CLI still leaves its output for normalization as evidence.
# Record its exit code rather than propagating it; report loading and
# assessment treat a nonzero exit as an incomplete trial.
cli_exit=0
record_status '{"phase":"running"}'
if [ "$agent" = claude ]; then
  claude -p "$task" --model "$model" \
    ${allowed:+--allowedTools "$allowed"} \
    --output-format stream-json --verbose >"$trace_dir/trace.jsonl" 2>"$trace_dir/stderr.log" || cli_exit=$?
  record_status "{\"cli_exit_code\":$cli_exit}"
elif [ "$agent" = codex ]; then
  if [ -n "${BEHAVIOR_DIFF_CODEX_ISOLATION_ROOT:-}" ]; then
    isolation_args=(exec --workspace "$PWD" --root "$BEHAVIOR_DIFF_CODEX_ISOLATION_ROOT" --model "$model")
    if [ -n "${BEHAVIOR_DIFF_CODEX_DENY_READ:-}" ]; then
      isolation_args+=(--deny-read "$BEHAVIOR_DIFF_CODEX_DENY_READ")
    fi
    printf '%s\n' "$task" |
      python3 "$scripts/codex_isolated.py" "${isolation_args[@]}" \
        >"$trace_dir/codex-raw.jsonl" 2>"$trace_dir/stderr.log" || cli_exit=${PIPESTATUS[1]}
  else
    # Codex has no per-tool allowlist; use its normal workspace-write sandbox.
    codex exec --ephemeral --skip-git-repo-check -s workspace-write \
      -m "$model" --json "$task" </dev/null >"$trace_dir/codex-raw.jsonl" 2>"$trace_dir/stderr.log" || cli_exit=$?
  fi
  record_status "{\"phase\":\"normalizing\",\"cli_exit_code\":$cli_exit}"
  jq -c 'select(.type == "item.completed"
                and (.item.item_type // .item.type) == "command_execution")
         | {type: "assistant", message: {content: [{type: "tool_use",
            id: .item.id, name: "Bash", input: {command:
              (.item.command // "" | sub("^/bin/[a-zA-Z]+ -lc "; "")),
              raw_command: (.item.command // "")}}]}},
           {type: "user", message: {content: [{type: "tool_result",
            tool_use_id: .item.id, content: (.item.aggregated_output // null),
            is_error: ((.item.exit_code // 0) != 0)}]}}' \
    "$trace_dir/codex-raw.jsonl" >"$trace_dir/trace.jsonl"
  jq -s -c '[.[] | select(.type == "item.completed"
                          and (.item.item_type // .item.type) == "agent_message")
             | .item.text]
            | {type: "result", result: (last // "")}' \
    "$trace_dir/codex-raw.jsonl" >>"$trace_dir/trace.jsonl"
elif [ "$agent" = omp ]; then
  # PIPESTATUS separates the host CLI's exit from the task writer's.
  printf '%s\n' "$task" | omp -p \
    --mode json --no-session --no-title --cwd "$dir" \
    --model "$model" --tools read,bash,grep,glob \
    --approval-mode yolo \
    --config "$scripts/omp-isolation.json" \
    >"$trace_dir/omp-raw.jsonl" 2>"$trace_dir/stderr.log" || cli_exit=${PIPESTATUS[1]}
  record_status "{\"phase\":\"normalizing\",\"cli_exit_code\":$cli_exit}"
  normalize_pi_omp_json "$trace_dir/omp-raw.jsonl"
else
  printf '%s\n' "$task" |
    PI_SKIP_VERSION_CHECK=1 PI_TELEMETRY=0 \
      pi -p --mode json --no-session --model "$model" \
      --tools read,bash,grep,find,ls \
      >"$trace_dir/pi-raw.jsonl" 2>"$trace_dir/stderr.log" || cli_exit=${PIPESTATUS[1]}
  record_status "{\"phase\":\"normalizing\",\"cli_exit_code\":$cli_exit}"
  normalize_pi_omp_json "$trace_dir/pi-raw.jsonl"
fi
