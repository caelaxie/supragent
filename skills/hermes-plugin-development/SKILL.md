---
name: hermes-plugin-development
description: Create or update Hermes general plugins with `plugin.yaml`, `register(ctx)`, tool schemas, handlers, hooks, slash commands, CLI commands, and discovery or enablement debugging. Use when asked to build a Hermes plugin, write `plugin.yaml`, implement `register(ctx)`, add Hermes tools or hooks, or troubleshoot plugin loading and opt-in enablement.
---

# Hermes Plugin Development

## Goal

Design, implement, and validate Hermes general plugins without drifting into provider-plugin internals.

## When To Use

Use this skill for:

- New Hermes plugins under `~/.hermes/plugins/<name>/` or `.hermes/plugins/<name>/`
- Existing plugin edits involving `plugin.yaml`, `__init__.py`, `schemas.py`, or `tools.py`
- Adding Hermes tools, hooks, slash commands, CLI commands, or bundled skills
- Debugging discovery, missing env gating, or opt-in enablement problems

Do not use this skill as the primary guide for memory-provider or context-engine plugins. Mention them only as specialized follow-on work.

## Plugin Shape

Standard Hermes general plugin layout:

```text
~/.hermes/plugins/my-plugin/
├── plugin.yaml
├── __init__.py
├── schemas.py
└── tools.py
```

- `plugin.yaml`: plugin identity plus declared capabilities
- `schemas.py`: tool schemas the model sees
- `tools.py`: handlers that do the work
- `__init__.py`: `register(ctx)` wiring for tools, hooks, commands, or skills

Project-local plugins in `.hermes/plugins/` are disabled by default. They only load when Hermes starts with `HERMES_ENABLE_PROJECT_PLUGINS=true`.

## Workflow

1. Decide the plugin surface first.
- Tools: `ctx.register_tool`
- Hooks: `ctx.register_hook`
- Slash commands: `ctx.register_command`
- CLI commands: `ctx.register_cli_command`
- Bundled skills: `ctx.register_skill`

2. Write `plugin.yaml`.
- Include `name`, `version`, and `description`.
- Add `provides_tools` or `provides_hooks` when it improves clarity.
- Add `requires_env` only when the plugin truly depends on environment variables.

3. Define schemas in `schemas.py`.
- Schemas are model-facing contracts, so descriptions must say when to use the tool and what each field means.
- Keep the parameter object explicit, with clear `properties` and `required`.

4. Implement handlers in `tools.py`.
- Accept `args, **kwargs`.
- Return JSON strings, including on error paths.
- Catch exceptions and turn them into error JSON instead of crashing the tool call.

5. Register everything in `__init__.py`.
- Wire schema to handler with `register(ctx)`.
- Add hooks or commands only after the base tool flow is correct.

6. Validate discovery and enablement.
- Discovery is not enough: Hermes plugins are opt-in.
- Enable the plugin in `plugins.enabled` or via `hermes plugins enable <name>`.
- Use `/plugins` in a running session to confirm loaded state.

## Minimal Skeleton

`plugin.yaml`

```yaml
name: hello-world
version: "1.0"
description: Minimal Hermes plugin with one greeting tool
provides_tools:
  - hello_world
```

`schemas.py`

```python
HELLO_WORLD_SCHEMA = {
    "name": "hello_world",
    "description": "Return a friendly greeting for the provided name.",
    "parameters": {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Name to greet",
            }
        },
        "required": ["name"],
    },
}
```

`tools.py`

```python
import json


def hello_world(args, **kwargs):
    try:
        name = args.get("name", "World")
        return json.dumps({"message": f"Hello, {name}!"})
    except Exception as e:
        return json.dumps({"error": str(e)})
```

`__init__.py`

```python
from .schemas import HELLO_WORLD_SCHEMA
from .tools import hello_world


def register(ctx):
    ctx.register_tool("hello_world", HELLO_WORLD_SCHEMA, hello_world)
```

## Guardrails

- Handlers must return JSON strings, not Python dicts.
- Handlers should accept `args, **kwargs` for forward compatibility.
- Catch exceptions in handlers and return structured error JSON.
- Tool descriptions must be specific enough that the model knows when to call them.
- Project-local plugins need `HERMES_ENABLE_PROJECT_PLUGINS=true`.
- Discovered plugins stay inactive until explicitly enabled.

## Optional Extensions

- Hooks: use `ctx.register_hook` for lifecycle events like `pre_tool_call`, `post_tool_call`, `pre_llm_call`, `post_llm_call`, `on_session_start`, and `on_session_end`.
- Slash commands: use `ctx.register_command(name, handler, description)` when the feature should appear in chat sessions as `/name`.
- CLI commands: use `ctx.register_cli_command(...)` when the feature should add `hermes <plugin> <subcommand>` behavior.
- Bundled skills: use `ctx.register_skill(name, path)` when the plugin should ship promptable skills namespaced as `plugin:skill`.
- Env gating: use `requires_env` in `plugin.yaml` for API keys or similar dependencies; Hermes can prompt for missing values during plugin install.
- Distribution: for packaged plugins, expose an entry point under `project.entry-points."hermes_agent.plugins"` in `pyproject.toml`.

## Validation Checklist

- Hermes starts without plugin import or registration errors.
- `hermes plugins list` shows the plugin as discovered.
- The plugin is explicitly enabled, not merely installed.
- The expected tool or command appears and executes successfully.
- `/plugins` in a running session shows the plugin as loaded.
- Missing `requires_env` values disable the plugin cleanly instead of crashing it.

## Common Mistakes

- Returning a dict from a handler instead of `json.dumps(...)`
- Omitting `**kwargs` from the handler signature
- Letting exceptions escape from the handler
- Writing vague schema descriptions like `"Does stuff"`
- Assuming a plugin is active because Hermes discovered it
