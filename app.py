
import os
from pathlib import Path
from dotenv import load_dotenv

import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine, text

# Load environment variables from project root
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

st.set_page_config(
    page_title="Bank Credit Risk Analytics",
    page_icon="🏦",
    layout="wide"
)

st.title("Bank Customer Credit Risk Analysis")
st.caption("Business Analytics Dashboard | German Credit Dataset")

@st.cache_data(ttl=60)
def load_data():
    # Try to read DATABASE_URL from Streamlit secrets safely
    database_url = None
    try:
        database_url = st.secrets.get("DATABASE_URL")
    except Exception:
        # secrets.toml not available or st.secrets not initialized
        pass

    # Fall back to environment variables
    if not database_url:
        database_url = os.getenv("DATABASE_URL")

    # If neither source contains DATABASE_URL, show error
    if not database_url:
        st.error("DATABASE_URL not found")
        st.info(
            "Please set DATABASE_URL in your .env file or "
            "in Streamlit secrets (secrets.toml)."
        )
        st.stop()

    # Ensure driver uses psycopg2 (matches psycopg2-binary in requirements)
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+psycopg2://", 1)
    elif database_url.startswith("postgresql+psycopg://"):
        database_url = database_url.replace("postgresql+psycopg://", "postgresql+psycopg2://", 1)

    # Add SSL mode only if missing
    if "sslmode=" not in database_url:
        separator = "&" if "?" in database_url else "?"
        database_url += f"{separator}sslmode=require"

    # Create SQLAlchemy engine with SSL
    engine = create_engine(
        database_url,
        pool_pre_ping=True,
        connect_args={"sslmode": "require"}
    )

    try:
        with engine.connect() as connection:
            df = pd.read_sql(
                text("SELECT * FROM credit_risk_analysis"),
                connection
            )
    except Exception as e:
        st.error("Database Connection Failed")
        st.info(f"Failed to connect to Neon PostgreSQL: {e}")
        st.stop()
    finally:
        engine.dispose()

    return df


try:
    df = load_data()

    st.sidebar.header("Dashboard Filters")

    age_options = sorted(df["age_group"].dropna().unique())
    selected_age = st.sidebar.multiselect(
        "Age Group",
        age_options,
        default=age_options
    )

    purpose_options = sorted(
        df["loan_purpose"].dropna().unique()
    )
    selected_purpose = st.sidebar.multiselect(
        "Loan Purpose",
        purpose_options,
        default=purpose_options
    )

    filtered = df[
        df["age_group"].isin(selected_age)
        & df["loan_purpose"].isin(selected_purpose)
    ].copy()

    total = len(filtered)
    good = (filtered["risk_status"] == "Good").sum()
    bad = (filtered["risk_status"] == "Bad").sum()

    bad_rate = (bad / total * 100) if total else 0

    st.subheader("Key Performance Indicators")

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Total Customers", f"{total:,}")
    c2.metric("Good Credit", f"{good:,}")
    c3.metric("Bad Credit", f"{bad:,}")
    c4.metric("Bad Classification Rate", f"{bad_rate:.2f}%")

    st.divider()

    left, right = st.columns(2)

    with left:
        st.subheader("Credit Classification Distribution")

        risk_counts = (
            filtered["risk_status"]
            .value_counts()
            .rename_axis("Classification")
            .reset_index(name="Customers")
        )

        fig = px.pie(
            risk_counts,
            names="Classification",
            values="Customers",
            hole=0.55
        )

        st.plotly_chart(fig, use_container_width=True)

    with right:
        st.subheader("Average Loan Amount by Classification")

        avg_loan = (
            filtered.groupby("risk_status", as_index=False)
            ["credit_amount"].mean()
        )

        fig = px.bar(
            avg_loan,
            x="risk_status",
            y="credit_amount",
            color="risk_status",
            labels={
                "risk_status": "Classification",
                "credit_amount": "Average Loan Amount"
            }
        )

        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    left, right = st.columns(2)

    with left:
        st.subheader("Bad Credit by Age Group")

        age_analysis = (
            filtered.groupby("age_group")
            .agg(
                Total=("risk_status", "size"),
                Bad=("risk_status", lambda x: (x == "Bad").sum())
            )
            .reset_index()
        )

        fig = px.bar(
            age_analysis,
            x="age_group",
            y="Bad",
            labels={
                "age_group": "Age Group",
                "Bad": "Bad Credit Classifications"
            }
        )

        st.plotly_chart(fig, use_container_width=True)

    with right:
        st.subheader("Loan Purpose Analysis")

        purpose_analysis = (
            filtered.groupby("loan_purpose")
            .agg(
                Total=("risk_status", "size"),
                Bad=("risk_status", lambda x: (x == "Bad").sum())
            )
            .reset_index()
        )

        fig = px.bar(
            purpose_analysis,
            x="loan_purpose",
            y="Bad",
            labels={
                "loan_purpose": "Loan Purpose",
                "Bad": "Bad Credit Classifications"
            }
        )

        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    st.subheader("Customer Credit Risk Records")

    st.dataframe(
        filtered,
        use_container_width=True,
        hide_index=True
    )

    st.caption(
        "Source: UCI Statlog German Credit Dataset. "
        "Good/Bad labels represent recorded dataset classifications, "
        "not observed future loan defaults."
    )

except ConnectionError as e:
    st.error("Database Connection Failed")
    st.info(f"{e}")
    st.info(
        "Please ensure DATABASE_URL is set in Streamlit secrets "
        "or in your .env file and Neon PostgreSQL is accessible."
    )
except Exception as e:
    st.error("Dashboard could not load")
    st.info(f"Error: {e}")
    st.info(
        "Please check that the database contains the "
        "credit_risk_analysis table with data."
    )
