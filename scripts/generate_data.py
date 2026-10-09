from __future__ import annotations

import argparse
import csv
from pathlib import Path

from sales_warehouse.generator import generate_dataset, write_dataset

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate deterministic warehouse CSV files."
    )
    parser.add_argument("--output-root", type=Path, default=REPOSITORY_ROOT)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def count_rows(path: Path) -> int:
    with path.open(encoding="utf-8", newline="") as handle:
        return sum(1 for _ in csv.DictReader(handle))


def main() -> int:
    args = parse_args()
    paths = write_dataset(generate_dataset(seed=args.seed), args.output_root)
    for name, path in paths.items():
        print(f"{name}: {path} ({count_rows(path)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
