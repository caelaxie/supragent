---
name: pr
description: Fallback GitHub pull-request creation/update workflow using the gh CLI. Use only when the current project does not define PR-specific guidelines, templates, or commands.
---

# PR

## Goal

When the current project has no PR-specific guidance, create or update a PR with a base branch, title, body, and default self-assignment when the PR has no assignee.

## Fallback Scope

Use this skill only as fallback PR guidance, whether it is installed globally or locally. Before following this workflow, check the current project for files that define PR-specific instructions, such as `AGENTS.md`, `CONTRIBUTING.md`, `README.md`, `.github/pull_request_template.md`, or other local docs referenced by the project.

If the current project defines PR guidelines, templates, required sections, title/body conventions, review conventions, or create/update commands, disregard this skill and follow the project-local guidance instead. Do not merge this skill's default title format, body sections, or commands into a project-defined PR process.

Do not treat the mere existence of a file as project PR guidance; defer only when the file actually prescribes PR behavior.

## Workflow

1. Resolve PR state and base branch.
- Run:
```bash
gh pr view --json number,baseRefName,title,body,assignees 2>/dev/null
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
gh pr view --json number,title,body,baseRefName,assignees 2>/dev/null
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
- Default assignment:
  - New PRs: assign yourself with `--assignee "@me"`.
  - Existing PRs: check `assignees`; if none are present, add yourself with `--add-assignee "@me"`.
- Create:
```bash
git push -u origin HEAD
gh pr create --base "<BASE>" --title "<title>" --body "<body>" --assignee "@me"
```
- Update:
```bash
ASSIGNEE_ARGS=()
if [ "$(gh pr view --json assignees --jq '.assignees | length')" = "0" ]; then
  ASSIGNEE_ARGS=(--add-assignee "@me")
fi
gh pr edit --base "<BASE>" --title "<title>" --body "<body>" "${ASSIGNEE_ARGS[@]}"
```

## Guardrails

- Keep analysis diff and PR `--base` aligned.
- If branch has uncommitted changes, note they are not part of the PR.
- This skill is independent of `review-team`; do not add review-report sections.
- If a request also requires `review-team`, run in a separate flow/turn. Do not co-trigger or merge output contracts.

## Output

- PR URL.
- Whether PR was created or updated.
