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
- `app.json: {}` — pure defaults
- No community plugins installed
- Core plugins enabled: `graph`, `backlink`, `outgoing-link`, `tag-pane`, `properties`,
  `daily-notes`, `templates`, `bases`, `sync`

### Markdown Links

Skills use standard markdown links — not wikilinks. Link format:
`[display text](relative/path/to/note.md)`. This avoids any Obsidian-specific
syntax and keeps notes portable. Obsidian resolves markdown links in the graph
and backlinks panel the same way it resolves wikilinks.

### Tag-Notes Pattern

A tag-note is a regular `.md` file whose name starts with `@`, stored in the
`@tags/` folder. Content notes link to it with `[@topic](@tags/@topic.md)`.
The backlinks panel on `@topic.md` becomes a live, auto-maintained index of
every note on that topic — no queries, no plugins, no maintenance.

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
├── @tags/
│   └── @{topic}.md              ← tag-note hubs; one per topic, person, project
└── {YYYYMMDDHHmm} {title}.md   ← all content notes, flat at root
```

That's the entire structure. No `Inbox/`, `Projects/`, `Notes/`, or `Daily/` folders.
The `@tags/` folder is the only special directory — its `@` prefix keeps it at
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

[@tag1](@tags/@tag1.md) [@tag2](@tags/@tag2.md)

{one or two sentence summary}

**Context:** why this was captured.

**Content:** decisions, code, findings, references.
```

The tag-link line immediately follows the heading. The summary provides an at-a-glance
overview and is a primary target for search ranking. `Context` and `Content` are always
present; additional sections (e.g. `**Decision**`, `**References**`) may be added when
the content warrants it.

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

**Purpose:** Captures session context as a note. `$ARGUMENTS` is a hint or instruction
— not the literal note content. Claude reads the hint, draws on session context, and
composes the note body. `@tags` in the hint become tag-note references. No questions asked.

**Invocation:** `/obsidian-capture <hint>`
**Model-invocable:** `false` — always explicitly triggered by the user.
**Allowed tools:** `Read Glob Bash(date:*) Bash(mkdir:*) Bash(bash:*) Write`

**Protocol:**

1. Resolve vault path. On failure: show setup message and stop.
2. Run `date +%Y%m%d%H%M` for the Zettelkasten ID and `date +%Y-%m-%d` for frontmatter.
3. Parse `$ARGUMENTS` for `@word` tokens — these are **explicit tags**.
4. For each explicit tag: run `tag-note.sh --vault VAULT --tag topic`.
   The script creates `@tags/@topic.md` if it doesn't exist. No confirmation needed.
5. Glob `@tags/` to see all existing tags. Using the hint and session context, identify
   any additional relevant tags. If found, present them for confirmation:
   ```
   Suggested tags: @tdd @java — add? (y/n or pick: 1 2)
   ```
   Add only confirmed tags. Run `tag-note.sh` for any confirmed tag that doesn't exist yet.
6. Strip `@word` tokens from `$ARGUMENTS`, then derive filename:
   `{ID} {first 6 words of stripped content}.md` — title portion uses plain
   spaces (e.g. `202605111430 Rebates architecture decision.md`).
7. Collision check: if `{ID}.md` prefix already exists in vault root, append next
   available letter suffix to the ID (`a`, `b`, ...) until unique.
8. Compose the note from session context, using the hint as a spotlight — capture only
   what the hint points to, not the full session. The note must be self-contained: a
   reader with no session context should understand it fully. Include code snippets,
   decisions, links, and references as needed. Length and structure follow the content.
9. Write the note:
   ```markdown
   ---
   date: {YYYY-MM-DD}
   ---

   # {title}

   {tag-link line: [@tag1](@tags/@tag1.md) [@tag2](@tags/@tag2.md)}

   {one or two sentence summary}

   **Context:** why this was captured.

   **Content:** decisions, code, findings, references.
   ```
10. Write to `$OBSIDIAN_VAULT/{filename}.md`.
11. Confirm: `Captured → {filename}.md`

**Failure contract:**
- Vault path missing: show setup message, stop.
- Write fails: print the full composed note content so the user can paste manually.
  Never silently discard content.

---

### `obsidian-update`

**Purpose:** Add content to an existing note, identified by Zettelkasten ID or
fuzzy title search. The natural follow-up to `/recap` and `/tdd-session`.

**Invocation:** `/obsidian-update <id or title>`
**Model-invocable:** `false` — always human-driven.
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

**Search model:**

- `@word` tokens in the query are **tag filters**; remaining words are the **keyword**.
- **Tag filter:** strip the leading `@` from each tag token, then Grep all content notes
  for `](@tags/@{topic}` to collect the matching note set. Multiple tags are combined
  with OR (union) — a note is included if it links to any of the specified tags.
- **Keyword filter:** applied within the tag-filtered set (or across the full vault if
  no tags were given). Matches note filenames and body text.
- Tag-only query (no keyword): returns all notes in the tag-filtered set.
- Keyword-only query (no tags): searches the full vault.

**Protocol:**

1. Resolve vault path. On failure: setup message and stop.
2. Parse `$ARGUMENTS`: split into `@word` tag tokens and remaining keyword string.
3. **Build the candidate set:**
   - If tags present: Grep all content notes at vault root for each tag pattern
     `](@tags/@{topic}`; union the results.
   - If no tags: candidate set is all content notes at vault root.
4. **Apply keyword filter:** if a keyword string is present, filter the candidate set
   to notes whose filename or body contains the keyword terms.
5. Return top 5 results, ranked: title match > body match.
6. Present results:
   ```
   [1] 202605101020 Rebates architecture decision.md
       Tags: [@rebates](@tags/@rebates.md) [@architecture](@tags/@architecture.md)
       "...commission calculations run nightly after market close..."

   [2] 202605091400 Rebates service overview.md
       Tags: [@rebates](@tags/@rebates.md) [@projects](@tags/@projects.md)
       "...advisors linked by alias lookup..."
   ```
7. Ask: `Enter a number to view, or (x) to exit.`
8. On selection: Read and print the full note. Ask: `(b) Back  (x) Exit`

**When no results:** report "No notes found for `{query}`." and suggest
`/obsidian-capture @{topic} ...` to create a first entry on that topic.

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

Ensures a tag-note exists.

```
Usage:
  bash ~/.claude/skills/obsidian/scripts/tag-note.sh --vault PATH --tag TOPIC
    → creates @tags/@{topic}.md if absent; prints its path
    → exit 0 always (idempotent)
```

### `slug.sh`

Converts a human-readable title to a kebab-case slug. Not used for note
filenames (which use plain spaces). Reserved for future skills that need
a URL-safe identifier.

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

`SCORE` is an integer: +2 for each keyword term matched in the filename or summary
line, +1 for each term matched elsewhere in the body. Results sorted descending by
score; newest ID first as tiebreaker.

---

## `disable-model-invocation` Decisions

| Skill | Value | Rationale |
|-------|-------|-----------|
| `obsidian-capture` | `true` | always explicitly triggered by the user |
| `obsidian-update` | `false` | always human-driven |
| `obsidian-search` | `false` | Claude retrieves vault context autonomously |

---

## `allowed-tools` per Skill

| Skill | Tools |
|-------|-------|
| `obsidian-capture` | `Read Glob Bash(date:*) Bash(mkdir:*) Bash(bash:*) Write AskUserQuestion` |
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

### `obsidian-literal`

Captures input exactly as-is, with no Claude interpretation or composition. The raw
content of `$ARGUMENTS` becomes the note body. For when the user wants to preserve
a snippet, quote, code block, or raw thought verbatim. Format TBD.

### `obsidian-log`

An activity log skill, model-invocable. Monitors session interactions and captures
important topics, decisions, and actions as structured log entries. Intended to run
autonomously — Claude decides what is worth logging. Format and trigger conditions TBD.

---

## Open Questions

Points that need a decision before implementation begins.

~~1. **`@tags` in title derivation**~~ — `@word` tokens are input syntax for tagging and
   are stripped before deriving the filename and heading title.

~~2. **`obsidian-update` in autonomous mode**~~ — `model-invocable` set to `false`;
   skill is always human-driven.

~~3. **Tag match grep pattern**~~ — resolved as part of the search model redesign.
   Tags are parsed separately from the query string; `@` is stripped before building
   the grep pattern. Multiple tags use OR. See updated search protocol.

~~4. **Tag suggestion mechanism**~~ — resolved. Claude globs `@tags/` and uses session
   context to suggest additional tags. Explicit tags are applied automatically; suggested
   tags require user confirmation. `tag-note.sh --suggest` mode removed.

~~5. **`search.sh` SCORE**~~ — resolved. SCORE is an integer computed as:
   +2 for each keyword term matched in the filename, +1 for each term matched in the
   body. Results sorted descending by score; newest ID first as tiebreaker.

~~6. **`obsidian-capture` composition guidelines**~~ — resolved. Hint acts as a spotlight.
   Note must be self-contained. Fixed structure: title, tags, summary, Context, Content.
   Length and additional sections follow the content.

7. **`obsidian-log` — format and trigger conditions TBD**
   Needs decisions on: what constitutes a loggable event, entry format, whether it writes
   one note per session or appends to a running log, and how Claude decides what to capture.
