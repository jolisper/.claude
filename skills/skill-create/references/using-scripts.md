Source: https://agentskills.io/skill-creation/using-scripts
Fetch that URL for full details when in doubt.

## When to use a script

Use a `scripts/` file instead of inline commands when any of these apply:
- Commands include complex flag values with quotes, `%`-sequences, or special characters that can trigger agent safety checks
- The skill chains multiple commands with `&&`, `||`, or `echo "..."` separators
- The workflow involves a loop, conditional branching, or batch iteration
- Text processing (`grep`, `awk`, `sed`) with patterns that vary by user input
- Consistent, reproducible behavior is critical — removing variation from agent-constructed commands

One-off commands with a few plain flags don't need a script.

## Script design (agentic use)
- **No interactive prompts** — accept all input via flags, env vars, or stdin.
- **`--help` output** — document flags and examples; the agent reads this to learn the interface.
- **Helpful errors** — include what was expected and what to try next.
- **Structured output** — use `status=…` key=value lines or JSON on stdout; diagnostics to stderr.
- **Idempotency** — agents may retry; "create if not exists" is safer than "create and fail".
- **Predictable output size** — if output could be large, default to a summary and support `--offset`.

## Claude Code path caveat

The agentskills.io spec says to use relative paths (`scripts/foo.sh`), but **Claude Code runs commands from the current working directory, not the skill directory**. Relative paths will resolve to the wrong location.

The correct path depends on the skill's install scope — `create-skill` knows this from Phase 2 and should embed the right form:

**Global skill** (`~/.claude/skills/<name>/`): must use the hardcoded path — global skills can be invoked from any CWD, so `$(pwd)` is unreliable:
```bash
bash ~/.claude/skills/<skill-name>/scripts/<script>.sh
```

**Project-local skill** (`.claude/skills/<name>/`): project root is not known at creation time, but Claude Code runs with CWD = project root at invocation, so `$(pwd)` resolves correctly:
```bash
bash "$(pwd)/.claude/skills/<skill-name>/scripts/<script>.sh"
```
> Note: this assumes Claude Code is invoked from the project root. If run from a subdirectory, `$(pwd)` will resolve incorrectly — but there is no better option without knowing the project path at creation time.

## Frontmatter when scripts are used
Add `Bash(bash:*)` to `allowed-tools` so the agent can invoke scripts.

## Script template (bash)
```bash
#!/usr/bin/env bash
set -euo pipefail

# Usage: scripts/<name>.sh [--flag VALUE] ...

PARAM=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --param) PARAM="$2"; shift 2 ;;
    --help)
      echo "Usage: scripts/<name>.sh --param VALUE"
      echo "  Description of what the script does."
      exit 0 ;;
    *) echo "Error: unknown argument: $1" >&2; exit 1 ;;
  esac
done

if [[ -z "$PARAM" ]]; then
  echo "Error: --param is required." >&2
  exit 1
fi

# ... logic ...

echo "status=done result=$PARAM"
```
