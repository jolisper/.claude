# VoiceInk Language Switcher — Spec

## Goal

A Claude Code skill (`/voiceink-lang`) that switches VoiceInk's transcription language (Spanish ↔ English) from the terminal without interrupting the user's workflow.

## Background

VoiceInk uses OpenAI's Whisper model for transcription. The transcription language is controlled by the `SelectedLanguage` key in the plist. This key **survives app restarts** — unlike `TranscriptionPrompt`, which VoiceInk overwrites on launch with its UI-set value.

The transcription prompt (Output Format field in UI) also influences output language, but `SelectedLanguage` is the reliable mechanism.

Relevant plist keys:
- `SelectedLanguage` — language code (e.g. `en`, `es`). Survives restarts. ✓
- `TranscriptionPrompt` — Whisper initial prompt. Gets overwritten by VoiceInk on launch. ✗

Plist location:
`~/Library/Preferences/com.prakashjoshipax.VoiceInk.plist`

## Implementation approach

Use `defaults write` to update `SelectedLanguage`, then restart VoiceInk. The sequence must be:

1. `pkill -x VoiceInk`
2. `sleep 3` (wait for full quit)
3. `defaults write com.prakashjoshipax.VoiceInk SelectedLanguage <code>`
4. `open -g /Applications/VoiceInk.app` (`-g` launches without stealing focus)

No AppleScript or UI automation needed.

### Language codes

| Language | Code |
|---|---|
| Spanish | `es` |
| English | `en` |

## Known limitations

- VoiceInk must restart to pick up the language change — brief interruption unavoidable
- Automatic multilingual detection (no restart needed) is not supported yet ([issue #518](https://github.com/Beingpax/VoiceInk/issues/518))

## Skill interface

Una sola skill que alterna entre inglés y español:

```
/voiceink-switch
```

Lee el `SelectedLanguage` actual del plist y cambia al otro:
- Si está en `en` → cambia a `es`
- Si está en `es` → cambia a `en`

Al finalizar, imprime el idioma activo en la consola antes de devolver el foco:

```
VoiceInk → 🇪🇸 Spanish
```
```
VoiceInk → 🇺🇸 English
```

## Prerequisites

- VoiceInk must be running
- Accessibility permissions enabled for the terminal app in System Settings → Privacy & Security → Accessibility
