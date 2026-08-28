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
    """ROA = Net Profit / Total Assets × 100."""
    if total_assets == 0:
        return None

    return (net_profit / total_assets) * 100