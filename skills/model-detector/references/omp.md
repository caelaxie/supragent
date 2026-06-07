# Oh My Pi (OMP) Model Detection

Use this reference when the target is an Oh My Pi (OMP) / coding-agent session, turn, leaf entry, role (default/smol/slow/plan/designer/commit/task/vision), task subagent, or any OMP-managed provider call.

OMP is the current primary runner in this harness. Codex and OpenCode references remain for compatibility with those external runners.

## Adapter Fields
- `runner`: `omp`.
- `target_boundary`: OMP session id (or `~/.omp/agent/sessions/--<cwd-encoded>--/<ts>_<id>.jsonl` path), leaf/entry id or turn timestamp, role name (`default`, `smol`, `slow`, `plan`, `designer`, `commit`, `task`, `vision`), subagent/task name or child session id, provider call / request id.
- `runtime_metadata`: Session JSONL entries (`model_change`, assistant `message` with `provider`/`model`), `buildSessionContext` derived model map (per-role), current turn/tool metadata, RPC state model object, AgentSession live model, subagent spawn parameters (`model`, `thinkingLevel`), task execution effectiveAgent.
- `request_response_fields`: Outgoing provider request top-level `model` (and `reasoning_effort` / thinking fields), response metadata, streaming events, pi-native stream payloads, gateway/broker request records.
- `config_paths`: `~/.omp/agent/models.yml` (primary model catalog + equivalence + overrides), `~/.omp/agent/config.yml` (`modelRoles`, `enabledModels`, `modelProviderOrder`, scoped entries), project `<cwd>/.omp/config.yml` + nearest ancestor `.omp` dirs via config discovery, legacy `settings.json`, CLI flags (`--model`, `--smol`, `--slow`, `--plan`, ...), environment variables (`PI_*_MODEL`, `OMP_*` mirrors).
- `session_log_paths`: `~/.omp/agent/sessions/...` JSONL files, `~/.omp/agent/blobs/`, terminal breadcrumb files under `~/.omp/agent/terminal-sessions/`, tool/subagent output artifacts.
- `alias_resolution`: Concrete `provider/modelId` vs canonical ids (e.g. `gpt-5.3-codex`); `modelRoles` role aliases; `equivalence.overrides` and `exclude` in models.yml; context promotion targets (`contextPromotionTarget`); globs/fuzzy matching only affect selection (stored and logged values are exact selectors).
- `multi_agent_rules`: OMP maintains distinct models per role via `modelRoles` + per-role `model_change` entries. Task subagents declare their own `model` (and `thinkingLevel`) in agent frontmatter and execute in isolated child sessions with their own JSONL entries. Per-role or per-subagent config answers only for that named scope unless runtime evidence (model_change / message on the target leaf path) proves the same model handled the target turn. Do not collapse default/coding, planning, title, summarization, review, designer, commit, or tool-specialist roles/subagents into one session-level model.
- `secret_rules`: Redact all `*_API_KEY`, `*_TOKEN`, `*_OAUTH_*`, bearer tokens, full request/response bodies, prompts, attachments, and image data. Report only model/provider/role fields, file paths (with line anchors when useful), and presence/absence of credentials. Environment-backed secrets in models.yml are reported as references only.
- `confidence_rules`: High when first-party runtime metadata (`model_change` for the exact leaf/role or assistant `message.provider`+`model`, live tool/RPC metadata, or subagent session records) is bound to the target turn/leaf/role/subagent. Medium when model comes from config (`models.yml` + `modelRoles` or agent frontmatter `model`) after confirming no overriding runtime `model_change` on the target path. Low when only built-in registry defaults, implicit discovery, or non-target evidence is available. Unknown when no exact model selector is exposed.

## Config and Runtime Model Resolution Precedence (OMP)
Collect evidence in this order for the target boundary. Always start from the highest-precedence source that supplies data for the exact target; still record lower-precedence values that were overridden.

1. First-party runtime for the exact target (preferred for high confidence):
   - `model_change` entries on the leaf-to-root parent chain for the requested role (or default role).
   - Assistant `message` entries (`provider` + `model`) for the turn.
   - Live AgentSession / tool call metadata / RPC state for the current turn.
   - Subagent child session entries or spawn parameters when the target is a task subagent.
   - Temporary context promotion `model_change` entries (note they are temporary and do not rewrite saved role mappings).

2. Explicit CLI / environment overrides active for the session or turn:
   - `--model provider/id` (or role-specific `--smol`, `--slow`, `--plan`, ...).
   - `PI_SMOL_MODEL`, `PI_SLOW_MODEL`, `PI_PLAN_MODEL`, and other `PI_*_MODEL` env vars.

3. Project settings (nearest ancestor `.omp/config.yml` or discovered settings capability items under `.omp`).

4. Global user settings:
   - `~/.omp/agent/config.yml` → `modelRoles` (role → `provider/modelId` or canonical id; may carry `:thinkingLevel` suffix), `enabledModels` (scoped), `modelProviderOrder`.
   - `~/.omp/agent/models.yml` → provider definitions, concrete models, `modelOverrides`, `equivalence.overrides` / `exclude`.

5. Built-in ModelRegistry catalog + runtime discovery (Ollama, llama.cpp, LM Studio, explicit `discovery` providers, extension-registered providers) after `models.yml` merge.

Legacy `.json`/`.jsonc` paths are still honored only when passed programmatically to ModelRegistry; the documented user paths are `models.yml` and `config.yml`.

## Model Fields and Evidence Locations
Search these keys and structures (add to the generic search keys from the adapter contract as needed):

- Session JSONL: `"type": "model_change"`, `"model"`, `"role"`.
- Assistant messages: `"provider"`, `"model"` inside the `message` object.
- `models.yml`:
  - `providers.<provider-id>.models[].id`
  - `providers.<provider-id>.modelOverrides.<model-id>`
  - `equivalence.overrides["<provider>/<model>"]`
- `config.yml`:
  - `modelRoles.default`, `modelRoles.smol`, `modelRoles.slow`, `modelRoles.plan`, `modelRoles.designer`, `modelRoles.commit`, `modelRoles.task`, `modelRoles.vision`
- Task agent definitions (frontmatter under agents/ dirs discovered via `.omp`, `.claude`, `.codex`, `.gemini`, plugins, bundled):
  - `model: ...`
  - `thinkingLevel: off|minimal|low|medium|high|xhigh`
- Runtime surfaces: tool metadata `model`, RPC responses containing `model: { provider, id }`.
- Provider wire: request body `model`; response and usage metadata.
- CLI / env: `--model`, `PI_*_MODEL` family, `OMP_*` mirrors.

Preserve provider-qualified forms (`anthropic/claude-sonnet-4-5`, `openai/gpt-5.3-codex`) exactly as stored or logged. When a canonical id is in effect, report both the canonical and the concrete provider/model that actually executed (session state always records the concrete).

## OMP-Specific Workflow
1. Capture scope: session (id or path), target leaf/entry or message timestamp, role (if role-specific question), subagent name (if task subagent), cwd.
2. Inspect runtime first:
   - Read the session JSONL for the target boundary.
   - Walk `parentId` chain (or simulate `buildSessionContext` logic) to find the latest `model_change` for the relevant role on the path to the leaf.
   - Use the `provider` + `model` from the assistant `message` entry for the turn as fallback or confirmation.
   - For subagents: prefer the child session's own entries or the model/thinkingLevel passed at spawn time plus the agent definition.
3. If the user asks for "current model" without naming a role or agent, resolve the active model for the default role (or the role that produced the current leaf's last assistant message).
4. Read config (`models.yml` + `config.yml` modelRoles + agent frontmatter) only when runtime proof for the target is missing or to document overrides/precedence.
5. Resolve aliases and equivalence only with proof at the target time:
   - Record the concrete selector that executed.
   - Note any canonical mapping or temporary promotion.
6. Report one result per distinct role or subagent when the target scope includes multiple.
7. Record confidence, binding evidence (exact entry ids, file paths + offsets, metadata keys), and any limits (missing session file for old turns, redacted auth, unavailable child session, etc.).
8. `next_proof_step`: suggest the concrete next action that would raise confidence (e.g., "inspect model_change entries after <leafId> for role 'plan'", "read ~/.omp/agent/config.yml modelRoles", "re-run with --plan to force a plan-role turn").

## Output Contract Additions for OMP
- `runner`: `omp`.
- `agent`: role name (e.g. `plan`, `smol`) or task subagent name when the question targets that scope.
- `exact_model`: the concrete selector (`provider/modelId` preferred) or canonical id that was active for the target.
- `provider`: the provider id portion (or inferred from the model string / message).
- `confidence`, `evidence`, `limits`, `next_proof_step` follow the skill-wide rules.

Treat any `auto`, `latest`, deployment name, gateway route, or product label as unresolved unless first-party OMP metadata maps it to a concrete model id for this exact target turn/role/subagent.
