#!/usr/bin/env bash
set -euo pipefail

# detect.sh — Identifies the active macOS wallpaper (aerial or system default).
#
# Output (stdout): key=value lines
#   status=ok
#   name=<display name>
#   slug=<kebab-slug>
#   thumbnail=<path>   (aerials only; empty for system wallpapers)
#   video=<path>
#
#   status=error
#   reason=<message>

WALLPAPER_BASE="$HOME/Library/Application Support/com.apple.wallpaper"
PLIST="$WALLPAPER_BASE/Store/Index.plist"
AERIALS_DIR="$WALLPAPER_BASE/aerials"
ENTRIES_JSON="$AERIALS_DIR/manifest/entries.json"
LOCTABLE="$AERIALS_DIR/manifest/TVIdleScreenStrings.bundle/Contents/Resources/Localizable.nocache.loctable"
SYSTEM_WALLPAPERS="/System/Library/Desktop Pictures/.wallpapers"

if [[ ! -f "$PLIST" ]]; then
  echo "status=error"
  echo "reason=Wallpaper plist not found at $PLIST"
  exit 0
fi

PROVIDER=$(python3 -c "
import plistlib, pathlib, sys
p = pathlib.Path('$PLIST')
with open(p, 'rb') as f:
    d = plistlib.load(f)
choices = (d.get('AllSpacesAndDisplays') or d.get('SystemDefault', {})).get('Linked', {}).get('Content', {}).get('Choices', [{}])
print(choices[0].get('Provider', '') if choices else '')
" 2>/dev/null || true)

# ── Aerial ────────────────────────────────────────────────────────────────────

if [[ "$PROVIDER" == "com.apple.wallpaper.choice.aerials" ]]; then
  VIDEO=$(ls -t "$AERIALS_DIR/videos/"*.mov 2>/dev/null | head -1 || true)
  if [[ -z "$VIDEO" ]]; then
    echo "status=error"
    echo "reason=No aerial video found in $AERIALS_DIR/videos/ — the aerial may still be downloading"
    exit 0
  fi

  UUID=$(basename "$VIDEO" .mov)
  THUMBNAIL="$AERIALS_DIR/thumbnails/$UUID.png"

  if [[ ! -f "$THUMBNAIL" ]]; then
    echo "status=error"
    echo "reason=Thumbnail not found at $THUMBNAIL"
    exit 0
  fi

  RESULT=$(UUID="$UUID" ENTRIES="$ENTRIES_JSON" LOCTABLE="$LOCTABLE" python3 << 'PYEOF'
import json, subprocess, os, sys

uuid = os.environ['UUID']
entries_path = os.environ['ENTRIES']
loctable_path = os.environ['LOCTABLE']

try:
    with open(entries_path) as f:
        data = json.load(f)
except Exception as e:
    print(f"error:Could not read entries.json: {e}", file=sys.stderr)
    sys.exit(1)

shotid = ''
for asset in data.get('assets', []):
    if asset.get('id') == uuid:
        shotid = asset.get('shotID', '')
        break

if not shotid:
    print(f"error:UUID {uuid} not found in entries.json", file=sys.stderr)
    sys.exit(1)

name = shotid  # fallback
try:
    result = subprocess.run(
        ['plutil', '-convert', 'json', '-o', '-', loctable_path],
        capture_output=True, check=True
    )
    en = json.loads(result.stdout).get('en', {})
    name = en.get(f'{shotid}_NAME', '') or shotid
except Exception:
    pass

print(f"shotid:{shotid}\nname:{name}")
PYEOF
  )

  if echo "$RESULT" | grep -q "^error:"; then
    echo "status=error"
    echo "reason=$(echo "$RESULT" | grep "^error:" | sed 's/^error://')"
    exit 0
  fi

  NAME=$(echo "$RESULT" | grep "^name:" | sed 's/^name://')
  SLUG=$(echo "$NAME" | tr '[:upper:]' '[:lower:]' | sed 's/ /-/g' | tr -cd '[:alnum:]-')

  echo "status=ok"
  echo "name=$NAME"
  echo "slug=$SLUG"
  echo "thumbnail=$THUMBNAIL"
  echo "video=$VIDEO"
  exit 0
fi

# ── System default (.wallpapers) ──────────────────────────────────────────────

if [[ "$PROVIDER" == "default" || -z "$PROVIDER" ]]; then
  # Read SystemWallpaperURL from defaults → extract wallpaper name
  WP_URL=$(defaults read com.apple.wallpaper SystemWallpaperURL 2>/dev/null || true)
  WP_NAME=""
  if [[ -n "$WP_URL" ]]; then
    # URL form: file:///System/Library/Desktop%20Pictures/.wallpapers/Tahoe%20Day/Tahoe%20Day.mov
    WP_NAME=$(python3 -c "
from urllib.parse import unquote
import sys, os
url = '$WP_URL'
path = unquote(url.replace('file://', ''))
print(os.path.basename(os.path.dirname(path)))
" 2>/dev/null || true)
  fi

  VIDEO=""

  # Try exact path from URL first
  if [[ -n "$WP_URL" ]]; then
    EXACT=$(python3 -c "
from urllib.parse import unquote
print(unquote('$WP_URL'.replace('file://', '')))
" 2>/dev/null || true)
    if [[ -f "$EXACT" ]]; then
      VIDEO="$EXACT"
    fi
  fi

  # Fall back: find by name in .wallpapers
  if [[ -z "$VIDEO" && -n "$WP_NAME" && -d "$SYSTEM_WALLPAPERS/$WP_NAME" ]]; then
    VIDEO=$(find "$SYSTEM_WALLPAPERS/$WP_NAME" -name "*.mov" | head -1 || true)
  fi

  # Last resort: most recently modified package in .wallpapers
  if [[ -z "$VIDEO" && -d "$SYSTEM_WALLPAPERS" ]]; then
    VIDEO=$(find "$SYSTEM_WALLPAPERS" -name "*.mov" -not -path "*/.git/*" | head -1 || true)
    if [[ -n "$VIDEO" ]]; then
      WP_NAME=$(basename "$(dirname "$VIDEO")")
    fi
  fi

  if [[ -z "$VIDEO" ]]; then
    echo "status=error"
    echo "reason=Could not locate a wallpaper video in $SYSTEM_WALLPAPERS"
    exit 0
  fi

  [[ -z "$WP_NAME" ]] && WP_NAME=$(basename "$(dirname "$VIDEO")")
  SLUG=$(echo "$WP_NAME" | tr '[:upper:]' '[:lower:]' | sed 's/ /-/g' | tr -cd '[:alnum:]-')

  echo "status=ok"
  echo "name=$WP_NAME"
  echo "slug=$SLUG"
  echo "thumbnail="
  echo "video=$VIDEO"
  exit 0
fi

# ── Unsupported provider ───────────────────────────────────────────────────────

echo "status=error"
echo "reason=Unsupported wallpaper provider: $PROVIDER. This skill supports aerials and system default wallpapers only."
