#!/bin/sh
# Outputs the model name to stdout for status line display.
# Returns empty string if no model is configured.
# Format: [model-name] (with brackets) or empty.

# Priority order:
# 1. display_name field from input JSON (preferred for Ollama)
# 2. model field from input JSON (fallback)
# 3. cwd/.claude/settings.json model field
# 4. $HOME/.claude/settings.json model field

input=$(cat 2>/dev/null)

# Try input JSON first - prefer display_name over model
configured_model=""
if echo "$input" | jq -e . >/dev/null 2>&1; then
  # Check if model is an object (has display_name or id field)
  model_type=$(echo "$input" | jq -r '.model | type')
  if [ "$model_type" = "object" ]; then
    configured_model=$(echo "$input" | jq -r '.model.display_name // .model.id // ""')
  else
    configured_model=$(echo "$input" | jq -r '.model // ""')
  fi
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
