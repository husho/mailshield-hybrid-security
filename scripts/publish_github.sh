#!/usr/bin/env bash
set -euo pipefail

REPO_NAME="${1:-mailshield-hybrid-security}"
VISIBILITY="${2:-public}"

if ! command -v gh >/dev/null 2>&1; then
  echo "[error] GitHub CLI (gh) not found"
  exit 1
fi

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "[error] not a git repository"
  exit 1
fi

if [ -z "$(git rev-parse --verify HEAD 2>/dev/null || true)" ]; then
  echo "[error] no commit yet; create initial commit first"
  exit 1
fi

if ! gh auth status >/dev/null 2>&1; then
  echo "[error] gh is not authenticated"
  exit 1
fi

if ! git remote get-url origin >/dev/null 2>&1; then
  echo "[info] creating GitHub repo: $REPO_NAME ($VISIBILITY)"
  gh repo create "$REPO_NAME" --"$VISIBILITY" --source . --remote origin --push
else
  echo "[info] origin already exists; pushing current branch"
  git push -u origin "$(git branch --show-current)"
fi

echo "[ok] publish completed"
