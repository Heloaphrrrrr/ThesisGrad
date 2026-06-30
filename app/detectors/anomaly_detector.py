import pandas as pd
from sklearn.ensemble import IsolationForest

from app.config import PipelineConfig
from app.preprocessing.feature_builder import FeatureBuilder


class AnomalyDetector:
    """
    Isolation Forest for row-level anomaly detection.

    A global model is always trained. If anomaly_segment_column is configured,
    additional segment-level models are trained for large enough groups.
    """

    def __init__(self, config: PipelineConfig):
        self.config = config
        self.model: IsolationForest | None = None
        self.feature_builder: FeatureBuilder | None = None
        self.segment_models: dict[object, tuple[FeatureBuilder, IsolationForest]] = {}
        self._fitted = False

    def _build_model(self, n_rows: int) -> IsolationForest:
        return IsolationForest(
            n_estimators=self.config.n_estimators,
            contamination=self.config.contamination,
            max_samples=min(self.config.max_samples, n_rows),
            random_state=self.config.random_state,
        )

    def _fit_one_model(self, df: pd.DataFrame) -> tuple[FeatureBuilder, IsolationForest]:
        feature_builder = FeatureBuilder(self.config)
        feature_builder.fit(df)
        X = feature_builder.transform(df)

        model = self._build_model(len(df))
        model.fit(X)

        return feature_builder, model

    def fit(self, df: pd.DataFrame):
        self.feature_builder, self.model = self._fit_one_model(df)
        self.segment_models = {}

        segment_col = self.config.anomaly_segment_column
        if segment_col and segment_col in df.columns:
            segment_df = df.dropna(subset=[segment_col])

            for segment_value, group_df in segment_df.groupby(segment_col):
                if len(group_df) < self.config.min_anomaly_segment_size:
                    continue

                self.segment_models[segment_value] = self._fit_one_model(group_df)

        self._fitted = True

        return self

    def predict_scores(self, df: pd.DataFrame) -> pd.DataFrame:
        if not self._fitted:
            raise ValueError("AnomalyDetector must be fitted before predict_scores().")

        result = df[[self.config.id_column]].copy()
        result["raw_score"] = pd.NA
        result["decision_score"] = pd.NA
        result["is_anomaly"] = 0
        result["anomaly_model_segment"] = "global"

        pending_index = df.index

        segment_col = self.config.anomaly_segment_column
        if segment_col and segment_col in df.columns and self.segment_models:
            processed = []

            for segment_value, row_index in df.groupby(segment_col).groups.items():
                segment_model = self.segment_models.get(segment_value)
                if segment_model is None:
                    continue

                feature_builder, model = segment_model
                row_df = df.loc[row_index]
                X = feature_builder.transform(row_df)

                result.loc[row_index, "raw_score"] = model.score_samples(X)
                result.loc[row_index, "decision_score"] = model.decision_function(X)
                result.loc[row_index, "is_anomaly"] = (model.predict(X) == -1).astype(int)
                result.loc[row_index, "anomaly_model_segment"] = str(segment_value)
                processed.extend(row_index)

            pending_index = df.index.difference(pd.Index(processed))

        if len(pending_index) > 0:
            if self.feature_builder is None or self.model is None:
                raise ValueError("Global anomaly model is not fitted.")

            pending_df = df.loc[pending_index]
            X = self.feature_builder.transform(pending_df)

            result.loc[pending_index, "raw_score"] = self.model.score_samples(X)
            result.loc[pending_index, "decision_score"] = self.model.decision_function(X)
            result.loc[pending_index, "is_anomaly"] = (
                self.model.predict(X) == -1
            ).astype(int)

        return result
