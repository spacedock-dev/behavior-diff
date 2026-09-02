#!/usr/bin/env bash
# E2E harness for the rules-edit nudge hooks (PostToolUse detect + Stop remind).
#
# hooks-test.sh already covers the hook logic with synthetic payloads. This
# harness drives the seams only a live agent session owns: that the plugin's
# hooks are wired at all, that the whisper reaches the agent, that the agent
# asks, and that the Stop line renders. It sets up an isolated sandbox and
# asserts the state a real session leaves behind; the session itself is run by
# the operator.
#
#   nudge-e2e.sh setup          sandbox repo + isolated state, prints the prompt
#   nudge-e2e.sh check          assert the nudge state left by the last turn
#   nudge-e2e.sh drop-whisper   remove the whisper marker (arms the Stop line)
#   nudge-e2e.sh reset          delete the sandbox
#
# Override paths with NUDGE_E2E_REPO / NUDGE_E2E_STATE. Both are deleted by
# setup and reset, so each must carry the sandbox marker written at setup.
#
# NUDGE_E2E_AGENT picks which agent runs the session: claude (default,
# sonnet) or codex (gpt-5.6-terra). Both stacks carry the nudge hooks, and
# the ask rate is a property of the agent, so the journey is worth running
# on each. NUDGE_E2E_MODEL overrides the model for either.
#
# The defaults are the common ones on purpose: a whisper the everyday model
# ignores is the result that matters, and the hook wiring under test does
# not need a larger model.
#
# NUDGE_E2E_FIXTURE picks what the sandbox contains:
#   capsule (default)  rk-monitor — the harder case, for testing
#   demo               pricer — a bug anyone understands in one sentence,
#                      where the before-answer is wrong rather than just
#                      worded differently, for showing someone the report
#   demo-inbox-cleanup inbox cleanup — a non-developer backup where one
#                      broader rule archives both a routine update and an
#                      important cancellation notice
#   demo-invoice-review invoice review — a non-developer decision case where
#                      a quick-review shortcut may skip payment history
#   demo-ascii-response reminder emails — the vague-rule demo: one line
#                      with no trigger point ("use ASCII to visualize"),
#                      where the flows stay identical and the answer
#                      gains a drawn timeline
set -euo pipefail

repo=${NUDGE_E2E_REPO:-/tmp/nudge-e2e}
state=${NUDGE_E2E_STATE:-/tmp/nudge-e2e-state}
agent=${NUDGE_E2E_AGENT:-claude}
case $agent in
  claude) session_cmd="claude --model ${NUDGE_E2E_MODEL:-sonnet}" ;;
  codex)  session_cmd="codex -m ${NUDGE_E2E_MODEL:-gpt-5.6-terra}" ;;
  *) printf 'nudge-e2e: NUDGE_E2E_AGENT must be claude or codex: %s\n' \
       "$agent" >&2; exit 2 ;;
esac
fixture=${NUDGE_E2E_FIXTURE:-capsule}
here=$(cd -- "$(dirname -- "$0")" && pwd -P)
case $fixture in
  capsule)
    fixture_dir=$here/../e2e/$fixture
    instruction_file=CLAUDE.md
    ;;
  demo | demo-inbox-cleanup | demo-invoice-review | demo-ascii-response)
    fixture_dir=$here/../e2e/$fixture
    instruction_file=AGENTS.md
    ;;
  *) printf 'nudge-e2e: unknown NUDGE_E2E_FIXTURE: %s\n' \
       "$fixture" >&2; exit 2 ;;
esac
capsule=$fixture_dir/project
nudge=$state/nudge
marker=.nudge-e2e-sandbox
failures=0

die() { printf 'nudge-e2e: %s\n' "$1" >&2; exit 2; }
pass() { printf '  ok    %s\n' "$1"; }
fail() { printf '  FAIL  %s\n' "$1" >&2; failures=$((failures + 1)); }
info() { printf '  --    %s\n' "$1"; }

usage() {
  cat >&2 <<'EOF'
usage: nudge-e2e.sh setup | check | drop-whisper | reset
  setup          sandbox repo + isolated state, prints the prompt
  check          assert the nudge state left by the last turn
  drop-whisper   remove the whisper marker (arms the Stop line)
  reset          delete the sandbox
EOF
  exit 2
}

# rm -rf targets come from the environment, so refuse anything that is not an
# absolute path we created ourselves and marked.
check_sandbox_path() {
  local path=$1 name=$2
  [[ -n $path ]] || die "$name is empty"
  [[ $path == /* ]] || die "$name must be an absolute path: $path"
  case $path in
    / | "$HOME" | "$HOME"/) die "$name refuses to target $path" ;;
  esac
}

remove_sandbox() {
  local path=$1 name=$2
  check_sandbox_path "$path" "$name"
  [[ -e $path ]] || return 0
  [[ -f $path/$marker ]] ||
    die "$path exists but has no $marker — refusing to delete a directory this harness did not create"
  rm -rf -- "$path"
}

# Newest match for a glob, or empty. Bash 3.2 has no nullglob by default here,
# so an unmatched pattern comes back as the literal pattern and is filtered.
newest() {
  local pattern=$1 found='' f
  for f in $pattern; do
    [[ -e $f ]] || continue
    if [[ -z $found || $f -nt $found ]]; then found=$f; fi
  done
  printf '%s' "$found"
}

cmd_setup() {
  command -v git >/dev/null 2>&1 || die "git is required"
  [[ -d $capsule ]] || die "$fixture fixture missing: $capsule"
  [[ -f $capsule/$instruction_file ]] ||
    die "$fixture instruction file missing: $capsule/$instruction_file"
  [[ -f $fixture_dir/rule.md ]] || die "$fixture rule.md is missing"
  [[ -f $fixture_dir/task.md ]] || die "$fixture task.md is missing"
  if [[ $instruction_file == AGENTS.md ]] &&
     ! grep -qxF -- '@AGENTS.md' "$capsule/CLAUDE.md"; then
    die "$fixture CLAUDE.md must import canonical AGENTS.md"
  fi
  remove_sandbox "$repo" NUDGE_E2E_REPO
  remove_sandbox "$state" NUDGE_E2E_STATE
  mkdir -p -- "$repo" "$nudge"
  : > "$repo/$marker"
  : > "$state/$marker"

  # A concrete fixture, not an abstract prompt. The journey only produces a
  # useful diff if the rule can change a decision about project evidence. See
  # ../e2e/$fixture/{rule,task}.md.
  cp -R -- "$capsule"/. "$repo/"
  find "$repo" -name '__pycache__' -type d -exec rm -rf -- {} + 2>/dev/null || true
  git -C "$repo" init -q
  git -C "$repo" add -A
  git -C "$repo" -c user.name=nudge-e2e -c user.email=nudge-e2e@invalid \
    commit -qm "init"

  cat <<EOF

Sandbox ready: $repo   (state: $state)

1. Start a session with the isolated state:

       cd $repo && BEHAVIOR_DIFF_HOME=$state $session_cmd

   (NUDGE_E2E_AGENT=codex or NUDGE_E2E_MODEL=opus for another stack; the
   ask rate belongs to the agent, so it is worth measuring on each.)

2. Journey A ($fixture fixture) — paste this into the session as the prompt.
   Do NOT mention behavior-diff, or the prompt causes the ask instead of the
   hook:

$(if [[ -f $fixture_dir/edit-prompt.md ]]; then
    sed 's/^/       /' "$fixture_dir/edit-prompt.md"
  else
    printf '       Add this to %s:\n' "$instruction_file"
    sed 's/^/       /' "$fixture_dir/rule.md"
  fi)

   Expect the agent to ask, unprompted, whether to run behavior-diff.

   Answer Skip and confirm no Stop line follows. The ask has been seen
   answered without a keypress in a driven pane (cause unconfirmed), so if
   something answers before you do, that is not the agent's choice — note
   it and re-run.

   This step is model behavior, so run it a few times and record how often
   it asks.

   To carry the journey into behavior-diff, accept the ask. At its run gate,
   verify that its task preserves this neutral scenario:

$(sed 's/^/       /' "$fixture_dir/task.md")

3. Assert the state from another terminal:

       NUDGE_E2E_FIXTURE=$fixture NUDGE_E2E_REPO=$repo \
         NUDGE_E2E_STATE=$state $0 check

4. Journey B — the Stop fallback, which never happens naturally:

       NUDGE_E2E_FIXTURE=$fixture NUDGE_E2E_REPO=$repo \
         NUDGE_E2E_STATE=$state $0 drop-whisper

   Then end one more turn and expect exactly one line starting with a chart
   emoji, and silence on every later turn.
EOF
}

cmd_check() {
  [[ -d $nudge ]] ||
    die "no state at $nudge — was the session started with BEHAVIOR_DIFF_HOME=$state?"

  local edits spoken whisper recorded count
  edits=$(newest "$nudge/*.edits")
  spoken=$(newest "$nudge/*.edits.spoken")
  whisper=$(newest "$nudge/*.whispered")
  recorded=${edits:-$spoken}

  if [[ -n $recorded ]]; then
    pass "edit recorded ($(basename -- "$recorded"))"
    if grep -qF -- "$instruction_file" "$recorded"; then
      pass "$instruction_file is the recorded path"
    else
      fail "recorded path is not $instruction_file: $(tr '\n' ' ' < "$recorded")"
    fi
    count=$(grep -c . -- "$recorded" || true)
    if [[ $count -eq 1 ]]; then
      pass "exactly one path recorded (non-instruction files ignored, no duplicates)"
    else
      info "$count paths recorded — expected 1 unless you edited more"
    fi
  else
    fail "nothing recorded — the PostToolUse hook did not fire (plugin enabled?)"
  fi

  if [[ -n $whisper ]]; then
    pass "whisper marker present — the agent owns the ask, Stop must stay silent"
  else
    info "no whisper marker — either it never fired, or drop-whisper armed Journey B"
  fi
  [[ -n $spoken ]] && info "state claimed (.spoken) — the Stop line already fired this session"

  printf '\n'
  info "Stop only speaks while the edit is uncommitted:"
  git -C "$repo" status --porcelain -- "$instruction_file" | sed 's/^/        /'

  if [[ $failures -gt 0 ]]; then
    printf '\n%d check(s) failed\n' "$failures" >&2
    exit 1
  fi
}

cmd_drop_whisper() {
  local whisper
  whisper=$(newest "$nudge/*.whispered")
  [[ -n $whisper ]] || die "no whisper marker in $nudge — nothing to drop"
  rm -f -- "$whisper"
  pass "whisper marker removed — end a turn to expect the Stop reminder"
}

[[ $# -eq 1 ]] || usage
case $1 in
  setup) cmd_setup ;;
  check) cmd_check ;;
  drop-whisper) cmd_drop_whisper ;;
  reset)
    remove_sandbox "$repo" NUDGE_E2E_REPO
    remove_sandbox "$state" NUDGE_E2E_STATE
    pass "sandbox cleared"
    ;;
  *) usage ;;
esac
