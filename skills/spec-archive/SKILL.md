---
name: spec-archive
description: >
  Close out a completed spec-workflow initiative. Checks completeness and uncommitted
  changes, appends a retrospective to the implement log, and moves initiatives/<name>/
  to initiatives/_archive/<name>/. Use as the final step in the spec-workflow pipeline,
  after spec-verify-static and spec-verify-dynamic.
disable-model-invocation: true
argument-hint: "<initiative-name>"
allowed-tools: Read Edit Bash(git rev-parse:*) Bash(git status:*) Bash(ls:*) Bash(mkdir:*) Bash(mv:*)
when_to_use: >
  Invoke as the final step of a spec-workflow initiative, after spec-verify-static and
  spec-verify-dynamic confirm all invariants pass. Use when the user wants to formally close out and archive an
  initiative.
effort: high
---

Archive a completed spec-workflow initiative: run four pre-move checks, append a
retrospective, update the implement log, and move the initiative directory to the archive.

**Always run all four checks before moving — do not skip any gate even when the user
seems eager to proceed.**

**All confirmation gates use plain text menus — never call AskUserQuestion. Print the
menu, wait for the user's reply, then act on it.**

## Step 1 — Accept initiative name

`$ARGUMENTS` is the initiative name. If empty, ask:

```
Which initiative should be archived? (kebab-case name):
```

## Step 2 — Resolve project root

Run `git rev-parse --show-toplevel`. Use the result as `<root>`. If it fails, use the
current working directory and note it.

## Step 3 — Verify initiative exists

Run `ls <root>/initiatives/<name>/`. If the directory does not exist, stop:

```
initiatives/<name>/ not found. Nothing to archive.
```

## Step 4 — Completeness check

Read `<root>/initiatives/<name>/logbook.md`. If missing, stop:

```
initiatives/<name>/logbook.md not found. Cannot verify completeness.
```

Read the frontmatter `status` field. If not `complete`, ask:

```
logbook.md status is "<current-status>", not "complete".
How do you want to proceed?
(a) Archive anyway
(b) Cancel
```

On (b): stop.

## Step 5 — Uncommitted changes check

Read `logbook.md` to identify the implementation files changed during the initiative.

If no implementation files are referenced, print:
```
No implementation files found in logbook.md — skipping uncommitted changes check.
```
and proceed to Step 6.

Run `git status --porcelain <implementation files>`. If any have unstaged or uncommitted
changes, surface them and ask:

```
The following implementation files have uncommitted changes:
<file list>
How do you want to proceed?
(a) Archive anyway
(b) Cancel
```

On (b): stop.

## Step 6 — Retrospective note

Read `logbook.md` and generate a retrospective paragraph covering: phases completed,
any deviations from the functional spec, and lessons or observations from the implementation.

Present the draft and ask:

```
Retrospective draft:
---
<draft text>
---
How do you want to proceed?
(a) Append as shown
(b) Edit — paste your revised version
(c) Cancel
```

On (c): stop.
On (b): ask "Paste your revised retrospective:" and use the user's reply in place of the draft.

Append the accepted text to `logbook.md` under a `## Retrospective` heading at the
end of the file.

## Step 7 — Date stamp

Edit `logbook.md` frontmatter: set `status: archived` and add `archived: <YYYY-MM-DD>`
using today's date.

## Step 8 — Final confirmation and move

Ask:

```
About to move initiatives/<name>/ → initiatives/_archive/<name>/.
How do you want to proceed?
(a) Proceed
(b) Cancel
```

On (b): stop. The retrospective and date stamp written in Steps 6–7 remain in place —
re-run `spec-archive` or undo them manually.

Run `ls <root>/initiatives/_archive/<name>/` to check whether the destination already
exists. If it does, stop:

```
initiatives/_archive/<name>/ already exists. Remove it manually before archiving.
```

Run `mkdir -p <root>/initiatives/_archive/`.

Run `mv <root>/initiatives/<name>/ <root>/initiatives/_archive/<name>/`.

If the move fails: report the error and stop — `initiatives/<name>/` remains intact.

On success, print:

```
initiatives/<name>/ archived to initiatives/_archive/<name>/.
```
