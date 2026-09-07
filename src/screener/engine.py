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


def winsor_scale(
    series: pd.Series,
    higher_is_better: bool = True,
) -> pd.Series:
    values = pd.to_numeric(series, errors="coerce")

    if values.notna().sum() == 0:
        return pd.Series(50.0, index=series.index)

    p10 = values.quantile(0.10)
    p90 = values.quantile(0.90)

    clipped = values.clip(lower=p10, upper=p90)

    if p90 == p10:
        score = pd.Series(50.0, index=series.index)
    else:
        score = (
            (clipped - p10)
            / (p90 - p10)
            * 100
        )

        if not higher_is_better:
            score = 100 - score

    return score.fillna(50.0)


def calculate_day17_metrics(
    df: pd.DataFrame,
    db_path=DB_PATH,
) -> pd.DataFrame:
    result = df.copy()

    con = sqlite3.connect(db_path)

    pnl_query = """
        SELECT
            company_id,
            year,
            operating_profit,
            net_profit
        FROM profitandloss
    """

    pnl = pd.read_sql_query(
        pnl_query,
        con,
    )

    balance_query = """
        SELECT
            company_id,
            year,
            equity_capital,
            reserves,
            borrowings
        FROM balancesheet
    """

    balance_sheet = pd.read_sql_query(
        balance_query,
        con,
    )

    con.close()

    balance_sheet["capital_employed"] = (
        pd.to_numeric(
            balance_sheet["equity_capital"],
            errors="coerce",
        ).fillna(0)
        + pd.to_numeric(
            balance_sheet["reserves"],
            errors="coerce",
        ).fillna(0)
        + pd.to_numeric(
            balance_sheet["borrowings"],
            errors="coerce",
        ).fillna(0)
    )

    balance_sheet = balance_sheet.merge(
        pnl[
            [
                "company_id",
                "year",
                "operating_profit",
            ]
        ],
        on=["company_id", "year"],
        how="left",
    )

    balance_sheet["roce_pct"] = (
        pd.to_numeric(
            balance_sheet["operating_profit"],
            errors="coerce",
        )
        / balance_sheet["capital_employed"].replace(
            0,
            float("nan"),
        )
        * 100
    )

    latest_roce = (
        balance_sheet
        .sort_values(["company_id", "year"])
        .groupby(
            "company_id",
            as_index=False,
        )
        .tail(1)
        [
            [
                "company_id",
                "roce_pct",
            ]
        ]
    )

    result = result.merge(
        latest_roce,
        on="company_id",
        how="left",
    )

    result["cfo_pat_ratio"] = (
        pd.to_numeric(
            result["cash_from_operations_cr"],
            errors="coerce",
        )
        / pd.to_numeric(
            result["net_profit_cr"],
            errors="coerce",
        ).replace(
            0,
            float("nan"),
        )
    )

    historical = result.copy()

    historical = historical.sort_values(
        ["company_id", "year"]
    )

    historical["fcf_current"] = pd.to_numeric(
        historical["free_cash_flow_cr"],
        errors="coerce",
    )

    historical["fcf_5yr_ago"] = (
        historical
        .groupby("company_id")["fcf_current"]
        .shift(5)
    )

    valid_fcf = (
        historical["fcf_current"] > 0
    ) & (
        historical["fcf_5yr_ago"] > 0
    )

    historical["fcf_cagr"] = pd.NA

    historical.loc[valid_fcf, "fcf_cagr"] = (
        (
            historical.loc[
                valid_fcf,
                "fcf_current",
            ]
            / historical.loc[
                valid_fcf,
                "fcf_5yr_ago",
            ]
        )
        ** (1 / 5)
        - 1
    ) * 100

    latest_fcf_cagr = (
        historical
        .sort_values(["company_id", "year"])
        .groupby(
            "company_id",
            as_index=False,
        )
        .tail(1)
        [
            [
                "company_id",
                "fcf_cagr",
            ]
        ]
    )

    result = result.merge(
        latest_fcf_cagr,
        on="company_id",
        how="left",
    )

    return result


def calculate_composite_score(
    df: pd.DataFrame,
) -> pd.DataFrame:
    result = df.copy()

    result["score_roe"] = winsor_scale(
        result["return_on_equity_pct"],
        higher_is_better=True,
    )

    result["score_roce"] = winsor_scale(
        result["roce_pct"],
        higher_is_better=True,
    )

    result["score_npm"] = winsor_scale(
        result["net_profit_margin_pct"],
        higher_is_better=True,
    )

    result["profitability_score"] = (
        result["score_roe"] * 0.15
        + result["score_roce"] * 0.10
        + result["score_npm"] * 0.10
    )

    result["score_fcf_cagr"] = winsor_scale(
        result["fcf_cagr"],
        higher_is_better=True,
    )

    result["score_cfo_pat"] = winsor_scale(
        result["cfo_pat_ratio"],
        higher_is_better=True,
    )

    result["score_fcf_positive"] = (
        pd.to_numeric(
            result["free_cash_flow_cr"],
            errors="coerce",
        )
        > 0
    ).astype(float) * 100

    result["cash_quality_score"] = (
        result["score_fcf_cagr"] * 0.15
        + result["score_cfo_pat"] * 0.10
        + result["score_fcf_positive"] * 0.05
    )

    result["score_revenue_growth"] = winsor_scale(
        result["revenue_cagr_5yr"],
        higher_is_better=True,
    )

    result["score_pat_growth"] = winsor_scale(
        result["pat_cagr_5yr"],
        higher_is_better=True,
    )

    result["growth_score"] = (
        result["score_revenue_growth"] * 0.10
        + result["score_pat_growth"] * 0.10
    )

    result["score_de"] = winsor_scale(
        result["debt_to_equity"],
        higher_is_better=False,
    )

    icr = pd.to_numeric(
        result["interest_coverage"],
        errors="coerce",
    )

    result["score_icr"] = winsor_scale(
        icr,
        higher_is_better=True,
    )

    if "icr_label" in result.columns:
        debt_free = (
            result["icr_label"]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.lower()
            .eq("debt free")
        )

        result.loc[
            debt_free,
            "score_icr",
        ] = 100.0

    result["leverage_score"] = (
        result["score_de"] * 0.10
        + result["score_icr"] * 0.05
    )

    result["composite_quality_score"] = (
        result["profitability_score"]
        + result["cash_quality_score"]
        + result["growth_score"]
        + result["leverage_score"]
    ).clip(
        lower=0,
        upper=100,
    )

    sector = (
        result["broad_sector"]
        .fillna("Unknown")
        .astype(str)
        .str.strip()
    )

    result["sector_relative_score"] = (
        result
        .assign(_score=result["composite_quality_score"])
        .groupby(sector)["_score"]
        .rank(
            pct=True,
            method="average",
        )
        * 100
    )

    return result


def load_financial_ratios(
    db_path=DB_PATH,
) -> pd.DataFrame:
    con = sqlite3.connect(db_path)

    ratios_query = """
        SELECT *
        FROM financial_ratios
        ORDER BY company_id, year
    """

    df = pd.read_sql_query(
        ratios_query,
        con,
    )

    pnl_query = """
        SELECT
            company_id,
            year,
            sales AS sales_cr,
            net_profit AS net_profit_cr
        FROM profitandloss
    """

    pnl = pd.read_sql_query(
        pnl_query,
        con,
    )

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

    market = pd.read_sql_query(
        market_query,
        con,
    )

    sector_query = """
        SELECT
            company_id,
            broad_sector
        FROM sectors
    """

    sectors = pd.read_sql_query(
        sector_query,
        con,
    )

    con.close()

    pnl = pnl.sort_values(
        ["company_id", "year"]
    )

    market = market.sort_values(
        ["company_id", "year"]
    )

    df = df.sort_values(
        ["company_id", "year"]
    )

    df = df.merge(
        pnl,
        on=["company_id", "year"],
        how="left",
    )

    df = df.merge(
        market,
        on=["company_id", "year"],
        how="left",
    )

    df = df.merge(
        sectors[
            [
                "company_id",
                "broad_sector",
            ]
        ],
        on="company_id",
        how="left",
    )

    df["revenue_cagr_3yr"] = (
        df.groupby("company_id")["sales_cr"]
        .transform(
            lambda s: (
                (
                    s
                    / s.shift(3)
                )
                ** (1 / 3)
                - 1
            )
            * 100
        )
    )

    df["de_declining"] = (
        df.groupby("company_id")["debt_to_equity"]
        .transform(
            lambda s: s < s.shift(1)
        )
        .fillna(False)
    )

    df = calculate_day17_metrics(
        df,
        db_path,
    )

    df = calculate_composite_score(df)

    df = (
        df.sort_values(
            ["company_id", "year"]
        )
        .groupby(
            "company_id",
            group_keys=False,
        )
        .tail(1)
        .reset_index(drop=True)
    )

    return df


def apply_filters(
    df: pd.DataFrame,
    filters: dict,
) -> pd.DataFrame:
    result = df.copy()

    if filters.get("roe_min") is not None:
        result = result[
            result["return_on_equity_pct"]
            > filters["roe_min"]
        ]

    if filters.get("de_max") is not None:
        de_condition = (
            result["debt_to_equity"]
            < filters["de_max"]
        )

        if filters.get("de_exact") is True:
            de_condition = (
                result["debt_to_equity"]
                .fillna(float("inf"))
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

            result = result[
                financials | de_condition
            ]
        else:
            result = result[
                de_condition
            ]

    if filters.get("fcf_min") is not None:
        result = result[
            result["free_cash_flow_cr"]
            > filters["fcf_min"]
        ]

    if filters.get("revenue_cagr_5yr_min") is not None:
        result = result[
            result["revenue_cagr_5yr"]
            > filters["revenue_cagr_5yr_min"]
        ]

    if filters.get("pat_cagr_5yr_min") is not None:
        result = result[
            result["pat_cagr_5yr"]
            > filters["pat_cagr_5yr_min"]
        ]

    if filters.get("revenue_cagr_3yr_min") is not None:
        if "revenue_cagr_3yr" in result.columns:
            result = result[
                result["revenue_cagr_3yr"]
                > filters["revenue_cagr_3yr_min"]
            ]

    if filters.get("opm_min") is not None:
        result = result[
            result["operating_profit_margin_pct"]
            > filters["opm_min"]
        ]

    if filters.get("pe_max") is not None:
        if "pe_ratio" in result.columns:
            result = result[
                result["pe_ratio"]
                < filters["pe_max"]
            ]

    if filters.get("pb_max") is not None:
        if "pb_ratio" in result.columns:
            result = result[
                result["pb_ratio"]
                < filters["pb_max"]
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
        icr = result[
            "interest_coverage"
        ].fillna(0)

        if "icr_label" in result.columns:
            icr = icr.mask(
                result["icr_label"]
                .fillna("")
                .astype(str)
                .str.strip()
                .str.lower()
                .eq("debt free"),
                float("inf"),
            )

        result = result[
            icr >= filters["icr_min"]
        ]

    if filters.get("market_cap_min") is not None:
        if "market_cap_cr" in result.columns:
            result = result[
                result["market_cap_cr"]
                >= filters["market_cap_min"]
            ]

    if filters.get("net_profit_min") is not None:
        if "net_profit_cr" in result.columns:
            result = result[
                result["net_profit_cr"]
                >= filters["net_profit_min"]
            ]

    if filters.get("eps_cagr_min") is not None:
        result = result[
            result["eps_cagr_5yr"]
            > filters["eps_cagr_min"]
        ]

    if filters.get("asset_turnover_min") is not None:
        result = result[
            result["asset_turnover"]
            > filters["asset_turnover_min"]
        ]

    if filters.get("sales_min") is not None:
        result = result[
            result["sales_cr"]
            > filters["sales_min"]
        ]

    if filters.get("de_declining") is True:
        if "de_declining" in result.columns:
            result = result[
                result["de_declining"] == True
            ]

    if "composite_quality_score" in result.columns:
        result = result.sort_values(
            "composite_quality_score",
            ascending=False,
        )

    return result.reset_index(drop=True)


class ScreenerEngine:

    def __init__(
        self,
        db_path=DB_PATH,
        config_path=CONFIG_PATH,
    ):
        self.db_path = Path(db_path)
        self.config_path = Path(config_path)

        self.config = load_config()

        self.df = load_financial_ratios(
            self.db_path
        )

    def run(
        self,
        filters: dict,
    ) -> pd.DataFrame:
        return apply_filters(
            self.df,
            filters,
        )

    def run_preset(
        self,
        preset_name: str,
    ) -> pd.DataFrame:
        if preset_name not in self.config["presets"]:
            raise ValueError(
                f"Unknown preset: {preset_name}. "
                f"Available: "
                f"{list(self.config['presets'])}"
            )

        filters = self.config["presets"][
            preset_name
        ]

        return self.run(filters)


def main():

    print("Sprint 3 - Screener Engine")
    print("=" * 60)

    engine = ScreenerEngine()

    print(
        "Database:",
        engine.db_path,
    )

    print(
        "Config:",
        engine.config_path,
    )

    print(
        "Rows:",
        len(engine.df),
    )

    print(
        "Companies:",
        engine.df["company_id"].nunique(),
    )

    print("\nAvailable presets:")

    for name in engine.config["presets"]:
        print(" -", name)

    print("\nPreset Results:")
    print("-" * 60)

    for preset in engine.config["presets"]:

        result = engine.run_preset(
            preset
        )

        print(
            preset,
            "rows=",
            len(result),
            "companies=",
            result["company_id"].nunique(),
        )


if __name__ == "__main__":
    main()