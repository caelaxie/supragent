---
name: bitwarden-cli
description: Use Bitwarden Password Manager CLI (`bw`) to authenticate, unlock a vault, manage `BW_SESSION`, configure cloud or self-hosted server settings, sync vault state, list or get vault objects, create or edit items with `bw get template`, `jq`, and `bw encode`, or safely lock and log out of terminal sessions. Use when Codex needs to work with Bitwarden vault data from the terminal or troubleshoot Bitwarden CLI auth, session, and object mutation behavior.
---

# Bitwarden CLI

## Goal

Use `bw` to access or mutate Bitwarden vault data safely from the terminal without leaking master passwords, API credentials, session keys, or vault contents.

## Workflow

1. Verify the CLI is installed and note the version in play.

```bash
bw --version
```

- If `bw` is missing, use Bitwarden's official CLI install docs.
- Use `bw update` only when the user explicitly wants to check for a newer CLI build.

2. Configure the correct server before authenticating.

```bash
bw config server
bw config server bitwarden.com
bw config server https://bw.company.com
bw status
```

- Use the correct cloud or self-hosted server before `bw login`.
- Confirm `serverUrl` with `bw status`.

3. Check current auth state before choosing the next step.

```bash
bw status
```

- `status` is one of `unauthenticated`, `locked`, or `unlocked`.
- `unauthenticated` means the user must log in.
- `locked` means the user is already logged in and only needs `bw unlock`.
- `unlocked` means a valid session key is already active for this shell or command.

4. Log in with the method that matches the user's environment.

```bash
bw login
bw login --sso
BW_CLIENTID=... BW_CLIENTSECRET=... bw login --apikey
```

- Prefer interactive `bw login` for normal user sessions.
- Use `bw login --sso` when the account requires SSO.
- Use `bw login --apikey` for automation, external applications, or cases where normal login is not suitable.
- If the user explicitly wants a one-shot session key from email/password login, `bw login --raw` can return it directly.
- Avoid passing passwords directly on the command line unless the user explicitly requests it. Prefer the interactive prompt, `--passwordenv`, or `--passwordfile`.

5. Unlock the vault and capture the session key deliberately.

```bash
export BW_SESSION="$(bw unlock --raw)"
bw status
bw --session "$BW_SESSION" list items --search github
```

- `bw login` authenticates the account. `bw unlock` decrypts the vault and returns a new session key.
- Any previous session key becomes invalid after a new `bw unlock`.
- Prefer exporting `BW_SESSION` for a single shell session or pass `--session` per command when you want tighter scope.
- Never echo `BW_SESSION` into logs, tickets, or chat output.

6. Sync vault state before reads when other clients may have changed data.

```bash
bw sync
bw sync --last
```

- Use `bw sync` before reads if the vault may be stale.
- Use `bw sync -f` only when troubleshooting stale local state or a partial sync problem.

7. Use `bw list` and `bw get` for read paths.

```bash
bw --session "$BW_SESSION" list items --search github
bw --session "$BW_SESSION" get item <item-id>
bw --session "$BW_SESSION" get password github.com
bw --session "$BW_SESSION" get totp github.com
```

- Use `bw list` to discover candidate objects and IDs.
- Use `bw get item` for the full JSON object.
- Use `bw get password`, `bw get username`, `bw get uri`, `bw get totp`, or `bw get notes` when the user needs one field.
- Use `jq` after `bw get item` when the user needs targeted extraction from object JSON.

8. Create new objects from Bitwarden templates, then encode the full JSON payload.

```bash
bw --session "$BW_SESSION" get template folder | jq '.name = "Infra"' | bw encode | bw --session "$BW_SESSION" create folder

item_template="$(bw --session "$BW_SESSION" get template item)"
login_template="$(bw --session "$BW_SESSION" get template item.login)"
jq -n \
  --argjson item "$item_template" \
  --argjson login "$login_template" \
  '$item | .type = 1 | .name = "Github" | .login = $login | .login.username = "bot@example.com" | .login.password = "replace-me"' \
  | bw encode \
  | bw --session "$BW_SESSION" create item
```

- Start from `bw get template ...` instead of hand-writing object JSON.
- Use `jq` to fill the template with the required fields.
- If `jq` is unavailable, write the full template JSON to a temporary file, edit it completely, then pass it to `bw encode`.
- Pipe the final JSON through `bw encode` before `bw create` or `bw edit`.
- Do not store the encoded payload in tracked files unless the user explicitly wants that artifact.

9. Edit existing objects by starting from the current object, not a partial patch.

```bash
bw --session "$BW_SESSION" get item <item-id> \
  | jq '.notes = "rotated on 2026-03-06"' \
  | bw encode \
  | bw --session "$BW_SESSION" edit item <item-id>
```

- `bw edit` replaces the stored object with the supplied full JSON payload.
- Begin from `bw get item <id>` for edits so unchanged fields survive.
- If `jq` is unavailable, edit the full current object in a temporary file instead of constructing a partial payload.
- Use templates for new objects and full current objects for edits.

10. End the session explicitly.

```bash
bw lock
bw logout
```

- Use `bw lock` when the user is done for now but wants to remain logged in.
- Use `bw logout` when switching accounts, rotating auth posture, or removing local login state.
- `bw lock` destroys active session keys, so commands using the old `BW_SESSION` will fail until the vault is unlocked again.

## Guardrails

- Never print master passwords, API keys, `BW_SESSION`, or decrypted secrets unless the user explicitly asks for raw output.
- Prefer prompt-based login or `--passwordenv` over putting passwords directly in shell history.
- Prefer `--apikey` for automation instead of personal interactive login flows.
- Treat `bw get password`, `bw get totp`, and attachment retrieval as sensitive output and redact by default.
- Use `bw sync` before reads if multiple devices or teammates may have modified shared vault content.
- Start create flows from `bw get template` and edit flows from `bw get item`; do not hand-build partial JSON for `bw edit`.
- If the user really wants app-runtime secret injection instead of vault CRUD, note that Bitwarden Secrets Manager is a better fit than the Password Manager CLI.

## Troubleshooting

- `bw status` returns `unauthenticated`:
  - Run `bw login` with the correct method, then `bw unlock`.
- `bw status` returns `locked`:
  - Run `bw unlock` and export or pass the new session key.
- Commands fail after a fresh `bw unlock`:
  - Replace the old `BW_SESSION`. Previous session keys become invalid on each unlock.
- The wrong server is configured:
  - Check `bw config server` and `bw status`, then re-run `bw config server <value>` before logging in again if needed.
- Reads look stale:
  - Run `bw sync` or `bw sync -f`, then retry the read.
- `bw edit` drops fields unexpectedly:
  - The payload was incomplete. Rebuild the edit from `bw get item <id>` and apply the change with `jq`.

## Output

- Show the exact commands used.
- State the observed Bitwarden state from `bw status`.
- State whether `BW_SESSION` was exported, passed with `--session`, or intentionally omitted.
- State whether the command only read data or also created, edited, locked, or logged out.
- Call out any written files or sensitive output that should be cleaned up or redacted.
