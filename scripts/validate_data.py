from __future__ import annotations

import argparse
from pathlib import Path

from sales_warehouse.validation import validate_paths

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate the generated warehouse CSV files."
    )
    parser.add_argument("--root", type=Path, default=REPOSITORY_ROOT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    violations = validate_paths(args.root)
    if violations:
        for violation in violations:
            print(
                f"{violation.code} | {violation.file} | "
                f"{violation.row_key} | {violation.detail}"
            )
        print(f"Validation failed with {len(violations)} violation(s).")
        return 1

    print("Validation passed: 500 customers, 60 products, 5000 sales, 30 delta rows.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
