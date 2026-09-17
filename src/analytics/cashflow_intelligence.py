from __future__ import annotations

import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd

from src.analytics.cashflow_kpis import (
    free_cash_flow,
    cfo_quality_score,
    cfo_quality_label,
    capex_intensity,
    capex_intensity_label,
    fcf_conversion_rate,
    capital_allocation_pattern,
)


ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "nifty100.db"
OUTPUT_DIR = ROOT / "output"

INTELLIGENCE_PATH = OUTPUT_DIR / "cashflow_intelligence.xlsx"
DISTRESS_PATH = OUTPUT_DIR / "distress_alerts.csv"


def calculate_fcf_cagr(company_cf: pd.DataFrame) -> float | None:
    data = company_cf[
        company_cf["year"].between(2020, 2024)
    ].copy()

    data = data.dropna(subset=["fcf"])

    if len(data) < 2:
        return None

    data = data.sort_values("year")

    start_fcf = data.iloc[0]["fcf"]
    end_fcf = data.iloc[-1]["fcf"]

    if start_fcf == 0:
        return None

    if start_fcf > 0 and end_fcf > 0:
        years = data.iloc[-1]["year"] - data.iloc[0]["year"]

        if years <= 0:
            return None

        return ((end_fcf / start_fcf) ** (1 / years) - 1) * 100

    return None


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)

    sectors = pd.read_sql_query(
        """
        SELECT DISTINCT company_id, broad_sector
        FROM sectors
        """,
        conn,
    )

    cashflow = pd.read_sql_query(
        """
        SELECT
            company_id,
            year,
            operating_activity,
            investing_activity,
            financing_activity,
            net_cash_flow
        FROM cashflow
        """,
        conn,
    )

    pnl = pd.read_sql_query(
        """
        SELECT
            company_id,
            year,
            sales,
            operating_profit,
            net_profit
        FROM profitandloss
        """,
        conn,
    )

    balancesheet = pd.read_sql_query(
        """
        SELECT
            company_id,
            year,
            borrowings
        FROM balancesheet
        """,
        conn,
    )

    conn.close()

    target_ids = sectors["company_id"].tolist()

    cashflow = cashflow[
        cashflow["company_id"].isin(target_ids)
    ].copy()

    pnl = pnl[
        pnl["company_id"].isin(target_ids)
    ].copy()

    balancesheet = balancesheet[
        balancesheet["company_id"].isin(target_ids)
    ].copy()

    for df in [cashflow, pnl, balancesheet]:
        df["year"] = pd.to_numeric(
            df["year"],
            errors="coerce",
        )

    cashflow["fcf"] = cashflow.apply(
        lambda row: free_cash_flow(
            row["operating_activity"],
            row["investing_activity"],
        ),
        axis=1,
    )

    sector_map = sectors.set_index(
        "company_id"
    )["broad_sector"].to_dict()

    results = []
    distress_rows = []

    for company_id in target_ids:

        company_cf = (
            cashflow[
                cashflow["company_id"] == company_id
            ]
            .sort_values("year")
            .copy()
        )

        company_pnl = (
            pnl[
                pnl["company_id"] == company_id
            ]
            .sort_values("year")
            .copy()
        )

        company_bs = (
            balancesheet[
                balancesheet["company_id"] == company_id
            ]
            .sort_values("year")
            .copy()
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
            how="inner",
        )

        cfo_ratios = []

        for _, row in merged.iterrows():
            ratio = cfo_quality_score(
                row["operating_activity"],
                row["net_profit"],
            )

            if ratio is not None and np.isfinite(ratio):
                cfo_ratios.append(ratio)

        if cfo_ratios:
            cfo_score = float(np.mean(cfo_ratios))
        else:
            cfo_score = None

        cfo_label = cfo_quality_label(
            cfo_score
        )

        capex_value = capex_intensity(
            latest_cf["investing_activity"],
            latest_pnl["sales"],
        )

        capex_label = capex_intensity_label(
            capex_value
        )

        fcf_cagr = calculate_fcf_cagr(
            company_cf
        )

        latest_fcf = free_cash_flow(
            latest_cf["operating_activity"],
            latest_cf["investing_activity"],
        )

        fcf_conversion = fcf_conversion_rate(
            latest_fcf,
            latest_pnl["operating_profit"],
        )

        distress_flag = (
            pd.notna(
                latest_cf["operating_activity"]
            )
            and pd.notna(
                latest_cf["financing_activity"]
            )
            and latest_cf["operating_activity"] < 0
            and latest_cf["financing_activity"] > 0
        )

        deleveraging_flag = False

        bs_2024 = company_bs[
            company_bs["year"] == 2024
        ]

        bs_2023 = company_bs[
            company_bs["year"] == 2023
        ]

        if (
            latest_cf["financing_activity"] < 0
            and not bs_2024.empty
            and not bs_2023.empty
        ):
            debt_2024 = bs_2024.iloc[-1]["borrowings"]
            debt_2023 = bs_2023.iloc[-1]["borrowings"]

            if (
                pd.notna(debt_2024)
                and pd.notna(debt_2023)
                and debt_2024 < debt_2023
            ):
                deleveraging_flag = True

        capital_label = capital_allocation_pattern(
            latest_cf["operating_activity"],
            latest_cf["investing_activity"],
            latest_cf["financing_activity"],
            cfo_score,
        )

        sector = sector_map.get(
            company_id,
            "Unknown",
        )

        results.append(
            {
                "company_id": company_id,
                "sector": sector,
                "cfo_quality_score": cfo_score,
                "cfo_quality_label": cfo_label,
                "capex_intensity_pct": capex_value,
                "capex_label": capex_label,
                "fcf_cagr_5yr": fcf_cagr,
                "fcf_conversion_pct": fcf_conversion,
                "distress_flag": distress_flag,
                "deleveraging_flag": deleveraging_flag,
                "capital_allocation_label": capital_label,
            }
        )

        if distress_flag:
            distress_rows.append(
                {
                    "company_id": company_id,
                    "operating_activity": latest_cf[
                        "operating_activity"
                    ],
                    "financing_activity": latest_cf[
                        "financing_activity"
                    ],
                    "net_profit": latest_pnl[
                        "net_profit"
                    ],
                }
            )

    result_df = pd.DataFrame(results)

    distress_df = pd.DataFrame(
        distress_rows
    )

    result_df = result_df.sort_values(
        "company_id"
    ).reset_index(drop=True)

    result_df.to_excel(
        INTELLIGENCE_PATH,
        index=False,
    )

    distress_df.to_csv(
        DISTRESS_PATH,
        index=False,
    )

    print()
    print("DAY 31 CASH FLOW INTELLIGENCE")
    print("=" * 50)
    print()
    print("Companies:", len(result_df))
    print("Required companies: 92")
    print()
    print("CFO Quality Labels:")
    print(
        result_df[
            "cfo_quality_label"
        ]
        .value_counts(dropna=False)
        .to_string()
    )
    print()
    print("CapEx Labels:")
    print(
        result_df[
            "capex_label"
        ]
        .value_counts(dropna=False)
        .to_string()
    )
    print()
    print(
        "Distress flags:",
        int(
            result_df[
                "distress_flag"
            ].sum()
        ),
    )
    print(
        "Deleveraging flags:",
        int(
            result_df[
                "deleveraging_flag"
            ].sum()
        ),
    )
    print()
    print(
        "Missing CFO Quality:",
        result_df[
            "cfo_quality_score"
        ].isna().sum(),
    )
    print(
        "Missing CapEx Intensity:",
        result_df[
            "capex_intensity_pct"
        ].isna().sum(),
    )
    print()
    print("Excel output:")
    print(INTELLIGENCE_PATH)
    print()
    print("Distress output:")
    print(DISTRESS_PATH)


if __name__ == "__main__":
    main()