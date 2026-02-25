---
name: pr
description: Create or update GitHub pull requests for the current branch using the gh CLI. Use when asked to open, draft, or refresh a PR, or to generate a PR title/body from git diff/log context.
---

# PR

## Overview

Create or update a pull request for the current branch with a consistent title/body format derived from git context and the diff.

## Workflow

### 1. Determine base branch

Run:
```
git rev-parse --abbrev-ref --symbolic-full-name @{u} 2>/dev/null || echo main
```

Use the result as `BASE` in subsequent commands.

### 2. Gather context (run in parallel)

```
git log --oneline BASE..HEAD
git diff --stat BASE...HEAD
gh pr view --json number,title,body 2>/dev/null
```

If `gh pr view` returns data, the PR already exists.

### 3. Inspect changes

- If the diff stat is under ~500 lines, run: `git diff BASE...HEAD`
- If larger, read the changed files directly to capture key changes and file:line references.

### 4. Draft PR title and body

Guidelines:
- **Title**: `type: description` (feat, fix, refactor, chore, docs, test)
- **Summary**: 1–3 sentences explaining what changed and why
- **Key Changes**: 5–8 bullets with `file:line` references; use `[new]`, `[removed]`, `[refactored]` where applicable
- **Style**: present tense, direct language, no fluff

Body format:
```
## Summary

<1-3 sentences>

## Key Changes

<bullets with file:line references>
```

### 5. Create or update the PR

- If no PR exists:
  - Push the branch if needed: `git push -u origin HEAD`
  - Create: `gh pr create --title "<title>" --body "<body>"`
- If a PR exists:
  - Update: `gh pr edit --title "<title>" --body "<body>"`

### 6. Output result

- Show the PR URL
- Briefly state whether it was created or updated

## Example

Title:
```
feat: add device-based authentication
```

Body:
```
## Summary

Add device ID authentication flow for mobile clients, enabling secure login without user credentials.

## Key Changes

- [new] Device ID validation logic (src/auth/device.ts:45)
- [new] Mobile client configuration (src/config/clients.ts:12)
- Update token validator to accept device tokens (src/auth/validator.ts:89)
- [new] Test cases for device flow (src/auth/__tests__/device.test.ts:1)
```
