# Data Dictionary
## Bluestock Fintech — Mutual Fund Analysis Project
**Day 2 Deliverable**

---

## How to read this document

Each section covers one table. For every column you'll find:
- **Type** — the data type stored in SQLite
- **Definition** — what the column actually means in plain English
- **Source** — which raw CSV it came from

---

## dim_fund

The main reference table. One row per mutual fund scheme.

| Column | Type | Definition | Source |
|---|---|---|---|
| amfi_code | INTEGER (PK) | Unique 6–7 digit number assigned by AMFI to every scheme | 01_fund_mster.csv |
| scheme_name | TEXT | Full official name of the mutual fund scheme | 01_fund_mster.csv |
| fund_house | TEXT | Name of the Asset Management Company (AMC) that runs the fund | 01_fund_mster.csv |
| category | TEXT | SEBI-defined broad category — Equity, Debt, Hybrid, Solution Oriented, Other | 01_fund_mster.csv |
| sub_category | TEXT | More specific bucket within the category — Large Cap, Mid Cap, Liquid, ELSS etc. | 01_fund_mster.csv |
| fund_type | TEXT | Whether this is a Direct plan (no distributor commission) or Regular plan | 01_fund_mster.csv |
| risk_grade | TEXT | Risk level as per SEBI riskometer — Low, Low to Moderate, Moderate, Moderately High, High, Very High | 01_fund_mster.csv |
| benchmark | TEXT | Index used to measure the fund's performance (e.g. Nifty 50, BSE Sensex) | 01_fund_mster.csv |
| launch_date | TEXT | Date when the fund started (YYYY-MM-DD) | 01_fund_mster.csv |

---

## dim_date

Calendar dimension. One row per trading date in the dataset.

| Column | Type | Definition | Source |
|---|---|---|---|
| date_id | TEXT (PK) | Date in YYYY-MM-DD format — used as the join key | Generated from 02_nav_history.csv |
| year | INTEGER | Calendar year (e.g. 2024) | Generated |
| quarter | INTEGER | Quarter number 1–4 (Q1 = Jan–Mar) | Generated |
| month | INTEGER | Month number 1–12 | Generated |
| month_name | TEXT | Full month name (January, February…) | Generated |
| week | INTEGER | ISO week number of the year (1–53) | Generated |
| day_of_week | TEXT | Day name (Monday, Tuesday…) | Generated |
| is_month_end | INTEGER | 1 if this date is the last day of the month, else 0 | Generated |

---

## fact_nav

Daily NAV (price) of every fund scheme. This is the largest table.

| Column | Type | Definition | Source |
|---|---|---|---|
| id | INTEGER (PK) | Auto-generated row ID | System |
| amfi_code | INTEGER (FK) | Links to dim_fund — tells you which fund this NAV belongs to | 02_nav_history.csv |
| date_id | TEXT (FK) | Links to dim_date — the date of this NAV | 02_nav_history.csv |
| nav | REAL | Net Asset Value in Indian Rupees (₹). Must be > 0 | 02_nav_history.csv |

---

## fact_transactions

Every buy, sell, or switch transaction made by investors.

| Column | Type | Definition | Source |
|---|---|---|---|
| id | INTEGER (PK) | Auto-generated row ID | System |
| transaction_date | TEXT | Date the transaction was processed (YYYY-MM-DD) | 08_investor_transactions.csv |
| amfi_code | INTEGER (FK) | Which fund was bought/sold | 08_investor_transactions.csv |
| investor_id | TEXT | Anonymised unique identifier for each investor | 08_investor_transactions.csv |
| transaction_type | TEXT | Type of transaction — SIP, Lumpsum, Redemption, Switch, SWP, Other | 08_investor_transactions.csv |
| amount | REAL | Transaction value in ₹. Must be > 0 | 08_investor_transactions.csv |
| units | REAL | Number of fund units bought or redeemed | 08_investor_transactions.csv |
| nav_at_transaction | REAL | The NAV of the fund on the day of the transaction | 08_investor_transactions.csv |
| state | TEXT | Indian state where the investor is registered | 08_investor_transactions.csv |
| kyc_status | TEXT | Whether the investor completed KYC verification (YES / NO / PENDING) | 08_investor_transactions.csv |

---

## fact_performance

Periodic performance snapshot for each fund scheme.

| Column | Type | Definition | Source |
|---|---|---|---|
| id | INTEGER (PK) | Auto-generated row ID | System |
| amfi_code | INTEGER (FK) | Which fund this performance row is for | 07_scheme_performance.csv |
| as_of_date | TEXT | The date as of which these returns were calculated | 07_scheme_performance.csv |
| return_1y | REAL | Absolute return over the last 1 year (%) | 07_scheme_performance.csv |
| return_3y | REAL | CAGR over the last 3 years (%) | 07_scheme_performance.csv |
| return_5y | REAL | CAGR over the last 5 years (%) | 07_scheme_performance.csv |
| return_ytd | REAL | Return from Jan 1 of the current year to as_of_date (%) | 07_scheme_performance.csv |
| expense_ratio | REAL | Total Expense Ratio — annual fee charged by the fund as % of AUM. Valid range: 0.1% to 2.5% | 07_scheme_performance.csv |
| sharpe_ratio | REAL | Return earned per unit of risk taken. Higher is better | 07_scheme_performance.csv |
| alpha | REAL | Extra return generated above the benchmark. Positive alpha = fund outperformed | 07_scheme_performance.csv |
| beta | REAL | How much the fund moves relative to the market. Beta > 1 = more volatile than market | 07_scheme_performance.csv |

---

## fact_aum

Monthly AUM (Assets Under Management) reported by each fund house.

| Column | Type | Definition | Source |
|---|---|---|---|
| id | INTEGER (PK) | Auto-generated row ID | System |
| fund_house | TEXT | Name of the AMC | 03_aum_by_fund_house.csv |
| month | TEXT | Reporting month in YYYY-MM format | 03_aum_by_fund_house.csv |
| aum_crore | REAL | Total assets managed by the fund house in that month, in ₹ crore | 03_aum_by_fund_house.csv |
| scheme_count | INTEGER | Number of active schemes run by this fund house that month | 03_aum_by_fund_house.csv |

---

## Supporting Tables

These were loaded as-is from cleaned CSVs — column definitions follow the source file headers.

| Table | Source File | Description |
|---|---|---|
| sip_inflows | 04_monthly_sip_inflows.csv | Month-wise total SIP inflow amounts across the industry |
| category_inflows | 05_category_inflows.csv | Net inflows into each fund category per month |
| folio_count | 06_industry_folio_count.csv | Total number of investor folios (accounts) over time |
| portfolio_holdings | 09_portfolio_holdings.csv | Stock/bond level holdings of each fund scheme |
| benchmark_indices | 10_benchmark_indices.csv | Daily closing values of market indices (Nifty, Sensex etc.) |

---

## Data Cleaning Notes

| Dataset | What was cleaned |
|---|---|
| nav_history | Dates parsed to datetime, sorted by fund + date, forward-filled for holidays/weekends, duplicates removed, rows with NAV ≤ 0 dropped |
| investor_transactions | transaction_type standardised to SIP/Lumpsum/Redemption/Switch/SWP, amount ≤ 0 dropped, dates fixed, KYC values normalised |
| scheme_performance | Return columns coerced to numeric, values outside -100% to +200% set to NaN, expense_ratio outside 0.1–2.5% set to NaN |
| All other files | Dates parsed, string whitespace stripped, duplicate and fully empty rows removed |

---

*Last updated: Day 2*
*Project: Mutual Fund Analysis Dashboard — Bluestock Fintech Internship*
*Author: Likhitha VK*
