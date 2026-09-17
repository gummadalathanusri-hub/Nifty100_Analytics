import sqlite3
import pandas as pd
import numpy as np

conn = sqlite3.connect("nifty100.db")

sectors = pd.read_sql_query(
    "SELECT DISTINCT company_id, broad_sector FROM sectors",
    conn
)

ids = sectors["company_id"].tolist()

cf = pd.read_sql_query(
    """
    SELECT company_id, year,
           operating_activity,
           investing_activity,
           financing_activity,
           net_cash_flow
    FROM cashflow
    """,
    conn
)

pnl = pd.read_sql_query(
    """
    SELECT company_id, year,
           sales,
           operating_profit,
           net_profit
    FROM profitandloss
    """,
    conn
)

bs = pd.read_sql_query(
    """
    SELECT company_id, year, borrowings
    FROM balancesheet
    """,
    conn
)

conn.close()

cf = cf[cf["company_id"].isin(ids)].copy()
pnl = pnl[pnl["company_id"].isin(ids)].copy()
bs = bs[bs["company_id"].isin(ids)].copy()

cf["fcf"] = (
    cf["operating_activity"] +
    cf["investing_activity"]
)

results = []
distress = []
deleveraging = []

for company_id in ids:

    company_cf = (
        cf[cf["company_id"] == company_id]
        .sort_values("year")
    )

    company_pnl = (
        pnl[pnl["company_id"] == company_id]
        .sort_values("year")
    )

    company_bs = (
        bs[bs["company_id"] == company_id]
        .sort_values("year")
    )

    latest_cf = company_cf[
        company_cf["year"] == 2024
    ]

    latest_pnl = company_pnl[
        company_pnl["year"] == 2024
    ]

    if latest_cf.empty or latest_pnl.empty:
        continue

    latest_cf = latest_cf.iloc[-1]
    latest_pnl = latest_pnl.iloc[-1]

    five_year_cf = company_cf[
        company_cf["year"].between(2020, 2024)
    ]

    five_year_pnl = company_pnl[
        company_pnl["year"].between(2020, 2024)
    ]

    merged = five_year_cf.merge(
        five_year_pnl[
            ["year", "net_profit"]
        ],
        on="year",
        how="inner"
    )

    merged = merged[
        merged["net_profit"].notna()
        & merged["net_profit"].ne(0)
        & merged["operating_activity"].notna()
    ]

    cfo_ratios = (
        merged["operating_activity"]
        / merged["net_profit"]
    )

    cfo_score = (
        cfo_ratios.mean()
        if not cfo_ratios.empty
        else np.nan
    )

    sales = latest_pnl["sales"]
    cfi = latest_cf["investing_activity"]

    if (
        pd.notna(cfi)
        and pd.notna(sales)
        and sales != 0
    ):
        capex_intensity = abs(cfi) / sales * 100
    else:
        capex_intensity = np.nan

    distress_flag = (
        pd.notna(latest_cf["operating_activity"])
        and pd.notna(latest_cf["financing_activity"])
        and latest_cf["operating_activity"] < 0
        and latest_cf["financing_activity"] > 0
    )

    company_bs_2024 = company_bs[
        company_bs["year"] == 2024
    ]

    company_bs_2023 = company_bs[
        company_bs["year"] == 2023
    ]

    deleveraging_flag = False

    if (
        latest_cf["financing_activity"] < 0
        and not company_bs_2024.empty
        and not company_bs_2023.empty
    ):

        debt_2024 = company_bs_2024.iloc[-1]["borrowings"]
        debt_2023 = company_bs_2023.iloc[-1]["borrowings"]

        if pd.notna(debt_2024) and pd.notna(debt_2023):
            deleveraging_flag = debt_2024 < debt_2023

    results.append(
        {
            "company_id": company_id,
            "cfo_quality_score": cfo_score,
            "capex_intensity_pct": capex_intensity,
            "distress_flag": distress_flag,
            "deleveraging_flag": deleveraging_flag
        }
    )

    if distress_flag:
        distress.append(company_id)

    if deleveraging_flag:
        deleveraging.append(company_id)

result_df = pd.DataFrame(results)

print()
print("DAY 31 BENCHMARK")
print("=" * 50)

print()
print("Companies benchmarked:", len(result_df))

print()
print("CFO Quality Score:")
print(
    result_df["cfo_quality_score"]
    .describe()
    .to_string()
)

print()
print("CapEx Intensity:")
print(
    result_df["capex_intensity_pct"]
    .describe()
    .to_string()
)

print()
print("Distress flags:", len(distress))
print(distress)

print()
print("Deleveraging flags:", len(deleveraging))
print(deleveraging)

print()
print("Missing CFO Quality:",
      result_df["cfo_quality_score"].isna().sum())

print("Missing CapEx Intensity:",
      result_df["capex_intensity_pct"].isna().sum())