---
name: obsidian-tags
description: >
  Use this skill to analyze the vault for recurring topics and suggest new
  tags. Invoke when the user runs /obsidian-tags to discover tagging
  opportunities across the vault and optionally backfill accepted tags onto
  existing notes.
argument-hint: "[topic or keyword]"
disable-model-invocation: true
allowed-tools: Read Glob Grep Bash(bash:*) Bash(date:*) Edit Write
when_to_use: >
  Invoke when the user explicitly runs /obsidian-tags to audit the vault's
  tag coverage and discover new tag candidates based on vault-wide analysis.
---

Analyze the vault for recurring topics and suggest new tags. `$ARGUMENTS` is
an optional keyword or topic to focus the analysis on.

## Step 1 — Resolve vault path and language

Check in order, stopping at the first match. Set VAULT to the resolved path.
Also read the `language` field from the matched config file; set **LANG** to
that value. If absent or VAULT came from the env var, default LANG to `en`.

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

If `$ARGUMENTS` is non-empty, store it as **FOCUS** — a keyword or topic to
prioritize during analysis. Otherwise FOCUS is empty (full vault analysis).

## Step 3 — Read vault notes

Glob `{VAULT}/*.md` to get all root-level content notes. Exclude any files
under `{VAULT}/@tags/`.

For each note:
- Read the frontmatter `type:` field.
- If `type: log`, add to **SKIPPED** list and skip — do not read further.
- Otherwise, read the file and extract:
  - **Filename** (without path)
  - **Existing tags** — all `[@tag]` tokens from the tag-link line (the first
    non-empty line after the `# Heading` containing `](@tags/`). Empty if no
    tag-link line exists.
  - **Summary** — the first non-empty line after the tag-link line (or after
    the heading if no tag-link line).
  - **Body** — remaining content below the summary.

## Step 4 — Build user-owned tag list

Glob `{VAULT}/@tags/@*.md` to get all tag stubs. For each stub, read it and
check whether its content contains `managed-by:`. Strip `@` prefix and `.md`
suffix from stubs that do **not** contain `managed-by:`. Store as **USER_TAGS**.

Tags with `managed-by:` are system-owned and must be excluded from all
suggestion and matching logic.

## Step 5 — Analyze for tag candidates

Study all non-skipped notes together. Identify topics, tools, concepts, or
themes that:

1. Appear across **two or more** notes (in filename, summary, or body).
2. Are **not already represented** by any tag in USER_TAGS.
3. Are **specific enough to be useful** as a filter — not generic terms like
   "work" or "session", but meaningful identifiers like `voiceink`, `esco3`,
   `kinesis-freestyle`, or `balances`.

For each candidate, record:
- **PROPOSED_NAME** — lowercase, hyphen-separated identifier
- **RATIONALE** — one short phrase describing what it groups
- **MATCHING_NOTES** — list of filenames this tag applies to

If FOCUS is set, prioritize candidates related to FOCUS; still include other
strong candidates if they emerge naturally.

Target 3–8 candidates. Discard candidates that only apply to a single note or
that are too generic to be useful as a filter.

## Step 6 — Present candidates

If no candidates found, report:
```
No new tag candidates found — the vault's current tags appear to cover the
recurring topics well.
```
and stop.

Otherwise print (write rationales in LANG):

```
Vault analysis — N notes read, M skipped (type: log), K existing tags.

Suggested new tags:

1) #proposed-name — rationale
   → Note Title One.md
   → Note Title Two.md

2) #proposed-name — rationale
   → Note Title Three.md, Note Title Four.md

...

(a) Accept all
(b) Pick — reply with numbers: 1 2 ...
    To rename while picking, add the new name after the number: 1 new-name 2
(c) Abort
```

Wait for the user's reply.

On (c): stop.

On (a) or (b): parse the selection into **ACCEPTED** candidates. When the
user's reply contains `N new-name` pairs (e.g. `1 voiceink-app 2`), apply
the new name to that candidate. Normalize any user-supplied name to lowercase
and replace spaces with hyphens.

After parsing, if any accepted candidate still uses Claude's proposed name,
ask once:
```
Any renames? (e.g. 1 new-name 2 other-name)
(s) Skip — keep all proposed names
```
On (s) or any reply that contains no rename pairs: keep all proposed names and proceed.
Otherwise apply the supplied renames and proceed.

## Step 7 — Create tag stubs

For each tag in ACCEPTED:

Run `bash -c "test -f '{VAULT}/@tags/@{tag}.md'"`. If non-zero:
Write to `{VAULT}/@tags/@{tag}.md`:
```markdown
# @{tag}
```
No frontmatter — user-created stubs are plain.

## Step 8 — Offer backfill

For each tag in ACCEPTED, print:

```
Apply #tag-name to N note(s)?
  1) Note Title One.md
  2) Note Title Two.md
(a) Apply to all
(b) Pick — reply with numbers: 1 2 ...
(c) Skip
```

Wait for the user's reply. Collect the notes to backfill for this tag into
**BACKFILL**. Repeat for each accepted tag before proceeding to Step 9.

## Step 9 — Apply backfill

Run `date +%Y-%m-%d` → **TODAY**.

For each (tag, note) pair in BACKFILL:

1. Read the note.
2. Update the tag-link line using Edit:
   - If the note has a tag-link line (a line containing `](@tags/`): append
     ` [@{tag}](@tags/@{tag}.md)` to it.
   - If no tag-link line exists: insert `[@{tag}](@tags/@{tag}.md)` as a new
     line immediately after the `# Heading` line, followed by a blank line.
3. Update the `updated:` frontmatter field to TODAY using Edit.

If an edit fails on a specific note, report it and continue — do not abort.

## Step 10 — Confirm

Print a summary (in LANG):

```
Done.

New tags created: #tag1, #tag2, ...
Backfilled:
  #tag1 → Note A.md, Note B.md
  #tag2 → Note C.md
  (skipped: #tag3)
```

Omit the Backfilled section if nothing was backfilled.

## Failure contract

- **Vault not configured:** show the setup message from Step 1 and stop.
- **No candidates found:** report and stop (see Step 6).
- **Edit fails on a note:** report which note failed and continue with the
  remaining backfill.
