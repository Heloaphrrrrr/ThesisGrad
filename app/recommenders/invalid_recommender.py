import difflib
import pandas as pd

from app.config import PipelineConfig
from .base_recommender import BaseRecommender


class InvalidRecommender(BaseRecommender):
    def __init__(self, config: PipelineConfig):
        self.config = config

    def recommend(self, value, column_name: str) -> tuple:
        rule = self.config.rules[column_name]

        if rule.dtype == "numeric":
            if pd.notna(value):
                numeric_value = float(value)

                if rule.min_value is not None and numeric_value < rule.min_value:
                    return rule.min_value, 1.0

                if rule.max_value is not None and numeric_value > rule.max_value:
                    return rule.max_value, 1.0

        if rule.dtype == "categorical" and rule.allowed_values:
            if value is not None and pd.notna(value):
                matches = difflib.get_close_matches(
                    str(value),
                    rule.allowed_values,
                    n=1,
                    cutoff=0.6,
                )

                if matches:
                    similarity = difflib.SequenceMatcher(
                        None, str(value), matches[0]
                    ).ratio()
                    return matches[0], round(float(similarity), 4)

            return rule.allowed_values[0], 0.5

        return None, 0.0