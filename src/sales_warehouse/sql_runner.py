from __future__ import annotations

import csv
import os
import re
import time
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any, Iterable

import pymssql

from .validation import validate_paths


@dataclass(frozen=True, slots=True)
class SqlConfig:
    host: str
    port: int
    user: str
    password: str
    database: str

    @classmethod
    def from_env(cls) -> "SqlConfig":
        names = (
            "WAREHOUSE_SQL_HOST",
            "WAREHOUSE_SQL_PORT",
            "WAREHOUSE_SQL_USER",
            "WAREHOUSE_SQL_PASSWORD",
            "WAREHOUSE_SQL_DATABASE",
        )
        missing = [name for name in names if not os.getenv(name)]
        if missing:
            raise RuntimeError(
                "Missing SQL Server environment variables: " + ", ".join(missing)
            )

        return cls(
            host=os.environ["WAREHOUSE_SQL_HOST"],
            port=int(os.environ["WAREHOUSE_SQL_PORT"]),
            user=os.environ["WAREHOUSE_SQL_USER"],
            password=os.environ["WAREHOUSE_SQL_PASSWORD"],
            database=os.environ["WAREHOUSE_SQL_DATABASE"],
        )


@dataclass(frozen=True, slots=True)
class IntegrationResult:
    initial_customers: int
    first_delta_updates: int
    repeated_delta_updates: int
    final_customers: int
    duplicate_business_keys: int
    fact_rows: int


def split_sql_batches(script: str) -> tuple[str, ...]:
    return tuple(
        batch.strip()
        for batch in re.split(r"(?im)^\s*GO\s*$", script)
        if batch.strip()
    )


def _connect(config: SqlConfig, database: str = "master"):
    return pymssql.connect(
        server=config.host,
        port=config.port,
        user=config.user,
        password=config.password,
        database=database,
        login_timeout=5,
        timeout=30,
        as_dict=True,
        autocommit=True,
    )


def wait_for_sql(
    config: SqlConfig,
    attempts: int = 30,
    delay_seconds: float = 2.0,
) -> None:
    if attempts < 1:
        raise ValueError("attempts must be at least 1")
    if delay_seconds < 0:
        raise ValueError("delay_seconds must not be negative")

    for attempt in range(1, attempts + 1):
        try:
            connection = _connect(config)
        except (pymssql.Error, OSError):
            if attempt == attempts:
                break
            time.sleep(delay_seconds)
        else:
            connection.close()
            return

    raise TimeoutError(
        f"SQL Server at {config.host}:{config.port} was not ready after "
        f"{attempts} attempts."
    )


def _quote_database_name(database: str) -> str:
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,127}", database):
        raise ValueError("Database name must be a simple SQL identifier.")
    return f"[{database}]"


def _reset_test_database(config: SqlConfig) -> None:
    quoted_database = _quote_database_name(config.database)
    connection = _connect(config)
    cursor = connection.cursor()
    try:
        cursor.execute(
            f"""
            IF DB_ID(N'{config.database}') IS NOT NULL
            BEGIN
                ALTER DATABASE {quoted_database}
                    SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
                DROP DATABASE {quoted_database};
            END;
            """
        )
        cursor.execute(f"CREATE DATABASE {quoted_database};")
    finally:
        cursor.close()
        connection.close()


def _execute_sql_files(connection: Any, root: Path) -> None:
    cursor = connection.cursor()
    try:
        for path in sorted((root / "sql").glob("*.sql")):
            for batch in split_sql_batches(path.read_text(encoding="utf-8")):
                cursor.execute(batch)
    finally:
        cursor.close()


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _customer_values(rows: Iterable[dict[str, str]]) -> list[tuple[Any, ...]]:
    return [
        (
            row["customer_id"],
            row["customer_name"],
            row["city"],
            row["state"],
            row["segment"],
            date.fromisoformat(row["signup_date"]),
        )
        for row in rows
    ]


def _product_values(rows: Iterable[dict[str, str]]) -> list[tuple[Any, ...]]:
    return [
        (
            row["product_id"],
            row["product_name"],
            row["category"],
            Decimal(row["unit_price"]),
        )
        for row in rows
    ]


def _sale_values(rows: Iterable[dict[str, str]]) -> list[tuple[Any, ...]]:
    return [
        (
            row["sale_id"],
            date.fromisoformat(row["sale_date"]),
            row["customer_id"],
            row["product_id"],
            int(row["quantity"]),
            Decimal(row["unit_price"]),
            Decimal(row["discount_rate"]),
            Decimal(row["sales_amount"]),
        )
        for row in rows
    ]


def _load_base_staging(connection: Any, root: Path) -> None:
    cursor = connection.cursor()
    try:
        cursor.execute(
            "DELETE FROM stg.Sale; DELETE FROM stg.Product; DELETE FROM stg.Customer;"
        )
        cursor.executemany(
            """
            INSERT INTO stg.Customer
                (CustomerID, CustomerName, City, StateName, Segment, SignupDate)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            _customer_values(
                _read_csv(root / "data" / "generated" / "customers.csv")
            ),
        )
        cursor.executemany(
            """
            INSERT INTO stg.Product
                (ProductID, ProductName, Category, UnitPrice)
            VALUES (%s, %s, %s, %s)
            """,
            _product_values(_read_csv(root / "data" / "generated" / "products.csv")),
        )
        cursor.executemany(
            """
            INSERT INTO stg.Sale
                (SaleID, SaleDate, CustomerID, ProductID, Quantity,
                 UnitPrice, DiscountRate, SalesAmount)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            _sale_values(_read_csv(root / "data" / "generated" / "sales.csv")),
        )
    finally:
        cursor.close()


def _load_customer_delta(connection: Any, root: Path) -> None:
    cursor = connection.cursor()
    try:
        cursor.execute("DELETE FROM stg.Customer;")
        cursor.executemany(
            """
            INSERT INTO stg.Customer
                (CustomerID, CustomerName, City, StateName, Segment, SignupDate)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            _customer_values(
                _read_csv(root / "data" / "delta" / "customers_delta.csv")
            ),
        )
    finally:
        cursor.close()


def _execute_dimensions(connection: Any) -> dict[str, int]:
    cursor = connection.cursor()
    try:
        cursor.execute("EXEC etl.usp_LoadDimensions;")
        row = cursor.fetchone()
        if row is None:
            raise RuntimeError("Dimension procedure did not return its action counts.")
        return {key: int(value) for key, value in row.items()}
    finally:
        cursor.close()


def _execute_fact_load(connection: Any) -> int:
    cursor = connection.cursor()
    try:
        cursor.execute("EXEC etl.usp_LoadFactSales;")
        row = cursor.fetchone()
        if row is None:
            raise RuntimeError("Fact procedure did not return an insert count.")
        return int(row["FactRowsInserted"])
    finally:
        cursor.close()


def _scalar(connection: Any, query: str, column: str) -> int:
    cursor = connection.cursor()
    try:
        cursor.execute(query)
        row = cursor.fetchone()
        if row is None:
            raise RuntimeError(f"Verification query returned no value for {column}.")
        return int(row[column])
    finally:
        cursor.close()


def run_integration(root: Path, config: SqlConfig) -> IntegrationResult:
    if re.fullmatch(
        r"sales_warehouse_[a-z0-9_]+_test", config.database.casefold()
    ) is None:
        raise ValueError(
            "WAREHOUSE_SQL_DATABASE must match sales_warehouse_<purpose>_test."
        )

    violations = validate_paths(root)
    if violations:
        raise ValueError(
            f"Generated data has {len(violations)} validation violation(s)."
        )

    wait_for_sql(config)
    _reset_test_database(config)
    connection = _connect(config, database=config.database)
    try:
        _execute_sql_files(connection, root)
        _load_base_staging(connection, root)
        _execute_dimensions(connection)
        initial_customers = _scalar(
            connection,
            "SELECT COUNT(*) AS CustomerCount FROM dw.DimCustomer;",
            "CustomerCount",
        )
        inserted_facts = _execute_fact_load(connection)

        _load_customer_delta(connection, root)
        first_delta = _execute_dimensions(connection)
        repeated_delta = _execute_dimensions(connection)

        final_customers = _scalar(
            connection,
            "SELECT COUNT(*) AS CustomerCount FROM dw.DimCustomer;",
            "CustomerCount",
        )
        duplicate_business_keys = _scalar(
            connection,
            """
            SELECT COALESCE(SUM(DuplicateCount - 1), 0) AS DuplicateBusinessKeys
            FROM
            (
                SELECT COUNT(*) AS DuplicateCount
                FROM dw.DimCustomer
                GROUP BY CustomerID
                HAVING COUNT(*) > 1
            ) AS Duplicates;
            """,
            "DuplicateBusinessKeys",
        )
        fact_rows = _scalar(
            connection,
            "SELECT COUNT(*) AS FactRows FROM dw.FactSales;",
            "FactRows",
        )

        if inserted_facts != fact_rows:
            raise RuntimeError(
                f"Fact procedure inserted {inserted_facts} rows but "
                f"{fact_rows} rows exist."
            )

        return IntegrationResult(
            initial_customers=initial_customers,
            first_delta_updates=first_delta["CustomerUpdates"],
            repeated_delta_updates=repeated_delta["CustomerUpdates"],
            final_customers=final_customers,
            duplicate_business_keys=duplicate_business_keys,
            fact_rows=fact_rows,
        )
    finally:
        connection.close()
