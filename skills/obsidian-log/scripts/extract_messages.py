#!/usr/bin/env python3
"""Extract last user and assistant messages from a Claude Code transcript."""
import json
import sys
import re


def flatten(t):
    t = re.sub(r'^#{1,6} +(.*)', r'**\1**', t, flags=re.MULTILINE)
    t = re.sub(r'(?<!`)<([a-zA-Z][a-zA-Z0-9_-]*)>(?!`)', r'`<\1>`', t)
    t = re.sub(r'^( {0,3})```', r'\1~~~', t, flags=re.MULTILINE)
    return t


def extract(path, role):
    try:
        lines = open(path).readlines()
        for line in reversed(lines):
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
                if d.get('type') == role:
                    content = d.get('message', {}).get('content', '')
                    if role == 'user':
                        if isinstance(content, str) and content.strip():
                            print(flatten(content.strip()))
                            return
                    elif role == 'assistant':
                        if isinstance(content, list):
                            parts = [b.get('text', '') for b in content if b.get('type') == 'text']
                            text = ''.join(parts).strip()
                            if text:
                                print(flatten(text))
                                return
                        elif isinstance(content, str) and content.strip():
                            print(flatten(content.strip()))
                            return
            except Exception:
                continue
    except Exception:
        pass


if __name__ == '__main__':
    if len(sys.argv) < 3:
        sys.exit(1)
    extract(sys.argv[1], sys.argv[2])
