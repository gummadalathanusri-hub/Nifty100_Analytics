from pathlib import Path
import sqlite3

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


DB_PATH = Path("nifty100.db")
OUTPUT_DIR = Path("reports/radar_charts")

METRICS = [
    "ROE",
    "ROCE",
    "NPM",
    "D/E",
    "FCF Score",
    "PAT CAGR 5yr",
    "Revenue CAGR 5yr",
    "Composite Score",
]


def load_data():
    connection = sqlite3.connect(DB_PATH)

    financial_ratios = pd.read_sql_query(
        """
        SELECT
            company_id,
            year,
            net_profit_margin_pct,
            return_on_equity_pct,
            debt_to_equity,
            free_cash_flow_cr,
            pat_cagr_5yr,
            revenue_cagr_5yr,
            composite_quality_score
        FROM financial_ratios
        """,
        connection,
    )

    profit_loss = pd.read_sql_query(
        """
        SELECT
            company_id,
            year,
            operating_profit
        FROM profitandloss
        """,
        connection,
    )

    balance_sheet = pd.read_sql_query(
        """
        SELECT
            company_id,
            year,
            equity_capital,
            reserves,
            borrowings
        FROM balancesheet
        """,
        connection,
    )

    peer_groups = pd.read_sql_query(
        """
        SELECT
            company_id,
            peer_group_name
        FROM peer_percentiles
        GROUP BY company_id, peer_group_name
        """,
        connection,
    )

    connection.close()

    balance_sheet["capital_employed"] = (
        balance_sheet["equity_capital"]
        + balance_sheet["reserves"]
        + balance_sheet["borrowings"]
    )

    balance_sheet["roce_pct"] = np.where(
        balance_sheet["capital_employed"] != 0,
        balance_sheet["operating_profit"]
        if "operating_profit" in balance_sheet.columns
        else 0,
        np.nan,
    )

    roce = profit_loss.merge(
        balance_sheet[
            [
                "company_id",
                "year",
                "capital_employed",
            ]
        ],
        on=["company_id", "year"],
        how="left",
    )

    roce["roce_pct"] = np.where(
        roce["capital_employed"] != 0,
        roce["operating_profit"] / roce["capital_employed"] * 100,
        np.nan,
    )

    roce = roce[
        [
            "company_id",
            "year",
            "roce_pct",
        ]
    ]

    financial_ratios = financial_ratios.merge(
        roce,
        on=["company_id", "year"],
        how="left",
    )

    financial_ratios = financial_ratios.sort_values(
        ["company_id", "year"]
    )

    latest = financial_ratios.groupby(
        "company_id",
        as_index=False,
    ).tail(1)

    latest = latest.merge(
        peer_groups,
        on="company_id",
        how="left",
    )

    return latest


def normalize_series(series):
    series = pd.to_numeric(series, errors="coerce")

    if series.notna().sum() == 0:
        return pd.Series(50.0, index=series.index)

    minimum = series.min()
    maximum = series.max()

    if pd.isna(minimum) or pd.isna(maximum) or minimum == maximum:
        return pd.Series(50.0, index=series.index)

    return ((series - minimum) / (maximum - minimum) * 100).fillna(50)


def prepare_metrics(data):
    result = pd.DataFrame(index=data.index)

    result["ROE"] = normalize_series(data["return_on_equity_pct"])
    result["ROCE"] = normalize_series(data["roce_pct"])
    result["NPM"] = normalize_series(data["net_profit_margin_pct"])

    de = pd.to_numeric(data["debt_to_equity"], errors="coerce")
    result["D/E"] = normalize_series(-de)

    result["FCF Score"] = normalize_series(data["free_cash_flow_cr"])
    result["PAT CAGR 5yr"] = normalize_series(data["pat_cagr_5yr"])
    result["Revenue CAGR 5yr"] = normalize_series(
        data["revenue_cagr_5yr"]
    )
    result["Composite Score"] = pd.to_numeric(
        data["composite_quality_score"],
        errors="coerce",
    ).fillna(50)

    return result.clip(0, 100)


def radar_chart(company_id, company_values, peer_average, output_path):
    values = company_values[METRICS].astype(float).tolist()
    average_values = peer_average[METRICS].astype(float).tolist()

    angles = np.linspace(
        0,
        2 * np.pi,
        len(METRICS),
        endpoint=False,
    ).tolist()

    values += values[:1]
    average_values += average_values[:1]
    angles += angles[:1]

    figure, axis = plt.subplots(
        figsize=(9, 9),
        subplot_kw={"polar": True},
    )

    axis.plot(
        angles,
        values,
        linewidth=2,
        label=str(company_id),
    )
    axis.fill(
        angles,
        values,
        alpha=0.25,
    )

    axis.plot(
        angles,
        average_values,
        linestyle="--",
        linewidth=2,
        label="Peer Group Average",
    )

    axis.set_xticks(angles[:-1])
    axis.set_xticklabels(METRICS)
    axis.set_ylim(0, 100)
    axis.set_title(
        f"{company_id} - Peer Radar",
        pad=20,
    )
    axis.legend(
        loc="upper right",
        bbox_to_anchor=(1.25, 1.15),
    )

    figure.tight_layout()
    figure.savefig(
        output_path,
        dpi=150,
        bbox_inches="tight",
    )
    plt.close(figure)


def standalone_chart(
    company_id,
    company_values,
    nifty_average,
    output_path,
):
    value = float(company_values["Composite Score"])
    benchmark = float(nifty_average["Composite Score"])

    figure, axis = plt.subplots(figsize=(8, 5))

    axis.bar(
        ["Composite Score"],
        [value],
        width=0.5,
    )

    axis.axhline(
        benchmark,
        linestyle="--",
        linewidth=2,
        label="Nifty 100 Average",
    )

    axis.set_ylim(0, 100)
    axis.set_ylabel("Score")
    axis.set_title(f"{company_id} - Nifty 100 Reference")
    axis.legend()

    figure.tight_layout()
    figure.savefig(
        output_path,
        dpi=150,
        bbox_inches="tight",
    )
    plt.close(figure)


def generate_radar_charts():
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    data = load_data()
    metrics = prepare_metrics(data)

    data = data.reset_index(drop=True)
    metrics = metrics.reset_index(drop=True)

    combined = pd.concat(
        [
            data[["company_id", "peer_group_name"]],
            metrics,
        ],
        axis=1,
    )

    nifty_average = combined[METRICS].mean()

    for company_id, company_data in combined.groupby("company_id"):
        company_row = company_data.iloc[0]
        peer_group = company_row["peer_group_name"]

        output_path = OUTPUT_DIR / f"{company_id}_radar.png"

        if pd.isna(peer_group) or str(peer_group).strip() == "":
            standalone_chart(
                company_id,
                company_row,
                nifty_average,
                output_path,
            )
            continue

        peer_data = combined[
            combined["peer_group_name"] == peer_group
        ]

        peer_average = peer_data[METRICS].mean()

        radar_chart(
            company_id,
            company_row,
            peer_average,
            output_path,
        )

    print("Day 19 completed")
    print(f"Charts generated: {len(list(OUTPUT_DIR.glob('*.png')))}")
    print(f"Output directory: {OUTPUT_DIR}")


if __name__ == "__main__":
    generate_radar_charts()