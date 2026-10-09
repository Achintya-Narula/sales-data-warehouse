from __future__ import annotations

import json
import sys
from dataclasses import asdict
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "src"))

from sales_warehouse.sql_runner import SqlConfig, run_integration  # noqa: E402


def main() -> int:
    result = run_integration(REPOSITORY_ROOT, SqlConfig.from_env())
    print(json.dumps(asdict(result), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
