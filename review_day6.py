import pandas as pd
from pathlib import Path

p = Path("data/raw")

files = [
    "profitandloss.xlsx",
    "balancesheet.xlsx",
    "cashflow.xlsx",
]

companies = [
    "ADANIPORTS",
    "ASIANPAINT",
    "BAJFINANCE",
    "JIOFIN",
    "TCS",
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

    for company in companies:
        company_df = df[
            df["company_id"] == company
        ]

        years = (
            company_df["year"]
            .astype(str)
            .tolist()
        )

        print(
            f"{company}: {years}"
        )