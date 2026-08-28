SELECT COUNT(*) AS total_companies
FROM companies;


SELECT
    id,
    company_name,
    website
FROM companies
ORDER BY company_name;


SELECT
    s.broad_sector,
    COUNT(*) AS company_count
FROM sectors s
GROUP BY s.broad_sector
ORDER BY company_count DESC;


SELECT
    m.company_id,
    c.company_name,
    m.year,
    m.market_cap_crore
FROM market_cap m
JOIN companies c
    ON m.company_id = c.id
ORDER BY m.market_cap_crore DESC
LIMIT 10;


SELECT
    company_id,
    date,
    close_price
FROM stock_prices
WHERE company_id = 'TCS'
ORDER BY date;


SELECT
    s.broad_sector,
    ROUND(AVG(m.market_cap_crore), 2) AS avg_market_cap_crore
FROM market_cap m
JOIN sectors s
    ON m.company_id = s.company_id
GROUP BY s.broad_sector
ORDER BY avg_market_cap_crore DESC;


SELECT
    company_id,
    COUNT(DISTINCT year) AS years_available,
    MIN(year) AS first_year,
    MAX(year) AS last_year
FROM profitandloss
WHERE year IS NOT NULL
GROUP BY company_id
ORDER BY years_available DESC;


SELECT
    company_id,
    COUNT(DISTINCT year) AS years_available
FROM profitandloss
WHERE year IS NOT NULL
GROUP BY company_id
HAVING COUNT(DISTINCT year) < 5
ORDER BY years_available;


SELECT
    company_id,
    year,
    earnings_per_share
FROM financial_ratios
WHERE earnings_per_share < 0
ORDER BY company_id, year;


PRAGMA foreign_key_check;