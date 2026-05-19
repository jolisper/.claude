# Status Line Ollama API Integration

## Overview

Ollama's `/api/generate` and `/api/ps` endpoints provide all necessary metrics for the status line. No log parsing required.

## Ollama API Endpoints

### `/api/generate` (per-request)
Returns context and timing metrics:

```json
{
    "model": "qwen3.5:35b-a3b-coding-nvfp4",
    "prompt_eval_count": 12,        // input tokens
    "eval_count": 922,              // output tokens
    "total_duration": 14341267375, // ns
    "prompt_eval_duration": 100525208, // ns
    "eval_duration": 14210496250    // ns
}
```

### `/api/ps` (running models)
Returns model memory info:

```json
{
    "models": [
      {
        "name": "qwen3.5:35b-a3b-coding-nvfp4",
        "size_vram": 25267526954,    // VRAM usage
        "context_length": 262144     // max context
      }
    ]
}
```

### `/api/show` (model details)
Returns model config:

```json
{
    "details": {
      "parameter_size": "35.1B",
      "quantization_level": "nvfp4"
    },
    "model_info": {
      "general.architecture": "qwen3_5_moe",
      "context_length": 262144
    }
}
```

## Status Line Mapping

**Important:** Ollama doesn't expose the current context window config via its API. The status line gets context info from **Claude's own API response**, not from Ollama.

| Status Line Field | Source |
|-------------------|--------|
| **Model name** | Claude's JSON input (`.model` field) |
| **Context %** | Claude's API (`.context_window.used_percentage`) |
| **Input tokens** | Claude's API (`.cost.input_tokens`) |
| **Output tokens** | Claude's API (`.cost.output_tokens`) |
| **Response time** | Claude's API (`.cost.total_duration_ms`) |
| **GPU memory** | `/api/ps[].size_vram` (optional) |
| **Cache %** | `~/.ollama/logs/server.log` — `matched/total` from last `msg="cache hit"` line |
| **Rate limits** | Not available (hide for Ollama) |
| **Cost** | Not available (hide for Ollama) |

**Note:** For Ollama models, the context percentage and token counts come from Claude's API response, which wraps the Ollama calls. The cache hit % is parsed from the Ollama server log (`cache.go` emits a `msg="cache hit"` line after every request with `total`, `matched`, `cached`, and `left` fields). The last known value is persisted to `/tmp/ollama-cache-pct` so it survives log rotation gaps.

## Model Detection

The model name is provided in Claude's JSON input to the status line script:

```json
{
    "model": "qwen3.5:35b-a3b-coding-nvfp4",
    "rate_limits": {...}   // If present, it's Claude.ai
}
```

**Detection logic:**
```bash
# Extract model name from Claude's JSON input
configured_model=$(echo "$input" | jq -r '.model // empty')

# Check if model name suggests Ollama
case "$configured_model" in
  ollama/*|qwen*|llama*|gpt-oss*|glm*|deepseek*)
        # Possible Ollama model
        ollama_candidate=true
        ;;
esac

# Verify Ollama server is running before making API calls
if [ "$ollama_candidate" = "true" ]; then
  if curl -s --connect-timeout 1 http://localhost:11434/api/tags >/dev/null 2>&1; then
    is_ollama=true
  fi
fi
```

**Key indicators:**
- Model name starts with `qwen`, `llama`, `gpt-oss`, `glm`, `deepseek` → likely Ollama
- `rate_limits` field present → definitely Claude.ai
- Server responds to `localhost:11434` → Ollama is running

## Implementation Steps

1. Add model name extraction from input JSON
2. Add Ollama model name pattern matching (case statement on model prefixes)
3. Parse last `msg="cache hit"` line from `~/.ollama/logs/server.log` using `tail -300 | grep | tail -1`
4. Extract `total` and `matched` fields with `sed`; compute `cache_pct_val = matched * 100 / total`
5. Persist result to `/tmp/ollama-cache-pct`; fall back to persisted value when log parse yields nothing
6. Skip rate limits and cost sections for Ollama
7. Test with various Ollama models
