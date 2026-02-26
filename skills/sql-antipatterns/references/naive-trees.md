# Naive Trees
## Objective
Represent hierarchical data so descendant/ancestor traversal, subtree reads, and branch mutations are reliable and efficient.

## Antipattern
Use a plain adjacency list (`parent_id`) but handle hierarchy logic with fixed-depth self-joins or application-side tree reconstruction instead of recursive SQL.

## Why It Fails
- Fixed-depth joins break as soon as real depth exceeds assumptions.
- Loading entire trees into application memory wastes I/O for subtree-only operations.
- Deletes and moves are brittle without consistent descendant discovery.
- Missing cycle guards can produce infinite recursion or duplicate paths.

## How To Detect
- Self-referencing FK exists, but recursive CTEs are absent from query workload.
- Query code contains repeated `JOIN table t1 ... JOIN table t2 ... JOIN table t3 ...`.
- Branch operations are implemented with ad-hoc scripts.

```sql
SELECT conrelid::regclass AS table_name, conname
FROM pg_constraint
WHERE contype = 'f'
  AND conrelid = confrelid;
```

## Legitimate Exceptions
- Guaranteed shallow depth (for example, max depth 2) and stable requirements.
- Very small trees where full-table reads are acceptable.
- Temporary analytical snapshots with no branch mutation operations.

## Preferred Design
Default to adjacency list plus recursive CTE traversal. Move to closure table when high-frequency ancestor/descendant queries and branch moves are both core workloads.

```sql
CREATE TABLE categories (
  category_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  parent_id   BIGINT REFERENCES categories(category_id) ON DELETE CASCADE,
  name        TEXT NOT NULL
);

CREATE INDEX categories_parent_id_idx ON categories(parent_id);
```

## PostgreSQL Implementation Patterns
```sql
-- Descendants of a root node (PostgreSQL 14+ SEARCH/CYCLE syntax)
WITH RECURSIVE category_tree(category_id, parent_id, name, depth) AS (
  SELECT c.category_id, c.parent_id, c.name, 0
  FROM categories c
  WHERE c.category_id = 42

  UNION ALL

  SELECT c.category_id, c.parent_id, c.name, ct.depth + 1
  FROM categories c
  JOIN category_tree ct ON c.parent_id = ct.category_id
)
SEARCH DEPTH FIRST BY category_id SET order_col
CYCLE category_id SET is_cycle USING path_col
SELECT category_id, parent_id, name, depth
FROM category_tree
WHERE NOT is_cycle
ORDER BY order_col;
```

```sql
-- Ancestors of a node
WITH RECURSIVE ancestors(category_id, parent_id, depth) AS (
  SELECT c.category_id, c.parent_id, 0
  FROM categories c
  WHERE c.category_id = 42

  UNION ALL

  SELECT p.category_id, p.parent_id, a.depth + 1
  FROM categories p
  JOIN ancestors a ON p.category_id = a.parent_id
)
SELECT *
FROM ancestors
ORDER BY depth;
```

Notes:
- `SEARCH` chooses stable depth-first or breadth-first ordering and adds an implicit sort column.
- `CYCLE` adds implicit cycle marker/path columns and prevents infinite loops when used with `WHERE NOT is_cycle`.

## Migration Pattern
```sql
-- 0) Preflight (fail-closed): detect cycles before backfill.
-- PostgreSQL 14+:
WITH RECURSIVE probe(category_id, parent_id) AS (
  SELECT c.category_id, c.parent_id
  FROM categories c

  UNION ALL

  SELECT c.category_id, c.parent_id
  FROM categories c
  JOIN probe p ON c.category_id = p.parent_id
)
CYCLE category_id SET is_cycle USING cycle_path
SELECT category_id, cycle_path
FROM probe
WHERE is_cycle
LIMIT 1;

DO $$
BEGIN
  IF EXISTS (
    WITH RECURSIVE probe(category_id, parent_id) AS (
      SELECT c.category_id, c.parent_id
      FROM categories c

      UNION ALL

      SELECT c.category_id, c.parent_id
      FROM categories c
      JOIN probe p ON c.category_id = p.parent_id
    )
    CYCLE category_id SET is_cycle USING cycle_path
    SELECT 1
    FROM probe
    WHERE is_cycle
    LIMIT 1
  ) THEN
    RAISE EXCEPTION 'Preflight failed: cycle detected in categories';
  END IF;
END
$$;

-- PostgreSQL <14 fallback:
WITH RECURSIVE probe(category_id, parent_id, path, is_cycle) AS (
  SELECT c.category_id, c.parent_id, ARRAY[c.category_id], false
  FROM categories c

  UNION ALL

  SELECT c.category_id, c.parent_id, p.path || c.category_id, c.category_id = ANY(p.path)
  FROM categories c
  JOIN probe p ON c.category_id = p.parent_id
  WHERE NOT p.is_cycle
)
SELECT category_id, path
FROM probe
WHERE is_cycle
LIMIT 1;

DO $$
BEGIN
  IF EXISTS (
    WITH RECURSIVE probe(category_id, parent_id, path, is_cycle) AS (
      SELECT c.category_id, c.parent_id, ARRAY[c.category_id], false
      FROM categories c

      UNION ALL

      SELECT c.category_id, c.parent_id, p.path || c.category_id, c.category_id = ANY(p.path)
      FROM categories c
      JOIN probe p ON c.category_id = p.parent_id
      WHERE NOT p.is_cycle
    )
    SELECT 1
    FROM probe
    WHERE is_cycle
    LIMIT 1
  ) THEN
    RAISE EXCEPTION 'Preflight failed: cycle detected in categories';
  END IF;
END
$$;

-- 1) Keep adjacency list as canonical write model.
-- 2) Add closure table for fast ancestor/descendant and reverse lookups.
CREATE TABLE category_paths (
  ancestor_id   BIGINT NOT NULL REFERENCES categories(category_id) ON DELETE CASCADE,
  descendant_id BIGINT NOT NULL REFERENCES categories(category_id) ON DELETE CASCADE,
  depth         INT NOT NULL CHECK (depth >= 0),
  PRIMARY KEY (ancestor_id, descendant_id)
);

-- 3) Backfill transitive closure with explicit cycle guard.
WITH RECURSIVE walk(ancestor_id, descendant_id, depth, path, is_cycle) AS (
  SELECT c.category_id, c.category_id, 0, ARRAY[c.category_id], false
  FROM categories c

  UNION ALL

  SELECT
    w.ancestor_id,
    c.category_id,
    w.depth + 1,
    w.path || c.category_id,
    c.category_id = ANY(w.path)
  FROM walk w
  JOIN categories c ON c.parent_id = w.descendant_id
  WHERE NOT w.is_cycle
)
INSERT INTO category_paths (ancestor_id, descendant_id, depth)
SELECT ancestor_id, descendant_id, depth
FROM walk
WHERE NOT is_cycle
ON CONFLICT (ancestor_id, descendant_id) DO UPDATE
SET depth = EXCLUDED.depth;

-- 4) Add reverse-lookup index after backfill to avoid backfill maintenance overhead.
CREATE INDEX category_paths_descendant_id_idx
  ON category_paths (descendant_id, ancestor_id);
```

## Rollback Considerations
- Keep `categories.parent_id` as the source of truth until closure parity checks pass.
- If cutover fails, stop closure-table reads and return to recursive CTE reads from adjacency data.
- If backfill is partial or bad, `TRUNCATE category_paths` and rerun after fixing cycle errors.

## Version and Engine Caveats
- `SEARCH` and `CYCLE` are available in PostgreSQL 14+.
- On PostgreSQL <14, emulate cycle detection with an array path (`id = ANY(path)`) in a recursive CTE.
- Recursive CTE support exists in many engines, but `SEARCH`/`CYCLE` syntax and behavior are not portable.
