---
name: d2lang
description: Generate, refactor, debug, and explain D2 diagrams using documented D2 language and CLI behavior. Use when requests mention D2, .d2 files, architecture/flow/ERD/sequence/class diagrams, imports, layers/scenarios/steps composition, D2 layout/style tuning, or D2 render/format/validate/export commands.
---

# D2lang

## Goal

Produce valid, readable `.d2` that renders correctly with documented D2 syntax/CLI.

## Intake Gate

Before writing a new diagram, confirm:
- Diagram type.
- Required entities and relationships.
- Required grouping/containers.
- Output/format/layout constraints (if any).

Clarifying protocol:
1. Ask at most 3 high-impact questions.
2. Prioritize structure, then relationships, then constraints.
3. Proceed with explicit assumptions only for non-safety-critical ambiguity.
4. If ambiguity can impact security, auth, data integrity, compliance, or destructive operations, stop and ask for clarification.

## Workflow

1. Classify diagram and minimum nodes/edges.
2. Choose layout strategy (`elk` for dense graphs, `dagre` for simple flows unless user specifies otherwise).
3. Define containers/shapes first, then connections.
4. Apply shared styles (`classes`/globs) before local overrides.
5. Use imports/composition only when requested or clearly beneficial.
6. Validate and format before finalizing.

## D2 Rules (Strict)

- Use documented operators only: `--`, `->`, `<-`, `<->`.
- Connect by key, not label.
- Quote reserved/special keys when needed.
- Keep paths unambiguous for nested containers.
- Use `null` intentionally for deletions.

## CLI

```bash
d2 fmt diagram.d2
d2 validate diagram.d2
d2 diagram.d2 diagram.svg
```

Optional exports: `pdf`, `pptx`, `gif`, `txt` when requested.

## Response Contract

Always:
1. Return one complete `.d2` file in a fenced `d2` block (unless user asks partial).
2. Include `Assumptions` when details are missing.
3. Include one short layout rationale.
4. Include one recommended render command (and optional validate command).
5. Preserve semantics first when refactoring existing diagrams.

## Compatibility

- If co-triggered with review-oriented skills, treat review feedback as internal constraints.
- Final user-facing output remains this skill’s `.d2` response contract unless user requests a separate review artifact.
