# Adding A Runner Adapter

Use this guide when adding first-class support for another coding agent.

## Steps

1. Create `references/<runner>.md` with the runner's common lowercase name.
2. Fill every field from `runner-adapter-contract.md`; use `unknown` only when the runner truly does not expose that surface.
3. Keep `SKILL.md` concise and runner-agnostic. Do not add runner-specific workflows to the main skill body.
4. Add concrete config paths, metadata field names, log paths, database names, and search keys in the runner reference.
5. Document config precedence and runtime override behavior.
6. Define how aliases, routes, deployments, default models, and provider-qualified model names are resolved.
7. Define multi-agent behavior: primary agents, subagents, title/summarizer agents, planner/reviewer agents, and when per-agent config can answer the requested target.
8. Add secret redaction rules for API keys, auth tokens, headers, prompts, attachments, and full payloads.
9. Use Context7 or first-party docs for current library/API behavior before encoding details.
10. Update `README.md` or agent metadata only when the public capability description changes.

## Reference Template

```markdown
# <Runner> Model Detection

Use this reference when the target is <runner surfaces>.

## Adapter Fields

- `runner`: `<runner>`.
- `target_boundary`: ...
- `runtime_metadata`: ...
- `request_response_fields`: ...
- `config_paths`: ...
- `session_log_paths`: ...
- `alias_resolution`: ...
- `multi_agent_rules`: ...
- `secret_rules`: ...
- `confidence_rules`: ...

## Workflow

1. ...
```
