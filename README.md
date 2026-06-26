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
| `1password-cli` | Secure secret access via 1Password CLI (`op`) for reading, injecting, and templating secrets. |
| `bitwarden-cli` | Bitwarden CLI (`bw`) workflows for vault auth, session management, and secret retrieval. |
| `commit` | Fallback commit workflow using conventional messages when a project has no commit-specific guidance. |
| `d2lang` | Supports D2 diagram creation, refactoring, validation, and export workflows. |
| `hermes-plugin-development` | Guides Hermes plugin authoring and validation across manifests, registration, tools, hooks, and enablement. |
| `modified-karpathy-guidelines` | Provides coding guidance to reduce overcomplication and improve code quality. |
| `model-detector` | Finds exact model IDs for Oh My Pi (OMP), Codex, OpenCode, APIs, and extensible coding-agent runners from first-party runtime evidence, config, logs, and request or response fields. |
| `pr` | Fallback GitHub pull-request workflow when a project has no PR-specific guidance; self-assigns unassigned PRs by default. |
| `review-team` | Coordinates parallel review roles for evidence-based, severity-ranked findings and fixes. |
| `rust-guidelines` | Rust coding, review, test, Cargo, and API guidance with focused local references and official-doc fallback for uncovered details. |
| `sql-antipatterns` | Audits PostgreSQL designs for anti-patterns and recommends constraint-first alternatives. |
| `stash-override-rules` | Helps author, merge, and validate Stash VPN override rules and routing behavior. |
