from __future__ import annotations

import pymssql
import pytest

from sales_warehouse import sql_runner
from sales_warehouse.sql_runner import (
    SqlConfig,
    run_integration,
    split_sql_batches,
    wait_for_sql,
)


def config() -> SqlConfig:
    return SqlConfig(
        host="sql.example.test",
        port=1433,
        user="sa",
        password="DoNotPrintThisPassword!",
        database="warehouse_test",
    )


def test_split_sql_batches_uses_only_standalone_go_lines() -> None:
    script = "SELECT 'go inside text';\nGO\nSELECT 2;\n  go  \nSELECT 3;"

    assert split_sql_batches(script) == (
        "SELECT 'go inside text';",
        "SELECT 2;",
        "SELECT 3;",
    )


def test_config_from_env_reads_required_connection_values(monkeypatch) -> None:
    monkeypatch.setenv("WAREHOUSE_SQL_HOST", "database.internal")
    monkeypatch.setenv("WAREHOUSE_SQL_PORT", "1434")
    monkeypatch.setenv("WAREHOUSE_SQL_USER", "warehouse_user")
    monkeypatch.setenv("WAREHOUSE_SQL_PASSWORD", "secret-value")
    monkeypatch.setenv("WAREHOUSE_SQL_DATABASE", "warehouse_ci_test")

    assert SqlConfig.from_env() == SqlConfig(
        host="database.internal",
        port=1434,
        user="warehouse_user",
        password="secret-value",
        database="warehouse_ci_test",
    )


def test_integration_rejects_database_without_test_suffix(tmp_path) -> None:
    unsafe = SqlConfig(
        host="sql.example.test",
        port=1433,
        user="sa",
        password="secret-value",
        database="sales_warehouse",
    )

    with pytest.raises(ValueError, match="must end with '_test'"):
        run_integration(tmp_path, unsafe)


def test_database_creation_uses_a_separate_sql_batch(monkeypatch) -> None:
    statements: list[str] = []

    class Cursor:
        def execute(self, statement: str) -> None:
            statements.append(statement)

        def close(self) -> None:
            pass

    class Connection:
        def cursor(self) -> Cursor:
            return Cursor()

        def close(self) -> None:
            pass

    monkeypatch.setattr(sql_runner, "_connect", lambda _config: Connection())

    sql_runner._reset_test_database(config())

    assert len(statements) == 2
    assert "DROP DATABASE [warehouse_test]" in statements[0]
    assert statements[1].strip() == "CREATE DATABASE [warehouse_test];"


def test_wait_for_sql_retries_until_connection_succeeds(monkeypatch) -> None:
    attempts = 0
    sleeps: list[float] = []

    class Connection:
        closed = False

        def close(self) -> None:
            self.closed = True

    connection = Connection()

    def connect(_config: SqlConfig, database: str = "master") -> Connection:
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise pymssql.OperationalError("not ready")
        assert database == "master"
        return connection

    monkeypatch.setattr(sql_runner, "_connect", connect)
    monkeypatch.setattr(sql_runner.time, "sleep", sleeps.append)

    wait_for_sql(config(), attempts=3, delay_seconds=0.25)

    assert attempts == 3
    assert sleeps == [0.25, 0.25]
    assert connection.closed is True


def test_wait_for_sql_stops_without_exposing_password(monkeypatch) -> None:
    call_count = 0

    def connect(_config: SqlConfig, database: str = "master") -> None:
        nonlocal call_count
        call_count += 1
        raise pymssql.OperationalError("still starting")

    monkeypatch.setattr(sql_runner, "_connect", connect)
    monkeypatch.setattr(sql_runner.time, "sleep", lambda _seconds: None)

    with pytest.raises(TimeoutError) as captured:
        wait_for_sql(config(), attempts=2, delay_seconds=0)

    message = str(captured.value)
    assert call_count == 2
    assert "sql.example.test" in message
    assert "1433" in message
    assert "2 attempts" in message
    assert "DoNotPrintThisPassword!" not in message
