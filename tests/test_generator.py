from __future__ import annotations

import hashlib
from pathlib import Path

from sales_warehouse.generator import generate_dataset, write_dataset


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_generate_exact_row_counts() -> None:
    dataset = generate_dataset(seed=42)

    assert len(dataset.customers) == 500
    assert len(dataset.products) == 60
    assert len(dataset.sales) == 5_000
    assert len(dataset.customer_delta) == 30


def test_business_keys_are_unique() -> None:
    dataset = generate_dataset(seed=42)

    assert [row.customer_id for row in dataset.customers] == [
        f"C{number:04d}" for number in range(1, 501)
    ]
    assert [row.product_id for row in dataset.products] == [
        f"P{number:03d}" for number in range(1, 61)
    ]
    assert [row.sale_id for row in dataset.sales] == [
        f"S{number:05d}" for number in range(1, 5_001)
    ]


def test_delta_targets_existing_customers_and_changes_tracked_values() -> None:
    dataset = generate_dataset(seed=42)
    customers = {row.customer_id: row for row in dataset.customers}

    assert [row.customer_id for row in dataset.customer_delta] == [
        f"C{number:04d}" for number in range(1, 31)
    ]
    assert all(row.customer_id in customers for row in dataset.customer_delta)
    assert all(
        row.city != customers[row.customer_id].city
        and row.segment != customers[row.customer_id].segment
        for row in dataset.customer_delta
    )


def test_same_seed_writes_identical_files(tmp_path: Path) -> None:
    first_paths = write_dataset(generate_dataset(seed=42), tmp_path / "first")
    second_paths = write_dataset(generate_dataset(seed=42), tmp_path / "second")

    assert first_paths.keys() == second_paths.keys()
    assert {
        name: file_hash(path) for name, path in first_paths.items()
    } == {
        name: file_hash(path) for name, path in second_paths.items()
    }
