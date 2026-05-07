import pandas as pd
from sklearn.neighbors import NearestNeighbors

from app.config import PipelineConfig
from app.preprocessing.feature_builder import FeatureBuilder
from .base_recommender import BaseRecommender


class MissingRecommender(BaseRecommender):
    def __init__(self, config: PipelineConfig):
        self.config = config

        # Dùng lại FeatureBuilder để đảm bảo cùng không gian đặc trưng với anomaly
        self.feature_builder = FeatureBuilder(config)

        # KNN model
        self.nn = NearestNeighbors(
            n_neighbors=config.knn_neighbors,
            metric="euclidean"
        )

        self.reference_df: pd.DataFrame | None = None

    def fit(self, reference_df: pd.DataFrame):
        """
        reference_df = dữ liệu sạch (không lỗi)
        """
        self.reference_df = reference_df.copy()

        # Fit feature space
        self.feature_builder.fit(reference_df)
        X_ref = self.feature_builder.transform(reference_df)

        # Fit KNN
        self.nn.fit(X_ref)

        return self

    def recommend(self, row_df: pd.DataFrame, column_name: str):
        """
        row_df: 1 dòng cần sửa
        column_name: cột bị missing
        """

        if self.reference_df is None:
            raise ValueError("MissingRecommender must be fitted first.")

        # Transform dòng cần dự đoán
        X_row = self.feature_builder.transform(row_df)

        # Tìm K hàng xóm gần nhất
        distances, indices = self.nn.kneighbors(X_row)

        neighbors = self.reference_df.iloc[indices[0]]

        rule = self.config.rules[column_name]

        # =========================
        # NUMERIC
        # =========================
        if rule.dtype == "numeric":
            vals = pd.to_numeric(neighbors[column_name], errors="coerce").dropna()

            if len(vals) == 0:
                return None

            return round(float(vals.median()), 2)

        # =========================
        # CATEGORICAL
        # =========================
        elif rule.dtype == "categorical":
            mode_val = neighbors[column_name].mode(dropna=True)

            if mode_val.empty:
                return None

            return mode_val.iloc[0]

        return None