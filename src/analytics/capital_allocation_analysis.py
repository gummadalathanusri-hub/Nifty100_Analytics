from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "nifty100.db"
INPUT_PATH = ROOT / "output" / "capital_allocation.csv"
INTELLIGENCE_PATH = ROOT / "output" / "cashflow_intelligence.xlsx"
CHANGES_PATH = ROOT / "output" / "pattern_changes.csv"


def main():
    conn = sqlite3.connect(DB_PATH)

    target = pd.read_sql_query(
        """
        SELECT DISTINCT company_id
        FROM sectors
        """,
        conn,
    )

    conn.close()

    target_ids = set(target["company_id"])

    allocation = pd.read_csv(INPUT_PATH)

    allocation = allocation[
        allocation["company_id"].isin(target_ids)
    ].copy()

    allocation["year"] = pd.to_numeric(
        allocation["year"],
        errors="coerce",
    )

    allocation = allocation.sort_values(
        ["company_id", "year"]
    ).reset_index(drop=True)

    changes = []

    for company_id, group in allocation.groupby(
        "company_id"
    ):
        group = group.sort_values("year").reset_index(
            drop=True
        )

        for i in range(1, len(group)):
            previous = group.iloc[i - 1]
            current = group.iloc[i]

            if (
                previous["pattern_label"]
                != current["pattern_label"]
            ):
                changes.append(
                    {
                        "company_id": company_id,
                        "previous_year": int(
                            previous["year"]
                        ),
                        "previous_pattern": previous[
                            "pattern_label"
                        ],
                        "current_year": int(
                            current["year"]
                        ),
                        "current_pattern": current[
                            "pattern_label"
                        ],
                    }
                )

    changes_df = pd.DataFrame(changes)

    if not changes_df.empty:
        changes_df = changes_df.sort_values(
            ["company_id", "current_year"]
        ).reset_index(drop=True)

    changes_df.to_csv(
        CHANGES_PATH,
        index=False,
    )

    latest = allocation[
        allocation["year"] == 2024
    ].copy()

    distribution = (
        latest["pattern_label"]
        .value_counts()
        .sort_index()
    )

    intelligence = pd.read_excel(
        INTELLIGENCE_PATH
    )

    latest_labels = latest[
        ["company_id", "pattern_label"]
    ].rename(
        columns={
            "pattern_label":
            "capital_allocation_label"
        }
    )

    intelligence = intelligence.drop(
        columns=["capital_allocation_label"],
        errors="ignore",
    )

    intelligence = intelligence.merge(
        latest_labels,
        on="company_id",
        how="left",
    )

    intelligence.to_excel(
        INTELLIGENCE_PATH,
        index=False,
    )

    print()
    print("DAY 32 CAPITAL ALLOCATION ANALYSIS")
    print("=" * 50)
    print()
    print("Target companies:", len(target_ids))
    print("Target rows:", len(allocation))
    print("Latest year rows:", len(latest))
    print(
        "Duplicate company-year:",
        allocation.duplicated(
            ["company_id", "year"]
        ).sum(),
    )
    print()
    print("2024 Pattern Distribution:")
    print(distribution.to_string())
    print()
    print("Pattern changes:", len(changes_df))
    print()
    print("Output:")
    print(CHANGES_PATH)
    print()
    print("Updated:")
    print(INTELLIGENCE_PATH)


if __name__ == "__main__":
    main()