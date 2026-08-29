from src.analytics.cagr import (
    calculate_cagr,
    calculate_window_cagr,
)

def test_normal_cagr():
    value, flag = calculate_cagr(100, 121, 2)

    assert abs(value - 10.0) < 0.01
    assert flag is None


def test_zero_base():
    value, flag = calculate_cagr(0, 100, 5)

    assert value is None
    assert flag == "ZERO_BASE"


def test_decline_to_loss():
    value, flag = calculate_cagr(100, -20, 5)

    assert value is None
    assert flag == "DECLINE_TO_LOSS"


def test_turnaround():
    value, flag = calculate_cagr(-100, 50, 5)

    assert value is None
    assert flag == "TURNAROUND"


def test_both_negative():
    value, flag = calculate_cagr(-100, -50, 5)

    assert value is None
    assert flag == "BOTH_NEGATIVE"


def test_insufficient_years():
    value, flag = calculate_cagr(100, 150, 0)

    assert value is None
    assert flag == "INSUFFICIENT"


def test_missing_start():
    value, flag = calculate_cagr(None, 100, 5)

    assert value is None
    assert flag == "INSUFFICIENT"


def test_missing_end():
    value, flag = calculate_cagr(100, None, 5)

    assert value is None
    assert flag == "INSUFFICIENT"


def test_negative_years():
    value, flag = calculate_cagr(100, 150, -5)

    assert value is None
    assert flag == "INSUFFICIENT"


def test_cagr_growth():
    value, flag = calculate_cagr(100, 133.1, 3)

    assert abs(value - 10.0) < 0.01
    assert flag is None

def test_window_cagr():
    values = [
        (2020, 100),
        (2021, 110),
        (2022, 121),
    ]

    value, flag = calculate_window_cagr(values, 2)

    assert abs(value - 10.0) < 0.01
    assert flag is None


def test_window_cagr_insufficient_data():
    values = [
        (2021, 100),
        (2022, 110),
    ]

    value, flag = calculate_window_cagr(values, 5)

    assert value is None
    assert flag == "INSUFFICIENT"