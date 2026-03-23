#!/usr/bin/env bash
set -e
if ! grep -q '^!settings\.json$' .gitignore; then
  sed -i '' 's/^!CLAUDE\.md$/!CLAUDE.md\n!settings.json/' .gitignore
fi
git add .gitignore settings.json
echo "settings.json is now tracked. Review and commit, then run untrack-settings.sh."
