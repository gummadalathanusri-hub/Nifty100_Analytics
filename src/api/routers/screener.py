import math
import sqlite3
from pathlib import Path

import pandas as pd
from fastapi import APIRouter, HTTPException, Query, Request

ROOT = Path(__file__).resolve().parents[3]
UNIVERSE_PATH = ROOT / "output" / "sprint6_company_universe.csv"

SPRINT6_UNIVERSE = set(
    pd.read_csv(UNIVERSE_PATH)["id"].astype(str).str.strip().str.upper()
)

router = APIRouter(tags=["Screener"])


@router.get("/screener")
def run_screener(
    request: Request,
    min_roe: str | None = Query(default=None),
    max_de: str | None = Query(default=None),
    min_fcf: str | None = Query(default=None),
    sector: str | None = None,
    min_rev_cagr_5yr: str | None = Query(default=None),
    min_pat_cagr_5yr: str | None = Query(default=None),
    max_pe: str | None = Query(default=None),
):
    """Return ranked companies matching the supplied screening filters."""
    numeric_filters = {
        "min_roe": min_roe,
        "max_de": max_de,
        "min_fcf": min_fcf,
        "min_rev_cagr_5yr": min_rev_cagr_5yr,
        "min_pat_cagr_5yr": min_pat_cagr_5yr,
        "max_pe": max_pe,
    }

    parsed_filters = {}

    for name, value in numeric_filters.items():
        if value is not None:
            try:
                parsed_value = float(value)
            except (TypeError, ValueError):
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid value for {name}",
                )

            if not math.isfinite(parsed_value):
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid value for {name}",
                )

            parsed_filters[name] = parsed_value

    min_roe = parsed_filters.get("min_roe")
    max_de = parsed_filters.get("max_de")
    min_fcf = parsed_filters.get("min_fcf")
    min_rev_cagr_5yr = parsed_filters.get("min_rev_cagr_5yr")
    min_pat_cagr_5yr = parsed_filters.get("min_pat_cagr_5yr")
    max_pe = parsed_filters.get("max_pe")

    placeholders = ",".join(["?"] * len(SPRINT6_UNIVERSE))
    universe_params = sorted(SPRINT6_UNIVERSE)

    query = f"""
        SELECT
            fr.company_id,
            c.company_name,
            s.broad_sector,
            fr.year,
            fr.return_on_equity_pct AS roe_pct,
            fr.debt_to_equity AS de,
            fr.free_cash_flow_cr AS fcf_cr,
            fr.revenue_cagr_5yr,
            fr.pat_cagr_5yr,
            mc.pe_ratio
        FROM financial_ratios fr
        JOIN companies c
            ON c.id = fr.company_id
        LEFT JOIN sectors s
            ON s.company_id = fr.company_id
        LEFT JOIN market_cap mc
            ON mc.company_id = fr.company_id
            AND mc.year = fr.year
        WHERE UPPER(fr.company_id) IN ({placeholders})
          AND fr.year = (
              SELECT MAX(fr2.year)
              FROM financial_ratios fr2
              WHERE fr2.company_id = fr.company_id
          )
    """

    conditions = []
    params = list(universe_params)

    if min_roe is not None:
        conditions.append("fr.return_on_equity_pct >= ?")
        params.append(min_roe)

    if max_de is not None:
        conditions.append("fr.debt_to_equity <= ?")
        params.append(max_de)

    if min_fcf is not None:
        conditions.append("fr.free_cash_flow_cr >= ?")
        params.append(min_fcf)

    if sector:
        conditions.append("LOWER(s.broad_sector) = LOWER(?)")
        params.append(sector.strip())

    if min_rev_cagr_5yr is not None:
        conditions.append("fr.revenue_cagr_5yr >= ?")
        params.append(min_rev_cagr_5yr)

    if min_pat_cagr_5yr is not None:
        conditions.append("fr.pat_cagr_5yr >= ?")
        params.append(min_pat_cagr_5yr)

    if max_pe is not None:
        conditions.append("mc.pe_ratio <= ?")
        params.append(max_pe)

    if conditions:
        query += " AND " + " AND ".join(conditions)

    query += """
        ORDER BY
            fr.return_on_equity_pct DESC,
            fr.revenue_cagr_5yr DESC
    """

    with sqlite3.connect(request.app.state.db_path) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(query, params).fetchall()

    return {
        "count": len(rows),
        "results": [dict(row) for row in rows],
    }
