---
name: obsidian-search
description: >
  Use this skill to search the Obsidian vault by tag and/or keyword and surface
  relevant notes. Invoke when the user runs /obsidian-search, or when Claude needs
  to retrieve vault context autonomously before starting a task.
argument-hint: "[#tag ...] [keyword ...]"
disable-model-invocation: false
allowed-tools: Read Glob Grep Bash(bash:*)
when_to_use: >
  Invoke when the user runs /obsidian-search, or when Claude needs to check the
  vault for prior context on a topic. Accepts #tag filters, keyword terms, or both.
---

Search the Obsidian vault by tag, keyword, or both. Returns up to 5 ranked results.
When invoked by the user, an interactive viewer allows browsing full notes.
When invoked autonomously by Claude, present results and stop — skip the viewer.

## Step 1 — Resolve vault path

Check in order, stopping at the first match. Set VAULT to the resolved path.

1. Run `bash -c 'printf "%s" "$OBSIDIAN_VAULT"'` — if non-empty, VAULT = that value.
2. Read `.claude/obsidian-vault.json` in the current directory. If present and
   has a `vault` field, VAULT = that value.
3. Read `~/.claude/obsidian-vault.json`. If present and has a `vault` field,
   VAULT = that value.
4. If VAULT is still unset, print and stop:
   ```
   Obsidian vault not configured. Set it up with one of:

     export OBSIDIAN_VAULT="/path/to/your/vault"

   Or run /obsidian-vault to configure interactively.

   Then re-invoke this skill.
   ```

## Step 2 — Parse arguments

If `$ARGUMENTS` is empty, ask: `What are you searching for?` and use the answer.

Extract all tokens matching `#[a-zA-Z][a-zA-Z0-9_-]*` from `$ARGUMENTS`.
Normalize each to lowercase (strip `#`). Store as **TAGS**.
The remainder is the **KEYWORD** string.

## Step 3 — Build candidate set

**If TAGS is non-empty:**
For each tag, use Grep to search `{VAULT}` for the pattern `@tags/@{tag}.md`.
Union the matching files across all tags — include a note if it matches any tag.

**If TAGS is empty:**
Glob `{VAULT}/notes/*.md` to get all content notes.

In both cases, exclude any files under `{VAULT}/@tags/`.

## Step 4 — Apply keyword filter

If KEYWORD is non-empty: keep only candidates whose filename or body contains
at least one KEYWORD term. Use Grep to check each candidate.

If KEYWORD is empty: skip this step.

## Step 5 — Rank and select top 5

Score each candidate:
- KEYWORD appears in the filename → **title match** (higher rank)
- KEYWORD appears only in the body → **body match** (lower rank)
- No KEYWORD → all equal

Sort title matches before body matches. Within each tier, read the `id:`
frontmatter field and sort newest first. Take the top 5.

## Step 6 — Extract display fields

For each result, read the note and extract:
- **id:** from the `id:` frontmatter field
- **Tags:** the tag-link line (first non-empty line after the `# Heading`)
- **Snippet:** if KEYWORD non-empty, ~10 words of context around the first
  keyword match; otherwise use the summary line (first non-empty line after
  the tag-link line)

## Step 7 — Present results

```
[1] {filename}  (id: {id})
    Tags: {tag-link line}
    "{snippet}"

[2] ...
```

If no candidates remain after Steps 3–4: report
`No notes found for "{query}".`
and suggest `/obsidian-capture #{topic} ... to create a first note on that topic.`
Then stop.

## Step 8 — Interactive viewer (user invocations only)

Ask: `Enter a number to view, or (x) to exit.`

On a valid number: Read and print the full note content. Then ask:
```
(b) Back to results
(x) Exit
```
On (b): re-display results from Step 7 and repeat Step 8.
On (x): stop.

On (x) at the initial prompt: stop.
