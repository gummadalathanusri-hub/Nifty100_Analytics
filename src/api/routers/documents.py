import sqlite3

from fastapi import APIRouter, HTTPException, Request

router = APIRouter(tags=["Documents"])


@router.get("/companies/{ticker}/documents")
def get_company_documents(ticker: str, request: Request):
    """Return annual-report documents and URL validity information."""

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
            FROM documents
            WHERE company_id = ?
            ORDER BY year DESC
            """,
            (company["id"],),
        ).fetchall()

    documents = []

    for row in rows:
        item = dict(row)
        report_url = item.get("annual_report")

        item["is_url_valid"] = bool(
            isinstance(report_url, str)
            and report_url.strip().lower().startswith(("http://", "https://"))
        )

        documents.append(item)

    return {
        "company_id": company["id"],
        "company_name": company["company_name"],
        "documents": documents,
    }
