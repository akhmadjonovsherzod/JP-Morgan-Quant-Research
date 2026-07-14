import os
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv
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


def get_connection():
    return psycopg2.connect(**DB_CONFIG)


def load_loan_data(conn):
    print("Loading loan data...")
    df = pd.read_csv(LOAN_CSV)
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    df.rename(columns={"default": "default_flag"}, inplace=True)

    rows = [
        (
            int(row["customer_id"]),
            int(row["credit_lines_outstanding"]),
            float(row["loan_amt_outstanding"]),
            float(row["total_debt_outstanding"]),
            float(row["income"]),
            int(row["years_employed"]),
            int(row["fico_score"]),
            int(row["default_flag"]),
        )
        for _, row in df.iterrows()
    ]

    sql = """
        INSERT INTO loan_data
            (customer_id, credit_lines_outstanding, loan_amt_outstanding,
             total_debt_outstanding, income, years_employed, fico_score, default_flag)
        VALUES %s
        ON CONFLICT (customer_id) DO NOTHING
    """

    with conn.cursor() as cur:
        execute_values(cur, sql, rows, page_size=500)
    conn.commit()
    print(f"  ✓ Inserted {len(rows):,} loan records")


def load_gas_prices(conn):
    print("Loading natural gas prices...")
    df = pd.read_csv(GAS_CSV)
    df.columns = [c.strip() for c in df.columns]
    df["price_date"] = pd.to_datetime(df["Dates"], format="%m/%d/%y").dt.date
    df["price"] = pd.to_numeric(df["Prices"], errors="coerce")

    rows = [
        (str(row["price_date"]), float(row["price"]))
        for _, row in df.iterrows()
        if pd.notna(row["price"])
    ]

    sql = """
        INSERT INTO nat_gas_prices (price_date, price)
        VALUES %s
        ON CONFLICT (price_date) DO NOTHING
    """

    with conn.cursor() as cur:
        execute_values(cur, sql, rows)
    conn.commit()
    print(f"  ✓ Inserted {len(rows)} gas price records")


def main():
    print(f"\n{'='*50}")
    print(f"  Data Loader — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*50}\n")

    try:
        conn = get_connection()
        print(f"✓ Connected to PostgreSQL\n")
        load_loan_data(conn)
        load_gas_prices(conn)
        conn.close()
        print("\n✓ All data loaded successfully!")

    except psycopg2.OperationalError as e:
        print(f"\n✗ Could not connect: {e}")


if __name__ == "__main__":
    main()
