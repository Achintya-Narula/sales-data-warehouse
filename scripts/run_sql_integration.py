from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from sales_warehouse.sql_runner import SqlConfig, run_integration

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    result = run_integration(REPOSITORY_ROOT, SqlConfig.from_env())
    print(json.dumps(asdict(result), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
