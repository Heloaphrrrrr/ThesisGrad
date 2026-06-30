import numpy as np
import pandas as pd

from app.config import PipelineConfig
from app.schemas import IssueRecord, make_issue_id
from app.utils import parse_ecommerce_invoice_date


class CrossFieldValidator:
    def __init__(self, config: PipelineConfig):
        self.config = config

    def detect(self, df: pd.DataFrame) -> pd.DataFrame:
        records = []
        records.extend(self._detect_ecommerce_rules(df))
        records.extend(self._detect_bank_rules(df))

        return pd.DataFrame(records, columns=self.config.issue_output_columns)

    def _make_record(self, df, idx, col, current_value, reason, severity="high"):
        severity_score = {
            "low": 0.1,
            "medium": 0.4,
            "high": 0.8,
            "critical": 1.0,
        }.get(severity, 0.5)

        issue = IssueRecord(
            issue_id=make_issue_id(),
            row_id=df.at[idx, self.config.id_column],
            column_name=col,
            issue_type="invalid",
            current_value=current_value,
            suggested_value=None,
            confidence=1.0,
            severity=severity,
            severity_score=severity_score,
            reason=reason,
            source_method="cross_field_rule",
            can_auto_fix=True,
        )
        return issue.to_dict()

    def _detect_ecommerce_rules(self, df: pd.DataFrame) -> list[dict]:
        records = []

        if {"price", "quantity", "unit_price"}.issubset(df.columns):
            records.extend(self._detect_price_quantity_unit_price(df))

        if {"age", "age_group"}.issubset(df.columns):
            records.extend(self._detect_age_group(df))

        if "invoice_date" in df.columns:
            records.extend(self._detect_invoice_date_parts(df))

        return records

    def _detect_price_quantity_unit_price(self, df: pd.DataFrame) -> list[dict]:
        records = []

        price = pd.to_numeric(df["price"], errors="coerce")
        quantity = pd.to_numeric(df["quantity"], errors="coerce")
        unit_price = pd.to_numeric(df["unit_price"], errors="coerce")
        expected_price = quantity * unit_price
        tolerance = np.maximum(price.abs() * 0.001, 0.01)

        mask = price.notna() & quantity.notna() & unit_price.notna()
        mask = mask & (price - expected_price).abs().gt(tolerance)

        for idx in df.index[mask.fillna(False)]:
            records.append(
                self._make_record(
                    df=df,
                    idx=idx,
                    col="unit_price",
                    current_value=df.at[idx, "unit_price"],
                    reason="unit_price is inconsistent with price and quantity.",
                )
            )

        return records

    def _detect_age_group(self, df: pd.DataFrame) -> list[dict]:
        records = []

        age = pd.to_numeric(df["age"], errors="coerce")
        expected = pd.cut(
            age,
            bins=[0, 25, 35, 45, 55, np.inf],
            labels=["18_25", "26_35", "36_45", "46_55", "56_plus"],
            include_lowest=True,
        ).astype("object")

        current = df["age_group"].astype("string").str.strip()
        mask = (
            age.notna()
            & current.notna()
            & current.ne("")
            & current.ne(expected.astype("string"))
        )

        for idx in df.index[mask.fillna(False)]:
            records.append(
                self._make_record(
                    df=df,
                    idx=idx,
                    col="age_group",
                    current_value=df.at[idx, "age_group"],
                    reason="age_group is inconsistent with age.",
                    severity="medium",
                )
            )

        return records

    def _detect_invoice_date_parts(self, df: pd.DataFrame) -> list[dict]:
        records = []
        parsed = parse_ecommerce_invoice_date(df["invoice_date"])

        checks = {
            "invoice_year": parsed.dt.year,
            "invoice_month": parsed.dt.month,
            "invoice_day": parsed.dt.day,
            "day_of_week": parsed.dt.dayofweek,
            "is_weekend": parsed.dt.dayofweek.isin([5, 6]).astype("Int64"),
        }

        for col, expected in checks.items():
            if col not in df.columns:
                continue

            current = pd.to_numeric(df[col], errors="coerce")
            mask = parsed.notna() & current.notna() & current.ne(expected)

            for idx in df.index[mask.fillna(False)]:
                records.append(
                    self._make_record(
                        df=df,
                        idx=idx,
                        col=col,
                        current_value=df.at[idx, col],
                        reason=f"{col} is inconsistent with invoice_date.",
                        severity="medium",
                    )
                )

        return records

    def _detect_bank_rules(self, df: pd.DataFrame) -> list[dict]:
        required_cols = {"value", "transaction_count"}
        if not required_cols.issubset(set(df.columns)):
            return []

        records = []
        value = pd.to_numeric(df["value"], errors="coerce")
        count = pd.to_numeric(df["transaction_count"], errors="coerce")
        mask = (count == 0) & (value > 0)

        for idx in df.index[mask.fillna(False)]:
            records.append(
                self._make_record(
                    df=df,
                    idx=idx,
                    col="transaction_count",
                    current_value=df.at[idx, "transaction_count"],
                    reason="transaction_count is 0 while value is greater than 0.",
                )
            )

        return records
