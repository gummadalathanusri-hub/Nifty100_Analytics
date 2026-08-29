from typing import Optional


def net_profit_margin(
    net_profit: float,
    sales: float,
) -> Optional[float]:
    """Net Profit Margin = Net Profit / Sales × 100."""
    if sales == 0:
        return None

    return (net_profit / sales) * 100


def operating_profit_margin(
    operating_profit: float,
    sales: float,
) -> Optional[float]:
    """Operating Profit Margin = Operating Profit / Sales × 100."""
    if sales == 0:
        return None

    return (operating_profit / sales) * 100


def check_opm_difference(
    calculated_opm: Optional[float],
    source_opm: Optional[float],
) -> bool:
    """
    Check whether calculated OPM differs from source OPM
    by more than 1 percentage point.
    """
    if calculated_opm is None or source_opm is None:
        return False

    return abs(calculated_opm - source_opm) > 1


def return_on_equity(
    net_profit: float,
    equity_capital: float,
    reserves: float,
) -> Optional[float]:
    """
    ROE = Net Profit / (Equity Capital + Reserves) × 100.

    Return None when Equity + Reserves <= 0.
    """
    equity = equity_capital + reserves

    if equity <= 0:
        return None

    return (net_profit / equity) * 100


def return_on_capital_employed(
    ebit: float,
    equity_capital: float,
    reserves: float,
    borrowings: float,
) -> Optional[float]:
    """
    ROCE = EBIT / (Equity + Reserves + Borrowings) × 100.
    """
    capital_employed = (
        equity_capital
        + reserves
        + borrowings
    )

    if capital_employed <= 0:
        return None

    return (ebit / capital_employed) * 100


def return_on_assets(
    net_profit: float,
    total_assets: float,
) -> Optional[float]:
    if total_assets == 0:
        return None

    return (net_profit / total_assets) * 100

def debt_to_equity(
    borrowings: float,
    equity_capital: float,
    reserves: float,
) -> float:
    if borrowings == 0:
        return 0

    equity = equity_capital + reserves

    if equity <= 0:
        return None

    return borrowings / equity


def high_leverage_flag(
    debt_equity: float,
    broad_sector: str,
) -> bool:
    if debt_equity is None:
        return False

    if str(broad_sector).strip().lower() == "financials":
        return False

    return debt_equity > 5


def interest_coverage_ratio(
    operating_profit: float,
    other_income: float,
    interest: float,
) -> Optional[float]:

    if interest == 0:
        return None

    return (operating_profit + other_income) / interest


def icr_label(
    icr: Optional[float],
) -> Optional[str]:
    if icr is None:
        return "Debt Free"

    return None


def icr_warning_flag(
    icr: Optional[float],
) -> bool:
    if icr is None:
        return False

    return icr < 1.5


def net_debt(
    borrowings: float,
    investments: float,
) -> float:

    return borrowings - investments


def asset_turnover(
    sales: float,
    total_assets: float,
) -> Optional[float]:

    if total_assets == 0:
        return None

    return sales / total_assets