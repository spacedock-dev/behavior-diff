#!/usr/bin/env bash
set -euo pipefail

here=$(cd "$(dirname "$0")" && pwd -P)
skill=$here/../plugin/skills/behavior-diff-live/SKILL.md
renderer=$here/../plugin/skills/behavior-diff/scripts/render.py
decisions=$here/../plugin/skills/behavior-diff/scripts/decisions.py
claude_manifest=$here/../plugin/.claude-plugin/plugin.json
codex_manifest=$here/../plugin/.codex-plugin/plugin.json
readme=$here/../README.md

require_output() {
  grep -qF -- "$1" "$2" || fail "$3"
}
reject_output() {
  if grep -qF -- "$1" "$2"; then
    fail "$3"
  fi
}
require_order_after() {
  local marker=$1
  local first=$2
  local second=$3
  local file=$4
  local message=$5
  local content
  content=$(cat "$file")
  case $content in
    *"$marker"*"$first"*"$second"*) ;;
    *) fail "$message" ;;
  esac
}

tmp=$(mktemp -d "${TMPDIR:-/tmp}/behavior-diff-live-contract.XXXXXX")
trap 'rm -rf "$tmp"' EXIT

build_run() {
  local run=$1
  local trace_source=$2
  mkdir -p "$run"/{before-1,after-1}/project

  cat >"$run/before-1/trace.jsonl" <<'JSON'
{"type":"assistant","message":{"content":[{"type":"tool_use","name":"Bash","input":{"command":"Read: AGENTS.md"}}]}}
{"type":"result","result":"Before answer"}
JSON
  cat >"$run/after-1/trace.jsonl" <<'JSON'
{"type":"assistant","message":{"content":[{"type":"tool_use","name":"Bash","input":{"command":"Read: AGENTS.md"}}]}}
{"type":"assistant","message":{"content":[{"type":"tool_use","name":"Bash","input":{"command":"Test: bash behavior-diff/tests/live-report-contract.sh"}}]}}
{"type":"result","result":"After answer"}
JSON
  printf '%s\n' 'Original project instructions.' \
    >"$run/before-1/project/AGENTS.md"
  printf '%s\n' 'Updated project instructions.' \
    >"$run/after-1/project/AGENTS.md"
  printf '%s\n' $'before-1\tREVIEW\t-' $'after-1\tREVIEW\t-' \
    >"$run/grades.tsv"
  printf '%s\n' 'Compare the two instruction snapshots.' >"$run/task.md"
  cat >"$run/decisions.json" <<'JSON'
{"chain":[{"topic":"Evidence choice","decision":"Which evidence was used?","anchor":"work","before":[{"choice":"read only","n":1}],"after":[{"choice":"read and test","n":1}],"diverges":true}],"fork":1,"fork_note":"Synthetic fixture.","counts":{"before":1,"after":1}}
JSON

  if [[ $trace_source == self-reported ]]; then
    cat >"$run/config.json" <<'JSON'
{"title":"Live contract","sub":"Synthetic contract fixture.","expected":null,"target_file":"AGENTS.md","mode":"review","vocab":"generic","trace_source":"self-reported","before_label":"parent snapshot <baseline>","after_label":"target snapshot <candidate>"}
JSON
  else
    cat >"$run/config.json" <<'JSON'
{"title":"Live contract","sub":"Synthetic contract fixture.","expected":null,"target_file":"AGENTS.md","mode":"review","vocab":"generic"}
JSON
  fi
}

fail() {
  printf 'FAIL: %s\n' "$1" >&2
  exit 1
}
require_fixed() { grep -qF -- "$1" "$skill" || fail "$2"; }
[[ $(jq -r '.version' "$claude_manifest") == 0.3.1 ]] ||
  fail 'Claude manifest version is not 0.3.1'
[[ $(jq -r '.version' "$codex_manifest") == 0.3.1 ]] ||
  fail 'Codex manifest version is not 0.3.1'
require_output '## Hooks: the nudge (0.3.1)' "$readme" \
  'README Hooks heading version is not 0.3.1'

require_fixed 'one numbered line per tool action' \
  'missing action contract: one numbered line per tool action'
require_fixed 'Never group several actions on one line.' \
  'missing action contract: grouped actions are not forbidden'
require_fixed 'every task tool action completed before report delivery' \
  'missing pre-delivery action boundary'
require_fixed "Do not include the final delivery SendMessage in \`ACTIONS\`." \
  'missing final delivery exclusion'
require_fixed '"trace_source": "self-reported"' \
  'missing trace source contract'
require_fixed '"before_label": "current file"' \
  'missing default before label contract'
require_fixed '"after_label": "your change applied"' \
  'missing default after label contract'
require_fixed 'raw-actions-and-final-answers report' \
  'failed extraction does not fall back to raw actions and final answers'
require_fixed 'Do not invent a flow.' \
  'failed extraction fallback does not forbid an invented flow'
reject_output 'flow-diff-only report' "$skill" \
  'stale flow-diff-only fallback remains in the live skill'
require_fixed 'If decision extraction succeeded, use the flow-diff shape' \
  'successful extraction summary lost its flow-diff shape'
require_fixed 'If decision extraction was skipped after two failed attempts' \
  'failed extraction summary is not conditional'
require_fixed 'summarize each side'\''s ordered self-reported actions' \
  'failed extraction summary does not preserve ordered actions'
require_fixed 'quote both final answers, and repeat the visible extractor-skip note' \
  'failed extraction summary does not repeat answers and skip note'
reject_output '7. **Summarize in conversation** in the flow-diff shape' "$skill" \
  'step 7 still requires a flow when extraction failed'

decision_match=$(grep -nF -- 'Then extract the decision diff' "$skill") ||
  fail 'missing decision extraction marker'
render_match=$(grep -nF -- "Then run \`scripts/render.py\`" "$skill") ||
  fail 'missing render marker'
open_match=$(grep -nF -- "immediately \`open\` the report.html" "$skill") ||
  fail 'missing open marker'

decision_line=${decision_match%%:*}
render_line=${render_match%%:*}
open_line=${open_match%%:*}

((decision_line < render_line)) ||
  fail 'decision extraction must precede render'
((render_line <= open_line)) ||
  fail 'render must not follow open'

self_run=$tmp/self-reported
captured_run=$tmp/captured
build_run "$self_run" self-reported
build_run "$captured_run" captured
self_prompt=$tmp/self-prompt.txt
captured_prompt=$tmp/captured-prompt.txt
python3 "$decisions" "$self_run" --emit-prompt >"$self_prompt"
python3 "$decisions" "$captured_run" --emit-prompt >"$captured_prompt"
require_output 'self-reported actions' "$self_prompt" \
  'self-reported decision prompt does not identify its evidence source'
require_output 'action number' "$self_prompt" \
  'self-reported decision prompt does not use action-number anchors'
require_output 'reported actions:' "$self_prompt" \
  'self-reported decision prompt does not label reported action entries'
reject_output 'commands it ran' "$self_prompt" \
  'self-reported decision prompt claims its actions are captured commands'
reject_output 'actually did' "$self_prompt" \
  'self-reported decision prompt claims reported actions actually happened'
require_output \
  'A decision is not an action; some decisions leave no action' \
  "$self_prompt" 'self-reported prompt lost its action evidence noun'
reject_output 'A decision is not a command' "$self_prompt" \
  'self-reported prompt uses the captured command evidence noun'

require_output 'captured tool calls' "$captured_prompt" \
  'captured decision prompt does not identify its evidence source'
require_output 'command number' "$captured_prompt" \
  'captured decision prompt does not use command-number anchors'
require_output 'commands it ran:' "$captured_prompt" \
  'captured decision prompt does not label captured command entries'
require_output 'actually did and said' "$captured_prompt" \
  'captured decision prompt lost its performed-action evidence clause'
reject_output 'self-reported' "$captured_prompt" \
  'captured decision prompt uses self-reported source wording'
require_output \
  'A decision is not a command; some decisions leave no command' \
  "$captured_prompt" 'captured prompt lost its command evidence noun'
reject_output 'A decision is not an action' "$captured_prompt" \
  'captured prompt uses self-reported action wording'

python3 "$renderer" "$self_run" "$self_run" contract \
  "$self_run/config.json" >/dev/null
python3 "$renderer" "$captured_run" "$captured_run" contract \
  "$captured_run/config.json" >/dev/null

read_action='Read: AGENTS.md'
test_action='Test: bash behavior-diff/tests/live-report-contract.sh'

for report in "$self_run/report.md" "$self_run/report.html"; do
  require_output 'self-reported actions' "$report" \
    "self-reported report does not label its evidence as self-reported actions: $report"
  reject_output 'actual commands' "$report" \
    "self-reported report claims to contain actual commands: $report"
  reject_output 'command-derived' "$report" \
    "self-reported report includes command-derived flow: $report"
  require_output "$read_action" "$report" \
    "self-reported report dropped the read action: $report"
  require_output "$test_action" "$report" \
    "self-reported report dropped the test action: $report"
  reject_output "\$ $read_action" "$report" \
    "self-reported read action has a shell prompt prefix: $report"
  reject_output "\$ $test_action" "$report" \
    "self-reported test action has a shell prompt prefix: $report"
  require_output \
    'No automatic verdict — compare the reported actions, decision diff, and final answers' \
    "$report" "self-reported report directs readers to removed flows: $report"
  reject_output 'No automatic verdict — compare the flows and final answers' \
    "$report" "self-reported report kept the captured-mode result: $report"
  require_output \
    'The decisions come from self-reported actions and final answers.' \
    "$report" "self-reported decision blurb does not disclose its evidence: $report"
  require_output 'Extractor output can vary from run to run.' "$report" \
    "self-reported decision blurb claims deterministic extraction: $report"
  reject_output 'stable across extractions' "$report" \
    "self-reported report claims extractor output is stable: $report"
  require_output 'Decision diff — top divergences' "$report" \
    "self-reported report dropped the decision diff: $report"
  case $report in
    *.md)
      after_marker='## AFTER — target snapshot <candidate>'
      require_output 'parent snapshot <baseline>' "$report" \
        "self-reported Markdown changed the literal before label: $report"
      require_output 'target snapshot <candidate>' "$report" \
        "self-reported Markdown changed the literal after label: $report"
      ;;
    *)
      after_marker='<h2>After</h2>'
      require_output 'parent snapshot &lt;baseline&gt;' "$report" \
        "self-reported HTML did not escape the before label: $report"
      require_output 'target snapshot &lt;candidate&gt;' "$report" \
        "self-reported HTML did not escape the after label: $report"
      reject_output 'parent snapshot <baseline>' "$report" \
        "self-reported HTML contains an unescaped before label: $report"
      reject_output 'target snapshot <candidate>' "$report" \
        "self-reported HTML contains an unescaped after label: $report"
      ;;
  esac
  require_order_after "$after_marker" "$read_action" "$test_action" "$report" \
    "self-reported actions are not preserved in order: $report"
done

for report in "$captured_run/report.md" "$captured_run/report.html"; do
  require_output 'actual commands' "$report" \
    "captured report lost its actual commands wording: $report"
  require_output 'command-derived' "$report" \
    "captured report lost its command-derived flow: $report"
  require_output "$read_action" "$report" \
    "captured report dropped the raw read command: $report"
  require_output "$test_action" "$report" \
    "captured report dropped the raw test command: $report"
  require_output 'Before answer' "$report" \
    "captured report dropped the before final answer: $report"
  require_output 'After answer' "$report" \
    "captured report dropped the after final answer: $report"
  require_output 'current file' "$report" \
    "captured report lost the default before label: $report"
  require_output 'your change applied' "$report" \
    "captured report lost the default after label: $report"
  require_output 'No automatic verdict — compare the flows and final answers' \
    "$report" "captured report changed its review result: $report"
  reject_output \
    'No automatic verdict — compare the reported actions, decision diff, and final answers' \
    "$report" "captured report used the self-reported review result: $report"
  require_output \
    'The fork and main divergences are stable across extractions; minor rows can vary run to run.' \
    "$report" "captured report changed its extraction stability wording: $report"
  case $report in
    *.md)
      after_marker='## AFTER — your change applied'
      reject_output "\$ $read_action" "$report" \
        "captured Markdown added a read command prompt prefix: $report"
      reject_output "\$ $test_action" "$report" \
        "captured Markdown added a test command prompt prefix: $report"
      require_order_after 'Flow diff — command-derived' 'Divergence:' \
        'AFTER, all 1 trials → Run tests' "$report" \
        "captured Markdown lost the classified flow divergence: $report"
      ;;
    *)
      after_marker='<h2>After</h2>'
      require_output "\$ $read_action" "$report" \
        "captured HTML lost the read command prompt prefix: $report"
      require_output "\$ $test_action" "$report" \
        "captured HTML lost the test command prompt prefix: $report"
      require_order_after 'Flow diff — command-derived' 'paths diverge here' \
        'Run tests' "$report" \
        "captured HTML lost the classified flow divergence: $report"
      ;;
  esac
  require_order_after "$after_marker" "$read_action" "$test_action" "$report" \
    "captured commands are not preserved in order: $report"
done

printf '%s\n' '{"trace_source":"invented"}' >"$tmp/invalid-config.json"
if python3 "$renderer" "$captured_run" "$captured_run" contract \
  "$tmp/invalid-config.json" >"$tmp/invalid-output.txt" \
  2>"$tmp/invalid-error.txt"; then
  fail 'renderer accepts an invalid trace_source'
fi
require_output 'trace_source must be either "captured" or "self-reported"' \
  "$tmp/invalid-error.txt" 'renderer omits the trace-source provenance error'

printf '%s\n' '{"trace_source":null}' >"$tmp/null-source-config.json"
if python3 "$renderer" "$captured_run" "$captured_run" contract \
  "$tmp/null-source-config.json" >/dev/null 2>&1; then
  fail 'renderer accepts a malformed trace_source'
fi

printf '%s\n' '{' >"$tmp/malformed-config.json"
if python3 "$renderer" "$captured_run" "$captured_run" contract \
  "$tmp/malformed-config.json" >/dev/null 2>&1; then
  fail 'renderer accepts malformed config JSON'
fi

printf '%s\n' '{"trace_source":"invented"}' \
  >"$captured_run/config.json"
if python3 "$decisions" "$captured_run" --emit-prompt \
  >"$tmp/invalid-emit-output.txt" 2>"$tmp/invalid-emit-error.txt"; then
  fail 'decision prompt accepts an invalid trace_source'
fi
require_output 'trace_source must be either "captured" or "self-reported"' \
  "$tmp/invalid-emit-error.txt" \
  'decision prompt omits the trace-source provenance error'

printf '%s\n' 'ok — live report contract passed'
