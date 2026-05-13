import pandas as pd
from sklearn.ensemble import IsolationForest

from app.config import PipelineConfig
from app.preprocessing.feature_builder import FeatureBuilder


class AnomalyDetector:
    """
    Isolation Forest để detect anomaly theo row.
    """

    def __init__(self, config: PipelineConfig):
        self.config = config

        self.model = IsolationForest(
            n_estimators=config.n_estimators,
            contamination=config.contamination,
            max_samples=config.max_samples,
            random_state=config.random_state,
        )

        self.feature_builder = FeatureBuilder(config)
        self._fitted = False

    def fit(self, df: pd.DataFrame):
        self.feature_builder.fit(df)
        X = self.feature_builder.transform(df)

        self.model.fit(X)
        self._fitted = True

        return self

    def predict_scores(self, df: pd.DataFrame) -> pd.DataFrame:
        if not self._fitted:
            raise ValueError("AnomalyDetector must be fitted before predict_scores().")

        X = self.feature_builder.transform(df)

        raw_scores = self.model.score_samples(X)
        decision_scores = self.model.decision_function(X)
        labels = self.model.predict(X)

        result = df[[self.config.id_column]].copy()
        result["raw_score"] = raw_scores
        result["decision_score"] = decision_scores
        result["is_anomaly"] = (labels == -1).astype(int)

        return result