---
name: git-log
description: Use this skill to view recent git history or search commit messages. Invoke when the user asks to see the git log, recent commits, or wants to find a commit by keyword.
disable-model-invocation: false
argument-hint: "[search term]"
allowed-tools: Bash(bash ~/.claude/skills/git-log/scripts/:*)
---

## Available scripts

- **`~/.claude/skills/git-log/scripts/git-log.sh`** — Fetches git history. Handles both the no-arg summary and the batched search loop.

---

## No arguments

Run:
```bash
bash ~/.claude/skills/git-log/scripts/git-log.sh
```

Display the output to the user. Done.

---

## With arguments — search loop

Set `offset = 0`. Repeat:

**Step 1 — Run the script:**
```bash
bash ~/.claude/skills/git-log/scripts/git-log.sh --search $ARGUMENTS --offset <offset>
```

**Step 2 — Read the final `status=` line:**

- `status=no_more_commits` → tell the user "No more commits to search." Stop.
- `status=done match_count=N batch_count=M offset=O` → continue to Step 3.

**Step 3 — Display matches:**

Each matching commit is preceded by `=== MATCH: <hash> ===`. Display the full block for each match. **Bold every occurrence** of `$ARGUMENTS` (case-insensitive) in the subject and body — wrap with `**...**`, preserving original casing.

**Step 4 — Ask the user:**

If `match_count > 0`:
```
Found <match_count> match(es) in commits <offset+1>–<offset+batch_count>. What next?
(a) Continue searching
(b) Stop
```

If `match_count == 0`:
```
No matches in commits <offset+1>–<offset+batch_count>. What next?
(a) Search next 100 commits
(b) Stop
```

- On (a): `offset += batch_count`, repeat from Step 1.
- On (b): stop.
