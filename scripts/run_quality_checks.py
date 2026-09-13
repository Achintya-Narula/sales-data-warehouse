from pathlib import Path
import json

from data_quality import run_quality_checks


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    report = run_quality_checks(root / "data" / "source")
    reports = root / "reports"
    reports.mkdir(exist_ok=True)
    (reports / "data_quality_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"passed": report["passed"], "checks_failed": report["checks_failed"], "row_counts": report["row_counts"]}, indent=2))
    if not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
