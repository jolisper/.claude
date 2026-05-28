#!/usr/bin/env bash

PAYLOAD=$(cat)
DATE=$(date '+%Y-%m-%d')
TIMESTAMP=$(date '+%H:%M')

# Resolve vault path from global config
VAULT=$(python3 -c "
import json, os
try:
    d = json.load(open(os.path.expanduser('~/.claude/obsidian-vault.json')))
    print(d.get('vault', ''))
except Exception:
    pass
" 2>/dev/null) || exit 0

[ -z "$VAULT" ] && exit 0

NOTE="$VAULT/Log $DATE.md"

# Extract transcript path, session id from payload
TRANSCRIPT_PATH=$(printf '%s' "$PAYLOAD" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('transcript_path',''))" 2>/dev/null)
SESSION_ID=$(printf '%s' "$PAYLOAD" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('session_id','')[:8])" 2>/dev/null)

# Capture working directory context
CWD_NAME=$(basename "$(pwd)")
GIT_BRANCH=$(git branch --show-current 2>/dev/null)

# Extract ai-title from transcript
AI_TITLE=""
if [ -n "$TRANSCRIPT_PATH" ] && [ -f "$TRANSCRIPT_PATH" ]; then
    AI_TITLE=$(python3 -c "
import json, sys
path = sys.argv[1]
try:
    lines = open(path).readlines()
    for line in reversed(lines):
        line = line.strip()
        if not line:
            continue
        try:
            d = json.loads(line)
            if d.get('type') == 'ai-title':
                print(d.get('title', ''))
                break
        except Exception:
            continue
except Exception:
    pass
" "$TRANSCRIPT_PATH" 2>/dev/null)
fi

# Extract last user typed message: last type=user entry where content is a string (not array/tool result)
USER_MESSAGE=""
if [ -n "$TRANSCRIPT_PATH" ] && [ -f "$TRANSCRIPT_PATH" ]; then
    USER_MESSAGE=$(python3 -c "
import json, sys, re
def flatten(t):
    return re.sub(r'^#{1,6} +(.*)', r'**\1**', t, flags=re.MULTILINE)
path = sys.argv[1]
try:
    lines = open(path).readlines()
    for line in reversed(lines):
        line = line.strip()
        if not line:
            continue
        try:
            d = json.loads(line)
            if d.get('type') == 'user':
                content = d.get('message', {}).get('content', '')
                if isinstance(content, str) and content.strip():
                    print(flatten(content.strip()))
                    break
        except Exception:
            continue
except Exception:
    pass
" "$TRANSCRIPT_PATH" 2>/dev/null)
fi

# Extract last assistant message from transcript (full text, no truncation)
LAST_ASSISTANT=""
if [ -n "$TRANSCRIPT_PATH" ] && [ -f "$TRANSCRIPT_PATH" ]; then
    LAST_ASSISTANT=$(python3 -c "
import json, sys, re
def flatten(t):
    return re.sub(r'^#{1,6} +(.*)', r'**\1**', t, flags=re.MULTILINE)
path = sys.argv[1]
try:
    lines = open(path).readlines()
    for line in reversed(lines):
        line = line.strip()
        if not line:
            continue
        try:
            d = json.loads(line)
            if d.get('type') == 'assistant':
                content = d.get('message', {}).get('content', '')
                if isinstance(content, list):
                    parts = [b.get('text','') for b in content if b.get('type') == 'text']
                    text = ''.join(parts).strip()
                    if text:
                        print(flatten(text))
                        break
                elif isinstance(content, str) and content.strip():
                    print(flatten(content.strip()))
                    break
        except Exception:
            continue
except Exception:
    pass
" "$TRANSCRIPT_PATH" 2>/dev/null)
fi

# Skip turns with no user message (sub-agent completions, etc.)
[ -z "$USER_MESSAGE" ] && exit 0

# Create note if it doesn't exist
if [ ! -f "$NOTE" ]; then
    NOTE_ID=$(date '+%Y%m%d%H%M')
    printf -- '---\nid: %s\ncreated: %s\nupdated: %s\ntype: log\n---\n\n# Log %s\n\n[@log](@tags/@log.md)\n' \
        "$NOTE_ID" "$DATE" "$DATE" "$DATE" > "$NOTE"
fi

# Ensure @log tag stub exists (managed by obsidian-log)
if [ ! -f "$VAULT/@tags/@log.md" ]; then
    printf -- '---\nmanaged-by: obsidian-log\n---\n\n# @log\n' > "$VAULT/@tags/@log.md"
fi

# Append the log entry
{
    if [ -n "$AI_TITLE" ]; then
        printf '\n## %s — `%s` — %s\n\n' "$TIMESTAMP" "$SESSION_ID" "$AI_TITLE"
    else
        printf '\n## %s — `%s`\n\n' "$TIMESTAMP" "$SESSION_ID"
    fi
    if [ -n "$GIT_BRANCH" ]; then
        printf '**Cwd:** `%s` · **Branch:** `%s`\n\n' "$CWD_NAME" "$GIT_BRANCH"
    else
        printf '**Cwd:** `%s`\n\n' "$CWD_NAME"
    fi
    printf '**User:**\n%s\n\n' "$USER_MESSAGE"
    printf '**Assistant:**\n%s\n' "$LAST_ASSISTANT"
} >> "$NOTE"

# Update frontmatter updated date
python3 -c "
import re, sys
path, date = sys.argv[1], sys.argv[2]
try:
    content = open(path).read()
    content = re.sub(r'^updated: .*\$', f'updated: {date}', content, flags=re.MULTILINE)
    open(path, 'w').write(content)
except Exception:
    pass
" "$NOTE" "$DATE"
