import sqlite3
from pathlib import Path

import pandas as pd

from src.analytics.cashflow_kpis import (
    cfo_quality_score,
    capital_allocation_pattern,
)


DB_PATH = Path("nifty100.db")
OUTPUT_PATH = Path("output/capital_allocation.csv")


def main():
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    con = sqlite3.connect(DB_PATH)

    query = """
        SELECT
            p.company_id,
            p.year,
            c.operating_activity AS cfo,
            c.investing_activity AS cfi,
            c.financing_activity AS cff,
            p.net_profit AS pat
        FROM profitandloss p
        LEFT JOIN cashflow c
            ON p.company_id = c.company_id
            AND p.year = c.year
        ORDER BY p.company_id, p.year
    """

    df = pd.read_sql(query, con)
    con.close()

    print("P&L base rows:", len(df))
    print("Companies:", df["company_id"].nunique())

    df["cfo_sign"] = df["cfo"].apply(
        lambda x: "+"
        if pd.notna(x) and x > 0
        else "-"
        if pd.notna(x) and x < 0
        else "0"
    )

    df["cfi_sign"] = df["cfi"].apply(
        lambda x: "+"
        if pd.notna(x) and x > 0
        else "-"
        if pd.notna(x) and x < 0
        else "0"
    )

    df["cff_sign"] = df["cff"].apply(
        lambda x: "+"
        if pd.notna(x) and x > 0
        else "-"
        if pd.notna(x) and x < 0
        else "0"
    )

    df["cfo_pat_ratio"] = df.apply(
        lambda row: cfo_quality_score(
            row["cfo"],
            row["pat"],
        ),
        axis=1,
    )

    df["pattern_label"] = df.apply(
        lambda row: capital_allocation_pattern(
            row["cfo"],
            row["cfi"],
            row["cff"],
            row["cfo_pat_ratio"],
        ),
        axis=1,
    )

    output = df[
        [
            "company_id",
            "year",
            "cfo_sign",
            "cfi_sign",
            "cff_sign",
            "pattern_label",
        ]
    ].copy()

    output = output.drop_duplicates(
        subset=["company_id", "year"]
    )

    output.to_csv(
        OUTPUT_PATH,
        index=False,
    )

    print("Capital allocation file generated.")
    print("Rows:", len(output))
    print("Unique company-year:", output[["company_id", "year"]].drop_duplicates().shape[0])
    print("Companies:", output["company_id"].nunique())
    print("\nPattern counts:")
    print(output["pattern_label"].value_counts())
    print("\nSample:")
    print(output.head(10).to_string(index=False))


if __name__ == "__main__":
    main()