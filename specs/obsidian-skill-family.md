# Obsidian Skill Family — Design Spec

**Date:** 2026-05-11
**Status:** Draft v3
**Vault analyzed:** `~/Documents/Inviu` (old) + `~/Documents/Inviu Vault` (fresh)

---

## Executive Summary

A family of Claude Code skills for integrating an Obsidian vault into the development
workflow. The organizing principle is the **tag-notes pattern**: instead of folders and
frontmatter taxonomies, every note links to one or more `@topic` notes that act as
navigable indexes. The graph and backlinks panel do the filing — no manual organization
required.

Notes are identified by a **Zettelkasten timestamp** prefix (`YYYYMMDDHHmm`) embedded
in the filename. This gives every note a stable, unique ID independent of its title.

The family has **3 core skills**:

| Tier | Skill | Purpose |
|------|-------|---------|
| Write | `obsidian-capture` | Instant note with `@tags`, no questions asked |
| Write | `obsidian-update` | Add content to an existing note by ID or fuzzy name |
| Read | `obsidian-search` | Search and surface relevant vault notes |

---

## Research Findings

### How Obsidian Works on Disk

Obsidian vaults are **plain directories of Markdown files**. No database, no
proprietary format. Every note is a `.md` file. The entire skill family operates via
direct file I/O — no plugin or running Obsidian instance required.

The fresh vault (`~/Documents/Inviu Vault`) has:
- `app.json: {}` — pure defaults; **wikilinks are the default link format**
- No community plugins installed
- Core plugins enabled: `graph`, `backlink`, `outgoing-link`, `tag-pane`, `properties`,
  `daily-notes`, `templates`, `bases`, `sync`

### Wikilinks

Internal links: `[[Note Name]]`, `[[Note Name|alias]]`, `[[Note Name#Heading]]`.
Obsidian resolves these across the vault by filename, regardless of directory.
Skills emit wikilinks — not markdown links — because wikilinks appear in the graph
and backlinks panel.

### Tag-Notes Pattern

A tag-note is a regular `.md` file whose name starts with `@`. Content notes link
to it with `[[@topic]]`. The backlinks panel on `@topic.md` becomes a live,
auto-maintained index of every note on that topic — no queries, no plugins, no
maintenance.

Advantages over `#tags`:
- Clickable from the graph
- Backlinks panel shows full context, not just a list
- The tag itself can have content (a description, related links)
- Works with the `bases` core plugin for filtered views

### Obsidian Bases (core plugin, enabled)

Bases is Obsidian's built-in database view. It renders notes as a table and filters
by frontmatter fields. A single `date:` field in every note's frontmatter is enough
to make a Bases view that sorts all notes chronologically — no Dataview needed.

### Zettelkasten Prefixer (core plugin, enabled)

Obsidian's built-in Zettelkasten Prefixer uses `YYYYMMDDHHmm` (minute precision,
12 digits) as the standard timestamp format. The skill family adopts this same
convention for consistency.

---

## Design Philosophy

### 1. Tag-notes as the only organization primitive

No folder hierarchy beyond `@ (Tags)/`. Organization emerges from wikilinks to
`@topic` notes. Every note belongs where its links point.

### 2. File I/O only

Skills write directly to vault files. Works whether Obsidian is open or closed.
No plugins required.

### 3. Capture is sacred — never block it

`obsidian-capture` never asks questions and never fails silently. A blocked
capture is a lost thought. If a referenced `@tag` doesn't exist yet, the skill
creates the stub automatically.

### 4. Tags on demand

When a skill encounters an `@topic` reference that has no corresponding
`@ (Tags)/@topic.md`, it creates the stub. Skills also suggest existing tags
the user might want to add, based on vault contents.

### 5. Every note has a stable ID

The Zettelkasten timestamp prefix (`YYYYMMDDHHmm`) is the note's immutable identity.
Titles can change; the ID never does. Skills use the ID as the primary reference
and fall back to fuzzy title search for human convenience.

### 6. The graph is the maintenance tool

Orphan notes — notes with no `[[@...]]` links — are visible in the graph without
any skill. No maintenance skill is needed until a real recurring problem emerges
from actual vault usage.

### 7. Integrate with existing skills

`obsidian-update` is the natural follow-up to `recap` and `tdd-session`.
`obsidian-search` can surface context before a session.
`obsidian-capture` can be triggered by Claude autonomously to save key findings.

---

## Note ID System

Every note created by `obsidian-capture` gets a **Zettelkasten timestamp** prefix:

```
202605111430 Rebates architecture decision.md
└─────────┘ └──────────────────────────────┘
    ID              human-readable title
```

**Format:** `YYYYMMDDHHmm` — year, month, day, hour, minute (12 digits, minute precision).
Generated with `date +%Y%m%d%H%M`.

**Collision handling:** if two notes are captured in the same minute, the second gets
a letter suffix: `202605111430`, `202605111430a`, `202605111430b`, etc. The skill
checks for existence before writing and appends the next available suffix.

**Wikilinks with ID:** `[[202605111430 Rebates architecture decision]]` — the ID
anchors the link; Obsidian's link-update feature keeps the title portion in sync.

**Using the ID in skills:**
- `/obsidian-update 202605111430` — exact match, no ambiguity
- `/obsidian-update rebates architecture` — fuzzy match on the title portion
- Multiple fuzzy matches → numbered list → user picks one

---

## Vault Schema

```
$OBSIDIAN_VAULT/
├── @ (Tags)/
│   └── @{topic}.md              ← tag-note hubs; one per topic, person, project
└── {YYYYMMDDHHmm} {title}.md   ← all content notes, flat at root
```

That's the entire structure. No `Inbox/`, `Projects/`, `Notes/`, or `Daily/` folders.
The `@ (Tags)/` folder is the only special directory — its `@` prefix keeps it at
the top of the file explorer.

### Tag-note format

```markdown
# @topic
```

Optionally, a one-line description below the heading. Nothing else is required.
The backlinks panel provides all the content.

### Content note format

```markdown
---
date: YYYY-MM-DD
---

# Title

[[@tag1]] [[@tag2]]

{body}
```

The tag-link line immediately follows the heading. It is the first thing a reader
sees and the primary connection to the graph.

---

## Frontmatter Schema

Every note created by the skill family uses exactly one frontmatter field:

```yaml
---
date: YYYY-MM-DD
---
```

Nothing else. No `title`, `type`, `status`, `source`, or `tags` fields.
The `date` field enables Bases views and chronological sorting. Everything
else is expressed through wikilinks and headings.

Tag-notes in `@ (Tags)/` have no frontmatter at all.

---

## Configuration Contract

All skills resolve the vault path using this priority chain:

1. `$OBSIDIAN_VAULT` environment variable (absolute path)
2. `.claude/obsidian-vault` file at the project root (one line: the absolute path)
3. `~/.claude/obsidian-vault` file at the global level (one line: the absolute path)
4. **Fail with a setup message** — skills never guess or create a vault silently

The project-local file (step 2) allows per-project vault overrides. Most users
will only configure the global pointer and never need the local one.

### Setup message

```
Obsidian vault not configured. Set it up with one of:

  export OBSIDIAN_VAULT="/path/to/your/vault"

Or create a persistent pointer:

  echo "/path/to/your/vault" > ~/.claude/obsidian-vault

Then re-invoke this skill.
```

---

## Skill Specifications

---

### `obsidian-capture`

**Purpose:** Instant note creation. Any thought, finding, snippet, or decision.
Parses `@tags` from the input, creates missing tag-notes, suggests existing ones.
No questions asked.

**Invocation:** `/obsidian-capture <content>`
**Model-invocable:** `true` — Claude proactively captures key findings.
**Allowed tools:** `Read Glob Bash(date:*) Bash(mkdir:*) Bash(bash:*) Write`

**Protocol:**

1. Resolve vault path. On failure: show setup message and stop.
2. Run `date +%Y%m%d%H%M` for the Zettelkasten ID and `date +%Y-%m-%d` for frontmatter.
3. Parse `$ARGUMENTS` for `@word` tokens. Each becomes a tag-note reference.
4. For each `@topic` found: run `tag-note.sh --vault VAULT --tag topic`.
   The script creates `@ (Tags)/@topic.md` if it doesn't exist.
5. If no `@tags` found in input: run `tag-note.sh --suggest --vault VAULT --content "$ARGUMENTS"`.
   The script greps existing tag-notes for semantic matches and prints suggestions.
   Print them: `Suggested tags: [[@tdd]] [[@java]] — add any with /obsidian-capture @tdd ...`
   Do not block or ask — this is advisory only.
6. Derive filename: `{ID} {first 6 words of content}.md` (slugified title portion).
7. Collision check: if `{ID}.md` prefix already exists in vault root, append next
   available letter suffix to the ID (`a`, `b`, ...) until unique.
8. Compose the note:
   ```markdown
   ---
   date: {YYYY-MM-DD}
   ---

   # {first line of content}

   {tag-link line: [[@tag1]] [[@tag2]]}

   {full content}
   ```
9. Write to `$OBSIDIAN_VAULT/{filename}.md`.
10. Confirm: `Captured → {filename}.md`

**Failure contract:**
- Vault path missing: show setup message, stop.
- Write fails: print the full composed note content so the user can paste manually.
  Never silently discard content.

---

### `obsidian-update`

**Purpose:** Add content to an existing note, identified by Zettelkasten ID or
fuzzy title search. The natural follow-up to `/recap` and `/tdd-session`.

**Invocation:** `/obsidian-update <id or title>`
**Model-invocable:** `true` — Claude can update notes after a session ends.
**Allowed tools:** `Read Glob Grep Bash(date:*) Bash(bash:*) Write Edit AskUserQuestion`

**Protocol:**

1. Resolve vault path. On failure: show setup message and stop.
2. Resolve the target note from `$ARGUMENTS`:

   **If `$ARGUMENTS` is a 12-digit number (or 12-digit + letter):**
   - Glob `$OBSIDIAN_VAULT/{id}*.md` for an exact ID match.
   - If found: use it directly.
   - If not found: report "No note found with ID `{id}`." and stop.

   **Otherwise (fuzzy title search):**
   - Run `search.sh --vault VAULT --query "$ARGUMENTS" --limit 10`.
   - Filter results to title matches only (not body matches) for precision.
   - If exactly one match: use it directly, print `Updating: {filename}`.
   - If multiple matches: present a numbered list and ask:
     ```
     Multiple notes match "{query}":
     [1] 202605101020 Rebates architecture decision.md
     [2] 202605091400 Rebates service overview.md

     Enter a number to select, or (x) to cancel.
     ```
     Wait for selection. On (x): stop.
   - If no matches: report "No note found matching `{query}`." Suggest
     `/obsidian-capture` to create one, and stop.

3. Read the selected note. Show its title and last 5 lines as context:
   ```
   Updating: 202605101020 Rebates architecture decision.md
   ...
   Last content: "commission rate is applied after tax deduction"
   ```
4. Ask: `What do you want to add?`
5. Compose the addition:
   ```markdown

   ---

   {YYYY-MM-DD} — {user's content}
   ```
6. Append to the end of the note using Edit.
7. Update the `date:` frontmatter to today.
8. Confirm: `Updated → {filename}.md`

**Failure contract:**
- If Edit fails: report the error, print the content the user wanted to add so
  nothing is lost, and stop.

---

### `obsidian-search`

**Purpose:** Search the vault and surface relevant notes.

**Invocation:** `/obsidian-search <query>`
**Model-invocable:** `true` — Claude retrieves past context autonomously.
**Allowed tools:** `Read Glob Grep Bash(bash:*) AskUserQuestion`

**Protocol:**

1. Resolve vault path. On failure: setup message and stop.
2. Run three searches (Glob + Grep) against `$OBSIDIAN_VAULT`:
   - **Tag match:** if query starts with `@`, Glob `@ (Tags)/@*{query}*.md` and
     Grep all notes for `[[@{query}]]` to find every note on that topic.
   - **Title match:** Glob `*.md` at root, filter filenames containing query terms
     (match against the title portion after the ID prefix).
   - **Full-text match:** Grep `*.md` at root for query terms.
3. Exclude `@ (Tags)/` files from title and full-text results (they're hubs, not content).
4. Merge and deduplicate. Rank: tag match > title match > body match. Return top 5.
5. Present results:
   ```
   [1] 202605101020 Rebates architecture decision.md
       Tags: [[@rebates]] [[@architecture]]
       "...commission calculations run nightly after market close..."

   [2] 202605091400 Rebates service overview.md
       Tags: [[@rebates]] [[@projects]]
       "...advisors linked by alias lookup..."
   ```
6. Ask: `Enter a number to view, or (x) to exit.`
7. On selection: Read and print the full note. Ask: `(b) Back  (x) Exit`

**When no results:** report "No notes found for `{query}`." and suggest
`/obsidian-capture @{query} ...` to create a first entry on that topic.

---

## Shared Scripts

All scripts live at `~/.claude/skills/obsidian/scripts/`.

### `vault.sh`

Resolves and validates the vault path.

```
Usage: bash ~/.claude/skills/obsidian/scripts/vault.sh
Output: absolute vault path on stdout
Exit non-zero + error message on failure
```

Logic: check `$OBSIDIAN_VAULT` → check `.claude/obsidian-vault` (project-local) →
check `~/.claude/obsidian-vault` (global) → validate path exists and contains
`.obsidian/` → print path.

### `tag-note.sh`

Ensures a tag-note exists, and optionally suggests existing tags.

```
Usage:
  bash ~/.claude/skills/obsidian/scripts/tag-note.sh --vault PATH --tag TOPIC
    → creates @ (Tags)/@{topic}.md if absent; prints its path
    → exit 0 always (idempotent)

  bash ~/.claude/skills/obsidian/scripts/tag-note.sh --suggest --vault PATH --content TEXT
    → greps existing tag-note filenames against words in TEXT
    → prints matching @tags one per line
```

### `slug.sh`

Converts a human-readable title to a kebab-case slug (used for the title
portion of the filename, after the ID).

```
Usage: bash ~/.claude/skills/obsidian/scripts/slug.sh "My Note Title"
Output: my-note-title
```

### `search.sh`

Multi-field grep search with ranked results.

```
Usage: bash ~/.claude/skills/obsidian/scripts/search.sh --vault PATH --query QUERY [--limit N]
Output: lines of: SCORE\tFILE\tSNIPPET
```

---

## `disable-model-invocation` Decisions

| Skill | Value | Rationale |
|-------|-------|-----------|
| `obsidian-capture` | `false` | Claude captures key findings proactively |
| `obsidian-update` | `false` | Claude updates notes after recap/tdd-session |
| `obsidian-search` | `false` | Claude retrieves vault context autonomously |

---

## `allowed-tools` per Skill

| Skill | Tools |
|-------|-------|
| `obsidian-capture` | `Read Glob Bash(date:*) Bash(mkdir:*) Bash(bash:*) Write` |
| `obsidian-update` | `Read Glob Grep Bash(date:*) Bash(bash:*) Write Edit AskUserQuestion` |
| `obsidian-search` | `Read Glob Grep Bash(bash:*) AskUserQuestion` |

---

## Integration Points with Existing Skills

These are **opt-in suggestions** — a one-line print at the end of the existing
skill's output, never an automatic invocation.

| Trigger | Suggested skill | Placement |
|---------|----------------|-----------|
| After `/recap` | `obsidian-update` | Last line of recap output |
| After `/tdd-session` | `obsidian-update` | After final cycle summary |
| After `/try` | `obsidian-capture` | After investigation summary |

Example line appended to `/recap`:
```
Knowledge base: run /obsidian-update <note> to log this session's progress.
```

---

---

## Implementation Order

1. **Shared scripts** — `vault.sh`, `slug.sh`, `tag-note.sh`, `search.sh`
2. **`obsidian-capture`** — smallest skill; validates the config, ID generation, and tag-note flow
3. **`obsidian-search`** — unlocks retrieval; `obsidian-update` depends on its search logic
4. **`obsidian-update`** — builds on search for note resolution

---

## Phase 2 — Future Skills

No Phase 2 skills defined yet. Candidates will be identified from real vault usage.
