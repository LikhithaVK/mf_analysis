"""
db_loader.py
Day 2 — SQLite Star Schema + Data Load
Run: python db_loader.py
Creates: bluestock_mf.db in project root
"""

import os
import sqlite3
import pandas as pd
from sqlalchemy import create_engine, text

PROCESSED = "data/processed"
DB_PATH   = "bluestock_mf.db"

engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)

# ─────────────────────────────────────────────────────────────────────────────
# 1. CREATE STAR SCHEMA
# ─────────────────────────────────────────────────────────────────────────────
SCHEMA_SQL = """
-- ── DIMENSION TABLES ──────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS dim_fund (
    amfi_code       INTEGER PRIMARY KEY,
    scheme_name     TEXT    NOT NULL,
    fund_house      TEXT,
    category        TEXT,
    sub_category    TEXT,
    fund_type       TEXT,
    risk_grade      TEXT,
    benchmark       TEXT,
    launch_date     TEXT
);

CREATE TABLE IF NOT EXISTS dim_date (
    date_id         TEXT    PRIMARY KEY,   -- YYYY-MM-DD
    year            INTEGER,
    quarter         INTEGER,
    month           INTEGER,
    month_name      TEXT,
    week            INTEGER,
    day_of_week     TEXT,
    is_month_end    INTEGER                -- 1 or 0
);

-- ── FACT TABLES ───────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS fact_nav (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    amfi_code       INTEGER NOT NULL,
    date_id         TEXT    NOT NULL,
    nav             REAL    NOT NULL CHECK (nav > 0),
    FOREIGN KEY (amfi_code) REFERENCES dim_fund (amfi_code),
    FOREIGN KEY (date_id)   REFERENCES dim_date (date_id)
);

CREATE TABLE IF NOT EXISTS fact_transactions (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    transaction_date    TEXT,
    amfi_code           INTEGER,
    investor_id         TEXT,
    transaction_type    TEXT    CHECK (transaction_type IN ('SIP','Lumpsum','Redemption','Switch','SWP','Other')),
    amount              REAL    CHECK (amount > 0),
    units               REAL,
    nav_at_transaction  REAL,
    state               TEXT,
    kyc_status          TEXT,
    FOREIGN KEY (amfi_code) REFERENCES dim_fund (amfi_code)
);

CREATE TABLE IF NOT EXISTS fact_performance (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    amfi_code       INTEGER,
    as_of_date      TEXT,
    return_1y       REAL,
    return_3y       REAL,
    return_5y       REAL,
    return_ytd      REAL,
    expense_ratio   REAL,
    sharpe_ratio    REAL,
    alpha           REAL,
    beta            REAL,
    FOREIGN KEY (amfi_code) REFERENCES dim_fund (amfi_code)
);

CREATE TABLE IF NOT EXISTS fact_aum (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    fund_house      TEXT,
    month           TEXT,
    aum_crore       REAL,
    scheme_count    INTEGER
);
"""

print("Creating SQLite star schema...")
with engine.connect() as conn:
    for stmt in SCHEMA_SQL.strip().split(";"):
        stmt = stmt.strip()
        if stmt and not stmt.startswith("--"):
            conn.execute(text(stmt))
    conn.commit()
print("✓ Schema created")


# ─────────────────────────────────────────────────────────────────────────────
# 2. HELPER — load CSV and push to SQLite
# ─────────────────────────────────────────────────────────────────────────────

def load_table(csv_fname, table_name, column_map=None):
    fpath = os.path.join(PROCESSED, csv_fname)
    if not os.path.exists(fpath):
        print(f"  [SKIP] {csv_fname} not found in data/processed/")
        return

    df = pd.read_csv(fpath)

    if column_map:
        df.rename(columns=column_map, inplace=True)

    # Only keep columns that exist in df
    df.to_sql(table_name, con=engine, if_exists="replace", index=False)

    # Verify row count
    with engine.connect() as conn:
        db_count = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()
    match = "✓" if db_count == len(df) else "✗ MISMATCH"
    print(f"  {match}  {table_name}: source={len(df)} rows, db={db_count} rows")


# ─────────────────────────────────────────────────────────────────────────────
# 3. BUILD dim_date from NAV history date range
# ─────────────────────────────────────────────────────────────────────────────

print("\nBuilding dim_date...")
nav_path = os.path.join(PROCESSED, "02_nav_history_clean.csv")
if os.path.exists(nav_path):
    nav = pd.read_csv(nav_path)
    date_col = [c for c in nav.columns if "date" in c.lower()][0]
    dates = pd.to_datetime(nav[date_col], errors="coerce").dropna().unique()
    date_df = pd.DataFrame({"date_id": pd.DatetimeIndex(dates)})
    date_df["date_id"]     = date_df["date_id"].dt.strftime("%Y-%m-%d")
    date_df["year"]        = pd.DatetimeIndex(dates).year
    date_df["quarter"]     = pd.DatetimeIndex(dates).quarter
    date_df["month"]       = pd.DatetimeIndex(dates).month
    date_df["month_name"]  = pd.DatetimeIndex(dates).strftime("%B")
    date_df["week"]        = pd.DatetimeIndex(dates).isocalendar().week.values
    date_df["day_of_week"] = pd.DatetimeIndex(dates).strftime("%A")
    date_df["is_month_end"]= pd.DatetimeIndex(dates).is_month_end.astype(int)
    date_df.drop_duplicates("date_id", inplace=True)
    date_df.to_sql("dim_date", con=engine, if_exists="replace", index=False)
    print(f"  ✓ dim_date: {len(date_df)} dates loaded")
else:
    print("  [SKIP] nav_history_clean.csv not found — dim_date not built")


# ─────────────────────────────────────────────────────────────────────────────
# 4. LOAD ALL TABLES
# ─────────────────────────────────────────────────────────────────────────────

print("\nLoading cleaned data into SQLite...")

load_table("01_fund_master_clean.csv",          "dim_fund")
load_table("02_nav_history_clean.csv",          "fact_nav")
load_table("08_investor_transactions_clean.csv","fact_transactions")
load_table("07_scheme_performance_clean.csv",   "fact_performance")
load_table("03_aum_by_fund_house_clean.csv",    "fact_aum")
load_table("04_monthly_sip_inflows_clean.csv",  "sip_inflows")
load_table("05_category_inflows_clean.csv",     "category_inflows")
load_table("06_industry_folio_count_clean.csv", "folio_count")
load_table("09_portfolio_holdings_clean.csv",   "portfolio_holdings")
load_table("10_benchmark_indices_clean.csv",    "benchmark_indices")

print(f"\n✓ db_loader.py complete — database saved to {DB_PATH}")
