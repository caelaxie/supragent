---
name: sql-antipatterns
description: Use when designing, reviewing, or writing SQL tables, schemas, and queries to identify and remediate SQL anti-patterns. This skill is a growing collection; currently includes Jaywalking (comma-separated ID lists) and should be extended with additional anti-pattern chapters over time.
---

# Ch. 2: Jaywalking

Note: this skill is designed as a multi-chapter anti-patterns guide. Add new anti-patterns as additional chapters in this file.

Core idea: when a row needs to reference multiple values (e.g., a product has multiple contact accounts), do not cram them into a single column as a comma-separated list. That is the "Jaywalking" antipattern. Store one value per row using an intersection table.

## Objective: store multivalue attributes

You start with a simple relationship:

- `Products.account_id` -> one "primary contact" per product (many products -> one account)

But requirements change: one product needs multiple contacts. Now you have a many-to-many relationship (product <-> account).

## Antipattern: comma-separated lists

You change:

- from `account_id BIGINT`
- to `account_id VARCHAR(...)` containing `"12,34,56"`

This looks like fewer schema changes, but it creates structural problems:

### A. Querying becomes pattern-matching

You cannot do `WHERE account_id = 12`. You end up doing regex/LIKE hacks.

- False positives are easy (e.g., `12` matches `112`)
- Indexes become useless (full scans)
- Vendor-specific syntax (not portable)

### B. Joins become expensive and awkward

Joining a CSV field to Accounts requires string/regex expressions, which destroys optimizer options and index usage.

### C. Aggregations become "string tricks"

Counting contacts per product becomes "count commas + 1" style hacks, which are fragile and unreadable.

### D. Updates are painful

Appending is easy-ish; removing typically requires:

1. read the string
2. split in app code
3. remove item
4. join string
5. write back

### E. Integrity is not enforceable

You cannot apply a proper foreign key to individual items inside a string.
So garbage like `"12,banana"` can slip in, and your DB cannot stop it.

### F. Arbitrary length ceilings

"How many IDs fit?" becomes a nonsense question because it depends on digit length, separators, etc.

## Solution: intersection table (the correct model)

Create a mapping table like `Contacts(product_id, account_id)`:

- one row per association
- `PRIMARY KEY (product_id, account_id)` to prevent duplicates
- foreign keys to enforce integrity

### What you gain immediately

- Fast queries with indexes
- Simple joins
- Real aggregates (`COUNT(*) GROUP BY ...`)
- Easy updates (`INSERT`/`DELETE` one row)
- Referential integrity enforced by the database
- Extensibility: add metadata per association (e.g., `is_primary`, `added_at`, `added_by`)

## Practical patterns you should internalize

### Schema

```sql
CREATE TABLE Contacts (
  product_id BIGINT NOT NULL,
  account_id BIGINT NOT NULL,
  PRIMARY KEY (product_id, account_id),
  FOREIGN KEY (product_id) REFERENCES Products(product_id),
  FOREIGN KEY (account_id) REFERENCES Accounts(account_id)
);
```

### Query: products for an account

```sql
SELECT p.*
FROM Products p
JOIN Contacts c ON c.product_id = p.product_id
WHERE c.account_id = 34;
```

### Query: accounts for a product

```sql
SELECT a.*
FROM Accounts a
JOIN Contacts c ON c.account_id = a.account_id
WHERE c.product_id = 123;
```

### Aggregate: number of contacts per product

```sql
SELECT product_id, COUNT(*) AS contacts_per_product
FROM Contacts
GROUP BY product_id;
```

### Update: add/remove one association

```sql
INSERT INTO Contacts(product_id, account_id) VALUES (456, 34);
DELETE FROM Contacts WHERE product_id = 456 AND account_id = 34;
```
