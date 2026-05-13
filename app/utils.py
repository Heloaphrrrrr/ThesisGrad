from __future__ import annotations

from typing import Any, Iterable
import numpy as np
import pandas as pd


def normalize_empty_strings(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    for col in out.columns:
        if out[col].dtype == "object":
            out[col] = out[col].replace(r"^\s*$", pd.NA, regex=True)

    return out


def safe_to_numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def ensure_columns_exist(df: pd.DataFrame, required_columns: Iterable[str]) -> None:
    missing = [col for col in required_columns if col not in df.columns]

    if missing:
        raise ValueError(f"Missing required columns: {missing}")


def ensure_transaction_id(df: pd.DataFrame, id_column: str) -> pd.DataFrame:
    out = df.copy()

    if id_column not in out.columns:
        out.insert(0, id_column, [f"T{i:08d}" for i in range(len(out))])

    return out


def add_bank_derived_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    if "date" in out.columns:
        parsed = pd.to_datetime(out["date"], errors="coerce")
    elif "DATE" in out.columns:
        out = out.rename(columns={"DATE": "date"})
        parsed = pd.to_datetime(out["date"], errors="coerce")
    else:
        parsed = None

    rename_map = {
        "DOMAIN": "domain",
        "LOCATION": "location",
        "VALUE": "value",
        "TRANSACTION_COUNT": "transaction_count",
    }

    out = out.rename(columns={k: v for k, v in rename_map.items() if k in out.columns})

    if "domain" in out.columns:
        out["domain"] = out["domain"].astype(str).str.strip().str.upper()
        out["domain"] = out["domain"].replace({"RESTRAUNT": "RESTAURANT"})

    if "location" in out.columns:
        out["location"] = out["location"].astype(str).str.strip()

    if parsed is not None:
        out["date"] = parsed
        out["year"] = parsed.dt.year
        out["month"] = parsed.dt.month
        out["day"] = parsed.dt.day
        out["day_of_week"] = parsed.dt.dayofweek

    if "value" in out.columns:
        out["value"] = pd.to_numeric(out["value"], errors="coerce")

    if "transaction_count" in out.columns:
        out["transaction_count"] = pd.to_numeric(
            out["transaction_count"], errors="coerce"
        )

    if "value" in out.columns and "transaction_count" in out.columns:
        denom = out["transaction_count"].replace(0, np.nan)
        out["avg_transaction_value"] = out["value"] / denom

    return out


def severity_from_score(score: float) -> str:
    if score >= 1.0:
        return "critical"
    if score >= 0.5:
        return "high"
    if score >= 0.2:
        return "medium"
    return "low"


def clamp_confidence(value: float) -> float:
    return round(float(max(0.0, min(1.0, value))), 4)