---
name: commit
description: Fallback git commit workflow using conventional commit messages. Use only when the current project does not define commit-specific guidelines, message formats, staging rules, or commands.
---

# Git Conventional Commit

## Goal

When the current project has no commit-specific guidance, create accurate, scoped commits with concise conventional messages.

## Fallback Scope

Use this skill only as fallback commit guidance, whether it is installed globally or locally. Before following this workflow, check the current project for files that define commit-specific instructions, such as `AGENTS.md`, `CONTRIBUTING.md`, `README.md`, `.gitmessage`, `.github` docs, or other local docs referenced by the project.

If the current project defines commit guidelines, message formats, trailer requirements, signing requirements, staging rules, branch policies, or commit commands, disregard this skill and follow the project-local guidance instead. Do not merge this skill's conventional message format, staging defaults, split rules, or command guardrails into a project-defined commit process.

Do not treat the mere existence of a file as project commit guidance; defer only when the file actually prescribes commit behavior.

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
