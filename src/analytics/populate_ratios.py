from pathlib import Path
import sqlite3

import pandas as pd

from src.analytics.ratios import (
    net_profit_margin,
    operating_profit_margin,
    return_on_equity,
    return_on_capital_employed,
    debt_to_equity,
    high_leverage_flag,
    interest_coverage_ratio,
    icr_label,
    icr_warning_flag,
    asset_turnover,
)

from src.analytics.cagr import calculate_metric_cagrs


ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "nifty100.db"


def safe_number(value):
    if pd.isna(value):
        return 0.0
    return float(value)


def main():

    con = sqlite3.connect(DB_PATH)

    pnl = pd.read_sql(
        "SELECT * FROM profitandloss",
        con,
    )

    bs = pd.read_sql(
        "SELECT * FROM balancesheet",
        con,
    )

    cf = pd.read_sql(
        "SELECT * FROM cashflow",
        con,
    )

    companies = pd.read_sql(
        "SELECT * FROM companies",
        con,
    )

    sectors = pd.read_sql(
        "SELECT * FROM sectors",
        con,
    )

    pnl["year"] = pd.to_numeric(
        pnl["year"],
        errors="coerce",
    )

    bs["year"] = pd.to_numeric(
        bs["year"],
        errors="coerce",
    )

    cf["year"] = pd.to_numeric(
        cf["year"],
        errors="coerce",
    )

    # Remove duplicate company-year rows
    pnl = pnl.drop_duplicates(
        subset=["company_id", "year"]
    )

    bs = bs.drop_duplicates(
        subset=["company_id", "year"]
    )

    cf = cf.drop_duplicates(
        subset=["company_id", "year"]
    )

    revenue_cagr = calculate_metric_cagrs(
        pnl,
        "sales",
    )

    pat_cagr = calculate_metric_cagrs(
        pnl,
        "net_profit",
    )

    eps_cagr = calculate_metric_cagrs(
        pnl,
        "eps",
    )

    revenue_cagr = revenue_cagr[
        [
            "company_id",
            "year",
            "sales_cagr_5yr",
            "sales_cagr_5yr_flag",
        ]
    ].rename(
        columns={
            "sales_cagr_5yr": "revenue_cagr_5yr",
            "sales_cagr_5yr_flag": "revenue_cagr_5yr_flag",
        }
    )

    pat_cagr = pat_cagr[
        [
            "company_id",
            "year",
            "net_profit_cagr_5yr",
            "net_profit_cagr_5yr_flag",
        ]
    ].rename(
        columns={
            "net_profit_cagr_5yr": "pat_cagr_5yr",
            "net_profit_cagr_5yr_flag": "pat_cagr_5yr_flag",
        }
    )

    eps_cagr = eps_cagr[
        [
            "company_id",
            "year",
            "eps_cagr_5yr",
            "eps_cagr_5yr_flag",
        ]
    ]


    base = pnl[
        [
            "company_id",
            "year",
            "sales",
            "operating_profit",
            "opm_percentage",
            "other_income",
            "interest",
            "net_profit",
            "eps",
            "dividend_payout",
        ]
    ].copy()

    base = base.merge(
        bs[
            [
                "company_id",
                "year",
                "equity_capital",
                "reserves",
                "borrowings",
                "investments",
                "total_assets",
            ]
        ],
        on=["company_id", "year"],
        how="left",
    )

    base = base.merge(
        cf[
            [
                "company_id",
                "year",
                "operating_activity",
                "investing_activity",
            ]
        ],
        on=["company_id", "year"],
        how="left",
    )

    base = base.merge(
        sectors,
        on="company_id",
        how="left",
    )

    base = base.merge(
        revenue_cagr,
        on=["company_id", "year"],
        how="left",
    )

    base = base.merge(
        pat_cagr,
        on=["company_id", "year"],
        how="left",
    )

    base = base.merge(
        eps_cagr,
        on=["company_id", "year"],
        how="left",
    )

    results = []

    for _, row in base.iterrows():

        sales = safe_number(row["sales"])
        net_profit = safe_number(row["net_profit"])
        operating_profit = safe_number(
            row["operating_profit"]
        )
        other_income = safe_number(
            row["other_income"]
        )
        interest = safe_number(row["interest"])

        equity_capital = safe_number(
            row["equity_capital"]
        )
        reserves = safe_number(row["reserves"])
        borrowings = safe_number(row["borrowings"])
        investments = safe_number(row["investments"])
        total_assets = safe_number(
            row["total_assets"]
        )

        operating_activity = safe_number(
            row["operating_activity"]
        )
        investing_activity = safe_number(
            row["investing_activity"]
        )

        # Profitability
        npm = net_profit_margin(
            net_profit,
            sales,
        )

        opm = operating_profit_margin(
            operating_profit,
            sales,
        )

        roe = return_on_equity(
            net_profit,
            equity_capital,
            reserves,
        )

        roce = return_on_capital_employed(
            operating_profit,
            equity_capital,
            reserves,
            borrowings,
        )

        # Leverage
        de = debt_to_equity(
            borrowings,
            equity_capital,
            reserves,
        )

        leverage_flag = high_leverage_flag(
            de,
            row["broad_sector"],
        )

        icr = interest_coverage_ratio(
            operating_profit,
            other_income,
            interest,
        )

        label = icr_label(icr)

        warning = icr_warning_flag(icr)
                                   
        turnover = asset_turnover(
            sales,
            total_assets,
        )

        fcf = (
            operating_activity
            + investing_activity
        )
        
        if pd.isna(row["year"]):
            continue

        results.append(
            {
                "company_id": row["company_id"],
                "year": int(row["year"]),

                "net_profit_margin_pct": npm,
                "operating_profit_margin_pct": opm,
                "return_on_equity_pct": roe,
                "debt_to_equity": de,
                "interest_coverage": icr,
                "asset_turnover": turnover,

                "free_cash_flow_cr": fcf,
                "capex_cr": abs(investing_activity),

                "earnings_per_share": row["eps"],

                "book_value_per_share": (
                    equity_capital + reserves
                ),

                "dividend_payout_ratio_pct": (
                    row["dividend_payout"]
                ),

                "total_debt_cr": borrowings,

                "cash_from_operations_cr": (
                    operating_activity
                ),

                "revenue_cagr_5yr": (
                    row["revenue_cagr_5yr"]
                ),

                "revenue_cagr_5yr_flag": (
                    row["revenue_cagr_5yr_flag"]
                ),

                "pat_cagr_5yr": (
                    row["pat_cagr_5yr"]
                ),

                "pat_cagr_5yr_flag": (
                    row["pat_cagr_5yr_flag"]
                ),

                "eps_cagr_5yr": (
                    row["eps_cagr_5yr"]
                ),

                "eps_cagr_5yr_flag": (
                    row["eps_cagr_5yr_flag"]
                ),

                "high_leverage_flag": int(
                    leverage_flag
                ),

                "icr_label": label,

                "icr_warning_flag": int(
                    warning
                ),
            }
        )

    result_df = pd.DataFrame(results)

    score_columns = [
        "net_profit_margin_pct",
        "operating_profit_margin_pct",
        "return_on_equity_pct",
        "debt_to_equity",
        "interest_coverage",
        "asset_turnover",
    ]

    result_df["composite_quality_score"] = (
        result_df[score_columns]
        .rank(pct=True)
        .mean(axis=1)
        * 100
    )

    con.execute(
        "DELETE FROM financial_ratios"
    )

    result_df.to_sql(
        "financial_ratios",
        con,
        if_exists="append",
        index=False,
    )

    con.commit()

    print(
        "financial_ratios populated successfully."
    )

    print(
        "Rows:",
        con.execute(
            "SELECT COUNT(*) FROM financial_ratios"
        ).fetchone()[0],
    )

    print(
        "Companies:",
        con.execute(
            "SELECT COUNT(DISTINCT company_id) "
            "FROM financial_ratios"
        ).fetchone()[0],
    )

    con.close()


if __name__ == "__main__":
    main()