#!/bin/sh
# Outputs "true" if ANTHROPIC_BASE_URL points to a local network address,
# "false" otherwise. Used by statusline and hooks to detect Ollama/local mode.

if [ -z "$ANTHROPIC_BASE_URL" ]; then
  echo "false"
  exit 0
fi

_host=$(echo "$ANTHROPIC_BASE_URL" | sed 's|^[a-z]*://||; s|[:/].*||')
case "$_host" in
  localhost|127.*|0.0.0.0|\[::1\])        echo "true"  ;;
  10.*|192.168.*)                          echo "true"  ;;
  172.1[6-9].*|172.2[0-9].*|172.3[0-1].*) echo "true" ;;
  169.254.*|\[fe80:*\])                    echo "true"  ;;
  *.local)                                 echo "true"  ;;
  *)                                       echo "false" ;;
esac
