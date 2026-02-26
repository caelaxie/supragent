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
SELECT
  n.nspname AS schema_name,
  c.relname AS table_name,
  con.conname AS fk_name,
  pg_get_constraintdef(con.oid) AS fk_def
FROM pg_constraint con
JOIN pg_class c ON c.oid = con.conrelid
JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE con.contype = 'f'
  AND n.nspname NOT IN ('pg_catalog', 'information_schema')
  AND NOT EXISTS (
    SELECT 1
    FROM pg_index i
    WHERE i.indrelid = con.conrelid
      AND i.indisvalid
      AND i.indpred IS NULL
      AND (i.indkey::smallint[])[1:array_length(con.conkey, 1)] = con.conkey
  )
ORDER BY 1, 2, 3;
```

### 3) Potential Repeating-Group Columns (suffix-numbered columns)

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

### 4) Potential Polymorphic Pairs (`*_type` + `*_id`)

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

Note: all four are heuristics; review findings before enforcement.
