import pandas as pd

from app.config import PipelineConfig


class FixService:
    def __init__(self, config: PipelineConfig):
        self.config = config

    def apply_fixes(
        self,
        df: pd.DataFrame,
        issues_df: pd.DataFrame,
        mode: str = "conservative",
    ) -> pd.DataFrame:
        fixed_df = df.copy()

        if issues_df.empty:
            return fixed_df

        for _, issue in issues_df.iterrows():
            if not issue.get("can_auto_fix", False):
                continue

            suggested_value = issue.get("suggested_value")

            if pd.isna(suggested_value):
                continue

            confidence = float(issue.get("confidence", 0.0))

            if mode == "conservative":
                if confidence < self.config.conservative_confidence_threshold:
                    continue

            elif mode == "interactive":
                print(
                    f"Fix row={issue['row_id']} col={issue['column_name']} "
                    f"{issue['current_value']} -> {suggested_value} "
                    f"(confidence={confidence})"
                )
                answer = input("Apply fix? [y/N]: ").strip().lower()

                if answer != "y":
                    continue

            elif mode == "auto":
                pass

            else:
                raise ValueError(f"Unknown mode: {mode}")

            mask = fixed_df[self.config.id_column] == issue["row_id"]
            fixed_df.loc[mask, issue["column_name"]] = suggested_value

        return fixed_df