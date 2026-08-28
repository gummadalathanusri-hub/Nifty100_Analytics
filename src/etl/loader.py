from pathlib import Path
from datetime import datetime
import sqlite3

import pandas as pd

from src.etl.normaliser import normalize_ticker, normalize_year


CORE_FILES = {
    "analysis.xlsx",
    "balancesheet.xlsx",
    "cashflow.xlsx",
    "companies.xlsx",
    "documents.xlsx",
    "profitandloss.xlsx",
    "prosandcons.xlsx",
}


TABLE_LOAD_ORDER = [
    ("companies.xlsx", "companies"),
    ("profitandloss.xlsx", "profitandloss"),
    ("balancesheet.xlsx", "balancesheet"),
    ("cashflow.xlsx", "cashflow"),
    ("analysis.xlsx", "analysis"),
    ("documents.xlsx", "documents"),
    ("prosandcons.xlsx", "prosandcons"),
    ("sectors.xlsx", "sectors"),
    ("market_cap.xlsx", "market_cap"),
    ("financial_ratios.xlsx", "financial_ratios"),
    ("peer_groups.xlsx", "peer_groups"),
    ("stock_prices.xlsx", "stock_prices"),
]


def load_excel(file_path: str | Path) -> pd.DataFrame:

    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(
            f"Excel file not found: {file_path}"
        )

    header_row = (
        1 if file_path.name.lower() in CORE_FILES else 0
    )

    df = pd.read_excel(
        file_path,
        header=header_row,
    )

    df = df.dropna(
        axis=0,
        how="all",
    )

    df = df.dropna(
        axis=1,
        how="all",
    )

    df.columns = [
        str(column)
        .strip()
        .lower()
        .replace(" ", "_")
        for column in df.columns
    ]
    for column in ("company_id", "ticker"):

        if column in df.columns:

            df[column] = df[column].apply(
                normalize_ticker
            )

    if "year" in df.columns:

        df["year"] = df["year"].apply(
            normalize_year
        )

    if "date" in df.columns:

        df["date"] = pd.to_datetime(
            df["date"],
            errors="coerce"
        )

    return df

def load_raw_directory(
    directory: str | Path,
) -> dict[str, pd.DataFrame]:

    directory = Path(directory)

    if not directory.exists():
        raise FileNotFoundError(
            f"Directory not found: {directory}"
        )

    files = sorted(
        directory.glob("*.xlsx")
    )

    return {
        file.name: load_excel(file)
        for file in files
    }


def load_all_to_sqlite(
    source_directory: str | Path,
    db_path: str | Path = "nifty100.db",
    audit_path: str | Path = "output/load_audit.csv",
) -> pd.DataFrame:

    source_directory = Path(
        source_directory
    )

    db_path = Path(
        db_path
    )

    audit_path = Path(
        audit_path
    )

    raw_data = load_raw_directory(
        source_directory / "raw"
    )

    supporting_data = load_raw_directory(
        source_directory / "supporting"
    )

    data = {
        **raw_data,
        **supporting_data,
    }

    audit_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    db_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    connection = sqlite3.connect(
        db_path
    )

    audit_rows = []

    try:
        connection.execute(
            "PRAGMA foreign_keys = ON"
        )

        schema_path = Path(
            "db/schema.sql"
        )

        if not schema_path.exists():

            raise FileNotFoundError(
                f"Schema file not found: {schema_path}"
            )

        schema_sql = schema_path.read_text(
            encoding="utf-8"
        )

        connection.executescript(
            schema_sql
        )
        for filename, table_name in TABLE_LOAD_ORDER:

            started_at = datetime.now()
            if filename not in data:

                audit_rows.append({
                    "table_name": table_name,
                    "source_file": filename,
                    "source_rows": 0,
                    "loaded_rows": 0,
                    "rejected_rows": 0,
                    "status": "MISSING",
                    "message": "Source file not found",
                    "loaded_at": started_at,
                })

                continue

            dataframe = data[
                filename
            ].copy()

            source_rows = len(
                dataframe
            )

            rejected_rows = 0

            if table_name != "companies" and "company_id" in dataframe.columns:
                companies_df = data["companies.xlsx"]
                valid_company_ids = set(
                    companies_df["id"]
                    .dropna()
                    .astype(str)
                    .str.strip()
                    .str.upper()
                    )
                normalized_ids = (
                    dataframe["company_id"]
                    .fillna("")
                    .astype(str)
                    .str.strip()
                    .str.upper()
                    )
                valid_mask = normalized_ids.isin(valid_company_ids)

                rejected_rows += int((~valid_mask).sum())

                dataframe = dataframe.loc[valid_mask].copy()
                if table_name in {
                    "profitandloss",
                    "balancesheet",
                    "cashflow",
                    "documents",
                    "financial_ratios",
                    "market_cap",
}:
                     if "company_id" in dataframe.columns and "year" in dataframe.columns:
                         duplicate_subset = ["company_id", "year"]
                     elif table_name == "stock_prices":
                         if "company_id" in dataframe.columns and "date" in dataframe.columns:
                             duplicate_subset = ["company_id", "date"]
                         elif table_name == "sectors":
                             if "company_id" in dataframe.columns:
                                 duplicate_subset = ["company_id"]
                             elif table_name == "peer_groups":
                                 if "company_id" in dataframe.columns:
                                     duplicate_subset = ["company_id", "peer_group_name"]
                                 elif table_name == "prosandcons":
                                     if "company_id" in dataframe.columns:
                                         duplicate_subset = ["company_id"]
                                     elif table_name == "analysis":
                                         if "company_id" in dataframe.columns:
                                             duplicate_subset = ["company_id"]
                                             if duplicate_subset:
                                                 before_count = len(dataframe)
                                                 dataframe = dataframe.drop_duplicates(
                                                     subset=duplicate_subset,
                                                     keep="first",
                                                     )
                                                 rejected_rows += before_count - len(dataframe)


                valid_company_ids = set(
                    companies_df["id"]
                    .dropna()
                    .apply(normalize_ticker)
                    .dropna()
                )

                normalized_ids = (
                    dataframe["company_id"]
                    .apply(normalize_ticker)
                )

                valid_mask = (
                    normalized_ids
                    .isin(valid_company_ids)
                )

                rejected_rows += int(
                    (~valid_mask).sum()
                )

                dataframe = dataframe.loc[
                    valid_mask
                ].copy()

                dataframe["company_id"] = (
                    normalized_ids.loc[
                        valid_mask
                    ]
                )
                if (
                    table_name in {
                    "profitandloss",
                    "balancesheet",
                    "cashflow",
                    "documents",
                    "financial_ratios",
                    "market_cap",
                }
                and "company_id" in dataframe.columns
                and "year" in dataframe.columns
            ):
                    before_dedup = len(
                    dataframe
                )
                    before_dedup = len(dataframe)
                    if table_name in {
                        "profitandloss",
                        "balancesheet",
                        "cashflow",
                        "documents",
                        "financial_ratios",
                        "market_cap",
                        }:
                        if "company_id" in dataframe.columns and "year" in dataframe.columns:
                            dataframe = dataframe.drop_duplicates(
                                subset=["company_id", "year"],
                                keep="first",
                                )
                        elif table_name == "stock_prices":
                            if "company_id" in dataframe.columns and "date" in dataframe.columns:
                                dataframe = dataframe.drop_duplicates(
                                    subset=["company_id", "date"],
                                    keep="first",
                                    )
                            elif table_name == "sectors":
                                if "company_id" in dataframe.columns:
                                    dataframe = dataframe.drop_duplicates(
                                        subset=["company_id"],
                                        keep="first",
                                        )
                                elif table_name == "peer_groups":
                                    if "company_id" in dataframe.columns and "peer_group_name" in dataframe.columns:
                                        dataframe = dataframe.drop_duplicates(
                                            subset=["company_id", "peer_group_name"],
                                            keep="first",
                                            )
                                    elif table_name == "analysis":
                                        if "company_id" in dataframe.columns:
                                            dataframe = dataframe.drop_duplicates(
                                                subset=["company_id"],
                                                keep="first",
                                                )
                                        elif table_name == "prosandcons":
                                            if "company_id" in dataframe.columns:
                                                dataframe = dataframe.drop_duplicates(
                                                    subset=["company_id"],
                                                    keep="first",
                                                    )
                                            else:
                                                dataframe = dataframe.drop_duplicates(
                                                    keep="first"
                                                    )
                                                duplicate_rows = before_dedup - len(dataframe)
                                                if duplicate_rows < 0:
                                                    duplicate_rows = 0
                                                    rejected_rows += duplicate_rows

            table_columns = [
                row[1]
                for row in connection.execute(
                    f"PRAGMA table_info({table_name})"
                ).fetchall()
            ]
            dataframe = dataframe[
                [
                    column
                    for column in table_columns
                    if column in dataframe.columns
                ]
            ]
            try:

                dataframe.to_sql(
                    table_name,
                    connection,
                    if_exists="append",
                    index=False,
                )

                loaded_rows = len(
                    dataframe
                )

                audit_rows.append({
                    "table_name": table_name,
                    "source_file": filename,
                    "source_rows": source_rows,
                    "loaded_rows": loaded_rows,
                    "rejected_rows": rejected_rows,
                    "status": "SUCCESS",
                    "message": "",
                    "loaded_at": started_at,
                })

            except Exception as exc:

                audit_rows.append({
                    "table_name": table_name,
                    "source_file": filename,
                    "source_rows": source_rows,
                    "loaded_rows": 0,
                    "rejected_rows": source_rows,
                    "status": "FAILED",
                    "message": str(exc),
                    "loaded_at": started_at,
                })

                connection.rollback()

                raise

        connection.commit()

    finally:

        connection.close()
    audit = pd.DataFrame(
        audit_rows
    )

    audit.to_csv(
        audit_path,
        index=False,
    )

    return audit