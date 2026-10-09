from __future__ import annotations

import os
from pathlib import Path

import pytest

from sales_warehouse.sql_runner import SqlConfig, run_integration


pytestmark = pytest.mark.integration


def test_complete_sql_server_load_is_idempotent() -> None:
    if not os.getenv("WAREHOUSE_SQL_HOST"):
        pytest.skip("WAREHOUSE_SQL_HOST is not set; SQL Server integration is opt-in")

    config = SqlConfig.from_env()
    result = run_integration(Path(__file__).resolve().parents[1], config)

    assert result.initial_customers == 500
    assert result.first_delta_updates == 30
    assert result.repeated_delta_updates == 0
    assert result.final_customers == 500
    assert result.duplicate_business_keys == 0
    assert result.fact_rows == 5_000
