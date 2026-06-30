import pandas as pd

from app.config import PipelineConfig
from app.utils import clamp_confidence
from .base_recommender import BaseRecommender
from .mixed_type_neighbors import MixedTypeNearestNeighbors


class MissingRecommender(BaseRecommender):
    def __init__(self, config: PipelineConfig):
        self.config = config
        self.nn = MixedTypeNearestNeighbors(config)
        self.reference_df: pd.DataFrame | None = None

    def fit(self, reference_df: pd.DataFrame):
        self.reference_df = reference_df.copy()
        self.nn.fit(reference_df)
        return self

    def recommend(self, row_df: pd.DataFrame, column_name: str) -> tuple:
        if self.reference_df is None:
            raise ValueError("MissingRecommender must be fitted first.")

        neighbors = self.nn.kneighbors(row_df, exclude_columns=[column_name])

        rule = self.config.rules[column_name]

        if rule.dtype == "numeric":
            vals = pd.to_numeric(neighbors[column_name], errors="coerce").dropna()
            if len(vals) == 0:
                return None, 0.0

            suggested = round(float(vals.median()), 2)

            mean_val = abs(vals.mean())
            std_val = vals.std(ddof=0)

            if mean_val == 0:
                confidence = 0.5
            else:
                cv = std_val / mean_val
                confidence = 1 / (1 + cv)

            return suggested, clamp_confidence(confidence)

        if rule.dtype == "categorical":
            vals = neighbors[column_name].dropna()
            if vals.empty:
                return None, 0.0

            mode_val = vals.mode(dropna=True)
            if mode_val.empty:
                return None, 0.0

            suggested = mode_val.iloc[0]
            confidence = (vals == suggested).sum() / len(vals)

            return suggested, clamp_confidence(confidence)

        return None, 0.0
