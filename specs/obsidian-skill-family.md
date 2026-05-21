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

The family has **5 core skills**:

| Tier | Skill | Purpose |
|------|-------|---------|
| Setup | `obsidian-vault` | Configure and initialize a vault; validate readiness |
| Write | `obsidian-capture` | Capture session context as a note, guided by a hint |
| Write | `obsidian-literal` | Save content verbatim as a note — no synthesis or rewriting |
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

### Tag token syntax (skill input)

Skills accept `#word` tokens in their arguments to specify tags. The rules:

- **Valid characters:** letters, digits, hyphens, underscores — `[a-zA-Z0-9_-]+`
- **Case:** normalized to lowercase before use (`#Rebate` → `rebate` → `@tags/@rebate.md`)
- **Multi-word tags:** use hyphens — `#rebate-service` is one tag, maps to `@tags/@rebate-service.md`
- **Boundary:** a `#` followed by a character outside the valid set is not a tag token (e.g. `#1` is not a tag if the first char after `#` is a digit — digits are allowed only after the first letter character... actually digits are fine: `#q1` is valid, but a bare `#123` is not — the token must start with a letter)

To keep it simple: a tag token matches `#[a-zA-Z][a-zA-Z0-9_-]*`.

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

Every note created by `obsidian-capture` gets a **Zettelkasten timestamp** stored in
its frontmatter `id:` field. The filename contains only the human-readable title.

```
Rebates architecture decision.md
───────────────────────────────
        human-readable title

frontmatter:
  id: 202605111430
  date: 2026-05-11
```

**Format:** `YYYYMMDDHHmm` — year, month, day, hour, minute (12 digits, minute precision).
Generated with `date +%Y%m%d%H%M`.

**Collision handling:** if two notes are captured in the same minute, the second gets
a letter suffix on the `id:` value: `202605111430`, `202605111430a`, `202605111430b`,
etc. The skill greps vault frontmatter for the ID before writing and appends the next
available suffix. The filename is unaffected.

**Using the ID in skills:**
- `/obsidian-update 202605111430` — greps frontmatter for `^id: 202605111430`, exact match
- `obsidian-search` results always display the `id:` so the user can copy it for updates

---

## Vault Schema

```
$OBSIDIAN_VAULT/
├── @tags/
│   └── @{topic}.md    ← tag-note hubs; one per topic, person, project
└── {title}.md         ← all content notes, flat at root; ID lives in frontmatter
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
id: YYYYMMDDHHmm
created: YYYY-MM-DD
updated: YYYY-MM-DD
type: capture
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

Every note created by the skill family uses four frontmatter fields:

```yaml
---
id: YYYYMMDDHHmm
created: YYYY-MM-DD
updated: YYYY-MM-DD
type: capture
---
```

`id` is the stable unique identifier used by skills to look up notes.
`created` records when the note was first written — never changed after creation.
`updated` records the last time content was appended — set equal to `created` at creation, updated by `obsidian-update`.
`type` identifies the origin skill and enables filtered Bases views.

### Note types

| Type | Skill | Description |
|------|-------|-------------|
| `capture` | `obsidian-capture` | Hint-based snapshot synthesized from session context |
| `literal` | `obsidian-literal` *(planned)* | Verbatim content — no synthesis or rewriting |
| `journal` | `obsidian-journal` *(planned)* | Work day or session summary |
| `log` | `obsidian-log` *(planned)* | Automatic hook-driven activity log |

`obsidian-update` appends content to a note but never changes its `type`.

Tag-notes in `@tags/` have no frontmatter at all.

---

## Configuration Contract

All skills resolve the vault path using this priority chain:

1. `$OBSIDIAN_VAULT` environment variable (absolute path)
2. `.claude/obsidian-vault.json` file at the project root
3. `~/.claude/obsidian-vault.json` file at the global level
4. **Fail with a setup message** — skills never guess or create a vault silently

The project-local file (step 2) overrides the global one when both exist. The
`obsidian-vault` skill asks the user which scope to write during setup.

### Config file format

Both the project-local and global config files use JSON:

```json
{
  "vault": "/absolute/path/to/vault",
  "language": "en"
}
```

`language` is a BCP 47 / ISO 639-1 code (e.g. `"en"`, `"es"`, `"pt"`, `"fr"`).
All note content is written in this language. If absent, skills default to `"en"`.
The vault path and language always travel together in the same config file.

### Setup message

```
Obsidian vault not configured. Set it up with one of:

  export OBSIDIAN_VAULT="/path/to/your/vault"

Or run /obsidian-vault to configure interactively.

Then re-invoke this skill.
```

---

## Skill Specifications

---

### `obsidian-vault`

**Purpose:** Configure and initialize an Obsidian vault for use with the skill family.
Run once before using any other skill. Works with existing vaults and creates new ones.
Ensures the vault is in the correct state and gives a clear green light when done.

**Invocation:** `/obsidian-vault [path]`
**Model-invocable:** `false` — always explicitly triggered by the user.
**Allowed tools:** `Read Glob Bash(mkdir:*) Bash(bash:*) Write`

**Protocol:**

1. If `$ARGUMENTS` contains a path, use it. Otherwise ask for the vault path.
2. Expand `~` and resolve the absolute path.
3. **Detect vault state** (two separate bash checks):
   - Path exists + `.obsidian/` exists → existing vault, skip to step 5
   - Path exists, no `.obsidian/` → go to step 4b
   - Path does not exist → go to step 4a
4. **4a** — path missing: ask `(a) Create a new vault here / (b) Cancel`. On (a): mkdir, continue to 4b.
   **4b** — no `.obsidian/`: ask `(a) Initialize as a new Obsidian vault / (b) Cancel`. On (a): create `.obsidian/` and write `{}` to `.obsidian/app.json`.
5. **Ensure `@tags/` exists:** create it if missing. Never touch existing contents.
6. **Choose config scope:** ask `(a) Project-local (.claude/obsidian-vault.json in cwd) / (b) Global (~/.claude/obsidian-vault.json)`.
7. **Choose vault language:** ask:
   ```
   What language should notes be written in?
   Enter an ISO 639-1 code (e.g. en, es, fr, pt). Default: en
   ```
   If the answer is empty, use `en`. Store as LANG.
8. **Write config** to the chosen location:
   ```json
   { "vault": "/absolute/path/to/vault", "language": "en" }
   ```
9. **Validate** (each as a separate bash call):
   - Vault path is readable and writable
   - `.obsidian/` directory exists
   - `@tags/` directory exists
   - Config file is valid JSON, `vault` equals the correct path, `language` is present
10. Report result:
    ```
    ✓ Vault configured: /path/to/vault
    ✓ Language: {LANG}
    ✓ @tags/ ready
    ✓ Config pointer written to {config_path}
    All skills are ready to use.
    ```

**Failure contract:**
- Any mkdir or write fails: report the error and stop immediately.
- Any validation check fails: report exactly which check failed and what the user needs to fix.

---

### `obsidian-capture`

**Purpose:** Captures session context as a note. `$ARGUMENTS` is a mix of an optional
set of `#tag` tokens (anywhere in the string) and a mandatory hint. Claude strips the
tags, uses the remainder as the hint, draws on session context, and composes the note
body. Tags can appear at the start, end, or middle of the argument string.

**Invocation:** `/obsidian-capture [#tag ...] <hint> [#tag ...]`
**Model-invocable:** `false` — always explicitly triggered by the user.
**Allowed tools:** `Read Glob Grep Bash(date:*) Bash(mkdir:*) Bash(bash:*) Write`

**Protocol:**

1. Resolve vault path and read `language` from the config (default `en` if absent).
   Store as **LANG**. On vault failure: show setup message and stop.
2. Parse `$ARGUMENTS` for `#word` tokens — these are **explicit tags**. Strip them;
   the remainder is the **hint**. If the hint is empty (i.e. `$ARGUMENTS` was blank or
   contained only `#tag` tokens), ask: `What should this note capture?` Apply the same
   tag-parsing to the answer: extract any `#word` tokens as additional explicit tags,
   use the remainder as the hint.
3. Run `date +%Y%m%d%H%M` for the Zettelkasten ID and `date +%Y-%m-%d` for frontmatter.
4. For each explicit tag: check if `@tags/@{topic}.md` exists; create it if not.
   No confirmation needed.
5. Glob `@tags/` to see all existing tags. Using the hint and session context, identify
   any additional relevant tags. If found, present them numbered:
   ```
   Suggested tags: 1) #tdd  2) #java — add?
   (a) Add all
   (b) Pick — reply with numbers: 1 2 ...
   (c) Skip
   ```
   Add only confirmed tags. Create `@tags/@{topic}.md` stub for any newly added tag.
6. ID collision check: Grep vault root `*.md` files for `^id: {ID}` in frontmatter.
   If found, append next available letter suffix (`a`, `b`, ...) until unique.
7. Derive a **TITLE** from the hint and session context — a short, coherent,
   properly capitalized title that describes what the note is about. The hint is
   a spotlight, not the literal title. Do not repeat information already expressed
   by the tags — the title should complement them, not restate them.
   Example: hint `all 4 core skills implemented` + tag `#obsidian-skill-family`
   → title `Core Skills Complete` (not `Obsidian Skill Family — Core Skills Complete`).
   Derive **FILENAME** from TITLE: `{TITLE}.md` — plain spaces, no ID prefix.
8. Compose the note from session context, using the hint as a spotlight — capture only
   what the hint points to, not the full session. The note must be self-contained: a
   reader with no session context should understand it fully. Include code snippets,
   decisions, links, and references as needed. Length and structure follow the content.
   Write all prose (title, summary, Context, Content) in **LANG**. If the hint or
   session context is in a different language, translate to LANG before composing.
   Never translate: tag names (identifiers), code snippets, quoted text, or any
   other content not generated by the skill.
9. Write the note:
   ```markdown
   ---
   id: {YYYYMMDDHHmm}
   created: {YYYY-MM-DD}
   updated: {YYYY-MM-DD}
   type: capture
   ---

   # {TITLE}

   {tag-link line: [@tag1](@tags/@tag1.md) [@tag2](@tags/@tag2.md)}

   {one or two sentence summary}

   **Context:** why this was captured.

   **Content:** decisions, code, findings, references.
   ```
10. Write to `$OBSIDIAN_VAULT/{filename}.md`.
11. Confirm: `Captured → {filename}.md  (id: {ID})`

**Failure contract:**
- Vault path missing: show setup message, stop.
- Write fails: print the full composed note content so the user can paste manually.
  Never silently discard content.

---

### `obsidian-update`

**Purpose:** Add content to an existing note, identified by its Zettelkasten ID.
The natural follow-up to `/recap` and `/tdd-session`.

**Invocation:** `/obsidian-update <id> [hint]`
**Model-invocable:** `false` — always human-driven.
**Allowed tools:** `Read Glob Grep Bash(date:*) Bash(bash:*) Write Edit`

**Protocol:**

1. Resolve vault path and read `language` from the config (default `en` if absent).
   Store as **LANG**. On vault failure: show setup message and stop.
2. Extract the first whitespace-delimited token as **ID**; remainder is **HINT**.
   If ID does not match `^\d{12}[a-z]?$`: report
   "Expected a note ID (e.g. 202605111430). Use /obsidian-search to find one." and stop.
3. Grep all `*.md` files at vault root for `^id: {ID}` in frontmatter.
   - If found: use that file.
   - If not found: report "No note found with ID `{id}`." and stop.
4. Read the selected note. Show its title and last 5 lines as context:
   ```
   Updating: Rebates architecture decision.md  (id: 202605101020)
   ...
   Last content: "commission rate is applied after tax deduction"
   ```
5. If HINT is non-empty, use it directly; otherwise ask: `What do you want to add?`
6. Parse the answer (or HINT) for `#word` tag tokens. Strip them; the remainder is the content.
   For each new tag (not already linked in the note's tag-link line): check if
   `@tags/@{topic}.md` exists; create it if not. Append
   `[@topic](@tags/@topic.md)` to the note's tag-link line using Edit.
7. Compose the addition in **LANG**, translating the user's input if it is in a
   different language. Never translate: tag names (identifiers), code snippets,
   quoted text, or any other content not generated by the skill.
   ```markdown

   ---

   {YYYY-MM-DD} — {content in LANG}
   ```
8. Append to the end of the note using Edit.
9. Update the `updated:` frontmatter to today.
10. Confirm: `Updated → {filename}.md  (id: {id})`

**Failure contract:**
- If Edit fails: report the error, print the content the user wanted to add so
  nothing is lost, and stop.

---

### `obsidian-search`

**Purpose:** Search the vault and surface relevant notes.

**Invocation:** `/obsidian-search [#tag ...] [keyword ...]`
**Model-invocable:** `true` — Claude retrieves past context autonomously.
**Allowed tools:** `Read Glob Grep Bash(bash:*)`

**Search model:**

- `#word` tokens in the query are **tag filters**; remaining words are the **keyword**.
- **Tag filter:** strip the leading `#` from each tag token, then Grep all content notes
  for `](@tags/@{topic}` to collect the matching note set. Multiple tags are combined
  with OR (union) — a note is included if it links to any of the specified tags.
- **Keyword filter:** applied within the tag-filtered set (or across the full vault if
  no tags were given). Matches note filenames and body text.
- Tag-only query (no keyword): returns all notes in the tag-filtered set.
- Keyword-only query (no tags): searches the full vault.

**Protocol:**

1. Resolve vault path. On failure: setup message and stop.
2. Parse `$ARGUMENTS`: split into `#word` tag tokens and remaining keyword string.
3. **Build the candidate set:**
   - If tags present: Grep all content notes at vault root for each tag pattern
     `](@tags/@{topic}`; union the results.
   - If no tags: candidate set is all content notes at vault root.
4. **Apply keyword filter:** if a keyword string is present, filter the candidate set
   to notes whose filename or body contains the keyword terms.
5. Return top 5 results, ranked: title match > body match.
6. Present results:
   ```
   [1] Rebates architecture decision.md  (id: 202605101020)
       Tags: [@rebates](@tags/@rebates.md) [@architecture](@tags/@architecture.md)
       "...commission calculations run nightly after market close..."

   [2] Rebates service overview.md  (id: 202605091400)
       Tags: [@rebates](@tags/@rebates.md) [@projects](@tags/@projects.md)
       "...advisors linked by alias lookup..."
   ```
7. Ask: `Enter a number to view, or (x) to exit.`
8. On selection: Read and print the full note. Ask: `(b) Back  (x) Exit`

**When no results:** report "No notes found for `{query}`." and suggest
`/obsidian-capture #{topic} ...` to create a first entry on that topic.

---

## Shared Scripts

**Status: Deferred.** Shared scripts (`vault.sh`, `tag-note.sh`, `slug.sh`, `search.sh`)
were originally planned to centralize common logic. After implementing all four core
skills, the decision was made to inline the logic in each skill instead. Scripts may
be revisited if duplication becomes a maintenance burden.

---

## `disable-model-invocation` Decisions

| Skill | Value | Rationale |
|-------|-------|-----------|
| `obsidian-vault` | `true` | setup skill, always user-triggered |
| `obsidian-capture` | `true` | always explicitly triggered by the user |
| `obsidian-update` | `true` | always human-driven |
| `obsidian-search` | `false` | Claude retrieves vault context autonomously |

---

## `allowed-tools` per Skill

| Skill | Tools |
|-------|-------|
| `obsidian-vault` | `Read Glob Bash(mkdir:*) Bash(bash:*) Write` |
| `obsidian-capture` | `Read Glob Grep Bash(date:*) Bash(mkdir:*) Bash(bash:*) Write` |
| `obsidian-literal` | `Read Glob Grep Bash(date:*) Bash(mkdir:*) Bash(bash:*) Write` |
| `obsidian-update` | `Read Glob Grep Bash(date:*) Bash(bash:*) Write Edit` |
| `obsidian-search` | `Read Glob Grep Bash(bash:*)` |

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

| # | Item | Status |
|---|------|--------|
| 1 | **Shared scripts** — `vault.sh`, `slug.sh`, `tag-note.sh`, `search.sh` | ⏸ Deferred — all skills inline their logic |
| 2 | **`obsidian-vault`** — must work before any other skill; validates the entire setup | ✅ Done (`skills/obsidian-vault/SKILL.md`) |
| 3 | **`obsidian-capture`** — validates ID generation and tag-note flow | ✅ Done (`skills/obsidian-capture/SKILL.md`) |
| 4 | **`obsidian-search`** — tag and keyword search; results surface IDs for use with `obsidian-update` | ✅ Done (`skills/obsidian-search/SKILL.md`) |
| 5 | **`obsidian-update`** — ID-only note lookup via frontmatter grep | ✅ Done (`skills/obsidian-update/SKILL.md`) |
| 6 | **Language config** — `language` field in config JSON; vault setup asks for ISO code; capture and update write and translate to vault language | ✅ Done (`obsidian-vault` Step 6–7; `obsidian-capture` Step 1+9; `obsidian-update` Step 1+7) |
| 7 | **`type` frontmatter field** — `obsidian-capture` writes `type: capture`; planned types for future skills: `literal`, `journal`, `log` | ✅ Done (`obsidian-capture` Step 9) |
| 8 | **`obsidian-literal`** — verbatim capture skill; body preserved exactly as provided; only title synthesized | ✅ Done (`skills/obsidian-literal/SKILL.md`) |

---

## Phase 2 — Future Skills

### `obsidian-literal`

**Status: implemented** (`skills/obsidian-literal/SKILL.md`)

Saves content verbatim as a note — no synthesis, no rewriting, no translation of
the body. Tags are parsed from `$ARGUMENTS`; the remainder (or an interactive
answer if `$ARGUMENTS` is tag-only) becomes the note body exactly as provided.
Only the title is synthesized by the skill (in vault LANG). `type: literal`.

### `obsidian-log`

Automatically records session activity as a single Obsidian note, built incrementally
as the session progresses. The goal: a user reading the log after a long day should
have a clear picture of what happened, from a list of short summaries.

**Trigger:** `Stop` hook — fires once per turn, after Claude finishes responding.
The hook is deterministic and runs outside the session agent (no context leak).

**Mechanism:** the `Stop` hook invokes a separate `claude` CLI process using
**Claude Haiku** (fast, low cost — ~$0.000005 per turn). That process receives
the turn context (user prompt + Claude response) and appends a one-line summary
to the session log note. The session agent is unaware of the log.

**One note per session:** a new timestamped note is created at session start
(`SessionStart` hook) and appended to on each turn.

**Loggable events** (what Haiku looks for in each turn):
- Decisions made (architectural, design, product)
- Problems encountered and how they were resolved
- Files or components created or significantly modified
- Skills or tools used
- Open questions left unresolved

**Still TBD:** note format and structure, exact Haiku prompt, note naming convention,
and how granular each entry should be.

---

## Open Questions

Points that need a decision before implementation begins.

~~1. **`#tags` in title derivation**~~ — `#word` tokens are input syntax for tagging and
   are stripped before deriving the filename and heading title.

~~2. **`obsidian-update` in autonomous mode**~~ — `model-invocable` set to `false`;
   skill is always human-driven.

~~3. **Tag match grep pattern**~~ — resolved as part of the search model redesign.
   Tags are parsed separately from the query string; `#` is stripped before building
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

~~7. **`obsidian-log`**~~ — core decisions made. One note per session, incremental writes
   via `Stop` hook, Haiku writes one-line summaries per turn. Note format, Haiku prompt,
   and entry granularity still TBD — tracked in Phase 2 spec.

~~8. **Config file format**~~ — resolved. Both project-local and global config files use
   JSON: `{"vault": "/absolute/path"}`. Plain-text format rejected in favor of JSON for
   extensibility.

~~9. **Config scope selection**~~ — resolved. `obsidian-vault` asks the user at setup time
   whether to write project-local (`.claude/obsidian-vault.json`) or global (`~/.claude/obsidian-vault.json`).
   Local overrides global when both exist.
