#!/usr/bin/env bash
# Bridge-only publication: immutable generation base, one output commit, exact CAS.
# No rebase, merge, unrestricted force, automatic retry or reset is permitted.
set -euo pipefail

fail() { printf 'WRN bridge publication refused: %s\n' "$*" >&2; exit 1; }
check_only=false
if [[ "${1:-}" == --check-output-lineage ]]; then
  check_only=true
  shift
  set -- main "${1:-}"
fi
branch="${1:-}"
base="${2:-}"
[[ "$branch" == main ]] || fail 'only main is a permitted target'
[[ "$base" =~ ^[a-f0-9]{40}$ ]] || fail 'a full generation-base SHA is required'
[[ "$(git rev-parse --is-inside-work-tree)" == true ]] || fail 'not a worktree'
if [[ "$check_only" == false ]]; then
  [[ -z "$(git status --porcelain --untracked-files=normal)" ]] || fail 'worktree is not clean'
fi
[[ "$(git rev-parse --verify "${base}^{commit}")" == "$base" ]] || fail 'generation base is not an exact commit'
head="$(git rev-parse --verify 'HEAD^{commit}')"
read -r -a lineage <<< "$(git rev-list --parents -n 1 "$head")"
[[ "${#lineage[@]}" -eq 2 && "${lineage[1]}" == "$base" && "$head" != "$base" ]] \
  || fail 'HEAD must be exactly one non-merge commit directly on the generation base'

# A producer must not smuggle source/configuration changes into its data commit.
count=0
while IFS= read -r -d '' file; do
  case "$file" in
    news.json|news-feed.json|feed-status.json|news-archive-manifest.json|news-archive-capture.json|source-catalog.json|sources-registry.json|aggregate-errors.json|aggregate-run-status.json|events.json|events-feed.json|editorial-review.json|source-health.json|source-health-report.json|discovered-feeds.json|feature-audit.json|language-source-audit.json|source-discovery-report.json|source-health-history.json|source-recovery-report.json|source-category-audit.json) ;;
    news-archive/*.json)
      [[ "$file" =~ ^news-archive/[a-z0-9][a-z0-9_-]*\.json$ ]] || fail 'invalid archive output path'
      ;;
    *) fail "non-output path in publication commit: $file" ;;
  esac
  entry="$(git ls-tree "$head" -- "$file")"
  if [[ -n "$entry" ]]; then
    [[ "$entry" == '100644 blob '* ]] || fail "output is not a regular non-executable file: $file"
  fi
  count=$((count + 1))
done < <(git diff --name-only --no-renames -z "$base" "$head")
[[ "$count" -gt 0 ]] || fail 'empty publication commit'

# Read-only shared lineage check for recovery after a failed/uncertain push.
# This mode never verifies freshness, publishes, or claims remote acceptance.
if [[ "$check_only" == true ]]; then
  printf '%s\n' "$head"
  exit 0
fi

# Validate the exact committed generation, never merely trust a successful build.
python build_source_archive.py --verify-only --require-fresh
[[ -z "$(git status --porcelain --untracked-files=normal)" ]] || fail 'read-only verification changed the worktree'
[[ "$(git rev-parse HEAD)" == "$head" ]] || fail 'HEAD changed during verification'

remote_head() {
  local line oid ref extra
  line="$(git ls-remote --exit-code --refs origin "refs/heads/$branch")" || return 1
  [[ "$line" != *$'\n'* ]] || return 1
  read -r oid ref extra <<< "$line"
  [[ "$oid" =~ ^[a-f0-9]{40}$ && "$ref" == "refs/heads/$branch" && -z "${extra:-}" ]] || return 1
  printf '%s' "$oid"
}
remote="$(remote_head)" || fail 'cannot establish current remote state; no push attempted'
if [[ "$remote" == "$head" ]]; then
  printf 'WRN bridge output commit is already the remote head; no push repeated.\n'
  exit 0
fi
[[ "$remote" == "$base" ]] || fail 'remote moved after generation; rebuild and revalidate, do not rebase outputs'

# The explicit lease is server-side compare-and-swap, not permission to rewrite.
# The single-parent check above proves this exact update is a fast-forward from
# the leased base. Never remove the checks or add an unbound --force fallback.
if git push --force-with-lease="refs/heads/$branch:$base" origin "$head:refs/heads/$branch"; then
  verified="$(remote_head)" || fail 'push accepted but verification unavailable; outcome requires inspection, no retry'
  [[ "$verified" == "$head" ]] || fail 'push accepted but remote changed before verification; inspect before retry'
  printf 'WRN bridge output commit published and remote head verified.\n'
  exit 0
fi
# A transport failure can occur after acceptance. Inspect once, never retry.
verified="$(remote_head)" || fail 'push returned failure and current remote is unknown; inspect before retry'
if [[ "$verified" == "$head" ]]; then
  printf 'WRN bridge output commit verified on remote after transport failure; no retry.\n'
  exit 0
fi
fail 'push did not verify at the expected head; no automatic retry or rebase'
