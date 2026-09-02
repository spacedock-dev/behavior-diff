#!/usr/bin/env bash
# Behavior Diff for a local instruction-file change.
#
# Run from a git repo where an instruction file (CLAUDE.md, a skill's
# SKILL.md or README.md, ...) has UNCOMMITTED changes:
#
#   behavior-diff.sh --file CLAUDE.md --task "one-line scenario" \
#       [--trials 3 | --fast] [--model sonnet] [--before-file ORIGINAL]
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

file="" task="" trials=3 agent=claude model="" vocab=generic extract_agent="" extract_model="" before_file=""
while [ $# -gt 0 ]; do
  case "$1" in
    --file) file=$2; shift 2 ;;
    --before-file) before_file=$2; shift 2 ;;
    --task) task=$2; shift 2 ;;
    --trials) trials=$2; shift 2 ;;
    --fast) trials=1; shift ;;
    --model) model=$2; shift 2 ;;
    --agent) agent=$2; shift 2 ;;
    --vocab) vocab=$2; shift 2 ;;
    --extract-agent) extract_agent=$2; shift 2 ;;
    --extract-model) extract_model=$2; shift 2 ;;
    -h|--help) sed -n '2,21p' "$0"; exit 0 ;;
    *) echo "behavior-diff: unknown argument $1 (see --help)" >&2; exit 2 ;;
  esac
done
case "$vocab" in generic|spacedock) ;; *) echo "behavior-diff: --vocab must be generic or spacedock" >&2; exit 2 ;; esac
case "$agent" in claude|codex) ;; *) echo "behavior-diff: --agent must be claude or codex" >&2; exit 2 ;; esac
case "$trials" in ''|*[!0-9]*|0) echo "behavior-diff: --trials must be a positive integer" >&2; exit 2 ;; esac
[ -n "$model" ] || model=$([ "$agent" = codex ] && echo gpt-5.6-terra || echo sonnet)
[ -n "$file" ] && [ -n "$task" ] || {
  echo "behavior-diff: --file and --task are required (see --help)" >&2; exit 2; }
command -v jq >/dev/null || { echo "behavior-diff: jq required" >&2; exit 3; }
command -v "$agent" >/dev/null || { echo "behavior-diff: $agent CLI required (--agent $agent)" >&2; exit 3; }

# Resolve the sandbox world and the "before" side. The tracked-file git
# path stays the default: before = the repo at HEAD, sandboxes from
# `git archive HEAD`. An untracked file diffs against --before-file, else
# the newest hook-captured baseline; a non-git folder is copied as-is.
world=git           # git: sandboxes from `git archive HEAD` | copy: folder copy
before_mode="head"  # head: repo at HEAD | file: $before_file | absent: no file
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
if repo=$(git rev-parse --show-toplevel 2>/dev/null) \
   && git -C "$repo" rev-parse -q --verify HEAD >/dev/null 2>&1; then
  :
else
  world=copy
  repo=$(pwd -P)
  # copy-world guard: every trial gets a full copy of this folder (2 x
  # trials of them), so refuse a huge one instead of silently snapshotting
  # it — think a 2 GB ~/.claude full of session transcripts
  cap_kb=${BEHAVIOR_DIFF_COPY_CAP_KB:-204800}   # 200 MB
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
  exit 2 ;;
esac
if [ "$world" = git ] && [ -z "$before_file" ] \
   && git -C "$repo" cat-file -e "HEAD:$rel" 2>/dev/null; then
  if git -C "$repo" diff --quiet HEAD -- "$rel"; then
    echo "behavior-diff: $rel has no uncommitted change — nothing to compare" >&2
    exit 2
  fi
else
  before_mode="file"
  if [ -z "$before_file" ]; then
    before_file=$(resolve_baseline "$abs") || {
      echo "behavior-diff: no 'before' source for $rel — git does not track it and no baseline exists under $baselines. Pass --before-file <original>." >&2
      exit 2; }
    # only a store-resolved entry can be the hook's ABSENT marker; a
    # user-given --before-file is always read as a plain file
    case "$(basename "$before_file")" in
      *-ABSENT) before_mode="absent" ;; # the file did not exist yet
    esac
  fi
  if [ "$before_mode" = file ]; then
    [ -f "$before_file" ] || {
      echo "behavior-diff: before file not found: $before_file" >&2; exit 2; }
    if cmp -s "$before_file" "$repo/$rel"; then
      echo "behavior-diff: $rel matches the before content — nothing to compare" >&2
      exit 2
    fi
  fi
fi

scripts=$(cd "$(dirname "$0")" && pwd)
runs_root=${BEHAVIOR_DIFF_HOME:-$HOME/.behavior-diff}
run=$runs_root/runs/diff-$(date +%Y%m%d-%H%M%S)
mkdir -p "$run"
printf '%s\n' "$task" > "$run/task.md"
case "$before_mode" in
  head) sub="Same task, same settings, fresh agent runs. Before is the repo at HEAD; After adds only your uncommitted change to $rel. No automatic grading — compare what the agents did and said." ;;
  file) sub="Same task, same settings, fresh agent runs. Before is your saved original of $rel ($before_file); After is the same world with your current $rel. No automatic grading — compare what the agents did and said." ;;
  absent) sub="Same task, same settings, fresh agent runs. Before has no $rel (the file did not exist yet); After adds your current $rel. No automatic grading — compare what the agents did and said." ;;
esac
jq -n --arg f "$rel" --arg task "$task" --arg vocab "$vocab" \
  --arg title "Behavior Diff — $rel" \
  --arg sub "$sub" \
  '{title:$title, sub:$sub, scenario:$task, expected:null,
    target_file:$f, mode:"review", vocab:$vocab}' > "$run/config.json"

# Conservative read/run allowlist; no Write/Edit, no network tools.
ALLOWED='Bash(pytest:*),Bash(python3:*),Bash(python:*),Bash(bash:*),Bash(sh:*),Bash(node:*),Bash(npm:*),Bash(make:*),Bash(go:*),Bash(cargo:*),Bash(printf:*),Bash(echo:*),Bash(ls:*),Bash(cat:*),Bash(head:*),Bash(sed:*),Bash(git:*),Bash(find:*),Bash(grep:*),Bash(rg:*),Read,Grep,Glob'

launch() { # $1 variant, $2 trial index
  local dir=$run/$1-$2
  mkdir -p "$dir/project"
  if [ "$world" = git ]; then
    git -C "$repo" archive HEAD | tar -x -C "$dir/project"
  else
    # non-git folder: both variants get the same plain copy of the folder;
    # never ingest the runs/baselines home, even when it sits inside it
    local excl="$runs_root"
    case "$runs_root" in "$repo"/*) excl=./${runs_root#"$repo"/} ;; esac
    tar -C "$repo" --exclude .git --exclude "$excl" -cf - . | tar -x -C "$dir/project"
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
  ( cd "$dir/project" && git init -q \
      && git config user.email b@diff && git config user.name behavior-diff \
      && git add -A && git commit -qm "snapshot for behavior diff" \
      && "$scripts/run-trial.sh" --agent "$agent" --model "$model" \
           --dir "$dir/project" --task-file "$run/task.md" \
           --allowed "$ALLOWED" --trace-dir "$dir" ) &
}

echo "behavior diff on $rel: $trials trial(s) per variant, agent $agent, model $model"
for v in before after; do
  for t in $(seq 1 "$trials"); do launch "$v" "$t"; done
done
wait || true

# Review mode: BLOCKED for broken runs, neutral REVIEW otherwise.
for v in before after; do
  for t in $(seq 1 "$trials"); do
    verdict=REVIEW
    jq -e -s '[.[] | select(.type == "result"
                            and ((.result // "") | length > 0))]
              | length > 0' \
      "$run/$v-$t/trace.jsonl" >/dev/null 2>&1 || verdict=BLOCKED
    printf '%s\t%s\t-\n' "$v-$t" "$verdict"
  done
done > "$run/grades.tsv"

echo
# Decision diff: one model pass over the final answers. Best-effort — if it
# fails, render.py falls back to the command-derived flow diff alone.
python3 "$scripts/decisions.py" "$run" ${extract_agent:+--agent "$extract_agent"} ${extract_model:+--model "$extract_model"} || true
python3 "$scripts/render.py" "$run" "$run" "$model" "$run/config.json"
open "$run/report.html" 2>/dev/null || true
