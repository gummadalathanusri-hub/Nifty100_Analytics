import sqlite3
from pathlib import Path

import pandas as pd
from fastapi import APIRouter, HTTPException, Query, Request

ROOT = Path(__file__).resolve().parents[3]

UNIVERSE_PATH = ROOT / "output" / "sprint6_company_universe.csv"

SPRINT6_UNIVERSE = set(
    pd.read_csv(UNIVERSE_PATH)["id"].astype(str).str.strip().str.upper()
)

router = APIRouter(tags=["Companies"])


@router.get("/companies")
def get_companies(
    request: Request,
    sector: str | None = None,
    market_cap_category: str | None = None,
    search: str | None = Query(default=None),
):
    """Return the 92-company Sprint 6 universe with optional filters."""

    placeholders = ",".join("?" for _ in SPRINT6_UNIVERSE)

    query = f"""
        SELECT
            c.id AS company_id,
            c.company_name,
            s.broad_sector,
            s.sub_sector,
            c.roe_percentage AS roe_pct,
            c.roce_percentage AS roce_pct
        FROM companies c
        LEFT JOIN sectors s
            ON c.id = s.company_id
        WHERE UPPER(c.id) IN ({placeholders})
    """

    conditions = []
    params = sorted(SPRINT6_UNIVERSE)

    if sector:
        conditions.append("LOWER(s.broad_sector) = LOWER(?)")
        params.append(sector)

    if market_cap_category:
        conditions.append("LOWER(s.market_cap_category) = LOWER(?)")
        params.append(market_cap_category)

    if search:
        conditions.append(
            "(LOWER(c.company_name) LIKE LOWER(?) " "OR LOWER(c.id) LIKE LOWER(?))"
        )
        search_value = f"%{search}%"
        params.extend([search_value, search_value])

    if conditions:
        query += " AND " + " AND ".join(conditions)

    query += " ORDER BY c.company_name"

    with sqlite3.connect(request.app.state.db_path) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(query, params).fetchall()

    return [dict(row) for row in rows]


@router.get("/companies/{ticker}")
def get_company(ticker: str, request: Request):
    """Return the company profile, latest KPIs, and sector information."""

    ticker = ticker.upper()

    with sqlite3.connect(request.app.state.db_path) as connection:
        connection.row_factory = sqlite3.Row

        company = connection.execute(
            """
            SELECT *
            FROM companies
            WHERE UPPER(id) = UPPER(?)
            """,
            (ticker,),
        ).fetchone()

        if company is None or company["id"].upper() not in SPRINT6_UNIVERSE:
            raise HTTPException(
                status_code=404,
                detail=f"Company '{ticker}' not found",
            )

        sector = connection.execute(
            """
            SELECT *
            FROM sectors
            WHERE company_id = ?
            LIMIT 1
            """,
            (company["id"],),
        ).fetchone()

        ratios = connection.execute(
            """
            SELECT *
            FROM financial_ratios
            WHERE company_id = ?
            ORDER BY year DESC
            LIMIT 1
            """,
            (company["id"],),
        ).fetchone()

    return {
        "company": dict(company),
        "latest_ratios": dict(ratios) if ratios else {},
        "sector": dict(sector) if sector else {},
    }


@router.get("/companies/{ticker}/pl")
def get_company_pl(
    ticker: str,
    request: Request,
    from_year: int | None = Query(default=None),
    to_year: int | None = Query(default=None),
):
    """Return P&L history with optional year filters."""

    ticker = ticker.upper()

    with sqlite3.connect(request.app.state.db_path) as connection:
        connection.row_factory = sqlite3.Row

        company = connection.execute(
            """
            SELECT id
            FROM companies
            WHERE UPPER(id) = UPPER(?)
            """,
            (ticker,),
        ).fetchone()

        if company is None or company["id"].upper() not in SPRINT6_UNIVERSE:
            raise HTTPException(
                status_code=404,
                detail=f"Company '{ticker}' not found",
            )

        query = """
            SELECT *
            FROM profitandloss
            WHERE company_id = ?
        """

        params = [company["id"]]

        if from_year is not None:
            query += " AND year >= ?"
            params.append(from_year)

        if to_year is not None:
            query += " AND year <= ?"
            params.append(to_year)

        query += " ORDER BY year"

        rows = connection.execute(query, params).fetchall()

    return {
        "company_id": company["id"],
        "from_year": from_year,
        "to_year": to_year,
        "count": len(rows),
        "data": [dict(row) for row in rows],
    }


@router.get("/companies/{ticker}/bs")
def get_company_bs(
    ticker: str,
    request: Request,
    from_year: int | None = Query(default=None),
    to_year: int | None = Query(default=None),
):
    """Return balance-sheet history with optional year filters."""

    ticker = ticker.upper()

    with sqlite3.connect(request.app.state.db_path) as connection:
        connection.row_factory = sqlite3.Row

        company = connection.execute(
            """
            SELECT id
            FROM companies
            WHERE UPPER(id) = UPPER(?)
            """,
            (ticker,),
        ).fetchone()

        if company is None or company["id"].upper() not in SPRINT6_UNIVERSE:
            raise HTTPException(
                status_code=404,
                detail=f"Company '{ticker}' not found",
            )

        query = """
            SELECT *
            FROM balancesheet
            WHERE company_id = ?
        """

        params = [company["id"]]

        if from_year is not None:
            query += " AND year >= ?"
            params.append(from_year)

        if to_year is not None:
            query += " AND year <= ?"
            params.append(to_year)

        query += " ORDER BY year"

        rows = connection.execute(query, params).fetchall()

    return {
        "company_id": company["id"],
        "from_year": from_year,
        "to_year": to_year,
        "count": len(rows),
        "data": [dict(row) for row in rows],
    }


@router.get("/companies/{ticker}/cashflow")
def get_company_cashflow(
    ticker: str,
    request: Request,
    from_year: int | None = Query(default=None),
    to_year: int | None = Query(default=None),
):
    """Return cash-flow history with optional year filters."""

    ticker = ticker.upper()

    with sqlite3.connect(request.app.state.db_path) as connection:
        connection.row_factory = sqlite3.Row

        company = connection.execute(
            """
            SELECT id
            FROM companies
            WHERE UPPER(id) = UPPER(?)
            """,
            (ticker,),
        ).fetchone()

        if company is None or company["id"].upper() not in SPRINT6_UNIVERSE:
            raise HTTPException(
                status_code=404,
                detail=f"Company '{ticker}' not found",
            )

        query = """
            SELECT *
            FROM cashflow
            WHERE company_id = ?
        """

        params = [company["id"]]

        if from_year is not None:
            query += " AND year >= ?"
            params.append(from_year)

        if to_year is not None:
            query += " AND year <= ?"
            params.append(to_year)

        query += " ORDER BY year"

        rows = connection.execute(query, params).fetchall()

    return {
        "company_id": company["id"],
        "from_year": from_year,
        "to_year": to_year,
        "count": len(rows),
        "data": [dict(row) for row in rows],
    }


@router.get("/companies/{ticker}/ratios")
def get_company_ratios(
    ticker: str,
    request: Request,
    year: int | None = Query(default=None),
):
    """Return financial-ratio history with an optional year filter."""

    ticker = ticker.upper()

    with sqlite3.connect(request.app.state.db_path) as connection:
        connection.row_factory = sqlite3.Row

        company = connection.execute(
            """
            SELECT id
            FROM companies
            WHERE UPPER(id) = UPPER(?)
            """,
            (ticker,),
        ).fetchone()

        if company is None or company["id"].upper() not in SPRINT6_UNIVERSE:
            raise HTTPException(
                status_code=404,
                detail=f"Company '{ticker}' not found",
            )

        query = """
            SELECT *
            FROM financial_ratios
            WHERE company_id = ?
        """

        params = [company["id"]]

        if year is not None:
            query += " AND year = ?"
            params.append(year)

        query += " ORDER BY year"

        rows = connection.execute(query, params).fetchall()

    return {
        "company_id": company["id"],
        "year": year,
        "count": len(rows),
        "data": [dict(row) for row in rows],
    }


@router.get("/companies/{ticker}/tearsheet")
def get_company_tearsheet(
    ticker: str,
    request: Request,
):
    """Return the pre-generated company tearsheet PDF."""

    from fastapi.responses import FileResponse

    ticker = ticker.upper()

    with sqlite3.connect(request.app.state.db_path) as connection:
        company = connection.execute(
            """
            SELECT id
            FROM companies
            WHERE UPPER(id) = UPPER(?)
            """,
            (ticker,),
        ).fetchone()

    if company is None or company[0].upper() not in SPRINT6_UNIVERSE:
        raise HTTPException(
            status_code=404,
            detail=f"Company '{ticker}' not found",
        )

    tearsheet_path = (
        Path(request.app.state.root_path)
        / "reports"
        / "tearsheets"
        / f"{ticker}_tearsheet.pdf"
    )

    if not tearsheet_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Tearsheet for '{ticker}' not found",
        )

    return FileResponse(
        path=tearsheet_path,
        media_type="application/pdf",
        filename=f"{ticker}_tearsheet.pdf",
    )
