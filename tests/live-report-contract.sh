#!/usr/bin/env bash
set -euo pipefail

here=$(cd "$(dirname "$0")" && pwd -P)
skill=$here/../plugin/skills/behavior-diff-live/SKILL.md
headless_skill=$here/../plugin/skills/behavior-diff/SKILL.md
demo_skill=$here/../.agents/skills/run-behavior-diff-demo-journey/SKILL.md
spacedock_reference=$here/../plugin/skills/behavior-diff/references/spacedock-duo.md
spacedock_fixture_script=$here/../plugin/skills/behavior-diff/scripts/make-spacedock-fixtures.sh
legacy_spacedock_fixture_script=$here/../plugin/skills/behavior-diff/scripts/make-capsule.sh
e2e_readme=$here/../e2e/README.md
nudge_script=$here/nudge-e2e.sh
renderer=$here/../plugin/skills/behavior-diff/scripts/render.py
decisions=$here/../plugin/skills/behavior-diff/scripts/decisions.py
claude_manifest=$here/../plugin/.claude-plugin/plugin.json
codex_manifest=$here/../plugin/.codex-plugin/plugin.json
readme=$here/../README.md

fixture_root=$here/fixtures/report-rendering
update_report_fixtures=false
require_output() {
  grep -qF -- "$1" "$2" || fail "$3"
}
require_line() {
  grep -qxF -- "$1" "$2" || fail "$3"
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
require_definition_at_first_use() {
  local file=$1
  local message=$2
  local first_use
  local definition
  first_use=$(grep -nF -- 'Spacedock fixtures' "$file" |
    sed -n '1s/:.*//p' || true)
  definition=$(grep -nE -- \
    'Spacedock fixtures.*isolated.*before/after.*test repo' "$file" |
    sed -n '1s/:.*//p' || true)
  if [[ -z $first_use || -z $definition ]] ||
    ((definition < first_use || definition > first_use + 1)); then
    fail "$message"
  fi
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
progress() {
  printf '[report] %s\n' "$1"
}

usage() {
  printf 'Usage: %s [--update-report-fixtures]\n' "$0" >&2
  exit 2
}

copy_report_fixtures() {
  local mode=$1
  local run=$2
  local fixture_dir=$fixture_root/$mode

  mkdir -p "$fixture_dir"
  cp "$run/report.md" "$fixture_dir/report.md"
  cp "$run/report.html" "$fixture_dir/report.html"
  cp "$run/report-artifact.html" "$fixture_dir/report-artifact.html"
}

require_exact_report() {
  local mode=$1
  local report=$2
  local fixture
  fixture=$fixture_root/$mode/$(basename "$report")

  if ! cmp -s "$fixture" "$report"; then
    printf 'Rendered report differs from fixture: %s\n' "$fixture" >&2
    if diff -u "$fixture" "$report" >&2; then
      fail "rendered report comparison failed unexpectedly: $report"
    else
      fail "rendered report differs from fixture: $report"
    fi
  fi
}

case $# in
  0) ;;
  1)
    [[ $1 == --update-report-fixtures ]] || usage
    update_report_fixtures=true
    ;;
  *) usage ;;
esac

require_usage() {
  local stderr=$tmp/usage-stderr.txt
  local stdout=$tmp/usage-stdout.txt
  local expected=$tmp/usage-expected.txt
  local status

  if bash "$0" "$@" >"$stdout" 2>"$stderr"; then
    fail "invalid arguments succeeded: $*"
  else
    status=$?
  fi
  [[ $status == 2 ]] || fail "invalid arguments returned $status instead of 2: $*"
  [[ ! -s $stdout ]] || fail "invalid arguments wrote to stdout: $*"
  printf 'Usage: %s [--update-report-fixtures]\n' "$0" >"$expected"
  cmp -s "$expected" "$stderr" ||
    fail "invalid arguments did not print the exact usage diagnostic: $*"
}

require_usage --unknown-option
require_usage --update-report-fixtures surplus
python3 "$here/report-schema-test.py"

progress 'Validate manifests and live-skill reporting contract'
[[ -x $spacedock_fixture_script ]] ||
  fail 'renamed Spacedock fixture builder is missing or not executable'
[[ ! -e $legacy_spacedock_fixture_script ]] ||
  fail 'legacy make-capsule.sh path still exists'
require_output 'Usage: make-spacedock-fixtures.sh' \
  "$spacedock_fixture_script" \
  'fixture builder help still uses the legacy name'
require_output 'make-spacedock-fixtures:' "$spacedock_fixture_script" \
  'fixture builder diagnostics still use the legacy name'
require_output 'FIXTURES OK' "$spacedock_fixture_script" \
  'fixture builder does not produce the documented validation signal'
reject_output 'make-capsule' "$spacedock_fixture_script" \
  'fixture builder still uses the legacy script name'
reject_output 'CAPSULE' "$spacedock_fixture_script" \
  'fixture builder still uses the legacy validation name'
require_definition_at_first_use "$headless_skill" \
  'headless skill does not define Spacedock fixtures at first use'
require_output '`make-spacedock-fixtures.sh`' "$headless_skill" \
  'headless skill does not name the fixture builder'
require_definition_at_first_use "$skill" \
  'live skill does not define Spacedock fixtures at first use'
require_output '`make-spacedock-fixtures.sh`' "$skill" \
  'live skill does not name the fixture builder'
require_output 'Hand-built files can contain state' "$spacedock_reference" \
  'Spacedock reference does not name the hand-built state risk'
require_output 'Spacedock itself would never create' "$spacedock_reference" \
  'Spacedock reference does not explain why hand-built fixtures are unsafe'
require_output 'FIXTURES OK' "$spacedock_reference" \
  'Spacedock reference does not name the fixture validation signal'
reject_output 'capsule' "$headless_skill" \
  'headless skill still uses the unexplained capsule term'
reject_output 'capsule' "$skill" \
  'live skill still uses the unexplained capsule term'
reject_output 'capsule' "$spacedock_reference" \
  'Spacedock reference still uses the unexplained capsule term'
require_fixed() { grep -qF -- "$1" "$skill" || fail "$2"; }
require_output 'The skill owns judgment.' "$headless_skill" \
  'headless skill does not state its judgment ownership'
require_output 'The scripts own repeatable mechanics.' "$headless_skill" \
  'headless skill does not state script ownership'
require_output '--agent pi' "$headless_skill" \
  'headless skill does not name the Pi trial stack'
require_output '<exact-current-pi-model>' "$headless_skill" \
  'headless skill does not require the exact Pi model'
require_output '--agent omp' "$headless_skill" \
  'headless skill does not name the OMP trial stack'
require_output '<exact-current-omp-model>' "$headless_skill" \
  'headless skill does not require the exact OMP model'
require_output 'Pi has no built-in subagent dispatch.' "$skill" \
  'live skill invents a built-in Pi dispatch path'
require_output 'one `task` batch' "$skill" \
  'live skill does not use one OMP task batch'
require_output 'Results return to the parent automatically.' "$skill" \
  'live skill does not explain OMP result delivery'
require_output 'decision diff skipped: host has no subagent dispatch' "$skill" \
  'live skill has no honest Codex no-dispatch extraction path'
require_output 'claude, codex, pi, or omp' "$claude_manifest" \
  'Claude manifest does not name all trial stacks'
require_output 'claude, codex, pi, or omp' "$codex_manifest" \
  'Codex manifest does not name all trial stacks'
require_output 'Pi and OMP are trial stacks, not plugin hosts' "$readme" \
  'README does not separate trial stacks from plugin hosts'
require_output 'Run it as soon as the task is known.' "$headless_skill" \
  'headless skill does not start the default run immediately'
require_output 'Only add `--fast` when the user explicitly requested it' \
  "$headless_skill" \
  'headless skill does not reserve fast mode for explicit requests'
require_output 'Do not mention trial counts, cost' "$headless_skill" \
  'headless skill still exposes run counts or cost to the user'
require_output 'full versus fast modes' "$headless_skill" \
  'headless skill still exposes implementation modes to the user'
reject_output 'Confirm before running' "$headless_skill" \
  'headless skill still asks for run confirmation'
reject_output 'plus the cost:' "$headless_skill" \
  'headless skill still advertises model-run cost'
require_line '       behavior-diff.sh --agent <current-host> --file <file> --task "<task>"' \
  "$headless_skill" \
  'default command does not preserve the current agent host'
require_line '       behavior-diff.sh --agent <current-host> --file <file> --task "<task>" --fast' \
  "$headless_skill" \
  'explicit fast command does not preserve the current agent host'
require_output 'Run behavior-diff with this exact task:' "$demo_skill" \
  'demo journey does not supply the exact fixture task with the nudge response'
require_output 'the exact task step 1 printed' "$demo_skill" \
  'demo journey does not reuse the harness task'
reject_output 'Tell the user the cost before starting' "$demo_skill" \
  'demo journey still adds a cost confirmation'
reject_output 'choose `--fast`' "$demo_skill" \
  'demo journey still offers fast mode by default'
reject_output 'states its cost' "$e2e_readme" \
  'e2e guide still expects a separate model-cost gate'
reject_output 'The rule is meant to affect this later request.' \
  "$nudge_script" \
  'nudge setup prompt still inlines the later task into the edit turn'
require_output 'take that session out of auto mode' "$nudge_script" \
  'nudge setup does not tell the claude operator to leave auto mode'
require_output 'no mode to turn off here' "$nudge_script" \
  'nudge setup has no codex counterpart for the auto-mode precaution'
require_output 'Run behavior-diff with this exact task:' "$nudge_script" \
  'nudge setup does not accept behavior-diff with the exact task'
reject_output 'At its run gate' "$nudge_script" \
  'nudge setup still expects a later confirmation gate'
nudge_setup=$tmp/nudge-setup.txt
NUDGE_E2E_FIXTURE=demo-ascii-response \
  NUDGE_E2E_REPO=$tmp/nudge-repo \
  NUDGE_E2E_STATE=$tmp/nudge-state \
  "$nudge_script" setup >"$nudge_setup"
expected_task=$(sed 's/^/       /' \
  "$here/../e2e/demo-ascii-response/task.md")
edit_section=$(sed -n \
  '/2\. Journey A/,/Expect the agent to ask/p' "$nudge_setup")
# A renamed heading would empty this range and pass the negative check below
# without reading anything, so anchor it first.
[[ -n $edit_section ]] ||
  fail 'rendered edit-prompt section not found — range markers drifted'
case $edit_section in
  *"$expected_task"*) fail 'rendered edit prompt still inlines the task' ;;
esac
accept_section=$(sed -n \
  '/To carry the journey into behavior-diff/,/3\. Assert/p' "$nudge_setup")
case $accept_section in
  *"$expected_task"*) ;;
  *) fail 'rendered nudge acceptance does not include the full fixture task' ;;
esac

[[ $(jq -r '.version' "$claude_manifest") == 0.3.2 ]] ||
  fail 'Claude manifest version is not 0.3.2'
[[ $(jq -r '.version' "$codex_manifest") == 0.3.2 ]] ||
  fail 'Codex manifest version is not 0.3.2'

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
require_fixed 'If decision extraction was skipped because the host has no subagent' \
  'no-dispatch extraction summary is not conditional'
require_fixed 'dispatch or after two failed attempts' \
  'failed extraction summary is not conditional'
require_fixed 'summarize each side'\''s ordered self-reported actions' \
  'failed extraction summary does not preserve ordered actions'
require_fixed 'quote both final answers, and repeat the visible extractor-skip note' \
  'failed extraction summary does not repeat answers and skip note'
reject_output '7. **Summarize in conversation** in the flow-diff shape' "$skill" \
  'step 7 still requires a flow when extraction failed'

decision_match=$(grep -nF -- 'On hosts with dispatch, extract the decision diff' "$skill") ||
  fail 'missing conditional decision extraction marker'
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

progress 'Build captured and self-reported decision prompts'

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

progress 'Render captured and self-reported reports'

python3 "$renderer" "$self_run" "$self_run" contract \
  "$self_run/config.json" >"$self_run/render.stdout"
self_run_path=$(cd "$self_run" && pwd -P)
if ! printf '%s\n' \
  'mode review · BEFORE pass 0/1 · AFTER pass 0/1 → No automatic verdict — compare the reported actions, decision diff, and final answers' \
  "report: $self_run_path/report.md" \
  "page:   $self_run_path/report.html" |
  cmp -s - "$self_run/render.stdout"; then
  fail 'renderer stdout changed'
fi
python3 "$renderer" "$captured_run" "$captured_run" contract \
  "$captured_run/config.json" >/dev/null
if [[ $update_report_fixtures == true ]]; then
  copy_report_fixtures captured "$captured_run"
  copy_report_fixtures self-reported "$self_run"
fi

for run in "$self_run" "$captured_run"; do
  [[ -f $run/report-data.json ]] ||
    fail "renderer did not write report-data.json: $run"
  python3 "$here/report-schema-test.py" "$run/report-data.json"
done

[[ $(jq -r '.schema_version' "$captured_run/report-data.json") == 1 ]] ||
  fail 'captured report data schema version is not 1'
[[ $(jq -r '.metadata.trace_source' "$captured_run/report-data.json") == captured ]] ||
  fail 'captured report data provenance is not captured'
[[ $(jq -r '.metadata.trace_source' "$self_run/report-data.json") == self-reported ]] ||
  fail 'self-reported report data provenance is not self-reported'
[[ $(jq -r '.variants.after.trials[0].commands | join("|")' "$captured_run/report-data.json") == 'Read: AGENTS.md|Test: bash behavior-diff/tests/live-report-contract.sh' ]] ||
  fail 'report data does not preserve after commands in order'
[[ $(jq -r '.command_flow.enabled == false and (.command_flow.shared | length == 0) and (.command_flow.before.prefix | length == 0) and (.command_flow.before.paths | length == 0) and (.command_flow.after.prefix | length == 0) and (.command_flow.after.paths | length == 0)' "$self_run/report-data.json") == true ]] ||
  fail 'self-reported report data must disable and empty command flow'

graded_run=$tmp/graded
build_run "$graded_run" captured
python3 "$renderer" "$graded_run" "$graded_run" contract >/dev/null
require_output '**0 of 1 valid trials met the expectation** (blocked: 0)' \
  "$graded_run/report.md" \
  'graded Markdown count must emphasize only the expectation result'

invalid_decisions_run=$tmp/invalid-decisions
build_run "$invalid_decisions_run" captured
printf '%s\n' '{"chain":[{"decision":"Synthetic decision","topic":"","anchor":"work","before":[{"choice":"before","n":1}],"after":[{"choice":"after","n":1}],"diverges":true}],"fork":2,"counts":{"before":1,"after":1}}' \
  >"$invalid_decisions_run/decisions.json"
cat >"$invalid_decisions_run/before-1/trace.jsonl" <<'JSON'
{"type":"assistant","message":{"content":[{"type":"tool_use","name":"Bash","input":{"command":"Read: AGENTS.md"}}]}}
[]
{"type":"assistant","message":[]}
{"type":"assistant","message":{"content":[null,{"type":"tool_use","input":null},{"type":"tool_use","input":{"command":17}},{"type":"tool_use","name":17,"input":{"file_path":"AGENTS.md"}}]}}
{"type":"result","result":"Before answer"}
JSON
python3 "$renderer" "$invalid_decisions_run" "$invalid_decisions_run" contract \
  "$invalid_decisions_run/config.json" >/dev/null
[[ $(jq '.decisions.rows | length' "$invalid_decisions_run/report-data.json") == 0 ]] ||
  fail 'out-of-range decision fork must fall back to empty decisions'

for report in report.md report.html report-artifact.html; do
  require_exact_report captured "$captured_run/$report"
  require_exact_report self-reported "$self_run/$report"
done

read_action='Read: AGENTS.md'
test_action='Test: bash behavior-diff/tests/live-report-contract.sh'

progress 'Validate self-reported wording, escaping, and action order'

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

progress 'Validate captured flow, labels, and command order'

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

progress 'Reject invalid provenance and malformed configuration'

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
