from src.analytics.cashflow_kpis import (
    free_cash_flow,
    cfo_quality_score,
    cfo_quality_label,
    capex_intensity,
    capex_intensity_label,
    fcf_conversion_rate,
    capital_allocation_pattern,
)


def test_free_cash_flow():
    assert free_cash_flow(100, -40) == 60


def test_free_cash_flow_negative():
    assert free_cash_flow(20, -50) == -30


def test_cfo_quality_score():
    assert cfo_quality_score(120, 100) == 1.2


def test_cfo_quality_zero_pat():
    assert cfo_quality_score(100, 0) is None


def test_cfo_quality_labels():
    assert cfo_quality_label(1.2) == "High Quality"
    assert cfo_quality_label(0.75) == "Moderate"
    assert cfo_quality_label(0.3) == "Accrual Risk"


def test_capex_intensity():
    assert capex_intensity(-50, 1000) == 5.0


def test_capex_intensity_labels():
    assert capex_intensity_label(2.5) == "Asset Light"
    assert capex_intensity_label(5.0) == "Moderate"
    assert capex_intensity_label(10.0) == "Capital Intensive"


def test_fcf_conversion_rate():
    assert fcf_conversion_rate(60, 100) == 60.0


def test_fcf_conversion_zero_operating_profit():
    assert fcf_conversion_rate(60, 0) is None


def test_reinvestor_pattern():
    assert capital_allocation_pattern(100, -50, -20) == "Reinvestor"


def test_shareholder_returns_pattern():
    assert (
        capital_allocation_pattern(150, -50, -20, 1.5)
        == "Shareholder Returns"
    )


def test_liquidating_assets_pattern():
    assert capital_allocation_pattern(100, 50, -20) == "Liquidating Assets"


def test_distress_signal_pattern():
    assert capital_allocation_pattern(-100, 50, 20) == "Distress Signal"


def test_growth_funded_by_debt_pattern():
    assert capital_allocation_pattern(-100, -50, 20) == "Growth Funded by Debt"


def test_cash_accumulator_pattern():
    assert capital_allocation_pattern(100, 50, 20) == "Cash Accumulator"


def test_pre_revenue_pattern():
    assert capital_allocation_pattern(-100, -50, -20) == "Pre-Revenue"


def test_mixed_pattern():
    assert capital_allocation_pattern(100, -50, 20) == "Mixed"