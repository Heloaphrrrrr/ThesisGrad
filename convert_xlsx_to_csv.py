import pandas as pd
from pathlib import Path

input_path = Path("data/bankdataset.xlsx")
output_path = Path("data/bank_clean.csv")

df = pd.read_excel(input_path)

print("Original columns:")
print(df.columns.tolist())

df.to_csv(output_path, index=False)

print(f"Saved to: {output_path}")
print(df.head())