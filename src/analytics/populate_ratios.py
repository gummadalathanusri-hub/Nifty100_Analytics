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
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def normalize_pnl_years(pnl):
    pnl = pnl.copy()

    pnl["year_raw"] = (
        pnl["year"]
        .astype(str)
        .str.strip()
    )

    pnl["year"] = (
        pnl["year_raw"]
        .str.extract(
            r"(19\d{2}|20\d{2})",
            expand=False,
        )
    )

    pnl.loc[
        pnl["year_raw"].str.upper().eq("TTM"),
        "year"
    ] = "2024"

    pnl["year"] = pd.to_numeric(
        pnl["year"],
        errors="coerce",
    )

    pnl = pnl.dropna(
        subset=["company_id", "year"]
    ).copy()

    pnl["year"] = pnl["year"].astype(int)

    pnl["_is_ttm"] = (
        pnl["year_raw"]
        .str.upper()
        .eq("TTM")
        .astype(int)
    )

    pnl = (
        pnl.sort_values(
            [
                "company_id",
                "year",
                "_is_ttm",
            ]
        )
        .drop_duplicates(
            subset=[
                "company_id",
                "year",
            ],
            keep="last",
        )
        .drop(
            columns=[
                "year_raw",
                "_is_ttm",
            ]
        )
        .reset_index(drop=True)
    )

    return pnl


def normalize_statement_years(df):
    df = df.copy()

    df["year"] = (
        df["year"]
        .astype(str)
        .str.extract(
            r"(19\d{2}|20\d{2})",
            expand=False,
        )
    )

    df["year"] = pd.to_numeric(
        df["year"],
        errors="coerce",
    )

    df = df.dropna(
        subset=[
            "company_id",
            "year",
        ]
    ).copy()

    df["year"] = df["year"].astype(int)

    df = (
        df.drop_duplicates(
            subset=[
                "company_id",
                "year",
            ],
            keep="last",
        )
        .reset_index(drop=True)
    )

    return df


def calculate_cagr_table(pnl, metric):
    result = calculate_metric_cagrs(
        pnl,
        metric,
    )

    return result[
        [
            "company_id",
            "year",
            f"{metric}_cagr_5yr",
            f"{metric}_cagr_5yr_flag",
        ]
    ].copy()


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

    sectors = pd.read_sql(
        "SELECT * FROM sectors",
        con,
    )

    print("P&L rows:", len(pnl))
    print("BS rows:", len(bs))
    print("CF rows:", len(cf))
    print("Sectors rows:", len(sectors))

    pnl = normalize_pnl_years(pnl)
    bs = normalize_statement_years(bs)
    cf = normalize_statement_years(cf)

    print(
        "P&L NULL years after conversion:",
        pnl["year"].isna().sum(),
    )

    print(
        "P&L after dedup:",
        len(pnl),
    )

    print(
        "BS after dedup:",
        len(bs),
    )

    print(
        "CF after dedup:",
        len(cf),
    )

    revenue_cagr = calculate_cagr_table(
        pnl,
        "sales",
    )

    revenue_cagr = revenue_cagr.rename(
        columns={
            "sales_cagr_5yr": "revenue_cagr_5yr",
            "sales_cagr_5yr_flag": "revenue_cagr_5yr_flag",
        }
    )

    pat_cagr = calculate_cagr_table(
        pnl,
        "net_profit",
    )

    pat_cagr = pat_cagr.rename(
        columns={
            "net_profit_cagr_5yr": "pat_cagr_5yr",
            "net_profit_cagr_5yr_flag": "pat_cagr_5yr_flag",
        }
    )

    eps_cagr = calculate_cagr_table(
        pnl,
        "eps",
    )

    print(
        "Revenue CAGR:",
        len(revenue_cagr),
        "unique company-year:",
        revenue_cagr[
            ["company_id", "year"]
        ].drop_duplicates().shape[0],
    )

    print(
        "PAT CAGR:",
        len(pat_cagr),
        "unique company-year:",
        pat_cagr[
            ["company_id", "year"]
        ].drop_duplicates().shape[0],
    )

    print(
        "EPS CAGR:",
        len(eps_cagr),
        "unique company-year:",
        eps_cagr[
            ["company_id", "year"]
        ].drop_duplicates().shape[0],
    )

    base_columns = [
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

    base = pnl[
        [
            column
            for column in base_columns
            if column in pnl.columns
        ]
    ].copy()

    base = base.merge(
        bs[
            [
                column
                for column in [
                    "company_id",
                    "year",
                    "equity_capital",
                    "reserves",
                    "borrowings",
                    "investments",
                    "total_assets",
                ]
                if column in bs.columns
            ]
        ],
        on=[
            "company_id",
            "year",
        ],
        how="left",
    )

    print(
        "After BS merge:",
        len(base),
    )

    base = base.merge(
        cf[
            [
                column
                for column in [
                    "company_id",
                    "year",
                    "operating_activity",
                    "investing_activity",
                ]
                if column in cf.columns
            ]
        ],
        on=[
            "company_id",
            "year",
        ],
        how="left",
    )

    print(
        "After CF merge:",
        len(base),
    )

    sectors = (
        sectors
        .drop_duplicates(
            subset=["company_id"],
            keep="last",
        )
        .copy()
    )

    base = base.merge(
        sectors,
        on="company_id",
        how="left",
    )

    print(
        "After sectors merge:",
        len(base),
    )

    base = base.merge(
        revenue_cagr,
        on=[
            "company_id",
            "year",
        ],
        how="left",
    )

    base = base.merge(
        pat_cagr,
        on=[
            "company_id",
            "year",
        ],
        how="left",
    )

    base = base.merge(
        eps_cagr,
        on=[
            "company_id",
            "year",
        ],
        how="left",
    )

    print(
        "BASE ROWS:",
        len(base),
    )

    print(
        "BASE DUPLICATES:",
        base.duplicated(
            [
                "company_id",
                "year",
            ]
        ).sum(),
    )

    print(
        "BASE UNIQUE COMPANY-YEAR:",
        base[
            [
                "company_id",
                "year",
            ]
        ].drop_duplicates().shape[0],
    )

    results = []

    for _, row in base.iterrows():

        sales = safe_number(
            row.get("sales")
        )

        net_profit = safe_number(
            row.get("net_profit")
        )

        operating_profit = safe_number(
            row.get("operating_profit")
        )

        other_income = safe_number(
            row.get("other_income")
        )

        interest = safe_number(
            row.get("interest")
        )

        equity_capital = safe_number(
            row.get("equity_capital")
        )

        reserves = safe_number(
            row.get("reserves")
        )

        borrowings = safe_number(
            row.get("borrowings")
        )

        total_assets = safe_number(
            row.get("total_assets")
        )

        operating_activity = safe_number(
            row.get("operating_activity")
        )

        investing_activity = safe_number(
            row.get("investing_activity")
        )

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

        de = debt_to_equity(
            borrowings,
            equity_capital,
            reserves,
        )

        sector_value = row.get(
            "broad_sector",
            None,
        )

        leverage_flag = high_leverage_flag(
            de,
            sector_value,
        )

        icr = interest_coverage_ratio(
            operating_profit,
            other_income,
            interest,
        )

        label = icr_label(
            icr
        )

        warning = icr_warning_flag(
            icr
        )

        turnover = asset_turnover(
            sales,
            total_assets,
        )

        fcf = (
            operating_activity
            + investing_activity
        )

        result = {
            "company_id": row["company_id"],
            "year": int(row["year"]),
            "net_profit_margin_pct": npm,
            "operating_profit_margin_pct": opm,
            "return_on_equity_pct": roe,
            "debt_to_equity": de,
            "interest_coverage": icr,
            "asset_turnover": turnover,
            "free_cash_flow_cr": fcf,
            "capex_cr": abs(
                investing_activity
            ),
            "earnings_per_share": row.get(
                "eps"
            ),
            "book_value_per_share": (
                equity_capital
                + reserves
            ),
            "dividend_payout_ratio_pct": row.get(
                "dividend_payout"
            ),
            "total_debt_cr": borrowings,
            "cash_from_operations_cr": (
                operating_activity
            ),
            "revenue_cagr_5yr": row.get(
                "revenue_cagr_5yr"
            ),
            "revenue_cagr_5yr_flag": row.get(
                "revenue_cagr_5yr_flag"
            ),
            "pat_cagr_5yr": row.get(
                "net_profit_cagr_5yr"
            )
            if "net_profit_cagr_5yr" in row.index
            else row.get("pat_cagr_5yr"),
            "pat_cagr_5yr_flag": row.get(
                "net_profit_cagr_5yr_flag"
            )
            if "net_profit_cagr_5yr_flag" in row.index
            else row.get("pat_cagr_5yr_flag"),
            "eps_cagr_5yr": row.get(
                "eps_cagr_5yr"
            ),
            "eps_cagr_5yr_flag": row.get(
                "eps_cagr_5yr_flag"
            ),
            "high_leverage_flag": int(
                leverage_flag
            ),
            "icr_label": label,
            "icr_warning_flag": int(
                warning
            ),
        }

        result["return_on_capital_employed_pct"] = roce

        results.append(result)

    print(
        "RESULTS LIST LENGTH:",
        len(results),
    )

    result_df = pd.DataFrame(
        results
    )

    result_df = result_df.drop_duplicates(
        subset=[
            "company_id",
            "year",
        ],
        keep="last",
    ).reset_index(drop=True)

    score_columns = [
        "net_profit_margin_pct",
        "operating_profit_margin_pct",
        "return_on_equity_pct",
        "debt_to_equity",
        "interest_coverage",
        "asset_turnover",
    ]

    available_score_columns = [
        column
        for column in score_columns
        if column in result_df.columns
    ]

    score_data = result_df[
        available_score_columns
    ].copy()

    score_data = score_data.apply(
        pd.to_numeric,
        errors="coerce",
    )

    ranks = score_data.rank(
        pct=True,
        na_option="keep",
    )

    result_df[
        "composite_quality_score"
    ] = (
        ranks.mean(
            axis=1,
            skipna=True,
        )
        * 100
    )

    result_df[
        "composite_quality_score"
    ] = result_df[
        "composite_quality_score"
    ].fillna(0)

    table_columns = [
        row[1]
        for row in con.execute(
            "PRAGMA table_info(financial_ratios)"
        ).fetchall()
    ]

    result_df = result_df[
        [
            column
            for column in table_columns
            if column in result_df.columns
        ]
    ]

    con.execute(
        "DELETE FROM financial_ratios"
    )

    con.commit()

    result_df.to_sql(
        "financial_ratios",
        con,
        if_exists="append",
        index=False,
    )

    con.commit()

    rows = con.execute(
        "SELECT COUNT(*) FROM financial_ratios"
    ).fetchone()[0]

    companies = con.execute(
        """
        SELECT COUNT(DISTINCT company_id)
        FROM financial_ratios
        """
    ).fetchone()[0]

    unique_company_year = con.execute(
        """
        SELECT COUNT(*)
        FROM (
            SELECT DISTINCT company_id, year
            FROM financial_ratios
        )
        """
    ).fetchone()[0]

    print(
        "financial_ratios populated successfully."
    )

    print(
        "Rows:",
        rows,
    )

    print(
        "Unique company-year:",
        unique_company_year,
    )

    print(
        "Companies:",
        companies,
    )

    con.close()


if __name__ == "__main__":
    main()