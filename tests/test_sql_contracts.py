from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SQL_FILES = [
    "00_create_schema.sql",
    "01_create_staging.sql",
    "02_create_dimensions.sql",
    "03_create_fact_sales.sql",
    "04_load_dimensions.sql",
    "05_load_fact_sales.sql",
    "06_analytics.sql",
]


def read_sql(name: str) -> str:
    return (ROOT / "sql" / name).read_text(encoding="utf-8").casefold()


def test_required_sql_files_exist() -> None:
    assert [path.name for path in sorted((ROOT / "sql").glob("*.sql"))] == SQL_FILES


def test_required_schemas_and_tables_are_declared() -> None:
    schema_sql = read_sql("00_create_schema.sql")
    staging_sql = read_sql("01_create_staging.sql")
    dimension_sql = read_sql("02_create_dimensions.sql")
    fact_sql = read_sql("03_create_fact_sales.sql")

    assert all(f"create schema {name}" in schema_sql for name in ("stg", "dw", "etl"))
    assert all(
        f"create table stg.{name}" in staging_sql
        for name in ("customer", "product", "sale")
    )
    assert all(
        f"create table dw.{name}" in dimension_sql
        for name in ("dimcustomer", "dimproduct", "dimdate")
    )
    assert "create table dw.factsales" in fact_sql


def test_dimensional_integrity_is_explicit() -> None:
    dimension_sql = read_sql("02_create_dimensions.sql")
    fact_sql = read_sql("03_create_fact_sales.sql")

    assert dimension_sql.count("primary key") >= 3
    assert "unique (customerid)" in dimension_sql
    assert "unique (productid)" in dimension_sql
    assert "unique (fulldate)" in dimension_sql
    assert "foreign key (datekey) references dw.dimdate(datekey)" in fact_sql
    assert "foreign key (customerkey) references dw.dimcustomer(customerkey)" in fact_sql
    assert "foreign key (productkey) references dw.dimproduct(productkey)" in fact_sql
    assert "check (quantity > 0)" in fact_sql
    assert "check (salesamount >= 0)" in fact_sql
    assert "create index ix_factsales_datekey" in fact_sql


def test_dimension_load_uses_conditional_scd_type_one_merges() -> None:
    load_sql = read_sql("04_load_dimensions.sql")

    assert "create or alter procedure etl.usp_loaddimensions" in load_sql
    assert "merge dw.dimcustomer as target" in load_sql
    assert "merge dw.dimproduct as target" in load_sql
    assert load_sql.count("when matched and") == 2
    assert load_sql.count("then update set") == 2
    assert load_sql.count("when not matched by target then") == 2
    assert "output $action" in load_sql


def test_fact_load_rejects_unresolved_dimensions_and_duplicate_sales() -> None:
    load_sql = read_sql("05_load_fact_sales.sql")

    assert "create or alter procedure etl.usp_loadfactsales" in load_sql
    assert "throw" in load_sql
    assert "left join dw.dimcustomer" in load_sql
    assert "left join dw.dimproduct" in load_sql
    assert "left join dw.dimdate" in load_sql
    assert "not exists" in load_sql


def test_analytics_use_ctes_and_window_functions() -> None:
    analytics_sql = read_sql("06_analytics.sql")

    assert "with monthly_revenue as" in analytics_sql
    assert "lag(" in analytics_sql
    assert analytics_sql.count("row_number() over") >= 2
    assert "repeatcustomer" in analytics_sql


def test_dax_file_contains_the_five_documented_measures() -> None:
    dax = (ROOT / "powerbi" / "measures.dax").read_text(encoding="utf-8")

    for measure in (
        "Total Revenue =",
        "Order Count =",
        "Average Order Value =",
        "Previous Month Revenue =",
        "Revenue MoM % =",
    ):
        assert measure in dax
