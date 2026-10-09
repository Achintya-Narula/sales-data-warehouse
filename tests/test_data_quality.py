from __future__ import annotations

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


def test_written_dataset_can_be_loaded_and_validated(tmp_path: Path) -> None:
    write_dataset(BASE, tmp_path)

    assert validate_paths(tmp_path) == ()
