import pandas as pd

from app.config import PipelineConfig


class MissingDetector:
    """
    Detect missing data:
    - NaN / None
    - empty string nếu column required=True
    """

    def __init__(self, config: PipelineConfig):
        self.config = config

    def detect(self, df: pd.DataFrame) -> pd.DataFrame:
        records = []

        for col, rule in self.config.rules.items():
            if col not in df.columns:
                continue

            if not rule.required:
                continue

            series = df[col]

            missing_mask = series.isna()

            if series.dtype == "object":
                empty_mask = series.fillna("").astype(str).str.strip() == ""
                missing_mask = missing_mask | empty_mask

            for idx in df.index[missing_mask]:
                records.append({
                    "row_id": df.at[idx, self.config.id_column],
                    "column_name": col,
                    "issue_type": "missing",
                    "current_value": None,
                    "anomaly_score": None,
                    "suggested_value": None,
                    "reason": f"Required column '{col}' is missing.",
                    "source_method": "rule_missing_detector",
                })

        return pd.DataFrame(records, columns=self.config.issue_output_columns)