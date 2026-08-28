import logging
import re
from pathlib import Path
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)

OUTPUT_PATH = Path("output/validation_failures.csv")


def _add_failure(
    failures: list[dict[str, Any]],
    rule_id: str,
    company_id: Any,
    year: Any,
    severity: str,
    message: str,
) -> None:
    failures.append(
        {
            "rule_id": rule_id,
            "company_id": company_id,
            "year": year,
            "severity": severity,
            "message": message,
        }
    )


def validate_companies(
    companies: pd.DataFrame,
    failures: list[dict[str, Any]],
) -> None:

    duplicates = companies[companies["id"].duplicated(keep=False)]

    for _, row in duplicates.iterrows():
        _add_failure(
            failures,
            "DQ-01",
            row.get("id"),
            None,
            "CRITICAL",
            f"Duplicate company primary key: {row['id']}",
        )

    for _, row in companies.iterrows():
        ticker = str(row.get("id", "")).strip().upper()

        if not 2 <= len(ticker) <= 12:
            _add_failure(
                failures,
                "DQ-08",
                ticker,
                None,
                "CRITICAL",
                f"Ticker length invalid: {ticker}",
            )

        if not re.fullmatch(r"[A-Z0-9&-]+", ticker):
            _add_failure(
                failures,
                "DQ-08",
                ticker,
                None,
                "CRITICAL",
                f"Invalid ticker format: {ticker}",
            )

def validate_annual_uniqueness(
    dataframe: pd.DataFrame,
    table_name: str,
    failures: list[dict[str, Any]],
) -> None:

    duplicates = dataframe[
        dataframe.duplicated(subset=["company_id", "year"], keep=False)
    ]

    for _, row in duplicates.iterrows():
        _add_failure(
            failures,
            "DQ-02",
            row.get("company_id"),
            row.get("year"),
            "WARNING",
            f"Duplicate company-year in {table_name}",
        )


def validate_fk(
    dataframe: pd.DataFrame,
    companies: pd.DataFrame,
    table_name: str,
    failures: list[dict[str, Any]],
) -> None:
    """Validate foreign-key integrity for company_id."""

    valid_companies = set(
        companies["id"]
        .dropna()
        .astype(str)
        .str.strip()
        .str.upper()
    )

    for _, row in dataframe.iterrows():
        company_id = str(row.get("company_id", "")).strip().upper()

        if company_id and company_id not in valid_companies:
            _add_failure(
                failures,
                "DQ-03",
                company_id,
                row.get("year"),
                "CRITICAL",
                f"Orphan company_id in {table_name}",
            )

            
def validate_profit_and_loss(
    pnl: pd.DataFrame,
    failures: list[dict[str, Any]],
) -> None:
    
    for _, row in pnl.iterrows():
        sales = pd.to_numeric(row.get("sales"), errors="coerce")
        operating_profit = pd.to_numeric(
            row.get("operating_profit"), errors="coerce"
        )
        source_opm = pd.to_numeric(
            row.get("opm_percentage"), errors="coerce"
        )

        if pd.notna(sales) and sales != 0 and pd.notna(operating_profit):
            calculated_opm = operating_profit / sales * 100

            if (
                pd.notna(source_opm)
                and abs(source_opm - calculated_opm) >= 1.0
            ):
                _add_failure(
                    failures,
                    "DQ-05",
                    row.get("company_id"),
                    row.get("year"),
                    "WARNING",
                    f"OPM mismatch: source={source_opm:.2f}, "
                    f"calculated={calculated_opm:.2f}",
                )
        if pd.notna(sales) and sales <= 0:
            _add_failure(
                failures,
                "DQ-06",
                row.get("company_id"),
                row.get("year"),
                "WARNING",
                f"Non-positive sales: {sales}",
            )


        tax = pd.to_numeric(row.get("tax_percentage"), errors="coerce")

        if pd.notna(tax) and not 0 <= tax <= 60:
            _add_failure(
                failures,
                "DQ-11",
                row.get("company_id"),
                row.get("year"),
                "WARNING",
                f"Tax percentage outside 0-60: {tax}",
            )

        dividend = pd.to_numeric(
            row.get("dividend_payout"), errors="coerce"
        )

        if pd.notna(dividend) and dividend > 200:
            _add_failure(
                failures,
                "DQ-12",
                row.get("company_id"),
                row.get("year"),
                "WARNING",
                f"Dividend payout above 200%: {dividend}",
            )

        net_profit = pd.to_numeric(
            row.get("net_profit"), errors="coerce"
        )
        eps = pd.to_numeric(row.get("eps"), errors="coerce")

        if (
            pd.notna(net_profit)
            and pd.notna(eps)
            and net_profit > 0
            and eps <= 0
        ):
            _add_failure(
                failures,
                "DQ-14",
                row.get("company_id"),
                row.get("year"),
                "WARNING",
                f"Positive net profit with non-positive EPS: {eps}",
            )


def validate_balance_sheet(
    balance_sheet: pd.DataFrame,
    failures: list[dict[str, Any]],
) -> None:

    for _, row in balance_sheet.iterrows():
        assets = pd.to_numeric(row.get("total_assets"), errors="coerce")
        liabilities = pd.to_numeric(
            row.get("total_liabilities"), errors="coerce"
        )

        if (
            pd.notna(assets)
            and pd.notna(liabilities)
            and assets != 0
        ):
            difference = abs(assets - liabilities) / abs(assets)

            if difference >= 0.01:
                _add_failure(
                    failures,
                    "DQ-04",
                    row.get("company_id"),
                    row.get("year"),
                    "WARNING",
                    f"Balance-sheet difference: {difference:.2%}",
                )

        fixed_assets = pd.to_numeric(
            row.get("fixed_assets"), errors="coerce"
        )

        if pd.notna(fixed_assets) and fixed_assets < 0:
            _add_failure(
                failures,
                "DQ-10",
                row.get("company_id"),
                row.get("year"),
                "WARNING",
                f"Negative fixed assets: {fixed_assets}",
            )

        if (
            pd.notna(assets)
            and pd.notna(liabilities)
            and assets != liabilities
        ):
            _add_failure(
                failures,
                "DQ-15",
                row.get("company_id"),
                row.get("year"),
                "INFO",
                "Total assets do not equal total liabilities.",
            )


def validate_cashflow(
    cashflow: pd.DataFrame,
    failures: list[dict[str, Any]],
) -> None:


    for _, row in cashflow.iterrows():
        operating = pd.to_numeric(
            row.get("operating_activity"), errors="coerce"
        )
        investing = pd.to_numeric(
            row.get("investing_activity"), errors="coerce"
        )
        financing = pd.to_numeric(
            row.get("financing_activity"), errors="coerce"
        )
        net_cash = pd.to_numeric(
            row.get("net_cash_flow"), errors="coerce"
        )

        if all(pd.notna(x) for x in [operating, investing, financing, net_cash]):
            calculated = operating + investing + financing

            if abs(net_cash - calculated) > 10:
                _add_failure(
                    failures,
                    "DQ-09",
                    row.get("company_id"),
                    row.get("year"),
                    "WARNING",
                    f"Net cash mismatch: source={net_cash}, "
                    f"calculated={calculated}",
                )

def validate_year_format(
    dataframes: dict[str, pd.DataFrame],
    failures: list[dict[str, Any]],
) -> None:
    for table_name, dataframe in dataframes.items():
        if "year" not in dataframe.columns:
            continue

        for _, row in dataframe.iterrows():
            year = row.get("year")
            if pd.isna(year):
                continue

            try:
                numeric_year = float(year)

                if (
                    not numeric_year.is_integer()
                    or not 1900 <= int(numeric_year) <= 2100
                ):
                    raise ValueError

            except (TypeError, ValueError):
                _add_failure(
                    failures,
                    "DQ-07",
                    row.get("company_id"),
                    year,
                    "CRITICAL",
                    f"Invalid year format in {table_name}: {year}",
                )
def validate_coverage(
    pnl: pd.DataFrame,
    balance_sheet: pd.DataFrame,
    cashflow: pd.DataFrame,
    failures: list[dict[str, Any]],
) -> None:

    for dataframe, table_name in [
        (pnl, "profitandloss"),
        (balance_sheet, "balancesheet"),
        (cashflow, "cashflow"),
    ]:
        coverage = dataframe.groupby("company_id")["year"].nunique()

        for company_id, years in coverage.items():
            if years < 5:
                _add_failure(
                    failures,
                    "DQ-16",
                    company_id,
                    None,
                    "WARNING",
                    f"{table_name} has only {years} years of coverage",
                )


def validate_all(
    companies: pd.DataFrame,
    profitandloss: pd.DataFrame,
    balancesheet: pd.DataFrame,
    cashflow: pd.DataFrame,
    documents: pd.DataFrame | None = None,
) -> pd.DataFrame:

    failures: list[dict[str, Any]] = []

    validate_companies(companies, failures)

    for dataframe, table_name in [
        (profitandloss, "profitandloss"),
        (balancesheet, "balancesheet"),
        (cashflow, "cashflow"),
    ]:
        validate_annual_uniqueness(dataframe, table_name, failures)
        validate_fk(dataframe, companies, table_name, failures)

    validate_profit_and_loss(profitandloss, failures)
    validate_balance_sheet(balancesheet, failures)
    validate_cashflow(cashflow, failures)

    validate_year_format(
        {
            "profitandloss": profitandloss,
            "balancesheet": balancesheet,
            "cashflow": cashflow,
        },
        failures,
    )

    validate_coverage(
        profitandloss,
        balancesheet,
        cashflow,
        failures,
    )

    result = pd.DataFrame(failures)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(OUTPUT_PATH, index=False)

    logger.info("Data-quality validation complete: %d failures", len(result))

    return result