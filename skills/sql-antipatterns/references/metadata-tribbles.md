# Metadata Tribbles

## Objective
Scale data volume without cloning tables or columns for each new time period, tenant, or status value.

## Antipattern
Treat new data values as new schema objects:
- table-per-year / table-per-tenant (`bugs_2024`, `bugs_2025`, ...)
- column-per-year / column-per-status (`revenue2024`, `revenue2025`, ...)

## Why It Fails
- Query fanout: cross-period reports require growing `UNION` chains.
- Schema drift: every DDL change must be repeated everywhere.
- Integrity gaps: one FK cannot target a family of cloned tables.
- Operational misses: outages when the next table/column is not created on time.

## How To Detect
- Repeating table names that differ only by suffix (`_2024`, `_tenant42`, ...).
- Repeating value-cloned columns (`revenue2024`, `revenue2025`, `status_open_count`, `status_closed_count`).
- Runbooks that include "create next month's/year's table."
- Reporting SQL that manually unions many near-identical tables.

Disambiguation:
- If the shape is repeating groups like `phone1`, `phone2`, `tag1`, `tag2` in one table, classify as `multicolumn-attributes` instead of metadata tribbles.

## Legitimate Exceptions
- Cold archive split, where historical data is intentionally isolated and never queried with hot data.
- Engine/platform constraints where true partitioning is unavailable and tradeoffs are explicit.

## Preferred Design
- Keep one logical table per entity.
- Represent changing dimensions as rows, not columns.
- Use partitioning for physical layout, not for logical data modeling.
- Keep FK-backed relationships explicit.

## PostgreSQL Implementation Patterns
1. Partition by an access-aligned key (`date_reported`, `tenant_id`, or hash of stable ID).
2. Query the partitioned parent table; do not manually `UNION` partitions.
3. Pre-create future partitions (scheduler/job) to avoid runtime failures.
4. Keep partition pruning effective:
   - filter directly on the partition key (`>=`, `<`, `BETWEEN`)
   - avoid wrapping the partition key in functions in predicates
   - verify pruning with `EXPLAIN (ANALYZE, BUFFERS)`
5. For FKs involving partitioned tables, remember uniqueness rules:
   - referenced key must be `PRIMARY KEY`/`UNIQUE` on the parent
   - for partitioned parents, that uniqueness must include all partition-key columns
   - child FK must reference that full key (including partition key) if required by parent uniqueness

Example FK pattern (range partitioned by `date_reported`):

```sql
CREATE TABLE bugs (
  bug_id BIGINT NOT NULL,
  date_reported DATE NOT NULL,
  summary TEXT NOT NULL,
  PRIMARY KEY (bug_id, date_reported)
) PARTITION BY RANGE (date_reported);

CREATE TABLE bug_comments (
  comment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  bug_id BIGINT NOT NULL,
  date_reported DATE NOT NULL,
  body TEXT NOT NULL,
  FOREIGN KEY (bug_id, date_reported)
    REFERENCES bugs (bug_id, date_reported)
);
```

## Migration Pattern
1. Create the new canonical parent table and required partitions.
2. Dual-write new traffic to both old and new structures.
3. Backfill historical data into the new model in batches.
4. Validate counts, checksums, and FK integrity.
5. Cut reads, then writes, to the new model.
6. Remove legacy tables/columns only after a stable soak period.

## Rollback Considerations
- Keep legacy tables/columns queryable and writable until partitioned-parent parity checks pass.
- If cutover fails, route reads/writes back to legacy objects and pause partition attach/detach operations.
- Preserve dual-write/backfill checkpoints so replay can resume from last known-good state.

## Version and Engine Caveats
- PostgreSQL parent-level index creation propagates to partitions in PG 11+.
- Partitioned-table uniqueness is per-partition unless partition keys are part of the unique/primary key.
- FK + `ATTACH PARTITION`/`DETACH PARTITION` behavior has received fixes across supported major/minor releases; verify your exact server version against current PostgreSQL release notes before relying on attach/detach-heavy workflows.
- If you operate on older patch levels or mixed fleets, avoid risky attach/detach operations with dependent FKs, or run post-change FK consistency checks and recreate affected constraints if needed.
- Other engines differ: confirm partitioning/FK semantics before porting this guidance.
