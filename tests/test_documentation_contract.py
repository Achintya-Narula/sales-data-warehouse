from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
BUILD_NOTES = ROOT / "docs" / "build-notes.md"
LICENSE = ROOT / "LICENSE"


def test_readme_covers_problem_architecture_setup_evidence_and_limits() -> None:
    text = README.read_text(encoding="utf-8")

    for heading in (
        "# Sales Data Warehouse",
        "## Why I built it",
        "## Data flow",
        "## Warehouse model",
        "## Run it locally",
        "## Verification",
        "## Limits",
    ):
        assert heading in text


def test_readme_records_exact_reproducible_counts_and_commands() -> None:
    text = README.read_text(encoding="utf-8")

    for count in (
        "500 customers",
        "60 products",
        "5,000 sales",
        "30 changed customers",
    ):
        assert count in text
    assert "python scripts/generate_data.py --output-root . --seed 42" in text
    assert "python scripts/validate_data.py --root ." in text
    assert 'python -m pytest -m "not integration" -q' in text
    assert "python scripts/run_sql_integration.py" in text


def test_build_notes_explain_merge_risk_and_production_alternative() -> None:
    text = BUILD_NOTES.read_text(encoding="utf-8")

    assert "MERGE" in text
    assert "explicit `UPDATE` and `INSERT` phases" in text
    assert "locking" in text
    assert "retry" in text
    assert "Power BI" in text


def test_public_prose_avoids_prohibited_dash_characters() -> None:
    text = README.read_text(encoding="utf-8") + BUILD_NOTES.read_text(encoding="utf-8")

    assert "\N{EM DASH}" not in text
    assert "\N{EN DASH}" not in text


def test_repository_uses_mit_license() -> None:
    text = LICENSE.read_text(encoding="utf-8")

    assert text.startswith("MIT License\n")
    assert "Copyright (c) 2026 Achintya Narula" in text
