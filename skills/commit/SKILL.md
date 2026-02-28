---
name: commit
description: Create well-formatted git commits using conventional commit messages. Use when asked to stage changes, analyze diffs, split work into multiple commits, or craft a conventional commit message for a repository.
---

# Git Conventional Commit

## Goal

Create accurate, scoped commits with concise conventional messages.

## Workflow

1. Determine commit scope before staging.
- If a reviewed-file allowlist exists (for example from `review-team`), use it as the scope source of truth.

2. Stage only in-scope files.
- Prefer explicit path staging (`git add <path> ...`).
- If out-of-scope files are already staged, unstage them before continuing.
- Use blanket staging only when the user explicitly asks to commit all current changes.

3. Analyze what will be committed.
- Use `git diff --cached` for message drafting and scope verification.
- If unstaged changes exist, inspect them separately and keep them out of this commit unless requested.

4. Split when needed.
- Split by logical unit when changes are unrelated, cross-type (code/docs/tests), or too large for a clear review.

5. Commit with conventional format.
- Format: `<type>: <description>`.
- Types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `chore`.
- Rules: imperative mood, first line under 72 chars, no scopes, no trailer lines.

## Command Guardrails

- Use `git commit -m "<subject>"` (optional second `-m` for body).
- Do not use heredocs for commit messages.

## Output

- State what was committed (scope summary).
- Show final commit message used.
- If any changes were intentionally excluded, state why.
