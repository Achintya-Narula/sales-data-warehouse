from __future__ import annotations

from dataclasses import replace

from sales_warehouse.generator import generate_dataset
from sales_warehouse.validation import validate_dataset


def test_delta_with_new_customer_id_is_rejected() -> None:
    dataset = generate_dataset(seed=42)
    invalid_delta_row = replace(dataset.customer_delta[0], customer_id="C9999")
    changed_dataset = replace(
        dataset,
        customer_delta=(invalid_delta_row,) + dataset.customer_delta[1:],
    )

    assert any(
        violation.code == "delta_unknown_customer"
        and violation.row_key == "C9999"
        for violation in validate_dataset(changed_dataset)
    )
