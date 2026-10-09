from __future__ import annotations

import csv
from dataclasses import replace
from datetime import date
from decimal import Decimal
from pathlib import Path

from sales_warehouse.generator import generate_dataset, write_dataset
from sales_warehouse.validation import validate_dataset, validate_paths

BASE = generate_dataset(seed=42)


def violation_codes(dataset=BASE) -> set[str]:
    return {violation.code for violation in validate_dataset(dataset)}


def test_duplicate_business_key_is_reported() -> None:
    dataset = replace(BASE, customers=BASE.customers + (BASE.customers[0],))

    assert "duplicate_key" in violation_codes(dataset)


def test_unknown_customer_reference_is_reported() -> None:
    changed_sale = replace(BASE.sales[0], customer_id="C9999")
    dataset = replace(BASE, sales=(changed_sale,) + BASE.sales[1:])

    assert "unknown_customer" in violation_codes(dataset)


def test_unknown_product_reference_is_reported() -> None:
    changed_sale = replace(BASE.sales[0], product_id="P999")
    dataset = replace(BASE, sales=(changed_sale,) + BASE.sales[1:])

    assert "unknown_product" in violation_codes(dataset)


def test_sale_before_customer_signup_is_reported() -> None:
    changed_customer = replace(BASE.customers[0], signup_date=date(2025, 1, 1))
    changed_sale = replace(
        BASE.sales[0],
        customer_id=changed_customer.customer_id,
        sale_date=date(2024, 1, 1),
    )
    dataset = replace(
        BASE,
        customers=(changed_customer,) + BASE.customers[1:],
        sales=(changed_sale,) + BASE.sales[1:],
    )

    assert "invalid_date" in violation_codes(dataset)


def test_nonpositive_quantity_is_reported() -> None:
    changed_sale = replace(BASE.sales[0], quantity=-1)
    dataset = replace(BASE, sales=(changed_sale,) + BASE.sales[1:])

    assert "invalid_quantity" in violation_codes(dataset)


def test_incorrect_sale_arithmetic_is_reported() -> None:
    changed_sale = replace(BASE.sales[0], sales_amount=Decimal("0.01"))
    dataset = replace(BASE, sales=(changed_sale,) + BASE.sales[1:])

    assert "amount_mismatch" in violation_codes(dataset)


def test_blank_required_value_is_reported() -> None:
    changed_product = replace(BASE.products[0], product_name="  ")
    dataset = replace(BASE, products=(changed_product,) + BASE.products[1:])

    assert "required_value" in violation_codes(dataset)


def test_valid_generated_dataset_has_no_violations() -> None:
    assert validate_dataset(BASE) == ()


def test_incorrect_file_row_count_is_reported() -> None:
    dataset = replace(BASE, sales=BASE.sales[:-1])

    assert any(
        violation.code == "row_count" and violation.file == "sales.csv"
        for violation in validate_dataset(dataset)
    )


def test_invalid_business_identifier_is_reported() -> None:
    changed_customer = replace(BASE.customers[0], customer_id="customer-one")
    dataset = replace(BASE, customers=(changed_customer,) + BASE.customers[1:])

    assert "invalid_identifier" in violation_codes(dataset)


def test_sale_outside_date_dimension_range_is_reported() -> None:
    changed_sale = replace(BASE.sales[0], sale_date=date(2026, 1, 1))
    dataset = replace(BASE, sales=(changed_sale,) + BASE.sales[1:])

    assert "invalid_date" in violation_codes(dataset)


def test_written_dataset_can_be_loaded_and_validated(tmp_path: Path) -> None:
    write_dataset(BASE, tmp_path)

    assert validate_paths(tmp_path) == ()


def test_malformed_csv_value_returns_parse_violation(tmp_path: Path) -> None:
    paths = write_dataset(BASE, tmp_path)
    sales_path = paths["sales"]
    with sales_path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
        field_names = list(rows[0])
    rows[0]["quantity"] = "not-an-integer"
    with sales_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=field_names, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    violations = validate_paths(tmp_path)

    assert len(violations) == 1
    assert violations[0].code == "parse_error"
    assert violations[0].file == "sales.csv"
