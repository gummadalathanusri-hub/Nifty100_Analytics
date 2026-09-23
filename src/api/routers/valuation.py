import sqlite3

from fastapi import APIRouter, HTTPException, Request

router = APIRouter(tags=["Valuation"])


@router.get("/market-cap/{ticker}")
def get_market_cap_history(ticker: str, request: Request):
    """Return historical market-cap and valuation multiples for a company."""

    with sqlite3.connect(request.app.state.db_path) as connection:
        connection.row_factory = sqlite3.Row

        company = connection.execute(
            """
            SELECT id, company_name
            FROM companies
            WHERE UPPER(id) = UPPER(?)
            """,
            (ticker,),
        ).fetchone()

        if company is None:
            raise HTTPException(
                status_code=404,
                detail=f"Company '{ticker}' not found",
            )

        rows = connection.execute(
            """
            SELECT *
            FROM market_cap
            WHERE company_id = ?
              AND year BETWEEN 2019 AND 2024
            ORDER BY year
            """,
            (company["id"],),
        ).fetchall()

    return {
        "company_id": company["id"],
        "company_name": company["company_name"],
        "history": [dict(row) for row in rows],
    }
