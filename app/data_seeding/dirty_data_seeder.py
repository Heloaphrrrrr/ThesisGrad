from __future__ import annotations

import numpy as np
import pandas as pd

from app.data_seeding.seed_rules import (
    MISSING_COLUMNS,
    INVALID_RULES,
    ANOMALY_MULTIPLIERS,
)


class DirtyDataSeeder:
    def __init__(self, random_state: int = 42):
        self.rng = np.random.default_rng(random_state)

    def seed(
        self,
        clean_df: pd.DataFrame,
        dirty_rate: float = 0.2,
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        dirty_df = clean_df.copy()
        labels = []

        n_rows = len(dirty_df)
        n_dirty = int(n_rows * dirty_rate)

        dirty_indices = self.rng.choice(
            dirty_df.index,
            size=n_dirty,
            replace=False,
        )

        parts = np.array_split(dirty_indices, 3)

        self._inject_missing(dirty_df, parts[0], labels)
        self._inject_invalid(dirty_df, parts[1], labels)
        self._inject_anomaly(dirty_df, parts[2], labels)

        labels_df = pd.DataFrame(labels)

        return dirty_df, labels_df

    def _inject_missing(self, df, indices, labels):
        for idx in indices:
            col = self.rng.choice(MISSING_COLUMNS)

            if col not in df.columns:
                continue

            original = df.at[idx, col]
            df.at[idx, col] = pd.NA

            labels.append({
                "row_id": df.at[idx, "transaction_id"],
                "column_name": col,
                "issue_type": "missing",
                "original_value": original,
                "dirty_value": None,
            })

    def _inject_invalid(self, df, indices, labels):
        invalid_cols = list(INVALID_RULES.keys())

        for idx in indices:
            col = self.rng.choice(invalid_cols)

            if col not in df.columns:
                continue

            original = df.at[idx, col]
            dirty_value = INVALID_RULES[col]
            df.at[idx, col] = dirty_value

            labels.append({
                "row_id": df.at[idx, "transaction_id"],
                "column_name": col,
                "issue_type": "invalid",
                "original_value": original,
                "dirty_value": dirty_value,
            })

    def _inject_anomaly(self, df, indices, labels):
        anomaly_cols = list(ANOMALY_MULTIPLIERS.keys())

        for idx in indices:
            col = self.rng.choice(anomaly_cols)

            if col not in df.columns:
                continue

            original = df.at[idx, col]

            try:
                dirty_value = float(original) * ANOMALY_MULTIPLIERS[col]
            except Exception:
                continue

            df.at[idx, col] = dirty_value

            labels.append({
                "row_id": df.at[idx, "transaction_id"],
                "column_name": col,
                "issue_type": "anomaly",
                "original_value": original,
                "dirty_value": dirty_value,
            })