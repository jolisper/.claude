---
name: sdk
description: >
  Use this skill when you need to switch or install a specific SDK version for
  Java, Node, Gradle, Maven, Kotlin, or any other SDKMAN-managed candidate.
  Invoke when a build fails due to a wrong Java/SDK version, when the project
  requires a different environment than the current default, or when the user
  asks to change the Java, Node, or Gradle version. Accepts a candidate and
  version as arguments (e.g. "java 21.0.3-tem", "node 20.0.2-amzn"). Checks
  whether the candidate is already installed, offers to install it if not, then
  sets it as the system default via SDKMAN.
disable-model-invocation: false
argument-hint: "candidate version  (e.g. java 21.0.3-tem)"
allowed-tools: Bash(bash:*)
compatibility:
  - claude-code
---

## Available scripts

- `~/.claude/skills/sdk/scripts/sdk.sh` — checks, installs, and activates an SDKMAN candidate

## Step 1: Parse arguments

Read `$ARGUMENTS`. Split on whitespace: the first token is `CANDIDATE`; the remaining tokens joined form `VERSION`.

- If `$ARGUMENTS` is empty, ask: "Which SDK and version do you need? (e.g. `java 21.0.3-tem`, `node 20.0.2-amzn`)"
- If only a candidate is given with no version, set `VERSION=""` and proceed — Step 2 will list versions.

## Step 2: Check if the candidate is installed

If `VERSION` is non-empty, run:

```
bash ~/.claude/skills/sdk/scripts/sdk.sh --candidate <CANDIDATE> --version <VERSION>
```

Interpret the structured `status=…` output:

| status | meaning | next step |
|---|---|---|
| `ok` | already installed; set as default | Step 4 |
| `not-installed` | not present locally | Step 2b |
| any non-zero exit / no structured output | SDKMAN not found or unexpected error | report error and stop |

## Step 2b: Show available versions

Reached when `VERSION` is empty **or** when `status=not-installed`.

Run:

```
bash ~/.claude/skills/sdk/scripts/sdk.sh --candidate <CANDIDATE> --list-available <VERSION>
```

(Pass the partial version as the filter, e.g. `17` or `21`. If `VERSION` is empty, omit the filter.)

The script outputs matching identifiers sorted by reliability: Temurin (`tem`) first, then Corretto (`amzn`), Zulu (`zulu`), GraalVM Community (`graalce`), then others.

Present the list to the user:

```
Available <CANDIDATE> versions (most reliable first):
  1. <identifier>
  2. <identifier>
  ...

Which version would you like to install? (enter number or full identifier, or "cancel")
```

Wait for the user to pick one. Set `VERSION` to the chosen identifier and go directly to install — **skip the confirmation gate in Step 3**, the selection is already explicit consent.

## Step 3: Confirmation gate — install missing candidate

Only reached when `VERSION` was a full identifier supplied by the user (not chosen from the list) and it is not installed. Present:

```
`<CANDIDATE> <VERSION>` is not installed locally. Install it now via SDKMAN?
(a) Install
(b) Cancel
```

Wait for explicit approval. On (b), stop. On (a), run:

```
bash ~/.claude/skills/sdk/scripts/sdk.sh --candidate <CANDIDATE> --version <VERSION> --install
```

| status | meaning | next step |
|---|---|---|
| `installed` | installed and set as default | Step 4 |
| any non-zero exit | install failed | report stderr output and stop |

## Step 4: Report result

On success, report to the user:

```
SDK active: <CANDIDATE> <VERSION>
Home: <home value from script output>

Set as SDKMAN default. New shells will use this version automatically.
```

After reporting, run this single export so the variable persists for all subsequent Bash calls in this session:

```
export JAVA_HOME=<home>
```

That's it — one call, once. All subsequent commands (`mvn`, `gradle`, `java`, etc.) will inherit `JAVA_HOME` automatically. Do not repeat the export before each command.
