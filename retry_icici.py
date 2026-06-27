import requests, pandas as pd, time

code, name = 120503, "ICICI Prudential Bluechip Direct"
url = f"https://api.mfapi.in/mf/{code}"

for attempt in range(3):
    try:
        print(f"Attempt {attempt+1}...")
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        df = pd.DataFrame(r.json()['data'])
        df['scheme_code'] = code
        df['scheme_name'] = name
        df['nav'] = pd.to_numeric(df['nav'], errors='coerce')
        df['date'] = pd.to_datetime(df['date'], format='%d-%m-%Y', errors='coerce')
        df.sort_values('date', inplace=True)
        df.to_csv(f"data/raw/icici_prudential_bluechip_direct_{code}_nav.csv", index=False)
        print(f"✓ {len(df)} records saved. Latest NAV: ₹{df['nav'].iloc[-1]:.4f}")
        break
    except Exception as e:
        print(f"  ✗ {e}")
        time.sleep(5)
