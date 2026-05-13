import pandas as pd


class ReportService:
    @staticmethod
    def build_summary(issues_df: pd.DataFrame) -> pd.DataFrame:
        if issues_df.empty:
            return pd.DataFrame({
                "metric": ["total_issues"],
                "value": [0],
            })

        rows = []

        rows.append({"metric": "total_issues", "value": len(issues_df)})

        for issue_type, count in issues_df["issue_type"].value_counts().items():
            rows.append({"metric": f"issue_type_{issue_type}", "value": count})

        if "severity" in issues_df.columns:
            for severity, count in issues_df["severity"].value_counts().items():
                rows.append({"metric": f"severity_{severity}", "value": count})

        if "confidence" in issues_df.columns:
            rows.append({
                "metric": "average_confidence",
                "value": round(float(issues_df["confidence"].mean()), 4),
            })

        fixable_rate = issues_df["can_auto_fix"].mean() if "can_auto_fix" in issues_df else 0

        rows.append({
            "metric": "fixable_rate",
            "value": round(float(fixable_rate), 4),
        })

        return pd.DataFrame(rows)

    @staticmethod
    def build_recommendations(issues_df: pd.DataFrame) -> pd.DataFrame:
        if issues_df.empty:
            return pd.DataFrame()

        return issues_df[[
            "issue_id",
            "row_id",
            "column_name",
            "issue_type",
            "current_value",
            "suggested_value",
            "confidence",
            "severity",
            "reason",
            "can_auto_fix",
        ]].copy()

    @staticmethod
    def build_dataset_profile(df: pd.DataFrame, issues_df: pd.DataFrame) -> pd.DataFrame:
        rows = []

        row_count = len(df)

        for col in df.columns:
            missing_count = int(df[col].isna().sum())
            missing_rate = missing_count / row_count if row_count > 0 else 0

            row = {
                "column_name": col,
                "missing_count": missing_count,
                "missing_rate": round(missing_rate, 4),
                "unique_count": int(df[col].nunique(dropna=True)),
                "min": None,
                "max": None,
                "issue_count": 0,
                "anomaly_count": 0,
                "invalid_count": 0,
            }

            if pd.api.types.is_numeric_dtype(df[col]):
                row["min"] = df[col].min()
                row["max"] = df[col].max()

            if not issues_df.empty and "column_name" in issues_df.columns:
                col_issues = issues_df[issues_df["column_name"] == col]
                row["issue_count"] = len(col_issues)
                row["anomaly_count"] = len(
                    col_issues[col_issues["issue_type"] == "anomaly"]
                )
                row["invalid_count"] = len(
                    col_issues[col_issues["issue_type"] == "invalid"]
                )

            rows.append(row)

        return pd.DataFrame(rows)