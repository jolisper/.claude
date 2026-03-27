---
name: git-rebase
description: >
  Use this skill when the user wants to rebase the current branch onto its
  base branch. Invoke for requests like "rebase", "rebase onto main", or
  "sync with main". Guides conflict resolution file-by-file with a per-file
  menu.
disable-model-invocation: true
argument-hint: "target branch (optional)"
allowed-tools: Bash(git status:*) Bash(git rev-parse:*) Bash(git log:*) Bash(git branch:*) Bash(git fetch:*) Bash(git rebase:*) Bash(git stash:*) Bash(git diff:*) Bash(git add:*) Bash(git checkout:*) Bash(python3:*) Read Edit
---

Update the current branch by rebasing it onto its base branch (the branch it was originally created from). Follow this protocol:

**Important**: Never use `cd`, `git -C`, `&&`, or `||`. Run each command separately with no path arguments — rely on the shell's current working directory.

## Step 1 — Pre-flight check

**Target branch override**: If `$ARGUMENTS` is set and non-empty, use it as the base branch and skip auto-detection in step 3 below.

Run each of these commands separately:

1. `git status`
2. `git rev-parse --abbrev-ref HEAD` — note the current branch name.
3. **Detect the base branch** (skip if `$ARGUMENTS` provided): First check the branch's reflog for its actual creation source:
   - Run `git log -g --format="%gs" <current-branch>` and look for an entry matching `branch: Created from <source>`. Use the most recent such entry and extract `<source>` as the base branch.
   - If the reflog yields no result, fall back to checking common branch names with `git branch -a`: prefer `main`, then `master`, then `develop`, then `dev`.
   - If neither approach yields a clear result, ask the user: "Which branch is the base branch for this rebase?"
4. **Shared branch guard**: Run `git branch -r --list origin/<current-branch>`.
   - If the remote branch exists, warn the user:
     ```
     ⚠ Warning: `<current-branch>` exists on the remote. Rebasing will rewrite its
     history, causing divergence for anyone else tracking this branch.

     How do you want to proceed?
     (a) Proceed — I understand this branch is shared and intend to rewrite its history
     (b) Abort
     ```
   - Even if the user explicitly asked to rebase, still surface this warning — the user may not have considered that others are tracking this branch.
   - On (b): stop.
5. `git fetch origin`
6. `git log HEAD..origin/<base> --oneline` — if output is empty after fetch, report "Already up to date" and stop.

## Step 2 — Handle dirty working tree

If `git status` shows uncommitted changes:
- Tell the user what changed and ask whether to: (a) stash changes, rebase, then restore — or (b) abort.
- If stash: run `git stash`, then continue, then `git stash pop` at the end.
- Do not rebase over a dirty tree.

## Step 3 — Rebase

Run `git rebase origin/<base>` and capture the full output.

## Step 4 — Interpret the result

Report exactly one of these outcomes:

- **Rebased cleanly** — show rebased commits: `git log ORIG_HEAD..HEAD --oneline`, then proceed to Step 5.
- **Auth / network error** — show the error and suggest checking SSH keys or credentials.
- **Other error** — show stderr and explain the likely cause.
- **Rebase conflict** — follow the guided conflict flow below (Steps 4a–4d).

### Step 4a — Announce conflict summary and upfront analysis

When `git rebase origin/<base>` exits with a conflict:
1. Run `git diff --name-only --diff-filter=U` to get the list of conflicting files.
2. Announce: "Rebase paused — N file(s) have conflicts. Resolving one at a time. Type 'abort' at any point to cancel."
3. Tell the user: "Let me read all N files upfront to give you clear recommendations."
4. Use the Read tool to read **all conflicting files at once** (batch them in a single tool call).
5. Write a **general summary**: identify any common pattern across all files (e.g. "All 4 conflicts follow the same pattern: master added X, our branch added Y — both need to be kept"). If there is no common pattern, briefly describe each file's situation.

### Step 4b — Per-file guided loop

For each conflicting file, in order:

1. **Open with a short analysis reminder** — print a one-line summary recapping the general pattern or this file's specific situation from Step 4a (e.g. "All 4 conflicts follow the same pattern: master added X, our branch added Y — keep both in each file."). This keeps context visible as earlier output scrolls away.

2. **Classify the conflict type** by inspecting `git status --short` output for that file:
   - `UU` — both sides edited (content conflict)
   - `DU` / `UD` — deleted on one side, modified on the other (structural conflict)
   - `AA` — both sides added the file (add/add conflict)

3. **Show the per-file analysis** (using what was already read in Step 4a — do NOT re-read):
   - State what each side changed (e.g. "HEAD added X, ours added Y").
   - Give a clear recommendation (e.g. "keep both", "keep theirs", etc.).
   - Show the conflicting section as-is using the standard conflict marker format (`<<<<<<<`, `=======`, `>>>>>>>`), containing only the conflicting lines — no surrounding context. Then separately show the recommended resolved version in a second fenced code block, with a heading that includes the strategy: "Recommended resolution (keep-both):", "Recommended resolution (keep-theirs):", "Recommended resolution (keep-ours):", or "Recommended resolution (custom):" as appropriate.
   - For structural conflicts: describe what happened (e.g. "This file was deleted on the base branch but you modified it locally").

4. **Present the resolution menu and wait for the user to choose** — do NOT proceed until the user replies. Always show (a)–(e); include (f) only when a recommendation was given:
   ```
   How do you want to resolve <file>?
   (a) Keep ours
   (b) Keep theirs
   (c) Keep both
   (d) Edit manually
   (e) Abort rebase
   (f) Apply recommendation — <one-line summary>   ← include only when a recommendation was given
   ```

5. **Execute the chosen strategy** — options (a), (b), (c), (f) use Bash only (no Edit tool); option (d) uses the Edit tool (see Step 4c):
   - **(a) Keep ours** — show what "ours" looks like (the `<<<<<<< HEAD` side), ask the user to confirm ("Type 'yes' to apply or 'abort' to cancel"), then run `git checkout --ours <file>` and `git add <file>` via Bash, and move to the next conflicting file.
   - **(b) Keep theirs** — show what "theirs" looks like (the `=======` → `>>>>>>>` side), ask the user to confirm ("Type 'yes' to apply or 'abort' to cancel"), then run `git checkout --theirs <file>` and `git add <file>` via Bash, and move to the next conflicting file.
   - **(c) Keep both** — show the resolved snippet (both sides, no conflict markers) in a fenced code block. Then apply via Bash (do NOT use the Edit tool):
     1. Run `python3 ~/.claude/skills/git-rebase/scripts/resolve-conflict.py --help` to confirm the interface, then:
        `python3 ~/.claude/skills/git-rebase/scripts/resolve-conflict.py --file <file> --strategy keep-both`
     2. Run `git diff --check <file>` — if markers remain, report line numbers and ask the user to fix manually, then re-verify.
     3. If clean: run `git add <file>` and move to the next conflicting file.
   - **(d) Edit manually** — follow Step 4c below, then move to the next conflicting file.
   - **(e) Abort rebase** — run `git rebase --abort` and stop.
   - **(f) Apply recommendation** — show the recommended resolved snippet in a fenced code block. Then apply via Bash (do NOT use the Edit tool). Two sub-cases:
     - **Simple "keep both" (recommended text = both sides concatenated verbatim):**
       `python3 ~/.claude/skills/git-rebase/scripts/resolve-conflict.py --file <file> --strategy keep-both`
     - **Custom resolution (recommended text differs from simple concatenation):** write the recommended text to a temp file, then call the script:
       ```
       python3 -c "open('/tmp/_conflict_res.txt','w').write('''<recommended text>''')"
       python3 ~/.claude/skills/git-rebase/scripts/resolve-conflict.py --file <file> --strategy custom --resolution-file /tmp/_conflict_res.txt
       ```
     After applying (either sub-case), run `git diff --check <file>` — if markers remain, report line numbers and ask the user to fix. If clean, run `git add <file>` and move to the next file.

### Step 4c — "Edit manually" flow

This flow is only for option **(d)**. The agent applies the suggested resolution via the Edit tool, which triggers the IDE diff viewer when an IDE is connected — letting the user review and adjust. If no IDE is connected, the agent tells the user to open the file in their editor instead.

1. If you haven't already shown a suggested resolved snippet in Step 4b, show one now in a fenced code block.
2. If running with IDE integration: use the Edit tool to apply the suggested resolution to the file (this opens the IDE diff viewer for the user to review/adjust).
   If running without IDE integration: tell the user "Open `<file>` in your editor, apply the resolution above, then save the file." and ask them to type 'done' when saved.
3. After the edit (whether by Edit tool or user), run `git diff --check <file>` to verify no conflict markers remain.
   - If markers remain: report the exact line numbers and ask the user to fix them. Do not attempt to re-apply the fix yourself. Repeat verification after the user confirms.
   - If clean: run `git add <file>` and proceed to the next conflicting file.

### Step 4d — Continue the rebase

After all conflicting files are resolved:
1. Run `git rebase --continue`.
2. If this triggers another conflict round (multi-commit rebase), repeat from Step 4a for the new set of conflicts, and announce which commit is now being applied.
3. If it succeeds, proceed to Step 5.

## Step 5 — Post-rebase summary

1. Show:
   - Current branch and base branch
   - Number of new commits integrated
   - One-line log of those commits (`git log ORIG_HEAD..HEAD --oneline`)

2. If a stash was used, run `git stash pop`:
   - If it exits non-zero or `git status` shows conflicts afterward, treat it as a conflict and apply the same per-file guided loop (Steps 4b/4c) for each conflicting file before declaring success.
   - Do not silently warn — actively guide the user through each conflict to resolution.
   - Once all stash conflicts are resolved, confirm the stash pop succeeded.

3. **Post-rebase verification** — After the summary (and stash pop if applicable), ask the user:
   ```
   Rebase complete. Want me to run a quick build/test check to catch semantic conflicts?
   (a) Yes — run build/tests
   (b) No — skip
   ```
   If the user chooses (a): **clean the build first** (e.g., `npm run clean`, `make clean`, `cargo clean`, etc.), then run the project's build/test command (check for `package.json` scripts, `Makefile`, `Cargo.toml`, `pyproject.toml`, etc.) and report pass/fail. If tests fail, show the relevant errors and ask the user how to proceed.
   If the user chooses (b): note — "A clean rebase does not guarantee semantic correctness; it only means git resolved textual conflicts. Consider running your test suite manually before pushing."
