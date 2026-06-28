-- ============================================================
-- schema.sql
-- Bluestock MF Analysis — SQLite Star Schema
-- Day 2 Deliverable
-- ============================================================

-- ── DIMENSION TABLES ──────────────────────────────────────

CREATE TABLE IF NOT EXISTS dim_fund (
    amfi_code       INTEGER PRIMARY KEY,   -- Unique AMFI scheme code (7 digits)
    scheme_name     TEXT    NOT NULL,      -- Full name of the mutual fund scheme
    fund_house      TEXT,                  -- AMC name (e.g. HDFC, SBI, ICICI)
    category        TEXT,                  -- SEBI category (Equity, Debt, Hybrid)
    sub_category    TEXT,                  -- Sub-category (Large Cap, Mid Cap etc.)
    fund_type       TEXT,                  -- Direct or Regular
    risk_grade      TEXT,                  -- Low / Moderate / High / Very High
    benchmark       TEXT,                  -- Benchmark index name
    launch_date     TEXT                   -- Fund launch date (YYYY-MM-DD)
);

CREATE TABLE IF NOT EXISTS dim_date (
    date_id         TEXT    PRIMARY KEY,   -- Date in YYYY-MM-DD format
    year            INTEGER,               -- Calendar year
    quarter         INTEGER,               -- Quarter (1–4)
    month           INTEGER,               -- Month number (1–12)
    month_name      TEXT,                  -- Month name (January etc.)
    week            INTEGER,               -- ISO week number
    day_of_week     TEXT,                  -- Day name (Monday etc.)
    is_month_end    INTEGER                -- 1 if last day of month, else 0
);

-- ── FACT TABLES ───────────────────────────────────────────

CREATE TABLE IF NOT EXISTS fact_nav (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    amfi_code       INTEGER NOT NULL,      -- FK → dim_fund
    date_id         TEXT    NOT NULL,      -- FK → dim_date
    nav             REAL    NOT NULL CHECK (nav > 0),  -- Net Asset Value in ₹
    FOREIGN KEY (amfi_code) REFERENCES dim_fund (amfi_code),
    FOREIGN KEY (date_id)   REFERENCES dim_date (date_id)
);

CREATE TABLE IF NOT EXISTS fact_transactions (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    transaction_date    TEXT,              -- Date of transaction (YYYY-MM-DD)
    amfi_code           INTEGER,           -- FK → dim_fund
    investor_id         TEXT,              -- Unique investor identifier
    transaction_type    TEXT CHECK (transaction_type IN
                            ('SIP','Lumpsum','Redemption','Switch','SWP','Other')),
    amount              REAL CHECK (amount > 0),  -- Transaction amount in ₹
    units               REAL,              -- Units purchased or redeemed
    nav_at_transaction  REAL,             -- NAV on transaction date
    state               TEXT,              -- Investor's state (for geo analysis)
    kyc_status          TEXT,              -- KYC verification status
    FOREIGN KEY (amfi_code) REFERENCES dim_fund (amfi_code)
);

CREATE TABLE IF NOT EXISTS fact_performance (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    amfi_code       INTEGER,               -- FK → dim_fund
    as_of_date      TEXT,                  -- Performance snapshot date
    return_1y       REAL,                  -- 1-year return (%)
    return_3y       REAL,                  -- 3-year CAGR (%)
    return_5y       REAL,                  -- 5-year CAGR (%)
    return_ytd      REAL,                  -- Year-to-date return (%)
    expense_ratio   REAL,                  -- TER in % (valid range: 0.1–2.5)
    sharpe_ratio    REAL,                  -- Risk-adjusted return metric
    alpha           REAL,                  -- Excess return vs benchmark
    beta            REAL,                  -- Sensitivity to market movements
    FOREIGN KEY (amfi_code) REFERENCES dim_fund (amfi_code)
);

CREATE TABLE IF NOT EXISTS fact_aum (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    fund_house      TEXT,                  -- AMC name
    month           TEXT,                  -- Month (YYYY-MM)
    aum_crore       REAL,                  -- Assets under management in ₹ crore
    scheme_count    INTEGER                -- Number of schemes for that month
);
