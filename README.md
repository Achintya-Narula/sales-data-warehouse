# Sales Data Warehouse

A reproducible SQL Server warehouse built from deterministic fictional sales data. It covers source generation, data-quality checks, dimensional modelling, SCD Type 1 updates, analytical SQL, DAX measures, and automated verification.

This is a focused learning project, not a production data platform. Its limits are documented alongside the parts that work.

## Why I built it

Most small data projects begin with a table that is already clean. I wanted to work through what has to happen before that point: generating repeatable inputs, rejecting bad records, designing dimensions and a fact table, loading changes safely, and proving that a second run does not create duplicates.

The 30-row customer delta is important to the project. Without it, the dimension load would demonstrate inserts but would never prove that an existing customer can be updated.

## What is included

- Deterministic Python generation for 500 customers, 60 products, 5,000 sales, and 30 changed customers.
- Validation for duplicate keys, required values, references, dates, quantities, and decimal arithmetic.
- SQL Server staging, customer, product, date, and sales fact tables.
- SCD Type 1 customer and product loads with conditional `MERGE` branches.
- An idempotent fact load that rejects unresolved dimension keys.
- Monthly revenue, customer ranking, product ranking, month-over-month revenue, and repeat-customer views.
- Five readable Power BI measures stored as DAX.
- Python tests, SQL contract tests, and a container-backed SQL Server integration workflow.

## Data flow

1. `scripts/generate_data.py` creates the base CSV files and customer delta from a fixed seed.
2. `scripts/validate_data.py` checks the files before any database work begins.
3. Python loads the base files into the `stg` schema with parameterized inserts.
4. `etl.usp_LoadDimensions` loads the three dimensions and reports insert and update actions.
5. `etl.usp_LoadFactSales` resolves surrogate keys and loads each sale once.
6. The customer staging table is replaced with the 30-row delta.
7. The dimension procedure runs twice. The first delta run should update 30 customers; the repeated run should update zero.
8. Verification queries check final row counts and duplicate business keys.

## Warehouse model

| Layer | Object | Purpose |
| --- | --- | --- |
| Staging | `stg.Customer`, `stg.Product`, `stg.Sale` | Typed landing tables for the generated CSV files |
| Dimension | `dw.DimCustomer` | Customer attributes with a surrogate key and Type 1 updates |
| Dimension | `dw.DimProduct` | Product attributes and prices with a surrogate key |
| Dimension | `dw.DimDate` | One row per date from 2024-01-01 through 2025-12-31 |
| Fact | `dw.FactSales` | Quantity, price, discount, and sales amount linked to all three dimensions |
| Analytics | `dw.vw_*` | Monthly, customer, product, trend, and repeat-customer views |

Business identifiers remain unique in the dimensions and fact. Foreign keys protect every fact-to-dimension relationship. The load uses surrogate keys for joins while preserving source identifiers for traceability.

## Repository guide

```text
.github/workflows/ci.yml        Python checks and SQL Server integration
data/generated/                 Deterministic base CSV files
data/delta/                     Thirty changed customer rows
docs/build-notes.md             Decisions, assumptions, and production changes
powerbi/measures.dax            Five Power BI measures
scripts/                        Generation, validation, and integration commands
sql/                            Ordered schema, load, and analytics scripts
src/sales_warehouse/            Python generation, validation, and SQL runner code
tests/                          Unit, contract, documentation, and integration tests
```

## Run it locally

### Python checks

Python 3.12 is required. On Windows PowerShell:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python scripts/generate_data.py --output-root . --seed 42
python scripts/validate_data.py --root .
python -m pytest -m "not integration" -q
```

The generation command rewrites the checked sample files. A clean `git diff -- data` after generation proves that the same seed produced the committed bytes.

### SQL Server integration

The GitHub Actions workflow runs the database scenario with SQL Server 2022 CU27. To run it from Windows PowerShell with Docker:

```powershell
$image = "mcr.microsoft.com/mssql/server:2022-CU27-ubuntu-22.04@sha256:4402d880dd4c34bfa7d8705e56a86cd6c88da80a1f6bbbe741f999e76264a090"
$password = "WarehouseLocal_$(Get-Random)_A9!"

docker run --name warehouse-sql --detach --publish 1433:1433 `
  --env ACCEPT_EULA=Y --env MSSQL_SA_PASSWORD="$password" $image

$env:WAREHOUSE_SQL_HOST = "localhost"
$env:WAREHOUSE_SQL_PORT = "1433"
$env:WAREHOUSE_SQL_USER = "sa"
$env:WAREHOUSE_SQL_PASSWORD = $password
$env:WAREHOUSE_SQL_DATABASE = "sales_warehouse_local_test"

python scripts/run_sql_integration.py
docker rm --force warehouse-sql
```

The integration command refuses to reset a database unless its name ends with `_test`. This guard keeps the destructive test reset away from ordinary database names.

## Verification

| Check | Evidence |
| --- | --- |
| Same input seed produces the same bytes | `tests/test_generator.py` compares SHA-256 hashes |
| Generated records satisfy business rules | `tests/test_data_quality.py` and `tests/test_scd_delta.py` |
| Required SQL objects and query patterns exist | `tests/test_sql_contracts.py` |
| Readiness polling is bounded and passwords stay out of errors | `tests/test_sql_runner.py` |
| SQL runs against a real database engine | `tests/test_sql_integration.py` and `.github/workflows/ci.yml` |
| Public documentation keeps its required evidence and limits | `tests/test_documentation_contract.py` |

The integration scenario asserts 500 initial customers, 30 first-pass updates, zero repeated updates, 500 final customers, zero duplicate customer identifiers, and 5,000 fact rows.

## Resume claim map

| Claim | Where to inspect it |
| --- | --- |
| Deterministic Python data pipeline | `src/sales_warehouse/generator.py` and generator tests |
| Data-quality validation | `src/sales_warehouse/validation.py` and validation tests |
| SQL Server dimensional model | `sql/00_create_schema.sql` through `sql/03_create_fact_sales.sql` |
| SCD Type 1 customer updates | `sql/04_load_dimensions.sql` and the integration test |
| Idempotent fact loading | `sql/05_load_fact_sales.sql` |
| Analytical SQL and DAX | `sql/06_analytics.sql` and `powerbi/measures.dax` |
| Container-backed CI | `.github/workflows/ci.yml` |

## Limits

- All records are fictional and generated locally. There is no external business dataset.
- SCD Type 1 keeps only the latest tracked customer and product values. It does not preserve history.
- `MERGE` is used for a controlled batch demonstration with one writer. It is not presented as the default answer for a highly concurrent production load.
- The DAX file is reviewable source text. This repository does not include a binary Power BI report, and DAX execution is not part of CI.
- There is no scheduler, cloud deployment, streaming ingestion, currency conversion, or operational monitoring.

The reasoning behind these boundaries and the changes I would make for production are in [the build notes](docs/build-notes.md).

## License

MIT
