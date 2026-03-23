#!/usr/bin/env bash
set -e
MSG="${1:?Usage: update-settings.sh <commit-message>}"

python3 scripts/migrate-settings.py
git add -f settings.json
git commit -m "$MSG"
git rm --cached settings.json
echo "settings.json committed and untracked."
