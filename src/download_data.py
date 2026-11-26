
from ucimlrepo import fetch_ucirepo
from pathlib import Path
import pandas as pd

print("Downloading German Credit dataset...")

dataset = fetch_ucirepo(id=144)

features = dataset.data.features.copy()
targets = dataset.data.targets.copy()

df = pd.concat([features, targets], axis=1)

output = Path("data/raw/german_credit.csv")
output.parent.mkdir(parents=True, exist_ok=True)

df.to_csv(output, index=False)

print("\nDownload successful!")
print("Dataset shape:", df.shape)

print("\nColumn names:")
print(df.columns.tolist())

print("\nFirst five records:")
print(df.head())

print("\nCredit risk distribution:")
print(targets.value_counts())
