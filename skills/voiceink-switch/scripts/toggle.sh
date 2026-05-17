#!/usr/bin/env bash
set -euo pipefail

PLIST="com.prakashjoshipax.VoiceInk"
APP="/Applications/VoiceInk.app"

# Capture active app before killing VoiceInk
active_app=$(osascript -e 'tell application "System Events" to get name of first application process whose frontmost is true' 2>/dev/null || echo "")

current=$(defaults read "$PLIST" SelectedLanguage 2>/dev/null || echo "en")

if [[ "$current" == "en" ]]; then
    new_lang="es"
    label="🇪🇸 Spanish"
else
    new_lang="en"
    label="🇺🇸 English"
fi

pkill -x VoiceInk || true
sleep 3
defaults write "$PLIST" SelectedLanguage "$new_lang"
open -g "$APP"

# Return focus to the previously active app
if [[ -n "$active_app" ]]; then
    osascript -e "tell application \"$active_app\" to activate" 2>/dev/null || true
fi

echo "status=done lang=$new_lang"
echo "VoiceInk → $label"
