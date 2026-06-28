import pandas as pd
df = pd.read_csv("data/raw/01_fund_master.csv")
for c in df.columns:
    if "date" in c.lower():
        df[c] = pd.to_datetime(df[c], errors="coerce")
df.dropna(how="all", inplace=True)
df.drop_duplicates(inplace=True)
str_cols = df.select_dtypes(include="object").columns
for c in str_cols:
    df[c] = df[c].str.strip()
df.to_csv("data/processed/01_fund_master_clean.csv", index=False)
print(f"✓ Saved 01_fund_master_clean.csv ({len(df)} rows)")
