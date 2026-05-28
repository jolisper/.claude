#!/usr/bin/env bash
# resolve-worktree-path.sh — sourceable helper for resolving worktree paths

expand_path() {
  local path="${1/#\~/$HOME}"
  if [[ "$path" != /* ]]; then
    path="$HOME/$path"
  fi
  echo "$path"
}

# Main block — only runs when executed directly, not when sourced
if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  set -eu
  if [[ "${1:-}" == "--help" ]]; then
    echo "Usage: resolve-worktree-path.sh [config-file]"
    echo ""
    echo "Reads worktrees_path from config-file (default: ~/.claude/worktree-config.json)"
    echo "and outputs the resolved absolute directory."
    echo ""
    echo "Exit codes:"
    echo "  0  Success. Empty stdout = use default path."
    echo "     stdout 'status=done path=<dir>' = use <dir> as worktree base."
    echo "  1  Error (unreadable file, invalid JSON, path is a file, mkdir failed). See stderr."
    echo ""
    echo "Example:"
    echo "  resolve-worktree-path.sh ~/.claude/worktree-config.json"
    exit 0
  fi
  config_path="${1:-~/.claude/worktree-config.json}"
  if [[ -z "$config_path" ]] || [[ ! -f "$config_path" ]]; then
    exit 0
  fi
  if [[ ! -r "$config_path" ]]; then
    echo "resolve-worktree-path: config file is not readable: $config_path" >&2
    exit 1
  fi
  first_char=$(read -rn1 first < "$config_path"; printf '%s' "$first")
  if [[ "$first_char" != "{" ]]; then
    echo "resolve-worktree-path: config file does not appear to be JSON (expected '{')" >&2
    exit 1
  fi
  worktrees_path=$(grep -o '"worktrees_path"[[:space:]]*:[[:space:]]*"[^"]*"' "$config_path" | sed 's/.*"\([^"]*\)"[[:space:]]*$/\1/') || true
  if [[ -z "$worktrees_path" ]]; then
    exit 0
  fi
  resolved=$(expand_path "$worktrees_path")
  if [[ -e "$resolved" && ! -d "$resolved" ]]; then
    echo "resolve-worktree-path: worktrees_path exists but is not a directory: $resolved" >&2
    exit 1
  fi
  if [[ ! -e "$resolved" ]]; then
    if ! mkdir -p "$resolved"; then
      echo "resolve-worktree-path: failed to create directory: $resolved" >&2
      exit 1
    fi
  fi
  echo "status=done path=$resolved"
  exit 0
fi
