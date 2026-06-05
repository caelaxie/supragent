---
name: model-detector
description: Detect the exact model identifier used by Codex, an agent run, CLI invocation, API request, or application integration from first-party metadata, logs, config, and request or response evidence. Use when asked what model is being used, to verify a model, or to distinguish exact model IDs from aliases and family names.
---

# Model Detector

## Goal

Determine the exact model identifier for the target run or integration from evidence. Do not infer the model from behavior, speed, UI branding, or broad family labels.

## Target First

Before investigating, name the target:
- Current Codex thread or turn.
- A spawned subagent.
- A Codex CLI or desktop run.
- An OpenAI API request.
- An application, gateway, router, or third-party client.

If the user does not specify a target, default to the current Codex thread and say that this scope is assumed.

## Evidence Order

Prefer proof in this order:
1. First-party runtime metadata for the exact thread, job, request, or trace.
2. Raw request or response fields that include a model ID.
3. Local command invocation, config, or environment variables that set the model.
4. Application logs or provider traces tied to the same request ID.
5. Source code defaults only when no runtime override can apply.

Treat aliases such as `auto`, `latest`, `best`, `default`, deployment names, gateway names, or product labels as unresolved unless first-party metadata maps them to a concrete model ID for this request.

## Workflow

1. Capture scope and timestamp.
- Record the target and whether the answer needs current live proof or static configuration proof.
- If a request ID, thread ID, trace ID, run ID, or log window is available, use it to bind the evidence.

2. Inspect exposed metadata.
- Read any explicit model fields already present in the conversation, thread context, app metadata, tool metadata, or run status.
- For tools that expose request metadata, inspect that metadata directly before searching files.
- If metadata only says a broad family such as `GPT-5` or a surface such as `Codex`, do not treat that as exact.

3. Check local invocation and config.
- Inspect the command, flags, config files, and relevant environment variables that selected the model.
- Search targeted paths for keys such as `model`, `model_id`, `MODEL`, `OPENAI_MODEL`, `CODEX_MODEL`, `deployment`, `engine`, and provider-specific aliases.
- Keep searches scoped to the project or run artifacts unless the user approves broader personal log inspection.

4. Check request and response evidence.
- For OpenAI or compatible APIs, look for the model in the outgoing request body and in the provider response or trace.
- For routers or gateways, follow the request through routing logs to the provider call and final response.
- If request and response disagree, report both and explain which value answers the user's target.

5. Resolve aliases only with proof.
- If the app uses a deployment name, route, or alias, find the mapping active at the request time.
- If no active mapping is available, report the alias as evidence but mark the exact model unknown.

6. Report confidence.
- High: exact model ID tied to the target request/thread by first-party metadata, request/response, or trace.
- Medium: exact model ID comes from config or command line and no runtime override was found.
- Low: only defaults, source code, or partial logs were available.
- Unknown: no exact model evidence was exposed.

## Output

Return:
- `target`: the run, thread, request, or integration investigated.
- `exact_model`: the concrete model ID, or `unknown`.
- `confidence`: `high`, `medium`, `low`, or `unknown`.
- `evidence`: commands, file paths with lines, metadata fields, request IDs, or trace IDs.
- `limits`: missing metadata, aliases, unavailable logs, or unverified runtime overrides.
- `next_proof_step`: one concrete action that would raise confidence, when applicable.

## Guardrails

- Never claim an exact model from self-identification, writing style, latency, benchmark behavior, or visible UI text alone.
- Do not expose secrets, full prompts, or private payloads while collecting proof; quote only the fields needed to prove the model.
- If exact model metadata is not available, say so plainly instead of guessing.
- When library or API behavior is needed to interpret model fields, use Context7 for current official documentation before relying on memory.
