import sqlite3
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "nifty100.db"
UNIVERSE_PATH = ROOT / "output" / "sprint6_company_universe.csv"
OUTPUT_PATH = ROOT / "output" / "portfolio_stats.csv"

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


def load_portfolio_data() -> pd.DataFrame:
    """Load the latest-year KPI data for the Sprint 6 92-company universe."""

    universe = pd.read_csv(UNIVERSE_PATH)

    placeholders = ",".join(["?"] * len(universe))

    query = f"""
        SELECT
            company_id,
            year,
            {", ".join(KPIS)}
        FROM financial_ratios
        WHERE company_id IN ({placeholders})
        AND year = (
            SELECT MAX(fr2.year)
            FROM financial_ratios fr2
            WHERE fr2.company_id = financial_ratios.company_id
        )
        ORDER BY company_id
    """

    with sqlite3.connect(DB_PATH) as conn:
        df = pd.read_sql_query(
            query,
            conn,
            params=universe["id"].tolist(),
        )

    return df


def calculate_portfolio_stats(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate percentile and descriptive statistics for the 10 core KPIs."""

    rows = []

    for kpi in KPIS:
        values = pd.to_numeric(df[kpi], errors="coerce").dropna()

        rows.append(
            {
                "kpi": kpi,
                "p10": values.quantile(0.10),
                "p25": values.quantile(0.25),
                "p50": values.quantile(0.50),
                "p75": values.quantile(0.75),
                "p90": values.quantile(0.90),
                "mean": values.mean(),
                "std": values.std(),
                "count": values.count(),
            }
        )

    return pd.DataFrame(rows)


def main():
    """Generate portfolio-level KPI percentile and summary statistics."""
    print("SPRINT 6 - DAY 37 PORTFOLIO STATISTICS")
    print("=" * 50)

    df = load_portfolio_data()

    print(f"Companies loaded: {len(df)}")
    print(f"Latest year: {df['year'].max()}")

    print("\nMissing values:")
    print(df[KPIS].isna().sum().to_string())

    stats = calculate_portfolio_stats(df)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    stats.to_csv(OUTPUT_PATH, index=False)

    print(f"\nKPIs processed: {len(stats)}")
    print(f"Output: {OUTPUT_PATH}")

    print("\nPortfolio statistics:")
    print(stats.to_string(index=False))

    print("\nCompleted successfully.")


if __name__ == "__main__":
    main()
