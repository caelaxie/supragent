# Keyless Entry
## Objective
Enforce referential integrity in the database so every writer follows the same relationship rules.

## Antipattern
Skip foreign keys and rely on application checks, cron cleanup jobs, or manual scripts to keep related tables consistent.

## Why It Fails
- "Check then write" logic races under concurrency.
- Orphans accumulate and reporting becomes inconsistent.
- Integrity rules fragment across services, scripts, and ad-hoc SQL.
- Parent deletes/updates become expensive firefights instead of declarative referential actions.

## How To Detect
- `*_id` columns exist but no `FOREIGN KEY` constraints.
- Repeated orphan-audit queries are part of normal operations.
- Application code performs parent existence checks before every child insert.

```sql
-- Candidate ID columns without a foreign key constraint
SELECT n.nspname AS schema_name, c.relname AS table_name, a.attname AS column_name
FROM pg_attribute a
JOIN pg_class c ON c.oid = a.attrelid
JOIN pg_namespace n ON n.oid = c.relnamespace
LEFT JOIN pg_constraint fk
  ON fk.contype = 'f'
 AND fk.conrelid = a.attrelid
 AND a.attnum = ANY(fk.conkey)
WHERE c.relkind IN ('r', 'p')
  AND n.nspname NOT IN ('pg_catalog', 'information_schema')
  AND a.attnum > 0
  AND NOT a.attisdropped
  AND a.attname ~ '_id$'
  AND fk.oid IS NULL
ORDER BY 1, 2, 3;
```

## Legitimate Exceptions
- Cross-shard relationships where the engine cannot enforce cross-shard FKs.
- Short migration windows while data is repaired before constraint validation.
- Staging/raw ingestion tables that are not authoritative.

## Preferred Design
Declare foreign keys for real relationships, choose `ON DELETE`/`ON UPDATE` actions deliberately, and keep keys stable.

```sql
CREATE TABLE accounts (
  account_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  email      TEXT NOT NULL UNIQUE
);

CREATE TABLE bugs (
  bug_id       BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  reported_by  BIGINT NOT NULL,
  assigned_to  BIGINT,
  title        TEXT NOT NULL,
  status       TEXT NOT NULL DEFAULT 'NEW',
  CONSTRAINT bugs_reported_by_fkey
    FOREIGN KEY (reported_by) REFERENCES accounts(account_id) ON DELETE RESTRICT,
  CONSTRAINT bugs_assigned_to_fkey
    FOREIGN KEY (assigned_to) REFERENCES accounts(account_id) ON DELETE SET NULL
);
```

## PostgreSQL Implementation Patterns
```sql
-- PostgreSQL auto-indexes PRIMARY KEY/UNIQUE on referenced columns,
-- but does NOT auto-index referencing (child) FK columns.
CREATE INDEX bugs_reported_by_idx ON bugs(reported_by);
CREATE INDEX bugs_assigned_to_idx ON bugs(assigned_to);

-- For bulk loads, add FK as NOT VALID, then validate online later.
ALTER TABLE bugs
  ADD CONSTRAINT bugs_reported_by_fkey_v2
  FOREIGN KEY (reported_by) REFERENCES accounts(account_id)
  NOT VALID;

ALTER TABLE bugs
  VALIDATE CONSTRAINT bugs_reported_by_fkey_v2;
```

```sql
-- Typical orphan check prior to adding a FK
SELECT b.bug_id, b.reported_by
FROM bugs b
LEFT JOIN accounts a ON a.account_id = b.reported_by
WHERE b.reported_by IS NOT NULL
  AND a.account_id IS NULL
LIMIT 100;
```

## Migration Pattern
```sql
-- 1) Ensure supporting index on child/reference column first.
CREATE INDEX CONCURRENTLY IF NOT EXISTS order_items_order_id_idx
  ON order_items(order_id);

-- 2) Detect and fix orphan rows.
SELECT oi.order_id
FROM order_items oi
LEFT JOIN orders o ON o.order_id = oi.order_id
WHERE oi.order_id IS NOT NULL
  AND o.order_id IS NULL;

-- 3) Add FK without immediate full-table validation.
ALTER TABLE order_items
  ADD CONSTRAINT order_items_order_id_fkey
  FOREIGN KEY (order_id) REFERENCES orders(order_id)
  ON DELETE CASCADE
  NOT VALID;

-- 4) Validate after cleanup.
ALTER TABLE order_items
  VALIDATE CONSTRAINT order_items_order_id_fkey;
```

## Rollback Considerations
- Keep legacy app-side checks temporarily behind a feature flag until FK validation succeeds.
- If rollout fails, route writes through the legacy path and drop newly added `NOT VALID` constraints.
- Preserve orphan-audit query outputs so repaired rows can be replayed before a second validation attempt.

## Version and Engine Caveats
- In PostgreSQL, referenced columns must be `PRIMARY KEY`, `UNIQUE`, or backed by a non-partial unique index.
- PostgreSQL does not auto-create indexes for referencing FK columns; add them explicitly for delete/update check performance.
- `CREATE INDEX CONCURRENTLY` cannot run inside a transaction block.
- FK behavior and online-validation capabilities vary across engines; migration runbooks are engine-specific.
