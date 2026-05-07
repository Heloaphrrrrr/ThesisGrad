import pandas as pd


class ReportService:

    @staticmethod
    def build_summary(issues_df: pd.DataFrame) -> pd.DataFrame:
        if issues_df.empty:
            return pd.DataFrame({
                "metric": ["total_issues"],
                "value": [0]
            })

        summary = issues_df["issue_type"].value_counts().reset_index()
        summary.columns = ["issue_type", "count"]

        total = pd.DataFrame({
            "issue_type": ["total"],
            "count": [len(issues_df)]
        })

        return pd.concat([summary, total], ignore_index=True)

    @staticmethod
    def build_recommendations(issues_df: pd.DataFrame) -> pd.DataFrame:
        if issues_df.empty:
            return pd.DataFrame()

        return issues_df[[
            "row_id",
            "column_name",
            "issue_type",
            "current_value",
            "suggested_value"
        ]].copy()