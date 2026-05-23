# Spec: `obsidian-tags` Skill

## Implementation Status

✅ Implemented

---

## Summary

A skill that reads the entire vault, identifies recurring topics and concepts
that aren't yet captured as tags, and suggests a curated set of new tag
candidates. The user picks which to accept, and optionally backfills accepted
tags onto existing notes.

## Motivation

Tag suggestion in capture and related skills only matches against the
*existing* tag list — when no existing tag fits, the step is silently skipped.
The right fix isn't to guess new tags inline (no vault context), but to have a
dedicated research skill that reads the vault as a whole and discovers what
tags *should* exist, grounded in actual content.

This skill fills that gap: a deliberate, on-demand audit that grows the tag
vocabulary and retroactively applies it.

## Invocation

```
/obsidian-tags [topic]
```

The optional `topic` argument focuses the analysis on a specific keyword or
theme (e.g. `/obsidian-tags voiceink`). Without it, the full vault is analyzed.

## Behavior Contract

### Analysis

1. Read all root-level `.md` notes in the vault (exclude `@tags/` stubs).
2. Skip any note whose frontmatter contains `type: log` — log notes are
   session transcripts; their topics are already summarized in captures and
   journals. Report skipped notes in the output (e.g. `✗ Log 2026-05-21.md
   (skipped — type: log)`).
3. For each remaining note: extract existing tags, summary line, and body content.
4. Exclude **managed tags** from the existing tag list — any tag whose stub
   contains a `managed-by:` frontmatter field is system-owned and must not
   be suggested or reused by this skill (see Design Decisions).
4. Identify topics, tools, concepts, or themes that:
   - Appear across **two or more** notes (title, summary, or body).
   - Are **not already represented** by any existing user-owned tag.
   - Are **specific enough to be useful** as a filter — not generic terms
     like "work" or "notes", but identifiers like `voiceink`, `esco3`,
     `kinesis-freestyle`, or `balances`.
6. For each candidate: record which notes it applies to.
7. Target 3–8 candidates. Drop single-note or overly broad hits.

### Presentation

Show each candidate with a one-line rationale, the notes it covers, and a
rename prompt. The header reports how many notes were read and how many were
skipped:

```
Vault analysis — 12 notes read, 2 skipped (type: log), 3 existing tags.

Suggested new tags:

1) #voiceink — dictation tool appearing in 2 notes
   → Integración VoiceInk con Kinesis Freestyle Pro.md
   → Journal 2026-05-22.md
   Rename? (press enter to keep, or type a new name)

2) #kinesis-freestyle — keyboard hardware configuration
   → Integración VoiceInk con Kinesis Freestyle Pro.md
   Rename? (press enter to keep, or type a new name)

3) #balances — financial data processing work
   → Primer run del Esco3MovementsComparator en producción.md, ...
   Rename? (press enter to keep, or type a new name)

(a) Accept all
(b) Pick — reply with numbers: 1 2 ...
(c) Abort
```

The rename prompt is shown for every candidate before the accept/pick menu.
If the user types a new name, that name is used instead of Claude's proposal.
If the user presses enter, the proposed name is kept.

### Tag stub creation

For each accepted tag, create `@tags/@{tag}.md` if it doesn't already exist.
User-created tag stubs have no frontmatter:

```markdown
# @voiceink
```

### Backfill (per accepted tag)

For each accepted tag, offer to apply it to its matching notes:

```
Apply #voiceink to 2 note(s)?
  1) Integración VoiceInk con Kinesis Freestyle Pro.md
  2) Journal 2026-05-22.md
(a) Apply to all
(b) Pick — reply with numbers: 1 2 ...
(c) Skip
```

Backfill edits:
- Append `[@tag](@tags/@tag.md)` to the tag-link line if one exists.
- Insert a new tag-link line after the `# Heading` if none exists.
- Update `updated:` frontmatter to today's date.

If a backfill edit fails on a specific note, report it and continue — do not
abort the rest.

### Confirmation

At the end, print a summary of what was created and where tags were applied.

## Design Decisions

**Why vault-wide, not inline?**
Inline suggestions (guessing from a single note) lack context. A tag should
reflect a pattern across multiple notes — the vault is the source of truth for
what patterns actually exist.

**Why two or more notes as the threshold?**
A tag that applies to only one note is a label, not a filter. Tags earn their
place when they connect things. The threshold can be revisited once the vault
grows.

**Why separate from capture/literal/journal?**
Those skills run at note-creation time with no vault context loaded. Vault
analysis is expensive and deliberate — it belongs in a dedicated on-demand
skill, not inline in the capture flow.

**Backfill is opt-in per tag**
The user may accept a tag for future use but not want to touch existing notes.
Backfill is offered separately for each tag so they can be selective.

**System-owned tags (`managed-by:` convention)**
Not all tags are equal. Some tags (`#log`, `#journal`) are created and applied
exclusively by their respective skills (`obsidian-log`, `obsidian-journal`) and
should never be surfaced as suggestions to the user.

This is encoded in the tag stub itself via a `managed-by:` frontmatter field:

```markdown
---
managed-by: obsidian-log
---

# @log
```

Any stub with `managed-by:` is system-owned. Skills that suggest tags (this
skill, plus the suggestion step in `obsidian-capture`, `obsidian-literal`, and
`obsidian-journal`) must read all stubs, filter out those with `managed-by:`,
and only work with the remaining user-owned tags.

User-created stubs have no frontmatter — the absence of `managed-by:` is the
signal that a tag is user-owned and available for suggestion.

The `managed-by` value identifies the owning skill, serving as documentation
as well as the filter key. The convention does not affect notes that carry
the tag — only the stub file.

**Log notes are excluded from analysis**
Notes with `type: log` in frontmatter are session transcripts and are skipped
during vault scanning. Their topics are already distilled into captures and
journals, which are included. This keeps the analysis fast and avoids noise
from raw turn-by-turn logs.

**Claude proposes tag names; user can rename**
After analysis, each candidate is shown with Claude's proposed tag name. The
user can accept it (press enter) or type a replacement before anything is
created. This keeps the flow fast while preserving naming control.

**Always full scan on re-run**
Every invocation reads the whole vault fresh. No state is tracked between
runs. This is simple, predictable, and automatically includes notes added
since the last run.

## Relationship to Other Skills

| Skill | Relationship |
|---|---|
| `obsidian-capture` / `obsidian-literal` / `obsidian-journal` | Tag-suggestion step matches from existing user-owned tags — `obsidian-tags` is how new tags enter that list |
| `obsidian-log` | Creates and applies `#log`; owns `@tags/@log.md` with `managed-by: obsidian-log` |
| `obsidian-journal` | Creates and applies `#journal`; owns `@tags/@journal.md` with `managed-by: obsidian-journal` |
| `obsidian-update` | Backfill reuses the same tag-link edit logic |
| `obsidian-search` | Searches by existing tags — quality depends on how well the tag vocabulary covers the vault |

## Consequential Changes

Adopting the `managed-by:` convention requires updates beyond this skill:

| Artifact | Change |
|---|---|
| `@tags/@log.md` in vault | Add `managed-by: obsidian-log` frontmatter |
| `obsidian-log` stop-hook script | Write stub with `managed-by:` frontmatter when creating it |
| `obsidian-journal` SKILL.md | Write `@journal` stub with `managed-by:` frontmatter when creating it |
| `obsidian-capture` Step 6 | Filter out managed tags before matching suggestions |
| `obsidian-literal` Step 6 | Filter out managed tags before matching suggestions |
| `obsidian-journal` Step 8 | Filter out managed tags before matching suggestions |
