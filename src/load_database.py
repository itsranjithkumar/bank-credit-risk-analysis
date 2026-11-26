
import os
import getpass
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, URL, text

CSV_FILE = Path("data/processed/cleaned_credit_data.csv")

print("Loading cleaned banking data into PostgreSQL...")

if not CSV_FILE.exists():
    raise FileNotFoundError(f"Dataset not found: {CSV_FILE}")

# Database configuration
password = os.getenv("DB_PASSWORD") or getpass.getpass(
    "Enter PostgreSQL analyst password: "
)

db_url = URL.create(
    drivername="postgresql+psycopg2",
    username="analyst",
    password=password,
    host="localhost",
    port=5432,
    database="bank_credit_risk_analysis"
)

engine = create_engine(db_url)

# Read cleaned CSV
df = pd.read_csv(CSV_FILE)

# Load into existing PostgreSQL table
with engine.begin() as connection:
    existing_count = connection.execute(
        text("SELECT COUNT(*) FROM credit_risk_analysis")
    ).scalar()

    if existing_count > 0:
        raise RuntimeError(
            f"Table already contains {existing_count} records. "
            "Stopping to avoid duplicate insertion."
        )

    df.to_sql(
        name="credit_risk_analysis",
        con=connection,
        if_exists="append",
        index=False,
        method="multi",
        chunksize=500
    )

# Verify database records
with engine.connect() as connection:
    total = connection.execute(
        text("SELECT COUNT(*) FROM credit_risk_analysis")
    ).scalar()

    distribution = connection.execute(
        text("""
            SELECT risk_status, COUNT(*)
            FROM credit_risk_analysis
            GROUP BY risk_status
            ORDER BY risk_status
        """)
    ).fetchall()

print("\nDATABASE LOAD SUCCESSFUL")
print("------------------------")
print("Records loaded:", total)
print("\nCredit risk distribution:")

for status, count in distribution:
    print(f"{status}: {count}")

engine.dispose()
