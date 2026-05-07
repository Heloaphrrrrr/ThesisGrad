from abc import ABC, abstractmethod
import pandas as pd


class BaseDataSource(ABC):
    """
    Abstract class cho mọi nguồn dữ liệu (CSV, PostgreSQL, ...)
    """

    @abstractmethod
    def read(self) -> pd.DataFrame:
        pass

    @abstractmethod
    def write(self, df: pd.DataFrame, target_name: str) -> None:
        pass