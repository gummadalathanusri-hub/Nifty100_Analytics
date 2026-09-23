import sqlite3

from fastapi import APIRouter, Request

router = APIRouter(tags=["Portfolio"])


@router.get("/portfolio/stats")
def get_portfolio_stats(request: Request):
    """Return the portfolio KPI percentile statistics."""

    query = """
        SELECT
            kpi,
            p10,
            p25,
            p50,
            p75,
            p90,
            mean,
            std,
            count
        FROM portfolio_stats
        ORDER BY kpi
    """

    with sqlite3.connect(request.app.state.db_path) as connection:
        connection.row_factory = sqlite3.Row

        try:
            rows = connection.execute(query).fetchall()
        except sqlite3.OperationalError:
            rows = []

    if rows:
        return {
            "count": len(rows),
            "statistics": [dict(row) for row in rows],
        }

    # portfolio_stats.csv is the Sprint 6 deliverable.
    # Fall back to the generated CSV when the database table
    # does not exist.
    from pathlib import Path

    import pandas as pd

    csv_path = Path(request.app.state.db_path).parent / "output" / "portfolio_stats.csv"

    if not csv_path.exists():
        return {
            "count": 0,
            "statistics": [],
        }

    df = pd.read_csv(csv_path)

    return {
        "count": len(df),
        "statistics": df.to_dict(orient="records"),
    }
