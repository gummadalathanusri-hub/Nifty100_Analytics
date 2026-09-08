from pathlib import Path
import sqlite3
import pandas as pd

DB_PATH = Path("nifty100.db")
PEER_GROUPS_PATH = Path("data/supporting/peer_groups.xlsx")

METRICS = {
    "ROE": "return_on_equity_pct",
    "ROCE": "roce_pct",
    "Net Profit Margin": "net_profit_margin_pct",
    "D/E": "debt_to_equity",
    "FCF": "free_cash_flow_cr",
    "PAT CAGR 5yr": "pat_cagr_5yr",
    "Revenue CAGR 5yr": "revenue_cagr_5yr",
    "EPS CAGR 5yr": "eps_cagr_5yr",
    "Interest Coverage": "interest_coverage",
    "Asset Turnover": "asset_turnover",
}


def normalize_company_id(value) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip().upper()


def load_peer_groups() -> pd.DataFrame:
    peer_groups = pd.read_excel(PEER_GROUPS_PATH)

    peer_groups.columns = [
        str(column).strip().lower().replace(" ", "_")
        for column in peer_groups.columns
    ]

    required_columns = ["peer_group_name", "company_id"]

    missing_columns = [
        column
        for column in required_columns
        if column not in peer_groups.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing columns in peer_groups.xlsx: {missing_columns}"
        )

    peer_groups["company_id"] = (
        peer_groups["company_id"]
        .apply(normalize_company_id)
    )

    peer_groups["peer_group_name"] = (
        peer_groups["peer_group_name"]
        .astype(str)
        .str.strip()
    )

    return peer_groups[
        ["company_id", "peer_group_name"]
    ].drop_duplicates()


def load_financial_ratios(connection: sqlite3.Connection) -> pd.DataFrame:
    financial_ratios = pd.read_sql_query(
        "SELECT * FROM financial_ratios",
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

    financial_ratios["company_id"] = (
        financial_ratios["company_id"]
        .apply(normalize_company_id)
    )

    profit_loss["company_id"] = (
        profit_loss["company_id"]
        .apply(normalize_company_id)
    )

    balance_sheet["company_id"] = (
        balance_sheet["company_id"]
        .apply(normalize_company_id)
    )

    balance_sheet["capital_employed"] = (
        pd.to_numeric(balance_sheet["equity_capital"], errors="coerce")
        + pd.to_numeric(balance_sheet["reserves"], errors="coerce")
        + pd.to_numeric(balance_sheet["borrowings"], errors="coerce")
    )

    profit_loss["operating_profit"] = pd.to_numeric(
        profit_loss["operating_profit"],
        errors="coerce",
    )

    balance_sheet["capital_employed"] = pd.to_numeric(
        balance_sheet["capital_employed"],
        errors="coerce",
    )

    roce_data = profit_loss.merge(
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

    roce_data["roce_pct"] = (
        roce_data["operating_profit"]
        / roce_data["capital_employed"]
        * 100
    )

    roce_data = roce_data[
        [
            "company_id",
            "year",
            "roce_pct",
        ]
    ]

    financial_ratios = financial_ratios.merge(
        roce_data,
        on=["company_id", "year"],
        how="left",
    )

    return financial_ratios


def calculate_peer_percentiles(
    financial_ratios: pd.DataFrame,
    peer_groups: pd.DataFrame,
) -> pd.DataFrame:
    merged = financial_ratios.merge(
        peer_groups,
        on="company_id",
        how="left",
    )

    merged["peer_group_name"] = merged["peer_group_name"].fillna(
        "No peer group assigned"
    )

    records = []

    for metric_name, column_name in METRICS.items():
        if column_name not in merged.columns:
            continue

        metric_data = merged[
            [
                "company_id",
                "peer_group_name",
                "year",
                column_name,
            ]
        ].copy()

        metric_data = metric_data.rename(
            columns={column_name: "value"}
        )

        metric_data["value"] = pd.to_numeric(
            metric_data["value"],
            errors="coerce",
        )

        valid = metric_data[
            metric_data["value"].notna()
            & (
                metric_data["peer_group_name"]
                != "No peer group assigned"
            )
        ].copy()

        if valid.empty:
            continue

        valid["percentile_rank"] = (
            valid.groupby("peer_group_name")["value"]
            .rank(method="min", pct=True)
        )

        if metric_name == "D/E":
            valid["percentile_rank"] = (
                1 - valid["percentile_rank"]
            )

        valid["metric"] = metric_name

        records.append(
            valid[
                [
                    "company_id",
                    "peer_group_name",
                    "metric",
                    "value",
                    "percentile_rank",
                    "year",
                ]
            ]
        )

    if not records:
        return pd.DataFrame(
            columns=[
                "company_id",
                "peer_group_name",
                "metric",
                "value",
                "percentile_rank",
                "year",
            ]
        )

    result = pd.concat(
        records,
        ignore_index=True,
    )

    result["percentile_rank"] = (
        result["percentile_rank"] * 100
    ).round(2)

    return result


def create_table(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS peer_percentiles (
            company_id TEXT NOT NULL,
            peer_group_name TEXT NOT NULL,
            metric TEXT NOT NULL,
            value REAL,
            percentile_rank REAL,
            year INTEGER
        )
        """
    )

    connection.commit()


def save_peer_percentiles(
    result: pd.DataFrame,
    connection: sqlite3.Connection,
) -> None:
    connection.execute(
        "DELETE FROM peer_percentiles"
    )

    result.to_sql(
        "peer_percentiles",
        connection,
        if_exists="append",
        index=False,
    )

    connection.commit()


def main() -> None:
    connection = sqlite3.connect(DB_PATH)

    try:
        financial_ratios = load_financial_ratios(
            connection
        )

        peer_groups = load_peer_groups()

        result = calculate_peer_percentiles(
            financial_ratios,
            peer_groups,
        )

        create_table(connection)

        save_peer_percentiles(
            result,
            connection,
        )

        print("Day 18 completed")
        print(f"Rows inserted: {len(result)}")
        print(
            f"Companies: "
            f"{result['company_id'].nunique()}"
        )
        print(
            f"Peer groups: "
            f"{result['peer_group_name'].nunique()}"
        )
        print(
            f"Metrics: "
            f"{result['metric'].nunique()}"
        )

    finally:
        connection.close()


if __name__ == "__main__":
    main()