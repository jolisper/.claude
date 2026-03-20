#!/bin/sh
# Claude Code status line — mirrors ~/.zshrc PROMPT style
# Format: dirname (branch*) | [model] bar ctx% (cache%) | rate_limits | dur (api think%) | cost

input=$(cat)

cwd=$(echo "$input" | jq -r '.workspace.current_dir // .cwd // ""')
dirname=$(basename "$cwd")
now=$(date +%s)

# Section toggles — defaults (all on except lines)
branch=on; model=on; ctx_bar=on; cache_pct=on; coherence_warning=on
rate_limits=on; sess_duration=on; wall_time=on; api_duration=on
think_pct=on; lines=off; cost=on; time=on

# Override from config file if it exists
conf="$HOME/.claude/statusline.conf"
[ -f "$conf" ] && . "$conf"

# Git branch + dirty flag + diff stats
branch_str=""
if [ "$branch" = "on" ]; then
  if git -C "$cwd" rev-parse --git-dir >/dev/null 2>&1; then
    _branch=$(git -C "$cwd" branch --no-color 2>/dev/null | sed -n 's/^\* //p')
    if [ -n "$_branch" ]; then
      dirty=$(git -C "$cwd" status --porcelain 2>/dev/null)
      [ -n "$dirty" ] && _branch="${_branch}*"

      # Sum all added/removed lines (staged + unstaged) vs HEAD
      diff_stats=$(git -C "$cwd" diff HEAD --numstat 2>/dev/null)
      if [ -n "$diff_stats" ]; then
        diff_added=$(echo "$diff_stats" | awk '{s+=$1} END {print s+0}')
        diff_removed=$(echo "$diff_stats" | awk '{s+=$2} END {print s+0}')
      else
        diff_added=0
        diff_removed=0
      fi

      if [ "$diff_added" -gt 0 ] || [ "$diff_removed" -gt 0 ]; then
        branch_str=" (${_branch} +${diff_added}/-${diff_removed})"
      else
        branch_str=" (${_branch})"
      fi
    fi
  fi
fi

# Context window percentage — always computed (coherence_warning needs ctx_pct)
ctx_pct=$(echo "$input" | jq -r '.context_window.used_percentage // 0' | awk '{printf "%.0f", $1}')

# Progress bar — only built when ctx_bar is on
bar=""
if [ "$ctx_bar" = "on" ]; then
  filled=$(( ctx_pct * 10 / 100 ))
  empty=$(( 10 - filled ))
  if [ "$ctx_pct" -le 50 ]; then
    color=$(printf '\033[32m')   # green  (0–50%)
  elif [ "$ctx_pct" -le 75 ]; then
    color=$(printf '\033[33m')   # yellow (51–75%)
  else
    color=$(printf '\033[31m')   # red    (76–100%)
  fi
  reset=$(printf '\033[0m')
  bar="${color}"
  i=0
  while [ $i -lt $filled ]; do bar="${bar}▓"; i=$(( i + 1 )); done
  bar="${bar}${reset}"
  i=0
  while [ $i -lt $empty ];  do bar="${bar}░"; i=$(( i + 1 )); done
fi

# Session cost
cost_str=""
if [ "$cost" = "on" ]; then
  cost_str=$(echo "$input" | jq -r '.cost.total_cost_usd // 0' | awk '{printf "$%.2f", $1}')
fi

# Wall-clock duration from total_duration_ms (always parsed — think_pct also needs duration_ms)
duration_ms=$(echo "$input" | jq -r '.cost.total_duration_ms // 0' | awk '{printf "%.0f", $1}')
duration_str=""
if [ "$wall_time" = "on" ]; then
  dur_s=$(( duration_ms / 1000 ))
  dur_m=$(( dur_s / 60 ))
  dur_s=$(( dur_s % 60 ))
  dur_h=$(( dur_m / 60 ))
  dur_m=$(( dur_m % 60 ))
  dur_d=$(( dur_h / 24 ))
  dur_h=$(( dur_h % 24 ))
  if [ "$dur_d" -gt 0 ]; then
    duration_str=$(printf "%dd%02dh%02dm" "$dur_d" "$dur_h" "$dur_m")
  elif [ "$dur_h" -gt 0 ]; then
    duration_str=$(printf "%dh%02dm%02ds" "$dur_h" "$dur_m" "$dur_s")
  else
    duration_str=$(printf "%dm%02ds" "$dur_m" "$dur_s")
  fi
fi

# Session elapsed time since first prompt (written by UserPromptSubmit hook)
sess_duration_str=""
if [ "$sess_duration" = "on" ]; then
  session_id=$(echo "$input" | jq -r '.session_id // ""')
  session_start_file="/tmp/claude-session-start-${session_id}"
  if [ -n "$session_id" ] && [ -f "$session_start_file" ]; then
    session_start=$(cat "$session_start_file")
    elapsed_s=$(( now - session_start ))
    el_m=$(( elapsed_s / 60 ))
    el_s=$(( elapsed_s % 60 ))
    el_h=$(( el_m / 60 ))
    el_m=$(( el_m % 60 ))
    el_d=$(( el_h / 24 ))
    el_h=$(( el_h % 24 ))
    if [ "$el_d" -gt 0 ]; then
      sess_duration_str=$(printf "%dd%02dh%02dm" "$el_d" "$el_h" "$el_m")
    elif [ "$el_h" -gt 0 ]; then
      sess_duration_str=$(printf "%dh%02dm%02ds" "$el_h" "$el_m" "$el_s")
    else
      sess_duration_str=$(printf "%dm%02ds" "$el_m" "$el_s")
    fi
  fi
fi

# API duration + think percentage (share one jq call when either is on)
api_duration_str=""
think_pct_val=0
if [ "$api_duration" = "on" ] || [ "$think_pct" = "on" ]; then
  api_ms=$(echo "$input" | jq -r '.cost.total_api_duration_ms // 0' | awk '{printf "%.0f", $1}')
  if [ "$api_duration" = "on" ]; then
    api_s=$(( api_ms / 1000 ))
    api_m=$(( api_s / 60 ))
    api_s=$(( api_s % 60 ))
    api_h=$(( api_m / 60 ))
    api_m=$(( api_m % 60 ))
    if [ "$api_h" -gt 0 ]; then
      api_duration_str=$(printf "%dh%02dm%02ds" "$api_h" "$api_m" "$api_s")
    else
      api_duration_str=$(printf "%dm%02ds" "$api_m" "$api_s")
    fi
  fi
  if [ "$think_pct" = "on" ]; then
    think_pct_val=$(awk "BEGIN {printf \"%.0f\", ($api_ms > 0 && $duration_ms > 0) ? $api_ms * 100 / $duration_ms : 0}")
  fi
fi

# Rate limit usage (Claude.ai subscription — only present after first API response)
rate_limits_str=""
if [ "$rate_limits" = "on" ]; then
  five_pct=$(echo "$input" | jq -r '.rate_limits.five_hour.used_percentage // empty')
  five_resets_at=$(echo "$input" | jq -r '.rate_limits.five_hour.resets_at // empty')
  week_pct=$(echo "$input" | jq -r '.rate_limits.seven_day.used_percentage // empty')
  week_resets_at=$(echo "$input" | jq -r '.rate_limits.seven_day.resets_at // empty')

  fmt_remaining() {
    remaining=$(( $1 - now ))
    [ "$remaining" -lt 0 ] && remaining=0
    r_d=$(( remaining / 86400 ))
    r_h=$(( (remaining % 86400) / 3600 ))
    r_m=$(( (remaining % 3600) / 60 ))
    if [ "$r_d" -gt 0 ]; then
      printf "%dd%02dh" "$r_d" "$r_h"
    elif [ "$r_h" -gt 0 ]; then
      printf "%dh%02dm" "$r_h" "$r_m"
    else
      printf "%dm" "$r_m"
    fi
  }

  if [ -n "$five_pct" ] || [ -n "$week_pct" ]; then
    if [ -n "$five_pct" ]; then
      five_str="$(printf '%.0f' "$five_pct")%"
      [ -n "$five_resets_at" ] && five_str="${five_str}($(fmt_remaining "$five_resets_at"))"
      rate_limits_str="$five_str"
    fi
    if [ -n "$week_pct" ]; then
      week_str="$(printf '%.0f' "$week_pct")%"
      [ -n "$week_resets_at" ] && week_str="${week_str}($(fmt_remaining "$week_resets_at"))"
      rate_limits_str="${rate_limits_str:+$rate_limits_str }$week_str"
    fi
  fi
fi

# Cache hit ratio — always computed when either cache_pct display or coherence_warning is on
cache_pct_val=0
cache_pct_str=""
if [ "$cache_pct" = "on" ] || [ "$coherence_warning" = "on" ]; then
  cache_read=$(echo "$input" | jq -r '.context_window.current_usage.cache_read_input_tokens // 0')
  cache_create=$(echo "$input" | jq -r '.context_window.current_usage.cache_creation_input_tokens // 0')
  cache_input=$(echo "$input" | jq -r '.context_window.current_usage.input_tokens // 0')
  cache_total=$(( cache_read + cache_create + cache_input ))
  if [ "$cache_total" -gt 0 ]; then
    cache_pct_val=$(awk "BEGIN {printf \"%.0f\", $cache_read * 100 / $cache_total}")
    [ "$cache_pct" = "on" ] && cache_pct_str="(${cache_pct_val}%)"
  fi
fi

# Model label — only shown when a non-default model is configured
model_label_str=""
if [ "$model" = "on" ]; then
  configured_model=""
  if [ -f "$cwd/.claude/settings.json" ]; then
    configured_model=$(jq -r '.model // ""' "$cwd/.claude/settings.json")
  fi
  if [ -z "$configured_model" ] && [ -f "$HOME/.claude/settings.json" ]; then
    configured_model=$(jq -r '.model // ""' "$HOME/.claude/settings.json")
  fi
  if [ -n "$configured_model" ]; then
    model_label_str="[$configured_model] "
  fi
fi

# Coherence warning: red dot when context is large and cache is cold
warning=""
if [ "$coherence_warning" = "on" ]; then
  if [ "$ctx_pct" -gt 50 ] && [ "$cache_pct_val" -lt 20 ]; then
    warning="$(printf '\033[5;31m')●$(printf '\033[0m') "
  fi
fi

# Context block: bar + ctx% + optional cache% in parentheses
ctx_block="${warning}${bar} ${ctx_pct}%"
[ -n "$cache_pct_str" ] && ctx_block="${ctx_block} ${cache_pct_str}"

# Lines added/removed (session total from cost object)
lines_str=""
if [ "$lines" = "on" ]; then
  lines_added=$(echo "$input" | jq -r '.cost.total_lines_added // 0')
  lines_removed=$(echo "$input" | jq -r '.cost.total_lines_removed // 0')
  lines_str="+${lines_added}/-${lines_removed}"
fi

# Time of day
time_str=""
if [ "$time" = "on" ]; then
  time_str=$(date +%H:%M)
fi

# Build output by accumulating segments
time_prefix=""
[ "$time" = "on" ] && [ -n "$time_str" ] && time_prefix="${time_str} "
out="${time_prefix}${dirname}"

# Branch appends directly to dirname (no separator)
[ "$branch" = "on" ] && out="${out}${branch_str}"

# Helper: append " | segment" only when segment is non-empty
add_seg() {
  [ -n "$1" ] && out="${out} | $1"
}

# ctx block (bar + pct + cache + warning) + model label
[ "$ctx_bar" = "on" ] && add_seg "${model_label_str}${ctx_block}"

# Rate limits
[ "$rate_limits" = "on" ] && [ -n "$rate_limits_str" ] && add_seg "$rate_limits_str"

# Duration section: compose from enabled sub-parts
dur_parts=""
[ "$sess_duration" = "on" ] && [ -n "$sess_duration_str" ] && dur_parts="~${sess_duration_str}"
[ "$wall_time" = "on" ] && dur_parts="${dur_parts:+$dur_parts }${duration_str}"
api_part=""
[ "$api_duration" = "on" ] && api_part="$api_duration_str"
[ "$think_pct" = "on" ] && [ -n "$api_part" ] && api_part="$api_part ${think_pct_val}%"
[ -n "$api_part" ] && dur_parts="${dur_parts:+$dur_parts }($api_part)"
[ -n "$dur_parts" ] && add_seg "$dur_parts"

# Lines
[ "$lines" = "on" ] && add_seg "$lines_str"

# Cost
[ "$cost" = "on" ] && add_seg "$cost_str"

printf "%s" "$out"
