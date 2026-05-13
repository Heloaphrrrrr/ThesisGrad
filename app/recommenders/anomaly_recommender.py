import pandas as pd
from sklearn.neighbors import NearestNeighbors

from app.config import PipelineConfig
from app.preprocessing.feature_builder import FeatureBuilder
from app.utils import clamp_confidence
from .base_recommender import BaseRecommender


class AnomalyRecommender(BaseRecommender):
    def __init__(self, config: PipelineConfig):
        self.config = config
        self.feature_builder = FeatureBuilder(config)
        self.nn = NearestNeighbors(n_neighbors=config.knn_neighbors, metric="euclidean")
        self.reference_df: pd.DataFrame | None = None

    def fit(self, reference_df: pd.DataFrame):
        self.reference_df = reference_df.copy()
        self.feature_builder.fit(reference_df)
        X_ref = self.feature_builder.transform(reference_df)
        self.nn.fit(X_ref)
        return self

    def recommend(self, row_df: pd.DataFrame, column_name: str) -> tuple:
        if self.reference_df is None:
            raise ValueError("AnomalyRecommender must be fitted first.")

        X_row = self.feature_builder.transform(row_df)
        _, indices = self.nn.kneighbors(X_row)
        neighbors = self.reference_df.iloc[indices[0]]

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