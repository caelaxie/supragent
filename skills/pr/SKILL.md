---
name: pr
description: Create or update GitHub pull requests for the current branch using the gh CLI. Use when asked to open, draft, or refresh a PR, or to generate a PR title/body from git diff/log context.
---

# PR

## Goal

Create or update a PR with a base branch, title, and body that match the analyzed diff.

## Workflow

1. Resolve PR state and base branch.
- Run:
```bash
gh pr view --json number,baseRefName,title,body 2>/dev/null
gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name' 2>/dev/null || echo main
```
- Base precedence:
  - Existing PR: use `baseRefName`.
  - Otherwise use repo default branch.
  - Fallback to `main`.

2. Gather context (parallel).
```bash
git log --oneline BASE..HEAD
git diff --stat BASE...HEAD
gh pr view --json number,title,body,baseRefName 2>/dev/null
```

3. Inspect changes.
- If diff is moderate (<~500 lines), inspect full `git diff BASE...HEAD`.
- If large, inspect changed files directly and capture key file:line references.

4. Draft PR metadata.
- Title: `type: description` (`feat|fix|refactor|chore|docs|test`).
- Body sections:
  - `## Summary` (1-3 sentences)
  - `## Key Changes` (5-8 concrete bullets with file:line refs)

5. Create or update.
- Create:
```bash
git push -u origin HEAD
gh pr create --base "<BASE>" --title "<title>" --body "<body>"
```
- Update:
```bash
gh pr edit --base "<BASE>" --title "<title>" --body "<body>"
```

## Guardrails

- Keep analysis diff and PR `--base` aligned.
- If branch has uncommitted changes, note they are not part of the PR.
- This skill is independent of `review-team`; do not add review-report sections.
- If a request also requires `review-team`, run in a separate flow/turn. Do not co-trigger or merge output contracts.

## Output

- PR URL.
- Whether PR was created or updated.
