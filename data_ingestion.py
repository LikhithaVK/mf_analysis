"""
data_ingestion.py
Day 1 — Mutual Fund Data Ingestion & Validation
Run from project root: python data_ingestion.py
"""

import os
import pandas as pd

RAW = "data/raw"

# ---------------------------------------------------------------------------
# 1. LOAD ALL CSV DATASETS
# ---------------------------------------------------------------------------
CSV_FILES = [
    "01_fund_mster.csv",
    "02_nav_history.csv",
    "03_aum_by_fund_house.csv",
    "04_monthly_sip_inflows.csv",
    "05_category_inflows.csv",
    "06_industry_folio_count.csv",
    "07_scheme_performance.csv",
    "08_investor_transactions.csv",
    "09_portfolio_holdings.csv",
    "10_benchmark_indices.csv",
]
dataframes = {}

print("=" * 60)
print("LOADING CSV DATASETS")
print("=" * 60)

for fname in CSV_FILES:
    fpath = os.path.join(RAW, fname)
    key = fname.replace(".csv", "")

    if not os.path.exists(fpath):
        print(f"\n[SKIP] {fname} — file not found at {fpath}")
        continue

    df = pd.read_csv(fpath)
    dataframes[key] = df

    print(f"\n{'─'*50}")
    print(f"FILE : {fname}")
    print(f"SHAPE: {df.shape}  ({df.shape[0]} rows × {df.shape[1]} cols)")
    print("\nDTYPES:")
    print(df.dtypes.to_string())
    print("\nHEAD (5 rows):")
    print(df.head().to_string())

    # Basic anomaly checks
    null_cols = df.columns[df.isnull().any()].tolist()
    dup_count = df.duplicated().sum()
    if null_cols:
        print(f"\n⚠  NULLS in: {null_cols}")
    if dup_count:
        print(f"⚠  {dup_count} duplicate rows detected")

print("\n" + "=" * 60)
print(f"Loaded {len(dataframes)} / {len(CSV_FILES)} datasets successfully")
print("=" * 60)


# ---------------------------------------------------------------------------
# 2. EXPLORE FUND MASTER
# ---------------------------------------------------------------------------

print("\n" + "=" * 60)
print("FUND MASTER EXPLORATION")
print("=" * 60)

if "01_fund_mster" in dataframes:
    fm = dataframes["01_fund_mster"]

    print(f"\nTotal schemes : {len(fm)}")

    if "fund_house" in fm.columns:
        print(f"Unique fund houses : {fm['fund_house'].nunique()}")
        print(fm["fund_house"].value_counts().head(10).to_string())

    if "category" in fm.columns:
        print(f"\nUnique categories : {fm['category'].nunique()}")
        print(fm["category"].unique())

    if "sub_category" in fm.columns:
        print(f"\nUnique sub-categories : {fm['sub_category'].nunique()}")
        print(fm["sub_category"].unique())

    if "risk_grade" in fm.columns:
        print(f"\nRisk grade distribution:")
        print(fm["risk_grade"].value_counts().to_string())

    # AMFI scheme code structure (7-digit numeric)
    if "scheme_code" in fm.columns:
        sample_codes = fm["scheme_code"].head(5).tolist()
        print(f"\nSample scheme codes : {sample_codes}")
        print("AMFI codes are 7-digit numeric identifiers assigned by AMFI.")
else:
    print("fund_master.csv not loaded — skipping exploration.")


# ---------------------------------------------------------------------------
# 3. VALIDATE AMFI CODES
# ---------------------------------------------------------------------------

print("\n" + "=" * 60)
print("AMFI CODE VALIDATION")
print("=" * 60)

if "01_fund_mster" in dataframes and "02_nav_history" in dataframes:
    fm = dataframes["01_fund_mster"]
    nav = dataframes["02_nav_history"]

    if "scheme_code" in fm.columns and "scheme_code" in nav.columns:
        master_codes = set(fm["scheme_code"].dropna().unique())
        nav_codes = set(nav["scheme_code"].dropna().unique())

        missing_in_nav = master_codes - nav_codes
        extra_in_nav = nav_codes - master_codes

        print(f"\nScheme codes in fund_master  : {len(master_codes)}")
        print(f"Scheme codes in nav_history  : {len(nav_codes)}")
        print(f"Codes in master, missing from nav_history : {len(missing_in_nav)}")
        print(f"Codes in nav_history, not in master       : {len(extra_in_nav)}")

        if missing_in_nav:
            print(f"\nSample missing codes: {list(missing_in_nav)[:10]}")

        # ── DATA QUALITY SUMMARY ──────────────────────────────────────────
        # 1. fund_master contains {len(master_codes)} unique AMFI scheme codes.
        # 2. nav_history contains {len(nav_codes)} unique scheme codes.
        # 3. {len(missing_in_nav)} codes present in fund_master have NO matching
        #    NAV records — these schemes may be new, inactive, or data is missing.
        # 4. {len(extra_in_nav)} codes appear in nav_history but not in fund_master —
        #    possibly discontinued schemes or data pipeline gaps.
        # 5. Recommend treating fund_master as the master reference; any downstream
        #    joins should use a LEFT join from fund_master on scheme_code.
        # ─────────────────────────────────────────────────────────────────
        print("\nData quality summary written as comments above.")
    else:
        print("'scheme_code' column not found in one or both datasets.")
else:
    print("fund_master or nav_history not loaded — skipping validation.")

print("\n✓ data_ingestion.py complete")
