from pathlib import Path
import re

SQL_DIR = Path(__file__).resolve().parents[1] / "sql"


def _sql(name: str) -> str:
    return (SQL_DIR / name).read_text(encoding="utf-8").lower()


def test_warehouse_ddl_defines_star_schema_objects():
    sql = _sql("04_create_warehouse.sql")
    for object_name in ["dimcustomer", "dimproduct", "dimdate", "factsales"]:
        assert re.search(rf"create\s+table\s+dw\.{object_name}", sql)
    assert "customerkey" in sql and "productkey" in sql and "datekey" in sql


def test_dimension_etl_uses_scd_type_1_merge():
    sql = _sql("05_etl_dimensions.sql")
    assert sql.count("merge dw.dimcustomer") == 1
    assert sql.count("merge dw.dimproduct") == 1
    assert "when matched then" in sql
    assert "when not matched" in sql


def test_reporting_and_analytics_include_cte_and_window_functions():
    views = _sql("07_reporting_views.sql")
    analytics = _sql("08_analytics_queries.sql")
    assert "create or alter view" in views
    assert "with monthly_sales as" in analytics
    assert "lag(" in analytics
    assert "row_number() over" in analytics
