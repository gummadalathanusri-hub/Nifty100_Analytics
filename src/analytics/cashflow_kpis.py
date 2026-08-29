from __future__ import annotations

from typing import Optional


def free_cash_flow(
    operating_activity: float | None,
    investing_activity: float | None,
) -> Optional[float]:
    if operating_activity is None or investing_activity is None:
        return None

    return operating_activity + investing_activity


def cfo_quality_score(
    cfo: float | None,
    pat: float | None,
) -> Optional[float]:
    if cfo is None or pat is None or pat == 0:
        return None

    return cfo / pat


def cfo_quality_label(
    score: float | None,
) -> Optional[str]:
    if score is None:
        return None

    if score > 1.0:
        return "High Quality"
    elif score >= 0.5:
        return "Moderate"
    else:
        return "Accrual Risk"


def capex_intensity(
    investing_activity: float | None,
    sales: float | None,
) -> Optional[float]:
    if investing_activity is None or sales is None or sales == 0:
        return None

    return abs(investing_activity) / sales * 100


def capex_intensity_label(
    intensity: float | None,
) -> Optional[str]:
    if intensity is None:
        return None

    if intensity < 3:
        return "Asset Light"
    elif intensity <= 8:
        return "Moderate"
    else:
        return "Capital Intensive"


def fcf_conversion_rate(
    fcf: float | None,
    operating_profit: float | None,
) -> Optional[float]:
    if fcf is None or operating_profit is None or operating_profit == 0:
        return None

    return fcf / operating_profit * 100


def cash_flow_sign(value: float | None) -> str:
    if value is None:
        return "0"

    if value > 0:
        return "+"
    elif value < 0:
        return "-"
    else:
        return "0"


def capital_allocation_pattern(
    cfo: float | None,
    cfi: float | None,
    cff: float | None,
    cfo_pat_ratio: float | None = None,
) -> str:
    signs = (
        cash_flow_sign(cfo),
        cash_flow_sign(cfi),
        cash_flow_sign(cff),
    )

    if signs == ("+", "-", "-"):
        if cfo_pat_ratio is not None and cfo_pat_ratio > 1.0:
            return "Shareholder Returns"
        return "Reinvestor"

    if signs == ("+", "+", "-"):
        return "Liquidating Assets"

    if signs == ("-", "+", "+"):
        return "Distress Signal"

    if signs == ("-", "-", "+"):
        return "Growth Funded by Debt"

    if signs == ("+", "+", "+"):
        return "Cash Accumulator"

    if signs == ("-", "-", "-"):
        return "Pre-Revenue"

    if signs == ("+", "-", "+"):
        return "Mixed"

    return "Mixed"