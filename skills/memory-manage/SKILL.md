---
name: memory-manage
description: Use this skill when you want to review and manage Claude Code auto memory entries for the current project. Lists all entries, lets you select one, then offers edit, remove, archive, or keep for each item. Invoke when the user wants to clean up, update, or prune their memory.
disable-model-invocation: true
allowed-tools: Bash(pwd:*) Bash(rm:*) Read Edit Write
---

Manage Claude Code auto memory entries for the current project — list, select, and edit, remove, archive, or keep each item.

## Steps

1. Run `pwd` to get the current working directory as an absolute path.

2. Derive the project directory name: replace every `/` and `.` character in the path with `-`.
   Example: `/home/user/.claude` → `-home-user--claude`

3. Locate the memory directory: `~/.claude/projects/<derived-name>/memory/`

4. Read `MEMORY.md` from that directory. If it does not exist, report:
   > No memory found for this project at `<full-path>`.
   Then stop.

5. For each entry listed in `MEMORY.md`, read the linked `.md` file from the same directory to extract its frontmatter (`name`, `type`, `description`).

6. Present a concise numbered index:

```
[1] <name> (type: <type>)
    <description>

[2] ...
```

7. Scan the memory directory for `.md` files (excluding `MEMORY.md`) that are **not referenced** in `MEMORY.md`. These are archived memories. If any exist, append a note below the index:

```
─────────────────────────────────────────
N archived memory file(s) found in this project.
Use /memory-archive to manage them.
```

8. After the list (and optional archive notice), ask:

```
Enter a number to manage an entry, or (x) to exit memory-manage.
```

9. If the user enters a valid index number, show the full body of that memory entry (verbatim, including **Why:** and **How to apply:** if present), then ask:

```
How do you want to proceed?
(a) Edit
(b) Remove
(c) Archive — remove from index, keep file on disk
(d) Keep — go back to list
(e) Exit
```

10. **If (a) Edit:**
    - Show the current raw file content.
    - Ask: "What would you like to change?"
    - Wait for the user's description of the change.
    - Apply the edit using the Edit tool.
    - Confirm: "Entry updated." then go back to step 6.

11. **If (b) Remove:**
    - Show a confirmation gate:
      ```
      About to remove `<name>` from the memory index. How do you want to proceed?
      (a) Proceed
      (b) Cancel
      ```
    - On Cancel: go back to step 9 (re-show the entry action menu).
    - On Proceed:
      1. Remove the corresponding line from `MEMORY.md` using Edit — find and delete the line that links to `<filename>`.
      2. Check whether `MEMORY.md` still references `<filename>`. If no reference remains, delete the file with `rm <full-path>`.
      3. Confirm: "Entry removed." If `MEMORY.md` has no remaining entries, report "Memory index is empty — nothing left to manage." and stop. Otherwise go back to step 6.

12. **If (c) Archive:**
    - Remove the corresponding line from `MEMORY.md` using Edit — find and delete the line that links to `<filename>`. Do not touch the `.md` file.
    - Confirm: "Entry archived — removed from index, file kept at `<full-path>`." If `MEMORY.md` has no remaining entries, report "Memory index is empty — nothing left to manage." and stop. Otherwise go back to step 6.

13. **If (d) Keep:** go back to step 6.

14. **If (e) Exit:** stop.

## Input validation

- If the user enters an invalid number or out-of-range value at step 8: reply "Invalid selection — enter a number between 1 and N, or (x) to exit." and repeat the prompt.
- If the user enters anything other than a/b/c/d/e at step 9: repeat the step 9 prompt.
- If the user enters anything other than a/b at the confirmation gate: repeat the confirmation gate.

## Failure paths

- **Memory directory missing or MEMORY.md not found:** report the path that was checked and stop. Do not create files.
- **Individual memory file missing:** print `[file not found: <filename>]` inline in the index and skip that entry for edit/remove actions.
- **MEMORY.md becomes empty after an action (or was already empty):** report "Memory index is empty — nothing left to manage." and stop.
- **Edit tool fails on MEMORY.md:** report the error, do not delete any file, and return to step 6.
- **Edit tool fails on entry file:** report the error and return to step 6.
- **Edit tool fails on MEMORY.md during archive:** report the error, the `.md` file was not touched, and return to step 6.
- **rm fails:** report the error — the MEMORY.md line was already removed, so note: "Entry removed from index but the file could not be deleted — please remove `<filename>` manually."
