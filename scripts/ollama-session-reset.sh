#!/usr/bin/env bash
# UserPromptSubmit hook — called on every prompt.
# On new session start (first prompt after /clear or fresh launch):
#   1. Records session start time (used by the statusline for elapsed time).
#   2. If running in local/Ollama mode, unloads the current model to clear KV cache.

input=$(cat)

sid=$(echo "$input" | jq -r '.session_id // ""')
[ -z "$sid" ] && exit 0

sentinel="/tmp/claude-session-start-$sid"

# Already seen this session — nothing to do
[ -f "$sentinel" ] && exit 0

# New session: record start time
date +%s > "$sentinel"

is_local=$(sh "$HOME/.claude/statusline/is-local-mode.sh")
[ "$is_local" = "false" ] && exit 0

# Resolve model name from Anthropic env vars set by the Ollama launch subcommand
model="${ANTHROPIC_DEFAULT_SONNET_MODEL:-${ANTHROPIC_DEFAULT_OPUS_MODEL:-${ANTHROPIC_DEFAULT_HAIKU_MODEL:-}}}"
[ -z "$model" ] && exit 0

ollama_url="${ANTHROPIC_BASE_URL:-http://localhost:11434}"

curl -s "$ollama_url/api/generate" \
  -d "{\"model\":\"$model\",\"keep_alive\":0}" > /dev/null
