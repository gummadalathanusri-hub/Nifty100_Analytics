from src.analytics.ratios import (
    debt_to_equity,
    high_leverage_flag,
    interest_coverage_ratio,
    icr_label,
    icr_warning_flag,
    net_debt,
    asset_turnover,
)


def test_debt_to_equity_normal():
    assert debt_to_equity(300, 500, 500) == 0.3


def test_debt_to_equity_debt_free():
    assert debt_to_equity(0, 500, 500) == 0


def test_debt_to_equity_negative_equity():
    assert debt_to_equity(300, 500, -600) is None


def test_interest_coverage_normal():
    assert interest_coverage_ratio(200, 50, 50) == 5


def test_interest_coverage_zero_interest():
    assert interest_coverage_ratio(200, 50, 0) is None


def test_icr_debt_free_label():
    icr = interest_coverage_ratio(200, 50, 0)
    assert icr_label(icr) == "Debt Free"


def test_high_debt_to_equity_flag():
    assert high_leverage_flag(6, "Industrials") is True


def test_financials_high_leverage_suppressed():
    assert high_leverage_flag(6, "Financials") is False