import numpy as np
import pandas as pd

from app.config import PipelineConfig


class MixedTypeNearestNeighbors:
    """
    KNN for mixed e-commerce data.

    Numeric columns use normalized distance. Categorical columns use exact
    match/mismatch after trimming and case normalization.
    """

    def __init__(self, config: PipelineConfig):
        self.config = config
        self.reference_df: pd.DataFrame | None = None
        self.numeric_cols: list[str] = []
        self.categorical_cols: list[str] = []
        self.numeric_ranges: dict[str, float] = {}

    def fit(self, reference_df: pd.DataFrame):
        max_rows = self.config.max_reference_rows
        if max_rows and len(reference_df) > max_rows:
            reference_df = reference_df.sample(
                n=max_rows,
                random_state=self.config.random_state,
            )

        self.reference_df = reference_df.reset_index(drop=True).copy()

        context_cols = [
            col
            for col, rule in self.config.rules.items()
            if rule.use_for_recommendation
            and col != self.config.id_column
            and col in self.reference_df.columns
        ]

        self.numeric_cols = [
            col for col in context_cols
            if self.config.rules[col].dtype == "numeric"
        ]
        self.categorical_cols = [
            col for col in context_cols
            if self.config.rules[col].dtype == "categorical"
        ]

        self.numeric_ranges = {}
        for col in self.numeric_cols:
            values = pd.to_numeric(self.reference_df[col], errors="coerce")
            value_range = values.max() - values.min()
            self.numeric_ranges[col] = (
                float(value_range) if pd.notna(value_range) else 0.0
            )

        return self

    def kneighbors(self, row_df: pd.DataFrame, exclude_columns=None) -> pd.DataFrame:
        if self.reference_df is None:
            raise ValueError("MixedTypeNearestNeighbors must be fitted first.")

        exclude = set(exclude_columns or [])
        row = row_df.iloc[0]
        distances = np.zeros(len(self.reference_df), dtype=float)
        weights = 0

        for col in self.numeric_cols:
            if col in exclude:
                continue

            row_value = pd.to_numeric(pd.Series([row.get(col)]), errors="coerce").iloc[0]
            if pd.isna(row_value):
                continue

            ref_values = pd.to_numeric(self.reference_df[col], errors="coerce")
            value_range = self.numeric_ranges.get(col, 0.0)
            if value_range == 0:
                col_distance = (ref_values != row_value).astype(float)
            else:
                col_distance = (ref_values - row_value).abs() / value_range

            distances += col_distance.fillna(1.0).to_numpy(dtype=float)
            weights += 1

        for col in self.categorical_cols:
            if col in exclude:
                continue

            row_value = row.get(col)
            if pd.isna(row_value) or str(row_value).strip() == "":
                continue

            normalized_row = str(row_value).strip().casefold()
            normalized_ref = (
                self.reference_df[col].astype("string").str.strip().str.casefold()
            )
            col_distance = normalized_ref.ne(normalized_row).fillna(True).astype(float)

            distances += col_distance.to_numpy(dtype=float)
            weights += 1

        if weights > 0:
            distances = distances / weights

        n_neighbors = min(self.config.knn_neighbors, len(self.reference_df))
        neighbor_indices = np.argsort(distances, kind="mergesort")[:n_neighbors]
        return self.reference_df.iloc[neighbor_indices]
