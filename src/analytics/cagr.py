from typing import Optional, Tuple

import pandas as pd

def calculate_cagr(
    start: Optional[float],
    end: Optional[float],
    years: int,
) -> Tuple[Optional[float], Optional[str]]:
    """
    Calculate CAGR and return (value, flag).

    CAGR = ((end / start) ** (1 / years) - 1) * 100
    """

    if years <= 0:
        return None, "INSUFFICIENT"

    if start is None or end is None:
        return None, "INSUFFICIENT"

    if start == 0:
        return None, "ZERO_BASE"

    if start > 0 and end > 0:
        cagr = ((end / start) ** (1 / years) - 1) * 100
        return cagr, None

    if start > 0 and end < 0:
        return None, "DECLINE_TO_LOSS"

    if start < 0 and end > 0:
        return None, "TURNAROUND"

    if start < 0 and end < 0:
        return None, "BOTH_NEGATIVE"

    return None, "INSUFFICIENT"

def calculate_window_cagr(
    values,
    window_years: int,
):
    """
    Calculate CAGR using a year-based window.

    Returns:
        (cagr_value, flag)
    """

    if values is None or len(values) < window_years + 1:
        return None, "INSUFFICIENT"

    values = sorted(values, key=lambda x: x[0])

    start_year, start_value = values[-(window_years + 1)]
    end_year, end_value = values[-1]

    if end_year - start_year < window_years:
        return None, "INSUFFICIENT"

    return calculate_cagr(
        start_value,
        end_value,
        window_years,
    )

def calculate_metric_cagrs(
    dataframe,
    value_column: str,
    windows=(3, 5, 10),
):
    """
    Calculate 3-year, 5-year and 10-year CAGR values
    for each company.

    Returns one row per company.
    """

    required_columns = {"company_id", "year", value_column}

    missing = required_columns - set(dataframe.columns)

    if missing:
        raise ValueError(
            f"Missing required columns: {sorted(missing)}"
        )

    dataframe = dataframe[
        ["company_id", "year", value_column]
    ].copy()

    dataframe = dataframe.dropna(
        subset=["company_id", "year"]
    )

    dataframe["year"] = dataframe["year"].astype(int)

    results = []

    for company_id, group in dataframe.groupby("company_id"):

        group = (
            group
            .drop_duplicates(subset=["year"])
            .sort_values("year")
        )

        values = list(
            zip(
                group["year"],
                group[value_column],
            )
        )

        latest_year = int(group["year"].max())

        result = {
            "company_id": company_id,
            "year": latest_year,
        }

        for window in windows:

            value, flag = calculate_window_cagr(
                values,
                window,
            )

            result[
                f"{value_column}_cagr_{window}yr"
            ] = value

            result[
                f"{value_column}_cagr_{window}yr_flag"
            ] = flag

        results.append(result)

    return pd.DataFrame(results)