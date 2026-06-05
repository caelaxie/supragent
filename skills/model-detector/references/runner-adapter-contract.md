# Runner Adapter Contract

Use this contract for any coding-agent runner. Runner references should add concrete evidence surfaces while preserving the common evidence order, alias rules, and confidence rules from `../SKILL.md`.

## Required Fields

- `runner`: product, CLI, IDE, desktop, or service name.
- `target_boundary`: how to identify the exact thread, turn, session, message, job, subagent, provider call, or trace.
- `runtime_metadata`: first-party metadata fields, app state, run status, MCP/tool metadata, event payloads, or provider-call records that can contain the model.
- `request_response_fields`: outgoing request fields and incoming response fields that can contain exact model IDs.
- `config_paths`: project, workspace, user, managed, and environment config locations that can select model, provider, deployment, or route.
- `session_log_paths`: local data directories, databases, transcripts, debug logs, traces, or server logs tied to the target boundary.
- `alias_resolution`: where aliases, defaults, deployment names, or routes are mapped to exact models.
- `multi_agent_rules`: how the runner represents per-agent models and when one agent's model can answer the requested target.
- `secret_rules`: keys, tokens, prompt fields, payload fields, or attachments to redact or report only as present.
- `confidence_rules`: runner-specific rules for high, medium, low, and unknown confidence.

## Generic Search Keys

Use targeted searches with these keys, then add runner-specific keys from the runner reference:

```text
model
model_id
modelID
MODEL
provider
deployment
engine
route
agent
subagent
sessionID
session_id
threadID
thread_id
turnID
turn_id
messageID
message_id
requestID
request_id
traceID
trace_id
```

## Adapter Quality Bar

- Runtime evidence must be tied to the same target boundary before it earns high confidence.
- Config evidence must include precedence and override checks before it earns medium confidence.
- Source defaults are low confidence unless the runner proves no override can apply.
- Per-agent config is not session-level proof unless the target is that agent or runtime evidence links that agent to the target message.
- Provider routes and aliases are unresolved until mapped to an exact model at the target time.
