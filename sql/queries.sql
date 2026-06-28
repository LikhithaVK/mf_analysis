-- ============================================================
-- queries.sql
-- Bluestock MF Analysis — 10 Analytical SQL Queries
-- Database: bluestock_mf.db
-- ============================================================


-- ── QUERY 1: Top 5 Fund Houses by Total AUM ───────────────
-- Shows which AMCs manage the most money
SELECT
    fund_house,
    ROUND(SUM(aum_crore), 2)        AS total_aum_crore,
    COUNT(DISTINCT month)           AS months_reported
FROM fact_aum
GROUP BY fund_house
ORDER BY total_aum_crore DESC
LIMIT 5;


-- ── QUERY 2: Average NAV Per Month (across all funds) ─────
-- Useful for spotting market-wide NAV trends
SELECT
    d.year,
    d.month,
    d.month_name,
    ROUND(AVG(n.nav), 2)            AS avg_nav
FROM fact_nav n
JOIN dim_date d ON n.date_id = d.date_id
GROUP BY d.year, d.month
ORDER BY d.year, d.month;


-- ── QUERY 3: SIP Inflows Year-on-Year Growth ──────────────
-- Compares total SIP amounts year over year
SELECT
    strftime('%Y', transaction_date)        AS year,
    ROUND(SUM(amount), 2)                   AS total_sip_amount,
    COUNT(*)                                AS total_sip_transactions
FROM fact_transactions
WHERE transaction_type = 'SIP'
GROUP BY year
ORDER BY year;


-- ── QUERY 4: Transactions by State ────────────────────────
-- Geographic distribution of investor activity
SELECT
    state,
    COUNT(*)                        AS total_transactions,
    ROUND(SUM(amount), 2)           AS total_amount,
    COUNT(DISTINCT investor_id)     AS unique_investors
FROM fact_transactions
GROUP BY state
ORDER BY total_transactions DESC;


-- ── QUERY 5: Funds with Expense Ratio Below 1% ────────────
-- Cost-efficient funds — good for investor recommendations
SELECT
    f.scheme_name,
    f.fund_house,
    f.category,
    p.expense_ratio
FROM fact_performance p
JOIN dim_fund f ON p.amfi_code = f.amfi_code
WHERE p.expense_ratio < 1.0
  AND p.expense_ratio IS NOT NULL
ORDER BY p.expense_ratio ASC;


-- ── QUERY 6: Top 10 Funds by 3-Year Returns ───────────────
-- Best performing funds over a medium-term horizon
SELECT
    f.scheme_name,
    f.fund_house,
    f.sub_category,
    ROUND(p.return_3y, 2)           AS return_3y_pct
FROM fact_performance p
JOIN dim_fund f ON p.amfi_code = f.amfi_code
WHERE p.return_3y IS NOT NULL
ORDER BY p.return_3y DESC
LIMIT 10;


-- ── QUERY 7: Monthly Redemption vs Purchase Ratio ─────────
-- Tracks investor sentiment — high redemptions = panic selling
SELECT
    strftime('%Y-%m', transaction_date)     AS month,
    ROUND(SUM(CASE WHEN transaction_type IN ('SIP','Lumpsum') THEN amount ELSE 0 END), 2)  AS total_purchased,
    ROUND(SUM(CASE WHEN transaction_type = 'Redemption'       THEN amount ELSE 0 END), 2)  AS total_redeemed,
    ROUND(
        SUM(CASE WHEN transaction_type = 'Redemption' THEN amount ELSE 0 END) * 100.0 /
        NULLIF(SUM(CASE WHEN transaction_type IN ('SIP','Lumpsum') THEN amount ELSE 0 END), 0)
    , 2)                                    AS redemption_ratio_pct
FROM fact_transactions
GROUP BY month
ORDER BY month;


-- ── QUERY 8: NAV Growth of a Specific Fund (HDFC Top 100) ─
-- Year-end NAV to track long-term growth
SELECT
    d.year,
    ROUND(AVG(n.nav), 4)            AS avg_nav_for_year,
    MIN(n.nav)                      AS min_nav,
    MAX(n.nav)                      AS max_nav
FROM fact_nav n
JOIN dim_date d   ON n.date_id   = d.date_id
JOIN dim_fund f   ON n.amfi_code = f.amfi_code
WHERE f.amfi_code = 125497          -- HDFC Top 100 Direct
GROUP BY d.year
ORDER BY d.year;


-- ── QUERY 9: Funds by Risk Grade Distribution ─────────────
-- Understand how the universe is spread across risk levels
SELECT
    f.risk_grade,
    COUNT(DISTINCT f.amfi_code)     AS scheme_count,
    ROUND(AVG(p.return_1y), 2)      AS avg_1y_return,
    ROUND(AVG(p.expense_ratio), 3)  AS avg_expense_ratio
FROM dim_fund f
LEFT JOIN fact_performance p ON f.amfi_code = p.amfi_code
GROUP BY f.risk_grade
ORDER BY scheme_count DESC;


-- ── QUERY 10: KYC Compliance by Transaction Type ──────────
-- Flags non-KYC transactions — compliance/risk check
SELECT
    transaction_type,
    kyc_status,
    COUNT(*)                        AS transaction_count,
    ROUND(SUM(amount), 2)           AS total_amount
FROM fact_transactions
GROUP BY transaction_type, kyc_status
ORDER BY transaction_type, kyc_status;
