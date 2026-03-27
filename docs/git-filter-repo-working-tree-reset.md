# git filter-repo: Working Tree Reset Behavior — What Gets Destroyed and Why

## The Core Behavior That Bites You

`git filter-repo` does NOT operate only on git history. After rewriting commits,
it performs a hard reset of the working tree to match the new HEAD. This means:

1. **Uncommitted edits to tracked files are silently overwritten.**
2. **Previously-tracked files removed from history are deleted from disk.**

There is no warning. There is no stash. It just happens.

---

## Case 1: Uncommitted Edit to .gitignore Was Lost

### What happened

1. `.gitignore` was edited in the working tree (not staged, not committed).
2. `git filter-repo --invert-paths --force` was run immediately after.
3. `git filter-repo` rewrote the commits, then reset the working tree to match
   the new HEAD.
4. Because `.gitignore` is a tracked file, the reset restored it to the HEAD
   version — the pre-edit version.
5. The working tree edit was gone. No error. No diff. Just gone.

### Why it happens

`git filter-repo` internally runs something equivalent to:

```
git read-tree -u --reset HEAD
```

after rewriting history. This forcibly updates all tracked files in the working
tree to match the new HEAD. Uncommitted modifications to tracked files are
clobbered without mercy.

### How to prevent it

**Always commit (or at least stage) every change before running git filter-repo.**
Even a WIP commit is fine — you can amend or squash it afterward.

```bash
git add .gitignore
git commit -m "wip: update gitignore before history rewrite"
# THEN run filter-repo
git filter-repo ...
```

---

## Case 2: The CSV Files Were Deleted From Disk

### What happened

1. The subset CSVs were tracked in git (committed in history).
2. `git filter-repo --invert-paths` removed them from all commits.
3. After rewriting history, filter-repo reset the working tree to match the new
   HEAD — which no longer contains the CSVs.
4. Because the files were tracked (and the new HEAD has no record of them),
   the working tree reset deleted them from disk.
5. The `subset/` directory itself also vanished (no files = no directory).

### Why it happens

This is intentional behavior by design. From filter-repo's perspective, if a
file doesn't exist in the rewritten history, it has no business being in the
working tree either. The reset is meant to produce a clean, consistent state.

The problem is that the files may still be needed locally even if they
shouldn't be in git history (e.g., large data files used by tests).

### How to prevent it

Back up the files before running filter-repo.

```bash
cp -r docs/specs/securities-conciliation/data/subset/ /tmp/subset-backup/
git filter-repo --invert-paths ...
cp -r /tmp/subset-backup/ docs/specs/securities-conciliation/data/subset/
```

Or use `--partial` flag to prevent the working tree reset entirely:

```bash
git filter-repo --invert-paths --path <file> --partial
```

With `--partial`, filter-repo skips the working tree reset. WARNING: this also
skips updating refs and other cleanup steps — only use if you know what you're
doing and will handle refs manually.

---

## The Correct Order of Operations (for next time)

1. Back up any files you want to keep locally but remove from history.
2. Commit all staged/unstaged changes you want in the new history.
3. Run `git filter-repo`.
4. Restore backed-up files to disk (they will be untracked, per `.gitignore`).
5. Re-add the remote: `git remote add origin <url>` (filter-repo removes it).
6. Force-push when ready.

---

## The Remote Removal

`git filter-repo` also removes the `origin` remote as a safety mechanism to
prevent accidental pushes of rewritten history. This is not data loss but it
will break scripts and tools that expect `origin` to exist. Re-add it with:

```bash
git remote add origin git@bitbucket.org:<workspace>/<repo>.git
```
