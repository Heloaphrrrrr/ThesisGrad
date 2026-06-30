from __future__ import annotations

from typing import Any, Iterable
import numpy as np
import pandas as pd


def parse_ecommerce_invoice_date(series: pd.Series) -> pd.Series:
    text_series = series.astype("string").str.strip()
    iso_mask = text_series.str.match(r"^\d{4}-\d{1,2}-\d{1,2}").fillna(False)

    parsed = pd.Series(pd.NaT, index=series.index, dtype="datetime64[ns]")
    parsed.loc[iso_mask] = pd.to_datetime(
        series.loc[iso_mask],
        errors="coerce",
        dayfirst=False,
    )
    parsed.loc[~iso_mask] = pd.to_datetime(
        series.loc[~iso_mask],
        errors="coerce",
        dayfirst=True,
    )

    failed_mask = parsed.isna() & series.notna()

    if failed_mask.any():
        parsed.loc[failed_mask] = pd.to_datetime(
            series.loc[failed_mask],
            errors="coerce",
            dayfirst=False,
        )

    return parsed


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


def add_ecommerce_derived_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    rename_map = {
        "INVOICE_NO": "invoice_no",
        "CUSTOM_ID": "customer_id",
        "GENDER": "gender",
        "AGE": "age",
        "CATEGORY": "category",
        "QUANTITY": "quantity",
        "PRICE": "price",
        "PAYMENT_METHOD": "payment_method",
        "INVOICE_DATE": "invoice_date",
        "SHOPPING_MALL": "shopping_mall",
    }

    out = out.rename(columns={k: v for k, v in rename_map.items() if k in out.columns})

    if "gender" in out.columns:
        out["gender"] = out["gender"].astype(str).str.strip().str.title()

    if "category" in out.columns:
        out["category"] = out["category"].astype(str).str.strip()

    if "payment_method" in out.columns:
        out["payment_method"] = out["payment_method"].astype(str).str.strip().str.title()

    if "shopping_mall" in out.columns:
        out["shopping_mall"] = out["shopping_mall"].astype(str).str.strip()

    for col in ("age", "quantity"):
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")

    if "price" in out.columns:
        out["price"] = pd.to_numeric(out["price"], errors="coerce")

    if "invoice_date" in out.columns:
        parsed = parse_ecommerce_invoice_date(out["invoice_date"])
        out["invoice_date"] = parsed

        if "invoice_year" not in out.columns:
            out["invoice_year"] = parsed.dt.year
        if "invoice_month" not in out.columns:
            out["invoice_month"] = parsed.dt.month
        if "invoice_day" not in out.columns:
            out["invoice_day"] = parsed.dt.day
        if "day_of_week" not in out.columns:
            out["day_of_week"] = parsed.dt.dayofweek
        if "is_weekend" not in out.columns:
            out["is_weekend"] = parsed.dt.dayofweek.isin([5, 6]).astype(int)

    if "unit_price" not in out.columns and {"price", "quantity"}.issubset(out.columns):
        denom = out["quantity"].replace(0, np.nan)
        out["unit_price"] = out["price"] / denom

    if "age_group" not in out.columns and "age" in out.columns:
        out["age_group"] = pd.cut(
            out["age"],
            bins=[0, 25, 35, 45, 55, np.inf],
            labels=["18_25", "26_35", "36_45", "46_55", "56_plus"],
            include_lowest=True,
        ).astype("object")

    if "quantity_band" not in out.columns and "quantity" in out.columns:
        out["quantity_band"] = pd.cut(
            out["quantity"],
            bins=[0, 1, 3, np.inf],
            labels=["single", "small", "bulk"],
            include_lowest=True,
        ).astype("object")

    return out


def prepare_input_dataframe(df: pd.DataFrame, id_column: str) -> pd.DataFrame:
    out = normalize_empty_strings(df)

    if id_column == "transaction_id":
        out = add_bank_derived_features(out)
        out = ensure_transaction_id(out, id_column)
        return out

    if id_column == "invoice_no":
        out = add_ecommerce_derived_features(out)
        return out

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
