import pandas as pd

from app.config import PipelineConfig
from app.utils import safe_to_numeric


class InvalidDetector:
    """
    Detect invalid data dựa trên rule:
    - numeric: min_value / max_value
    - categorical: allowed_values
    - date: parse lỗi
    """

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
                records.extend(self._detect_date_invalid(df, col, series))

        return pd.DataFrame(records, columns=self.config.issue_output_columns)

    def _detect_numeric_invalid(self, df, col, series, rule):
        records = []
        numeric_series = safe_to_numeric(series)

        non_missing_mask = ~series.isna()

        # Nếu có giá trị không convert được sang số, coi là invalid
        invalid_type_mask = non_missing_mask & numeric_series.isna()

        for idx in df.index[invalid_type_mask]:
            records.append({
                "row_id": df.at[idx, self.config.id_column],
                "column_name": col,
                "issue_type": "invalid",
                "current_value": df.at[idx, col],
                "anomaly_score": None,
                "suggested_value": None,
                "reason": f"Column '{col}' must be numeric.",
                "source_method": "rule_invalid_detector",
            })

        if rule.min_value is not None:
            mask = numeric_series < rule.min_value
            for idx in df.index[mask.fillna(False)]:
                records.append({
                    "row_id": df.at[idx, self.config.id_column],
                    "column_name": col,
                    "issue_type": "invalid",
                    "current_value": df.at[idx, col],
                    "anomaly_score": None,
                    "suggested_value": None,
                    "reason": f"Value is smaller than minimum allowed: {rule.min_value}.",
                    "source_method": "rule_invalid_detector",
                })

        if rule.max_value is not None:
            mask = numeric_series > rule.max_value
            for idx in df.index[mask.fillna(False)]:
                records.append({
                    "row_id": df.at[idx, self.config.id_column],
                    "column_name": col,
                    "issue_type": "invalid",
                    "current_value": df.at[idx, col],
                    "anomaly_score": None,
                    "suggested_value": None,
                    "reason": f"Value is larger than maximum allowed: {rule.max_value}.",
                    "source_method": "rule_invalid_detector",
                })

        return records

    def _detect_categorical_invalid(self, df, col, series, rule):
        records = []

        if not rule.allowed_values:
            return records

        mask = ~series.isna() & ~series.isin(rule.allowed_values)

        for idx in df.index[mask]:
            records.append({
                "row_id": df.at[idx, self.config.id_column],
                "column_name": col,
                "issue_type": "invalid",
                "current_value": df.at[idx, col],
                "anomaly_score": None,
                "suggested_value": None,
                "reason": f"Value is not in allowed values: {rule.allowed_values}.",
                "source_method": "rule_invalid_detector",
            })

        return records

    def _detect_date_invalid(self, df, col, series):
        records = []

        parsed = pd.to_datetime(series, errors="coerce")
        mask = ~series.isna() & parsed.isna()

        for idx in df.index[mask]:
            records.append({
                "row_id": df.at[idx, self.config.id_column],
                "column_name": col,
                "issue_type": "invalid",
                "current_value": df.at[idx, col],
                "anomaly_score": None,
                "suggested_value": None,
                "reason": f"Column '{col}' has invalid date format.",
                "source_method": "rule_invalid_detector",
            })

        return records