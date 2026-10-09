# Build Notes

## Scope

I kept this project small enough to reproduce from a clean checkout while still exercising the parts of a warehouse load that can fail quietly: duplicate keys, invalid references, decimal calculations, changed dimension values, unresolved surrogate keys, and repeated execution.

The data is fictional by design. The point is the path from an input contract to a checked warehouse state, not a business conclusion about real customers.

## Assumptions

- A sale identifier represents one product line and is globally unique.
- Customer and product identifiers are stable business keys.
- The generated amounts are unitless fictional values. Currency conversion and taxation are outside this scope.
- Customer and product source rows are complete after Python validation.
- The date dimension covers the full generated sales range from 2024-01-01 through 2025-12-31.
- The demonstration load has one writer.

## Decisions

### Deterministic inputs

The generator uses a local `random.Random` instance and a fixed seed. CSV field order, line endings, identifier ranges, and decimal formatting are stable. This makes source changes visible in Git and allows tests to compare file hashes.

The separate 30-customer delta changes both city and segment for existing identifiers. It exists because a base file alone would not exercise the update branch of an SCD Type 1 load.

### Decimal arithmetic before database loading

Sales amounts use Python `Decimal` with two-place `ROUND_HALF_UP` rounding. Validation recomputes each amount from quantity, unit price, and discount rate before SQL Server receives the row. SQL constraints then provide a second boundary for quantities, prices, discounts, and amounts.

### Surrogate keys with retained business identifiers

Dimensions use integer surrogate keys for fact joins and unique source identifiers for traceability. The fact load stops before insertion if any customer, product, or date key cannot be resolved.

### Conditional Type 1 updates

The dimension procedure uses `MERGE` for this controlled batch exercise. A matched row updates only when a tracked attribute differs. `OUTPUT $action` records insert and update counts, so the integration test can distinguish the first 30 updates from the zero updates expected on the repeated delta.

The staging query ranks duplicate business identifiers before the merge, but Python validation treats a duplicate as a violation. Ranking is a defensive boundary, not permission to accept ambiguous source data.

### Repeatable fact loading

`SaleID` is unique in the fact table. The load inserts only identifiers that do not already exist, which lets the procedure be rerun without adding a second copy of a sale.

### Test database safety

The integration runner recreates its target database to begin from a known state. It refuses to do so unless the database name ends with `_test`. The password is accepted through environment variables and never included in readiness errors.

## MERGE boundary

SQL Server `MERGE` is useful here because the source is a validated batch and the demonstration has one writer. It still has concurrency and troubleshooting tradeoffs. [Microsoft's `MERGE` documentation](https://learn.microsoft.com/en-us/sql/t-sql/statements/merge-transact-sql?view=sql-server-ver17) recommends thorough production testing and notes that separate statements may behave better under heavy concurrency.

For a concurrent production load, I would evaluate explicit `UPDATE` and `INSERT` phases inside a transaction. The implementation would choose locking and isolation from measured workload behavior, retry transient deadlocks, record a batch identifier and row counts, and reject or quarantine duplicate source keys before either write phase.

That approach is longer than the current procedure, but its concurrency behavior and recovery points are easier to reason about under multiple writers.

## Power BI boundary

The repository stores five measures as readable DAX so their definitions can be reviewed in a normal code diff. It does not include a `.pbix` file. Binary report layout, relationships configured inside Power BI, refresh credentials, and rendered visuals are therefore not verified here.

## What I would add for production

1. A durable batch-control table with source hash, start time, end time, status, and row counts.
2. A quarantine path for malformed rows instead of stopping the complete batch.
3. Explicit transaction and retry rules based on concurrency testing.
4. Incremental extraction and watermark handling rather than generated full files.
5. Partitioning and retention rules after measuring table size and query patterns.
6. Secret management, monitoring, alerting, and an orchestrator appropriate to the deployment environment.

I have not added those components because there is no production workload in this repository to justify their configuration.
