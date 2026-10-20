#!/usr/bin/env bash
# Behavior Diff for a local instruction-file change.
#
# Run from a git repo where an instruction file (CLAUDE.md, a skill's
# SKILL.md or README.md, ...) has UNCOMMITTED changes:
#
#   behavior-diff.sh --file CLAUDE.md --task "one-line scenario" \
#       [--trials 3 | --fast] [--model NAME] [--before-file ORIGINAL]
#       [--purpose-file JSON] [--source-file JSON]
# Purpose is frozen report/assessment context, never an added trial instruction.
# Purpose and bounded recorded read/search returns go to the assessment provider
# and local reports. Supply reviewed safe context; exclusions are not privacy guarantees.
# --source-file is caller-verified historical provenance (original repository
# web URL, exact Before/After commits, optional PR/MR links) for a replayed
# Git history comparison. It is report-only, never inferred or a trial input.
# Without --source-file, GitHub Actions or GitLab CI repository and PR/MR links
# are detected once and frozen as report-only CI context with no commits.
#
# Before = the repo at HEAD. After = the same snapshot plus only your
# working-tree version of that one file — other uncommitted edits stay out.
# A file git does not track diffs against --before-file when given, else
# against the newest hook-captured baseline under
# ${BEHAVIOR_DIFF_HOME:-~/.behavior-diff}/baselines. In a folder that is
# not a git repo, the sandboxes are plain copies of the folder instead of
# a HEAD snapshot.
# N fresh headless trials run per variant in isolated temp copies; the
# report shows your git diff, the flow diff, and every trial's commands
# and final answer. Review mode: no automatic verdict — you judge.
# The user's real repo is never modified; runs land under
# ${BEHAVIOR_DIFF_HOME:-~/.behavior-diff}/runs.
set -euo pipefail

file="" task="" trials=3 agent=claude model="" vocab=generic extract_agent="" extract_model="" before_file="" purpose_file="" source_file=""
while [ $# -gt 0 ]; do
  case "$1" in
    --file | --before-file | --purpose-file | --source-file | --task | --trials | --model | --agent | --vocab | --extract-agent | --extract-model)
      if [ $# -lt 2 ] || [ -z "$2" ]; then
        echo "behavior-diff: $1 needs a value" >&2
        exit 2
      fi
      ;;
  esac
  case "$1" in
    --file)
      file=$2
      shift 2
      ;;
    --before-file)
      before_file=$2
      shift 2
      ;;
    --purpose-file)
      purpose_file=$2
      shift 2
      ;;
    --source-file)
      source_file=$2
      shift 2
      ;;
    --task)
      task=$2
      shift 2
      ;;
    --trials)
      trials=$2
      shift 2
      ;;
    --fast)
      trials=1
      shift
      ;;
    --model)
      model=$2
      shift 2
      ;;
    --agent)
      agent=$2
      shift 2
      ;;
    --vocab)
      vocab=$2
      shift 2
      ;;
    --extract-agent)
      extract_agent=$2
      shift 2
      ;;
    --extract-model)
      extract_model=$2
      shift 2
      ;;
    -h | --help)
      sed -n '2,28p' "$0"
      exit 0
      ;;
    *)
      echo "behavior-diff: unknown argument $1 (see --help)" >&2
      exit 2
      ;;
  esac
done
case "$vocab" in generic | spacedock) ;; *)
  echo "behavior-diff: --vocab must be generic or spacedock" >&2
  exit 2
  ;;
esac
case "$agent" in claude | codex | pi | omp) ;; *)
  echo "behavior-diff: unsupported trial stack \"$agent\"" >&2
  echo "Supported stacks: claude, codex, pi, omp." >&2
  echo "A new stack needs:" >&2
  echo "1. a fresh headless CLI run." >&2
  echo "2. machine-readable tool and final-answer events." >&2
  echo "3. a converter to canonical trace.jsonl." >&2
  exit 2
  ;;
esac
case "$trials" in '' | *[!0-9]* | 0)
  echo "behavior-diff: --trials must be a positive integer" >&2
  exit 2
  ;;
esac
if [ -z "$model" ]; then
  case "$agent" in
    claude) model=opus ;;
    codex) model=sol ;;
    pi)
      echo "behavior-diff: --agent pi requires --model with the exact Pi model ID" >&2
      exit 2
      ;;
    omp)
      echo "behavior-diff: --agent omp requires --model with the exact OMP model ID" >&2
      exit 2
      ;;
  esac
fi
[ -n "$file" ] && [ -n "$task" ] || {
  echo "behavior-diff: --file and --task are required (see --help)" >&2
  exit 2
}
command -v jq >/dev/null || {
  echo "behavior-diff: jq required" >&2
  exit 3
}
scripts=$(cd "$(dirname "$0")" && pwd)

# Validate and freeze purpose before any model discovery or trial launch.
# Never print rejected content: even a derived purpose can contain secrets.
purpose=null
if [ -n "$purpose_file" ]; then
  [ -f "$purpose_file" ] && [ -r "$purpose_file" ] && [ ! -L "$purpose_file" ] || {
    echo "behavior-diff: --purpose-file must name a readable regular JSON file, not a symlink" >&2
    exit 2
  }
  purpose=$(python3 "$scripts/purpose.py" "$purpose_file") || exit 2
  purpose_file=$(cd "$(dirname "$purpose_file")" && pwd -P)/$(basename "$purpose_file")
fi
# Source provenance is caller-authoritative: validate its shape and URLs only.
# Never derive it from the sandbox repository or its remotes.
source_json=null
if [ -n "$source_file" ]; then
  [ -f "$source_file" ] && [ -r "$source_file" ] && [ ! -L "$source_file" ] || {
    echo "behavior-diff: --source-file must name a readable regular JSON file, not a symlink" >&2
    exit 2
  }
  source_json=$(python3 "$scripts/source.py" "$source_file") || exit 2
  source_file=$(cd "$(dirname "$source_file")" && pwd -P)/$(basename "$source_file")
fi
# CI context names where this run executes, not what Before or After contain.
# Explicit source provenance wins entirely; the two are never blended.
ci_context=null
if [ -z "$source_file" ]; then
  ci_context=$(python3 "$scripts/ci_context.py") || exit 2
fi
command -v "$agent" >/dev/null || {
  echo "behavior-diff: $agent CLI required (--agent $agent)" >&2
  exit 3
}

# Resolve the sandbox world and the "before" side. The tracked-file git
# path stays the default: before = the repo at HEAD, sandboxes from
# `git archive HEAD`. An untracked file diffs against --before-file, else
# the newest hook-captured baseline; a non-git folder is copied as-is.
world=git          # git: sandboxes from `git archive HEAD` | copy: folder copy
before_mode="head" # head: repo at HEAD | file: $before_file | absent: no file
baselines=${BEHAVIOR_DIFF_HOME:-$HOME/.behavior-diff}/baselines
resolve_baseline() { # $1 = absolute target path -> newest baseline path
  # store key: percent-encoded absolute path
  # (keep this encoding identical to rules-edit-backup.sh)
  local enc newest
  enc=$(printf '%s' "$1" | sed 's|%|%25|g; s|/|%2F|g')
  # shellcheck disable=SC2012 # entry names are our own <ts>-<hash>, mtime = newest
  newest=$(ls -t "$baselines/$enc" 2>/dev/null | head -n 1)
  [ -n "$newest" ] || return 1
  printf '%s\n' "$baselines/$enc/$newest"
}

abs=$(cd "$(dirname "$file")" && pwd -P)/$(basename "$file")
if repo=$(git rev-parse --show-toplevel 2>/dev/null) &&
  git -C "$repo" rev-parse -q --verify HEAD >/dev/null 2>&1; then
  :
else
  world=copy
  repo=$(pwd -P)
  # copy-world guard: every trial gets a full copy of this folder (2 x
  # trials of them), so refuse a huge one instead of silently snapshotting
  # it — think a 2 GB ~/.claude full of session transcripts
  cap_kb=${BEHAVIOR_DIFF_COPY_CAP_KB:-204800} # 200 MB
  # du exits non-zero on a partial read (unreadable subdir) while still
  # printing a total — disarm it so the empty-value check below governs
  size_kb=$(du -sk "$repo" 2>/dev/null | awk '{print $1}') || true
  if [ -n "$size_kb" ] && [ "$size_kb" -gt "$cap_kb" ]; then
    echo "behavior-diff: $repo is ${size_kb}K on disk — over the ${cap_kb}K sandbox-copy cap. Run it from the smallest folder that holds the file, or raise BEHAVIOR_DIFF_COPY_CAP_KB." >&2
    exit 2
  fi
fi
rel=${abs#"$repo"/}
case "$rel" in /*)
  echo "behavior-diff: $file is outside $repo — run it from the folder that holds the file" >&2
  exit 2
  ;;
esac

# Supplied context files are not part of either trial's project inputs.
context_rel() { # $1 option name, $2 absolute context path -> repo-relative path
  if [ "$2" -ef "$abs" ] ||
    { [ -n "$before_file" ] && [ "$2" -ef "$before_file" ]; }; then
    echo "behavior-diff: $1 must not be a Before or After instruction file" >&2
    exit 2
  fi
  case "$2" in "$repo"/*) printf '%s\n' "${2#"$repo"/}" ;; esac
}
purpose_rel="" source_rel=""
if [ -n "$purpose_file" ]; then
  purpose_rel=$(context_rel --purpose-file "$purpose_file") || exit 2
fi
if [ -n "$source_file" ]; then
  source_rel=$(context_rel --source-file "$source_file") || exit 2
fi
if [ "$world" = git ] && [ -z "$before_file" ] &&
  git -C "$repo" cat-file -e "HEAD:$rel" 2>/dev/null; then
  if git -C "$repo" diff --quiet HEAD -- "$rel"; then
    echo "behavior-diff: $rel has no uncommitted change — nothing to compare" >&2
    exit 2
  fi
else
  before_mode="file"
  if [ -z "$before_file" ]; then
    before_file=$(resolve_baseline "$abs") || {
      echo "behavior-diff: no 'before' source for $rel — git does not track it and no baseline exists under $baselines. Pass --before-file <original>." >&2
      exit 2
    }
    # only a store-resolved entry can be the hook's ABSENT marker; a
    # user-given --before-file is always read as a plain file
    case "$(basename "$before_file")" in
      *-ABSENT) before_mode="absent" ;; # the file did not exist yet
    esac
  fi
  if [ "$before_mode" = file ]; then
    [ -f "$before_file" ] || {
      echo "behavior-diff: before file not found: $before_file" >&2
      exit 2
    }
    if cmp -s "$before_file" "$repo/$rel"; then
      echo "behavior-diff: $rel matches the before content — nothing to compare" >&2
      exit 2
    fi
  fi
fi

if [ "$agent" = codex ]; then
  case "$model" in
    sol | luna) model=$(python3 "$scripts/codex_model.py" "$model") || exit 2 ;;
  esac
fi
runs_root=${BEHAVIOR_DIFF_HOME:-$HOME/.behavior-diff}
mkdir -p "$runs_root/runs"
# mktemp -d creates a private directory atomically, so runs started in the same
# second under one home still get distinct IDs. Keep the path absolute: status
# commands and trial workers use it from other working directories.
runs_dir=$(cd "$runs_root/runs" && pwd -P)
run=$(mktemp -d "$runs_dir/diff-$(date +%Y%m%d-%H%M%S)-XXXXXX")
run_id=${run##*/}

say() { # one console line; a closed console must never stop the run
  if ! (printf '%s\n' "$*") 2>/dev/null; then
    exec >/dev/null # the subshell absorbed SIGPIPE; stop writing there
  fi
}
milestone() { say "behavior-diff $run_id: $*"; }
replay() { # $1 captured file, $2 console fd (1 or 2)
  [ -s "$1" ] || return 0
  if [ "$2" = 1 ]; then
    (cat -- "$1") 2>/dev/null || exec >/dev/null
  else
    (cat -- "$1" >&2) || exec 2>/dev/null
  fi
}
step_out="" step_err="" # capture files of this process's current step
drop_step_capture() {
  if [ -n "$step_out" ]; then rm -f -- "$step_out"; fi
  if [ -n "$step_err" ]; then rm -f -- "$step_err"; fi
  step_out="" step_err=""
}
begin_step_capture() {
  if ! step_out=$(mktemp "${TMPDIR:-/tmp}/behavior-diff-out.XXXXXX") ||
    ! step_err=$(mktemp "${TMPDIR:-/tmp}/behavior-diff-err.XXXXXX"); then
    drop_step_capture
    return 1
  fi
}
guarded_step() { # command...; buffers its console output, then replays it
  # A console closed while a child runs must not fail the child's own writes,
  # so children never write to it directly. The exit status is the child's.
  local code=0
  if ! begin_step_capture; then
    "$@" # no scratch space: keep the previous unbuffered behavior
    return
  fi
  "$@" >"$step_out" 2>"$step_err" || code=$?
  replay "$step_out" 1
  replay "$step_err" 2
  drop_step_capture
  return "$code"
}
record_status() { # $1 record, $2 kind, $3 JSON fields, [--owner]
  # progress.py diagnoses its own failures on stderr; none may change the
  # runner's exit code. Report loading and assessment read each trial record
  # and treat a recorded native failure as an incomplete trial.
  python3 "$scripts/progress.py" "$@" || :
}

# The runner owns RUN_DIR/status.json. Each trial worker owns its trial
# directory's status.json, and decisions.py owns assessment-status.json.
record_status "$run/status.json" run "$(jq -cn --arg run_id "$run_id" \
  --arg project "$repo" --arg target "$rel" --arg agent "$agent" \
  --arg model "$model" --arg trials "$trials" \
  '{run_id:$run_id, project:$project, target:$target, agent:$agent,
    model:$model, trials:($trials | tonumber), phase:"preparing",
    state:"running", report:{state:"pending", path:null}}')" --owner

preparing_trial="" # trial directory whose foreground preparation the runner owns
finish_run() {     # $1 terminal state, $2 exit code
  local fields
  fields=$(printf '{"state":"%s","exit_code":%d}' "$1" "$2")
  if [ -n "$preparing_trial" ]; then
    record_status "$preparing_trial/status.json" trial "$fields"
  fi
  record_status "$run/status.json" run "$fields"
}
on_run_exit() {
  local code=$?
  if [ -n "$step_out" ]; then replay "$step_out" 1; fi
  if [ -n "$step_err" ]; then replay "$step_err" 2; fi
  drop_step_capture
  if [ "$code" -eq 0 ]; then
    record_status "$run/status.json" run \
      '{"phase":"finished","state":"completed","exit_code":0}'
    milestone "finished (exit 0)"
  else
    finish_run failed "$code"
    milestone "failed (exit $code)"
  fi
  exit "$code"
}
on_run_signal() { # $1 signal name, $2 signal number
  trap - EXIT "$1"
  drop_step_capture
  finish_run interrupted $((128 + $2))
  milestone "interrupted by SIG$1"
  # Re-raise so callers still see termination by this signal.
  kill -s "$1" "$$"
  exit $((128 + $2))
}
trap on_run_exit EXIT
trap 'on_run_signal INT 2' INT
trap 'on_run_signal TERM 15' TERM
trap 'on_run_signal HUP 1' HUP

status_command="python3 $(printf '%q' "$scripts/status.py") $(printf '%q' "$run")"
say "behavior-diff run $run_id"
say "  target:    $rel"
say "  directory: $run"
say "  status:    $status_command"
say "  json:      $status_command --json"
say "  watch:     $status_command --watch"
printf '%s\n' "$task" >"$run/task.md"
case "$before_mode" in
  head)
    before_label="commit $(git -C "$repo" rev-parse --short HEAD)"
    after_label="$abs (uncommitted)"
    ;;
  file)
    before_label="$before_file"
    after_label="$abs"
    ;;
  absent)
    before_label="the file did not exist yet"
    after_label="$abs"
    ;;
esac
jq -n --arg f "$rel" --arg task "$task" --arg vocab "$vocab" \
  --arg title "Behavior Diff — $rel" --argjson purpose "$purpose" \
  --argjson source "$source_json" --argjson ci_context "$ci_context" \
  --arg before_label "$before_label" --arg after_label "$after_label" \
  '{title:$title, scenario:$task, purpose:$purpose,
    target_file:$f, mode:"review", vocab:$vocab,
    before_label:$before_label, after_label:$after_label}
    + (if $source == null then {} else {source:$source} end)
    + (if $ci_context == null then {} else {ci_context:$ci_context} end)' >"$run/config.json"

# Conservative read/run allowlist; no Write/Edit, no network tools.
ALLOWED='Bash(pytest:*),Bash(python3:*),Bash(python:*),Bash(bash:*),Bash(sh:*),Bash(node:*),Bash(npm:*),Bash(make:*),Bash(go:*),Bash(cargo:*),Bash(printf:*),Bash(echo:*),Bash(ls:*),Bash(cat:*),Bash(head:*),Bash(sed:*),Bash(git:*),Bash(find:*),Bash(grep:*),Bash(rg:*),Read,Grep,Glob'

# A nonempty final result keeps a trial reviewable; anything else is BLOCKED.
has_final_result() { # $1 trace.jsonl
  jq -e -s '[.[] | select(.type == "result"
                          and ((.result // "") | length > 0))]
            | length > 0' \
    "$1" >/dev/null 2>&1
}

interrupt_trial() { # $1 signal number; trap handler inside a trial worker
  drop_step_capture
  record_status "$trial_status" trial \
    "$(printf '{"state":"interrupted","exit_code":%d}' $((128 + $1)))"
  exit $((128 + $1))
}

snapshot_project() { # commit the prepared copy in the current directory
  git init -q && git config user.email b@diff &&
    git config user.name behavior-diff &&
    git add -A && git commit -qm "snapshot for behavior diff"
}

run_trial_worker() { # $1 trial directory; runs as a background job
  local dir=$1 name=${1##*/} code=0 final_result=false
  # Global only within this job's subshell, for the signal handler.
  trial_status=$dir/status.json
  # Take ownership so readers check the process that finishes this record.
  record_status "$trial_status" trial '{"phase":"preparing","state":"running"}' --owner
  trap 'interrupt_trial 15' TERM
  trap 'interrupt_trial 1' HUP
  if cd "$dir/project" && guarded_step snapshot_project; then
    guarded_step "$scripts/run-trial.sh" --agent "$agent" --model "$model" \
      --dir "$dir/project" --task-file "$run/task.md" \
      --allowed "$ALLOWED" --trace-dir "$dir" --status-file "$trial_status" ||
      code=$?
  else
    code=$?
  fi
  trap - TERM HUP
  if has_final_result "$dir/trace.jsonl"; then
    final_result=true
  fi
  if [ "$code" -eq 0 ]; then
    record_status "$trial_status" trial \
      "{\"phase\":\"finished\",\"state\":\"finished\",\"exit_code\":0,\"final_result\":$final_result}"
  else
    record_status "$trial_status" trial \
      "{\"state\":\"failed\",\"exit_code\":$code,\"final_result\":$final_result}"
  fi
  if [ "$final_result" = true ]; then
    milestone "$name ended (exit $code); final answer recorded"
  else
    milestone "$name ended (exit $code); no final answer"
  fi
  return "$code"
}

remove_context_file() { # $1 project copy, $2 repo-relative path, $3 option name
  # HEAD may contain a parent symlink where the working tree has a directory.
  # Check each parent before removal rather than following it outside the copy.
  local parent="$1" remaining="$2" component
  while [[ "$remaining" == */* ]]; do
    component=${remaining%%/*}
    remaining=${remaining#*/}
    parent=$parent/$component
    if [ -L "$parent" ]; then
      echo "behavior-diff: cannot isolate $3 through a snapshot parent symlink" >&2
      return 2
    fi
  done
  rm -f -- "$1/$2"
}

prepare_snapshot() { # $1 variant, $2 trial index; retain errexit in foreground
  local dir=$run/$1-$2
  if [ "$world" = git ]; then
    git -C "$repo" archive HEAD | tar -x -C "$dir/project"
  else
    # non-git folder: both variants get the same plain copy of the folder;
    # never ingest the runs/baselines home, even when it sits inside it
    local excl="$runs_root"
    case "$runs_root" in "$repo"/*) excl=./${runs_root#"$repo"/} ;; esac
    tar -C "$repo" --exclude .git --exclude "$excl" -cf - . | tar -x -C "$dir/project"
  fi
  if [ -n "$purpose_rel" ]; then
    remove_context_file "$dir/project" "$purpose_rel" --purpose-file || return
  fi
  if [ -n "$source_rel" ]; then
    remove_context_file "$dir/project" "$source_rel" --source-file || return
  fi
  mkdir -p "$(dirname "$dir/project/$rel")"
  if [ "$1" = after ]; then
    cp "$repo/$rel" "$dir/project/$rel"
  else
    case "$before_mode" in
      file) cp "$before_file" "$dir/project/$rel" ;;
      absent) rm -f "$dir/project/$rel" ;;
    esac
  fi
}

launch() { # $1 variant, $2 trial index
  local dir=$run/$1-$2
  mkdir -p "$dir/project"
  preparing_trial=$dir
  record_status "$dir/status.json" trial '{"phase":"preparing","state":"running"}' --owner
  if begin_step_capture; then
    # Do not run this through guarded_step's conditional: that would disable
    # errexit inside preparation and could launch an incomplete project copy.
    prepare_snapshot "$@" >"$step_out" 2>"$step_err"
    replay "$step_out" 1
    replay "$step_err" 2
    drop_step_capture
  else
    prepare_snapshot "$@"
  fi
  preparing_trial=""
  run_trial_worker "$dir" &
}

say "behavior diff on $rel: $trials trial(s) per variant, agent $agent, model $model"
record_status "$run/status.json" run '{"phase":"running_trials"}'
milestone "starting $((2 * trials)) trials"
for v in before after; do
  for t in $(seq 1 "$trials"); do launch "$v" "$t"; done
done
wait || true

record_status "$run/status.json" run '{"phase":"checking_results"}'
milestone "all trials ended; checking trial results"

# Review mode: BLOCKED for runs without a final answer, neutral REVIEW otherwise.
# Report loading also blocks a trial whose status record shows a native failure.
for v in before after; do
  for t in $(seq 1 "$trials"); do
    verdict=REVIEW
    has_final_result "$run/$v-$t/trace.jsonl" || verdict=BLOCKED
    printf '%s\t%s\t-\n' "$v-$t" "$verdict"
  done
done >"$run/grades.tsv"

say
# Decision diff: one model pass over the final answers. Best-effort — if it
# fails, render.py falls back to the command-derived flow diff alone.
if [ -z "$extract_agent" ]; then
  case "$extract_model" in
    sol | luna) extract_agent=codex ;;
    *) extract_agent=$agent ;;
  esac
fi
case "$agent" in
  pi | omp)
    case "$extract_agent" in
      pi | omp)
        [ -n "$extract_model" ] || extract_model=$model
        ;;
    esac
    ;;
esac
record_status "$run/status.json" run '{"phase":"comparing_evidence"}'
milestone "comparing evidence"
guarded_step python3 "$scripts/decisions.py" "$run" ${extract_agent:+--agent "$extract_agent"} ${extract_model:+--model "$extract_model"} || true
record_status "$run/status.json" run '{"phase":"rendering"}'
milestone "rendering report"
render_code=0
guarded_step python3 "$scripts/render.py" "$run" "$run" "$model" "$run/config.json" || render_code=$?
# Availability needs the renderer's success, not only a file left behind.
if [ "$render_code" -eq 0 ] && [ -s "$run/report.html" ]; then
  record_status "$run/status.json" run \
    "$(jq -cn --arg path "$run/report.html" '{report:{state:"available", path:$path}}')"
  milestone "report ready: $run/report.html"
else
  record_status "$run/status.json" run '{"report":{"state":"failed","path":null}}'
  milestone "report not produced (renderer exit $render_code)"
fi
[ "$render_code" -eq 0 ] || exit "$render_code"
open "$run/report.html" 2>/dev/null || true
