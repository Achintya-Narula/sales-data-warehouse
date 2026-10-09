from __future__ import annotations

import csv
import random
from dataclasses import asdict, dataclass, fields
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Iterable, TypeVar


MONEY = Decimal("0.01")
START_DATE = date(2024, 1, 1)
END_DATE = date(2025, 12, 31)

LOCATIONS = (
    ("Ahmedabad", "Gujarat"),
    ("Bengaluru", "Karnataka"),
    ("Chandigarh", "Chandigarh"),
    ("Chennai", "Tamil Nadu"),
    ("Delhi", "Delhi"),
    ("Hyderabad", "Telangana"),
    ("Jaipur", "Rajasthan"),
    ("Kochi", "Kerala"),
    ("Kolkata", "West Bengal"),
    ("Mumbai", "Maharashtra"),
    ("Pune", "Maharashtra"),
)
SEGMENTS = ("Consumer", "Corporate", "Small Business")
CATEGORIES = ("Electronics", "Home", "Office", "Software")
DISCOUNTS = tuple(Decimal(value) for value in ("0.00", "0.05", "0.10", "0.15", "0.20"))


@dataclass(frozen=True, slots=True)
class Customer:
    customer_id: str
    customer_name: str
    city: str
    state: str
    segment: str
    signup_date: date


@dataclass(frozen=True, slots=True)
class Product:
    product_id: str
    product_name: str
    category: str
    unit_price: Decimal


@dataclass(frozen=True, slots=True)
class Sale:
    sale_id: str
    sale_date: date
    customer_id: str
    product_id: str
    quantity: int
    unit_price: Decimal
    discount_rate: Decimal
    sales_amount: Decimal


@dataclass(frozen=True, slots=True)
class GeneratedDataset:
    customers: tuple[Customer, ...]
    products: tuple[Product, ...]
    sales: tuple[Sale, ...]
    customer_delta: tuple[Customer, ...]


Row = TypeVar("Row", Customer, Product, Sale)


def _generate_customers(rng: random.Random) -> tuple[Customer, ...]:
    customers: list[Customer] = []
    signup_start = date(2022, 1, 1)

    for number in range(1, 501):
        city, state = rng.choice(LOCATIONS)
        customers.append(
            Customer(
                customer_id=f"C{number:04d}",
                customer_name=f"Customer {number:04d}",
                city=city,
                state=state,
                segment=rng.choice(SEGMENTS),
                signup_date=signup_start + timedelta(days=rng.randrange(730)),
            )
        )

    return tuple(customers)


def _generate_products() -> tuple[Product, ...]:
    products: list[Product] = []

    for number in range(1, 61):
        category = CATEGORIES[(number - 1) % len(CATEGORIES)]
        price = (Decimal("149.00") + Decimal(number * 37)).quantize(MONEY)
        products.append(
            Product(
                product_id=f"P{number:03d}",
                product_name=f"{category} Item {number:02d}",
                category=category,
                unit_price=price,
            )
        )

    return tuple(products)


def _generate_sales(
    rng: random.Random,
    customers: tuple[Customer, ...],
    products: tuple[Product, ...],
) -> tuple[Sale, ...]:
    sales: list[Sale] = []
    available_days = (END_DATE - START_DATE).days + 1

    for number in range(1, 5_001):
        customer = rng.choice(customers)
        product = rng.choice(products)
        quantity = rng.randint(1, 5)
        discount_rate = rng.choice(DISCOUNTS)
        amount = (
            Decimal(quantity) * product.unit_price * (Decimal("1.00") - discount_rate)
        ).quantize(MONEY, rounding=ROUND_HALF_UP)
        sales.append(
            Sale(
                sale_id=f"S{number:05d}",
                sale_date=START_DATE + timedelta(days=rng.randrange(available_days)),
                customer_id=customer.customer_id,
                product_id=product.product_id,
                quantity=quantity,
                unit_price=product.unit_price,
                discount_rate=discount_rate,
                sales_amount=amount,
            )
        )

    return tuple(sales)


def _generate_customer_delta(customers: tuple[Customer, ...]) -> tuple[Customer, ...]:
    location_index = {location: index for index, location in enumerate(LOCATIONS)}
    segment_index = {segment: index for index, segment in enumerate(SEGMENTS)}
    changed: list[Customer] = []

    for customer in customers[:30]:
        current_location = (customer.city, customer.state)
        city, state = LOCATIONS[(location_index[current_location] + 1) % len(LOCATIONS)]
        segment = SEGMENTS[(segment_index[customer.segment] + 1) % len(SEGMENTS)]
        changed.append(
            Customer(
                customer_id=customer.customer_id,
                customer_name=customer.customer_name,
                city=city,
                state=state,
                segment=segment,
                signup_date=customer.signup_date,
            )
        )

    return tuple(changed)


def generate_dataset(seed: int = 42) -> GeneratedDataset:
    rng = random.Random(seed)
    customers = _generate_customers(rng)
    products = _generate_products()
    sales = _generate_sales(rng, customers, products)
    return GeneratedDataset(
        customers=customers,
        products=products,
        sales=sales,
        customer_delta=_generate_customer_delta(customers),
    )


def _serialise(value: object) -> str | int:
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, (str, int)):
        return value
    raise TypeError(f"Unsupported CSV value: {type(value).__name__}")


def _write_rows(path: Path, rows: Iterable[Row], row_type: type[Row]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    field_names = [field.name for field in fields(row_type)]

    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=field_names, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: _serialise(value) for key, value in asdict(row).items()})


def write_dataset(dataset: GeneratedDataset, root: Path) -> dict[str, Path]:
    paths = {
        "customers": root / "data" / "generated" / "customers.csv",
        "products": root / "data" / "generated" / "products.csv",
        "sales": root / "data" / "generated" / "sales.csv",
        "customer_delta": root / "data" / "delta" / "customers_delta.csv",
    }

    _write_rows(paths["customers"], dataset.customers, Customer)
    _write_rows(paths["products"], dataset.products, Product)
    _write_rows(paths["sales"], dataset.sales, Sale)
    _write_rows(paths["customer_delta"], dataset.customer_delta, Customer)
    return paths
