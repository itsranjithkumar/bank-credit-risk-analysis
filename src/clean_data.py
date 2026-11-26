
from pathlib import Path
import pandas as pd
import json

# Project paths
RAW_FILE = Path("data/raw/german_credit.csv")
CLEAN_FILE = Path("data/processed/cleaned_credit_data.csv")
REPORT_FILE = Path("reports/data_quality_report.json")

print("Starting data cleaning...")

# Load original dataset
df = pd.read_csv(RAW_FILE)

original_rows = len(df)

# Rename generic UCI attributes to meaningful business names
column_mapping = {
    "Attribute1": "checking_account",
    "Attribute2": "loan_duration_months",
    "Attribute3": "credit_history",
    "Attribute4": "loan_purpose",
    "Attribute5": "credit_amount",
    "Attribute6": "savings_account",
    "Attribute7": "employment_since",
    "Attribute8": "installment_rate",
    "Attribute9": "personal_status_sex",
    "Attribute10": "other_debtors",
    "Attribute11": "residence_since",
    "Attribute12": "property",
    "Attribute13": "age",
    "Attribute14": "other_installment_plans",
    "Attribute15": "housing",
    "Attribute16": "existing_credits",
    "Attribute17": "job",
    "Attribute18": "people_liable",
    "Attribute19": "telephone",
    "Attribute20": "foreign_worker",
    "class": "credit_class"
}

df.rename(columns=column_mapping, inplace=True)

# Remove exact duplicate records
duplicate_count = int(df.duplicated().sum())
df.drop_duplicates(inplace=True)

# Convert numeric columns
numeric_columns = [
    "loan_duration_months",
    "credit_amount",
    "installment_rate",
    "residence_since",
    "age",
    "existing_credits",
    "people_liable"
]

for col in numeric_columns:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# Remove records without a valid target
df["credit_class"] = pd.to_numeric(
    df["credit_class"], errors="coerce"
)

df = df[df["credit_class"].isin([1, 2])].copy()

# Handle missing numeric values
for col in numeric_columns:
    df[col] = df[col].fillna(df[col].median())

# Handle missing categorical values
categorical_columns = [
    col for col in df.columns
    if col not in numeric_columns + ["credit_class"]
]

for col in categorical_columns:
    df[col] = df[col].fillna("Unknown").astype(str)

# Convert credit classification into business-friendly labels
df["risk_status"] = df["credit_class"].map({
    1: "Good",
    2: "Bad"
})

# Create age groups
df["age_group"] = pd.cut(
    df["age"],
    bins=[0, 25, 35, 45, 55, float("inf")],
    labels=["18-25", "26-35", "36-45", "46-55", "56+"],
    right=True
).astype(str)

# Create loan amount bands based on dataset values
df["loan_amount_band"] = pd.cut(
    df["credit_amount"],
    bins=[0, 2000, 5000, 10000, float("inf")],
    labels=["Low", "Medium", "High", "Very High"],
    right=True
).astype(str)

# Save cleaned dataset
CLEAN_FILE.parent.mkdir(parents=True, exist_ok=True)
REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)

df.to_csv(CLEAN_FILE, index=False)

# Generate data quality report
report = {
    "original_rows": original_rows,
    "final_rows": len(df),
    "duplicate_rows_removed": duplicate_count,
    "missing_values_after_cleaning": int(df.isnull().sum().sum()),
    "columns": len(df.columns),
    "good_credit_records": int((df["risk_status"] == "Good").sum()),
    "bad_credit_records": int((df["risk_status"] == "Bad").sum()),
    "average_credit_amount": round(float(df["credit_amount"].mean()), 2),
    "average_customer_age": round(float(df["age"].mean()), 2)
}

with open(REPORT_FILE, "w") as file:
    json.dump(report, file, indent=4)

print("\nDATA CLEANING COMPLETED")
print("-----------------------")
print(json.dumps(report, indent=4))

print("\nCleaned dataset saved:", CLEAN_FILE)
print("\nCredit risk distribution:")
print(df["risk_status"].value_counts())
