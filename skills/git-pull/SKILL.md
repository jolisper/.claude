---
name: git-pull
description: Pull remote changes with guided merge conflict resolution
disable-model-invocation: false
allowed-tools: Bash(git status:*) Bash(git rev-parse:*) Bash(git log:*) Bash(git pull:*) Bash(git stash:*) Bash(git diff:*) Bash(git checkout:*) Bash(git add:*) Bash(git merge:*) Bash(git commit:*) Bash(python3:*) Read Edit
---

Perform a `git pull` following this protocol:

**Important**: Never use `cd`, `git -C`, `&&`, or `||`. Run each command separately with no path arguments — rely on the shell's current working directory.

## Step 1 — Pre-flight check

Run each of these commands separately:

1. `git status`
2. `git rev-parse --abbrev-ref HEAD`
3. `git rev-parse --abbrev-ref --symbolic-full-name @{u}` — if this command fails (non-zero exit or error output), treat upstream as not set.
4. `git log @{u}..HEAD --oneline` — if this command fails, skip and continue.

## Step 2 — Handle dirty working tree

If `git status` shows uncommitted changes (modified, staged, or untracked files that would conflict):
- Tell the user what changed and ask whether to: (a) stash changes and pull, (b) commit changes first, or (c) abort.
- If the user chooses stash: run `git stash`, then pull. The stash pop happens in Step 5 with proper conflict handling.
- Do not pull silently over a dirty tree.

## Step 3 — Pull

Run `git pull` and capture the full output.

## Step 4 — Interpret the result

Report exactly one of these outcomes:

- **Already up to date** — say so and show current branch + upstream.
- **Fast-forward or merge** — show new commits pulled: `git log ORIG_HEAD..HEAD --oneline`
- **Merge conflict** — follow the guided conflict flow below (Steps 4a–4d).
- **No upstream set** — explain the error and suggest: `git branch --set-upstream-to=origin/<branch> <branch>`
- **Auth / network error** — show the error message and suggest checking SSH keys or credentials.
- **Other error** — show stderr and explain the likely cause.

### Step 4a — Announce conflict summary and upfront analysis

When `git pull` exits with a conflict:
1. Run `git diff --name-only --diff-filter=U` to get the list of conflicting files.
2. Announce: "Merge paused — N file(s) have conflicts. Resolving one at a time. Type 'abort' at any point to cancel."
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
   (e) Abort merge
   (f) Apply recommendation — <one-line summary>   ← include only when a recommendation was given
   ```

5. **Execute the chosen strategy** — options (a), (b), (c), (f) use Bash only (no Edit tool); option (d) uses the Edit tool (see Step 4c):
   - **(a) Keep ours** — show what "ours" looks like (the `<<<<<<< HEAD` side), ask the user to confirm ("Type 'yes' to apply or 'abort' to cancel"), then run `git checkout --ours <file>` and `git add <file>` via Bash, and move to the next conflicting file.
   - **(b) Keep theirs** — show what "theirs" looks like (the `=======` → `>>>>>>>` side), ask the user to confirm ("Type 'yes' to apply or 'abort' to cancel"), then run `git checkout --theirs <file>` and `git add <file>` via Bash, and move to the next conflicting file.
   - **(c) Keep both** — show the resolved snippet (both sides, no conflict markers) in a fenced code block. Then apply via Bash (do NOT use the Edit tool):
     1. Strip conflict markers keeping both sides:
        ```
        python3 -c "
        import re, sys; f=sys.argv[1]; c=open(f).read()
        c=re.sub(r'^<{7}[^\n]*\n','',c,flags=re.MULTILINE)
        c=re.sub(r'^={7}\n','',c,flags=re.MULTILINE)
        c=re.sub(r'^>{7}[^\n]*\n','',c,flags=re.MULTILINE)
        open(f,'w').write(c)
        " <file>
        ```
     2. Run `git diff --check <file>` — if markers remain, report line numbers and ask the user to fix manually, then re-verify.
     3. If clean: run `git add <file>` and move to the next conflicting file.
   - **(d) Edit manually** — follow Step 4c below, then move to the next conflicting file.
   - **(e) Abort merge** — run `git merge --abort` and stop.
   - **(f) Apply recommendation** — show the recommended resolved snippet in a fenced code block. Then apply via Bash (do NOT use the Edit tool, even if the strip approach won't produce the right result). Two sub-cases:
     - **Simple "keep both" (recommended text = both sides concatenated verbatim):** use the same python3 strip command from option (c).
     - **Custom resolution (recommended text differs from simple concatenation):** write the recommended text to a temp file, then use python3 to replace the conflict block:
       ```
       python3 -c "
       import re, sys
       f = sys.argv[1]; r = sys.argv[2]
       c = open(f).read(); replacement = open(r).read()
       c = re.sub(r'<{7}[^\n]*\n.*?>{7}[^\n]*\n', replacement, c, count=1, flags=re.DOTALL)
       open(f, 'w').write(c)
       " <file> /tmp/_conflict_resolution.txt
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

### Step 4d — Complete the merge

After all conflicting files are resolved:
1. Run `git commit` (git uses the auto-generated merge commit message).
2. If it succeeds, proceed to Step 5.

## Step 5 — Post-pull summary

1. If commits were pulled, show:
   - Current branch and upstream
   - Number of new commits
   - One-line log of those commits (`git log ORIG_HEAD..HEAD --oneline`)

2. If a stash was used, run `git stash pop`:
   - If it exits non-zero or `git status` shows conflicts afterward, treat it as a conflict and apply the same per-file guided loop (Steps 4b/4c) for each conflicting file before declaring success.
   - Do not silently warn — actively guide the user through each conflict to resolution.
   - Once all stash conflicts are resolved, confirm the stash pop succeeded.

3. **Post-pull verification** — After the summary (and stash pop if applicable), ask the user:
   ```
   Pull complete. Want me to run a quick build/test check to catch semantic conflicts?
   (a) Yes — run build/tests
   (b) No — skip
   ```
   If the user chooses (a): **clean the build first** (e.g., `npm run clean`, `make clean`, `cargo clean`, etc.), then run the project's build/test command (check for `package.json` scripts, `Makefile`, `Cargo.toml`, `pyproject.toml`, etc.) and report pass/fail. If tests fail, show the relevant errors and ask the user how to proceed.
