"""
Excel data loader for the Nifty 100 Analytics project.
"""

from pathlib import Path

import pandas as pd

from src.etl.normaliser import normalize_ticker, normalize_year


# Source files that contain a title row before the actual headers.
CORE_FILES = {
    "analysis.xlsx",
    "balancesheet.xlsx",
    "cashflow.xlsx",
    "companies.xlsx",
    "documents.xlsx",
    "profitandloss.xlsx",
    "prosandcons.xlsx",
}


def load_excel(file_path: str | Path) -> pd.DataFrame:
    """
    Load an Excel file and return a cleaned DataFrame.

    Core files have a descriptive title row followed by the header.
    Supplementary files have the header in the first row.
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"Excel file not found: {file_path}")

    # Core files: title row + header row.
    # Supplementary files: header is the first row.
    header_row = 1 if file_path.name.lower() in CORE_FILES else 0

    df = pd.read_excel(file_path, header=header_row)

    # Remove completely empty rows and columns.
    df = df.dropna(axis=0, how="all")
    df = df.dropna(axis=1, how="all")

    # Standardise column names.
    df.columns = [
        str(column).strip().lower().replace(" ", "_")
        for column in df.columns
    ]

    # Standardise ticker/company identifiers.
    for column in ("company_id", "ticker"):
        if column in df.columns:
            df[column] = df[column].apply(normalize_ticker)

    # Standardise year values.
    if "year" in df.columns:
        df["year"] = df["year"].apply(normalize_year)

    # Standardise stock-price dates.
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")

    return df


def load_raw_directory(directory: str | Path) -> dict[str, pd.DataFrame]:
    """
    Load every Excel file from a directory.

    Returns:
        Dictionary mapping filename to cleaned DataFrame.
    """
    directory = Path(directory)

    if not directory.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")

    files = sorted(directory.glob("*.xlsx"))

    return {
        file.name: load_excel(file)
        for file in files
    }