#!/bin/sh
# Outputs the model name to stdout for status line display.
# Returns [model-name] when a model is configured.
# Returns empty string when no model is configured.

input=$(cat 2>/dev/null)

# Try input JSON first
configured_model=""
if echo "$input" | jq -e . >/dev/null 2>&1; then
  configured_model=$(echo "$input" | jq -r '.model.display_name // .model // ""')
fi

# Fallback to cwd settings.json
if [ -z "$configured_model" ]; then
  cwd=$(echo "$input" | jq -r '.workspace.current_dir // .cwd // ""' 2>/dev/null)
  if [ -n "$cwd" ] && [ -f "$cwd/.claude/settings.json" ]; then
    configured_model=$(jq -r '.model // ""' "$cwd/.claude/settings.json" 2>/dev/null)
  fi
fi

# Fallback to global settings.json
if [ -z "$configured_model" ] && [ -f "$HOME/.claude/settings.json" ]; then
  configured_model=$(jq -r '.model // ""' "$HOME/.claude/settings.json" 2>/dev/null)
fi

# Output with brackets if non-empty
if [ -n "$configured_model" ]; then
  echo "[$configured_model]"
fi
