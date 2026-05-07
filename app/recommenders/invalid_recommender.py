import pandas as pd

from app.config import PipelineConfig
from .base_recommender import BaseRecommender


class InvalidRecommender(BaseRecommender):
    def __init__(self, config: PipelineConfig):
        self.config = config

    def recommend(self, value, column_name: str):
        rule = self.config.rules[column_name]

        if rule.dtype == "numeric":
            if pd.notna(value):
                if rule.min_value is not None and float(value) < rule.min_value:
                    return rule.min_value

                if rule.max_value is not None and float(value) > rule.max_value:
                    return rule.max_value

        if rule.dtype == "categorical" and rule.allowed_values:
            # fallback: chọn giá trị hợp lệ đầu tiên
            return rule.allowed_values[0]

        return None