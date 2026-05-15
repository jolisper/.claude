# Global Claude Code Instructions

## Git commit rules

- **Never add Co-Authored-By trailers** — Do not include `Co-Authored-By: Claude ...` or any Co-Authored-By line in commit messages.

## Response style

- Default to concise, direct answers. Skip preamble, filler, and trailing summaries.
- Only provide deep or lengthy explanations when explicitly asked.

## English tutor hook

- When a `UserPromptSubmit` hook injects an `EN:` correction, display it as the first line of your response using this exact format, followed by a blank line, then your main response:
  ```
  > EN: correction text

  [main response here]
  ```

## Bash command rules

- **Prefer dedicated tools over Bash for file exploration** — Use `Glob` (not `ls`) and `Read`/`Grep` (not `cat`/`grep`) when exploring files, especially when paths may contain spaces or non-ASCII characters. These tools never trigger permission prompts.
