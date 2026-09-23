import sqlite3

from fastapi import APIRouter, HTTPException, Request

router = APIRouter(tags=["Peers"])


PEER_METRICS = [
    "Asset Turnover",
    "D/E",
    "EPS CAGR 5yr",
    "FCF",
    "Interest Coverage",
    "Net Profit Margin",
    "PAT CAGR 5yr",
    "ROCE",
    "ROE",
    "Revenue CAGR 5yr",
]


@router.get("/peers/{group_name}")
def get_peer_group(group_name: str, request: Request):
    """Return companies in a peer group with latest percentile metrics."""

    with sqlite3.connect(request.app.state.db_path) as connection:
        connection.row_factory = sqlite3.Row

        group_exists = connection.execute(
            """
            SELECT 1
            FROM peer_groups
            WHERE LOWER(peer_group_name) = LOWER(?)
            LIMIT 1
            """,
            (group_name,),
        ).fetchone()

        if group_exists is None:
            raise HTTPException(
                status_code=404,
                detail=f"Peer group '{group_name}' not found",
            )

        rows = connection.execute(
            """
            SELECT
                pp.company_id,
                pp.peer_group_name,
                pp.metric,
                pp.value,
                pp.percentile_rank,
                pp.year
            FROM peer_percentiles pp
            WHERE LOWER(pp.peer_group_name) = LOWER(?)
              AND pp.metric IN (
                  'Asset Turnover',
                  'D/E',
                  'EPS CAGR 5yr',
                  'FCF',
                  'Interest Coverage',
                  'Net Profit Margin',
                  'PAT CAGR 5yr',
                  'ROCE',
                  'ROE',
                  'Revenue CAGR 5yr'
              )
              AND pp.year = (
                  SELECT MAX(pp2.year)
                  FROM peer_percentiles pp2
                  WHERE pp2.company_id = pp.company_id
                    AND pp2.peer_group_name = pp.peer_group_name
                    AND pp2.metric = pp.metric
              )
            ORDER BY pp.company_id, pp.metric
            """,
            (group_name,),
        ).fetchall()

    companies = {}

    for row in rows:
        company_id = row["company_id"]

        if company_id not in companies:
            companies[company_id] = {
                "company_id": company_id,
                "peer_group_name": row["peer_group_name"],
                "year": row["year"],
                "metrics": {},
            }

        companies[company_id]["metrics"][row["metric"]] = {
            "value": row["value"],
            "percentile_rank": row["percentile_rank"],
        }

    return {
        "group_name": group_name,
        "year": max((row["year"] for row in rows), default=None),
        "company_count": len(companies),
        "companies": list(companies.values()),
    }


@router.get("/companies/{ticker}/peers/compare")
def compare_company_with_peers(
    ticker: str,
    request: Request,
):
    """Return company, peer-average, and benchmark radar data."""

    with sqlite3.connect(request.app.state.db_path) as connection:
        connection.row_factory = sqlite3.Row

        company = connection.execute(
            """
            SELECT
                c.id AS company_id,
                c.company_name,
                pg.peer_group_name
            FROM companies c
            LEFT JOIN peer_groups pg
                ON pg.company_id = c.id
            WHERE UPPER(c.id) = UPPER(?)
            LIMIT 1
            """,
            (ticker,),
        ).fetchone()

        if company is None:
            raise HTTPException(
                status_code=404,
                detail=f"Company '{ticker}' not found",
            )

        group_name = company["peer_group_name"]

        if group_name is None:
            raise HTTPException(
                status_code=404,
                detail=f"No peer group found for '{ticker}'",
            )

        peer_rows = connection.execute(
            """
            SELECT
                pp.company_id,
                pp.metric,
                pp.value,
                pp.year
            FROM peer_percentiles pp
            WHERE LOWER(pp.peer_group_name) = LOWER(?)
              AND pp.metric IN (
                  'Asset Turnover',
                  'D/E',
                  'EPS CAGR 5yr',
                  'FCF',
                  'Interest Coverage',
                  'Net Profit Margin',
                  'PAT CAGR 5yr',
                  'ROCE',
                  'ROE',
                  'Revenue CAGR 5yr'
              )
              AND pp.year = (
                  SELECT MAX(pp2.year)
                  FROM peer_percentiles pp2
                  WHERE pp2.company_id = pp.company_id
                    AND pp2.peer_group_name = pp.peer_group_name
                    AND pp2.metric = pp.metric
              )
            """,
            (group_name,),
        ).fetchall()

        company_rows = [
            row
            for row in peer_rows
            if row["company_id"].upper() == company["company_id"].upper()
        ]

        if not company_rows:
            raise HTTPException(
                status_code=404,
                detail=f"No peer metrics found for '{ticker}'",
            )

    company_values = {row["metric"]: row["value"] for row in company_rows}

    peer_average = {}

    for metric in PEER_METRICS:
        values = [
            row["value"]
            for row in peer_rows
            if row["metric"] == metric and row["value"] is not None
        ]

        peer_average[metric] = sum(values) / len(values) if values else None

    benchmark = {metric: peer_average[metric] for metric in PEER_METRICS}

    return {
        "company_id": company["company_id"],
        "company_name": company["company_name"],
        "peer_group": group_name,
        "year": max(
            (row["year"] for row in peer_rows),
            default=None,
        ),
        "axes": PEER_METRICS,
        "company": company_values,
        "peer_average": peer_average,
        "benchmark": benchmark,
    }
