
import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

# Load environment variables from project root
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

CSV_FILE = BASE_DIR / "data" / "processed" / "cleaned_credit_data.csv"
SCHEMA_FILE = BASE_DIR / "sql" / "schema.sql"
TABLE_NAME = "credit_risk_analysis"


def main():
    engine = None

    print("Connecting to Neon PostgreSQL...")

    # Validate required files
    if not CSV_FILE.exists():
        raise FileNotFoundError(f"Dataset not found: {CSV_FILE}")

    if not SCHEMA_FILE.exists():
        raise FileNotFoundError(f"Schema file not found: {SCHEMA_FILE}")

    # Read Neon connection string
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise ValueError(
            "DATABASE_URL not found. Please check your project .env file."
        )

    # Add SSL mode only if missing
    if "sslmode=" not in database_url:
        separator = "&" if "?" in database_url else "?"
        database_url += f"{separator}sslmode=require"

    try:
        # Create SQLAlchemy engine
        engine = create_engine(
            database_url,
            pool_pre_ping=True,
            connect_args={"sslmode": "require"}
        )

        # Test connection
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        print("Neon connection successful!")

        # Read cleaned dataset
        df = pd.read_csv(CSV_FILE)

        if df.empty:
            raise ValueError("The cleaned CSV file contains no records.")

        print(f"Loaded {len(df)} records from CSV.")

        # Read existing database schema
        schema_sql = SCHEMA_FILE.read_text(encoding="utf-8")

        # Validate required table name in schema
        if TABLE_NAME not in schema_sql:
            raise ValueError(
                f"Expected table '{TABLE_NAME}' was not found in schema.sql."
            )

        # Create table and replace data in one transaction
        with engine.begin() as connection:

            # Execute schema
            connection.execute(text(schema_sql))

            # Clear existing records before inserting new records
            connection.execute(
                text(
                    f"TRUNCATE TABLE {TABLE_NAME} "
                    "RESTART IDENTITY CASCADE"
                )
            )

            # Upload cleaned dataset
            df.to_sql(
                name=TABLE_NAME,
                con=connection,
                if_exists="append",
                index=False,
                method="multi",
                chunksize=500
            )

        print("Dataset uploaded successfully!")

        # Verify uploaded records
        with engine.connect() as connection:

            total_records = connection.execute(
                text(f"SELECT COUNT(*) FROM {TABLE_NAME}")
            ).scalar_one()

            distribution = connection.execute(
                text(
                    f"""
                    SELECT risk_status, COUNT(*) AS total
                    FROM {TABLE_NAME}
                    GROUP BY risk_status
                    ORDER BY risk_status
                    """
                )
            ).fetchall()

        print("\n========== DATABASE VERIFICATION ==========")
        print(f"CSV records: {len(df)}")
        print(f"Database records: {total_records}")

        print("\nCredit Risk Distribution:")

        for status, count in distribution:
            print(f"{status}: {count}")

        if total_records != len(df):
            raise RuntimeError(
                "Record count mismatch. Please check the database upload."
            )

        print("\nSUCCESS: All records verified in Neon PostgreSQL.")

    except Exception as error:
        print("\nDATABASE LOAD FAILED")
        print(f"Error: {error}")
        raise

    finally:
        if engine is not None:
            engine.dispose()


if __name__ == "__main__":
    main()
