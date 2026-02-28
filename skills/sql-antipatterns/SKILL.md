---
name: sql-antipatterns
description: Use when designing, reviewing, or writing SQL tables, schemas, and queries to detect and remediate SQL anti-patterns with PostgreSQL-first, constraint-backed designs and fail-closed migration guidance.
---

# SQL Anti-Patterns

## Goal

Detect SQL anti-patterns and return safe PostgreSQL-first remediations with verifiable migration plans.

## Default Posture

- Preserve relational guarantees (types, keys, constraints).
- Prefer one logical model + physical optimization (indexes/partitioning), not schema cloning.
- Keep migrations reversible and fail-closed.

## Workflow

1. Classify mode: `design`, `review`, or `migration`.
2. Always read `references/review-checklist.md`.
3. For migration/production DDL/backfill/cutover, also read `references/migration-playbook.md`.
4. Load only symptom-relevant anti-pattern references.
5. Prioritize integrity risk before operational risk.

## Routing (symptom -> reference)

- CSV IDs / comma-separated IDs -> `references/jaywalking.md`
- Tree traversal pain / fixed-depth joins -> `references/naive-trees.md`
- Missing FKs / app-side integrity checks / orphans -> `references/keyless-entry.md`
- EAV core model -> `references/entity-attribute-value.md`
- `*_type + *_id` polymorphism -> `references/polymorphic-associations.md`
- Repeating columns (`tag1`, `phone1`, etc.) -> `references/multicolumn-attributes.md`
- Table/column schema cloning by year/tenant -> `references/metadata-tribbles.md`
- Phased rollout/cutover template -> `references/migration-playbook.md`

## PostgreSQL Defaults

- Use FK-backed relationships and index referencing FK columns on write-heavy paths.
- Use recursive CTEs for hierarchies (`SEARCH/CYCLE` on PG14+ when needed).
- Validate partition pruning with `EXPLAIN (ANALYZE, BUFFERS)`.
- For dynamic attributes, keep relational core + bounded `jsonb` tail.

## Response Contract

For each anti-pattern, provide:
- `Signal`
- `Risk`
- `Preferred design`
- `Implementation` (concrete SQL)
- `Migration` (phased steps + validation + rollback trigger)
- `Caveats` (version/engine constraints)

## References

- `references/review-checklist.md`
- `references/migration-playbook.md`
- `references/jaywalking.md`
- `references/naive-trees.md`
- `references/keyless-entry.md`
- `references/entity-attribute-value.md`
- `references/polymorphic-associations.md`
- `references/multicolumn-attributes.md`
- `references/metadata-tribbles.md`
