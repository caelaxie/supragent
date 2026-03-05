# supragent

`supragent` is a compact repository of Codex skills for standardizing and accelerating common agent workflows.

## Install (Global by default)

Install all skills from this repository as globally available skills:

```bash
npx skills add <owner>/<repo> --global
```

Install a specific skill globally:

```bash
npx skills add <owner>/<repo> --global --skill <skill-name>
```

Use the same commands without `--global` when you want a local install.

## Skill Catalog

| Skill | Description |
|---|---|
| `commit` | Produces conventional commits, staged-change workflows, and commit message strategy support. |
| `d2lang` | Supports D2 diagram creation, refactoring, validation, and export workflows. |
| `modified-karpathy-guidelines` | Provides coding guidance to reduce overcomplication and improve code quality. |
| `pr` | Manages GitHub pull-request creation and updates using the `gh` CLI context. |
| `review-team` | Coordinates parallel review roles for evidence-based, severity-ranked findings and fixes. |
| `sql-antipatterns` | Audits PostgreSQL designs for anti-patterns and recommends constraint-first alternatives. |
| `stash-override-rules` | Helps author, merge, and validate Stash VPN override rules and routing behavior. |
