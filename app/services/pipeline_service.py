import pandas as pd

from app.config import PipelineConfig
from app.validators.missing_detector import MissingDetector
from app.validators.invalid_detector import InvalidDetector
from app.detectors.anomaly_detector import AnomalyDetector
from app.detectors.feature_contribution import FeatureContributionAnalyzer
from app.recommenders.missing_recommender import MissingRecommender
from app.recommenders.invalid_recommender import InvalidRecommender
from app.recommenders.anomaly_recommender import AnomalyRecommender


class DataCleaningPipelineService:

    def __init__(self, config: PipelineConfig):
        self.config = config

        # DETECTORS
        self.missing_detector = MissingDetector(config)
        self.invalid_detector = InvalidDetector(config)
        self.anomaly_detector = AnomalyDetector(config)

        # ANALYZER
        self.feature_analyzer = FeatureContributionAnalyzer(config)

        # RECOMMENDERS
        self.missing_recommender = MissingRecommender(config)
        self.invalid_recommender = InvalidRecommender(config)
        self.anomaly_recommender = AnomalyRecommender(config)

    def run(self, df: pd.DataFrame) -> pd.DataFrame:

        df = df.copy()

        # =====================================================
        # STEP 1: MISSING
        # =====================================================
        missing_df = self.missing_detector.detect(df)

        # =====================================================
        # STEP 2: INVALID
        # =====================================================
        invalid_df = self.invalid_detector.detect(df)

        # =====================================================
        # STEP 3: ANOMALY (Isolation Forest)
        # =====================================================

        error_ids = set()

        if not missing_df.empty:
            error_ids.update(missing_df["row_id"].tolist())

        if not invalid_df.empty:
            error_ids.update(invalid_df["row_id"].tolist())

        # loại dữ liệu lỗi obvious trước khi train
        clean_df = df[~df[self.config.id_column].isin(error_ids)].copy()

        if clean_df.empty:
            clean_df = df.copy()

        # train model
        self.anomaly_detector.fit(clean_df)

        score_df = self.anomaly_detector.predict_scores(df)

        anomaly_rows = score_df[
            score_df["is_anomaly"] == 1
        ][self.config.id_column].tolist()

        # =====================================================
        # STEP 4: FEATURE CONTRIBUTION
        # =====================================================
        self.feature_analyzer.fit(clean_df)

        candidate_cols = [
            col for col, rule in self.config.rules.items()
            if rule.use_for_detection and col != self.config.id_column
        ]

        anomaly_records = []

        for row_id in anomaly_rows:
            row_df = df[df[self.config.id_column] == row_id]

            suspicious_cols = self.feature_analyzer.find_suspicious_columns(
                row_df,
                candidate_cols
            )

            anomaly_score = float(
                score_df.loc[
                    score_df[self.config.id_column] == row_id,
                    "raw_score"
                ].iloc[0]
            )

            for col in suspicious_cols:
                anomaly_records.append({
                    "row_id": row_id,
                    "column_name": col,
                    "issue_type": "anomaly",
                    "current_value": row_df.iloc[0][col],
                    "anomaly_score": anomaly_score,
                    "suggested_value": None,
                    "reason": f"{col} lệch khỏi phân bố dữ liệu",
                    "source_method": "isolation_forest"
                })

        anomaly_df = pd.DataFrame(anomaly_records)

        # =====================================================
        # STEP 5: RECOMMEND
        # =====================================================

        self.missing_recommender.fit(clean_df)
        self.anomaly_recommender.fit(clean_df)

        all_issues = pd.concat(
            [missing_df, invalid_df, anomaly_df],
            ignore_index=True
        )

        # ---- missing ----
        for idx, row in all_issues[all_issues["issue_type"] == "missing"].iterrows():
            row_id = row["row_id"]
            col = row["column_name"]

            row_df = df[df[self.config.id_column] == row_id]

            suggestion = self.missing_recommender.recommend(row_df, col)

            all_issues.at[idx, "suggested_value"] = suggestion

        # ---- invalid ----
        for idx, row in all_issues[all_issues["issue_type"] == "invalid"].iterrows():
            col = row["column_name"]
            value = row["current_value"]

            suggestion = self.invalid_recommender.recommend(value, col)

            all_issues.at[idx, "suggested_value"] = suggestion

        # ---- anomaly ----
        for idx, row in all_issues[all_issues["issue_type"] == "anomaly"].iterrows():
            row_id = row["row_id"]
            col = row["column_name"]

            row_df = df[df[self.config.id_column] == row_id]

            suggestion = self.anomaly_recommender.recommend(row_df, col)

            all_issues.at[idx, "suggested_value"] = suggestion

        return all_issues