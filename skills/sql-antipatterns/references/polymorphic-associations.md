# Polymorphic Associations

## Objective
Let one child entity relate to different parent types while keeping real referential integrity.

## Antipattern
Store parent identity as `(parent_type, parent_id)` and treat it as a "conditional foreign key."

```sql
CREATE TABLE comments (
  comment_id    bigserial PRIMARY KEY,
  parent_type   text NOT NULL,
  parent_id     bigint NOT NULL,
  comment_text  text NOT NULL
);
```

## Why It Fails
- The database cannot enforce that `parent_id` exists in the table implied by `parent_type`.
- Cascades and deletes become manual, so orphan rows are common.
- Refactors of table/type names break data conventions.
- Queries need conditional joins and branch logic, which hurts readability and plans.

## How To Detect
- Columns named like `*_type` and `*_id` used together as one relationship.
- No actual `FOREIGN KEY` on the parent reference.
- ORM generic-relation pattern mirrored directly in physical schema.

## Legitimate Exceptions
- Cross-service references where parent rows are intentionally outside the local database boundary.
- Temporary ingestion/staging tables before normalization.
- Append-only logs where referential checks are intentionally deferred.

## Preferred Design
- Preferred: keep child facts in one table and model each parent link with explicit FK-backed mapping tables.
- Fixed small parent set: use nullable FK columns on the child table and enforce exactly one parent with `CHECK (num_nonnulls(...) = 1)`.
- If parents share a true supertype table, reference that supertype key directly.

## PostgreSQL Implementation Patterns
Fixed parent set with nullable FKs and exact-one check:

```sql
CREATE TABLE comments (
  comment_id            bigserial PRIMARY KEY,
  bug_id                bigint REFERENCES bugs(bug_id) ON DELETE CASCADE,
  feature_request_id    bigint REFERENCES feature_requests(feature_request_id) ON DELETE CASCADE,
  comment_text          text NOT NULL,
  created_at            timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT comments_exactly_one_parent_chk
    CHECK (num_nonnulls(bug_id, feature_request_id) = 1)
);
```

Index each relationship path:

```sql
CREATE INDEX comments_bug_id_idx
  ON comments (bug_id)
  WHERE bug_id IS NOT NULL;

CREATE INDEX comments_feature_request_id_idx
  ON comments (feature_request_id)
  WHERE feature_request_id IS NOT NULL;
```

Alternative: mapping tables per parent type:

```sql
CREATE TABLE bug_comments (
  comment_id  bigint PRIMARY KEY REFERENCES comments(comment_id) ON DELETE CASCADE,
  bug_id      bigint NOT NULL REFERENCES bugs(bug_id) ON DELETE CASCADE
);

CREATE TABLE feature_request_comments (
  comment_id          bigint PRIMARY KEY REFERENCES comments(comment_id) ON DELETE CASCADE,
  feature_request_id  bigint NOT NULL REFERENCES feature_requests(feature_request_id) ON DELETE CASCADE
);
```

## Migration Pattern
1. Add explicit nullable FK columns for each allowed parent table.
2. Backfill from legacy `(parent_type, parent_id)` columns.

```sql
UPDATE comments
SET bug_id = parent_id
WHERE parent_type = 'BUG';

UPDATE comments
SET feature_request_id = parent_id
WHERE parent_type = 'FEATURE_REQUEST';
```

3. Add FK constraints and `CHECK (num_nonnulls(...) = 1)`.
4. Add partial indexes on each FK column.
5. Switch application reads/writes, then drop `parent_type` and `parent_id`.

## Version and Engine Caveats
- `num_nonnulls()` is PostgreSQL-specific; other engines may require equivalent `CASE` arithmetic in `CHECK`.
- Partial indexes are PostgreSQL features (other engines may offer different filtered-index syntax).
- If parent set grows frequently, nullable-FK-column design can become unwieldy; prefer mapping tables or a true supertype.
