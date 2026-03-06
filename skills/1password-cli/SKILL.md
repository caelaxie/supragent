---
name: 1password-cli
description: Use 1Password CLI (`op`) for secure secret access from the terminal. Use when Codex needs to sign in to 1Password, choose an account, inspect or build secret references, read a single secret with `op read`, inject secrets into a subprocess with `op run`, render config templates with `op inject`, or troubleshoot 1Password CLI auth and secret resolution.
---

# 1Password CLI

## Goal

Use `op` to access secrets safely without copying plaintext values into tracked files, long-lived shell state, or normal command output.

## Workflow

1. Verify the CLI is available and reasonably current.

```bash
op --version
```

- If `op` is missing, use the official 1Password CLI install docs.
- Prefer the latest stable CLI when local behavior and docs differ.
- Use `op update` only when the user explicitly wants to check for or download a newer CLI build.

2. Prefer desktop app integration and confirm auth state.

```bash
op signin
op whoami
```

- Default path: enable `Integrate with 1Password CLI` in the 1Password desktop app, then let `op signin` or any protected command prompt for auth.
- `op signin` is idempotent. It only prompts when the user is not already authenticated.
- Use `op whoami` as the clean auth-state check.
- Treat `op signin --raw` session tokens as an automation fallback, not the default interactive flow.

3. Select the intended account explicitly when multiple accounts are configured.

```bash
op account list
op whoami --account <account>
OP_ACCOUNT=<account> op read <reference>
```

- Account precedence is: `--account`, then `OP_ACCOUNT`, then the most recently signed-in account.
- In scripts, prefer `--account` per command or set `OP_ACCOUNT` once for the script scope.

4. Obtain or verify a secret reference before reading values.

```bash
op item get <item> --vault <vault> --format json
```

- Inspect the JSON output for a field's `reference` value and reuse that reference instead of reconstructing it by hand.
- Prefer IDs over names when names are unstable or contain unsupported characters.
- Secret reference parts are case-insensitive. Names may use alphanumerics, spaces, `.`, `_`, and `-`. Use IDs if a path segment falls outside that set.

5. Use `op read` when the user needs one secret or one secret-backed file.

```bash
op read op://app-prod/db/password
op read --out-file ./id_rsa 'op://infra/ssh/private key?ssh-format=openssh'
```

- Default output is stdout. Use `--out-file` for files and keep the destination restrictive.
- Use query parameters for advanced cases such as OTPs or SSH key formatting.
- Choose `op read` for one resolved value, not for a full process environment.

6. Use `op run` as the default way to run a process with secrets.

```bash
export DB_PASSWORD='op://app-prod/db/password'
op run -- sh -c 'printf "%s\n" "$DB_PASSWORD"'

cat > .env <<'EOF'
DB_USER=op://app-prod/db/username
DB_PASSWORD=op://app-prod/db/password
EOF
op run --env-file=.env -- npm test
```

- `op run` resolves secret references in exported environment variables or dotenv files, then injects the resolved values only for the subprocess lifetime.
- Prefer this over exporting plaintext secrets into the current shell.
- Output masking is enabled by default. Avoid `--no-masking` unless the user explicitly asks for raw values.
- Watch for shell expansion order. If a command needs `$VAR`, run the expansion inside the subprocess (`sh -c '...'`) or export the reference before invoking `op run`.
- If the same variable exists in the shell and an env file, the env file wins.

7. Use `op inject` when the user wants a rendered config artifact.

```bash
cat > config.yml.tpl <<'EOF'
db_password: {{ op://app-prod/db/password }}
EOF

op inject -i config.yml.tpl -o config.yml
```

- Use `{{ op://... }}` placeholders in template files or stdin.
- Use stdin/stdout for transient output; use `-i` and `-o` when the user explicitly needs a file.
- Delete the rendered plaintext file when it is no longer needed.
- Choose `op inject` for config generation, not for launching a single command with secrets.

## Guardrails

- Prefer secret references over plaintext secrets in repo-tracked files, notes, tickets, and chat output.
- Redact resolved secret values unless the user explicitly requests the raw value.
- Prefer `op run` over long-lived plaintext exports.
- When writing files with `op read --out-file` or `op inject -o`, keep file permissions restrictive and call out cleanup.
- For CI, headless automation, or least-privilege access, prefer service accounts over personal interactive sessions.
- Keep 1Password shell plugins out of scope unless the user explicitly asks about `op plugin`.

## Troubleshooting

- `op whoami` fails:
  - The user is not authenticated. Run `op signin` and retry.
- The wrong account is active:
  - Run `op account list`, then retry with `--account <account>` or `OP_ACCOUNT=<account>`.
- A secret reference fails:
  - Re-check the vault, item, and field with `op item get <item> --vault <vault> --format json`.
  - Switch to IDs if names are ambiguous or contain unsupported characters.
  - Confirm the signed-in account has access to the vault.
- A command sees the literal `op://...` string instead of the secret:
  - Use `op read` for a single value, `op run` for environment injection, or `op inject` for templates.
- Automation uses `--raw` session tokens:
  - Treat them as temporary. They expire after inactivity and should not be stored in tracked files.

## Output

- Show the exact commands used.
- State which account and auth checks were performed.
- State whether secrets were injected into a subprocess, written to a file, or only referenced.
- If a command materialized plaintext on disk, name the file path and the cleanup expectation.
