from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from app.utils import parse_ecommerce_invoice_date


COLUMN_MAP = {
    "INVOICE_NO": "invoice_no",
    "CUSTOM_ID": "customer_id",
    "GENDER": "gender",
    "AGE": "age",
    "CATEGORY": "category",
    "QUANTITY": "quantity",
    "PRICE": "price",
    "PAYMENT_METHOD": "payment_method",
    "INVOICE_DATE": "invoice_date",
    "SHOPPING_MALL": "shopping_mall",
}


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    renamed = df.rename(columns=COLUMN_MAP).copy()
    renamed.columns = [col.strip().lower() for col in renamed.columns]
    return renamed


def build_age_group(age: int) -> str:
    if age <= 25:
        return "18_25"
    if age <= 35:
        return "26_35"
    if age <= 45:
        return "36_45"
    if age <= 55:
        return "46_55"
    return "56_plus"


def build_customer_segment(age: int) -> str:
    if age <= 25:
        return "young_adult"
    if age <= 45:
        return "adult"
    return "senior"


def build_quantity_band(quantity: int) -> str:
    if quantity <= 1:
        return "single"
    if quantity <= 3:
        return "small"
    return "bulk"


def build_price_band(base_unit_price: float) -> str:
    if base_unit_price < 100:
        return "low"
    if base_unit_price < 500:
        return "medium"
    return "high"


def transform_dataset(input_path: Path) -> dict[str, pd.DataFrame]:
    df = pd.read_excel(input_path)
    df = normalize_columns(df)

    df["invoice_date_raw"] = df["invoice_date"]
    df["invoice_date"] = parse_ecommerce_invoice_date(df["invoice_date_raw"])
    invalid_date_count = int(df["invoice_date"].isna().sum())
    if invalid_date_count > 0:
        sample_bad_dates = df.loc[
            df["invoice_date"].isna(),
            ["invoice_no", "invoice_date_raw"],
        ].head(10)
        raise ValueError(
            f"Found {invalid_date_count} invalid invoice_date values after parsing. "
            f"Sample:\n{sample_bad_dates}"
        )

    df["age"] = pd.to_numeric(df["age"], errors="coerce").astype("Int64")
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce").astype("Int64")
    df["price"] = pd.to_numeric(df["price"], errors="coerce")

    df["unit_price"] = (df["price"] / df["quantity"]).round(2)
    df["invoice_year"] = df["invoice_date"].dt.year
    df["invoice_month"] = df["invoice_date"].dt.month
    df["invoice_day"] = df["invoice_date"].dt.day
    df["day_of_week"] = df["invoice_date"].dt.dayofweek
    df["is_weekend"] = df["day_of_week"].isin([5, 6])
    df["age_group"] = df["age"].apply(lambda x: build_age_group(int(x)) if pd.notna(x) else None)
    df["customer_segment"] = df["age"].apply(
        lambda x: build_customer_segment(int(x)) if pd.notna(x) else None
    )
    df["quantity_band"] = df["quantity"].apply(
        lambda x: build_quantity_band(int(x)) if pd.notna(x) else None
    )

    category_stats = (
        df.groupby("category", dropna=False)["unit_price"]
        .median()
        .round(2)
        .reset_index(name="base_unit_price")
    )
    category_stats["price_band"] = category_stats["base_unit_price"].apply(
        lambda x: build_price_band(float(x)) if pd.notna(x) else None
    )

    mall_counts = (
        df.groupby("shopping_mall", dropna=False)
        .size()
        .reset_index(name="transaction_count")
    )
    max_count = mall_counts["transaction_count"].max()
    mall_counts["mall_popularity_score"] = (
        mall_counts["transaction_count"] / max_count
    ).round(4)
    mall_counts["mall_tier"] = pd.cut(
        mall_counts["mall_popularity_score"],
        bins=[-0.001, 0.33, 0.66, 1.0],
        labels=["small", "medium", "large"],
    ).astype(str)

    products = category_stats.copy()
    products.insert(0, "product_id", range(1, len(products) + 1))

    malls = mall_counts[["shopping_mall", "mall_tier", "mall_popularity_score"]].copy()
    malls.insert(0, "mall_id", range(1, len(malls) + 1))

    customers = (
        df[["customer_id", "gender", "age", "age_group", "customer_segment"]]
        .drop_duplicates(subset=["customer_id"])
        .reset_index(drop=True)
    )

    transactions = (
        df.merge(products[["product_id", "category", "base_unit_price"]], on="category", how="left")
          .merge(malls[["mall_id", "shopping_mall"]], on="shopping_mall", how="left")
          .copy()
    )
    transactions["price_deviation_from_category"] = (
        transactions["unit_price"] - transactions["base_unit_price"]
    ).round(2)

    transactions = transactions[
        [
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
    ].copy()

    return {
        "customers": customers,
        "products": products[["product_id", "category", "base_unit_price", "price_band"]],
        "shopping_malls": malls,
        "transactions": transactions,
    }


def export_csv_tables(tables: dict[str, pd.DataFrame], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for table_name, df in tables.items():
        df.to_csv(output_dir / f"{table_name}.csv", index=False)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        default="data/customer_shopping_data.xlsx",
        help="Path to the source Excel dataset.",
    )
    parser.add_argument(
        "--output-dir",
        default="outputs/ecommerce_import",
        help="Directory to write normalized CSV files.",
    )
    args = parser.parse_args()

    tables = transform_dataset(Path(args.input))
    export_csv_tables(tables, Path(args.output_dir))


if __name__ == "__main__":
    main()
