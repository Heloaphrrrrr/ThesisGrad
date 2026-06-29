import numpy as np
import pandas as pd
from sqlalchemy import create_engine, inspect, text

from .base_source import BaseDataSource


TARGET_TABLE_ALIASES = {
    "fixed_data": "fixed_transactions",
    "recommendations": "fix_recommendations",
}

SCHEMA_TABLES = {
    "detected_issues",
    "fix_recommendations",
    "cleaning_actions",
    "dataset_profile",
    "fixed_transactions",
}

DEPENDENT_CLEAR_ORDER = {
    "detected_issues": [
        "cleaning_actions",
        "fix_recommendations",
        "detected_issues",
    ],
    "fix_recommendations": [
        "fix_recommendations",
    ],
    "cleaning_actions": [
        "cleaning_actions",
    ],
    "dataset_profile": [
        "dataset_profile",
    ],
    "fixed_transactions": [
        "fixed_transactions",
    ],
}


class PostgresDataSource(BaseDataSource):
    def __init__(self, connection_uri: str, table_name: str, query: str | None = None):
        self.connection_uri = connection_uri
        self.table_name = table_name
        self.query = query
        self.engine = create_engine(connection_uri)

    def read(self) -> pd.DataFrame:
        query = self.query or f"SELECT * FROM {self.table_name}"
        return pd.read_sql(query, self.engine)

    def write(self, df: pd.DataFrame, target_name: str) -> None:
        resolved_target = TARGET_TABLE_ALIASES.get(target_name, target_name)
        prepared_df = self._prepare_dataframe_for_target(df, resolved_target)
        clean_df = self._sanitize_dataframe_for_sql(prepared_df)

        if resolved_target in SCHEMA_TABLES:
            if not self._table_exists(resolved_target):
                raise ValueError(
                    f"Target table '{resolved_target}' does not exist. "
                    "Please create schema before writing to PostgreSQL."
                )

            self._clear_table_before_write(resolved_target)

            if clean_df.empty:
                return

            clean_df.to_sql(
                resolved_target,
                self.engine,
                if_exists="append",
                index=False,
                method="multi",
            )
            return

        clean_df.to_sql(
            resolved_target,
            self.engine,
            if_exists="replace",
            index=False,
            method="multi",
        )

    def _prepare_dataframe_for_target(
        self,
        df: pd.DataFrame,
        target_name: str,
    ) -> pd.DataFrame:
        out = df.copy()

        if target_name == "detected_issues":
            out["table_name"] = self.table_name
            if "recommended_action" not in out.columns:
                out["recommended_action"] = out["can_auto_fix"].map(
                    lambda value: "auto_fix" if bool(value) else "review"
                )

            columns = [
                "issue_id",
                "row_id",
                "table_name",
                "column_name",
                "issue_type",
                "current_value",
                "suggested_value",
                "confidence",
                "severity",
                "severity_score",
                "reason",
                "source_method",
                "recommended_action",
                "can_auto_fix",
                "created_at",
            ]
            return out[columns]

        if target_name == "fix_recommendations":
            out["table_name"] = self.table_name
            if "approved" not in out.columns:
                out["approved"] = False
            if "applied_at" not in out.columns:
                out["applied_at"] = None

            columns = [
                "issue_id",
                "row_id",
                "table_name",
                "column_name",
                "suggested_value",
                "confidence",
                "approved",
                "applied_at",
            ]
            return out[columns]

        if target_name == "dataset_profile":
            out["table_name"] = self.table_name
            out = out.rename(
                columns={
                    "min": "min_value",
                    "max": "max_value",
                }
            )
            columns = [
                "table_name",
                "column_name",
                "missing_count",
                "missing_rate",
                "unique_count",
                "min_value",
                "max_value",
                "issue_count",
                "anomaly_count",
                "invalid_count",
            ]
            return out[columns]

        if target_name == "fixed_transactions":
            return self._build_fixed_transactions_dataframe(out)

        return out

    def _build_fixed_transactions_dataframe(self, fixed_df: pd.DataFrame) -> pd.DataFrame:
        base_transactions = pd.read_sql("SELECT * FROM transactions", self.engine)
        merged = base_transactions.merge(
            fixed_df,
            on="invoice_no",
            how="left",
            suffixes=("", "__fixed"),
        )

        updatable_columns = [
            "customer_id",
            "quantity",
            "price",
            "payment_method",
            "invoice_date",
            "unit_price",
            "invoice_year",
            "invoice_month",
            "invoice_day",
            "day_of_week",
            "is_weekend",
            "quantity_band",
            "price_deviation_from_category",
        ]

        for column in updatable_columns:
            fixed_column = f"{column}__fixed"
            if fixed_column in merged.columns:
                merged[column] = merged[fixed_column].combine_first(merged[column])

        columns = [
            "invoice_no",
            "customer_id",
            "product_id",
            "mall_id",
            "quantity",
            "price",
            "payment_method",
            "invoice_date",
            "unit_price",
            "invoice_year",
            "invoice_month",
            "invoice_day",
            "day_of_week",
            "is_weekend",
            "quantity_band",
            "price_deviation_from_category",
        ]
        return merged[columns]

    def _sanitize_dataframe_for_sql(self, df: pd.DataFrame) -> pd.DataFrame:
        out = df.copy().astype(object)
        out = out.where(pd.notna(out), None)

        def convert_value(value):
            if value is None:
                return None
            if isinstance(value, np.integer):
                return int(value)
            if isinstance(value, np.floating):
                return float(value)
            if isinstance(value, np.bool_):
                return bool(value)
            if isinstance(value, pd.Timestamp):
                return value.to_pydatetime()
            return value

        return out.map(convert_value)

    def _clear_table_before_write(self, target_name: str) -> None:
        clear_order = DEPENDENT_CLEAR_ORDER.get(target_name, [target_name])

        with self.engine.begin() as connection:
            for table_name in clear_order:
                if not self._table_exists(table_name):
                    continue
                connection.execute(text(f"DELETE FROM {table_name}"))

    def _table_exists(self, table_name: str) -> bool:
        return inspect(self.engine).has_table(table_name)
