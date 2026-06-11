#!/usr/bin/env bash
set -euo pipefail

PLIST="com.prakashjoshipax.VoiceInk"
APP="/Applications/VoiceInk.app"

active_app=$(osascript -e 'tell application "System Events" to get name of first application process whose frontmost is true' 2>/dev/null || echo "")

pkill -x VoiceInk || true
sleep 3
defaults write "$PLIST" SelectedLanguage "es"
open -g "$APP"

if [[ -n "$active_app" ]]; then
    osascript -e "tell application \"$active_app\" to activate" 2>/dev/null || true
fi

echo "status=done lang=es"
echo "VoiceInk → 🇪🇸 Spanish"
