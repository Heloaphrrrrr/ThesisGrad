import pandas as pd
from sklearn.neighbors import NearestNeighbors

from app.config import PipelineConfig
from app.preprocessing.feature_builder import FeatureBuilder


class FeatureContributionAnalyzer:
    """
    Xác định column nào gây anomaly.

    AnomalyDetector chỉ cho biết row nào bất thường.
    FeatureContributionAnalyzer giúp phân tích row đó để tìm column nghi ngờ.
    """

    def __init__(self, config: PipelineConfig):
        self.config = config
        self.feature_builder = FeatureBuilder(config)
        self.nn = NearestNeighbors(n_neighbors=config.knn_neighbors)

        self.reference_df: pd.DataFrame | None = None

    def fit(self, reference_df: pd.DataFrame):
        self.reference_df = reference_df.copy()

        self.feature_builder.fit(reference_df)
        X_ref = self.feature_builder.transform(reference_df)

        self.nn.fit(X_ref)

        return self

    def find_suspicious_columns(
        self,
        row_df: pd.DataFrame,
        candidate_columns: list[str],
    ) -> list[str]:

        if self.reference_df is None:
            raise ValueError("FeatureContributionAnalyzer must be fitted first.")

        X_row = self.feature_builder.transform(row_df)

        _, indices = self.nn.kneighbors(X_row)

        neighbor_rows = self.reference_df.iloc[indices[0]]

        suspicious_cols = []

        for col in candidate_columns:
            if col not in row_df.columns:
                continue

            value = row_df.iloc[0][col]
            rule = self.config.rules[col]

            if pd.isna(value):
                suspicious_cols.append(col)
                continue

            if rule.dtype == "numeric":
                neighbor_values = pd.to_numeric(
                    neighbor_rows[col],
                    errors="coerce"
                ).dropna()

                if len(neighbor_values) < 2:
                    continue

                mean_val = neighbor_values.mean()
                std_val = neighbor_values.std(ddof=0)

                try:
                    current_value = float(value)
                except Exception:
                    suspicious_cols.append(col)
                    continue

                if std_val == 0:
                    if abs(current_value - mean_val) > 0:
                        suspicious_cols.append(col)
                else:
                    z_score = abs((current_value - mean_val) / std_val)

                    if z_score >= self.config.feature_z_threshold:
                        suspicious_cols.append(col)

            elif rule.dtype == "categorical":
                mode_val = neighbor_rows[col].mode(dropna=True)

                if not mode_val.empty and value != mode_val.iloc[0]:
                    suspicious_cols.append(col)

        return suspicious_cols