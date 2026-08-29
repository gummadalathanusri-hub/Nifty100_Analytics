import sqlite3

con = sqlite3.connect("nifty100.db")

query1 = """
SELECT COUNT(*)
FROM financial_ratios r
JOIN sectors s ON r.company_id = s.company_id
WHERE s.broad_sector = 'Financials'
AND r.debt_to_equity > 5
"""

query2 = """
SELECT COUNT(*)
FROM financial_ratios r
JOIN sectors s ON r.company_id = s.company_id
WHERE s.broad_sector = 'Financials'
AND r.debt_to_equity > 5
AND r.high_leverage_flag = 1
"""

print("Financials with D/E > 5:", con.execute(query1).fetchone()[0])
print("Financials incorrectly flagged:", con.execute(query2).fetchone()[0])

con.close()