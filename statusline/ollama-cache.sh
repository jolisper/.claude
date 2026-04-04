#!/bin/sh
# Reads the last KV cache hit line from the Ollama server log and outputs
# the cache hit percentage (0-100) as an integer to stdout.
# Persists the last known value to /tmp/ollama-cache-pct for log rotation resilience.
# Outputs nothing if no data is available.

ollama_cache_file="/tmp/ollama-cache-pct"
ollama_log="$HOME/.ollama/logs/server.log"
cache_pct_val=0

if [ -f "$ollama_log" ]; then
  cache_line=$(tail -300 "$ollama_log" | grep 'msg="cache hit"' | tail -1)
  if [ -n "$cache_line" ]; then
    cache_total_kv=$(echo "$cache_line" | sed -n 's/.*total=\([0-9]*\).*/\1/p')
    cache_matched=$(echo "$cache_line" | sed -n 's/.*matched=\([0-9]*\).*/\1/p')
    if [ -n "$cache_total_kv" ] && [ "$cache_total_kv" -gt 0 ] 2>/dev/null; then
      cache_pct_val=$(awk "BEGIN {printf \"%.0f\", $cache_matched * 100 / $cache_total_kv}")
      [ "$cache_pct_val" -gt 100 ] && cache_pct_val=100
      echo "$cache_pct_val" > "$ollama_cache_file"
    fi
  fi
fi

if [ "$cache_pct_val" -eq 0 ] && [ -f "$ollama_cache_file" ]; then
  saved_val=$(cat "$ollama_cache_file")
  [ -n "$saved_val" ] && cache_pct_val=$saved_val
fi

[ "$cache_pct_val" -gt 0 ] && echo "$cache_pct_val"