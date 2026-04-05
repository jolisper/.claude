#!/bin/sh
# Outputs the model name to stdout for status line display.
# Returns empty string for default Anthropic models.
# Returns [display_name] for custom models (e.g., Ollama, /model opusplan).
# Format: [model-name] (with brackets) or empty.

# Priority order:
# 1. display_name field from input JSON (preferred for Ollama/custom models)
# 2. model field from input JSON (fallback for custom models)
# 3. cwd/.claude/settings.json model field
# 4. $HOME/.claude/settings.json model field

input=$(cat 2>/dev/null)

# Try input JSON first
configured_model=""
if echo "$input" | jq -e . >/dev/null 2>&1; then
   # Check if model is an object (custom model like Ollama, or /model <name>)
  model_type=$(echo "$input" | jq -r '.model | type')
  if [ "$model_type" = "object" ]; then
    # Custom model with display_name or id
    configured_model=$(echo "$input" | jq -r '.model.display_name // .model.id // ""')
  elif [ "$model_type" = "string" ]; then
    # Default Anthropic model (claude-*, sonnet, opus, haiku) - skip it
    configured_model=""
  fi
fi

# Fallback to cwd settings.json (for custom models configured there)
if [ -z "$configured_model" ]; then
  cwd=$(echo "$input" | jq -r '.workspace.current_dir // .cwd // ""' 2>/dev/null)
  if [ -n "$cwd" ] && [ -f "$cwd/.claude/settings.json" ]; then
    model_from_settings=$(jq -r '.model // ""' "$cwd/.claude/settings.json" 2>/dev/null)
    # Only set if it's a custom model (not a default Anthropic model)
    if [ -n "$model_from_settings" ]; then
      # Check if it's an Anthropic default model
      case "$model_from_settings" in
        claude-*|sonnet|opus|haiku|sonnet-3|sonnet-3.1|sonnet-3.2|sonnet-3.5|opusplan|opus-*)
          configured_model=""
           ;;
        *)
          configured_model="$model_from_settings"
           ;;
      esac
    fi
  fi
fi

# Fallback to global settings.json
if [ -z "$configured_model" ] && [ -f "$HOME/.claude/settings.json" ]; then
  model_from_settings=$(jq -r '.model // ""' "$HOME/.claude/settings.json" 2>/dev/null)
  # Only set if it's a custom model (not a default Anthropic model)
  if [ -n "$model_from_settings" ]; then
    case "$model_from_settings" in
      claude-*|sonnet|opus|haiku|sonnet-3|sonnet-3.1|sonnet-3.2|sonnet-3.5|opusplan|opus-*)
        configured_model=""
        ;;
      *)
        configured_model="$model_from_settings"
        ;;
    esac
  fi
fi

# Output with brackets if non-empty (custom model only)
if [ -n "$configured_model" ]; then
  echo "[$configured_model]"
fi
