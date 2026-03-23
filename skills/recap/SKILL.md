---
name: recap
description: Print a quick recap of the current session — what was done, decided, and where things stand. Invoke after long sessions, interruptions, or context compaction.
disable-model-invocation: false
argument-hint: "optional focus topic (e.g. 'what changed in auth')"
allowed-tools: Bash(git:*)
---

You are producing a concise session recap to help the user re-orient after an interruption.

## Parameters

The user may invoke this skill with an optional focus argument, e.g. `/recap what changed in the auth flow`.

- If a focus question or topic is provided (via `$ARGUMENTS`), treat it as the lens for the recap: surface only the parts of the session relevant to that topic, and answer the question directly in **Current state** if applicable.
- If no argument is provided, produce a general recap of the full session.

## Protocol

### Step 1 — Gather git context (if applicable)

Run `git status --short` and `git log --oneline -5` (separately).

- If the working directory is not a git repo, skip silently.
- Note any uncommitted changes or recent commits relevant to this session.

### Step 2 — Synthesize the recap

Review the full conversation history. Write a concise recap that covers:

- What was being worked on
- Key changes, decisions, or outcomes
- Where things stand (what's left, what's done, relevant git state)

Use whatever structure best fits the session — prose, bullets, sections, or a mix. Adapt length to complexity: a short session warrants a short recap. If a focus argument was provided, shape the recap around it.

Start with `## Recap`. Do not add preamble or a trailing summary.
