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

## Open design question: frontmatter vs. tag-notes for `project`

This is the primary unresolved question. It has family-wide impact.

### Background

The existing skill family uses a **tag-note system** in the note body:
`[@tag](@tags/@tag.md)` wikilinks, backed by stub files in `@tags/`. Designed
for Obsidian graph navigation and cross-skill consistency.

Obsidian Bases (v1.9+) **only reads frontmatter** — body tag-links are invisible
to it. Structured task fields (`status`, `due`, `priority`, `project`) must be in
frontmatter to be Bases-queryable.

### Use cases analyzed

| Use case | Tag-notes | Frontmatter |
|---|---|---|
| "Show all open tasks for project-x" | skill greps manually | Bases native filter |
| "Show everything related to project-x" (tasks, captures, ADRs) | grep across all note types — works because every skill writes tag-links | needs `project` field on every note type |
| "What's due this week?" | impossible — no typed date value | Bases date filter |
| Navigate from task → project note in Obsidian | clickable wikilink | plain text, no navigation |

### Emerging frame

- **Tag-notes** are good for *identity* — what a note is about, graph connections,
  human navigation, cross-note-type queries.
- **Frontmatter** is good for *state* — typed values, lifecycle fields, Bases queries,
  fields that change over time.

Under this reading: `project` as a tag-note links a task to a project and enables
cross-type vault queries. `status`, `due`, `priority` as frontmatter enable Bases
filtering and date sorting. Both systems doing different things, not competing.

### Not yet decided

- Whether `project` lives in frontmatter, tag-notes, or both.
- Whether other note types (capture, journal, literal) should adopt a `project`
  frontmatter field for Bases compatibility — or whether tag-notes remain the
  only cross-type linking mechanism.
- Whether the skill writes both representations when `project` is specified
  (frontmatter + tag-link) and what the maintenance contract looks like.

---

## Frontmatter schema (partial — pending project decision)

```yaml
---
id: 202605301042
created: 2026-05-30
updated: 2026-05-30
type: task
status: todo
due: 2026-06-10          # optional, ISO date
priority: medium         # optional: low | medium | high
project: project-x       # optional — format TBD (tag ref or free text)
---
```

---

## Notes

- Managed tag: `@task` (stub contains `managed-by: obsidian-task`).
- The skill does **not** delegate status transitions to `/obsidian-update` —
  it owns frontmatter mutations directly.
- `/obsidian-search` remains a general-purpose search skill; task-specific
  list/filter modes live in this skill.
