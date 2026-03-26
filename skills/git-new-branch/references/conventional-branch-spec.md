# Conventional Branch Spec — Reference

Source: https://conventional-branch.github.io/

## Branch types and aliases

| Menu label | Valid prefixes | Use for |
|---|---|---|
| feat | `feat/`, `feature/` | New functionality |
| fix | `fix/`, `bugfix/` | Bug corrections |
| hotfix | `hotfix/` | Critical urgent fixes |
| release | `release/` | Release preparation |
| chore | `chore/` | Non-code tasks (docs, deps, config) |

## Description rules

- Lowercase a–z, digits 0–9, hyphens only
- No consecutive hyphens (`--`)
- No leading or trailing hyphens
- Dots allowed only in `release/` descriptions (for version numbers)
- Should be concise and purpose-driven

## Optional ticket number inclusion

Ticket/issue numbers may be included at the start of the description:

```
feat/issue-123-add-login
bugfix/gh-456-fix-header-overflow
hotfix/JIRA-789-patch-auth-token
```

Pattern: `<ticket-prefix>-<number>-<short-description>`

## Examples by type

| Input intent | Good branch name |
|---|---|
| Add a login page | `feat/add-login-page` |
| Fix the header overflow bug | `bugfix/fix-header-overflow` |
| Fix issue #42 in the nav bar | `bugfix/issue-42-navbar-fix` |
| Patch a security vulnerability | `hotfix/security-patch` |
| Prepare version 1.2.0 | `release/v1.2.0` |
| Update dependencies | `chore/update-deps` |
| Add README docs | `chore/add-readme` |
| Refactor auth module | `feat/refactor-auth-module` |
| Fix the thing that crashes on login | `bugfix/fix-login-crash` |
| New dark mode toggle | `feat/dark-mode-toggle` |

## Colloquial → spec translation patterns

When the user gives informal input, apply these patterns:

- Strip filler words ("the", "a", "an", "that")
- Replace spaces with hyphens
- Lowercase everything
- Convert verbs to imperative form where natural ("fixing" → "fix", "adding" → "add")
- Drop vague words ("thing", "stuff", "some") — replace with the actual noun
- Preserve ticket numbers if mentioned
