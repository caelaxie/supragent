---
name: codeberg-cli
description: Use Codeberg CLI (`cb`, package `codeberg-cli`) to authenticate, manage Codeberg or Forgejo repos, issues, PRs, releases, Actions, notifications, labels, milestones, and raw API calls. Use when Codex needs to interact with Codeberg/Forgejo from the terminal, log in with a PAT, create or review PRs on Codeberg, open issues, cut releases, dispatch workflows, or troubleshoot `cb` auth and repo resolution.
---

# Codeberg CLI

## Goal

Use `cb` (Python package `codeberg-cli`) for Codeberg/Forgejo forge operations from the terminal without leaking PATs, without confusing this with GitHub `gh`, and without falling back to Forgejo's unrelated `fj`/`tea` CLIs.

## Workflow

1. Verify install and package identity.

```bash
which cb
cb --version
```

- Expected identity: `cb 0.5.x` (or newer) from PyPI package `codeberg-cli` (homepage `https://codeberg.org/ThatXliner/codeberg-cli`).
- Install if missing: `uv tool install codeberg-cli` (preferred) or `pip install codeberg-cli`.
- Package requires Python `>=3.12`.
- Do not document or use Homebrew's deprecated Rust `codeberg-cli`, Forgejo `fj`/`forgejo-cli`, or Gitea `tea`. If `cb --version` is missing or the binary is not `codeberg-cli`, install the correct package above.

2. Check auth state first.

```bash
cb auth status
cb auth whoami
```

- `auth status` prints login identity or `Not logged in`.
- `auth whoami` prints username only.
- If not logged in: obtain a PAT from `https://codeberg.org/user/settings/applications` (or `<base-url>/user/settings/applications` for self-hosted Forgejo), then:

```bash
cb auth login --token "$CODEBERG_TOKEN"
```

- Prefer env-var / secret-manager injection over pasting the token into chat or shell history. Interactive `cb auth login` (prompt) is fine only when the user is present.
- `cb auth login` validates via `GET /user`, then writes `token` into the config file.
- Config path is platformdirs `user_config_path("codeberg-cli")/config.toml`:
  - macOS: `~/Library/Application Support/codeberg-cli/config.toml`
  - Linux: `~/.config/codeberg-cli/config.toml` (typical)
- Discover path with `cb config path`. Never `cat`/print the token from config; never run `cb config get token` in agent output.

3. Set base URL for self-hosted Forgejo when needed.

- Global cascading option: `--base-url` / `-b` (default `https://codeberg.org`).
- Place global flags **before** the subcommand:

```bash
cb --base-url https://forge.example.com auth status
cb -b https://forge.example.com repo list
```

- Client normalizes: adds `https://` if missing, appends `/api/v1` for API calls, strips a trailing `/api/v1` for web URLs.
- Persist with `cb config set base_url https://forge.example.com` when the user wants a durable non-Codeberg default. Confirm with `cb config get base_url`.
- Do not invent a host; default is Codeberg unless the user or remotes clearly point elsewhere.

4. Prefer machine-readable output for agent parsing.

- Global flag `--json` / `-j` must also precede the subcommand:

```bash
cb --json repo list --limit 20
cb -j issue list --state open
```

- Prefer `--json` when the agent will parse results. Human tables are fine for user-facing summaries.
- Do **not** put `--json` after the subcommand (`cb repo list --json` fails with `Unknown option '--json'` on 0.5.0).
- For discovery of unknown flags, use `cb --help=plain` or subcommand `--help`.

5. Resolve the target repo deliberately.

- Most `issue` / `pr` / `release` / `actions` / `label` / `milestone` / `repo` mutators accept `--repo owner/name`.
- When omitted, `cb` infers `owner/repo` from `git remote get-url origin` (HTTPS or SSH).
- If not in a git repo or origin is unparsable, pass `--repo` explicitly.
- Prefer explicit `--repo` when multiple remotes exist or origin is not Codeberg/Forgejo.

6. Always run create/comment flows non-interactively.

- Several create/comment commands prompt for title/body/message when flags are omitted (`issue create`, `pr create`, `issue comment`, `pr comment`, `repo create` name).
- Always pass the full flag set for agent runs so the command never blocks on `input()`:

```bash
cb issue create --title "..." --body "..." --repo owner/repo
cb pr create --title "..." --body "..." --base main --head my-branch --repo owner/repo
cb issue comment 12 --message "..." --repo owner/repo
cb pr comment 3 --message "..." --repo owner/repo
```

7. Use common read workflows.

```bash
cb repo list --limit 30
cb repo list --owner someorg
cb repo view --repo owner/repo
cb repo search "query" --limit 20
cb issue list --state open --repo owner/repo
cb issue view 12 --repo owner/repo
cb pr list --state open --repo owner/repo
cb pr view 3 --repo owner/repo
cb pr status 3 --repo owner/repo
cb pr diff 3 --repo owner/repo
cb pr files 3 --repo owner/repo
cb release list --repo owner/repo
cb actions workflows --repo owner/repo
cb actions runs --repo owner/repo --limit 20
cb notify list --limit 30
cb org list
cb user
```

8. Use common write workflows only when requested.

```bash
# Repo
cb repo create --name my-repo --description "..." --private
cb repo create --name my-repo --org my-org --remote
cb repo clone owner/repo
cb repo fork --repo owner/repo
cb repo branch list --repo owner/repo
cb repo tag create v1.0.0 --message "release" --repo owner/repo

# Issue
cb issue create --title "..." --body "..." --labels "bug,help wanted" --repo owner/repo
cb issue close 12 --repo owner/repo
cb issue reopen 12 --repo owner/repo
cb issue edit 12 --title "..." --body "..." --repo owner/repo
cb issue comment 12 --message "..." --repo owner/repo

# PR
cb pr create --title "..." --body "..." --base main --head feature --repo owner/repo
cb pr checkout 3 --repo owner/repo   # alias: cb pr co 3
cb pr review 3 --approve --body "LGTM" --repo owner/repo
cb pr review 3 --request-changes --body "..." --repo owner/repo
cb pr review 3 --comment --body "..." --repo owner/repo
cb pr merge 3 --style squash --repo owner/repo   # style: merge|rebase|squash
cb pr close 3 --repo owner/repo
cb pr update 3 --style merge --repo owner/repo

# Release
cb release create v1.2.0 --title "v1.2.0" --notes "..." --repo owner/repo
cb release upload <id> ./dist/artifact.tar.gz --repo owner/repo

# Actions
cb actions dispatch ci.yml --ref main --repo owner/repo
```

- `pr review` requires exactly one of `--approve` / `--request-changes` / `--comment`.
- Destructive ops that support `--yes` (e.g. `repo delete`, `release delete`, `milestone delete`) must only run with explicit user intent; pass `--yes` only after confirmation of the target.
- For PR creation, push the head branch first with git if it is not on the remote yet (git is separate from `cb`).

9. Escape hatch: raw API.

```bash
cb api GET /user
cb api GET /repos/owner/repo
cb api POST /repos/owner/repo/issues --data '{"title":"x","body":"y"}'
```

- Use when a needed Forgejo API surface has no dedicated subcommand.
- `--data` is a JSON string for POST/PATCH bodies.
- Paths are API-relative (client already prefixes `/api/v1`).

10. Log out only when asked.

```bash
cb auth logout
```

- Removes stored credentials. Do not log out as a side effect of ordinary reads/writes.

## Guardrails

- Never print PATs, `cb config get token` output, or config.toml token values.
- Prefer `cb` over hand-rolled `curl` against Codeberg when a subcommand exists.
- Do not use this skill for GitHub; GitHub stays on `gh` / the `pr` skill.
- Do not confuse with `fj`/`tea`; if the user has those, still prefer `cb` only when this skill is loaded for Codeberg/`codeberg-cli` tasks.
- Always pass non-interactive flags for create/comment flows.
- Put `--json` / `--base-url` before the subcommand.
- Infer repo from cwd only when origin is the intended Forgejo remote; otherwise `--repo owner/name`.
- For PR creation, push the head branch first with git if it is not on the remote yet.
- Scope destructive actions (`delete`, `merge`, `transfer`, `archive` edits) to explicit user requests.

## Troubleshooting

- `Not logged in. Run 'cb auth login' first.` → run auth login with a valid PAT.
- Wrong host / 404 on known repos → check `--base-url` / `cb config get base_url` and that the remote host matches.
- `No repo specified and not in a git directory` → pass `--repo owner/name`.
- Command hangs waiting for input → missing `--title`/`--body`/`--message`; re-run with flags.
- `--json` "Unknown option" on a subcommand → move flag to `cb --json <subcommand> ...`.
- `cb` missing → install `codeberg-cli` with `uv tool install codeberg-cli`.
- Token invalid → regenerate PAT at user settings/applications; re-login.
- Actions dispatch 404 → list with `cb actions workflows`; Actions may be disabled.

## Output

- Show exact commands run.
- State auth identity from `cb auth whoami` / `auth status`.
- State effective base URL when non-default.
- State whether `--repo` was explicit or inferred.
- State read-only vs mutating actions performed.
- Never include tokens.
