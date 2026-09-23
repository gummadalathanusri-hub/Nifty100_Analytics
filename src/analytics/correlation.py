"""
Sprint 6 - Day 37
Pearson correlation heatmap for the 92-company universe.
"""

import sqlite3
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

ROOT_DIR = Path(__file__).resolve().parents[2]
DB_PATH = ROOT_DIR / "nifty100.db"
UNIVERSE_PATH = ROOT_DIR / "output" / "sprint6_company_universe.csv"
REPORTS_DIR = ROOT_DIR / "reports"

OUTPUT_PATH = REPORTS_DIR / "correlation_heatmap.png"

KPIS = [
    "net_profit_margin_pct",
    "operating_profit_margin_pct",
    "return_on_equity_pct",
    "debt_to_equity",
    "interest_coverage",
    "asset_turnover",
    "free_cash_flow_cr",
    "earnings_per_share",
    "revenue_cagr_5yr",
    "pat_cagr_5yr",
]


def load_kpi_data() -> pd.DataFrame:
    """Load the latest-year KPI data for the 92-company universe."""
    universe = pd.read_csv(UNIVERSE_PATH)

    company_ids = universe["id"].dropna().astype(str).unique().tolist()

    if len(company_ids) != 92:
        raise ValueError(f"Expected 92 companies, found {len(company_ids)}.")

    placeholders = ",".join(["?"] * len(company_ids))

    columns = ", ".join(KPIS)

    query = f"""
        SELECT
            company_id,
            year,
            {columns}
        FROM financial_ratios
        WHERE year = (
            SELECT MAX(year)
            FROM financial_ratios
        )
        AND company_id IN ({placeholders})
    """

    with sqlite3.connect(DB_PATH) as conn:
        df = pd.read_sql_query(
            query,
            conn,
            params=company_ids,
        )

    if len(df) != 92:
        raise ValueError(f"Expected 92 latest-year rows, found {len(df)}.")

    return df


def create_heatmap(df: pd.DataFrame) -> None:
    """Create and save the annotated Pearson correlation heatmap."""
    correlation = df[KPIS].corr(method="pearson")

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(14, 11))

    sns.heatmap(
        correlation,
        annot=True,
        fmt=".2f",
        cmap="coolwarm",
        center=0,
        square=True,
        linewidths=0.5,
        cbar_kws={"label": "Pearson Correlation"},
    )

    plt.title(
        "Pearson Correlation Heatmap — Nifty100 Sprint 6",
        fontsize=14,
    )
    plt.xticks(rotation=45, ha="right")
    plt.yticks(rotation=0)
    plt.tight_layout()

    plt.savefig(
        OUTPUT_PATH,
        dpi=150,
        bbox_inches="tight",
    )

    plt.close()


def main() -> None:
    """Run the correlation heatmap pipeline."""
    print("SPRINT 6 - DAY 37 CORRELATION HEATMAP")
    print("=" * 50)

    df = load_kpi_data()

    print(f"Companies loaded: {len(df)}")
    print(f"Latest year: {df['year'].unique().tolist()}")

    print("\nMissing values:")
    print(df[KPIS].isna().sum().to_string())

    create_heatmap(df)

    print("\nKPIs:")
    for kpi in KPIS:
        print(f"- {kpi}")

    print("\nOutput:")
    print(OUTPUT_PATH)

    print("\nCompleted successfully.")


if __name__ == "__main__":
    main()
