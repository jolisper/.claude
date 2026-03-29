---
name: memory-archive
description: Use this skill when you want to review unindexed (archived) Claude Code auto memory files for the current project. Lists memory files that exist on disk but are not referenced in MEMORY.md, lets you select one, then offers restore, remove, or keep for each item. Invoke when you want to clean up orphaned memory files or recover an archived entry.
disable-model-invocation: true
allowed-tools: Bash(pwd:*) Bash(rm:*) Read Edit Glob
---

Manage unindexed (archived) Claude Code memory files for the current project — list, select, and restore, remove, or keep each item.

## Steps

1. Run `pwd` to get the current working directory as an absolute path.

2. Derive the project directory name: replace every `/` and `.` character in the path with `-`.
   Example: `/home/user/.claude` → `-home-user--claude`

3. Locate the memory directory: `~/.claude/projects/<derived-name>/memory/`

4. Read `MEMORY.md` from that directory. If it does not exist, report:
   > No memory found for this project at `<full-path>`.
   Then stop.

5. Glob all `.md` files in the memory directory (excluding `MEMORY.md` itself). Cross-reference against `MEMORY.md` to find files that are **not referenced** in the index. These are the archived memories.

6. If no archived files are found, report:
   > No archived memory files found for this project.
   Then stop.

7. For each archived file, read it to extract its frontmatter (`name`, `type`, `description`). Present a numbered index:

```
[1] <name> (type: <type>)
    <description>

[2] ...
```

8. After the list, ask:

```
Enter a number to manage an entry, or (x) to exit memory-archive.
```

9. If the user enters a valid index number, show the full body of that memory entry (verbatim, including **Why:** and **How to apply:** if present), then ask:

```
How do you want to proceed?
(a) Restore — add back to MEMORY.md index
(b) Remove — delete the file permanently
(c) Keep — leave as archive, go back to list
(d) Exit
```

10. **If (a) Restore:**
    - Append a new line to `MEMORY.md` using Edit, in the format:
      `- [<name>](<filename>) — <description>`
    - Confirm: "Entry restored to index." then go back to step 7.

11. **If (b) Remove:**
    - Show a confirmation gate:
      ```
      About to permanently delete `<filename>`. This cannot be undone. How do you want to proceed?
      (a) Proceed
      (b) Cancel
      ```
    - On Cancel: go back to step 9 (re-show the entry action menu).
    - On Proceed:
      1. Delete the file with `rm <full-path>`.
      2. Confirm: "File deleted." If no archived files remain, report "No more archived files." and stop. Otherwise go back to step 7.

12. **If (c) Keep:** go back to step 7.

13. **If (d) Exit:** stop.

## Input validation

- If the user enters an invalid number or out-of-range value at step 8: reply "Invalid selection — enter a number between 1 and N, or (x) to exit." and repeat the prompt.
- If the user enters anything other than a/b/c/d at step 9: repeat the step 9 prompt.
- If the user enters anything other than a/b at the confirmation gate: repeat the confirmation gate.
- If the user enters `x` at step 8: stop.

## Failure paths

- **Memory directory missing or MEMORY.md not found:** report the path that was checked and stop. Do not create files.
- **Individual archived file unreadable:** print `[file not found: <filename>]` inline in the index and skip it for all actions.
- **Edit tool fails on MEMORY.md during restore:** report the error, the `.md` file was not touched, and return to step 7.
- **rm fails:** report the error and note: "The file could not be deleted — please remove `<filename>` manually." Return to step 7.

## Abort conditions

- Do not run if the memory directory does not exist — report the missing path and stop without creating anything.
