import pandas as pd

from app.config import PipelineConfig
from app.schemas import IssueRecord, make_issue_id


class MissingDetector:
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
                issue = IssueRecord(
                    issue_id=make_issue_id(),
                    row_id=df.at[idx, self.config.id_column],
                    column_name=col,
                    issue_type="missing",
                    current_value=None,
                    suggested_value=None,
                    confidence=1.0,
                    severity=rule.severity_if_missing,
                    severity_score=0.7 if rule.severity_if_missing == "high" else 0.4,
                    reason=f"Required column '{col}' is missing.",
                    source_method="rule_missing_detector",
                    can_auto_fix=True,
                )
                records.append(issue.to_dict())

        return pd.DataFrame(records, columns=self.config.issue_output_columns)