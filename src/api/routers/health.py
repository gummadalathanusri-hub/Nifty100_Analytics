import sqlite3
import time

from fastapi import APIRouter, Request

router = APIRouter(tags=["Health"])


TABLES = [
    "companies",
    "analysis",
    "balancesheet",
    "cashflow",
    "documents",
    "financial_ratios",
    "market_cap",
    "peer_groups",
    "profitandloss",
    "prosandcons",
]


@router.get("/health")
def health_check(request: Request):
    """Return API health status and database row counts."""

    db_path = request.app.state.db_path

    db_row_counts = {}

    with sqlite3.connect(db_path) as connection:
        for table in TABLES:
            row = connection.execute(f"SELECT COUNT(*) FROM [{table}]").fetchone()

            db_row_counts[table] = row[0]

    uptime_seconds = time.time() - request.app.state.start_time

    return {
        "status": "ok",
        "db_row_counts": db_row_counts,
        "uptime_seconds": round(uptime_seconds, 2),
        "version": request.app.state.version,
    }
