from pathlib import Path

import pandas as pd
import pytest

from src.etl.loader import load_excel, load_raw_directory


RAW_DIR = Path("data/raw")
SUPPORTING_DIR = Path("data/supporting")


def test_load_companies():
    df = load_excel(RAW_DIR / "companies.xlsx")

    assert df.shape[0] == 92
    assert "id" in df.columns
    assert "company_name" in df.columns


def test_load_profitandloss():
    df = load_excel(RAW_DIR / "profitandloss.xlsx")

    assert df.shape[0] == 1276
    assert "company_id" in df.columns
    assert "year" in df.columns
    assert "sales" in df.columns


def test_load_balancesheet():
    df = load_excel(RAW_DIR / "balancesheet.xlsx")

    assert df.shape[0] == 1312
    assert "total_assets" in df.columns
    assert "total_liabilities" in df.columns


def test_load_cashflow():
    df = load_excel(RAW_DIR / "cashflow.xlsx")

    assert df.shape[0] == 1187
    assert "net_cash_flow" in df.columns


def test_load_analysis():
    df = load_excel(RAW_DIR / "analysis.xlsx")

    assert df.shape[0] == 20
    assert "company_id" in df.columns
    assert "roe" in df.columns


def test_load_documents():
    df = load_excel(RAW_DIR / "documents.xlsx")

    assert df.shape[0] == 1585
    assert "annual_report" in df.columns


def test_load_prosandcons():
    df = load_excel(RAW_DIR / "prosandcons.xlsx")

    assert df.shape[0] == 16
    assert "pros" in df.columns
    assert "cons" in df.columns


def test_load_financial_ratios():
    df = load_excel(SUPPORTING_DIR / "financial_ratios.xlsx")

    assert df.shape[0] == 1184
    assert "net_profit_margin_pct" in df.columns
    assert "earnings_per_share" in df.columns


def test_load_market_cap():
    df = load_excel(SUPPORTING_DIR / "market_cap.xlsx")

    assert "market_cap_crore" in df.columns
    assert "enterprise_value_crore" in df.columns


def test_load_peer_groups():
    df = load_excel(SUPPORTING_DIR / "peer_groups.xlsx")

    assert "peer_group_name" in df.columns
    assert "is_benchmark" in df.columns


def test_load_sectors():
    df = load_excel(SUPPORTING_DIR / "sectors.xlsx")

    assert "broad_sector" in df.columns
    assert "sub_sector" in df.columns


def test_load_stock_prices():
    df = load_excel(SUPPORTING_DIR / "stock_prices.xlsx")

    assert df.shape[0] == 5520
    assert "date" in df.columns
    assert pd.api.types.is_datetime64_any_dtype(df["date"])


def test_missing_file_raises_error():
    with pytest.raises(FileNotFoundError):
        load_excel("data/raw/file_that_does_not_exist.xlsx")


def test_load_raw_directory():
    data = load_raw_directory(RAW_DIR)

    assert len(data) == 7
    assert "companies.xlsx" in data
    assert "profitandloss.xlsx" in data