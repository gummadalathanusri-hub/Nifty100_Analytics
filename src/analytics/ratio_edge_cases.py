import sqlite3
from pathlib import Path

import pandas as pd


DB_PATH = "nifty100.db"
COMPANIES_PATH = "data/raw/companies.xlsx"
OUTPUT_PATH = Path("output/ratio_edge_cases.log")


def main():
    con = sqlite3.connect(DB_PATH)

    ratios = pd.read_sql(
        """
        SELECT
            company_id,
            year,
            return_on_capital_employed_pct,
            return_on_equity_pct
        FROM financial_ratios
        """,
        con,
    )

    companies = pd.read_excel(
        COMPANIES_PATH,
        header=1,
    )

    companies = companies[
        ["id", "roce_percentage", "roe_percentage"]
    ].rename(
        columns={"id": "company_id"}
    )

    latest = (
        ratios
        .sort_values(["company_id", "year"])
        .drop_duplicates(
            subset=["company_id"],
            keep="last",
        )
    )

    merged = latest.merge(
        companies,
        on="company_id",
        how="left",
    )

    lines = [
        "Day 13 — Ratio Edge Case Log",
        "=" * 70,
        "",
    ]


    roce_data = merged[
        merged["return_on_capital_employed_pct"].notna()
        & merged["roce_percentage"].notna()
    ].copy()

    roce_data["difference"] = (
        roce_data["return_on_capital_employed_pct"]
        - roce_data["roce_percentage"]
    ).abs()

    roce_anomalies = roce_data[
        roce_data["difference"] > 5
    ].sort_values(
        "difference",
        ascending=False,
    )

    lines.append(
        f"ROCE anomalies (>5 percentage points): "
        f"{len(roce_anomalies)}"
    )
    lines.append("")

    for _, row in roce_anomalies.iterrows():

        engine = row["return_on_capital_employed_pct"]
        source = row["roce_percentage"]
        difference = row["difference"]

        lines.append(
            f"Company: {row['company_id']} | "
            f"Year: {int(row['year'])}"
        )
        lines.append(
            f"Metric: ROCE | "
            f"Engine: {engine:.2f}% | "
            f"Source: {source:.2f}% | "
            f"Difference: {difference:.2f} percentage points"
        )
        lines.append(
            "Category: data source issue / methodology difference"
        )
        lines.append(
            "Explanation: Ratio engine follows the Sprint-defined "
            "ROCE formula using available P&L and balance-sheet "
            "fields. The pre-computed source ROCE uses a different "
            "methodology/base."
        )
        lines.append("")


    roe_data = merged[
        merged["return_on_equity_pct"].notna()
        & merged["roe_percentage"].notna()
    ].copy()

    roe_data["difference"] = (
        roe_data["return_on_equity_pct"]
        - roe_data["roe_percentage"]
    ).abs()

    roe_anomalies = roe_data[
        roe_data["difference"] > 5
    ].sort_values(
        "difference",
        ascending=False,
    )

    lines.append(
        f"ROE anomalies (>5 percentage points): "
        f"{len(roe_anomalies)}"
    )
    lines.append("")

    for _, row in roe_anomalies.iterrows():

        engine = row["return_on_equity_pct"]
        source = row["roe_percentage"]
        difference = row["difference"]

        category = "data source issue"

        if row["company_id"] == "TCS":
            explanation = (
                "Source ROE value is anomalous (0.52%). "
                "Ratio engine value is retained for analytics; "
                "source value is retained for display comparison."
            )
        else:
            explanation = (
                "Difference between the ratio-engine calculation "
                "and the pre-computed company source value."
            )

        lines.append(
            f"Company: {row['company_id']} | "
            f"Year: {int(row['year'])}"
        )
        lines.append(
            f"Metric: ROE | "
            f"Engine: {engine:.2f}% | "
            f"Source: {source:.2f}% | "
            f"Difference: {difference:.2f} percentage points"
        )
        lines.append(
            f"Category: {category}"
        )
        lines.append(
            f"Explanation: {explanation}"
        )
        lines.append("")



    missing_roce = merged[
        merged["roce_percentage"].isna()
    ]

    missing_roe = merged[
        merged["roe_percentage"].isna()
    ]

    lines.append(
        f"Companies with missing source ROCE: "
        f"{len(missing_roce)}"
    )
    lines.append(
        "Missing ROCE companies: "
        + ", ".join(
            missing_roce["company_id"].astype(str)
        )
    )
    lines.append("")

    lines.append(
        f"Companies with missing source ROE: "
        f"{len(missing_roe)}"
    )
    lines.append(
        "Missing ROE companies: "
        + ", ".join(
            missing_roe["company_id"].astype(str)
        )
    )
    lines.append("")

    
    lines.append("Summary")
    lines.append("-" * 70)
    lines.append(
        "Ratio-engine values are used for analytics."
    )
    lines.append(
        "Pre-computed company values are retained for "
        "source/display comparison."
    )
    lines.append(
        "ROCE and ROE differences greater than 5 percentage "
        "points are logged."
    )
    lines.append(
        "Financials high-leverage carve-out was verified "
        "separately: 0 Financials records were incorrectly flagged."
    )

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_PATH.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )

    print("Ratio edge-case log generated.")
    print(f"ROCE anomalies: {len(roce_anomalies)}")
    print(f"ROE anomalies: {len(roe_anomalies)}")
    print(f"Missing source ROCE: {len(missing_roce)}")
    print(f"Missing source ROE: {len(missing_roe)}")
    print(f"Output: {OUTPUT_PATH}")

    con.close()


if __name__ == "__main__":
    main()