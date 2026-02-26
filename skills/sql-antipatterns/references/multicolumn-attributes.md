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
2. Backfill existing repeating columns.

```sql
INSERT INTO bug_tags (bug_id, tag_position, tag)
SELECT bug_id, pos, tag
FROM (
  SELECT bug_id, 1 AS pos, tag1 AS tag FROM bugs
  UNION ALL
  SELECT bug_id, 2 AS pos, tag2 AS tag FROM bugs
  UNION ALL
  SELECT bug_id, 3 AS pos, tag3 AS tag FROM bugs
) s
WHERE tag IS NOT NULL AND btrim(tag) <> ''
ON CONFLICT DO NOTHING;
```

3. Move writes to child rows and reads to joins.
4. Verify parity, then drop legacy columns.

## Rollback Considerations
- Keep legacy `tag1`/`tag2`/`tag3` columns until parity checks pass for migrated rows.
- If cutover fails, switch reads/writes back to legacy columns and rebuild `bug_tags`.
- Retain `(bug_id, tag_position)` mapping from backfill so replay is deterministic.

## Version and Engine Caveats
- Pattern is engine-agnostic, but index types, generated columns, and conflict-handling syntax vary by engine.
- If order is irrelevant, omit `tag_position` and use `PRIMARY KEY (bug_id, tag)` instead.
- For very high-cardinality tags, review index bloat and consider fillfactor/maintenance strategy.
