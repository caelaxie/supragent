---
name: d2lang
description: Generate, refactor, debug, and explain D2 diagram code with idiomatic syntax and render-ready output. Use when requests mention D2, .d2 files, architecture diagrams, flowcharts, ERDs/SQL tables, sequence diagrams, class diagrams, D2 CLI commands, or diagram layout/theme tuning.
---

# D2lang

## Overview

Translate diagram intent into valid, maintainable D2 that renders cleanly on first run.
Prefer deterministic structure, readable keys, and explicit layout/style choices.

## Workflow

1. Parse the request and classify diagram type.
- `architecture`/system map
- `flowchart`
- `erd`/SQL table relationships
- `sequence`
- `class`

2. Choose layout configuration before writing shapes.
- Default to `layout-engine: elk` for architecture and dense graphs.
- Use `layout-engine: dagre` for simple flowcharts.
- Use `layout-engine: tala` only when graph density or routing needs it.
- Set `theme-id` and `dark-theme-id` together.

3. Declare shapes first, then edges.
- Avoid creating nodes implicitly via edges unless intentionally sketching.
- Use descriptive keys (`api_gateway`, `payments_db`) instead of `a`, `b`.
- Use block containers for hierarchy; use dot paths only when concise.

4. Apply styles consistently.
- Use globs for broad defaults.
- Add local overrides only where semantically meaningful.
- Keep labels readable; use Markdown/code blocks only when needed.

5. Return complete output.
- Provide one full `.d2` file in a fenced `d2` block.
- Add one sentence on layout choice.
- Add one render command.

## Syntax Guardrails

- Use `#` single-line comments.
- Use quoted keys when names include reserved tokens or punctuation.
- Use these connection forms: `->`, `<-`, `--`, `<->`.
- Prefer block syntax for nested structures:

```d2
platform: {
  api: API Gateway
  db: Postgres
}
platform.api -> platform.db: reads
```

- Support multi-line labels and rich text when needed:

```d2
api -> worker: "enqueue\njob payload"
note: |md
### Retry Policy
- 3 attempts
- exponential backoff
|
```

## Core Patterns

### Baseline Scaffold

```d2
vars: {
  d2-config: {
    layout-engine: elk
    theme-id: 300
    dark-theme-id: 200
    pad: 20
    sketch: false
  }
}
direction: right
```

### Styling

```d2
*.style.fill: "#e6f4ff"
(* -> *).style.stroke-dash: 0
db.style: {
  fill: "#fff8e1"
  stroke: "#d97706"
  stroke-width: 2
}
```

### SQL Tables (ERD)

```d2
users: {
  shape: sql_table
  id: int PK
  email: varchar(255) UNQ
}
posts: {
  shape: sql_table
  id: int PK
  user_id: int FK
}
users.id <-> posts.user_id
```

### Sequence

```d2
shape: sequence_diagram
client: Client
api: API
db: DB
client -> api: GET /users
api -> db: query
db -> api: rows
api -> client: 200 OK
```

### Class

```d2
User: {
  shape: class
  fields: {
    id int
    email string
  }
  methods: {
    save()
    deactivate()
  }
}
```

## Refactor And Debug Rules

When given existing D2:
1. Preserve semantics first, then improve readability.
2. Normalize configuration into `vars.d2-config` when absent.
3. Move repeated style literals into globs.
4. Convert brittle dot-path sprawl into block containers where clearer.
5. Fix invalid keys/arrows/shape names and return corrected full file.

If render issues are reported:
1. Switch to `layout-engine: elk`.
2. Increase `pad`.
3. Shorten labels or move detail to Markdown nodes.
4. Split overloaded diagrams into layers/scenarios only if requested.

## Response Contract

Always return:
1. Complete `.d2` file (not fragments unless explicitly requested).
2. One-sentence rationale for layout and styling choices.
3. Recommended command, for example:

```bash
d2 diagram.d2 diagram.svg --theme=300 --dark-theme=200 -l elk --pad 20
```
