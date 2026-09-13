from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd


def _check(name: str, passed: bool, detail: str) -> dict[str, Any]:
    return {"name": name, "passed": bool(passed), "detail": detail}


def run_quality_checks(data_dir: str | Path) -> dict[str, Any]:
    data_dir = Path(data_dir)
    required = {
        "customers": data_dir / "customers.csv",
        "products": data_dir / "products.csv",
        "sales": data_dir / "sales.csv",
    }
    missing = [name for name, path in required.items() if not path.exists()]
    if missing:
        return {
            "passed": False,
            "checks_failed": len(missing),
            "row_counts": {},
            "checks": [_check(f"file_{name}", False, f"Missing {name}.csv") for name in missing],
        }

    customers = pd.read_csv(required["customers"])
    products = pd.read_csv(required["products"])
    sales = pd.read_csv(required["sales"])
    checks: list[dict[str, Any]] = []

    checks.append(_check("customer_id_unique", customers["customer_id"].is_unique, "Customer natural key is unique"))
    checks.append(_check("product_id_unique", products["product_id"].is_unique, "Product natural key is unique"))
    checks.append(_check("sale_id_unique", sales["sale_id"].is_unique, "Sale natural key is unique"))

    required_non_null = {
        "customers": (customers, ["customer_id", "customer_name", "city", "state", "segment"]),
        "products": (products, ["product_id", "product_name", "category", "unit_price"]),
        "sales": (sales, ["sale_id", "sale_date", "customer_id", "product_id", "quantity", "unit_price", "net_amount"]),
    }
    for name, (frame, columns) in required_non_null.items():
        passed = not frame[columns].isna().any().any()
        checks.append(_check(f"{name}_required_not_null", passed, f"Required {name} fields contain no nulls"))

    customer_ids = set(customers["customer_id"])
    product_ids = set(products["product_id"])
    orphan_customers = ~sales["customer_id"].isin(customer_ids)
    orphan_products = ~sales["product_id"].isin(product_ids)
    checks.append(
        _check("sales_customer_fk", not orphan_customers.any(), f"Orphan customer rows: {int(orphan_customers.sum())}")
    )
    checks.append(
        _check("sales_product_fk", not orphan_products.any(), f"Orphan product rows: {int(orphan_products.sum())}")
    )

    positive_qty = (sales["quantity"] > 0).all()
    positive_price = (sales["unit_price"] > 0).all()
    valid_discount = sales["discount_pct"].between(0, 0.5, inclusive="both").all()
    checks.append(_check("positive_quantity", positive_qty, "All quantities are greater than zero"))
    checks.append(_check("positive_unit_price", positive_price, "All unit prices are greater than zero"))
    checks.append(_check("discount_range", valid_discount, "Discounts stay between 0% and 50%"))

    expected_net = (sales["quantity"] * sales["unit_price"] * (1 - sales["discount_pct"])).round(2)
    math_ok = (expected_net.sub(sales["net_amount"]).abs() <= 0.01).all()
    checks.append(_check("net_amount_math", math_ok, "Net amount equals quantity × price × (1 - discount)"))

    parsed_dates = pd.to_datetime(sales["sale_date"], errors="coerce")
    dates_ok = parsed_dates.notna().all() and parsed_dates.between("2024-01-01", "2026-12-31").all()
    checks.append(_check("sale_date_range", dates_ok, "Sale dates are valid and within the demo warehouse range"))

    failed = sum(not item["passed"] for item in checks)
    return {
        "passed": failed == 0,
        "checks_failed": int(failed),
        "row_counts": {
            "customers": int(len(customers)),
            "products": int(len(products)),
            "sales": int(len(sales)),
        },
        "checks": checks,
    }
