from __future__ import annotations

from typing import Any, Iterable

import pandas as pd


def normalize_empty_strings(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert empty strings or whitespace-only strings to pd.NA.
    """
    out = df.copy()

    for col in out.columns:
        if out[col].dtype == "object":
            out[col] = out[col].replace(r"^\s*$", pd.NA, regex=True)

    return out


def safe_to_numeric(series: pd.Series) -> pd.Series:
    """
    Convert a pandas Series to numeric.
    Invalid values become NaN.
    """
    return pd.to_numeric(series, errors="coerce")


def ensure_columns_exist(df: pd.DataFrame, required_columns: Iterable[str]) -> None:
    """
    Raise error if dataset does not contain required columns.
    """
    missing = [col for col in required_columns if col not in df.columns]

    if missing:
        raise ValueError(f"Missing required columns: {missing}")


def value_to_string(value: Any) -> str:
    """
    Convert values safely for report/export.
    """
    if pd.isna(value):
        return ""
    return str(value)


def empty_issue_dataframe(columns: list[str]) -> pd.DataFrame:
    """
    Create an empty issue dataframe with standard output columns.
    """
    return pd.DataFrame(columns=columns)