---
name: model-detector
description: Detect exact model identifiers used by Codex, OpenCode, coding-agent runners, CLI invocations, API requests, or application integrations from first-party metadata, config, logs, traces, and request or response evidence. Use concise runner-agnostic workflow here, then load runner-specific references as needed.
---

# Model Detector

## Goal

Determine the exact model identifier for a target run or integration from evidence. Do not infer the model from behavior, speed, UI branding, broad family labels, or self-identification.

## Target First

Before investigating, name the target:
- Current Codex thread or turn.
- OpenCode session, message, agent, or subagent.
- Another coding-agent runner, CLI, desktop, IDE, session, job, or subagent.
- OpenAI or compatible API request.
- Application, gateway, router, or third-party client.

If the user does not specify a target, default to the current Codex thread and say that this scope is assumed.

## Load References

- Always follow the common workflow in this file.
- If the target is a coding-agent runner, load `references/runner-adapter-contract.md`.
- If the target runner is known and `references/<runner>.md` exists, load that file too.
- If the target runner has no reference yet, use the adapter contract and report which metadata, config, log, and request surfaces were checked.
- When adding support for a new runner, follow `references/adding-a-runner.md`.
- When current library, API, or tool behavior is needed to interpret model fields, use Context7 or first-party docs before relying on memory.

## Evidence Order

Prefer proof in this order:
1. First-party runtime metadata for the exact thread, turn, session, job, message, request, trace, or subagent.
2. Raw request or response fields that include a concrete model ID.
3. Local command invocation, flags, config, or environment variables that set the model.
4. Application logs, session records, provider traces, or router traces tied to the same target boundary.
5. Source defaults only when no runtime override can apply.

Treat aliases such as `auto`, `latest`, `best`, `default`, deployment names, gateway names, routes, or product labels as unresolved unless first-party metadata maps them to a concrete model ID for this target.

For multi-agent runners, per-agent config answers only for that named agent unless runtime evidence proves the same agent handled the target message. Do not collapse coding, planning, title, summarization, review, or tool-specialist agents into one session-level model.

## Workflow

1. Capture scope and timestamp.
- Record the target and whether the answer needs live runtime proof or static configuration proof.
- Bind evidence with any available thread ID, turn ID, session ID, message ID, request ID, trace ID, subagent ID, or log window.

2. Inspect exposed metadata.
- Read explicit model fields already present in conversation context, thread context, app metadata, tool metadata, run status, event payloads, or provider-call metadata.
- For tools that expose request metadata, inspect that metadata before searching files.
- If metadata only says a model family, provider, runner name, or product surface, do not treat it as exact.

3. Check invocation and config.
- Inspect commands, flags, config files, and environment variables that select model, provider, deployment, route, or reasoning mode.
- Search targeted paths for keys such as `model`, `model_id`, `modelID`, `MODEL`, `<RUNNER>_MODEL`, `provider`, `deployment`, `engine`, `route`, and provider-specific aliases.
- Keep searches scoped to the project, workspace, or run artifacts unless the user approves broader personal log inspection.
- Treat API keys and auth tokens only as presence/absence evidence. Never print secret values.

4. Check request, response, logs, and traces.
- For APIs, look for the model in outgoing request bodies and provider responses.
- For routers or gateways, follow the request through routing logs to the provider call and final response.
- For coding-agent runners, inspect session records, local data directories, transcripts, debug logs, databases, and client/server traces tied to the target boundary.
- If request and response disagree, report both and explain which value answers the target.

5. Resolve aliases only with proof.
- If the app uses an alias, deployment name, route, or default, find the active mapping at the target time.
- If no active mapping is available, report the alias as evidence but mark the exact model unknown.

6. Report confidence.
- High: exact model ID tied to the target by first-party runtime metadata, request/response, or trace.
- Medium: exact model ID comes from config or command line and no runtime override was found.
- Low: only defaults, source code, partial logs, or non-target-specific evidence were available.
- Unknown: no exact model evidence was exposed.

## Output

Return:
- `target`: the run, thread, session, message, request, or integration investigated.
- `runner`: the coding agent, CLI, API, gateway, or integration when known.
- `exact_model`: the concrete model ID, or `unknown`.
- `provider`: the provider, deployment, or route when known.
- `agent`: the agent or subagent name when the target is a multi-agent runner.
- `confidence`: `high`, `medium`, `low`, or `unknown`.
- `evidence`: commands, file paths with lines, metadata fields, request IDs, trace IDs, or config keys.
- `limits`: missing metadata, aliases, unavailable logs, or unverified runtime overrides.
- `next_proof_step`: one concrete action that would raise confidence, when applicable.

## Guardrails

- Never claim an exact model from self-identification, writing style, latency, benchmark behavior, or visible UI text alone.
- Do not expose secrets, full prompts, attachments, or private payloads while collecting proof; quote only the fields needed to prove the model.
- If exact model metadata is not available, say so plainly instead of guessing.
