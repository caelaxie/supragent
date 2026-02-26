---
name: sql-antipatterns
description: Use when designing, reviewing, or writing SQL tables, schemas, and queries to detect and remediate SQL anti-patterns with PostgreSQL-first, constraint-backed designs and fail-closed migration guidance.
---

# SQL Anti-Patterns

This skill is a PostgreSQL-first playbook for anti-pattern detection, remediation design, and safe migration planning.

Default posture:
- Preserve relational guarantees (types, keys, constraints).
- Prefer one logical model plus physical optimization (indexes/partitioning), not schema cloning.
- Keep migrations reversible and verifiable.
- Prefer fail-closed migration checks over silent coercion/skips.

## Workflow

1. Identify the request mode:
- Design: propose schema/query patterns that avoid anti-patterns.
- Review: detect anti-pattern signals and rank by risk.
- Migration: provide phased cutover and rollback path.

2. Load baseline review guidance:
- Always read `references/review-checklist.md` for schema/code reviews.
- For any migration or production DDL/backfill/cutover request, also read `references/migration-playbook.md`.

3. Load only relevant anti-pattern references:
- Do not load all references by default.
- Select by symptom using the routing table below.

4. Build a decision-complete response:
- Findings/signals.
- Preferred design with concrete SQL.
- Migration path and validation checks.
- Version/engine caveats.

5. If multiple anti-patterns appear:
- Prioritize by integrity risk first (missing FKs, polymorphic refs, EAV core-data misuse).
- Then prioritize by operational risk (partition mistakes, repeating groups, scaling pain).

## Routing Table

- Comma-separated IDs in one column or CSV joins/parsing:
  Read `references/jaywalking.md`.

- Tree/hierarchy traversal pain, fixed-depth joins, ancestor/descendant queries:
  Read `references/naive-trees.md`.

- Missing foreign keys, app-side referential checks, orphan cleanup scripts, or slow parent deletes/updates caused by unindexed child FK columns:
  Read `references/keyless-entry.md`.

- `(entity_id, attr_name, attr_value)` core model, heavy pivots/stringly-typed logic:
  Read `references/entity-attribute-value.md`.

- `*_type + *_id` parent polymorphism:
  Read `references/polymorphic-associations.md`.

- `tag1/tag2/tag3` or `phone1/phone2` repeating groups:
  Read `references/multicolumn-attributes.md`.

- Table-per-year/tenant or column-per-year/status schema cloning:
  Read `references/metadata-tribbles.md`.

- Need phased rollout/cutover/rollback template:
  Read `references/migration-playbook.md`.

## Trigger Phrases (User Language)

- "comma-separated IDs", "CSV IDs in one column", "array of IDs in text"
- "custom fields table", "name/value attributes", "EAV"
- "generic relation", "type + id parent", "polymorphic parent"
- "orphans cleanup job", "missing FKs", "foreign key errors in app only"
- "tag1/tag2 columns", "phone1 phone2", "add one more tag column"
- "table per year", "tenant-specific tables", "new yearly table"
- "ALTER TABLE on huge table", "backfill then cutover", "dual-write migration"

## Reference Files

- `references/review-checklist.md`
- `references/migration-playbook.md`
- `references/jaywalking.md`
- `references/naive-trees.md`
- `references/keyless-entry.md`
- `references/entity-attribute-value.md`
- `references/polymorphic-associations.md`
- `references/multicolumn-attributes.md`
- `references/metadata-tribbles.md`

## PostgreSQL Defaults

- Prefer FK-backed relationships and explicit indexing of referencing FK columns on write-heavy paths.
- For recursive hierarchy queries, use recursive CTEs; use `SEARCH`/`CYCLE` on PostgreSQL 14+ when needed.
- For partitioning, query the parent table and confirm pruning with `EXPLAIN (ANALYZE, BUFFERS)`.
- For dynamic attributes, prefer relational core + bounded `jsonb` tail with deliberate index/operator-class choices.

## Response Contract

For each identified anti-pattern, provide:
- `Signal`: how it was detected.
- `Risk`: integrity/performance/operational impact.
- `Preferred design`: target relational model.
- `Implementation`: concrete SQL DDL/DML/query patterns.
- `Migration`: phased plan + validation checks + rollback condition.
- `Caveats`: version/engine constraints.

## Maintenance

When adding a new anti-pattern:
1. Add `references/<name>.md` using the standard section contract:
- `# <Antipattern Name>`
- `## Objective`
- `## Antipattern`
- `## Why It Fails`
- `## How To Detect`
- `## Legitimate Exceptions`
- `## Preferred Design`
- `## PostgreSQL Implementation Patterns`
- `## Migration Pattern`
- `## Rollback Considerations`
- `## Version and Engine Caveats`
2. Add it to `## Reference Files`.
3. Add a symptom route in `## Routing Table`.
4. Update `references/review-checklist.md` when the new anti-pattern should be covered by baseline review heuristics.
