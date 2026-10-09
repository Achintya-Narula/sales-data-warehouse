from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from pathlib import Path
from typing import Callable, Iterable, TypeVar

from .generator import END_DATE, START_DATE, Customer, GeneratedDataset, Product, Sale

MONEY = Decimal("0.01")
Row = TypeVar("Row", Customer, Product, Sale)


@dataclass(frozen=True, slots=True)
class Violation:
    code: str
    file: str
    row_key: str
    detail: str


def _duplicate_key_violations(
    rows: Iterable[Row],
    key: Callable[[Row], str],
    file_name: str,
) -> list[Violation]:
    seen: set[str] = set()
    duplicates: list[Violation] = []

    for row in rows:
        row_key = key(row)
        if row_key in seen:
            duplicates.append(
                Violation(
                    code="duplicate_key",
                    file=file_name,
                    row_key=row_key,
                    detail="Business key appears more than once.",
                )
            )
        seen.add(row_key)

    return duplicates


def _required_text(
    values: Iterable[tuple[str, str]], file_name: str, row_key: str
) -> list[Violation]:
    return [
        Violation(
            code="required_value",
            file=file_name,
            row_key=row_key,
            detail=f"{field_name} must not be blank.",
        )
        for field_name, value in values
        if not value.strip()
    ]


def _identifier_violations(
    rows: Iterable[Row],
    key: Callable[[Row], str],
    pattern: str,
    file_name: str,
) -> list[Violation]:
    return [
        Violation(
            code="invalid_identifier",
            file=file_name,
            row_key=key(row),
            detail=f"Business key must match {pattern}.",
        )
        for row in rows
        if re.fullmatch(pattern, key(row)) is None
    ]


def _row_count_violation(
    rows: Iterable[Row], expected: int, file_name: str
) -> list[Violation]:
    actual = sum(1 for _ in rows)
    if actual == expected:
        return []
    return [
        Violation(
            code="row_count",
            file=file_name,
            row_key="",
            detail=f"Expected {expected} rows, found {actual}.",
        )
    ]


def validate_dataset(dataset: GeneratedDataset) -> tuple[Violation, ...]:
    violations: list[Violation] = []
    violations.extend(_row_count_violation(dataset.customers, 500, "customers.csv"))
    violations.extend(_row_count_violation(dataset.products, 60, "products.csv"))
    violations.extend(_row_count_violation(dataset.sales, 5_000, "sales.csv"))
    violations.extend(
        _row_count_violation(dataset.customer_delta, 30, "customers_delta.csv")
    )
    violations.extend(
        _duplicate_key_violations(
            dataset.customers, lambda row: row.customer_id, "customers.csv"
        )
    )
    violations.extend(
        _duplicate_key_violations(
            dataset.products, lambda row: row.product_id, "products.csv"
        )
    )
    violations.extend(
        _identifier_violations(
            dataset.customers, lambda row: row.customer_id, r"C\d{4}", "customers.csv"
        )
    )
    violations.extend(
        _identifier_violations(
            dataset.products, lambda row: row.product_id, r"P\d{3}", "products.csv"
        )
    )
    violations.extend(
        _identifier_violations(
            dataset.sales, lambda row: row.sale_id, r"S\d{5}", "sales.csv"
        )
    )
    violations.extend(
        _identifier_violations(
            dataset.customer_delta,
            lambda row: row.customer_id,
            r"C\d{4}",
            "customers_delta.csv",
        )
    )
    violations.extend(
        _duplicate_key_violations(dataset.sales, lambda row: row.sale_id, "sales.csv")
    )
    violations.extend(
        _duplicate_key_violations(
            dataset.customer_delta,
            lambda row: row.customer_id,
            "customers_delta.csv",
        )
    )

    customers = {row.customer_id: row for row in dataset.customers}
    products = {row.product_id: row for row in dataset.products}

    for customer in dataset.customers:
        violations.extend(
            _required_text(
                (
                    ("customer_id", customer.customer_id),
                    ("customer_name", customer.customer_name),
                    ("city", customer.city),
                    ("state", customer.state),
                    ("segment", customer.segment),
                ),
                "customers.csv",
                customer.customer_id,
            )
        )

    for product in dataset.products:
        violations.extend(
            _required_text(
                (
                    ("product_id", product.product_id),
                    ("product_name", product.product_name),
                    ("category", product.category),
                ),
                "products.csv",
                product.product_id,
            )
        )

    for sale in dataset.sales:
        violations.extend(
            _required_text(
                (
                    ("sale_id", sale.sale_id),
                    ("customer_id", sale.customer_id),
                    ("product_id", sale.product_id),
                ),
                "sales.csv",
                sale.sale_id,
            )
        )

        customer = customers.get(sale.customer_id)
        if not START_DATE <= sale.sale_date <= END_DATE:
            violations.append(
                Violation(
                    code="invalid_date",
                    file="sales.csv",
                    row_key=sale.sale_id,
                    detail=(
                        f"Sale date must be between {START_DATE.isoformat()} and "
                        f"{END_DATE.isoformat()}."
                    ),
                )
            )
        if customer is None:
            violations.append(
                Violation(
                    code="unknown_customer",
                    file="sales.csv",
                    row_key=sale.sale_id,
                    detail=(
                        f"Customer {sale.customer_id} is not present in the "
                        "customer file."
                    ),
                )
            )
        elif sale.sale_date < customer.signup_date:
            violations.append(
                Violation(
                    code="invalid_date",
                    file="sales.csv",
                    row_key=sale.sale_id,
                    detail="Sale date is earlier than the customer's signup date.",
                )
            )

        if sale.product_id not in products:
            violations.append(
                Violation(
                    code="unknown_product",
                    file="sales.csv",
                    row_key=sale.sale_id,
                    detail=(
                        f"Product {sale.product_id} is not present in the product file."
                    ),
                )
            )

        if sale.quantity <= 0:
            violations.append(
                Violation(
                    code="invalid_quantity",
                    file="sales.csv",
                    row_key=sale.sale_id,
                    detail="Quantity must be greater than zero.",
                )
            )

        expected_amount = (
            Decimal(sale.quantity)
            * sale.unit_price
            * (Decimal("1.00") - sale.discount_rate)
        ).quantize(MONEY, rounding=ROUND_HALF_UP)
        if sale.sales_amount != expected_amount:
            violations.append(
                Violation(
                    code="amount_mismatch",
                    file="sales.csv",
                    row_key=sale.sale_id,
                    detail=f"Expected {expected_amount}, found {sale.sales_amount}.",
                )
            )

    for customer in dataset.customer_delta:
        violations.extend(
            _required_text(
                (
                    ("customer_id", customer.customer_id),
                    ("customer_name", customer.customer_name),
                    ("city", customer.city),
                    ("state", customer.state),
                    ("segment", customer.segment),
                ),
                "customers_delta.csv",
                customer.customer_id,
            )
        )
        if customer.customer_id not in customers:
            violations.append(
                Violation(
                    code="delta_unknown_customer",
                    file="customers_delta.csv",
                    row_key=customer.customer_id,
                    detail="Delta rows must target an existing customer.",
                )
            )

    return tuple(violations)


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _parse_error(file_name: str, error: Exception) -> tuple[Violation, ...]:
    return (
        Violation(
            code="parse_error",
            file=file_name,
            row_key="",
            detail=str(error),
        ),
    )


def validate_paths(root: Path) -> tuple[Violation, ...]:
    try:
        customer_rows = _read_rows(root / "data" / "generated" / "customers.csv")
        customers = tuple(
            Customer(
                customer_id=row["customer_id"],
                customer_name=row["customer_name"],
                city=row["city"],
                state=row["state"],
                segment=row["segment"],
                signup_date=date.fromisoformat(row["signup_date"]),
            )
            for row in customer_rows
        )
    except (OSError, KeyError, TypeError, ValueError, InvalidOperation) as error:
        return _parse_error("customers.csv", error)

    try:
        product_rows = _read_rows(root / "data" / "generated" / "products.csv")
        products = tuple(
            Product(
                product_id=row["product_id"],
                product_name=row["product_name"],
                category=row["category"],
                unit_price=Decimal(row["unit_price"]),
            )
            for row in product_rows
        )
    except (OSError, KeyError, TypeError, ValueError, InvalidOperation) as error:
        return _parse_error("products.csv", error)

    try:
        sale_rows = _read_rows(root / "data" / "generated" / "sales.csv")
        sales = tuple(
            Sale(
                sale_id=row["sale_id"],
                sale_date=date.fromisoformat(row["sale_date"]),
                customer_id=row["customer_id"],
                product_id=row["product_id"],
                quantity=int(row["quantity"]),
                unit_price=Decimal(row["unit_price"]),
                discount_rate=Decimal(row["discount_rate"]),
                sales_amount=Decimal(row["sales_amount"]),
            )
            for row in sale_rows
        )
    except (OSError, KeyError, TypeError, ValueError, InvalidOperation) as error:
        return _parse_error("sales.csv", error)

    try:
        delta_rows = _read_rows(root / "data" / "delta" / "customers_delta.csv")
        customer_delta = tuple(
            Customer(
                customer_id=row["customer_id"],
                customer_name=row["customer_name"],
                city=row["city"],
                state=row["state"],
                segment=row["segment"],
                signup_date=date.fromisoformat(row["signup_date"]),
            )
            for row in delta_rows
        )
    except (OSError, KeyError, TypeError, ValueError, InvalidOperation) as error:
        return _parse_error("customers_delta.csv", error)

    dataset = GeneratedDataset(
        customers=customers,
        products=products,
        sales=sales,
        customer_delta=customer_delta,
    )
    return validate_dataset(dataset)
