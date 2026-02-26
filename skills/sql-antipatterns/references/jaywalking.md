# Jaywalking
## Objective
Model multi-value relationships without losing relational integrity, queryability, or performance.

## Antipattern
Store multiple foreign-key-like values in one column (for example, `products.account_ids_csv = '12,34,56'`) instead of one row per relationship.

## Why It Fails
- You cannot enforce a foreign key on each token inside a string.
- Filtering and joins become string parsing (`LIKE`, regex, split functions), which is brittle and slow.
- Aggregations require text tricks instead of relational operations.
- Updates are error-prone because add/remove operations require read-modify-write string manipulation.
- Data quality drifts (`'12,abc,,56'`) because the database cannot validate token semantics.

## How To Detect
- Columns named like `*_ids`, `*_list`, `*_csv` with `text`/`varchar` types.
- Queries that join on `regexp_split_to_table(...)`, `string_to_array(...)`, or `LIKE '%,%'`.
- No junction table for an obvious many-to-many relationship.

```sql
SELECT table_schema, table_name, column_name, data_type
FROM information_schema.columns
WHERE data_type IN ('text', 'character varying')
  AND column_name ~* '(_ids|_list|_csv)$';
```

## Legitimate Exceptions
- Short-lived staging/import columns before normalization.
- Read-only cache/materialized output derived from a normalized source of truth.
- Opaque payload fields that are not relational identifiers.

## Preferred Design
Use an intersection table with one row per association.

```sql
CREATE TABLE product_contacts (
  product_id BIGINT NOT NULL REFERENCES products(product_id) ON DELETE CASCADE,
  account_id BIGINT NOT NULL REFERENCES accounts(account_id) ON DELETE RESTRICT,
  is_primary BOOLEAN NOT NULL DEFAULT FALSE,
  added_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (product_id, account_id)
);

-- Composite PK helps lookups by product_id; add reverse index for account-driven queries.
CREATE INDEX product_contacts_account_id_idx ON product_contacts(account_id);
```

## PostgreSQL Implementation Patterns
```sql
-- Accounts for one product
SELECT a.*
FROM product_contacts pc
JOIN accounts a ON a.account_id = pc.account_id
WHERE pc.product_id = 123
ORDER BY a.account_id;

-- Products for one account
SELECT p.*
FROM product_contacts pc
JOIN products p ON p.product_id = pc.product_id
WHERE pc.account_id = 34;

-- Safe insert (idempotent)
INSERT INTO product_contacts (product_id, account_id)
VALUES (123, 34)
ON CONFLICT (product_id, account_id) DO NOTHING;

-- Remove one relationship
DELETE FROM product_contacts
WHERE product_id = 123 AND account_id = 34;
```

## Migration Pattern
```sql
-- 1) Create normalized table first.
CREATE TABLE product_contacts (
  product_id BIGINT NOT NULL,
  account_id BIGINT NOT NULL,
  PRIMARY KEY (product_id, account_id)
);

-- 2) Backfill from CSV safely.
INSERT INTO product_contacts (product_id, account_id)
SELECT p.product_id, trim(tok)::BIGINT
FROM products p
CROSS JOIN LATERAL regexp_split_to_table(COALESCE(p.account_ids_csv, ''), '\s*,\s*') AS tok
WHERE tok <> ''
  AND tok ~ '^\d+$'
ON CONFLICT DO NOTHING;

-- 3) Add FK constraints after cleanup.
ALTER TABLE product_contacts
  ADD CONSTRAINT product_contacts_product_fkey
  FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE;

ALTER TABLE product_contacts
  ADD CONSTRAINT product_contacts_account_fkey
  FOREIGN KEY (account_id) REFERENCES accounts(account_id) ON DELETE RESTRICT;
```

## Version and Engine Caveats
- PostgreSQL arrays/`jsonb` can store lists, but they still cannot enforce per-element foreign keys.
- `regexp_split_to_table` is PostgreSQL-specific; avoid embedding it into long-term relational design.
- Other engines often offer different string-split functions; migration scripts are engine-specific.
