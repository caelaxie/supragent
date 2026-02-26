# Entity-Attribute-Value

## Objective
Support variable attributes without giving up relational typing, constraints, and predictable queries.

## Antipattern
Store core entity facts as metadata rows, typically `(entity_id, attr_name, attr_value)`.

```sql
CREATE TABLE issue_attributes (
  issue_id    bigint NOT NULL,
  attr_name   text NOT NULL,
  attr_value  text NOT NULL
);
```

## Why It Fails
- Every read becomes string matching plus pivot/reconstruction logic.
- `attr_value` is usually text, so type safety and domain validation move into application code.
- `NOT NULL`, `CHECK`, and `FOREIGN KEY` rules cannot target one attribute cleanly.
- Naming drift (`report_date` vs `date_reported`) creates semantic duplicates.

## How To Detect
- A central table with columns like `*_id`, `name`, `value`.
- Frequent SQL using `CASE`, filtered aggregates, or repeated self-joins to rebuild one logical row.
- Business rules enforced in app code because schema constraints cannot express them.

## Legitimate Exceptions
- Short-lived migration states.
- Event/telemetry payload capture where values are not core relational facts.
- A truly open-ended "extension" field, while core attributes stay typed columns.

## Preferred Design
- Finite subtype set: use explicit subtype tables (class-table or concrete-table inheritance).
- Open-ended tail: use a relational base row plus one `jsonb` extension column.
- Keep high-value predicates (status, ownership, dates, joins) as normal typed columns.

## PostgreSQL Implementation Patterns
```sql
CREATE TABLE issues (
  issue_id      bigserial PRIMARY KEY,
  issue_type    text NOT NULL CHECK (issue_type IN ('BUG', 'FEATURE')),
  status        text NOT NULL,
  reported_by   bigint NOT NULL,
  attributes    jsonb NOT NULL DEFAULT '{}'::jsonb
);
```

Choose one GIN operator class based on query shape:

```sql
-- Default: broader operator support (?, ?|, ?&, @>, @?, @@), usually larger index.
CREATE INDEX issues_attributes_gin_ops_idx
  ON issues USING gin (attributes jsonb_ops);

-- Containment/jsonpath focused (@>, @?, @@), usually smaller/faster for those queries.
CREATE INDEX issues_attributes_gin_path_idx
  ON issues USING gin (attributes jsonb_path_ops);
```

Expression indexes for hot predicates:

```sql
CREATE INDEX issues_attr_severity_idx
  ON issues ((attributes ->> 'severity'));

CREATE INDEX issues_attr_business_value_idx
  ON issues (((attributes ->> 'business_value')::int));
```

Example query shapes:

```sql
SELECT issue_id
FROM issues
WHERE attributes @> '{"severity":"critical"}';

SELECT issue_id
FROM issues
WHERE ((attributes ->> 'business_value')::int) >= 8;
```

## Migration Pattern
1. Create target tables (typed subtype schema, or base table with `jsonb` attributes).
2. Backfill EAV rows into per-entity documents.

```sql
INSERT INTO issues (issue_id, issue_type, status, reported_by, attributes)
SELECT
  issue_id,
  MAX(attr_value) FILTER (WHERE attr_name = 'issue_type') AS issue_type,
  MAX(attr_value) FILTER (WHERE attr_name = 'status') AS status,
  (MAX(attr_value) FILTER (WHERE attr_name = 'reported_by'))::bigint AS reported_by,
  jsonb_object_agg(attr_name, attr_value) AS attributes
FROM issue_attributes
GROUP BY issue_id;
```

3. Promote frequently queried JSON keys into typed columns where needed.
4. Dual-write briefly, validate parity, then retire the EAV table.

## Version and Engine Caveats
- `jsonb`, GIN operator classes (`jsonb_ops`/`jsonb_path_ops`), and `@?`/`@@` are PostgreSQL features.
- `jsonb_path_ops` does not support key-exists operators (`?`, `?|`, `?&`).
- Expression indexes are widely available in PostgreSQL, but syntax and optimizer behavior differ by engine.
