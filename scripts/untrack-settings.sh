#!/usr/bin/env bash
set -e
sed -i '' '/^!settings\.json$/d' .gitignore
git rm --cached settings.json
echo "settings.json is now untracked. Commit the .gitignore change."
