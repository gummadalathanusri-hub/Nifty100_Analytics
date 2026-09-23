import logging
import sqlite3
import time
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routers import (
    companies,
    documents,
    health,
    peers,
    portfolio,
    screener,
    sectors,
    valuation,
)

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "nifty100.db"
VERSION = "1.0.0"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("nifty100_api")

app = FastAPI(
    title="Nifty100 Analytics API",
    description="REST API for Nifty100 financial analytics and screening.",
    version=VERSION,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_logging_middleware(request, call_next):
    """Log incoming API requests and their response status."""
    start_time = time.perf_counter()

    response = await call_next(request)

    elapsed = time.perf_counter() - start_time

    logger.info(
        "%s %s -> %s (%.4fs)",
        request.method,
        request.url.path,
        response.status_code,
        elapsed,
    )

    response.headers["X-Response-Time"] = f"{elapsed:.4f}"

    return response


def get_db_connection():
    """Open a SQLite connection to the Nifty100 analytics database."""
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


app.state.db_path = DB_PATH
app.state.root_path = ROOT
app.state.start_time = time.time()
app.state.version = VERSION
app.state.get_db_connection = get_db_connection


app.include_router(health.router, prefix="/api/v1")
app.include_router(companies.router, prefix="/api/v1")
app.include_router(screener.router, prefix="/api/v1")
app.include_router(sectors.router, prefix="/api/v1")
app.include_router(peers.router, prefix="/api/v1")
app.include_router(valuation.router, prefix="/api/v1")
app.include_router(portfolio.router, prefix="/api/v1")
app.include_router(documents.router, prefix="/api/v1")


@app.get("/")
def root():
    """Return API metadata and documentation links."""
    return {
        "name": "Nifty100 Analytics API",
        "version": VERSION,
        "docs": "/docs",
        "health": "/api/v1/health",
    }
