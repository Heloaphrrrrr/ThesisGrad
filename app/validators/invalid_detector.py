import pandas as pd

from app.config import PipelineConfig
from app.schemas import IssueRecord, make_issue_id
from app.utils import safe_to_numeric


class InvalidDetector:
    def __init__(self, config: PipelineConfig):
        self.config = config

    def detect(self, df: pd.DataFrame) -> pd.DataFrame:
        records = []

        for col, rule in self.config.rules.items():
            if col not in df.columns:
                continue

            if rule.dtype == "id":
                continue

            series = df[col]

            if rule.dtype == "numeric":
                records.extend(self._detect_numeric_invalid(df, col, series, rule))

            elif rule.dtype == "categorical":
                records.extend(self._detect_categorical_invalid(df, col, series, rule))

            elif rule.dtype == "date":
                records.extend(self._detect_date_invalid(df, col, series, rule))

        return pd.DataFrame(records, columns=self.config.issue_output_columns)

    def _make_record(self, df, idx, col, current_value, reason, severity):
        severity_score = {
            "low": 0.1,
            "medium": 0.4,
            "high": 0.7,
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
            source_method="rule_invalid_detector",
            can_auto_fix=True,
        )
        return issue.to_dict()

    def _detect_numeric_invalid(self, df, col, series, rule):
        records = []
        numeric_series = safe_to_numeric(series)
        non_missing_mask = ~series.isna()
        invalid_type_mask = non_missing_mask & numeric_series.isna()

        for idx in df.index[invalid_type_mask]:
            records.append(
                self._make_record(
                    df=df,
                    idx=idx,
                    col=col,
                    current_value=df.at[idx, col],
                    reason=f"Column '{col}' must be numeric.",
                    severity=rule.severity_if_invalid,
                )
            )

        if rule.min_value is not None:
            mask = numeric_series < rule.min_value
            for idx in df.index[mask.fillna(False)]:
                records.append(
                    self._make_record(
                        df=df,
                        idx=idx,
                        col=col,
                        current_value=df.at[idx, col],
                        reason=f"Value is smaller than minimum allowed: {rule.min_value}.",
                        severity=rule.severity_if_invalid,
                    )
                )

        if rule.max_value is not None:
            mask = numeric_series > rule.max_value
            for idx in df.index[mask.fillna(False)]:
                records.append(
                    self._make_record(
                        df=df,
                        idx=idx,
                        col=col,
                        current_value=df.at[idx, col],
                        reason=f"Value is larger than maximum allowed: {rule.max_value}.",
                        severity=rule.severity_if_invalid,
                    )
                )

        return records

    def _detect_categorical_invalid(self, df, col, series, rule):
        records = []

        if not rule.allowed_values:
            return records

        mask = ~series.isna() & ~series.isin(rule.allowed_values)

        for idx in df.index[mask]:
            records.append(
                self._make_record(
                    df=df,
                    idx=idx,
                    col=col,
                    current_value=df.at[idx, col],
                    reason=f"Value is not in allowed values: {rule.allowed_values}.",
                    severity=rule.severity_if_invalid,
                )
            )

        return records

    def _detect_date_invalid(self, df, col, series, rule):
        records = []

        parsed = pd.to_datetime(series, errors="coerce")
        mask = ~series.isna() & parsed.isna()

        for idx in df.index[mask]:
            records.append(
                self._make_record(
                    df=df,
                    idx=idx,
                    col=col,
                    current_value=df.at[idx, col],
                    reason=f"Column '{col}' has invalid date format.",
                    severity=rule.severity_if_invalid,
                )
            )

        return records