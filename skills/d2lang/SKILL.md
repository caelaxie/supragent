---
name: d2lang
description: Generate, refactor, debug, and explain D2 diagrams using documented D2 language and CLI behavior. Use when requests mention D2, .d2 files, architecture/flow/ERD/sequence/class diagrams, imports, layers/scenarios/steps composition, D2 layout/style tuning, or D2 render/format/validate/export commands.
---

# D2lang

## Overview

Use documented D2 syntax only.
Generate readable, maintainable `.d2` that renders cleanly on first run.
Return full-file outputs by default.

## Input Completeness Gate

Before generating a new diagram, confirm:
- Diagram type (architecture, flowchart, ERD, sequence, class, other).
- Nodes/actors/tables that must exist.
- Required relationships and direction.
- Required grouping/containers.
- Output preference (SVG/PNG/PDF/PPTX/GIF/TXT) if specified.
- Layout/theme constraints if specified.

If high-impact details are missing, ask clarifying questions first.

## Clarifying Question Protocol

1. Ask at most 3 high-impact questions.
2. Prioritize questions in this order: structure, relationships, constraints.
3. If the user does not provide details, proceed with explicit assumptions.

## Workflow

1. Classify the requested diagram and identify minimum required entities/edges.
2. Pick layout, direction, and theme strategy before writing shapes.
3. Declare shapes/containers first, then connections.
4. Apply shared style with globs/classes, then local overrides.
5. Add imports/composition only when requested or clearly beneficial.
6. Apply troubleshooting rules if compile/render quality is poor.
7. Return output following the response contract.

## Core Language Rules

### Comments and Strings

- Use line comments with `#`.
- Use block comments with triple double-quotes.
- Use unquoted strings when possible.
- Quote keys/labels that contain reserved symbols or reserved keywords.
- Use block strings for markdown, code, and latex text blocks.

```d2
"service endpoint": "/v1/payments"
"""
Block comments are valid in D2.
"""
note: |md
### Retry Policy
- exponential backoff
|
```

### Shapes, Keys, and Containers

- Use `shape` to set explicit shape type; default is `rectangle`.
- Treat keys as case-insensitive (`postgres` and `Postgres` resolve to same key).
- Use semicolons to define multiple objects on one line.
- Prefer block container syntax for nested hierarchy.
- Use full paths or parent references (`_`) for cross-container references.

### Connections

- Use only valid connection operators: `--`, `->`, `<-`, `<->`.
- Connect by key, not by label.
- Treat repeated connections as distinct edges.
- Index repeated connections when targeting them: `(a -> b)[0]`.
- Use `source-arrowhead` and `target-arrowhead` for arrowhead customization.

```d2
be: Backend
fe: Frontend
be -> fe: API
(be -> fe)[0].target-arrowhead.shape: diamond
```

### Overrides and Null

- Merge redeclarations with existing objects.
- Treat the latest explicit label assignment as authoritative.
- Use `null` to delete shapes, connections, or attributes.
- Expect nulling a shape to also remove its descendants/connections.

## Variables and Configuration

- Define variables under `vars`.
- Reference variables with `${...}`.
- Use dotted lookup for nested vars.
- Use `...${x}` to spread map/array values.
- Use single quotes to bypass substitutions.
- Configure CLI-equivalent options under `vars.d2-config`.

```d2
vars: {
  env: prod
  palette: {
    primary: "#0ea5e9"
  }
  d2-config: {
    layout-engine: elk
    theme-id: 300
    dark-theme-id: 200
    pad: 20
    sketch: false
  }
}
api: API {
  style.fill: ${palette.primary}
}
```

Compatibility note (local `d2 0.7.1`): CLI flags and env vars override `vars.d2-config`.

## Imports and Reuse

- Use regular imports (`x: @common`) or spread imports (`...@common`) inside maps.
- Omit `.d2` extension in import paths.
- Use partial imports to target a subpath from imported files.
- Resolve relative imports from the importing file path.
- Use classes for reusable style bundles and globs for bulk defaults.

```d2
classes: {
  service: {
    shape: rectangle
    style.fill: "#e0f2fe"
  }
}
api: @services.api
worker: {
  ...@services.worker
  class: service
}
```

## Composition (Layers, Scenarios, Steps)

- Use `layers` for independent boards with no inheritance.
- Use `scenarios` for boards inheriting from base layer/root board.
- Use `steps` for incremental changes inheriting from previous step.
- Use `link` to navigate to other boards.
- Use `--target` for rendering a specific board subtree.

```d2
app -> db
scenarios: {
  degraded: {
    app.style.opacity: 0.5
    app -> cache: fallback
  }
}
```

Compatibility note (local `d2 0.7.1`): composition rendering features are available, and `--target` is supported in CLI help.

## Special Diagram Types

### SQL Tables

- Use `shape: sql_table`.
- Define each row as `name: type {constraint: ...}`.
- Use `primary_key`, `foreign_key`, `unique` (shortened in rendering as PK/FK/UNQ).

```d2
users: {
  shape: sql_table
  id: int { constraint: primary_key }
  email: varchar(255) { constraint: unique }
}
posts: {
  shape: sql_table
  id: int { constraint: primary_key }
  user_id: int { constraint: foreign_key }
}
users.id <-> posts.user_id
```

### Sequence Diagrams

- Set `shape: sequence_diagram`.
- Treat declaration order as visual order.
- Declare actors used in groups at the top level first, then reference them in groups.

```d2
shape: sequence_diagram
client; api; db
client -> api: GET /users
api -> db: query
db -> api: rows
api -> client: 200 OK
```

### UML Class Diagrams

- Use `shape: class`.
- Use keys with `(` to define methods.
- Use optional visibility prefixes (`+`, `-`, `#`) for members.

```d2
User: {
  shape: class
  +id: int
  -token: string
  +save(): void
}
```

## Layout and Styling

- Default to `elk` for dense architecture diagrams.
- Use `dagre` for simple directional flows.
- Set `direction` (`up`, `down`, `left`, `right`) intentionally.
- Prefer globs for global style consistency.
- Use root styles only where supported.

Common style keys:
- `fill`, `fill-pattern`, `stroke`, `stroke-width`, `stroke-dash`
- `border-radius`, `shadow`, `3d`, `multiple`, `double-border`
- `font`, `font-size`, `font-color`, `bold`, `italic`, `underline`, `text-transform`
- `animated`

Compatibility note (local `d2 0.7.1`): `d2 layout` lists `dagre` and `elk` locally; docs include TALA-specific features such as object `near`, `top`, and `left`.

## Troubleshooting Playbook

When debugging compile/render issues:
1. Quote labels/values with reserved characters.
2. Add explicit newlines for long text labels.
3. Increase shape width/height when connections are cluttered.
4. Quote reserved keywords when used as normal keys.
5. Use semantic HTML in markdown blocks (for example `<br/>`).
6. Use ASCII punctuation for special syntax characters in non-English text.
7. Run formatter and validator to catch structural issues quickly.

```bash
d2 fmt diagram.d2
d2 validate diagram.d2
```

## CLI and Exports

Use commands aligned with official docs and local CLI:

```bash
d2 diagram.d2 diagram.svg
d2 --layout=elk --theme=300 --dark-theme=200 --pad=40 diagram.d2 diagram.svg
d2 --watch diagram.d2
d2 validate diagram.d2
d2 fmt diagram.d2
d2 diagram.d2 diagram.pdf
d2 diagram.d2 diagram.pptx
d2 diagram.d2 diagram.gif
d2 diagram.d2 diagram.txt
d2 --ascii-mode standard diagram.d2 diagram.txt
d2 --target='scenarios.degraded.*' diagram.d2 diagram.svg
echo "x -> y" | d2 - - > diagram.svg
```

Compatibility note (local `d2 0.7.1`): ASCII export is marked beta in docs; PNG/PDF/PPTX/GIF flows may require Playwright/browser dependencies.

## Response Contract

Always:
1. Ask clarifying questions first when requirements are incomplete.
2. Return one complete `.d2` file in a fenced `d2` block.
3. Include an `Assumptions` section when proceeding with missing details.
4. Include one sentence explaining layout/style choice.
5. Include one recommended render command (and optional validate command).
6. Preserve semantics first when refactoring existing diagrams.

## Self-Check Checklist

Before final response, verify:
1. Use only documented D2 syntax and CLI options.
2. Reference keys (not labels) in connections.
3. Keep containers/paths unambiguous.
4. Keep examples and commands internally consistent.
5. Return full-file output unless user explicitly requests partial output.
