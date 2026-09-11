from pathlib import Path
import sqlite3
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "nifty100.db"
MARKET_CAP_PATH = PROJECT_ROOT / "data" / "supporting" / "market_cap.xlsx"
OUTPUT_DIR = PROJECT_ROOT / "output"

SUMMARY_PATH = OUTPUT_DIR / "valuation_summary.xlsx"
FLAGS_PATH = OUTPUT_DIR / "valuation_flags.csv"


def load_market_cap():
    df = pd.read_excel(MARKET_CAP_PATH)

    required = [
        "company_id",
        "year",
        "market_cap_crore",
        "pe_ratio",
        "pb_ratio",
        "ev_ebitda"
    ]

    missing = [column for column in required if column not in df.columns]

    if missing:
        raise ValueError(f"Missing market cap columns: {missing}")

    df = df[required].copy()

    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df["market_cap_crore"] = pd.to_numeric(
        df["market_cap_crore"],
        errors="coerce"
    )
    df["pe_ratio"] = pd.to_numeric(
        df["pe_ratio"],
        errors="coerce"
    )
    df["pb_ratio"] = pd.to_numeric(
        df["pb_ratio"],
        errors="coerce"
    )
    df["ev_ebitda"] = pd.to_numeric(
        df["ev_ebitda"],
        errors="coerce"
    )

    return df


def load_database_data():
    with sqlite3.connect(DB_PATH) as conn:
        companies = pd.read_sql_query(
            """
            SELECT
                id AS company_id,
                company_name
            FROM companies
            """,
            conn
        )

        sectors = pd.read_sql_query(
            """
            SELECT
                company_id,
                broad_sector,
                sub_sector
            FROM sectors
            """,
            conn
        )

        ratios = pd.read_sql_query(
            """
            SELECT
                company_id,
                year,
                free_cash_flow_cr
            FROM financial_ratios
            """,
            conn
        )

    sectors = sectors.drop_duplicates("company_id")

    ratios["year"] = pd.to_numeric(
        ratios["year"],
        errors="coerce"
    )

    ratios["free_cash_flow_cr"] = pd.to_numeric(
        ratios["free_cash_flow_cr"],
        errors="coerce"
    )

    return companies, sectors, ratios


def calculate_valuation():
    market_cap = load_market_cap()
    companies, sectors, ratios = load_database_data()

    market_cap = market_cap[
        market_cap["company_id"].isin(
            sectors["company_id"]
        )
    ].copy()

    latest_year = int(market_cap["year"].max())

    latest_market = market_cap[
        market_cap["year"].eq(latest_year)
    ].copy()

    latest_market = latest_market.sort_values(
        ["company_id", "year"]
    )

    latest_fcf = (
        ratios[
            ratios["company_id"].isin(
                latest_market["company_id"]
            )
        ]
        .sort_values(["company_id", "year"])
        .groupby("company_id", as_index=False)
        .tail(1)
    )

    latest_fcf = latest_fcf[
        ["company_id", "free_cash_flow_cr"]
    ].copy()

    latest_fcf = latest_fcf.rename(
        columns={
            "free_cash_flow_cr": "FCF"
        }
    )

    latest_market = latest_market.merge(
        latest_fcf,
        on="company_id",
        how="left"
    )

    latest_market = latest_market.merge(
        companies,
        on="company_id",
        how="left"
    )

    latest_market = latest_market.merge(
        sectors[
            ["company_id", "broad_sector"]
        ],
        on="company_id",
        how="left"
    )

    five_year_market = market_cap[
        market_cap["year"].between(
            latest_year - 4,
            latest_year
        )
    ].copy()

    five_year_median_pe = (
        five_year_market
        .groupby("company_id")["pe_ratio"]
        .median()
        .reset_index()
        .rename(
            columns={
                "pe_ratio": "5yr_median_PE"
            }
        )
    )

    latest_market = latest_market.merge(
        five_year_median_pe,
        on="company_id",
        how="left"
    )

    sector_median_pe = (
        latest_market
        .groupby("broad_sector")["pe_ratio"]
        .median()
        .reset_index()
        .rename(
            columns={
                "pe_ratio": "sector_median_PE"
            }
        )
    )

    latest_market = latest_market.merge(
        sector_median_pe,
        on="broad_sector",
        how="left"
    )

    latest_market["FCF_yield_pct"] = (
        latest_market["FCF"]
        / latest_market["market_cap_crore"]
        * 100
    )

    latest_market.loc[
        latest_market["market_cap_crore"].le(0),
        "FCF_yield_pct"
    ] = pd.NA

    latest_market["PE_vs_sector_median_pct"] = (
        (
            latest_market["pe_ratio"]
            - latest_market["sector_median_PE"]
        )
        / latest_market["sector_median_PE"]
        * 100
    )

    latest_market.loc[
        latest_market["sector_median_PE"].le(0),
        "PE_vs_sector_median_pct"
    ] = pd.NA

    def get_flag(row):
        pe = row["pe_ratio"]
        sector_pe = row["sector_median_PE"]

        if pd.isna(pe) or pd.isna(sector_pe):
            return "Fair"

        if sector_pe <= 0:
            return "Fair"

        if pe > sector_pe * 1.5:
            return "Caution"

        if pe < sector_pe * 0.7:
            return "Discount"

        return "Fair"

    latest_market["flag"] = latest_market.apply(
        get_flag,
        axis=1
    )

    summary = latest_market[
        [
            "company_id",
            "company_name",
            "broad_sector",
            "pe_ratio",
            "pb_ratio",
            "ev_ebitda",
            "FCF_yield_pct",
            "5yr_median_PE",
            "PE_vs_sector_median_pct",
            "flag"
        ]
    ].copy()

    summary = summary.rename(
        columns={
            "broad_sector": "sector",
            "pe_ratio": "P/E",
            "pb_ratio": "P/B",
            "ev_ebitda": "EV/EBITDA"
        }
    )

    numeric_columns = [
        "P/E",
        "P/B",
        "EV/EBITDA",
        "FCF_yield_pct",
        "5yr_median_PE",
        "PE_vs_sector_median_pct"
    ]

    for column in numeric_columns:
        summary[column] = pd.to_numeric(
            summary[column],
            errors="coerce"
        ).round(2)

    summary = summary.sort_values(
        "company_id"
    ).reset_index(drop=True)

    flags = summary[
        summary["flag"].isin(
            ["Caution", "Discount"]
        )
    ].copy()

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    summary.to_excel(
        SUMMARY_PATH,
        index=False
    )

    flags.to_csv(
        FLAGS_PATH,
        index=False
    )

    print(f"Latest valuation year: {latest_year}")
    print(f"Valuation summary rows: {len(summary)}")
    print(f"Valuation flags rows: {len(flags)}")
    print(f"Caution: {(summary['flag'] == 'Caution').sum()}")
    print(f"Discount: {(summary['flag'] == 'Discount').sum()}")
    print(f"Fair: {(summary['flag'] == 'Fair').sum()}")
    print(f"Summary: {SUMMARY_PATH}")
    print(f"Flags: {FLAGS_PATH}")


if __name__ == "__main__":
    calculate_valuation()