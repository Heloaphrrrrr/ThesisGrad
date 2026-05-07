from __future__ import annotations

from typing import List

import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from app.config import PipelineConfig


class FeatureBuilder:
    def __init__(self, config: PipelineConfig):
        self.config = config
        self.numeric_cols: List[str] = []
        self.categorical_cols: List[str] = []
        self.preprocessor: ColumnTransformer | None = None

    def fit(self, df: pd.DataFrame) -> "FeatureBuilder":

        # =========================
        # 1. CHỌN CỘT CHO ML
        # =========================
        detect_cols = [
            col for col, rule in self.config.rules.items()
            if rule.use_for_detection and col != self.config.id_column
        ]

        # =========================
        # 2. PHÂN LOẠI FEATURE
        # =========================
        self.numeric_cols = [
            col for col in detect_cols
            if self.config.rules[col].dtype == "numeric"
        ]

        self.categorical_cols = [
            col for col in detect_cols
            if self.config.rules[col].dtype == "categorical"
        ]

        # =========================
        # 3. PIPELINE NUMERIC
        # =========================
        numeric_pipeline = Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler())
        ])

        # =========================
        # 4. PIPELINE CATEGORICAL
        # =========================
        categorical_pipeline = Pipeline([
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("encoder", OneHotEncoder(handle_unknown="ignore"))
        ])

        # =========================
        # 5. COMBINE
        # =========================
        self.preprocessor = ColumnTransformer(
            transformers=[
                ("num", numeric_pipeline, self.numeric_cols),
                ("cat", categorical_pipeline, self.categorical_cols),
            ],
            remainder="drop"
        )

        # =========================
        # 6. FIT
        # =========================
        self.preprocessor.fit(df)

        return self

    def transform(self, df: pd.DataFrame):

        if self.preprocessor is None:
            raise ValueError("FeatureBuilder must be fitted first")

        return self.preprocessor.transform(df)

    def fit_transform(self, df: pd.DataFrame):
        self.fit(df)
        return self.transform(df)