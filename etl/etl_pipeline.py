import os
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv
from prefect import flow, task, get_run_logger
from datetime import datetime

load_dotenv()

DB_CONFIG = {
    "host":     os.getenv("DB_HOST",     "localhost"),
    "port":     int(os.getenv("DB_PORT", "5432")),
    "dbname":   os.getenv("DB_NAME",     "quant_research"),
    "user":     os.getenv("DB_USER",     "postgres"),
    "password": os.getenv("DB_PASSWORD", "postgres"),
}

LOAN_CSV = "../Quant-Research-main/Task 3 - Credit risk analysis/Task 3 and 4_Loan_Data.csv"
GAS_CSV  = "../Quant-Research-main/Task 1 - Natural Gas Price Forecasting/Nat_Gas.csv"


@task(name="extract_loan_data", retries=2, retry_delay_seconds=5)
def extract_loan_data() -> pd.DataFrame:
    logger = get_run_logger()
    df = pd.read_csv(LOAN_CSV)
    logger.info(f"Extracted {len(df):,} rows")
    return df


@task(name="transform_loan_data")
def transform_loan_data(df: pd.DataFrame) -> pd.DataFrame:
    logger = get_run_logger()
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    df.rename(columns={"default": "default_flag"}, inplace=True)
    before = len(df)
    df.drop_duplicates(subset="customer_id", inplace=True)
    logger.info(f"Dropped {before - len(df)} duplicates")
    df["debt_to_income"] = (df["total_debt_outstanding"] / df["income"]).round(4)
    df = df[df["fico_score"].between(300, 850)]
    df = df[df["income"] > 0]
    logger.info(f"Transformed {len(df):,} rows")
    return df


@task(name="load_loan_data", retries=2)
def load_loan_data(df: pd.DataFrame) -> int:
    logger = get_run_logger()
    rows = [
        (
            int(r["customer_id"]),
            int(r["credit_lines_outstanding"]),
            float(r["loan_amt_outstanding"]),
            float(r["total_debt_outstanding"]),
            float(r["income"]),
            int(r["years_employed"]),
            int(r["fico_score"]),
            int(r["default_flag"]),
        )
        for _, r in df.iterrows()
    ]
    sql = """
        INSERT INTO loan_data
            (customer_id, credit_lines_outstanding, loan_amt_outstanding,
             total_debt_outstanding, income, years_employed, fico_score, default_flag)
        VALUES %s
        ON CONFLICT (customer_id) DO NOTHING
    """
    conn = psycopg2.connect(**DB_CONFIG)
    with conn.cursor() as cur:
        execute_values(cur, sql, rows, page_size=500)
    conn.commit()
    conn.close()
    logger.info(f"Loaded {len(rows):,} rows")
    return len(rows)


@task(name="extract_gas_prices")
def extract_gas_prices() -> pd.DataFrame:
    return pd.read_csv(GAS_CSV)


@task(name="transform_gas_prices")
def transform_gas_prices(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = [c.strip() for c in df.columns]
    df["price_date"] = pd.to_datetime(df["Dates"], format="%m/%d/%y").dt.date
    df["price"] = pd.to_numeric(df["Prices"], errors="coerce")
    df.dropna(subset=["price"], inplace=True)
    return df[["price_date", "price"]]


@task(name="load_gas_prices")
def load_gas_prices(df: pd.DataFrame) -> int:
    logger = get_run_logger()
    rows = [(str(r["price_date"]), float(r["price"])) for _, r in df.iterrows()]
    conn = psycopg2.connect(**DB_CONFIG)
    with conn.cursor() as cur:
        execute_values(
            cur,
            "INSERT INTO nat_gas_prices (price_date, price) VALUES %s ON CONFLICT (price_date) DO NOTHING",
            rows,
        )
    conn.commit()
    conn.close()
    logger.info(f"Loaded {len(rows)} rows")
    return len(rows)


@flow(name="quant_research_etl", log_prints=True)
def run_pipeline():
    print(f"\n{'='*50}")
    print(f"  Quant Research ETL — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*50}\n")

    raw_loans   = extract_loan_data()
    clean_loans = transform_loan_data(raw_loans)
    loan_count  = load_loan_data(clean_loans)

    raw_gas   = extract_gas_prices()
    clean_gas = transform_gas_prices(raw_gas)
    gas_count = load_gas_prices(clean_gas)

    print(f"\n✓ Pipeline complete: {loan_count:,} loans + {gas_count} gas prices loaded")


if __name__ == "__main__":
    run_pipeline()
