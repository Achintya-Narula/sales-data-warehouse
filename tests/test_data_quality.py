from pathlib import Path

import pandas as pd

from data_quality import run_quality_checks
from generate_sample_data import generate_source_data


def test_generate_source_data_is_reproducible_and_relationally_valid(tmp_path: Path):
    first = tmp_path / "first"
    second = tmp_path / "second"
    generate_source_data(first, seed=42, n_customers=120, n_products=25, n_sales=800)
    generate_source_data(second, seed=42, n_customers=120, n_products=25, n_sales=800)

    for filename in ["customers.csv", "products.csv", "sales.csv"]:
        pd.testing.assert_frame_equal(pd.read_csv(first / filename), pd.read_csv(second / filename))

    report = run_quality_checks(first)
    assert report["passed"] is True
    assert report["checks_failed"] == 0
    assert report["row_counts"] == {"customers": 120, "products": 25, "sales": 800}


def test_quality_checks_detect_orphan_customer_key(tmp_path: Path):
    generate_source_data(tmp_path, seed=7, n_customers=50, n_products=12, n_sales=200)
    sales_path = tmp_path / "sales.csv"
    sales = pd.read_csv(sales_path)
    sales.loc[0, "customer_id"] = 999999
    sales.to_csv(sales_path, index=False)

    report = run_quality_checks(tmp_path)
    assert report["passed"] is False
    assert any(check["name"] == "sales_customer_fk" and not check["passed"] for check in report["checks"])
