"""Data quality checks for MedViet patient datasets."""

from __future__ import annotations

from pathlib import Path
import re

import pandas as pd

VALID_CONDITIONS = ["Tiểu đường", "Huyết áp cao", "Tim mạch", "Khỏe mạnh"]
EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")


def build_patient_expectation_suite() -> dict:
    """Return the lab's expectation suite in a portable dictionary form."""

    return {
        "suite_name": "patient_data_suite",
        "expectations": [
            {"column": "patient_id", "expectation": "not_null"},
            {"column": "cccd", "expectation": "length_equals", "value": 12},
            {
                "column": "ket_qua_xet_nghiem",
                "expectation": "between",
                "min_value": 0,
                "max_value": 50,
            },
            {"column": "benh", "expectation": "in_set", "value_set": VALID_CONDITIONS},
            {"column": "email", "expectation": "matches_regex", "regex": EMAIL_RE.pattern},
            {"column": "patient_id", "expectation": "unique"},
        ],
    }


def _fail(results: dict, message: str) -> None:
    results["success"] = False
    results["failed_checks"].append(message)


def validate_anonymized_data(filepath: str) -> dict:
    """Validate anonymized patient data and return a grading-friendly summary."""

    df = pd.read_csv(filepath, dtype={"cccd": str, "so_dien_thoai": str})
    results = {
        "success": True,
        "failed_checks": [],
        "stats": {
            "total_rows": len(df),
            "columns": list(df.columns),
        },
    }

    original_path = Path("data/raw/patients_raw.csv")
    if "cccd" not in df.columns:
        _fail(results, "Missing cccd column")
    elif not df["cccd"].astype(str).str.fullmatch(r"\d{12}").all():
        _fail(results, "Anonymized cccd values must be 12-digit replacements")

    important_columns = ["patient_id", "cccd", "so_dien_thoai", "email", "benh", "ket_qua_xet_nghiem"]
    missing = [col for col in important_columns if col not in df.columns]
    if missing:
        _fail(results, f"Missing important columns: {missing}")
    else:
        null_columns = [col for col in important_columns if df[col].isna().any()]
        if null_columns:
            _fail(results, f"Null values found in important columns: {null_columns}")

    if original_path.exists():
        original_df = pd.read_csv(original_path, dtype={"cccd": str, "so_dien_thoai": str})
        if len(df) != len(original_df):
            _fail(results, f"Row count mismatch: anonymized={len(df)} original={len(original_df)}")
        if "cccd" in df.columns:
            leaked_cccd = set(df["cccd"].astype(str)) & set(original_df["cccd"].astype(str))
            if leaked_cccd:
                _fail(results, f"Original CCCD values leaked: {len(leaked_cccd)}")

    if "benh" in df.columns and not df["benh"].isin(VALID_CONDITIONS).all():
        _fail(results, "benh contains values outside the approved set")

    return results
