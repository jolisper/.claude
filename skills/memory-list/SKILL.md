---
name: memory-list
description: Use this skill when you want to list all Claude Code auto memory entries for the current project. Shows a concise index; the user can request full detail for a specific entry by number.
disable-model-invocation: true
allowed-tools: Bash(pwd:*) Read Glob
---

List all Claude Code auto memory entries for the current project.

## Steps

1. Run `pwd` to get the current working directory as an absolute path.

2. Derive the project directory name: replace every `/` and `.` character in the path with `-`.
   Example: `/home/user/.claude` → `-home-user--claude`

3. Locate the memory directory: `~/.claude/projects/<derived-name>/memory/`

4. Read `MEMORY.md` from that directory. If it does not exist, report:
   > No memory found for this project at `<full-path>`.
   Then stop.

4a. **Inline content detection.** Scan `MEMORY.md` for inline sections:
   - Split the content into sections by `## ` headings.
   - A section is **inline** if its body contains no link line matching `- [...](...)` (a markdown link-list entry).
   - Ignore the top-level `# Memory` heading and blank lines when classifying.
   - If **no** inline sections are found, proceed silently to step 5 — do not output anything.
   - If one or more inline sections are found, display this **before** the index:
     ```
     ⚠ MEMORY.md contains N inline section(s) not linked to files:
       - "## <heading>"
       - ...
     These entries are invisible to memory skills. Use /memory-manage to migrate them.
     ```
   - Continue to step 5 — process only linked entries as normal.

5. For each entry listed in `MEMORY.md`, read the linked `.md` file from the same directory to extract its frontmatter (`name`, `type`, `description`).

6. Present a concise index in this format:

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
Enter a number for full details, or (x) to exit memory-list.
```

9. If the user enters a valid index number, print the full body of that memory entry (verbatim, including **Why:** and **How to apply:** if present), then ask:

```
(l) Show list again, or (x) to exit memory-list.
```

   - If the user enters `l`, go back to step 6.
   - If the user enters `x`, stop.
   - If the user enters anything else, repeat this prompt.

10. If the user enters an invalid number or an out-of-range value at step 8, reply "Invalid selection — enter a number between 1 and N, or (x) to exit." and repeat the prompt.

11. If the user enters `x` at step 8, stop.

## Failure paths

- **Memory directory missing or MEMORY.md not found:** report the path that was checked and stop. Do not create files.
- **Individual memory file missing:** print `[file not found: <filename>]` inline and continue with remaining entries.
- **MEMORY.md is empty or has no entries:** report "Memory index is empty for this project."
