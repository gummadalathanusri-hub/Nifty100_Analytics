import pandas as pd
from pathlib import Path

p = Path("data/raw")

files = [
    "profitandloss.xlsx",
    "balancesheet.xlsx",
    "cashflow.xlsx",
]

for filename in files:
    print(f"\n=== {filename} ===")

    df = pd.read_excel(
        p / filename,
        header=1
    )

    df["company_id"] = (
        df["company_id"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    if "year" in df.columns:
        df["year"] = (
            df["year"]
            .astype(str)
            .str.strip()
        )

    key_duplicates = df.duplicated(
        subset=["company_id", "year"],
        keep=False
    )

    exact_duplicates = df.duplicated(
        keep=False
    )

    print(
        "Duplicate company-year rows:",
        int(key_duplicates.sum())
    )

    print(
        "Exact duplicate rows:",
        int(exact_duplicates.sum())
    )

    print(
        "\nDuplicate examples:"
    )

    print(
        df.loc[key_duplicates]
        .head(20)
        .to_string(index=False)
    )