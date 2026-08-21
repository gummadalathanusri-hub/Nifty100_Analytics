from pathlib import Path

import pandas as pd


SEVERITY_CRITICAL = "CRITICAL"
SEVERITY_WARNING = "WARNING"


def create_failure(
    rule_id: str,
    rule_name: str,
    severity: str,
    message: str,
    table: str | None = None,
    record_id=None,
    company_id=None,
    year=None,
) -> dict:
    return {
        "rule_id": rule_id,
        "rule_name": rule_name,
        "severity": severity,
        "table": table,
        "record_id": record_id,
        "company_id": company_id,
        "year": year,
        "message": message,
    }


def check_pk_uniqueness(
    df: pd.DataFrame,
    table: str,
    pk_column: str,
) -> list[dict]:
    failures = []

    if pk_column not in df.columns:
        failures.append(
            create_failure(
                SEVERITY_CRITICAL,
                f"Missing primary-key column: {pk_column}",
                table=table,
            )
        )
        return failures

    null_rows = df[df[pk_column].isna()]

    for index in null_rows.index:
        failures.append(
            create_failure(
                SEVERITY_CRITICAL,
                f"NULL primary key in {pk_column}",
                table=table,
                record_id=index,
            )
        )

    duplicates = df[df[pk_column].duplicated(keep=False)]

    for index, row in duplicates.iterrows():
        failures.append(
            create_failure(
                SEVERITY_CRITICAL,
                f"Duplicate primary key: {row[pk_column]}",
                table=table,
                record_id=row[pk_column],
            )
        )

    return failures


def check_company_year_uniqueness(
    df: pd.DataFrame,
    table: str,
) -> list[dict]:
    failures = []

    required = {"company_id", "year"}

    if not required.issubset(df.columns):
        return [
            create_failure(
                SEVERITY_CRITICAL,
                "Missing company_id or year column.",
                table=table,
            )
        ]

    duplicate_mask = df.duplicated(
        subset=["company_id", "year"],
        keep=False,
    )

    for index, row in df[duplicate_mask].iterrows():
        failures.append(
            create_failure(
                SEVERITY_CRITICAL,
                f"Duplicate company-year: "
                f"{row['company_id']} / {row['year']}",
                table=table,
                record_id=row.get("id"),
                company_id=row["company_id"],
                year=row["year"],
            )
        )

    return failures


def check_fk_integrity(
    child_df: pd.DataFrame,
    parent_df: pd.DataFrame,
    child_table: str,
    parent_table: str,
    key: str = "company_id",
) -> list[dict]:
    failures = []

    if key not in child_df.columns or key not in parent_df.columns:
        failures.append(
            create_failure(
                SEVERITY_CRITICAL,
                f"Missing FK column: {key}",
                table=child_table,
            )
        )
        return failures

    valid_keys = set(parent_df[key].dropna())

    invalid = child_df[
        child_df[key].notna()
        & ~child_df[key].isin(valid_keys)
    ]

    for index, row in invalid.iterrows():
        failures.append(
            create_failure(
                SEVERITY_CRITICAL,
                f"Unknown company_id: {row[key]} "
                f"(expected in {parent_table})",
                table=child_table,
                record_id=row.get("id"),
                company_id=row[key],
                year=row.get("year"),
            )
        )

    return failures


def validate_dataframe(
    df: pd.DataFrame,
    table: str,
    pk_column: str = "id",
) -> list[dict]:
    failures = []

    failures.extend(
        check_pk_uniqueness(
            df,
            table,
            pk_column,
        )
    )

    if {"company_id", "year"}.issubset(df.columns):
        failures.extend(
            check_company_year_uniqueness(
                df,
                table,
            )
        )

    return failures


def save_failures(
    failures: list[dict],
    output_path: str | Path = "output/validation_failures.csv",
) -> pd.DataFrame:
    output_path = Path(output_path)
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    columns = [
        "rule_id",
        "rule_name",
        "severity",
        "table",
        "record_id",
        "company_id",
        "year",
        "message",
    ]

    result = pd.DataFrame(failures, columns=columns)
    result.to_csv(output_path, index=False)

    return result