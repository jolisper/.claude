---
name: warp-theme-from-macos
description: >
  Use this skill to generate a Warp terminal theme from the currently active macOS
  aerial wallpaper. Extracts dominant colors from the aerial thumbnail and a 4K still
  from the video, then writes a .yaml + .jpg pair to ~/.warp/themes/. Only works when
  the active wallpaper uses the aerials provider — fails gracefully otherwise.
  Invoke when the user wants to create a Warp theme matching their macOS aerial wallpaper.
disable-model-invocation: true
allowed-tools: Bash(bash:*) Bash(qlmanage:*) Bash(sips:*) Write Read
argument-hint: "[--alt]"
---

## Arguments

If `$ARGUMENTS` contains `--alt`, use the alternative (pywal-style) color mapper. This affects Step 2 (adds `--alt` to the extract-colors call) and Steps 4–5 (appends `(Alt)` to the theme name and uses `<slug>-alt` as the file stem).

## Available scripts

- `~/.claude/skills/warp-theme-from-macos/scripts/detect.sh` — confirms aerials provider, resolves UUID, display name, slug, and file paths; outputs `key=value` lines
- `~/.claude/skills/warp-theme-from-macos/scripts/extract-colors.sh` — pure-Python PNG decoder; maps dominant thumbnail colors to Warp theme roles; outputs `key=value` hex lines; accepts `--alt` for pywal-style mapping

## Step 1 — Detect the active aerial

Run `bash ~/.claude/skills/warp-theme-from-macos/scripts/detect.sh` and parse each output line as `key=value`.

**If `status=not-aerial`:** stop and tell the user:
> "Your current wallpaper is not a macOS aerial. This skill only works with aerial
> wallpapers. Go to System Settings → Wallpaper, select an aerial from the Cityscape
> or Nature categories, then try again."

**If `status=error`:** stop and report: "Detection failed: `<reason>`. Check that macOS wallpaper data is intact at `~/Library/Application Support/com.apple.wallpaper/`."

**If `status=ok`:** capture `uuid`, `name`, `slug`, `thumbnail`, `video` and continue.

## Step 2 — Extract dominant colors

If `--alt` was passed, append `--alt` to the extract-colors command below.

If `thumbnail` is non-empty, run:
`bash ~/.claude/skills/warp-theme-from-macos/scripts/extract-colors.sh --thumbnail <thumbnail> [--alt]`

If `thumbnail` is empty (system default wallpaper), first extract a small still from the video for color sampling:
`qlmanage -t -s 256 -o /tmp/ <video>`
Then run:
`bash ~/.claude/skills/warp-theme-from-macos/scripts/extract-colors.sh --thumbnail /tmp/<slug>.mov.png [--alt]`

Parse each output line as `key=value`. Expected keys: `background`, `foreground`, `accent`, `cursor`, and the 16 ANSI keys (`normal_black` … `bright_white`).

**If the script exits non-zero:** stop and report: "Color extraction failed. Check that the thumbnail exists and is a valid PNG."

## Step 3 — Extract a background image

Run these as two separate Bash calls — do not chain them:

1. `qlmanage -t -s 3840 -o /tmp/ <video>`
2. `sips -s format jpeg -s formatOptions 90 /tmp/<uuid>.mov.png --out ~/.warp/themes/<slug>.jpg`

**After step 1:** verify `/tmp/<uuid>.mov.png` exists with Read. If it does not, stop and report: "Frame extraction failed — qlmanage produced no output. The video at `<video>` may be incomplete or still downloading."

**If step 2 fails:** stop and report the sips error.

## Step 4 — Write the theme file

If `--alt` was passed: use `<name> (Alt)` as the theme name and `<slug>-alt` as the file stem. Otherwise use `<name>` and `<slug>`.

Write `~/.warp/themes/<file-stem>.yaml` with this structure — substitute all `<…>` with values from the previous steps:

```yaml
name: <theme-name>
details: darker
background: '<background>'
foreground: '<foreground>'
accent: '<accent>'
cursor: '<cursor>'
background_image:
  path: <slug>.jpg
  opacity: 15
terminal_colors:
  normal:
    black: '<normal_black>'
    red: '<normal_red>'
    green: '<normal_green>'
    yellow: '<normal_yellow>'
    blue: '<normal_blue>'
    magenta: '<normal_magenta>'
    cyan: '<normal_cyan>'
    white: '<normal_white>'
  bright:
    black: '<bright_black>'
    red: '<bright_red>'
    green: '<bright_green>'
    yellow: '<bright_yellow>'
    blue: '<bright_blue>'
    magenta: '<bright_magenta>'
    cyan: '<bright_cyan>'
    white: '<bright_white>'
```

`opacity` must be the integer `15`, not the float `0.15` — a float silently drops the theme from Warp's list with no error message.

Note: `background_image.path` always uses `<slug>.jpg` (not `<slug>-alt.jpg`) — both variants share the same background image.

## Step 5 — Confirm

Report:

```
Theme created: <theme-name>
  YAML  → ~/.warp/themes/<file-stem>.yaml
  Image → ~/.warp/themes/<slug>.jpg

To apply: Warp → Settings → Appearance → Theme → Custom → <theme-name>
```
