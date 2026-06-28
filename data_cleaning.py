"""
data_cleaning.py
Day 2 — Data Cleaning
Reads from data/raw/, writes cleaned files to data/processed/
Run: python data_cleaning.py
"""

import os
import pandas as pd
import numpy as np

RAW = "data/raw"
PROCESSED = "data/processed"
os.makedirs(PROCESSED, exist_ok=True)

issues = []  # collect all anomalies for summary at end

# ── helper ────────────────────────────────────────────────────────────────────
def save(df, fname):
    path = os.path.join(PROCESSED, fname)
    df.to_csv(path, index=False)
    print(f"  ✓ Saved {fname}  ({len(df)} rows)")

def section(title):
    print(f"\n{'='*60}\n{title}\n{'='*60}")

# ─────────────────────────────────────────────────────────────────────────────
# 1. NAV HISTORY
# ─────────────────────────────────────────────────────────────────────────────
section("1. CLEANING nav_history.csv")

nav = pd.read_csv(os.path.join(RAW, "02_nav_history.csv"))
print(f"  Raw shape : {nav.shape}")

# Parse dates
date_col = [c for c in nav.columns if "date" in c.lower()][0]
nav[date_col] = pd.to_datetime(nav[date_col], errors="coerce")
null_dates = nav[date_col].isna().sum()
if null_dates:
    issues.append(f"nav_history: {null_dates} unparseable dates dropped")
nav.dropna(subset=[date_col], inplace=True)

# Identify amfi/scheme code column
code_col = next((c for c in nav.columns if "amfi" in c.lower() or "scheme_code" in c.lower() or "code" in c.lower()), None)
nav_col  = next((c for c in nav.columns if "nav" in c.lower()), None)

# Remove duplicates
before = len(nav)
nav.drop_duplicates(subset=[code_col, date_col] if code_col else [date_col], inplace=True)
dupes = before - len(nav)
if dupes:
    issues.append(f"nav_history: {dupes} duplicate rows removed")

# Sort
sort_cols = [code_col, date_col] if code_col else [date_col]
nav.sort_values(sort_cols, inplace=True)
nav.reset_index(drop=True, inplace=True)

# Forward-fill missing NAV (holidays/weekends) per scheme
if code_col and nav_col:
    nav[nav_col] = pd.to_numeric(nav[nav_col], errors="coerce")
    nav[nav_col] = nav.groupby(code_col)[nav_col].ffill()

# Validate NAV > 0
invalid_nav = nav[nav_col] <= 0 if nav_col else pd.Series([], dtype=bool)
count_invalid = invalid_nav.sum() if hasattr(invalid_nav, "sum") else 0
if count_invalid:
    issues.append(f"nav_history: {count_invalid} rows with NAV <= 0 dropped")
    nav = nav[nav[nav_col] > 0]

print(f"  Clean shape: {nav.shape}")
save(nav, "02_nav_history_clean.csv")


# ─────────────────────────────────────────────────────────────────────────────
# 2. INVESTOR TRANSACTIONS
# ─────────────────────────────────────────────────────────────────────────────
section("2. CLEANING investor_transactions.csv")

txn = pd.read_csv(os.path.join(RAW, "08_investor_transactions.csv"))
print(f"  Raw shape : {txn.shape}")

# Fix date formats
date_cols = [c for c in txn.columns if "date" in c.lower()]
for dc in date_cols:
    txn[dc] = pd.to_datetime(txn[dc], errors="coerce")

# Standardise transaction_type
txn_col = next((c for c in txn.columns if "type" in c.lower() or "transaction" in c.lower()), None)
if txn_col:
    txn[txn_col] = txn[txn_col].astype(str).str.strip().str.title()
    type_map = {
        "Sip": "SIP", "Systematic Investment Plan": "SIP",
        "Lumpsum": "Lumpsum", "Lump Sum": "Lumpsum", "One Time": "Lumpsum",
        "Redemption": "Redemption", "Redeem": "Redemption", "Withdrawal": "Redemption",
        "Switch": "Switch", "Swp": "SWP",
    }
    txn[txn_col] = txn[txn_col].replace(type_map)
    valid_types = {"SIP", "Lumpsum", "Redemption", "Switch", "SWP"}
    bad_types = ~txn[txn_col].isin(valid_types)
    if bad_types.sum():
        issues.append(f"investor_transactions: {bad_types.sum()} unknown transaction types → 'Other'")
        txn.loc[bad_types, txn_col] = "Other"
    print(f"  Transaction types: {txn[txn_col].unique()}")

# Validate amount > 0
amt_col = next((c for c in txn.columns if "amount" in c.lower()), None)
if amt_col:
    txn[amt_col] = pd.to_numeric(txn[amt_col], errors="coerce")
    bad_amt = txn[amt_col] <= 0
    if bad_amt.sum():
        issues.append(f"investor_transactions: {bad_amt.sum()} rows with amount <= 0 dropped")
        txn = txn[txn[amt_col] > 0]

# Check KYC enum
kyc_col = next((c for c in txn.columns if "kyc" in c.lower()), None)
if kyc_col:
    txn[kyc_col] = txn[kyc_col].astype(str).str.strip().str.upper()
    valid_kyc = {"YES", "NO", "PENDING", "VERIFIED", "TRUE", "FALSE", "1", "0"}
    bad_kyc = ~txn[kyc_col].isin(valid_kyc)
    if bad_kyc.sum():
        issues.append(f"investor_transactions: {bad_kyc.sum()} unexpected KYC values")
    print(f"  KYC values: {txn[kyc_col].unique()}")

txn.drop_duplicates(inplace=True)
print(f"  Clean shape: {txn.shape}")
save(txn, "08_investor_transactions_clean.csv")


# ─────────────────────────────────────────────────────────────────────────────
# 3. SCHEME PERFORMANCE
# ─────────────────────────────────────────────────────────────────────────────
section("3. CLEANING scheme_performance.csv")

perf = pd.read_csv(os.path.join(RAW, "07_scheme_performance.csv"))
print(f"  Raw shape : {perf.shape}")

# Return columns — coerce to numeric
return_cols = [c for c in perf.columns if any(x in c.lower() for x in ["return", "1y", "3y", "5y", "ytd", "cagr"])]
for rc in return_cols:
    perf[rc] = pd.to_numeric(perf[rc], errors="coerce")

# Flag anomalies — returns outside -100% to +200%
for rc in return_cols:
    anomalies = perf[(perf[rc] < -100) | (perf[rc] > 200)][rc]
    if len(anomalies):
        issues.append(f"scheme_performance: {len(anomalies)} anomalous values in {rc} (outside -100% to 200%)")
        print(f"  ⚠ {rc}: {len(anomalies)} anomalies flagged")
        perf.loc[(perf[rc] < -100) | (perf[rc] > 200), rc] = np.nan

# Expense ratio validation (0.1% to 2.5%)
exp_col = next((c for c in perf.columns if "expense" in c.lower() or "ter" in c.lower()), None)
if exp_col:
    perf[exp_col] = pd.to_numeric(perf[exp_col], errors="coerce")
    bad_exp = perf[(perf[exp_col] < 0.1) | (perf[exp_col] > 2.5)]
    if len(bad_exp):
        issues.append(f"scheme_performance: {len(bad_exp)} rows with expense_ratio outside 0.1–2.5%")
        print(f"  ⚠ expense_ratio: {len(bad_exp)} out-of-range values flagged as NaN")
        perf.loc[(perf[exp_col] < 0.1) | (perf[exp_col] > 2.5), exp_col] = np.nan

perf.drop_duplicates(inplace=True)
print(f"  Clean shape: {perf.shape}")
save(perf, "07_scheme_performance_clean.csv")


# ─────────────────────────────────────────────────────────────────────────────
# 4. REMAINING FILES — generic clean
# ─────────────────────────────────────────────────────────────────────────────
section("4. CLEANING REMAINING FILES")

other_files = {
    "01_fund_mster.csv":          "01_fund_master_clean.csv",
    "03_aum_by_fund_house.csv":  "03_aum_by_fund_house_clean.csv",
    "04_monthly_sip_inflows.csv":"04_monthly_sip_inflows_clean.csv",
    "05_category_inflows.csv":   "05_category_inflows_clean.csv",
    "06_industry_folio_count.csv":"06_industry_folio_count_clean.csv",
    "09_portfolio_holdings.csv": "09_portfolio_holdings_clean.csv",
    "10_benchmark_indices.csv":  "10_benchmark_indices_clean.csv",
}

for raw_fname, clean_fname in other_files.items():
    fpath = os.path.join(RAW, raw_fname)
    if not os.path.exists(fpath):
        print(f"  [SKIP] {raw_fname} not found")
        continue

    df = pd.read_csv(fpath)
    before = len(df)

    # Parse any date columns
    for c in df.columns:
        if "date" in c.lower():
            df[c] = pd.to_datetime(df[c], errors="coerce")

    # Strip string whitespace
    str_cols = df.select_dtypes(include="object").columns
    for c in str_cols:
        df[c] = df[c].str.strip()

    # Remove fully empty rows
    df.dropna(how="all", inplace=True)
    df.drop_duplicates(inplace=True)

    dupes = before - len(df)
    if dupes:
        issues.append(f"{raw_fname}: {dupes} duplicate/empty rows removed")

    save(df, clean_fname)


# ─────────────────────────────────────────────────────────────────────────────
# ANOMALY SUMMARY
# ─────────────────────────────────────────────────────────────────────────────
section("DATA QUALITY SUMMARY")
if issues:
    for i, issue in enumerate(issues, 1):
        print(f"  {i}. {issue}")
else:
    print("  No major anomalies found.")

print("\n✓ data_cleaning.py complete — check data/processed/")
