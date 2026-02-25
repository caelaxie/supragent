---
name: commit
description: Create well-formatted git commits using conventional commit messages. Use when asked to stage changes, analyze diffs, split work into multiple commits, or craft a conventional commit message for a repository.
---

# Git Conventional Commit

## Overview

Stage changes, analyze diffs, optionally split work into multiple commits, and create concise conventional commit messages without scopes or trailer lines.

## Workflow

1. **Stage files**
   - If nothing is staged, auto-stage all modified/new files with `git add`.

2. **Analyze changes**
   - Run `git diff` to understand what is being committed and ensure the message reflects the changes.

3. **Split if needed**
   - If multiple distinct logical changes are detected, suggest separate commits.

4. **Create commit**
   - Generate a concise conventional commit message and commit the staged changes.

## Commit Message Format

Use `<type>: <description>` with one of:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Formatting only (no logic change)
- `refactor`: Code restructuring
- `perf`: Performance improvement
- `test`: Adding/fixing tests
- `chore`: Build, tooling, dependencies

Rules:
- Present tense, imperative mood (e.g., "add" not "added").
- First line under 72 characters.
- Be specific about what changed.
- Do not include scopes in parentheses.
- Do not add trailer lines (Co-Authored-By, Signed-off-by, etc.).

## When to Split Commits

Split when changes involve:
- Unrelated parts of the codebase
- Different types (feature vs docs vs tests)
- Large changes that are clearer separated

## Examples

Single commits:
```
feat: add user authentication system
fix: resolve memory leak in rendering process
docs: update API documentation with new endpoints
refactor: simplify error handling in parser
chore: update package.json dependencies
```

Split commit scenario:
```
feat: add solc version type definitions
docs: update documentation for new solc versions
test: add unit tests for solc version features
chore: update dependencies
```

## Technical Implementation

Do not use heredocs for commit messages; they fail in sandboxed environments. Use:
```bash
git commit -m "feat: add user authentication"
git commit -m "feat: add user authentication" -m "Adds login, logout, and session management."
```

Avoid:
```bash
git commit -m "$(cat <<'EOF'
message here
EOF
)"
```

## Notes

- Already-staged files are committed as-is; unstaged changes trigger auto-staging.
- When splitting, help stage and commit each change separately.
