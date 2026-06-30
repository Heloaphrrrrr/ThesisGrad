from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

from scripts.import_ecommerce_data import normalize_columns, transform_dataset


def main() -> None:
    input_path = Path("data/customer_shopping_data.xlsx")
    raw_df = pd.read_excel(input_path)
    tables = transform_dataset(input_path)

    uri = "postgresql://postgres:Triweio_123@localhost:5432/doantn"
    engine = create_engine(uri)

    staging_raw = normalize_columns(raw_df).copy()
    staging_raw = staging_raw[
        [
            "invoice_no",
            "customer_id",
            "gender",
            "age",
            "category",
            "quantity",
            "price",
            "payment_method",
            "invoice_date",
            "shopping_mall",
        ]
    ]
    staging_raw = staging_raw.astype(object).where(pd.notna(staging_raw), None)
    staging_raw["source_file"] = str(input_path)

    with engine.begin() as conn:
        conn.execute(text("DELETE FROM staging_customer_shopping_raw"))
        conn.execute(text("DELETE FROM transactions"))
        conn.execute(text("DELETE FROM customers"))
        conn.execute(text("DELETE FROM products"))
        conn.execute(text("DELETE FROM shopping_malls"))

        staging_raw.to_sql(
            "staging_customer_shopping_raw",
            conn,
            if_exists="append",
            index=False,
        )
        tables["customers"].to_sql("customers", conn, if_exists="append", index=False)
        tables["products"].to_sql("products", conn, if_exists="append", index=False)
        tables["shopping_malls"].to_sql(
            "shopping_malls",
            conn,
            if_exists="append",
            index=False,
        )
        tables["transactions"].to_sql(
            "transactions",
            conn,
            if_exists="append",
            index=False,
        )

        conn.execute(
            text(
                "SELECT setval(pg_get_serial_sequence('products','product_id'), "
                "COALESCE((SELECT MAX(product_id) FROM products), 1), true)"
            )
        )
        conn.execute(
            text(
                "SELECT setval(pg_get_serial_sequence('shopping_malls','mall_id'), "
                "COALESCE((SELECT MAX(mall_id) FROM shopping_malls), 1), true)"
            )
        )

    print("import_ok")
    print({name: len(df) for name, df in tables.items()})


if __name__ == "__main__":
    main()
