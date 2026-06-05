# OpenCode Model Detection

Use this reference when the target is an OpenCode CLI, TUI, server, session, message, agent, or subagent run.

This reference follows current OpenCode docs that use `opencode.json`, top-level `model`, `agent`, and `provider` config. Some older installations or forks may use legacy `.opencode.json` and `agents`; check legacy files only as compatibility evidence.

## Adapter Fields

- `runner`: `opencode`.
- `target_boundary`: project path, session ID, message ID, agent name, subagent name, provider call, and timestamp.
- `runtime_metadata`: OpenCode session/message metadata, event payloads, server logs, debug traces, provider-call records, MCP/tool metadata, and terminal output tied to the session or message.
- `request_response_fields`: provider request or response fields named `model`, `provider`, `agent`, `sessionID`, `messageID`, route, request ID, or trace ID.
- `config_paths`: `OPENCODE_CONFIG_CONTENT`, managed config, project `opencode.json`, `.opencode` directories, `OPENCODE_CONFIG`, global `~/.config/opencode/opencode.json`, remote config, and legacy `.opencode.json` files when present.
- `session_log_paths`: configured data directories, `.opencode` project directories, debug logs, transcripts, local databases, server traces, and provider logs tied to the target boundary.
- `alias_resolution`: top-level `model`, top-level `small_model`, `agent.<name>.model`, `provider.<name>.models`, custom provider routes, gateway model names, and runtime defaults.
- `multi_agent_rules`: OpenCode can configure primary agents and subagents with different models; answer at agent scope unless runtime evidence proves the target message's agent.
- `secret_rules`: redact `apiKey`, `headers.Authorization`, provider tokens, prompts, attachments, and full payloads. Environment-backed secrets such as `{env:ANTHROPIC_API_KEY}` should be reported only as references, not resolved.
- `confidence_rules`: high when a provider call, session/message event, or runtime trace gives the exact model for the target message; medium for config after precedence and overrides are checked.

## Config Precedence

Check current OpenCode config sources in effective-precedence order when evidence is available:

1. macOS managed preferences, such as `.mobileconfig` via MDM.
2. Managed config files, such as `/Library/Application Support/opencode/` on macOS.
3. `OPENCODE_CONFIG_CONTENT` inline config.
4. Project `.opencode` directories for agents, commands, and plugins.
5. Project `opencode.json`, discovered from the current directory upward to the nearest Git directory.
6. `OPENCODE_CONFIG` custom config path.
7. Global `~/.config/opencode/opencode.json`.
8. Remote organizational config.

When using this order for detection, start from the highest-precedence source that exists, but still note lower-precedence model settings if they were overridden.

## Model Fields

Look for:

- Top-level `model`, for example `anthropic/claude-sonnet-4-20250514`.
- Top-level `small_model`, for smaller model selection.
- `agent.<name>.model` for primary agents and subagents.
- `agent.<name>.mode`, to distinguish primary agents from subagents.
- `provider.<name>.models`, including gateway or custom-provider model IDs.
- `provider.<name>.options.baseURL`, route, gateway, or deployment details.
- Legacy `agents.<name>.model` in `.opencode.json` if present.

Preserve provider-qualified model names exactly as written.

## Workflow

1. Capture project path, session ID, message ID, agent or subagent name, and timestamp when available.
2. Prefer runtime evidence from session/message metadata, events, provider calls, or debug traces.
3. If the user asks for "current model" but no message or agent is named, default to the active coding agent only when visible context clearly identifies it; otherwise report the target agent as unresolved.
4. Read effective config only when runtime proof is missing or incomplete.
5. If multiple agents have different models, return one row or bullet per agent.
6. If OpenCode selected a default because no model was configured, find the active default from runtime or config-load evidence before reporting it. If only source defaults are available, confidence is low.
