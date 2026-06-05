# Codex Model Detection

Use this reference when the target is Codex Desktop, Codex CLI, or a Codex-managed subagent.

## Adapter Fields

- `runner`: `codex`.
- `target_boundary`: thread ID, turn ID, session ID, subagent ID, request ID, and turn timestamp.
- `runtime_metadata`: Codex turn metadata, thread context, run status, tool request metadata, subagent result metadata, and provider request/response records when exposed.
- `request_response_fields`: request or response fields named `model`, `reasoning_effort`, provider, route, request ID, trace ID, or run ID.
- `config_paths`: Codex invocation flags, Codex config files, workspace metadata, and environment variables such as model-selection variables when present.
- `session_log_paths`: Codex session logs, transcripts, tool metadata, run records, or local app artifacts tied to the target boundary.
- `alias_resolution`: Codex aliases or product labels are unresolved unless first-party metadata maps them to an exact model for the target turn.
- `multi_agent_rules`: spawned subagents can use a different model from the parent turn; detect subagents from their own metadata.
- `secret_rules`: redact prompts, attachments, auth tokens, API keys, and full provider payloads; quote only model and target-binding fields.
- `confidence_rules`: high when first-party Codex metadata or provider request/response evidence is tied to the exact thread, turn, or subagent.

## Workflow

1. Capture the Codex thread, turn, session, and timestamp when available.
2. Inspect first-party runtime metadata before reading local files.
3. If the target is a subagent, use that subagent's own metadata rather than the parent thread's model.
4. If metadata only gives a family, product surface, or alias, search for the request or response record that resolves it.
5. Report config-derived answers as medium confidence only after checking that no runtime override was found.

## Common Evidence Examples

- `x-codex-turn-metadata.model`
- `x-codex-turn-metadata.reasoning_effort`
- `thread_id`, `turn_id`, `session_id`, and `turn_started_at_unix_ms`
- Provider request body `model`
- Provider response metadata `model`
