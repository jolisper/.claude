---
name: obsidian-journal
description: >
  Use this skill to write an end-of-day journal entry. Invoke when the user
  runs /obsidian-journal to save a verbatim day note and generate a structured
  debrief (events, decisions, reflections, next steps) synthesized from the
  literal input and today's vault notes.
argument-hint: "[#tag ...] [day note]"
disable-model-invocation: true
allowed-tools: Read Glob Grep Bash(date:*) Bash(bash:*) Bash(mkdir:*) Write
when_to_use: >
  Invoke when the user explicitly runs /obsidian-journal. Typically at the end
  of a work day. Creates one note per day — if today's journal already exists,
  points the user to it and stops.
---

Write an end-of-day journal entry. `$ARGUMENTS` is a mix of optional `#tag`
tokens and the day's literal note. Tags can appear anywhere in the string.

## Step 1 — Resolve vault path and language

Check in order, stopping at the first match. Set VAULT to the resolved path.
Also read the `language` field from the matched config file; set **LANG** to that
value. If the field is absent or VAULT came from the env var, default LANG to `en`.

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

Extract all tokens matching `#[a-zA-Z][a-zA-Z0-9_-]*` from `$ARGUMENTS`.
Normalize each to lowercase (strip `#`). Store as **TAGS**.
The remainder after removing all tag tokens is **DAY_NOTE**.

If DAY_NOTE is empty after stripping:
  Ask: `What do you want to record for today?`
  Use the answer verbatim as DAY_NOTE — do not parse tags from it.
  If DAY_NOTE is still empty: report "A day note is required." and stop.

## Step 3 — Generate timestamps

Run `date +%Y%m%d%H%M` → **ID**

Run `date +%Y-%m-%d` → **DATE**

## Step 4 — One-per-day check

Run `bash -c "test -f '{VAULT}/Journal {DATE}.md'"`.

If the file exists: read its frontmatter to extract the `id:` value. Report:
```
Ya existe un journal para hoy: Journal {DATE}.md  (id: {id})
Usá /obsidian-update {id} para agregarle contenido.
```
and stop.

## Step 5 — Ensure @tags/ exists

Run `bash -c "test -d '{VAULT}/@tags'"`. If non-zero:
Run `mkdir -p {VAULT}/@tags`. On failure: report the error and stop.

Ensure the `@journal` stub exists (managed by this skill):
Run `bash -c "test -f '{VAULT}/@tags/@journal.md'"`. If non-zero:
Write to `{VAULT}/@tags/@journal.md`:
```markdown
---
managed-by: obsidian-journal
---

# @journal
```

Add `journal` to TAGS if not already present — `@journal` is the managed tag for
journal notes and must always appear on them.

## Step 6 — Ensure tag stubs exist

For each tag in TAGS:

Run `bash -c "test -f '{VAULT}/@tags/@{tag}.md'"`. If non-zero:
Write to `{VAULT}/@tags/@{tag}.md`:
```markdown
# @{tag}
```
No confirmation needed.

## Step 7 — Search today's notes

Use Grep to search `{VAULT}` for `^created: {DATE}` in all `.md` files.
Exclude files under `{VAULT}/@tags/` and `{VAULT}/Journal {DATE}.md`.

Store the matching files as **TODAY_NOTES**. For each, read the file and
extract: filename, `id:`, the tag-link line, and the first non-empty line
after the tag-link line (the summary).

If TODAY_NOTES is non-empty, use these notes as additional source material
when composing the synthesis sections (Steps 9 and 10).

## Step 7b — Read today's session log

Check whether `{VAULT}/Log {DATE}.md` exists.

If it exists: Read the file. Extract all session entries — each entry starts with a
`## HH:MM` heading and includes the **User:** and **Assistant:** lines that follow it.
Store the list of entries as **LOG_ENTRIES**. Each entry should capture: the time,
the session title (ai-title after the `—` if present), the user message, and the
assistant response snippet.

If the file does not exist or is empty: set LOG_ENTRIES to empty and continue.

## Step 8 — Suggest additional tags

Glob `{VAULT}/@tags/@*.md` to get all existing tags. For each stub, read it
and check for a `managed-by:` frontmatter field. Strip `@` prefix and `.md`
suffix from stubs that do **not** contain `managed-by:`. Store as **USER_TAGS**.

Using DAY_NOTE and TODAY_NOTES context, identify relevant tags from USER_TAGS
not already in TAGS.

If suggestions exist, print (numbering each tag from 1):
```
Suggested tags: 1) #tag1  2) #tag2 — add?
(a) Add all
(b) Pick — reply with numbers: 1 2 ...
(c) Skip
```
Wait for the user's reply.
On (a): add all suggestions to TAGS.
On (b): parse the reply for space-separated numbers (1-based). Add the
  corresponding tags to TAGS.
On (c): continue.
For each newly added tag not yet on disk, write its stub as in Step 6.

## Step 9 — ID collision check

Use Grep to search `{VAULT}` for the line `^id: {ID}` in frontmatter.
If any file matches: append the next available letter suffix (`a`, `b`, ...)
and repeat until no match is found. Use the first available value as ID.

## Step 10 — Compose note

Write all synthesized prose and section headers in **LANG**.
DAY_NOTE must be preserved verbatim — never translated, rephrased, or altered.

Synthesize a **SUMMARY**: 2–3 sentences distilling the day from DAY_NOTE,
TODAY_NOTES, and LOG_ENTRIES. Write in LANG.

Synthesize the structured sections from DAY_NOTE, TODAY_NOTES, and LOG_ENTRIES.
LOG_ENTRIES are especially useful for the Events and Decisions sections — each
entry shows what was worked on in that session and what Claude helped with.
- **Eventos / Events** — what happened, key activities (bullet list); draw from
  LOG_ENTRIES session titles and user messages to name specific sessions and topics
- **Decisiones / Decisions** — decisions made and their rationale (bullet list)
- **Reflexiones / Reflections** — what worked, what didn't, lessons (bullet list)
- **Próximos pasos / Next steps** — open items, tomorrow's priorities (bullet list)

Where a bullet references one of TODAY_NOTES, link it:
`[note title](note filename.md)`

If a section has nothing to report, omit it entirely — do not write an empty
section.

When writing the tag-link line, place managed tags (stubs that contain `managed-by:`)
before user tags. `@journal` is always first.

Note structure:
```markdown
---
id: {ID}
created: {DATE}
updated: {DATE}
type: journal
---

# Journal {DATE}

[@journal](@tags/@journal.md) [@tag2](@tags/@tag2.md)

{SUMMARY}

## {section header in LANG: "Nota del día" / "Day note" / etc.}

{DAY_NOTE — verbatim}

## {Events section header in LANG}

- ...

## {Decisions section header in LANG}

- ...

## {Reflections section header in LANG}

- ...

## {Next steps section header in LANG}

- ...
```

Omit the tag-link line entirely if TAGS is empty.

## Step 11 — Write and confirm

Write the composed note to `{VAULT}/Journal {DATE}.md`.

Confirm:
```
Captured → Journal {DATE}.md  (id: {ID})
```

## Failure contract

- **Vault not configured:** show the setup message from Step 1 and stop.
- **Write fails:** print the full composed note content to the conversation
  so the user can paste it manually. Never silently discard content.
- **mkdir fails:** report the error and stop.
