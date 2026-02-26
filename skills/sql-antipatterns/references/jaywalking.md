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

-- Add reverse-path index before FK validation/cutover.
CREATE INDEX IF NOT EXISTS product_contacts_account_id_idx ON product_contacts(account_id);

-- Reject log is durable for remediation; clean up only after a successful run.
CREATE TABLE IF NOT EXISTS product_contact_rejects (
  reject_id         BIGSERIAL PRIMARY KEY,
  migration_run_id TEXT NOT NULL,
  product_id       BIGINT NOT NULL,
  raw_token        TEXT NOT NULL,
  reject_reason    TEXT NOT NULL,
  rejected_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS product_contact_rejects_run_idx
  ON product_contact_rejects (migration_run_id);

-- Use one run id consistently across this script.
-- Replace MIGRATION_RUN_ID with your deployment run id before execution.
-- Run reject capture + gate before any BEGIN/COMMIT block for cutover statements.

-- 2) Classify tokens before casting so malformed/overflow values are handled safely.
CREATE TEMP TABLE staged_product_contact_tokens AS
WITH tokens AS (
  SELECT
    p.product_id,
    btrim(tok) AS raw_token
  FROM products p
  CROSS JOIN LATERAL regexp_split_to_table(
    CASE
      WHEN NULLIF(btrim(p.account_ids_csv), '') IS NULL THEN NULL
      ELSE p.account_ids_csv
    END,
    ','
  ) AS tok
)
SELECT
  product_id,
  raw_token,
  CASE
    WHEN raw_token = '' THEN 'empty'
    WHEN raw_token !~ '^[0-9]+$' THEN 'non_numeric'
    WHEN length(raw_token) > 19
      OR (length(raw_token) = 19 AND raw_token > '9223372036854775807') THEN 'overflow'
    ELSE NULL
  END AS reject_reason
FROM tokens;

-- 3) Persist parse rejects first; this survives a failed gate when run in autocommit mode.
INSERT INTO product_contact_rejects (migration_run_id, product_id, raw_token, reject_reason)
SELECT 'MIGRATION_RUN_ID', product_id, raw_token, reject_reason
FROM staged_product_contact_tokens
WHERE reject_reason IS NOT NULL;

-- 4) Resolve cast-safe tokens for FK existence checks.
CREATE TEMP TABLE staged_product_contact_resolved AS
SELECT product_id, raw_token::BIGINT AS account_id, raw_token
FROM staged_product_contact_tokens
WHERE reject_reason IS NULL;

-- 5) Persist dangling-account rejects (numeric token, but no parent row).
INSERT INTO product_contact_rejects (migration_run_id, product_id, raw_token, reject_reason)
SELECT 'MIGRATION_RUN_ID', s.product_id, s.raw_token, 'missing_account'
FROM staged_product_contact_resolved s
LEFT JOIN accounts a ON a.account_id = s.account_id
WHERE a.account_id IS NULL;

-- 6) Fail closed before any insert into product_contacts.
DO $$
BEGIN
  IF EXISTS (
    SELECT 1
    FROM product_contact_rejects
    WHERE migration_run_id = 'MIGRATION_RUN_ID'
  ) THEN
    RAISE EXCEPTION
      'Backfill rejected malformed/overflow/dangling account_ids_csv tokens; inspect product_contact_rejects for migration_run_id=%',
      'MIGRATION_RUN_ID';
  END IF;
END $$;

-- 7) Backfill only after gate passes.
INSERT INTO product_contacts (product_id, account_id)
SELECT s.product_id, s.account_id
FROM staged_product_contact_resolved s
JOIN accounts a ON a.account_id = s.account_id
ON CONFLICT DO NOTHING;

-- 8) Add FK constraints with online-safe rollout.
-- Partitioned-table caveat: as of PostgreSQL 17 docs, foreign keys declared on
-- partitioned tables may not support NOT VALID. If product_contacts is
-- partitioned, plan a validated ADD CONSTRAINT path in a controlled lock window.
ALTER TABLE product_contacts
  ADD CONSTRAINT product_contacts_product_fkey
  FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE
  NOT VALID;

ALTER TABLE product_contacts
  ADD CONSTRAINT product_contacts_account_fkey
  FOREIGN KEY (account_id) REFERENCES accounts(account_id) ON DELETE RESTRICT
  NOT VALID;

ALTER TABLE product_contacts
  VALIDATE CONSTRAINT product_contacts_product_fkey;

ALTER TABLE product_contacts
  VALIDATE CONSTRAINT product_contacts_account_fkey;

-- 9) Cleanup reject rows only after successful backfill + validation.
DELETE FROM product_contact_rejects
WHERE migration_run_id = 'MIGRATION_RUN_ID';
```

## Rollback Considerations
- Keep `products.account_ids_csv` as fallback read/write shape until parity checks pass.
- If cutover fails, drop `product_contacts` constraints/tables and continue serving from legacy CSV.
- Preserve `product_contact_rejects` rows for the failed `migration_run_id` so remediation can target exact bad tokens.
- Delete `product_contact_rejects` rows for that `migration_run_id` only after a successful rerun.

## Version and Engine Caveats
- PostgreSQL arrays/`jsonb` can store lists, but they still cannot enforce per-element foreign keys.
- `regexp_split_to_table` is PostgreSQL-specific; avoid embedding it into long-term relational design.
- Other engines often offer different string-split functions; migration scripts are engine-specific.
