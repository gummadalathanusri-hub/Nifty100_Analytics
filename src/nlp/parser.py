import os
import re
import sqlite3
import pandas as pd


BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ANALYSIS_FILE = os.path.join(BASE_DIR, "data", "raw", "analysis.xlsx")
DB_FILE = os.path.join(BASE_DIR, "nifty100.db")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

PARSED_FILE = os.path.join(OUTPUT_DIR, "analysis_parsed.csv")
FAILURES_FILE = os.path.join(OUTPUT_DIR, "parse_failures.csv")

PATTERN = re.compile(r"(\d+)\s*Years?:?\s*([\d.]+)%")


def parse_metric(value):
    if pd.isna(value):
        return None

    text = str(value).strip()
    match = PATTERN.search(text)

    if not match:
        return None

    period_years = int(match.group(1))
    value_pct = float(match.group(2))

    return period_years, value_pct


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("Reading analysis.xlsx...")
    df = pd.read_excel(ANALYSIS_FILE, header=1)

    metric_columns = [
        "compounded_sales_growth",
        "compounded_profit_growth",
        "stock_price_cagr",
        "roe"
    ]

    parsed_rows = []
    failure_rows = []

    for _, row in df.iterrows():
        company_id = str(row["company_id"]).strip()

        for metric in metric_columns:
            raw_value = row[metric]
            parsed = parse_metric(raw_value)

            if parsed is None:
                failure_rows.append({
                    "company_id": company_id,
                    "metric_type": metric,
                    "raw_value": raw_value,
                    "failure_reason": "Regex did not match"
                })
                continue

            period_years, value_pct = parsed

            parsed_rows.append({
                "company_id": company_id,
                "metric_type": metric,
                "period_years": period_years,
                "value_pct": value_pct
            })

    parsed_df = pd.DataFrame(
        parsed_rows,
        columns=[
            "company_id",
            "metric_type",
            "period_years",
            "value_pct"
        ]
    )

    failures_df = pd.DataFrame(
        failure_rows,
        columns=[
            "company_id",
            "metric_type",
            "raw_value",
            "failure_reason"
        ]
    )

    parsed_df.to_csv(PARSED_FILE, index=False)
    failures_df.to_csv(FAILURES_FILE, index=False)

    print()
    print("Parsing complete.")
    print(f"Parsed rows: {len(parsed_df)}")
    print(f"Parse failures: {len(failures_df)}")
    print(f"Saved: {PARSED_FILE}")
    print(f"Saved: {FAILURES_FILE}")

    print()
    print("Running 5-year CAGR cross-validation...")

    con = sqlite3.connect(DB_FILE)

    query = """
        SELECT
            company_id,
            year,
            revenue_cagr_5yr,
            pat_cagr_5yr,
            eps_cagr_5yr
        FROM financial_ratios
        WHERE year = 2024
    """

    ratios_df = pd.read_sql_query(query, con)
    con.close()

    comparison_rows = []

    cagr_mapping = {
        "compounded_sales_growth": "revenue_cagr_5yr",
        "compounded_profit_growth": "pat_cagr_5yr"
    }

    cagr_df = parsed_df[
        parsed_df["period_years"] == 5
    ].copy()

    for _, row in cagr_df.iterrows():
        metric = row["metric_type"]

        if metric not in cagr_mapping:
            continue

        ratio_column = cagr_mapping[metric]

        company_ratio = ratios_df[
            ratios_df["company_id"] == row["company_id"]
        ]

        if company_ratio.empty:
            comparison_rows.append({
                "company_id": row["company_id"],
                "metric_type": metric,
                "analysis_value_pct": row["value_pct"],
                "ratio_engine_value_pct": None,
                "divergence_pct": None,
                "review_flag": "No Ratio Engine value"
            })
            continue

        ratio_value = company_ratio.iloc[0][ratio_column]

        if pd.isna(ratio_value):
            comparison_rows.append({
                "company_id": row["company_id"],
                "metric_type": metric,
                "analysis_value_pct": row["value_pct"],
                "ratio_engine_value_pct": None,
                "divergence_pct": None,
                "review_flag": "No Ratio Engine value"
            })
            continue

        analysis_value = float(row["value_pct"])
        ratio_value = float(ratio_value)

        if ratio_value == 0:
            divergence = None
            flag = "Manual review"
        else:
            divergence = abs(
                analysis_value - ratio_value
            ) / abs(ratio_value) * 100

            flag = "Manual review" if divergence > 5 else "OK"

        comparison_rows.append({
            "company_id": row["company_id"],
            "metric_type": metric,
            "analysis_value_pct": analysis_value,
            "ratio_engine_value_pct": ratio_value,
            "divergence_pct": divergence,
            "review_flag": flag
        })

    comparison_df = pd.DataFrame(comparison_rows)

    comparison_file = os.path.join(
        OUTPUT_DIR,
        "cagr_cross_validation.csv"
    )

    comparison_df.to_csv(
        comparison_file,
        index=False
    )

    print()
    print("Cross-validation complete.")
    print(f"Comparison rows: {len(comparison_df)}")
    print(f"Saved: {comparison_file}")

    if not comparison_df.empty:
        print()
        print("Cross-validation results:")
        print(comparison_df.to_string(index=False))


if __name__ == "__main__":
    main()