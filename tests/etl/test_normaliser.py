import pytest

from src.etl.normaliser import normalize_year, normalize_ticker
@pytest.mark.parametrize(
    "value, expected",
    [
        (2012, 2012),
        ("2012", 2012),
        ("2024", 2024),
        ("Dec 2012", 2012),
        ("Mar 2014", 2014),
        ("Mar-13", 2013),
        ("Mar-14", 2014),
        ("Dec-12", 2012),
        ("FY 2020", 2020),
        ("Year 2021", 2021),
        ("2022.0", 2022),
        ("Apr 2023", 2023),
        ("March 2015", 2015),
        ("Dec-2016", 2016),
        ("Jun 2017", 2017),
        ("Sep 2018", 2018),
        ("FY2019", 2019),
        (None, None),
        ("", None),
        ("not-a-year", None),
    ],
)
def test_normalize_year(value, expected):
    assert normalize_year(value) == expected
@pytest.mark.parametrize(
    "value, expected",
    [
        ("ABB", "ABB"),
        (" abb ", "ABB"),
        ("Hdfcbank", "HDFCBANK"),
        ("hdfcbank", "HDFCBANK"),
        ("TCS", "TCS"),
        (" tcs ", "TCS"),
        ("ADANIENSOL", "ADANIENSOL"),
        ("adaniensol", "ADANIENSOL"),
        ("ICICI Bank", "ICICIBANK"),
        (" ICICI Bank ", "ICICIBANK"),
        ("TCS.", "TCS"),
        ("TCS/", "TCS"),
        ("TCS-", "TCS"),
        (None, None),
        ("", None),
    ],
)
def test_normalize_ticker(value, expected):
    assert normalize_ticker(value) == expected