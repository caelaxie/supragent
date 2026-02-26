---
name: sql-antipatterns
description: Use when designing, reviewing, or writing SQL tables, schemas, and queries to identify and remediate SQL anti-patterns. This skill is a growing collection; currently includes Jaywalking, Naive Trees, Keyless Entry, Entity-Attribute-Value, Polymorphic Associations, Multicolumn Attributes, and Metadata Tribbles, and should be extended with additional anti-pattern sections over time.
---

# SQL Anti-Patterns

Note: this skill is designed as a multi-section anti-patterns guide. Add new anti-patterns as additional sections in this file.

## Jaywalking

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

## Naive Trees

## Objective: model hierarchical data for both reads and writes

This section focuses on representing tree-shaped data in SQL (threaded comments, org charts, categories, part explosions) while keeping common operations practical:

- fetch ancestors or descendants
- render a subtree in display order
- move or delete branches safely

## Antipattern: naive adjacency list usage

The common starting model stores only a parent pointer:

```sql
CREATE TABLE comments (
  comment_id BIGINT PRIMARY KEY,
  parent_id BIGINT REFERENCES comments(comment_id),
  body TEXT NOT NULL
);
```

This adjacency-list schema is valid, but it becomes an antipattern when teams expect deep-tree querying to stay simple without recursive SQL support.

## Why this fails in practice

### A. Fixed-depth joins do not scale

Without recursion, joins must be hardcoded by depth (`child`, `grandchild`, `great-grandchild`), which breaks as depth grows.

### B. "Load everything, rebuild in app code" wastes work

Pulling all rows and reconstructing trees in memory is expensive when you only need one subtree or aggregate.

### C. Deletes and moves get brittle

Subtree operations require multi-step logic to locate descendants and apply changes in the right order.

### D. Orphans and cleanup scripts appear

When tree operations are mostly app-side, integrity bugs tend to accumulate and need periodic repair jobs.

## When adjacency list is acceptable

Adjacency list is still fine when:

- tree depth is naturally shallow
- subtree/ancestor traversals are infrequent
- your database supports recursive queries and your team actually uses them

## Better approaches

### Option 1: adjacency list plus recursive CTE (recommended default in PostgreSQL)

```sql
WITH RECURSIVE comment_tree AS (
  SELECT c.comment_id, c.parent_id, c.body, 0 AS depth
  FROM comments c
  WHERE c.comment_id = 100

  UNION ALL

  SELECT c.comment_id, c.parent_id, c.body, ct.depth + 1
  FROM comments c
  JOIN comment_tree ct ON c.parent_id = ct.comment_id
)
SELECT *
FROM comment_tree
ORDER BY depth, comment_id;
```

This keeps schema design simple and normalized while enabling full-tree traversal.

### Option 2: path enumeration

Store the full ancestry path per row (for example `1/4/6/`), then query descendants by prefix.

Pros:
- straightforward descendant predicates

Cons:
- weak referential integrity enforcement
- path rewrite overhead when moving branches
- potential path-length growth issues

### Option 3: nested sets

Store interval boundaries (`nsleft`, `nsright`) so subtrees are range queries.

Pros:
- fast read-side subtree retrieval

Cons:
- inserts/moves can require renumbering many rows
- write-heavy workloads become costly

### Option 4: closure table

Store ancestor/descendant pairs in a companion table:

```sql
CREATE TABLE tree_paths (
  ancestor BIGINT NOT NULL,
  descendant BIGINT NOT NULL,
  path_length INT NOT NULL,
  PRIMARY KEY (ancestor, descendant),
  FOREIGN KEY (ancestor) REFERENCES comments(comment_id),
  FOREIGN KEY (descendant) REFERENCES comments(comment_id)
);
```

Pros:
- simple ancestor and descendant queries
- FK-backed integrity on both ends
- supports rich tree operations cleanly

Cons:
- extra storage proportional to tree depth

## Quick decision guide

- Use adjacency list + recursion for most PostgreSQL workloads.
- Use closure table when traversal and branch mutations are both common.
- Use nested sets only for mostly-static, read-heavy trees.
- Use path enumeration cautiously due to maintenance and integrity tradeoffs.

## Mini-antipattern: environment mismatch

If development and production database versions differ, recursive SQL support can diverge and break at runtime. Keep versions and capabilities aligned across environments.

## Keyless Entry

## Objective: simplify database architecture

This section argues that relationships are first-class data design, so the database should enforce them.
When foreign keys are omitted, teams usually re-implement referential integrity in application code and ad-hoc scripts, which is slower, riskier, and harder to maintain.

The failure mode in this section is operationally familiar: inconsistent reports, broken subtotals, and orphaned rows that require periodic "cleanup queries."

## Antipattern: "Leave Out the Constraints"

This section calls out this belief:

- foreign keys make the schema "too rigid,"
- checks in code are "good enough,"
- and dropping constraints improves performance/flexibility.

In practice, this creates predictable problems.

### A. "Pre-check then write" logic breaks under concurrency

Without FK enforcement, you end up writing:

- parent-exists checks before insert,
- child-exists checks before delete,
- and manual sequencing rules in every code path.

These checks race under concurrent transactions: a check can pass, then another session changes related rows before your write commits.

### B. Orphan detection becomes a permanent maintenance tax

If constraints are missing, you need recurring integrity audits (for example, orphan detection queries) for every relationship.
Then you still need policies for:

- how often checks run,
- how to repair bad rows,
- and who owns the repair logic.

### C. Parent-key updates create a catch-22

When child rows reference a parent key and that key changes, manual two-step update sequences can violate integrity either way (parent-first or child-first).
The database already has native mechanisms for this; skipping constraints recreates a hard problem badly.

### D. Integrity enforcement fragments across write paths

Even if your main app validates relationships, backfill scripts, admin SQL, and forgotten services can bypass those checks.
FK constraints protect all writers uniformly.

## How to recognize you're in this antipattern

A simple symptom: related tables exist, but there are no foreign keys between them.

Other common tells:

- "How do I find rows that exist in one table but not the other?"
- "How do I check parent existence before every insert?"
- "Foreign keys are too slow, so we avoid them."

## Legitimate uses (when constraints may be absent temporarily)

This section treats these as exceptions, not defaults:

- Temporary removal during data-cleanup or migration work
- Tooling workflows that require dropping and re-adding constraints
- Historical/legacy engines with weak or missing FK support
- Specific lock-behavior edge cases in some implementations
- Sharded/distributed setups where related rows can land on different shards and cross-shard foreign keys are unsupported

The key point: these are operational tradeoffs with a plan to restore enforcement, not a permanent design strategy.

## Solution: "Declare Constraints" (poka-yoke)

Core prescription: define foreign keys so invalid writes are rejected at the database boundary, not detected after the fact.

A practical rule set:

1. Declare FKs for real relationships.
    - Child columns must reference parent `PRIMARY KEY`/`UNIQUE` columns.
2. Choose referential actions intentionally.
    - Use `ON DELETE`/`ON UPDATE` behavior that matches business lifecycle rules.
3. Prefer stable identifiers.
    - Avoid frequently updating referenced natural keys; treat mutable labels/codes as attributes.
4. Let the database enforce integrity for every writer.
    - Apps, scripts, ad-hoc SQL, and migration tools all get the same guarantees.
5. Account for sharding limits explicitly.
    - In some sharded systems, foreign keys can enforce integrity only within a shard, not across shards.

### Practical PostgreSQL patterns

#### Create table with FKs

```sql
CREATE TABLE Bugs (
  bug_id       BIGSERIAL PRIMARY KEY,
  reported_by  BIGINT NOT NULL,
  status       VARCHAR(20) NOT NULL DEFAULT 'NEW',
  FOREIGN KEY (reported_by) REFERENCES Accounts(account_id),
  FOREIGN KEY (status)      REFERENCES BugStatus(status)
);
```

#### Add FKs to an existing table

```sql
ALTER TABLE bugs
  ADD CONSTRAINT bugs_reported_by_fkey
  FOREIGN KEY (reported_by)
  REFERENCES accounts(account_id)
  ON DELETE RESTRICT;

ALTER TABLE bugs
  ADD CONSTRAINT bugs_status_fkey
  FOREIGN KEY (status)
  REFERENCES bug_status(status)
  ON UPDATE CASCADE
  ON DELETE RESTRICT;
```

#### Referential action quick guide

- `ON DELETE RESTRICT/NO ACTION`: block parent delete when children exist
- `ON DELETE CASCADE`: delete dependent rows automatically
- `ON DELETE SET NULL/SET DEFAULT`: keep child row, rewrite FK value
- `ON UPDATE CASCADE`: propagate parent key updates to children

## Entity-Attribute-Value

## Objective: support variable attributes without throwing away relational guarantees

This section's target problem is real: some entities evolve and need different attributes over time (for example, bugs vs feature requests).
But this section argues that the common EAV shortcut solves this by moving schema into row data, which trades short-term flexibility for long-term query and integrity pain.

## Antipattern: "Use a Generic Attribute Table"

Typical shape:

- `Issues(issue_id, ...)`
- `IssueAttributes(issue_id, attr_name, attr_value)`

So each attribute becomes a row, and attribute names are stored as strings.

Why teams choose it:

- fewer declared columns,
- no `ALTER TABLE` for every new attribute,
- and fewer visible NULLs in subtype-specific fields.

These are mostly cosmetic wins.

## Why EAV fails in practice

### A. Queries become stringly typed and hard to read

Simple column access turns into "find rows where `attr_name = 'date_reported'`," then join/pivot logic to rebuild entities.

### B. You lose SQL types and basic validation

When everything is text in `attr_value`, the DB cannot enforce per-attribute types.
In a normal schema, writing `'banana'` to a date column fails; in EAV, it can be stored as the "date" attribute.

### C. Constraints stop working cleanly

- Required attributes are hard to enforce (`NOT NULL` no longer maps cleanly).
- Foreign keys on `attr_value` over-constrain unrelated attributes, because constraints apply to all rows in the table.

### D. Attribute naming drifts

Because names are just strings, semantic duplicates appear (`date_reported` vs `report_date`), and queries become defensive string matching.

### E. Reconstructing one row per entity is expensive

You either join once per attribute or do pivoting (`CASE`/aggregate patterns). Both get slower and more brittle as attributes grow.

## How to recognize you're in this antipattern

The strongest signal is a schema centered on `(entity_id, attr_name, attr_value)` for core business data.

Other tells:

- frequent SQL pivot/reconstruction queries,
- inability to express simple type/required constraints directly,
- inconsistent attribute naming that leaks into query logic.

## Legitimate uses (where flexibility is truly required)

This section's nuance is not "never dynamic data." It is:

- if subtypes are a finite set, model them explicitly with relational tables;
- if attributes are truly open-ended, keep a relational core and use one semistructured column (JSON/XML) for the dynamic tail;
- if you are temporarily stuck on EAV, query attributes as rows and assemble objects in application code instead of giant SQL pivots.

## Solution: model subtypes, not metadata-in-data

Core prescription: represent variable attributes with explicit subtype design, and keep relational structure for what is stable.

A practical decision framework:

1. If subtype set is finite, use subtype tables instead of EAV.
    - Concrete table inheritance: one table per subtype; subtype integrity is simple, cross-subtype querying is harder.
    - Class table inheritance: base table for shared fields plus 1:1 subtype tables; better for cross-subtype queries on shared fields.
2. If attributes are genuinely unbounded, use a semistructured column on a relational base row.
    - Accept that querying/indexing dynamic attributes is less graceful than scalar columns.
3. Preserve relational guarantees for common attributes.
    - Keep typing, constraints, and foreign keys in normal columns wherever possible.
4. Treat EAV as a migration state, not an end-state.
    - The longer it stays central, the more application code replaces database guarantees.

## Practical PostgreSQL examples

Treat each option as a separate modeling path (run each block set independently, not all in one database schema).

### EAV shape (the antipattern baseline)

```sql
CREATE TABLE Issues (
  issue_id BIGSERIAL PRIMARY KEY
);

CREATE TABLE IssueAttributes (
  issue_id   BIGINT NOT NULL REFERENCES Issues(issue_id),
  attr_name  VARCHAR(100) NOT NULL,
  attr_value TEXT NOT NULL
);
```

```sql
-- One issue represented as many key/value rows
INSERT INTO IssueAttributes (issue_id, attr_name, attr_value) VALUES
  (1234, 'date_reported', '2022-11-03'),
  (1234, 'status', 'NEW'),
  (1234, 'severity', 'loss of functionality');
```

### Option 1: Concrete Table Inheritance (one table per subtype)

```sql
CREATE TABLE Bugs (
  issue_id          BIGSERIAL PRIMARY KEY,
  reported_by       BIGINT NOT NULL,
  product_id        BIGINT,
  priority          VARCHAR(20),
  version_resolved  VARCHAR(20),
  status            VARCHAR(20),
  severity          VARCHAR(20),  -- bug-only
  version_affected  VARCHAR(20)   -- bug-only
);

CREATE TABLE FeatureRequests (
  issue_id          BIGSERIAL PRIMARY KEY,
  reported_by       BIGINT NOT NULL,
  product_id        BIGINT,
  priority          VARCHAR(20),
  version_resolved  VARCHAR(20),
  status            VARCHAR(20),
  sponsor           VARCHAR(50)   -- feature-only
);
```

```sql
INSERT INTO Bugs
  (reported_by, product_id, priority, version_resolved, status, severity, version_affected)
VALUES
  (101, 7, 'HIGH', NULL, 'NEW', 'loss of functionality', '1.0');

INSERT INTO FeatureRequests
  (reported_by, product_id, priority, version_resolved, status, sponsor)
VALUES
  (202, 7, 'MEDIUM', NULL, 'NEW', 'Acme Corp');
```

```sql
-- Cross-subtype querying typically needs a UNION ALL view of common columns
CREATE VIEW Issues AS
SELECT
  b.issue_id, b.reported_by, b.product_id, b.priority, b.version_resolved, b.status,
  'bug' AS issue_type
FROM Bugs b
UNION ALL
SELECT
  f.issue_id, f.reported_by, f.product_id, f.priority, f.version_resolved, f.status,
  'feature' AS issue_type
FROM FeatureRequests f;
```

### Option 2: Class Table Inheritance (base table + 1:1 subtype tables)

```sql
CREATE TABLE Issues (
  issue_id          BIGSERIAL PRIMARY KEY,
  reported_by       BIGINT NOT NULL,
  product_id        BIGINT,
  priority          VARCHAR(20),
  version_resolved  VARCHAR(20),
  status            VARCHAR(20)
);

CREATE TABLE Bugs (
  issue_id          BIGINT PRIMARY KEY REFERENCES Issues(issue_id),
  severity          VARCHAR(20),
  version_affected  VARCHAR(20)
);

CREATE TABLE FeatureRequests (
  issue_id          BIGINT PRIMARY KEY REFERENCES Issues(issue_id),
  sponsor           VARCHAR(50)
);
```

```sql
WITH new_issue AS (
  INSERT INTO Issues (reported_by, product_id, priority, version_resolved, status)
  VALUES (101, 7, 'HIGH', NULL, 'NEW')
  RETURNING issue_id
)
INSERT INTO Bugs (issue_id, severity, version_affected)
SELECT issue_id, 'loss of functionality', '1.0'
FROM new_issue;
```

```sql
WITH new_issue AS (
  INSERT INTO Issues (reported_by, product_id, priority, version_resolved, status)
  VALUES (202, 7, 'MEDIUM', NULL, 'NEW')
  RETURNING issue_id
)
INSERT INTO FeatureRequests (issue_id, sponsor)
SELECT issue_id, 'Acme Corp'
FROM new_issue;
```

```sql
-- Common cross-subtype search stays simple
SELECT issue_id, reported_by, product_id, priority, status
FROM Issues
WHERE product_id = 7
  AND status = 'NEW';
```

```sql
-- Full row with subtype attributes
SELECT
  i.issue_id, i.reported_by, i.product_id, i.priority, i.version_resolved, i.status,
  b.severity, b.version_affected, f.sponsor
FROM Issues i
LEFT JOIN Bugs b USING (issue_id)
LEFT JOIN FeatureRequests f USING (issue_id);
```

### Option 3: Semistructured column (JSON attributes on base row)

```sql
CREATE TABLE Issues (
  issue_id          BIGSERIAL PRIMARY KEY,
  reported_by       BIGINT NOT NULL,
  product_id        BIGINT,
  priority          VARCHAR(20),
  version_resolved  VARCHAR(20),
  status            VARCHAR(20),
  issue_type        VARCHAR(10),  -- BUG or FEATURE
  attributes        JSON NOT NULL
);
```

```sql
INSERT INTO Issues
  (reported_by, product_id, priority, version_resolved, status, issue_type, attributes)
VALUES
  (101, 7, 'HIGH', NULL, 'NEW', 'BUG',
   '{"severity":"loss of functionality","version_affected":"1.0"}'),
  (202, 7, 'MEDIUM', NULL, 'NEW', 'FEATURE',
   '{"sponsor":"Acme Corp","business_value":8}');
```

```sql
SELECT issue_id, product_id, priority, status, issue_type
FROM Issues
WHERE product_id = 7;
```

```sql
-- PostgreSQL JSON filtering on dynamic attributes
SELECT issue_id
FROM Issues
WHERE issue_type = 'BUG'
  AND attributes ->> 'severity' = 'loss of functionality';
```

```sql
SELECT issue_id
FROM Issues
WHERE issue_type = 'FEATURE'
  AND (attributes ->> 'business_value')::int >= 8;
```

## Polymorphic Associations

## Objective: reference multiple parent tables safely

This section addresses a common modeling problem: one child row (for example, a comment) may belong to one of multiple parent tables (for example, `Bugs` or `FeatureRequests`).

The temptation is to make one "flexible FK" using:

- `parent_type` (string like `Bug`, `FeatureRequest`)
- `parent_id` (numeric ID)

This is the polymorphic association antipattern.

## Antipattern: dual-purpose foreign key

Typical shape:

```sql
CREATE TABLE Comments (
  comment_id SERIAL PRIMARY KEY,
  parent_type VARCHAR(20) NOT NULL,
  parent_id BIGINT NOT NULL,
  comment_text TEXT NOT NULL
);
```

It looks flexible, but a foreign key cannot conditionally reference different tables based on another column.

## Why this fails in practice

### A. No referential integrity

The database cannot enforce that `parent_id` exists in the table named by `parent_type`.

### B. Hard-to-optimize queries

Every lookup needs both columns (`parent_type`, `parent_id`) and usually conditional joins.

### C. Deletion/update anomalies

Cascading behavior is manual and easy to miss, causing orphan rows.

### D. Metadata stored as data

Table identity is encoded in string values (`parent_type`), which is brittle during refactors.

### E. Cardinality rules are difficult to enforce

Business rules like "a comment must belong to exactly one parent" become custom logic instead of constraints.

## How to spot it quickly

- Presence of `*_type` + `*_id` pairs meant to target multiple parent tables.
- Team statements like "FK target depends on another column."
- ORM generic relation features used as the physical schema model.

## Better designs

### Option 1: intersection tables per parent type (preferred)

Keep comments in one table, then map parent relationships with explicit FK-backed tables.

```sql
CREATE TABLE BugComments (
  comment_id BIGINT NOT NULL,
  issue_id BIGINT NOT NULL,
  PRIMARY KEY (comment_id, issue_id),
  UNIQUE (comment_id),
  FOREIGN KEY (comment_id) REFERENCES Comments(comment_id),
  FOREIGN KEY (issue_id) REFERENCES Bugs(issue_id)
);

CREATE TABLE FeatureRequestComments (
  comment_id BIGINT NOT NULL,
  issue_id BIGINT NOT NULL,
  PRIMARY KEY (comment_id, issue_id),
  UNIQUE (comment_id),
  FOREIGN KEY (comment_id) REFERENCES Comments(comment_id),
  FOREIGN KEY (issue_id) REFERENCES FeatureRequests(issue_id)
);
```

Benefits:

- Real FK enforcement
- Clean, index-friendly joins
- Straightforward delete/update behavior
- Easy extension (audit columns, ownership, timestamps)

### Option 2: common supertype parent table

If parent tables share a real domain supertype, point comments to the supertype PK instead of polymorphic string/id pairs.

### Option 3: separate nullable FK columns (small fixed parent set)

Use explicit columns (for example, `bug_id`, `feature_request_id`) plus a `CHECK` constraint ensuring exactly one is non-null.

## Multicolumn Attributes

## Objective: store multivalue attributes without repeating groups

This section focuses on modeling attributes that can have multiple values (for example, tags, phone numbers, skills) without breaking relational design rules.

The core goal is to keep data in first normal form (1NF): one atomic value per column cell.

## Antipattern: repeating group columns

A common shortcut is to add numbered columns for the same logical attribute:

```sql
CREATE TABLE Bugs (
  bug_id SERIAL PRIMARY KEY,
  description VARCHAR(1000),
  tag1 VARCHAR(20),
  tag2 VARCHAR(20),
  tag3 VARCHAR(20)
);
```

This looks simple early on, but creates a rigid, hard-to-query schema.

## Why this fails in practice

### A. Fixed arbitrary limits

`tag1..tag3` assumes a max count. When requirements grow, schema changes are required.

### B. Query complexity

Finding by tag needs repetitive OR predicates across columns.

### C. Weak integrity guarantees

The database cannot cleanly prevent duplicates like putting the same tag in multiple slots.

### D. Fragile writes

Application logic must find "the next free column," which is error-prone and concurrency-unfriendly.

### E. Expensive schema churn

Every additional slot means `ALTER TABLE`, plus code, query, and ORM mapping changes.

### F. 1NF violation

Repeating groups encode a collection into columns instead of rows.

## How to spot it quickly

- Column families like `phone1`, `phone2`, `phone3`, or `tag1`, `tag2`, `tag3`
- Frequent queries with `OR` over near-identical columns
- Ongoing requests to add "one more column" for the same attribute

## Better design: dependent child table

Store each value as one row in a child table:

```sql
CREATE TABLE BugTags (
  bug_id BIGINT NOT NULL,
  tag VARCHAR(20) NOT NULL,
  PRIMARY KEY (bug_id, tag),
  FOREIGN KEY (bug_id) REFERENCES Bugs(bug_id) ON DELETE CASCADE
);
```

Example usage:

```sql
INSERT INTO BugTags (bug_id, tag) VALUES
  (1234, 'crash'),
  (1234, 'performance'),
  (1234, 'ui');
```

```sql
SELECT b.*
FROM Bugs b
JOIN BugTags t ON b.bug_id = t.bug_id
WHERE t.tag = 'performance';
```

Benefits:

- No fixed upper bound
- Cleaner queries and indexes
- Database-enforced uniqueness and referential integrity
- Simpler add/remove operations (`INSERT`/`DELETE` rows)

## Legitimate exceptions

Separate columns can be valid when values are not interchangeable and have distinct business meaning (for example, `reporter_id`, `assignee_id`, `qa_verifier_id`).

## Migration pattern

1. Create the child table.
2. Backfill from old columns with `UNION ALL`.
3. Switch reads/writes in application code.
4. Drop old repeating columns after verification.

## Metadata Tribbles

## Objective: structure data for scalability without cloning schema objects

As tables grow, query performance can degrade. The goal is to keep data scalable so performance remains acceptable as data accumulates, without resorting to duplicating tables or columns.

## Antipattern: clone tables or columns

### A. Spawning tables (table-per-year, table-per-tenant, etc.)

New tables are created for each new data value rather than storing that value as a row:

```sql
-- Antipattern: a new table every year
CREATE TABLE Bugs_2024 (...);
CREATE TABLE Bugs_2025 (...);
CREATE TABLE Bugs_2026 (...);
```

The predictable failure: the calendar flips and the app breaks because nobody created next year's table.

### B. Spawning columns (column-per-year, column-per-status, etc.)

New columns are added to an existing table for each new data value:

```sql
-- Antipattern: a new column every year
ALTER TABLE Customers ADD COLUMN revenue2024 NUMERIC(12,2);
ALTER TABLE Customers ADD COLUMN revenue2025 NUMERIC(12,2);
ALTER TABLE Customers ADD COLUMN revenue2026 NUMERIC(12,2);
```

## Why this fails in practice

### A. Data integrity drift

Rows can land in the wrong table (e.g., a 2025 bug inserted into `Bugs_2024`). Correcting this requires manual validation and per-table CHECK constraints to approximate correctness.

### B. Querying becomes awkward

Anything spanning "all years" requires a UNION across every cloned table, and that query must be updated as new tables appear.

### C. Schema changes are multiplied

Adding a new column (e.g., `hours`) requires altering every cloned table. UNION queries break if columns across tables diverge.

### D. Referential integrity is blocked

A child table cannot declare a foreign key against `Bugs_????` because a foreign key must reference one specific parent table, not a family of clones.

## How to spot it quickly

- Hearing "then we need to create a table (or column) per ..."
- Asking "what's the maximum number of tables/columns the database supports?"
- Discovering "we forgot to create a new table for the new year"
- Queries that ask "how do I query across all these identical tables?"

## Better design: partition and normalize

### Horizontal partitioning (by rows) in PostgreSQL

Keep one logical table and let PostgreSQL split storage into partitions. Queries always target the parent; partition pruning limits which physical partitions are scanned.

#### Range partitioning by time

```sql
CREATE TABLE bugs (
  bug_id        BIGINT GENERATED ALWAYS AS IDENTITY,
  date_reported DATE NOT NULL,
  status        TEXT NOT NULL,
  summary       TEXT NOT NULL,
  PRIMARY KEY (bug_id, date_reported)   -- partition key must be in PK
) PARTITION BY RANGE (date_reported);

CREATE TABLE bugs_2026_01 PARTITION OF bugs
  FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');

CREATE TABLE bugs_2026_02 PARTITION OF bugs
  FOR VALUES FROM ('2026-02-01') TO ('2026-03-01');
```

Indexes created on the parent are applied to all partitions automatically (PG 11+):

```sql
CREATE INDEX ON bugs (date_reported);
CREATE INDEX ON bugs (status, date_reported);
```

#### Automate future partitions to avoid "forgot next year"

```sql
CREATE OR REPLACE FUNCTION ensure_month_partition(p_month date)
RETURNS void LANGUAGE plpgsql AS $$
DECLARE
  start_date date := date_trunc('month', p_month)::date;
  end_date   date := (start_date + INTERVAL '1 month')::date;
  part_name  text := format('bugs_%s', to_char(start_date, 'YYYY_MM'));
BEGIN
  EXECUTE format(
    'CREATE TABLE IF NOT EXISTS %I PARTITION OF bugs FOR VALUES FROM (%L) TO (%L)',
    part_name, start_date, end_date
  );
END $$;
```

Schedule this monthly (e.g., via pg_cron) to pre-create upcoming partitions.

#### Hash partitioning (by tenant or surrogate key)

Use when queries are scoped to a specific tenant and even write distribution matters more than time-range pruning:

```sql
CREATE TABLE bugs (
  bug_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  tenant_id BIGINT NOT NULL,
  date_reported DATE NOT NULL,
  summary TEXT NOT NULL
) PARTITION BY HASH (tenant_id);

CREATE TABLE bugs_t0 PARTITION OF bugs FOR VALUES WITH (MODULUS 8, REMAINDER 0);
CREATE TABLE bugs_t1 PARTITION OF bugs FOR VALUES WITH (MODULUS 8, REMAINDER 1);
-- ... through remainder 7
```

#### Subpartitioning (range within list, or vice versa)

For large multi-tenant datasets with time-range queries:

```sql
CREATE TABLE bugs (
  tenant_id BIGINT NOT NULL,
  date_reported DATE NOT NULL,
  bug_id BIGINT GENERATED ALWAYS AS IDENTITY,
  summary TEXT NOT NULL,
  PRIMARY KEY (tenant_id, date_reported, bug_id)
) PARTITION BY LIST (tenant_id);

CREATE TABLE bugs_tenant_42 PARTITION OF bugs
  FOR VALUES IN (42)
  PARTITION BY RANGE (date_reported);

CREATE TABLE bugs_t42_2026_02 PARTITION OF bugs_tenant_42
  FOR VALUES FROM ('2026-02-01') TO ('2026-03-01');
```

### Querying across partitions

Always query the parent table. PostgreSQL reads as many partitions as needed automatically. No manual UNIONs required.

```sql
-- Spans two monthly partitions; Postgres handles it
SELECT count(*)
FROM bugs
WHERE date_reported >= DATE '2026-01-15'
  AND date_reported <  DATE '2026-03-01';
```

Partition pruning is most effective when the WHERE clause constrains the partition key with plain comparisons (`>=`, `<`, `BETWEEN`). Wrapping the key in expressions (e.g., `date_trunc(...)`) can suppress pruning.

Verify which partitions are actually scanned with:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT * FROM bugs
WHERE date_reported >= DATE '2026-02-01'
  AND date_reported <  DATE '2026-03-01';
```

### Foreign keys with partitioned tables

Reference the partitioned parent directly. Include the partition key in the FK so uniqueness is enforceable:

```sql
CREATE TABLE bug_comments (
  bug_id BIGINT NOT NULL,
  date_reported DATE NOT NULL,
  comment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  body TEXT NOT NULL,
  FOREIGN KEY (bug_id, date_reported)
    REFERENCES bugs (bug_id, date_reported)
);
```

If a stable surrogate FK without the partition key is required, use hash partitioning by `bug_id` (so the PK can be `bug_id` alone), or maintain a small unpartitioned lookup table keyed by `bug_id`.

### Normalizing spawned columns (fix for column-per-year)

Store each year's value as a row, not a column:

```sql
CREATE TABLE customer_revenue (
  customer_id BIGINT NOT NULL,
  year SMALLINT NOT NULL,
  revenue NUMERIC(12,2) NOT NULL,
  PRIMARY KEY (customer_id, year)
);
```

Adding a new year is now an `INSERT`, not an `ALTER TABLE`.

### Vertical partitioning (for wide tables with rarely used columns)

Split bulky or infrequently accessed columns into a companion table to keep the hot path lean:

```sql
CREATE TABLE bugs (
  bug_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  date_reported DATE NOT NULL,
  status TEXT NOT NULL,
  summary TEXT NOT NULL
);

CREATE TABLE bug_details (
  bug_id BIGINT PRIMARY KEY REFERENCES bugs(bug_id) ON DELETE CASCADE,
  description TEXT,
  stacktrace TEXT,
  raw_payload JSONB
);
```

This prevents accidental `SELECT *` from pulling large BLOB/TEXT/JSONB columns in every query.

## Legitimate exception

Manually splitting tables into an archive is reasonable when old data will never be queried alongside current data and the operational tradeoffs are accepted.

## Migration pattern from cloned tables

1. Create the partitioned parent `bugs`.
2. Create partitions matching each legacy table's date range.
3. Bulk-insert each legacy table into the parent (Postgres routes rows automatically):
   ```sql
   INSERT INTO bugs (bug_id, date_reported, status, summary)
   SELECT bug_id, date_reported, status, summary FROM bugs_2025;
   ```
4. Switch application reads/writes to `bugs`.
5. Drop legacy tables after verification.
