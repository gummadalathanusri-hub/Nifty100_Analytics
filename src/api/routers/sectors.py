import sqlite3
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request

router = APIRouter(tags=["Sectors"])

ROOT = Path(__file__).resolve().parents[3]
UNIVERSE_PATH = ROOT / "output" / "sprint6_company_universe.csv"


def load_universe():
    """Load the exact Sprint 6 92-company universe."""
    import csv

    with open(UNIVERSE_PATH, newline="", encoding="utf-8") as file:
        return {row["id"].strip() for row in csv.DictReader(file) if row.get("id")}


def median(values):
    """Calculate the median of a numeric list."""
    if not values:
        return None

    values = sorted(values)
    n = len(values)
    middle = n // 2

    if n % 2:
        return values[middle]

    return (values[middle - 1] + values[middle]) / 2


@router.get("/sectors")
def get_sectors(request: Request):
    """Return sector-level company counts and median latest-year KPIs."""

    universe = load_universe()
    placeholders = ",".join("?" for _ in universe)

    with sqlite3.connect(request.app.state.db_path) as connection:
        connection.row_factory = sqlite3.Row

        sectors = connection.execute(
            f"""
            SELECT DISTINCT s.broad_sector
            FROM sectors s
            WHERE s.broad_sector IS NOT NULL
              AND s.company_id IN ({placeholders})
            ORDER BY s.broad_sector
            """,
            tuple(universe),
        ).fetchall()

        results = []

        for sector_row in sectors:
            sector = sector_row["broad_sector"]

            company_count = connection.execute(
                f"""
                SELECT COUNT(DISTINCT s.company_id)
                FROM sectors s
                WHERE s.broad_sector = ?
                  AND s.company_id IN ({placeholders})
                """,
                (sector, *universe),
            ).fetchone()[0]

            values = connection.execute(
                f"""
                SELECT
                    fr.return_on_equity_pct,
                    mc.pe_ratio,
                    fr.debt_to_equity
                FROM financial_ratios fr
                JOIN sectors s
                    ON s.company_id = fr.company_id
                LEFT JOIN market_cap mc
                    ON mc.company_id = fr.company_id
                    AND mc.year = fr.year
                WHERE s.broad_sector = ?
                  AND fr.company_id IN ({placeholders})
                  AND fr.year = (
                      SELECT MAX(fr2.year)
                      FROM financial_ratios fr2
                      WHERE fr2.company_id = fr.company_id
                  )
                """,
                (sector, *universe),
            ).fetchall()

            roe = [
                row["return_on_equity_pct"]
                for row in values
                if row["return_on_equity_pct"] is not None
            ]

            pe = [row["pe_ratio"] for row in values if row["pe_ratio"] is not None]

            de = [
                row["debt_to_equity"]
                for row in values
                if row["debt_to_equity"] is not None
            ]

            results.append(
                {
                    "sector": sector,
                    "company_count": company_count,
                    "median_roe": median(roe),
                    "median_pe": median(pe),
                    "median_de": median(de),
                }
            )

    return results


@router.get("/sectors/{sector}/companies")
def get_sector_companies(sector: str, request: Request):
    """Return companies and latest KPIs for a sector."""

    universe = load_universe()
    placeholders = ",".join("?" for _ in universe)

    with sqlite3.connect(request.app.state.db_path) as connection:
        connection.row_factory = sqlite3.Row

        sector_exists = connection.execute(
            f"""
            SELECT 1
            FROM sectors
            WHERE LOWER(broad_sector) = LOWER(?)
              AND company_id IN ({placeholders})
            LIMIT 1
            """,
            (sector, *universe),
        ).fetchone()

        if sector_exists is None:
            raise HTTPException(
                status_code=404,
                detail=f"Sector '{sector}' not found",
            )

        rows = connection.execute(
            f"""
            SELECT
                c.id AS company_id,
                c.company_name,
                s.broad_sector,
                fr.year,
                fr.return_on_equity_pct AS roe_pct,
                fr.debt_to_equity,
                fr.revenue_cagr_5yr,
                fr.pat_cagr_5yr,
                fr.operating_profit_margin_pct
            FROM companies c
            JOIN sectors s
                ON s.company_id = c.id
            JOIN financial_ratios fr
                ON fr.company_id = c.id
            WHERE LOWER(s.broad_sector) = LOWER(?)
              AND c.id IN ({placeholders})
              AND fr.year = (
                  SELECT MAX(fr2.year)
                  FROM financial_ratios fr2
                  WHERE fr2.company_id = c.id
              )
            ORDER BY c.company_name
            """,
            (sector, *universe),
        ).fetchall()

    return [dict(row) for row in rows]
