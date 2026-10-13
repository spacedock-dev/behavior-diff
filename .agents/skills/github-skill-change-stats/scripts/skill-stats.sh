#!/usr/bin/env bash
# Print a Markdown table of the most-changed skills in each GitHub repository.
# Usage: skill-stats.sh [--top N] [--cache DIR] OWNER/REPO|URL...
set -euo pipefail

top=20
cache="${TMPDIR:-/tmp}/github-skill-change-stats"
repos=()
while (($#)); do
  case "$1" in
    --top)
      top="$2"
      shift 2
      ;;
    --cache)
      cache="$2"
      shift 2
      ;;
    -h | --help)
      sed -n '2,3p' "$0"
      exit 0
      ;;
    *)
      repos+=("$1")
      shift
      ;;
  esac
done
if ((${#repos[@]} == 0)); then
  printf 'usage: %s [--top N] [--cache DIR] OWNER/REPO|URL...\n' "$0" >&2
  exit 2
fi

# A skill is the first directory under any `skills/` directory. Paths under a
# top-level dot directory (.agents/, .claude/) are repository-maintainer skills
# and are skipped. Old and new paths of a moved skill merge by directory name.
skill_of='
function skill(path,  s) {
  if (path ~ /^\./ || !match(path, /(^|\/)skills\/[^\/]+\//)) return ""
  s = substr(path, RSTART, RLENGTH); sub(/.*skills\//, "", s); sub(/\/$/, "", s)
  return s
}'

stats() {
  local dir="$1"
  {
    # Commits: every commit in history, counted once per skill.
    git -C "$dir" log --format='@C %h %ad' --date=short --name-only
    # PRs: the #NUMBER in each main-line commit subject, counted once per skill.
    git -C "$dir" log --first-parent -m --format='@P %h %s' --name-only
  } | awk "$skill_of"'
    /^@C / { mode = "C"; c = $2; d = $3; next }
    /^@P / { mode = "P"; c = $2; pr = ""
             if (match($0, /#[0-9]+/)) pr = substr($0, RSTART, RLENGTH); next }
    NF == 0 { next }
    { s = skill($0); if (s == "") next }
    mode == "C" && !seen[c, s]++ {
      n[s]++
      if (d > last[s]) last[s] = d
      if (first[s] == "" || d < first[s]) first[s] = d
    }
    mode == "P" && pr != "" && !pseen[pr, s]++ { p[s]++ }
    END { for (s in n) printf "%d\t%d\t%s\t%s\t%s\n", p[s], n[s], s, first[s], last[s] }
  ' | sort -t "$(printf '\t')" -k1,1nr -k2,2nr -k3,3
}

for repo in "${repos[@]}"; do
  slug="${repo#https://github.com/}"
  slug="${slug%.git}"
  slug="${slug%/}"
  dir="$cache/${slug//\//__}"
  if [[ -d "$dir" ]]; then
    git -C "$dir" fetch -q origin
    git -C "$dir" update-ref HEAD FETCH_HEAD
  else
    mkdir -p "$cache"
    if ! git clone -q --filter=blob:none --no-checkout \
      "https://github.com/$slug" "$dir"; then
      printf '## %s\n\nSkipped: clone failed.\n\n' "$slug"
      continue
    fi
  fi

  total="$(git -C "$dir" rev-list --count HEAD)"
  with_pr="$(git -C "$dir" log --format=%s | grep -cE '#[0-9]+' || true)"
  printf '## %s\n\n' "$slug"
  printf 'HEAD %s · %s commits · %s with a PR number\n\n' \
    "$(git -C "$dir" log -1 --format='%h %ad' --date=short)" "$total" "$with_pr"
  printf '| # | Skill | PRs | Commits | First change | Last change |\n'
  printf '|---|---|---|---|---|---|\n'
  stats "$dir" | head -n "$top" |
    awk -F '\t' '{ printf "| %d | %s | %s | %s | %s | %s |\n", NR, $3, $1, $2, $4, $5 }'
  printf '\n'
done
