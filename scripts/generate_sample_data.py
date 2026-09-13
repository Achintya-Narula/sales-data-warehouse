from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


def generate_source_data(
    output_dir: str | Path,
    seed: int = 42,
    n_customers: int = 500,
    n_products: int = 60,
    n_sales: int = 5000,
) -> None:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(seed)

    cities = [
        ("Chandigarh", "Punjab"),
        ("Ludhiana", "Punjab"),
        ("Jaipur", "Rajasthan"),
        ("Delhi", "Delhi"),
        ("Pune", "Maharashtra"),
        ("Bengaluru", "Karnataka"),
        ("Hyderabad", "Telangana"),
        ("Kolkata", "West Bengal"),
    ]
    city_idx = rng.integers(0, len(cities), size=n_customers)
    signup_days = rng.integers(0, 900, size=n_customers)
    customers = pd.DataFrame(
        {
            "customer_id": np.arange(10001, 10001 + n_customers),
            "customer_name": [f"Customer {i:04d}" for i in range(1, n_customers + 1)],
            "city": [cities[i][0] for i in city_idx],
            "state": [cities[i][1] for i in city_idx],
            "segment": rng.choice(["Consumer", "Corporate", "Small Business"], p=[0.58, 0.22, 0.20], size=n_customers),
            "signup_date": (pd.Timestamp("2022-01-01") + pd.to_timedelta(signup_days, unit="D")).strftime("%Y-%m-%d"),
        }
    )

    categories = ["Electronics", "Office Supplies", "Accessories", "Home"]
    product_category = rng.choice(categories, size=n_products, p=[0.30, 0.28, 0.24, 0.18])
    category_base = {"Electronics": 3200, "Office Supplies": 450, "Accessories": 900, "Home": 1600}
    prices = np.array([max(99, rng.normal(category_base[c], category_base[c] * 0.28)) for c in product_category]).round(2)
    products = pd.DataFrame(
        {
            "product_id": np.arange(2001, 2001 + n_products),
            "product_name": [f"Product {i:03d}" for i in range(1, n_products + 1)],
            "category": product_category,
            "unit_price": prices,
            "active_flag": rng.choice([1, 0], p=[0.94, 0.06], size=n_products),
        }
    )

    customer_choices = rng.choice(customers["customer_id"].to_numpy(), size=n_sales)
    product_positions = rng.integers(0, n_products, size=n_sales)
    product_choices = products.iloc[product_positions]["product_id"].to_numpy()
    unit_prices = products.iloc[product_positions]["unit_price"].to_numpy()
    quantities = rng.integers(1, 6, size=n_sales)
    discounts = rng.choice([0.0, 0.05, 0.10, 0.15, 0.20], p=[0.42, 0.20, 0.19, 0.12, 0.07], size=n_sales)
    sale_days = rng.integers(0, 970, size=n_sales)
    sale_dates = pd.Timestamp("2024-01-01") + pd.to_timedelta(sale_days, unit="D")
    net_amount = (quantities * unit_prices * (1 - discounts)).round(2)

    sales = pd.DataFrame(
        {
            "sale_id": np.arange(500001, 500001 + n_sales),
            "sale_date": sale_dates.strftime("%Y-%m-%d"),
            "customer_id": customer_choices,
            "product_id": product_choices,
            "quantity": quantities,
            "unit_price": unit_prices,
            "discount_pct": discounts,
            "net_amount": net_amount,
        }
    ).sort_values(["sale_date", "sale_id"], ignore_index=True)

    customers.to_csv(output_dir / "customers.csv", index=False)
    products.to_csv(output_dir / "products.csv", index=False)
    sales.to_csv(output_dir / "sales.csv", index=False)


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    generate_source_data(root / "data" / "source")
    print("Generated customers.csv, products.csv, and sales.csv")


if __name__ == "__main__":
    main()
