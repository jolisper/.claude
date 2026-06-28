## Summary

`spec-archive` closes out a completed spec-workflow initiative by running a sequence of
pre-move checks, appending a retrospective note to the implement log, and moving
`initiatives/<name>/` to `initiatives/_archive/<name>/`. Consumer: a developer who has
finished an initiative and wants to formally close it out.

## Behavior

### Input

1. `$ARGUMENTS` is the initiative name (e.g. `my-feature`). If empty, the skill asks:
   ```
   Which initiative should be archived? (kebab-case name):
   ```
2. The skill resolves the project root via `git rev-parse --show-toplevel`. If that fails,
   it uses the current working directory and notes it.
3. If `initiatives/<name>/` does not exist, the skill stops:
   ```
   initiatives/<name>/ not found. Nothing to archive.
   ```

### Completeness check

4. The skill reads `initiatives/<name>/implement-log.md` frontmatter. If `implement-log.md`
   is missing, the skill stops:
   ```
   initiatives/<name>/implement-log.md not found. Cannot verify completeness.
   ```
5. If the frontmatter `status` field is not `complete`, the skill warns:
   ```
   implement-log.md status is "<current-status>", not "complete".
   How do you want to proceed?
   (a) Archive anyway
   (b) Cancel
   ```
   On (b): stop.

### Uncommitted changes check

6. The skill reads `implement-log.md` to identify the implementation files changed during
   the initiative. It checks those files for unstaged or uncommitted git changes.
7. If any implementation files have uncommitted changes, the skill surfaces them and asks:
   ```
   The following implementation files have uncommitted changes:
   <file list>
   How do you want to proceed?
   (a) Archive anyway
   (b) Cancel
   ```
   On (b): stop.
8. If `implement-log.md` references no implementation files, the uncommitted changes check
   is skipped and a note is printed: `No implementation files found in implement-log.md — skipping uncommitted changes check.`

### Retrospective note

9. The skill generates a retrospective paragraph from `implement-log.md` covering: phases
   completed, any deviations from the functional spec, and lessons or observations from
   the implementation.
10. The skill presents the draft and asks:
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
11. On (b): the skill accepts the user's revised text and uses it in place of the draft.
12. The skill appends the accepted retrospective under a `## Retrospective` heading at the
    end of `initiatives/<name>/implement-log.md`.

### Date stamp

13. The skill updates `implement-log.md` frontmatter: sets `status: archived` and adds
    `archived: <YYYY-MM-DD>` using today's date.

### Final confirmation and move

14. Before moving, the skill asks:
    ```
    About to move initiatives/<name>/ → initiatives/_archive/<name>/.
    How do you want to proceed?
    (a) Proceed
    (b) Cancel
    ```
    On (b): stop. The retrospective and date stamp written in the previous steps remain
    in place — the user can re-run `spec-archive` or undo manually.
15. The skill creates `initiatives/_archive/` if it does not exist, then moves
    `initiatives/<name>/` to `initiatives/_archive/<name>/`.
16. If the destination `initiatives/_archive/<name>/` already exists, the skill stops
    before moving and reports:
    ```
    initiatives/_archive/<name>/ already exists. Remove it manually before archiving.
    ```
17. After a successful move, the skill prints:
    ```
    initiatives/<name>/ archived to initiatives/_archive/<name>/.
    ```

### Edge cases

18. All checks run in order: completeness → uncommitted changes → retrospective → date
    stamp → move. A cancellation at any gate leaves all previously written changes (to
    `implement-log.md`) in place.
19. The skill does not delete the source directory before confirming the move succeeded.
    If the move fails, it reports the error and leaves `initiatives/<name>/` intact.
