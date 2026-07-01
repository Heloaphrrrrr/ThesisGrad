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
        self.numeric_ref_values: dict[str, np.ndarray] = {}
        self.categorical_ref_values: dict[str, pd.Series] = {}
        self._neighbor_cache: dict[tuple[str, tuple[str, ...]], pd.DataFrame] = {}

    def fit(self, reference_df: pd.DataFrame):
        self.reference_df = reference_df.reset_index(drop=True).copy()
        self._neighbor_cache = {}

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
        self.numeric_ref_values = {}
        for col in self.numeric_cols:
            values = pd.to_numeric(self.reference_df[col], errors="coerce")
            value_range = values.max() - values.min()
            self.numeric_ranges[col] = (
                float(value_range) if pd.notna(value_range) else 0.0
            )
            self.numeric_ref_values[col] = values.to_numpy(dtype=float)

        self.categorical_ref_values = {
            col: self.reference_df[col].astype("string").str.strip().str.casefold()
            for col in self.categorical_cols
        }

        return self

    def kneighbors(self, row_df: pd.DataFrame, exclude_columns=None) -> pd.DataFrame:
        if self.reference_df is None:
            raise ValueError("MixedTypeNearestNeighbors must be fitted first.")

        exclude = set(exclude_columns or [])
        row = row_df.iloc[0]
        cache_key = self._cache_key(row, exclude)
        cached = self._neighbor_cache.get(cache_key)
        if cached is not None:
            return cached

        distances = np.zeros(len(self.reference_df), dtype=float)
        weights = 0

        for col in self.numeric_cols:
            if col in exclude:
                continue

            row_value = pd.to_numeric(pd.Series([row.get(col)]), errors="coerce").iloc[0]
            if pd.isna(row_value):
                continue

            ref_values = self.numeric_ref_values[col]
            value_range = self.numeric_ranges.get(col, 0.0)
            if value_range == 0:
                col_distance = (ref_values != row_value).astype(float)
            else:
                col_distance = np.abs(ref_values - row_value) / value_range

            distances += np.nan_to_num(col_distance, nan=1.0)
            weights += 1

        for col in self.categorical_cols:
            if col in exclude:
                continue

            row_value = row.get(col)
            if pd.isna(row_value) or str(row_value).strip() == "":
                continue

            normalized_row = str(row_value).strip().casefold()
            normalized_ref = self.categorical_ref_values[col]
            col_distance = normalized_ref.ne(normalized_row).fillna(True).astype(float)

            distances += col_distance.to_numpy(dtype=float)
            weights += 1

        if weights > 0:
            distances = distances / weights

        n_neighbors = min(self.config.knn_neighbors, len(self.reference_df))
        neighbor_indices = np.argsort(distances, kind="mergesort")[:n_neighbors]
        neighbors = self.reference_df.iloc[neighbor_indices]
        self._neighbor_cache[cache_key] = neighbors
        return neighbors

    def _cache_key(self, row: pd.Series, exclude: set[str]) -> tuple[str, tuple[str, ...]]:
        row_id = row.get(self.config.id_column)
        if pd.isna(row_id):
            row_id = tuple(row.astype("string").fillna("<NA>").tolist())

        return str(row_id), tuple(sorted(exclude))
