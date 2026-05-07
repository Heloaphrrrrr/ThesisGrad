import pandas as pd
from sqlalchemy import create_engine

from .base_source import BaseDataSource


class PostgresDataSource(BaseDataSource):
    def __init__(self, connection_uri: str, table_name: str):
        self.connection_uri = connection_uri
        self.table_name = table_name
        self.engine = create_engine(connection_uri)

    def read(self) -> pd.DataFrame:
        query = f"SELECT * FROM {self.table_name}"
        return pd.read_sql(query, self.engine)

    def write(self, df: pd.DataFrame, target_name: str) -> None:
        df.to_sql(target_name, self.engine, if_exists="replace", index=False)