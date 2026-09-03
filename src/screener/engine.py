from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd
import yaml


DB_PATH = Path("nifty100.db")
CONFIG_PATH = Path("config/screener_config.yaml")


def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_financial_ratios(db_path=DB_PATH):
    con = sqlite3.connect(db_path)

    ratios_query = """
        SELECT *
        FROM financial_ratios
        ORDER BY company_id, year
    """

    df = pd.read_sql_query(ratios_query, con)

    pnl_query = """
        SELECT
            company_id,
            year,
            sales AS sales_cr,
            net_profit AS net_profit_cr
        FROM profitandloss
    """

    pnl = pd.read_sql_query(pnl_query, con)

    market_query = """
        SELECT
            company_id,
            year,
            market_cap_crore AS market_cap_cr,
            pe_ratio,
            pb_ratio,
            dividend_yield_pct
        FROM market_cap
    """

    market = pd.read_sql_query(market_query, con)

    sector_query = """
        SELECT
            company_id,
            broad_sector
        FROM sectors
    """

    sectors = pd.read_sql_query(sector_query, con)

    con.close()

    pnl = pnl.sort_values(["company_id", "year"])

    market = market.sort_values(["company_id", "year"])

    df = df.sort_values(["company_id", "year"])

    df = df.merge(
        pnl,
        on=["company_id", "year"],
        how="left"
    )

    df = df.merge(
        market,
        on=["company_id", "year"],
        how="left"
    )

    df = df.merge(
        sectors[["company_id", "broad_sector"]],
        on="company_id",
        how="left"
    )

    df["revenue_cagr_3yr"] = (
        df.groupby("company_id")["sales_cr"]
        .transform(
            lambda s: (
                (s / s.shift(3)) ** (1 / 3) - 1
            ) * 100
        )
    )

    df["de_declining"] = (
        df.groupby("company_id")["debt_to_equity"]
        .transform(lambda s: s < s.shift(1))
        .fillna(False)
    )

    df = (
        df.sort_values(["company_id", "year"])
        .groupby("company_id", group_keys=False)
        .tail(1)
        .reset_index(drop=True)
    )

    return df

def apply_filters(df: pd.DataFrame, filters: dict) -> pd.DataFrame:
    result = df.copy()

    if filters.get("roe_min") is not None:
        result = result[
            result["return_on_equity_pct"] > filters["roe_min"]
        ]

    if filters.get("de_max") is not None:
        de_condition = result["debt_to_equity"] < filters["de_max"]

        if filters.get("de_exact") is True:
            de_condition = (
                result["debt_to_equity"].fillna(float("inf"))
                == filters["de_max"]
            )

        if filters.get("financials_sector_exempt") is True:
            financials = (
                result["broad_sector"]
                .fillna("")
                .str.strip()
                .str.lower()
                .eq("financials")
            )
            result = result[financials | de_condition]
        else:
            result = result[de_condition]

    if filters.get("fcf_min") is not None:
        result = result[
            result["free_cash_flow_cr"] > filters["fcf_min"]
        ]

    if filters.get("revenue_cagr_5yr_min") is not None:
        result = result[
            result["revenue_cagr_5yr"] > filters["revenue_cagr_5yr_min"]
        ]

    if filters.get("pat_cagr_5yr_min") is not None:
        result = result[
            result["pat_cagr_5yr"] > filters["pat_cagr_5yr_min"]
        ]

    if filters.get("revenue_cagr_3yr_min") is not None:
        if "revenue_cagr_3yr" in result.columns:
            result = result[
                result["revenue_cagr_3yr"]
                > filters["revenue_cagr_3yr_min"]
            ]

    if filters.get("opm_min") is not None:
        result = result[
            result["operating_profit_margin_pct"] > filters["opm_min"]
        ]

    if filters.get("pe_max") is not None:
        if "pe_ratio" in result.columns:
            result = result[
                result["pe_ratio"] < filters["pe_max"]
            ]

    if filters.get("pb_max") is not None:
        if "pb_ratio" in result.columns:
            result = result[
                result["pb_ratio"] < filters["pb_max"]
            ]

    if filters.get("dividend_yield_min") is not None:
        if "dividend_yield_pct" in result.columns:
            result = result[
                result["dividend_yield_pct"]
                > filters["dividend_yield_min"]
            ]

    if filters.get("dividend_payout_max") is not None:
        if "dividend_payout_ratio_pct" in result.columns:
            result = result[
                result["dividend_payout_ratio_pct"]
                < filters["dividend_payout_max"]
            ]

    if filters.get("icr_min") is not None:
        icr = result["interest_coverage"].fillna(0)

        if "icr_label" in result.columns:
            icr = icr.mask(
                result["icr_label"].eq("Debt Free"),
                float("inf")
            )

        result = result[
            icr >= filters["icr_min"]
        ]

    if filters.get("market_cap_min") is not None:
        if "market_cap_cr" in result.columns:
            result = result[
                result["market_cap_cr"] >= filters["market_cap_min"]
            ]

    if filters.get("net_profit_min") is not None:
        if "net_profit_cr" in result.columns:
            result = result[
                result["net_profit_cr"] >= filters["net_profit_min"]
            ]

    if filters.get("eps_cagr_min") is not None:
        result = result[
            result["eps_cagr_5yr"] > filters["eps_cagr_min"]
        ]

    if filters.get("asset_turnover_min") is not None:
        result = result[
            result["asset_turnover"] > filters["asset_turnover_min"]
        ]

    if filters.get("sales_min") is not None:
        result = result[
            result["sales_cr"] > filters["sales_min"]
        ]

    if filters.get("de_declining") is True:
        if "de_declining" in result.columns:
            result = result[
                result["de_declining"] == True
            ]

    if "composite_quality_score" in result.columns:
        result = result.sort_values(
            "composite_quality_score",
            ascending=False
        )

    return result.reset_index(drop=True)
          
      
class ScreenerEngine:

    def __init__(
        self,
        db_path=DB_PATH,
        config_path=CONFIG_PATH
    ):

        self.db_path = Path(db_path)
        self.config_path = Path(config_path)

        self.config = load_config()

        self.df = load_financial_ratios(
            self.db_path
        )

    def run(self, filters: dict) -> pd.DataFrame:

        return apply_filters(
            self.df,
            filters,
        )

    def run_preset(
        self,
        preset_name: str
    ) -> pd.DataFrame:

        if preset_name not in self.config["presets"]:
            raise ValueError(
                f"Unknown preset: {preset_name}. "
                f"Available: {list(self.config['presets'])}"
            )

        filters = self.config["presets"][preset_name]

        return self.run(filters)


def main():

    print("Sprint 3 - Screener Engine")
    print("=" * 60)

    engine = ScreenerEngine()

    print("Database:", engine.db_path)
    print("Config:", engine.config_path)
    print("Rows:", len(engine.df))
    print(
        "Companies:",
        engine.df["company_id"].nunique()
    )

    print("\nAvailable presets:")

    for name in engine.config["presets"]:
        print(" -", name)

    print("\nPreset Results:")
    print("-" * 60)

    for preset in engine.config["presets"]:

        result = engine.run_preset(preset)

        print(
            preset,
            "rows=",
            len(result),
            "companies=",
            result["company_id"].nunique()
        )


if __name__ == "__main__":
    main()