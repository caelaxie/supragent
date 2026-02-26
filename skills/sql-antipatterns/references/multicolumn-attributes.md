# Multicolumn Attributes

## Objective
Represent multi-value attributes (tags, phones, skills) without repeating-group columns.

## Antipattern
Store interchangeable values in numbered columns like `tag1`, `tag2`, `tag3`.

```sql
CREATE TABLE bugs (
  bug_id        bigserial PRIMARY KEY,
  summary       text NOT NULL,
  tag1          text,
  tag2          text,
  tag3          text
);
```

## Why It Fails
- Hard upper bound forces repeated schema changes.
- Queries require repetitive `OR` predicates across columns.
- Duplicate prevention and ordering rules are difficult to enforce.
- Writes require "find next free slot" logic, which is fragile under concurrency.

## How To Detect
- Column families named `value1`, `value2`, `value3` for one logical attribute.
- Frequent requests to "add one more column" for the same attribute type.
- Query patterns like `WHERE tag1 = ? OR tag2 = ? OR tag3 = ?`.

## Legitimate Exceptions
- Distinct role-based columns (for example, `reporter_id`, `assignee_id`) where each column has different semantics.
- Fixed-width technical vectors where position is intrinsic and not a repeating business attribute.

## Preferred Design
Use a dependent child table with one row per value and explicit keys:
- Parent FK guarantees ownership and cleanup behavior.
- Composite primary key enforces positional uniqueness.
- Additional unique constraints enforce value-level business rules.

## PostgreSQL Implementation Patterns
```sql
CREATE TABLE bugs (
  bug_id    bigserial PRIMARY KEY,
  summary   text NOT NULL
);

CREATE TABLE bug_tags (
  bug_id         bigint NOT NULL REFERENCES bugs(bug_id) ON DELETE CASCADE,
  tag_position   smallint NOT NULL CHECK (tag_position >= 1),
  tag            text NOT NULL,
  PRIMARY KEY (bug_id, tag_position),
  CONSTRAINT bug_tags_unique_value_per_bug UNIQUE (bug_id, tag)
);

CREATE INDEX bug_tags_tag_idx ON bug_tags (tag);
```

Usage:

```sql
INSERT INTO bug_tags (bug_id, tag_position, tag) VALUES
  (42, 1, 'crash'),
  (42, 2, 'performance');

SELECT b.bug_id, b.summary
FROM bugs b
JOIN bug_tags t ON t.bug_id = b.bug_id
WHERE t.tag = 'performance';
```

## Migration Pattern
1. Create the child table and indexes.
2. Stage legacy values and capture duplicate-value conflicts before loading.
3. Fail closed if duplicate values exist for a bug.
4. Backfill only after the gate passes.

```sql
-- Replace MIGRATION_RUN_ID with your deployment run id.
CREATE TABLE IF NOT EXISTS bug_tag_rejects (
  reject_id         BIGSERIAL PRIMARY KEY,
  migration_run_id  TEXT NOT NULL,
  bug_id            BIGINT NOT NULL,
  tag               TEXT NOT NULL,
  reject_reason     TEXT NOT NULL,
  rejected_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS bug_tag_rejects_run_idx
  ON bug_tag_rejects (migration_run_id);

CREATE TEMP TABLE staged_bug_tags AS
SELECT bug_id, pos AS tag_position, btrim(tag) AS tag
FROM (
  SELECT bug_id, 1 AS pos, tag1 AS tag FROM bugs
  UNION ALL
  SELECT bug_id, 2 AS pos, tag2 AS tag FROM bugs
  UNION ALL
  SELECT bug_id, 3 AS pos, tag3 AS tag FROM bugs
) s
WHERE tag IS NOT NULL
  AND btrim(tag) <> '';

-- Capture duplicate values per bug before any insert; do not silently dedupe.
INSERT INTO bug_tag_rejects (migration_run_id, bug_id, tag, reject_reason)
SELECT 'MIGRATION_RUN_ID', bug_id, tag, 'duplicate_tag_value_for_bug'
FROM staged_bug_tags
GROUP BY bug_id, tag
HAVING COUNT(*) > 1;

DO $$
BEGIN
  IF EXISTS (
    SELECT 1
    FROM bug_tag_rejects
    WHERE migration_run_id = 'MIGRATION_RUN_ID'
  ) THEN
    RAISE EXCEPTION
      'Backfill rejected duplicate tag values; inspect bug_tag_rejects for migration_run_id=%',
      'MIGRATION_RUN_ID';
  END IF;
END $$;

INSERT INTO bug_tags (bug_id, tag_position, tag)
SELECT bug_id, tag_position, tag
FROM staged_bug_tags
ON CONFLICT (bug_id, tag_position) DO UPDATE
SET tag = EXCLUDED.tag;

-- Cleanup reject rows only after successful backfill/parity checks.
DELETE FROM bug_tag_rejects
WHERE migration_run_id = 'MIGRATION_RUN_ID';
```

5. Move writes to child rows and reads to joins.
6. Verify parity, then drop legacy columns.

## Rollback Considerations
- Keep legacy `tag1`/`tag2`/`tag3` columns until parity checks pass for migrated rows.
- If cutover fails, switch reads/writes back to legacy columns and rebuild `bug_tags`.
- Retain `(bug_id, tag_position)` mapping from backfill so replay is deterministic.

## Version and Engine Caveats
- Pattern is engine-agnostic, but index types, generated columns, and conflict-handling syntax vary by engine.
- If order is irrelevant, omit `tag_position` and use `PRIMARY KEY (bug_id, tag)` instead.
- For very high-cardinality tags, review index bloat and consider fillfactor/maintenance strategy.
