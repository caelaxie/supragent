# Migration Playbook

Reusable phased template for replacing SQL anti-patterns with normalized, constraint-backed designs.

## 1) Discover
- Define scope: source objects, target model, impacted services/jobs.
- Identify invariants: uniqueness, FK relationships, nullability, ordering, retention.
- Capture baseline metrics: row counts, write rates, query latency, error rates.
- Produce a mapping spec from old shape to new shape (column/table-level).

Exit criteria:
- Target schema approved.
- Data mapping and cutover criteria documented.
- Rollback conditions agreed.

## 2) Dual-Write and Backfill
- Create target schema, indexes, and constraints (defer `VALIDATE` when needed).
- Add dual-write path in application or triggers.
- Backfill historical rows in idempotent batches (`LIMIT`/key ranges/time windows).
- Record progress checkpoints to allow restart.

Execution tips:
- Keep batches small enough to stay under lock/replication thresholds.
- Use `INSERT ... ON CONFLICT ...` or merge logic for re-runnable loads.

Exit criteria:
- Dual-write active.
- Backfill reaches 100% logical coverage.

## 3) Validate
- Compare row counts by key ranges/time windows.
- Compare aggregates/checksums on critical columns.
- Validate referential integrity and uniqueness in target.
- Run shadow reads: old vs new query results for sampled production traffic.

Suggested checks:

```sql
-- Example count parity check by month
SELECT date_trunc('month', created_at) AS bucket, count(*) FROM old_table GROUP BY 1
EXCEPT
SELECT date_trunc('month', created_at) AS bucket, count(*) FROM new_table GROUP BY 1;
```

Exit criteria:
- No unexplained diffs.
- Error budget impact is acceptable.

## 4) Cutover
- Freeze risky schema changes during the window.
- Switch reads to target first (feature flag/canary rollout).
- Switch writes to target after read confidence is established.
- Keep dual-write briefly for fast fallback.

Exit criteria:
- Target handles full read/write load.
- Monitoring remains within SLOs.

## 5) Cleanup
- Disable dual-write.
- Validate and enforce any deferred constraints.
- Remove dead code paths, old tables/columns/views, and obsolete jobs.
- Update runbooks, dashboards, and ownership docs.

Exit criteria:
- Legacy path removed.
- Operational docs reflect new architecture.

## 6) Rollback Plan
- Predefine rollback triggers:
  - integrity violations
  - sustained latency/error regression
  - replication/backpressure risk
- Keep rollback mechanics ready:
  - feature flag to route reads/writes back
  - preserved old schema/data until stabilization
  - replay strategy for writes accepted during partial cutover
- Time-box rollback decision window and assign approvers.

Minimum rollback artifacts:
- One-command or one-flag traffic reversal.
- Last good checkpoint for backfill job.
- Diff report template to reconcile post-rollback drift.
