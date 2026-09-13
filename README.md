# Sales Analytics & Data Warehouse Pipeline

[![CI](https://github.com/Achintya-Narula/sales-data-warehouse/actions/workflows/ci.yml/badge.svg)](https://github.com/Achintya-Narula/sales-data-warehouse/actions/workflows/ci.yml)

A SQL Server/T-SQL data engineering project demonstrating how transactional sales data can be staged, transformed into a dimensional warehouse, quality-checked, and exposed for analytical SQL and Power BI.

## Stack
SQL Server, T-SQL, Python, pandas, NumPy, dimensional modeling, ETL, SCD Type 1, Power BI/DAX, pytest.

## Architecture

```text
Generated source CSVs
        |
        v
OLTP schema (oltp)
 Customers | Products | Sales
        |
        v
Staging schema (stg)
        |
        +--> Python data-quality checks
        |
        v
Dimension ETL
 DimCustomer (SCD1)
 DimProduct  (SCD1)
 DimDate
        |
        v
FactSales
        |
        v
Reporting views (rpt)
        |
        +--> Analytical SQL
        +--> Power BI semantic/report layer
```

## What this project demonstrates
- OLTP source tables with PK/FK and domain checks.
- Staging tables that decouple source ingestion from warehouse loading.
- Star schema with surrogate dimension keys and a clearly defined fact grain.
- Date Dimension covering calendar attributes used by BI/reporting.
- SCD Type 1 `MERGE` for Customer and Product dimensions.
- Idempotent-style fact `MERGE` keyed by source `SaleID`.
- Reporting views designed for analyst/BI consumption.
- SQL examples using joins, CTEs, aggregations, `LAG`, and `ROW_NUMBER`.
- Reproducible Python source data plus data-quality checks before loading.

## Generate and validate sample data

```bash
python -m venv .venv
# Activate the environment, then:
pip install -r requirements.txt
PYTHONPATH=src:scripts python scripts/generate_sample_data.py
PYTHONPATH=src:scripts python scripts/run_quality_checks.py
pytest
```

Windows PowerShell can use `$env:PYTHONPATH="src;scripts"` before the Python commands.

The default generator creates **500 customers, 60 products, and 5,000 sales rows**. The quality report checks unique natural keys, required fields, customer/product referential coverage, positive quantities/prices, discount bounds, amount arithmetic, and date validity.

## SQL Server execution order
1. `sql/01_create_oltp.sql`
2. Put the generated CSVs in `C:\data\sales-dw\` or edit the three paths in `02_load_source_data.sql`.
3. `sql/02_load_source_data.sql`
4. `sql/03_create_staging.sql`
5. `sql/04_create_warehouse.sql`
6. `sql/05_etl_dimensions.sql`
7. `sql/06_etl_fact.sql`
8. `sql/07_reporting_views.sql`
9. Use `sql/08_analytics_queries.sql` for analysis examples.

## Data model
See `docs/star_schema.md`. The fact table grain is one source sale line. Dimensions use warehouse surrogate keys while retaining source natural IDs for traceability.

## Why SCD Type 1 here?
For a compact sales analytics demo, current customer/product descriptors are enough. The `MERGE` statements overwrite attributes such as city, segment, category, or active flag when the natural key already exists. A Type 2 model would add effective dates/current flags and preserve history; that is intentionally outside this project's scope.

## Power BI
`powerbi/README.md` provides a recommended semantic model, report pages, and example DAX measures including total revenue, average line value, prior-month revenue, and month-over-month growth.

## Verification status
The Python data generator, data-quality checks, and SQL contract tests are automated with `pytest`. The T-SQL files are written for SQL Server and are included in execution order above; database-level verification requires running them against a SQL Server instance.

## Repository map

```text
data/source/                  reproducible source CSVs
sql/                          OLTP, staging, warehouse, ETL, reporting, and analytics scripts
src/data_quality.py           reusable data-quality checks
scripts/                      sample-data generation and quality-check entry points
tests/                        Python behavior tests and SQL contract tests
docs/star_schema.md           warehouse grain, keys, dimensions, and measures
powerbi/README.md             semantic-model guidance and DAX measures
reports/data_quality_report.json  latest generated quality report
```
