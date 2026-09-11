import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st


DB_PATH = Path(__file__).resolve().parents[3] / "nifty100.db"


def _read_sql(query, params=()):
    """Execute a read-only SQL query and return a DataFrame."""
    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql_query(query, conn, params=params)


@st.cache_data(ttl=600)
def get_companies():
    return _read_sql("""
        SELECT
            id,
            company_name,
            about_company,
            website,
            nse_profile,
            bse_profile,
            face_value,
            book_value,
            roce_percentage,
            roe_percentage
        FROM companies
        ORDER BY company_name
    """)


@st.cache_data(ttl=600)
def get_ratios(ticker, year=None):
    query = """
        SELECT
            fr.*,
            c.company_name
        FROM financial_ratios fr
        JOIN companies c ON c.id = fr.company_id
        WHERE c.id = ?
    """
    params = [ticker]

    if year is not None:
        query += " AND fr.year = ?"
        params.append(year)

    query += " ORDER BY fr.year"

    return _read_sql(query, params)


@st.cache_data(ttl=600)
def get_pl(ticker):
    return _read_sql("""
        SELECT
            pl.*,
            c.company_name
        FROM profitandloss pl
        JOIN companies c ON c.id = pl.company_id
        WHERE c.id = ?
        ORDER BY pl.year
    """, [ticker])


@st.cache_data(ttl=600)
def get_bs(ticker):
    return _read_sql("""
        SELECT
            bs.*,
            c.company_name
        FROM balancesheet bs
        JOIN companies c ON c.id = bs.company_id
        WHERE c.id = ?
        ORDER BY bs.year
    """, [ticker])


@st.cache_data(ttl=600)
def get_cf(ticker):
    return _read_sql("""
        SELECT
            cf.*,
            c.company_name
        FROM cashflow cf
        JOIN companies c ON c.id = cf.company_id
        WHERE c.id = ?
        ORDER BY cf.year
    """, [ticker])


@st.cache_data(ttl=600)
def get_sectors():
    return _read_sql("""
        SELECT
            s.id,
            s.company_id,
            c.company_name,
            c.nse_profile,
            s.broad_sector,
            s.sub_sector,
            s.index_weight_pct,
            s.market_cap_category
        FROM sectors s
        JOIN companies c ON c.id = s.company_id
        ORDER BY s.broad_sector, c.company_name
    """)


@st.cache_data(ttl=600)
def get_peers(group_name):
    return _read_sql("""
        SELECT
            pg.peer_group_name,
            pg.company_id,
            pg.is_benchmark,
            c.company_name,
            c.nse_profile
        FROM peer_groups pg
        JOIN companies c ON c.id = pg.company_id
        WHERE pg.peer_group_name = ?
        ORDER BY pg.is_benchmark DESC, c.company_name
    """, [group_name])


@st.cache_data(ttl=600)
def get_valuation(ticker):
    return _read_sql("""
        SELECT
            mc.*,
            c.company_name
        FROM market_cap mc
        JOIN companies c ON c.id = mc.company_id
        WHERE c.id = ?
        ORDER BY mc.year
    """, [ticker])


@st.cache_data(ttl=600)
def get_documents(ticker):
    return _read_sql("""
        SELECT
            d.*,
            c.company_name,
            c.nse_profile
        FROM documents d
        JOIN companies c ON c.id = d.company_id
        WHERE c.id = ?
        ORDER BY d.year DESC
    """, [ticker])


@st.cache_data(ttl=600)
def get_pros_cons(ticker):
    return _read_sql("""
        SELECT
            pc.pros,
            pc.cons
        FROM prosandcons pc
        JOIN companies c ON c.id = pc.company_id
        WHERE c.id = ? 
    """, [ticker])

@st.cache_data(ttl=600)
def get_all_ratios(year=None):
    """Return financial ratios for all companies, optionally filtered by year."""
    query = """
        SELECT
            fr.*,
            c.company_name
        FROM financial_ratios fr
        JOIN companies c ON c.id = fr.company_id
    """
    params = []

    if year is not None:
        query += " WHERE fr.year = ?"
        params.append(year)

    query += " ORDER BY c.company_name, fr.year"

    return _read_sql(query, params)