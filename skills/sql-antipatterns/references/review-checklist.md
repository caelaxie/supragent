# Review Checklist

Use this as a fast schema/code review pass across SQL anti-patterns.

## Quick Checklist
- Relationships are enforced with database FKs (not only app logic).
- FK columns on write-heavy paths have supporting indexes.
- Multi-valued attributes are row-based child tables, not comma-delimited strings or numbered columns.
- Flexible attributes are constrained (`jsonb` + checks/generated columns) instead of unconstrained EAV sprawl.
- Polymorphic references (`*_type` + `*_id`) are replaced with explicit relational mappings.
- Tree/hierarchy models match query needs (recursive CTE, closure table, path, etc.) and are index-backed.
- Partitioning is physical only: one logical parent table is queried, pruning is verified with `EXPLAIN`.

## Catalog Red-Flag Queries

Coverage note: catalog queries below provide partial coverage only; treat results as triage input, not enforcement on their own.

### 1) Potential Missing FKs (`*_id` heuristic)

```sql
WITH id_cols AS (
  SELECT
    n.nspname AS schema_name,
    c.relname AS table_name,
    a.attname AS column_name,
    c.oid AS relid,
    a.attnum
  FROM pg_attribute a
  JOIN pg_class c ON c.oid = a.attrelid AND c.relkind IN ('r', 'p')
  JOIN pg_namespace n ON n.oid = c.relnamespace
  WHERE a.attnum > 0
    AND NOT a.attisdropped
    AND a.attname ~ '(^|_)id$'
    AND n.nspname NOT IN ('pg_catalog', 'information_schema')
),
fk_cols AS (
  SELECT conrelid AS relid, unnest(conkey) AS attnum
  FROM pg_constraint
  WHERE contype = 'f'
),
pk_cols AS (
  SELECT conrelid AS relid, unnest(conkey) AS attnum
  FROM pg_constraint
  WHERE contype = 'p'
)
SELECT i.schema_name, i.table_name, i.column_name
FROM id_cols i
LEFT JOIN fk_cols f ON f.relid = i.relid AND f.attnum = i.attnum
LEFT JOIN pk_cols p ON p.relid = i.relid AND p.attnum = i.attnum
WHERE f.attnum IS NULL
  AND p.attnum IS NULL
ORDER BY 1, 2, 3;
```

### 2) Referencing FK Columns Missing Supporting Index

```sql
WITH fk AS (
  SELECT
    con.oid,
    con.conrelid,
    con.conname,
    con.conkey,
    array_length(con.conkey, 1) AS fk_nkeys
  FROM pg_constraint con
  WHERE con.contype = 'f'
)
SELECT
  n.nspname AS schema_name,
  c.relname AS table_name,
  fk.conname AS fk_name,
  pg_get_constraintdef(fk.oid) AS fk_def
FROM fk
JOIN pg_class c ON c.oid = fk.conrelid
JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE n.nspname NOT IN ('pg_catalog', 'information_schema')
  AND NOT EXISTS (
    SELECT 1
    FROM pg_index i
    WHERE i.indrelid = fk.conrelid
      AND i.indisvalid
      AND i.indpred IS NULL
      AND (
        -- Strong signal: leftmost index keys match FK columns in FK order.
        (i.indkey::smallint[])[1:fk.fk_nkeys] = fk.conkey
        OR (
          -- Composite-FK fallback: same leftmost key set with different order.
          fk.fk_nkeys > 1
          AND (
            SELECT array_agg(k ORDER BY k)
            FROM unnest((i.indkey::smallint[])[1:fk.fk_nkeys]) AS t(k)
          ) = (
            SELECT array_agg(k ORDER BY k)
            FROM unnest(fk.conkey) AS t(k)
          )
        )
      )
  )
ORDER BY 1, 2, 3;
```

Note: this is a conservative baseline and intentionally ignores partial indexes. It may still report false positives/negatives because planner choices depend on workload shape, operator classes, and stats. Confirm with `EXPLAIN` on representative FK-driven delete/update workloads before adding new indexes.

### 3) FK partial-index candidates (triage only)

```sql
SELECT
  n.nspname AS schema_name,
  c.relname AS table_name,
  con.conname AS fk_name,
  irel.relname AS index_name,
  pg_get_constraintdef(con.oid) AS fk_def,
  pg_get_expr(i.indpred, i.indrelid) AS index_predicate
FROM pg_constraint con
JOIN pg_class c ON c.oid = con.conrelid
JOIN pg_namespace n ON n.oid = c.relnamespace
JOIN pg_index i ON i.indrelid = con.conrelid
JOIN pg_class irel ON irel.oid = i.indexrelid
WHERE con.contype = 'f'
  AND n.nspname NOT IN ('pg_catalog', 'information_schema')
  AND i.indisvalid
  AND i.indpred IS NOT NULL
  AND (i.indkey::smallint[])[1:array_length(con.conkey, 1)] = con.conkey
ORDER BY 1, 2, 3, 4;
```

### 4) Potential Repeating-Group Columns (suffix-numbered columns)

```sql
WITH cols AS (
  SELECT
    table_schema,
    table_name,
    column_name,
    regexp_replace(column_name, '(_)?[0-9]+$', '') AS base_name
  FROM information_schema.columns
  WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
    AND column_name ~ '(_)?[0-9]+$'
)
SELECT
  table_schema,
  table_name,
  base_name,
  array_agg(column_name ORDER BY column_name) AS numbered_columns
FROM cols
GROUP BY 1, 2, 3
HAVING count(*) >= 2
ORDER BY 1, 2, 3;
```

### 5) Potential Polymorphic Pairs (`*_type` + `*_id`)

```sql
SELECT
  c1.table_schema,
  c1.table_name,
  regexp_replace(c1.column_name, '_type$', '') AS base_name,
  c1.column_name AS type_column,
  c2.column_name AS id_column
FROM information_schema.columns c1
JOIN information_schema.columns c2
  ON c1.table_schema = c2.table_schema
 AND c1.table_name = c2.table_name
 AND regexp_replace(c1.column_name, '_type$', '') =
     regexp_replace(c2.column_name, '_id$', '')
WHERE c1.table_schema NOT IN ('pg_catalog', 'information_schema')
  AND c1.column_name LIKE '%\_type' ESCAPE '\'
  AND c2.column_name LIKE '%\_id' ESCAPE '\'
ORDER BY 1, 2, 3;
```

### 6) Potential Jaywalking Columns (`*_ids`, `*_list`, `*_csv`)

```sql
SELECT table_schema, table_name, column_name, data_type
FROM information_schema.columns
WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
  AND (
    column_name LIKE '%\_ids' ESCAPE '\'
    OR column_name LIKE '%\_list' ESCAPE '\'
    OR column_name LIKE '%\_csv' ESCAPE '\'
  )
ORDER BY 1, 2, 3;
```

### 7) Potential EAV Table Shape

```sql
SELECT table_schema, table_name
FROM information_schema.columns
WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
GROUP BY table_schema, table_name
HAVING
  bool_or(column_name IN ('entity_id', 'object_id', 'owner_id'))
  AND bool_or(column_name IN ('attr_name', 'attribute', 'key'))
  AND bool_or(column_name IN ('attr_value', 'value', 'val'))
ORDER BY 1, 2;
```

### 8) Potential Metadata Tribbles (suffix-cloned tables)

```sql
WITH rels AS (
  SELECT
    n.nspname AS table_schema,
    c.relname AS table_name,
    regexp_replace(c.relname, '(_20[0-9]{2}|_[0-9]{4}|_[a-z]+[0-9]+)$', '') AS base_name
  FROM pg_class c
  JOIN pg_namespace n ON n.oid = c.relnamespace
  WHERE c.relkind IN ('r', 'p')
    AND n.nspname NOT IN ('pg_catalog', 'information_schema')
)
SELECT table_schema, base_name, array_agg(table_name ORDER BY table_name) AS cloned_tables
FROM rels
GROUP BY 1, 2
HAVING count(*) >= 2
ORDER BY 1, 2;
```

### 9) Potential Metadata Tribbles (column-per-year/status cloning)

```sql
WITH cols AS (
  SELECT
    table_schema,
    table_name,
    column_name,
    CASE
      WHEN column_name ~ '(_)?(19|20)[0-9]{2}$'
        THEN regexp_replace(column_name, '(_)?(19|20)[0-9]{2}$', '')
      WHEN column_name ~ '_(open|closed|pending|active|inactive|new|done|failed|success|error|approved|rejected)(_|$)'
        THEN regexp_replace(column_name, '_(open|closed|pending|active|inactive|new|done|failed|success|error|approved|rejected)(_|$)', '_')
      ELSE NULL
    END AS base_name
  FROM information_schema.columns
  WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
),
normalized AS (
  SELECT
    table_schema,
    table_name,
    column_name,
    regexp_replace(base_name, '_+$', '') AS base_name
  FROM cols
  WHERE base_name IS NOT NULL
)
SELECT
  table_schema,
  table_name,
  base_name,
  array_agg(column_name ORDER BY column_name) AS cloned_columns
FROM normalized
GROUP BY 1, 2, 3
HAVING count(*) >= 2
ORDER BY 1, 2, 3;
```

Note: all nine are heuristics; review findings before enforcement.
