---
name: run-tests
description: >
  Use when the user asks to run, execute, or check tests. Detects the project
  type, cleans build artifacts, and runs the test suite.
disable-model-invocation: true
allowed-tools: Bash(bun:*) Bash(pnpm:*) Bash(yarn:*) Bash(npm:*) Bash(cargo:*) Bash(go:*) Bash(mvn:*) Bash(gradle:*) Bash(pytest:*) Bash(mix:*) Bash(bundle:*) Bash(dotnet:*) Bash(make:*) Bash(bash:*) Read Glob
---

Run tests for the current project, cleaning build artifacts first. Follow this protocol:

**Important**: Never use `cd`, `git -C`, `&&`, or `||`. Run each command separately with no path arguments — rely on the shell's current working directory.

## Step 1 — Detect project type

Check for the following marker files in the current directory, in this priority order:

| Marker file(s) | Stack | Package manager |
|---|---|---|
| `bun.lockb` | Node.js | bun |
| `pnpm-lock.yaml` | Node.js | pnpm |
| `yarn.lock` | Node.js | yarn |
| `package.json` | Node.js | npm (fallback) |
| `Cargo.toml` | Rust | cargo |
| `go.mod` | Go | go |
| `pom.xml` | Java/Maven | mvn |
| `build.gradle` or `build.gradle.kts` | Java/Kotlin/Gradle | gradlew or gradle |
| `pyproject.toml`, `setup.py`, `pytest.ini`, or `setup.cfg` | Python | pytest |
| `mix.exs` | Elixir | mix |
| `Gemfile` | Ruby | bundle exec rspec |
| `*.sln` or `*.csproj` | .NET | dotnet |
| `Makefile` | Generic | make |

If no marker file is found, report clearly that the project type could not be detected and stop.

Announce which stack was detected before proceeding.

## Step 2 — Check for custom test script

**Node.js**: Read `package.json` and check for a `"test"` script under `"scripts"`. If it is absent, warn the user that no test script is defined and stop.

**Makefile**: Verify that both `clean` and `test` targets exist in the Makefile before running either. If a target is missing, warn the user and skip that step (skip clean if `clean` is missing; stop if `test` is missing).

## Step 3 — Clean

Run the appropriate clean command for the detected stack. Show the exact command before running it.

| Stack | Clean command |
|---|---|
| Node/bun | Check `package.json` for a `"clean"` script — run it if present; otherwise skip silently |
| Node/pnpm | Check `package.json` for a `"clean"` script — run it if present; otherwise skip silently |
| Node/yarn | Check `package.json` for a `"clean"` script — run it if present; otherwise skip silently |
| Node/npm | Check `package.json` for a `"clean"` script — run it if present; otherwise skip silently |
| Rust | `cargo clean` |
| Go | `go clean -testcache` |
| Maven | `mvn clean` |
| Gradle | `./gradlew clean` (fall back to `gradle clean` if `gradlew` is not present) |
| Python | `bash ~/.claude/skills/run-tests/scripts/python-clean.sh` |
| Elixir | `mix clean` |
| Ruby | *(no standard clean — skip silently)* |
| .NET | `dotnet clean` |
| Makefile | `make clean` (only if target exists — see Step 2) |

If clean fails, warn the user and ask whether to proceed with tests anyway or abort. Wait for their response before continuing.

## Step 4 — Run tests

Run the appropriate test command for the detected stack. Show the exact command before running it. Stream and display the full output — do not suppress or truncate any output.

| Stack | Test command |
|---|---|
| Node/bun | `bun test` |
| Node/pnpm | `pnpm test` |
| Node/yarn | `yarn test` |
| Node/npm | `npm test` |
| Rust | `cargo test` |
| Go | `go test ./...` |
| Maven | `mvn test` |
| Gradle | `./gradlew test` (fall back to `gradle test` if `gradlew` is not present) |
| Python | `pytest` |
| Elixir | `mix test` |
| Ruby | `bundle exec rspec` |
| .NET | `dotnet test` |
| Makefile | `make test` |

## Step 5 — Report result

Based on the exit code and output:

- **Passed**: Show a summary including test count and elapsed time if the output includes them.
- **Failed**: Show which tests failed and their full failure output. Do not hide or truncate any failures.
- **Error (non-test failure)**: Show stderr and explain the likely cause (missing dependencies, compilation error, misconfiguration, etc.).
