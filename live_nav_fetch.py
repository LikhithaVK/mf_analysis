"""
live_nav_fetch.py
Day 1 — Live NAV Fetch from mfapi.in
Run from project root: python live_nav_fetch.py
"""

import os
import time
import requests
import pandas as pd

RAW = "data/raw"
os.makedirs(RAW, exist_ok=True)

BASE_URL = "https://api.mfapi.in/mf/{scheme_code}"

# ---------------------------------------------------------------------------
# SCHEME REGISTRY
# ---------------------------------------------------------------------------

SCHEMES = {
    125497: "HDFC Top 100 Direct",
    119551: "SBI Bluechip Direct",
    120503: "ICICI Prudential Bluechip Direct",
    118632: "Nippon India Large Cap Direct",
    119092: "Axis Bluechip Direct",
    120841: "Kotak Bluechip Direct",
}


# ---------------------------------------------------------------------------
# FETCH HELPER
# ---------------------------------------------------------------------------

def fetch_nav(scheme_code: int, scheme_name: str) -> pd.DataFrame | None:
    """
    Fetch historical NAV for a scheme from mfapi.in.
    Returns a DataFrame with columns: date, nav, scheme_code, scheme_name.
    Saves raw CSV to data/raw/.
    """
    url = BASE_URL.format(scheme_code=scheme_code)
    print(f"\nFetching: {scheme_name} (code: {scheme_code})")
    print(f"  URL: {url}")

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"  ✗ Request failed: {e}")
        return None

    data = response.json()

    # Validate response structure
    if "data" not in data or not data["data"]:
        print(f"  ✗ No 'data' key in response or empty. Keys: {list(data.keys())}")
        return None

    # Parse NAV records
    df = pd.DataFrame(data["data"])          # columns: date, nav
    df["scheme_code"] = scheme_code
    df["scheme_name"] = scheme_name

    # Clean up types
    df["nav"] = pd.to_numeric(df["nav"], errors="coerce")
    df["date"] = pd.to_datetime(df["date"], format="%d-%m-%Y", errors="coerce")
    df.sort_values("date", inplace=True)
    df.reset_index(drop=True, inplace=True)

    # Save
    safe_name = scheme_name.lower().replace(" ", "_").replace("/", "_")
    out_path = os.path.join(RAW, f"{safe_name}_{scheme_code}_nav.csv")
    df.to_csv(out_path, index=False)
    print(f"  ✓ {len(df)} NAV records saved → {out_path}")
    print(f"    Date range: {df['date'].min().date()} to {df['date'].max().date()}")
    print(f"    Latest NAV: ₹{df['nav'].iloc[-1]:.4f}")

    return df


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("LIVE NAV FETCH — mfapi.in")
    print("=" * 60)

    all_dfs = []
    failed = []

    for code, name in SCHEMES.items():
        df = fetch_nav(code, name)
        if df is not None:
            all_dfs.append(df)
        else:
            failed.append((code, name))
        time.sleep(0.5)   # polite delay between requests

    # Combine all into one master NAV file
    if all_dfs:
        combined = pd.concat(all_dfs, ignore_index=True)
        combined_path = os.path.join(RAW, "all_schemes_nav_combined.csv")
        combined.to_csv(combined_path, index=False)
        print(f"\n✓ Combined NAV file saved → {combined_path}")
        print(f"  Total rows: {len(combined)}")
        print(f"  Schemes fetched: {combined['scheme_name'].nunique()}")

    if failed:
        print(f"\n✗ Failed fetches ({len(failed)}):")
        for code, name in failed:
            print(f"  {code} — {name}")
    else:
        print("\n✓ All schemes fetched successfully")

    print("\n✓ live_nav_fetch.py complete")
