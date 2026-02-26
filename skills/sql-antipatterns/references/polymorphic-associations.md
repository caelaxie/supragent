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
2. Run preflight checks and fail closed on unsupported types or dangling references.

```sql
-- Preflight A: unsupported parent_type values.
SELECT DISTINCT parent_type
FROM comments
WHERE parent_type IS NULL
   OR parent_type NOT IN ('BUG', 'FEATURE_REQUEST');

-- Preflight B: dangling parent references.
SELECT c.comment_id, c.parent_type, c.parent_id
FROM comments c
LEFT JOIN bugs b
  ON c.parent_type = 'BUG'
 AND b.bug_id = c.parent_id
LEFT JOIN feature_requests fr
  ON c.parent_type = 'FEATURE_REQUEST'
 AND fr.feature_request_id = c.parent_id
WHERE (c.parent_type = 'BUG' AND b.bug_id IS NULL)
   OR (c.parent_type = 'FEATURE_REQUEST' AND fr.feature_request_id IS NULL);
-- Abort if either query returns rows.

-- Fail closed: stop before backfill if either preflight condition exists.
DO $$
BEGIN
  IF EXISTS (
    SELECT 1
    FROM comments
    WHERE parent_type IS NULL
       OR parent_type NOT IN ('BUG', 'FEATURE_REQUEST')
  ) THEN
    RAISE EXCEPTION 'Unsupported or NULL parent_type values found in comments';
  END IF;

  IF EXISTS (
    SELECT 1
    FROM comments c
    LEFT JOIN bugs b
      ON c.parent_type = 'BUG'
     AND b.bug_id = c.parent_id
    LEFT JOIN feature_requests fr
      ON c.parent_type = 'FEATURE_REQUEST'
     AND fr.feature_request_id = c.parent_id
    WHERE (c.parent_type = 'BUG' AND b.bug_id IS NULL)
       OR (c.parent_type = 'FEATURE_REQUEST' AND fr.feature_request_id IS NULL)
  ) THEN
    RAISE EXCEPTION 'Dangling comment parent references found';
  END IF;
END $$;

-- 3) Backfill from legacy (parent_type, parent_id).
UPDATE comments
SET bug_id = parent_id
WHERE parent_type = 'BUG';

UPDATE comments
SET feature_request_id = parent_id
WHERE parent_type = 'FEATURE_REQUEST';

-- 4) Add constraints with low-disruption rollout.
ALTER TABLE comments
  ADD CONSTRAINT comments_bug_id_fkey
  FOREIGN KEY (bug_id) REFERENCES bugs(bug_id) ON DELETE CASCADE
  NOT VALID;

ALTER TABLE comments
  ADD CONSTRAINT comments_feature_request_id_fkey
  FOREIGN KEY (feature_request_id) REFERENCES feature_requests(feature_request_id) ON DELETE CASCADE
  NOT VALID;

ALTER TABLE comments
  ADD CONSTRAINT comments_exactly_one_parent_chk
  CHECK (num_nonnulls(bug_id, feature_request_id) = 1)
  NOT VALID;

-- Add relationship-path indexes before validation/cutover.
CREATE INDEX IF NOT EXISTS comments_bug_id_idx
  ON comments (bug_id)
  WHERE bug_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS comments_feature_request_id_idx
  ON comments (feature_request_id)
  WHERE feature_request_id IS NOT NULL;

-- If you choose CREATE INDEX CONCURRENTLY for large tables, run it outside BEGIN/COMMIT.

ALTER TABLE comments
  VALIDATE CONSTRAINT comments_bug_id_fkey;

ALTER TABLE comments
  VALIDATE CONSTRAINT comments_feature_request_id_fkey;

ALTER TABLE comments
  VALIDATE CONSTRAINT comments_exactly_one_parent_chk;

-- 5) Drift control: dual-write old and new columns, then verify parity before drop.
SELECT comment_id
FROM comments
WHERE (parent_type = 'BUG' AND bug_id IS DISTINCT FROM parent_id)
   OR (parent_type = 'FEATURE_REQUEST' AND feature_request_id IS DISTINCT FROM parent_id)
LIMIT 1;
-- Require zero rows before dropping parent_type/parent_id.
```

3. Switch application reads/writes, keep sync/parity checks during cutover, then drop `parent_type` and `parent_id`.

## Rollback Considerations
- Keep legacy `parent_type`/`parent_id` populated until parity checks stay clean through cutover.
- If rollout fails, revert reads/writes to legacy columns but keep `bug_id`/`feature_request_id` as shadow data.
- Preserve parity query output; it identifies rows requiring resync before another drop attempt.

## Version and Engine Caveats
- `num_nonnulls()` is PostgreSQL-specific; other engines may require equivalent `CASE` arithmetic in `CHECK`.
- Partial indexes are PostgreSQL features (other engines may offer different filtered-index syntax).
- If parent set grows frequently, nullable-FK-column design can become unwieldy; prefer mapping tables or a true supertype.
