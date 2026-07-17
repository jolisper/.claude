---
name: obsidian-journal
description: >
  Use this skill to write an end-of-day journal entry. Invoke when the user
  runs /obsidian-journal to generate a structured debrief (events, decisions,
  reflections, next steps) synthesized from the session log, vault notes, and
  an optional focus hint. Accepts an optional date (default: today) and tags.
argument-hint: "[YYYY-MM-DD] [hint]"
disable-model-invocation: true
allowed-tools: Read Glob Grep Bash(date:*) Bash(bash:*) Bash(mkdir:*) Write
when_to_use: >
  Invoke when the user explicitly runs /obsidian-journal. Typically at the end
  of a work day. Creates one note per day — if a journal for the target date
  already exists, offers to append an update section.
---

Write an end-of-day journal entry synthesized from the session log for the target
date. `$ARGUMENTS` accepts an optional date (YYYY-MM-DD, default: today), optional
`#tag` tokens, and an optional hint to focus the synthesis.

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

`$ARGUMENTS` may contain two optional components in any order:

1. **Date token** — a string matching `YYYY-MM-DD` (e.g. `2026-05-27`). Extract it as
   **TARGET_DATE**. If absent, TARGET_DATE is empty.
2. **Hint** — the remainder after removing the date token. Trim whitespace. Store as **HINT**.

`HINT` is a focus directive for journal synthesis — it is **not** stored verbatim in the
note. If HINT is empty the journal is generated purely from the session log.

## Step 3 — Generate timestamps

Run `date +%Y%m%d%H%M` → **ID**

If TARGET_DATE is non-empty, use it as **DATE**.
Otherwise run `date +%Y-%m-%d` → **DATE**.

## Step 4 — One-per-day check

Run `bash -c "test -f '{VAULT}/logbook/Journal {DATE}.md'"`.

If the file does not exist: continue to Step 5.

If the file exists: read its frontmatter to extract the `id:` value. Inform in LANG and ask:
- Spanish: `Ya existe un journal para {DATE}: Journal {DATE}.md (id: {id}). ¿Querés agregar una actualización?`
- English: `A journal for {DATE} already exists: Journal {DATE}.md (id: {id}). Add an update?`

```
(a) Yes
(b) Cancel
```

On (b): stop.

On (a) — **update flow** (skip Steps 5–11 entirely after this):

  If HINT is empty, ask: `What should the update focus on?` and use the reply as HINT.

  Run `date +%H:%M` → **UPDATE_TIME**.
  Run `date +%Y-%m-%d` → **TODAY**.

  Execute Steps 6 and 7 now to load TODAY_NOTES and LOG_ENTRIES, then continue.

  Synthesize an update using HINT, LOG_ENTRIES, and TODAY_NOTES following the same
  composition rules as Step 9. Produce only the synthesis sections that have
  content to report — omit empty ones.

  Compose the update block in LANG:
  ```markdown
  ## Update — {DATE} {UPDATE_TIME}

  {synthesis sections — same structure as the main note: Events, Decisions, Reflections, Next steps}
  ```

  Read the full content of `{VAULT}/logbook/Journal {DATE}.md` into **EXISTING_CONTENT**.
  Replace the `updated: {old_date}` line in the frontmatter with `updated: {TODAY}`.
  Append the update block after the last line of EXISTING_CONTENT.
  Write the result back to `{VAULT}/logbook/Journal {DATE}.md`.

  Compute:
  - **VAULT_NAME** = the last path segment of VAULT.
  - **URI_PATH** = `logbook/Journal {DATE}` with the `.md` extension stripped.
  - Percent-encode both (spaces → `%20`, `/` → `%2F`) for the URI below.

  Confirm:
  ```
  Updated → Journal {DATE}.md  (id: {id})
  obsidian://open?vault={VAULT_NAME}&file={URI_PATH}
  ```
  Stop.

## Step 5 — Ensure directories exist

Run `mkdir -p {VAULT}/logbook`. On failure: report the error and stop.

## Step 6 — Search today's notes

Use Grep to search `{VAULT}` for `^created: {DATE}` in all `.md` files.
Exclude files under `{VAULT}/@topics/` and `{VAULT}/logbook/Journal {DATE}.md`.

Store the matching files as **TODAY_NOTES**. For each, read the file and
extract: filename, `id:`, the tag-link line, and the first non-empty line
after the tag-link line (the summary).

If TODAY_NOTES is non-empty, use these notes as additional source material
when composing the synthesis sections (Steps 8 and 9).

## Step 7 — Read session log for DATE

Check whether `{VAULT}/logbook/Log {DATE}.md` exists.

If it exists: Read the file. Extract all session entries — each entry starts with a
`## HH:MM` heading and includes the **User:** and **Assistant:** lines that follow it.
Store the list of entries as **LOG_ENTRIES**. Each entry should capture: the time,
the session title (ai-title after the `—` if present), the user message, and the
assistant response snippet.

If the file does not exist or is empty:
  Print: `No session log found for {DATE}.`
  Ask:
  ```
  Continue anyway?
  (a) Yes — provide a hint
  (b) Cancel
  ```
  On (b): stop.
  On (a): if HINT is empty, ask `What should the journal focus on?` and use the
  reply as HINT. Set LOG_ENTRIES to empty.

## Step 8 — ID collision check

Use Grep to search `{VAULT}` for the line `^id: {ID}` in frontmatter.
If any file matches: append the next available letter suffix (`a`, `b`, ...)
and repeat until no match is found. Use the first available value as ID.

## Step 9 — Compose note

Write all synthesized prose and section headers in **LANG**.

If HINT is non-empty, open the composition with: "Focus the synthesis on: {HINT}."
Use HINT to guide which events, decisions, and reflections to emphasize — do not
write HINT verbatim into the note body.

Synthesize a **SUMMARY**: 2–3 sentences distilling the day from HINT (if set),
TODAY_NOTES, and LOG_ENTRIES. Write in LANG.

Synthesize the structured sections from HINT, TODAY_NOTES, and LOG_ENTRIES.
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

Note structure:
```markdown
---
id: {ID}
created: {DATE}
updated: {DATE}
type: journal
---

# Journal {DATE}

{SUMMARY}

## {Events section header in LANG}

- ...

## {Decisions section header in LANG}

- ...

## {Reflections section header in LANG}

- ...

## {Next steps section header in LANG}

- ...
```

## Step 10 — Write and confirm

Write the composed note to `{VAULT}/logbook/Journal {DATE}.md`.

Compute:
- **VAULT_NAME** = the last path segment of VAULT.
- **URI_PATH** = `logbook/Journal {DATE}` with the `.md` extension stripped.
- Percent-encode both (spaces → `%20`, `/` → `%2F`) for the URI below.

Confirm:
```
Captured → Journal {DATE}.md  (id: {ID})
obsidian://open?vault={VAULT_NAME}&file={URI_PATH}
```

## Failure contract

- **Vault not configured:** show the setup message from Step 1 and stop.
- **Write fails (new journal):** print the full composed note to the conversation
  so the user can paste it manually. Never silently discard content.
- **Write fails (update):** print the full update block to the conversation
  so the user can paste it manually. Never silently discard content.
- **mkdir fails:** report the error and stop.
