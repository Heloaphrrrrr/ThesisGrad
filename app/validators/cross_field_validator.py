import pandas as pd

from app.config import PipelineConfig
from app.schemas import IssueRecord, make_issue_id


class CrossFieldValidator:
    def __init__(self, config: PipelineConfig):
        self.config = config

    def detect(self, df: pd.DataFrame) -> pd.DataFrame:
        records = []

        required_cols = {"value", "transaction_count"}
        if not required_cols.issubset(set(df.columns)):
            return pd.DataFrame(records, columns=self.config.issue_output_columns)

        value = pd.to_numeric(df["value"], errors="coerce")
        count = pd.to_numeric(df["transaction_count"], errors="coerce")

        mask = (count == 0) & (value > 0)

        for idx in df.index[mask.fillna(False)]:
            issue = IssueRecord(
                issue_id=make_issue_id(),
                row_id=df.at[idx, self.config.id_column],
                column_name="transaction_count",
                issue_type="invalid",
                current_value=df.at[idx, "transaction_count"],
                suggested_value=None,
                confidence=1.0,
                severity="high",
                severity_score=0.8,
                reason="transaction_count is 0 while value is greater than 0.",
                source_method="cross_field_rule",
                can_auto_fix=True,
            )
            records.append(issue.to_dict())

        return pd.DataFrame(records, columns=self.config.issue_output_columns)