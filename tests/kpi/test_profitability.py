from src.analytics.ratios import (
    net_profit_margin,
    operating_profit_margin,
    check_opm_difference,
    return_on_equity,
    return_on_capital_employed,
    return_on_assets,
)


def test_net_profit_margin_normal():
    assert net_profit_margin(200, 1000) == 20


def test_net_profit_margin_zero_sales():
    assert net_profit_margin(200, 0) is None


def test_operating_profit_margin_normal():
    assert operating_profit_margin(150, 1000) == 15


def test_opm_cross_check_mismatch():
    calculated = operating_profit_margin(150, 1000)

    assert check_opm_difference(
        calculated,
        12
    ) is True


def test_opm_cross_check_within_tolerance():
    calculated = operating_profit_margin(150, 1000)

    assert check_opm_difference(
        calculated,
        14.5
    ) is False


def test_roe_negative_equity():
    assert return_on_equity(
        100,
        50,
        -100
    ) is None


def test_roce_normal():
    assert return_on_capital_employed(
        200,
        500,
        300,
        200
    ) == 20


def test_roa_zero_assets():
    assert return_on_assets(
        100,
        0
    ) is None