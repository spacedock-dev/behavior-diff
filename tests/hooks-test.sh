#!/usr/bin/env bash
# Self-check for the rules-edit hooks: pipes fake hook payloads through
# detect/remind and asserts state + output. No agent, no model, no network.
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd -P)
detect=$here/../plugin/scripts/rules-edit-detect.sh
remind=$here/../plugin/scripts/rules-edit-remind.sh

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
export BEHAVIOR_DIFF_HOME=$tmp/home
unset BEHAVIOR_DIFF_TRIAL 2>/dev/null || true
nudge=$BEHAVIOR_DIFF_HOME/nudge

payload() { # session file cwd
  jq -n --arg s "$1" --arg f "$2" --arg c "${3:-$tmp}" \
    '{session_id:$s, cwd:$c, tool_name:"Edit", tool_input:{file_path:$f}}'
}
stop_payload() { # session cwd
  jq -n --arg s "$1" --arg c "${2:-$tmp}" \
    '{session_id:$s, cwd:$c, stop_hook_active:false}'
}
fail() {
  echo "FAIL: $1"
  exit 1
}

# 1. first CLAUDE.md edit: recorded, and the agent whisper is emitted
out=$(payload s1 /proj/CLAUDE.md | "$detect")
grep -qxF /proj/CLAUDE.md "$nudge/s1.edits" || fail "edit not recorded"
printf '%s' "$out" | jq -e '.hookSpecificOutput.additionalContext | test("AskUserQuestion")' \
  >/dev/null || fail "whisper missing or does not name AskUserQuestion"
[ -f "$nudge/s1.whispered" ] || fail "whisper marker missing"

# 2. a non-instruction file is ignored
payload s1 /proj/main.py | "$detect"
[ "$(wc -l <"$nudge/s1.edits")" -eq 1 ] || fail "non-instruction file recorded"

# 3. same file again: recorded once, whispered once
out=$(payload s1 /proj/CLAUDE.md | "$detect")
[ "$(wc -l <"$nudge/s1.edits")" -eq 1 ] || fail "dedupe broken"
[ -z "$out" ] || fail "whispered twice"

# 4. a second instruction file: recorded, still no second whisper
out=$(payload s1 /proj/AGENTS.md | "$detect")
[ "$(wc -l <"$nudge/s1.edits")" -eq 2 ] || fail "second file not recorded"
[ -z "$out" ] || fail "whispered twice for second file"

# 5. trial guard: nothing recorded, nothing whispered
out=$(payload s9 /proj/AGENTS.md | BEHAVIOR_DIFF_TRIAL=1 "$detect")
[ ! -f "$nudge/s9.edits" ] && [ -z "$out" ] || fail "trial guard broken"

# 6. Stop is silent when the whisper was sent (the agent owns the question)
out=$(stop_payload s1 | "$remind")
[ -z "$out" ] || fail "Stop spoke despite whisper"

# 7. Stop fallback speaks once when there was no whisper (non-repo cwd errs
#    toward reminding), then never again
rm "$nudge/s1.whispered"
out=$(stop_payload s1 | "$remind")
printf '%s' "$out" | jq -e '.systemMessage | test("2 instruction files")' >/dev/null ||
  fail "fallback reminder missing"
[ -f "$nudge/s1.edits.spoken" ] || fail "state not claimed"
out=$(stop_payload s1 | "$remind")
[ -z "$out" ] || fail "reminded twice"

# 8. a committed (clean) file is not reminded about
repo=$tmp/repo && mkdir -p "$repo" && git -C "$repo" init -q
echo rules >"$repo/CLAUDE.md"
git -C "$repo" add CLAUDE.md && git -C "$repo" -c user.email=t@t -c user.name=t commit -qm x
payload s2 "$repo/CLAUDE.md" "$repo" | "$detect" >/dev/null
rm "$nudge/s2.whispered"
out=$(stop_payload s2 "$repo" | "$remind")
[ -z "$out" ] || fail "reminded about a committed file"

# 9. an uncommitted file in a repo IS reminded about (fallback path)
echo more >>"$repo/CLAUDE.md"
payload s3 "$repo/CLAUDE.md" "$repo" | "$detect" >/dev/null
rm "$nudge/s3.whispered"
out=$(stop_payload s3 "$repo" | "$remind")
printf '%s' "$out" | jq -e '.systemMessage' >/dev/null || fail "no reminder for dirty file"

# 10. stop_hook_active suppresses output (loop guard)
payload s4 /proj/CLAUDE.md | "$detect" >/dev/null
rm "$nudge/s4.whispered"
out=$(jq -n '{session_id:"s4", cwd:"/x", stop_hook_active:true}' | "$remind")
[ -z "$out" ] || fail "spoke during stop_hook_active"

# Codex payloads: apply_patch carries no tool_input.file_path — the edited
# paths ride the patch grammar in tool_input.command, cwd-relative (shape
# captured live from codex-cli 0.149.1; see the entity's probe A).
codex_payload() { # session patch-body cwd
  jq -n --arg s "$1" --arg p "$2" --arg c "${3:-$tmp}" \
    '{session_id:$s, cwd:$c, hook_event_name:"PostToolUse",
      tool_name:"apply_patch", tool_input:{command:$p},
      tool_response:"Exit code: 0\nSuccess."}'
}
patch_agents=$'*** Begin Patch\n*** Update File: AGENTS.md\n@@\n-a\n+b\n*** End Patch'

# 11. AC-1: an apply_patch updating AGENTS.md records the cwd-joined absolute
#     path exactly once and whispers once
out=$(codex_payload c1 "$patch_agents" /work | "$detect")
[ "$(cat "$nudge/c1.edits")" = "/work/AGENTS.md" ] ||
  fail "codex path missing, relative, or duplicated"
printf '%s' "$out" | jq -e '.hookSpecificOutput.additionalContext | test("AskUserQuestion")' \
  >/dev/null || fail "codex whisper missing"
[ -f "$nudge/c1.whispered" ] || fail "codex whisper marker missing"

# 12. AC-2: a patch touching CLAUDE.md and a non-instruction file records only
#     CLAUDE.md; two instruction files both land; a repeat patch records and
#     whispers nothing new
patch_mixed=$'*** Begin Patch\n*** Update File: CLAUDE.md\n@@\n-a\n+b\n*** Add File: notes.txt\n+hi\n*** End Patch'
codex_payload c2 "$patch_mixed" /work | "$detect" >/dev/null
[ "$(cat "$nudge/c2.edits")" = "/work/CLAUDE.md" ] || fail "non-instruction patch file recorded"
patch_two=$'*** Begin Patch\n*** Update File: CLAUDE.md\n@@\n-b\n+c\n*** Add File: sub/AGENTS.md\n+x\n*** End Patch'
out=$(codex_payload c2 "$patch_two" /work | "$detect")
[ "$(wc -l <"$nudge/c2.edits")" -eq 2 ] || fail "multi-file patch dedupe or recording broken"
grep -qxF /work/sub/AGENTS.md "$nudge/c2.edits" || fail "second instruction file not cwd-joined"
[ -z "$out" ] || fail "codex whispered twice"
out=$(codex_payload c2 "$patch_two" /work | "$detect")
[ "$(wc -l <"$nudge/c2.edits")" -eq 2 ] || fail "repeat patch re-recorded"
[ -z "$out" ] || fail "repeat patch whispered"

# 13. AC-3: the trial guard covers codex payloads too
out=$(codex_payload c9 "$patch_agents" /work | BEHAVIOR_DIFF_TRIAL=1 "$detect")
[ ! -f "$nudge/c9.edits" ] && [ -z "$out" ] || fail "codex trial guard broken"

# 14. AC-5: the Stop fallback fires from codex-recorded state — detect
#     (apply_patch payload) then remind names the file (non-repo cwd errs
#     toward reminding)
codex_payload c3 "$patch_agents" /work | "$detect" >/dev/null
rm "$nudge/c3.whispered"
out=$(stop_payload c3 /work | "$remind")
printf '%s' "$out" | jq -e '.systemMessage | test("AGENTS.md")' >/dev/null ||
  fail "codex detect-to-remind chain broken"

# Baseline backup hook (PreToolUse) — AC-1 and AC-5 of the non-git change,
# plus the runner's --before-file / baseline-resolve argument paths.
backup=$here/../plugin/scripts/rules-edit-backup.sh
runner=$here/../plugin/skills/behavior-diff/scripts/behavior-diff.sh
baselines=$BEHAVIOR_DIFF_HOME/baselines
enc_of() { printf '%s' "$1" | sed 's|%|%25|g; s|/|%2F|g'; }
nentries() { find "$1" -mindepth 1 -maxdepth 1 -type f ! -name '.*' | wc -l; }
real=$(cd "$tmp" && pwd -P) # the hook canonicalizes /var -> /private/var

# 15. AC-1 case A: untracked file — the pre-edit content lands in the store
mkdir -p "$real/plain"
printf 'original rules\n' >"$real/plain/CLAUDE.md"
bdir=$baselines/$(enc_of "$real/plain/CLAUDE.md")
out=$(payload b1 "$real/plain/CLAUDE.md" | "$backup") || fail "backup exited non-zero"
[ -z "$out" ] || fail "backup wrote to stdout"
[ "$(nentries "$bdir")" -eq 1 ] || fail "untracked file: expected one baseline entry"
cmp -s "$bdir/$(ls "$bdir")" "$real/plain/CLAUDE.md" || fail "baseline content wrong"
[ -f "$bdir/.session-b1" ] || fail "session marker missing"

# 16. AC-1 case C: a second edit in the same session keeps the first content
printf 'edited once\n' >"$real/plain/CLAUDE.md"
payload b1 "$real/plain/CLAUDE.md" | "$backup" || fail "backup re-run exited non-zero"
[ "$(nentries "$bdir")" -eq 1 ] || fail "second edit in one session added an entry"
grep -qxF 'original rules' "$bdir/$(ls "$bdir")" || fail "first edit did not win"

# 17. a NEW session snapshots the changed content; a third session with
#     unchanged content dedupes against that newest baseline
payload b2 "$real/plain/CLAUDE.md" | "$backup" || fail "second-session backup failed"
[ "$(nentries "$bdir")" -eq 2 ] || fail "new session did not snapshot new content"
payload b3 "$real/plain/CLAUDE.md" | "$backup" || fail "third-session backup failed"
[ "$(nentries "$bdir")" -eq 2 ] || fail "dedupe against newest baseline broken"
[ -f "$bdir/.session-b3" ] || fail "dedupe skipped the session marker"

# 18. AC-1 case B: a git-tracked file gets no baseline (even a dirty one)
realrepo=$(cd "$repo" && pwd -P)
payload b4 "$realrepo/CLAUDE.md" "$realrepo" | "$backup" || fail "tracked-file backup errored"
[ ! -d "$baselines/$(enc_of "$realrepo/CLAUDE.md")" ] || fail "tracked file backed up"

# 19. a file that does not exist yet gets an ABSENT marker
adir=$baselines/$(enc_of "$real/plain/AGENTS.md")
payload b5 "$real/plain/AGENTS.md" | "$backup" || fail "absent-file backup errored"
entry=$(ls "$adir" 2>/dev/null)
case "$entry" in *-ABSENT) ;; *) fail "ABSENT marker missing (got: $entry)" ;; esac

# 20. AC-5: broken JSON, unwritable store, trial guard — silent exit 0 each
out=$(printf 'not json' | "$backup") && [ -z "$out" ] || fail "broken JSON not fail-quiet"
ro=$tmp/ro && mkdir -p "$ro" && chmod 500 "$ro"
out=$(payload b6 "$real/plain/CLAUDE.md" | BEHAVIOR_DIFF_HOME=$ro/home "$backup") &&
  [ -z "$out" ] || fail "unwritable store not fail-quiet"
chmod 700 "$ro"
out=$(payload b7 "$real/plain/CLAUDE.md" | BEHAVIOR_DIFF_TRIAL=1 "$backup") &&
  [ -z "$out" ] || fail "trial guard broken for backup"
[ ! -f "$bdir/.session-b7" ] || fail "trial guard wrote a session marker"

# Runner argument paths (all exit before any trial launches; the stub agent
# CLI only satisfies the `command -v` precondition)
stub=$tmp/bin && mkdir -p "$stub"
printf '#!/bin/sh\nexit 0\n' >"$stub/claude" && chmod +x "$stub/claude"
plainrun=$real/plainrun && mkdir -p "$plainrun"
printf 'x\n' >"$plainrun/CLAUDE.md"

# 21. --before-file that does not exist is a plain exit 2
set +e
out=$(cd "$plainrun" && PATH="$stub:$PATH" "$runner" --file CLAUDE.md --task t \
  --before-file missing.md 2>&1)
code=$?
set -e
[ "$code" -eq 2 ] || fail "missing before file: exit $code, want 2"
printf '%s' "$out" | grep -q "before file not found" || fail "missing before-file message"

# 22. AC-4: untracked file, empty store, no --before-file — non-zero exit,
#     the message names the baseline store, and no run dir is created
set +e
out=$(cd "$plainrun" && PATH="$stub:$PATH" "$runner" --file CLAUDE.md --task t 2>&1)
code=$?
set -e
[ "$code" -eq 2 ] || fail "no before source: exit $code, want 2"
printf '%s' "$out" | grep -qF "$baselines" || fail "message does not name the baseline store"
[ -z "$(ls "$BEHAVIOR_DIFF_HOME/runs" 2>/dev/null)" ] || fail "run dir created despite hard stop"

# 23. AC-2: the tracked-file default path still stops with the same message
git -C "$repo" -c user.email=t@t -c user.name=t commit -qam clean
set +e
out=$(cd "$repo" && PATH="$stub:$PATH" "$runner" --file CLAUDE.md --task t 2>&1)
code=$?
set -e
[ "$code" -eq 2 ] || fail "clean tracked file: exit $code, want 2"
printf '%s' "$out" | grep -q "no uncommitted change — nothing to compare" ||
  fail "tracked-file default message changed"

# 24. the runner resolves the hook's baseline by itself: equal content is
#     reported against the resolved baseline, not the empty-store stop
payload r1 "$plainrun/CLAUDE.md" | "$backup" || fail "baseline plant failed"
set +e
out=$(cd "$plainrun" && PATH="$stub:$PATH" "$runner" --file CLAUDE.md --task t 2>&1)
code=$?
set -e
[ "$code" -eq 2 ] || fail "resolved-baseline equal content: exit $code, want 2"
printf '%s' "$out" | grep -q "matches the before content" ||
  fail "baseline auto-resolve did not find the hook's copy"

# 25. copy-world size guard: a folder over the cap is refused before any
#     run dir exists (fails if the guard is removed)
big=$real/bigrun && mkdir -p "$big"
printf 'new\n' >"$big/CLAUDE.md"
printf 'old\n' >"$big/orig.md"
dd if=/dev/zero of="$big/blob" bs=1024 count=64 2>/dev/null
set +e
out=$(cd "$big" && PATH="$stub:$PATH" BEHAVIOR_DIFF_COPY_CAP_KB=16 "$runner" \
  --file CLAUDE.md --task t --before-file orig.md 2>&1)
code=$?
set -e
[ "$code" -eq 2 ] || fail "size guard: exit $code, want 2"
printf '%s' "$out" | grep -q "smallest folder" || fail "size guard message missing"
[ -z "$(ls "$BEHAVIOR_DIFF_HOME/runs" 2>/dev/null)" ] || fail "size guard created a run dir"

# 26. a user-given --before-file whose NAME ends in -ABSENT is a plain
#     file, never the store's absence marker
printf 'x\n' >"$plainrun/orig-ABSENT"
set +e
out=$(cd "$plainrun" && PATH="$stub:$PATH" "$runner" --file CLAUDE.md --task t \
  --before-file orig-ABSENT 2>&1)
code=$?
set -e
[ "$code" -eq 2 ] || fail "-ABSENT-named before file: exit $code, want 2"
printf '%s' "$out" | grep -q "matches the before content" ||
  fail "-ABSENT-named before file not read as a plain file"

# 27. twin of 25: an unreadable subdir must not kill the runner silently —
#     du's partial-read failure is disarmed, later checks still speak
odd=$real/oddrun && mkdir -p "$odd/locked"
printf 'same\n' >"$odd/CLAUDE.md"
printf 'same\n' >"$odd/orig.md"
chmod 000 "$odd/locked"
set +e
out=$(cd "$odd" && PATH="$stub:$PATH" "$runner" --file CLAUDE.md --task t \
  --before-file orig.md 2>&1)
code=$?
set -e
chmod 700 "$odd/locked"
[ -n "$out" ] || fail "unreadable subdir: silent exit (code $code)"
printf '%s' "$out" | grep -q "matches the before content" ||
  fail "unreadable subdir: expected the plain equal-content stop, got: $out"
[ "$code" -eq 2 ] || fail "unreadable subdir: exit $code, want 2"

echo "ok — all hook self-checks passed"
