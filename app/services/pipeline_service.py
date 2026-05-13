import pandas as pd

from app.config import PipelineConfig
from app.schemas import IssueRecord, make_issue_id
from app.validators.missing_detector import MissingDetector
from app.validators.invalid_detector import InvalidDetector
from app.validators.cross_field_validator import CrossFieldValidator
from app.detectors.anomaly_detector import AnomalyDetector
from app.detectors.feature_contribution import FeatureContributionAnalyzer
from app.recommenders.missing_recommender import MissingRecommender
from app.recommenders.invalid_recommender import InvalidRecommender
from app.recommenders.anomaly_recommender import AnomalyRecommender
from app.utils import severity_from_score, clamp_confidence


class DataCleaningPipelineService:
    def __init__(self, config: PipelineConfig):
        self.config = config

        self.missing_detector = MissingDetector(config)
        self.invalid_detector = InvalidDetector(config)
        self.cross_field_validator = CrossFieldValidator(config)

        self.anomaly_detector = AnomalyDetector(config)
        self.feature_analyzer = FeatureContributionAnalyzer(config)

        self.missing_recommender = MissingRecommender(config)
        self.invalid_recommender = InvalidRecommender(config)
        self.anomaly_recommender = AnomalyRecommender(config)

    def run(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()

        missing_df = self.missing_detector.detect(df)
        invalid_df = self.invalid_detector.detect(df)
        cross_field_df = self.cross_field_validator.detect(df)

        known_issue_dfs = [missing_df, invalid_df, cross_field_df]
        known_issues_df = pd.concat(known_issue_dfs, ignore_index=True)

        issue_row_ids = set()
        if not known_issues_df.empty:
            issue_row_ids.update(known_issues_df["row_id"].tolist())

        clean_df = df[~df[self.config.id_column].isin(issue_row_ids)].copy()
        if clean_df.empty:
            clean_df = df.copy()

        self.anomaly_detector.fit(clean_df)
        score_df = self.anomaly_detector.predict_scores(df)

        anomaly_rows = score_df[
            score_df["is_anomaly"] == 1
        ][self.config.id_column].tolist()

        self.feature_analyzer.fit(clean_df)

        candidate_cols = [
            col for col, rule in self.config.rules.items()
            if rule.use_for_detection and col != self.config.id_column
        ]

        anomaly_records = []

        for row_id in anomaly_rows:
            row_df = df[df[self.config.id_column] == row_id].copy()

            if row_df.empty:
                continue

            suspicious_cols = self.feature_analyzer.find_suspicious_columns(
                row_df,
                candidate_cols,
            )

            score_row = score_df[score_df[self.config.id_column] == row_id].iloc[0]
            decision_score = float(score_row["decision_score"])
            raw_score = float(score_row["raw_score"])

            anomaly_confidence = clamp_confidence(abs(decision_score) * 5)

            for col in suspicious_cols:
                current_value = row_df.iloc[0][col]

                issue = IssueRecord(
                    issue_id=make_issue_id(),
                    row_id=row_id,
                    column_name=col,
                    issue_type="anomaly",
                    current_value=current_value,
                    suggested_value=None,
                    confidence=anomaly_confidence,
                    severity="medium",
                    severity_score=0.5,
                    reason=f"Column '{col}' deviates from similar normal records.",
                    source_method="isolation_forest+feature_contribution",
                    can_auto_fix=True,
                )

                anomaly_records.append(issue.to_dict())

        anomaly_df = pd.DataFrame(
            anomaly_records,
            columns=self.config.issue_output_columns,
        )

        all_issues = pd.concat(
            [missing_df, invalid_df, cross_field_df, anomaly_df],
            ignore_index=True,
        )

        if all_issues.empty:
            return pd.DataFrame(columns=self.config.issue_output_columns)

        self.missing_recommender.fit(clean_df)
        self.anomaly_recommender.fit(clean_df)

        for idx, issue in all_issues.iterrows():
            issue_type = issue["issue_type"]
            row_id = issue["row_id"]
            col = issue["column_name"]

            row_df = df[df[self.config.id_column] == row_id].copy()

            if row_df.empty:
                continue

            if issue_type == "missing":
                suggestion, confidence = self.missing_recommender.recommend(row_df, col)

                all_issues.at[idx, "suggested_value"] = suggestion
                all_issues.at[idx, "confidence"] = confidence

            elif issue_type == "invalid":
                value = issue["current_value"]

                if col in self.config.rules:
                    suggestion, confidence = self.invalid_recommender.recommend(value, col)
                else:
                    suggestion, confidence = None, 0.0

                all_issues.at[idx, "suggested_value"] = suggestion
                all_issues.at[idx, "confidence"] = confidence

            elif issue_type == "anomaly":
                suggestion, rec_confidence = self.anomaly_recommender.recommend(row_df, col)

                current_value = issue["current_value"]

                severity_score = self._calculate_anomaly_severity_score(
                    current_value=current_value,
                    suggested_value=suggestion,
                )

                all_issues.at[idx, "suggested_value"] = suggestion
                all_issues.at[idx, "confidence"] = min(
                    float(issue["confidence"]),
                    rec_confidence,
                )
                all_issues.at[idx, "severity_score"] = severity_score
                all_issues.at[idx, "severity"] = severity_from_score(severity_score)

        return all_issues[self.config.issue_output_columns]

    @staticmethod
    def _calculate_anomaly_severity_score(current_value, suggested_value) -> float:
        try:
            current = float(current_value)
            suggested = float(suggested_value)

            return abs(current - suggested) / (abs(suggested) + 1)

        except Exception:
            return 0.5