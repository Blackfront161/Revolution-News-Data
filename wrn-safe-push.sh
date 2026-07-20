#!/usr/bin/env bash
set -euo pipefail

branch="${1:-${GITHUB_REF_NAME:-main}}"
attempts="${WRN_PUSH_ATTEMPTS:-3}"

if [[ -n "$(git status --porcelain)" ]]; then
  echo "FEHLER: Arbeitsbaum ist vor dem Rebase nicht sauber."
  git status --short
  exit 1
fi

for attempt in $(seq 1 "${attempts}"); do
  echo "WRN Push-Versuch ${attempt}/${attempts}"

  git fetch origin "${branch}"
  git rebase "origin/${branch}"

  if git push origin "HEAD:${branch}"; then
    echo "WRN Push erfolgreich."
    exit 0
  fi

  sleep $((attempt * 4))
done

echo "FEHLER: WRN Push nach ${attempts} Versuchen fehlgeschlagen."
exit 1
