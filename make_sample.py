import pandas as pd
from pathlib import Path

input_path = Path("data/bank_clean.csv")
output_path = Path("data/bank_clean_sample.csv")

sample_size = 10000

df = pd.read_csv(input_path)

sample_df = df.sample(
    n=min(sample_size, len(df)),
    random_state=42
).reset_index(drop=True)

sample_df.to_csv(output_path, index=False)

print("=== SAMPLE CREATED ===")
print(f"Input: {input_path}")
print(f"Output: {output_path}")
print(f"Sample shape: {sample_df.shape}")
print(sample_df.head())