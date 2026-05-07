import os
import pandas as pd

from .base_source import BaseDataSource


class CSVDataSource(BaseDataSource):
    def __init__(self, input_path: str, output_dir: str = "outputs"):
        self.input_path = input_path
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def read(self) -> pd.DataFrame:
        df = pd.read_csv(self.input_path)
        return df.copy()

    def write(self, df: pd.DataFrame, target_name: str) -> None:
        output_path = os.path.join(self.output_dir, f"{target_name}.csv")
        df.to_csv(output_path, index=False)