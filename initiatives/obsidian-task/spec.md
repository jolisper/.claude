# Spec: obsidian-task

Status: **draft — design in progress**

---

## Purpose

A skill that manages the full lifecycle of a task note inside the Obsidian vault.
Unlike other obsidian-* skills that write and forget, `obsidian-task` owns create,
update, and query — one skill, multiple modes.

---

## Command surface

First token of `$ARGUMENTS` dispatches to a mode. Reserved verbs:

```
/obsidian-task                          → create (interactive)
/obsidian-task <hint>                   → create with hint
/obsidian-task list                     → show open tasks
/obsidian-task list #tag                → filter by tag
/obsidian-task start <id>              → todo → in-progress
/obsidian-task hold <id>               → any → hold
/obsidian-task done <id>               → any → done
/obsidian-task cancel <id>             → any → cancelled
```

Anything whose first token is not a reserved word is treated as a create hint.

---

## Status vocabulary

Five states, linear with a branch at the end:

```
todo → in-progress → done
                   → cancelled
     → hold (from any active state)
```

`hold` means paused intentionally — distinct from `cancelled` (abandoned) and
from blocked (not modeled explicitly).

---

## Date standard

All dates stored as ISO 8601: `YYYY-MM-DD`. Natural language input (`friday`,
`next week`, `2026-06-10`) is normalized to ISO at write time by the skill.
This applies across all obsidian-* skills, not just obsidian-task.

---

## Design decisions: tag-notes vs. Obsidian tags vs. frontmatter

This section records the design analysis and decisions made for the skill family.
It has family-wide impact beyond `obsidian-task`.

### The three systems

| System | How written | Obsidian sees it as | Bases-queryable | Graph edge |
|---|---|---|---|---|
| **Tag-note** | `[@tag](@tags/@tag.md)` in body | a link between two files | No | Yes |
| **Obsidian tag** | `#tag` in body or `tags:` in frontmatter | a tag index entry | Yes | No |
| **Frontmatter field** | `key: value` in YAML block | structured metadata | Yes | No |

Tag-notes and Obsidian tags look similar conceptually (both label a note) but
Obsidian handles them through entirely separate internal systems.

### Role of each system

- **Frontmatter** is authoritative for **querying and filtering** — Bases, scripts,
  structured reads. Only holds fields the skill owns completely (type, status, due,
  priority). Fields a human must supply (project) do not belong here: no skill can
  derive them reliably, so they become a maintenance burden.

- **Tag-notes** serve as **multi-dimensional labeling** — a folder replacement that
  lets a note belong to multiple topics simultaneously. Their value is the graph hub
  and backlinks panel, which emerge at scale. Overlap with frontmatter is acceptable
  when a skill owns both sides (e.g. `type: log` + `@log` tag-note).

### Decision: `project` stays in tag-notes only

`project` will not be added to frontmatter. No skill can derive which project a note
belongs to — it requires human input at write time, making it a maintenance liability.
Tag-notes handle project association through wikilinks; backlinks provide the index
for free.

### Decision: tag-notes are stubs

Tag-notes remain stub files (heading only, no content). The backlinks panel provides
the per-tag index without any maintained list.

### Open question: tag-notes vs. native Obsidian tags

Whether to replace tag-notes with native Obsidian tags (`#tag` / `tags:` frontmatter)
is not yet resolved. The trade-off:

- Native tags: Bases-queryable, no stub files, simpler — but no graph hub node.
- Tag-notes: graph edges and backlinks as index — but Bases-invisible, requires
  `@tags/` directory and stub files.

Current tag stubs are all empty (heading only), so the "content" advantage of
tag-notes is not being used. Graph hub value emerges at scale; the vault is young.

---

## Frontmatter schema

```yaml
---
id: 202605301042
created: 2026-05-30
updated: 2026-05-30
type: task
status: todo
due: 2026-06-10          # optional, ISO date
priority: medium         # optional: low | medium | high
---
```

Project association is handled via tag-notes in the note body, not frontmatter.

---

## Notes

- Managed tag: `@task` (stub contains `managed-by: obsidian-task`).
- Tag-notes remain stubs — no maintained index list. Obsidian backlinks provide the index for free.
- The skill does **not** delegate status transitions to `/obsidian-update` —
  it owns frontmatter mutations directly.
- `/obsidian-search` remains a general-purpose search skill; task-specific
  list/filter modes live in this skill.
