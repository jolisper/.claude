## Summary

When `spec-functional` resolves an initiative name and finds `initiatives/<name>/initiative.md`
on disk, it reads that file automatically and uses its content as seed context for drafting
the functional spec — without requiring the user to pass the file path manually. Consumer:
a developer running `/spec-functional` inside a spec-workflow initiative that already has
an `initiative.md`.

## Behavior

1. After the initiative `<name>` is confirmed (Step 3 of `spec-functional`), the skill
   attempts to read `<project-root>/initiatives/<name>/initiative.md`.
2. If `initiative.md` is found, the skill prints:
   ```
   Found initiatives/<name>/initiative.md — using it as context.
   ```
   then incorporates its content into the definition before proceeding to Step 4.
3. If `initiative.md` is not found, the skill proceeds without it — no message, no change
   in behavior.
4. `initiative.md` content supplements `$ARGUMENTS`; it does not replace it. If both are
   present, both are used as context for drafting.
5. If `$ARGUMENTS` is empty and `initiative.md` is present, the initiative file alone
   serves as the definition — the skill does not ask "What feature should this spec define?"
6. If `$ARGUMENTS` is empty and `initiative.md` is absent, the skill asks for a definition
   as normal.
7. The auto-read happens silently in one Read call — no additional confirmation or
   user interaction is required beyond the notification in Behavior 2.
8. If the Read fails (file exists but cannot be read), the skill reports the error and
   asks whether to proceed without the initiative context or cancel.
