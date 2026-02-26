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
  ON issues (
    (
      CASE
        WHEN (attributes ->> 'business_value') ~ '^-?[0-9]+(\.[0-9]+)?$'
          THEN (attributes ->> 'business_value')::numeric
      END
    )
  );
```

Example query shapes:

```sql
SELECT issue_id
FROM issues
WHERE attributes @> '{"severity":"critical"}';

SELECT issue_id
FROM issues
WHERE (
  CASE
    WHEN (attributes ->> 'business_value') ~ '^-?[0-9]+(\.[0-9]+)?$'
      THEN (attributes ->> 'business_value')::numeric
  END
) >= 8;
```

## Migration Pattern
1. Create target tables (typed subtype schema, or base table with `jsonb` attributes).
2. Run fail-closed prechecks for promoted core attributes (`issue_type`, `status`, `reported_by`).

```sql
-- Precheck A: conflicting duplicates for core attrs.
SELECT issue_id, attr_name, array_agg(DISTINCT attr_value ORDER BY attr_value) AS values_seen
FROM issue_attributes
WHERE attr_name IN ('issue_type', 'status', 'reported_by')
GROUP BY issue_id, attr_name
HAVING COUNT(DISTINCT attr_value) > 1;

-- Precheck B: avoid silent collapse by requiring exactly one core row per issue.
SELECT issue_id
FROM issue_attributes
GROUP BY issue_id
HAVING COUNT(*) FILTER (WHERE attr_name = 'issue_type') <> 1
    OR COUNT(*) FILTER (WHERE attr_name = 'status') <> 1
    OR COUNT(*) FILTER (WHERE attr_name = 'reported_by') <> 1;

-- Precheck C: guard BIGINT cast for reported_by.
SELECT issue_id, attr_value AS reported_by_raw
FROM issue_attributes
WHERE attr_name = 'reported_by'
  AND NOT (
    attr_value ~ '^[0-9]+$'
    AND (
      length(attr_value) < 19
      OR (length(attr_value) = 19 AND attr_value <= '9223372036854775807')
    )
  );

-- Precheck D: fail closed on duplicate keys before jsonb_object_agg.
SELECT issue_id, attr_name, COUNT(*) AS row_count
FROM issue_attributes
GROUP BY issue_id, attr_name
HAVING COUNT(*) > 1;
```

3. Backfill only after all prechecks return zero rows.

```sql
WITH per_issue AS (
  SELECT
    issue_id,
    MAX(attr_value) FILTER (WHERE attr_name = 'issue_type') AS issue_type,
    MAX(attr_value) FILTER (WHERE attr_name = 'status') AS status,
    MAX(attr_value) FILTER (WHERE attr_name = 'reported_by') AS reported_by_raw,
    jsonb_object_agg(attr_name, attr_value ORDER BY attr_name) AS attributes
  FROM issue_attributes
  GROUP BY issue_id
)
INSERT INTO issues (issue_id, issue_type, status, reported_by, attributes)
SELECT
  issue_id,
  issue_type,
  status,
  reported_by_raw::bigint AS reported_by,
  attributes
FROM per_issue
ON CONFLICT (issue_id) DO UPDATE
SET
  issue_type = EXCLUDED.issue_type,
  status = EXCLUDED.status,
  reported_by = EXCLUDED.reported_by,
  attributes = EXCLUDED.attributes;
```

4. Promote frequently queried JSON keys into typed columns where needed.
5. Dual-write briefly, validate parity, then retire the EAV table.

## Rollback Considerations
- Keep `issue_attributes` readable/writable until parity checks pass for row counts and core columns.
- If cutover fails, switch reads back to EAV and truncate/rebuild `issues` from corrected source rows.
- Keep precheck outputs for triage; they identify rows that must be fixed before reattempt.

## Version and Engine Caveats
- `jsonb`, GIN operator classes (`jsonb_ops`/`jsonb_path_ops`), and `@?`/`@@` are PostgreSQL features.
- `jsonb_path_ops` does not support key-exists operators (`?`, `?|`, `?&`).
- Expression indexes are widely available in PostgreSQL, but syntax and optimizer behavior differ by engine.
