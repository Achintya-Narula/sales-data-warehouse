from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "ci.yml"


def workflow_text() -> str:
    return WORKFLOW.read_text(encoding="utf-8")


def test_ci_uses_current_actions_and_read_only_permissions() -> None:
    text = workflow_text()

    assert "permissions:\n  contents: read" in text
    assert text.count("runs-on: ubuntu-24.04") == 2
    assert text.count("uses: actions/checkout@v5") == 2
    assert text.count("uses: actions/setup-python@v6") == 2
    assert text.count('python-version: "3.12"') == 2


def test_ci_runs_data_and_python_verification() -> None:
    text = workflow_text()

    assert "python scripts/generate_data.py --output-root . --seed 42" in text
    assert "python scripts/validate_data.py --root ." in text
    assert "python -m ruff check src scripts tests" in text
    assert 'python -m pytest -m "not integration" -q' in text


def test_ci_pins_sql_server_and_runs_the_real_integration() -> None:
    text = workflow_text()

    assert re.search(
        r"mcr\.microsoft\.com/mssql/server:2022-CU27-ubuntu-22\.04"
        r"@sha256:[0-9a-f]{64}",
        text,
    )
    assert "MSSQL_SA_PASSWORD" in text
    assert "WAREHOUSE_SQL_DATABASE: sales_warehouse_ci_test" in text
    assert "python -m pytest tests/test_sql_integration.py -q" in text
    assert "docker logs warehouse-sql" in text
    assert "if: failure()" in text
