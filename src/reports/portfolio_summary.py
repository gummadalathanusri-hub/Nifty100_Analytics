import os
import sqlite3
import math
import pandas as pd

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
)
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics


BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)

DB_PATH = os.path.join(
    BASE_DIR,
    "nifty100.db",
)

OUTPUT_DIR = os.path.join(
    BASE_DIR,
    "reports",
    "portfolio",
)

OUTPUT_PDF = os.path.join(
    OUTPUT_DIR,
    "portfolio_summary.pdf",
)


KPI_COLUMNS = [
    ("ROE", "return_on_equity_pct", "%"),
    ("Operating Margin", "operating_profit_margin_pct", "%"),
    ("Net Profit Margin", "net_profit_margin_pct", "%"),
    ("Debt / Equity", "debt_to_equity", "x"),
    ("Revenue CAGR 5Y", "revenue_cagr_5yr", "%"),
    ("PAT CAGR 5Y", "pat_cagr_5yr", "%"),
]


def get_connection():
    return sqlite3.connect(DB_PATH)


def load_data():
    conn = get_connection()

    companies = pd.read_sql_query(
        """
        SELECT id, company_name
        FROM companies
        ORDER BY id
        """,
        conn,
    )

    sectors = pd.read_sql_query(
        """
        SELECT company_id, broad_sector
        FROM sectors
        """,
        conn,
    )

    ratios = pd.read_sql_query(
        """
        SELECT
            company_id,
            year,
            return_on_equity_pct,
            operating_profit_margin_pct,
            net_profit_margin_pct,
            debt_to_equity,
            revenue_cagr_5yr,
            pat_cagr_5yr
        FROM financial_ratios
        ORDER BY company_id, year
        """,
        conn,
    )

    conn.close()

    return companies, sectors, ratios


def clean_number(value):
    if value is None:
        return None

    try:
        value = float(value)
    except (TypeError, ValueError):
        return None

    if not math.isfinite(value):
        return None

    return value


def format_value(value, unit):
    value = clean_number(value)

    if value is None:
        return "N/A"

    if unit == "x":
        return f"{value:.2f}x"

    return f"{value:.2f}%"


def trend_arrow(current, previous):
    current = clean_number(current)
    previous = clean_number(previous)

    if current is None or previous is None:
        return "→"

    if previous == 0:
        if current > 0:
            return "↑"
        if current < 0:
            return "↓"
        return "→"

    change_pct = ((current - previous) / abs(previous)) * 100

    if change_pct > 2:
        return "↑"

    if change_pct < -2:
        return "↓"

    return "→"


def trend_text(current, previous):
    arrow = trend_arrow(current, previous)

    if arrow == "↑":
        return "Improving"
    if arrow == "↓":
        return "Declining"

    return "Stable"


def latest_two_years(company_ratios):
    data = company_ratios.copy()

    data["year"] = pd.to_numeric(
        data["year"],
        errors="coerce",
    )

    data = data.dropna(
        subset=["year"]
    )

    data = data.sort_values(
        "year"
    )

    if data.empty:
        return None, None

    latest = data.iloc[-1]

    if len(data) == 1:
        return latest, None

    previous = data.iloc[-2]

    return latest, previous


def make_kpi_table(latest):
    rows = []

    for index in range(0, 6, 2):
        first = KPI_COLUMNS[index]
        second = KPI_COLUMNS[index + 1]

        first_name, first_column, first_unit = first
        second_name, second_column, second_unit = second

        first_value = format_value(
            latest.get(first_column),
            first_unit,
        )

        second_value = format_value(
            latest.get(second_column),
            second_unit,
        )

        rows.append(
            [
                Paragraph(
                    f"<b>{first_name}</b><br/>{first_value}",
                    KPI_STYLE,
                ),
                Paragraph(
                    f"<b>{second_name}</b><br/>{second_value}",
                    KPI_STYLE,
                ),
            ]
        )

    table = Table(
        rows,
        colWidths=[
            88 * mm,
            88 * mm,
        ],
        rowHeights=[
            24 * mm,
            24 * mm,
            24 * mm,
        ],
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    colors.HexColor("#F3F6FA"),
                ),
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.7,
                    colors.HexColor("#CBD5E1"),
                ),
                (
                    "INNERGRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.HexColor("#CBD5E1"),
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    10,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    10,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
            ]
        )
    )

    return table


def make_trend_table(latest, previous):
    rows = [
        [
            Paragraph("<b>KPI</b>", SMALL_STYLE),
            Paragraph("<b>Latest</b>", SMALL_STYLE),
            Paragraph("<b>Previous</b>", SMALL_STYLE),
            Paragraph("<b>Trend</b>", SMALL_STYLE),
        ]
    ]

    for name, column, unit in KPI_COLUMNS:
        current_value = latest.get(column)

        if previous is None:
            previous_value = None
        else:
            previous_value = previous.get(column)

        current_text = format_value(
            current_value,
            unit,
        )

        previous_text = format_value(
            previous_value,
            unit,
        )

        arrow = trend_arrow(
            current_value,
            previous_value,
        )

        trend = trend_text(
            current_value,
            previous_value,
        )

        rows.append(
            [
                Paragraph(name, SMALL_STYLE),
                Paragraph(current_text, SMALL_STYLE),
                Paragraph(previous_text, SMALL_STYLE),
                Paragraph(
                    f"<b>{arrow}</b> {trend}",
                    SMALL_STYLE,
                ),
            ]
        )

    table = Table(
        rows,
        colWidths=[
            55 * mm,
            35 * mm,
            35 * mm,
            51 * mm,
        ],
        repeatRows=1,
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#E8EEF5"),
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.HexColor("#CBD5E1"),
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
            ]
        )
    )

    return table


def build_company_page(
    story,
    company_id,
    company_name,
    sector,
    company_ratios,
):
    latest, previous = latest_two_years(
        company_ratios
    )

    if latest is None:
        return

    latest_year = int(latest["year"])

    if previous is not None:
        previous_year = int(previous["year"])
    else:
        previous_year = None

    header = Table(
        [
            [
                Paragraph(
                    f"<b>{company_name}</b>",
                    HEADER_STYLE,
                ),
                Paragraph(
                    f"<b>{company_id}</b>",
                    TICKER_STYLE,
                ),
            ]
        ],
        colWidths=[
            140 * mm,
            36 * mm,
        ],
    )

    header.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    colors.HexColor("#0B1F3A"),
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (0, 0),
                    12,
                ),
                (
                    "RIGHTPADDING",
                    (-1, 0),
                    (-1, 0),
                    12,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    10,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    10,
                ),
            ]
        )
    )

    story.append(header)
    story.append(Spacer(1, 5 * mm))

    story.append(
        Paragraph(
            f"Sector: <b>{sector}</b>",
            SECTOR_STYLE,
        )
    )

    story.append(
        Paragraph(
            f"Latest financial year: <b>{latest_year}</b>",
            SECTOR_STYLE,
        )
    )

    story.append(Spacer(1, 5 * mm))

    story.append(
        Paragraph(
            "Top 6 KPIs",
            SECTION_STYLE,
        )
    )

    story.append(Spacer(1, 2 * mm))

    story.append(
        make_kpi_table(latest)
    )

    story.append(Spacer(1, 6 * mm))

    if previous_year is not None:
        trend_title = (
            f"Year-over-Year Trend "
            f"({previous_year} → {latest_year})"
        )
    else:
        trend_title = "Year-over-Year Trend"

    story.append(
        Paragraph(
            trend_title,
            SECTION_STYLE,
        )
    )

    story.append(Spacer(1, 2 * mm))

    story.append(
        make_trend_table(
            latest,
            previous,
        )
    )

    story.append(Spacer(1, 7 * mm))

    story.append(
        Paragraph(
            "Trend rule",
            SECTION_STYLE,
        )
    )

    story.append(
        Paragraph(
            "↑ Increase greater than 2% &nbsp;&nbsp; "
            "↓ Decrease greater than 2% &nbsp;&nbsp; "
            "→ Change within ±2%. "
            "N/A indicates that the KPI is unavailable.",
            NOTE_STYLE,
        )
    )

    story.append(Spacer(1, 5 * mm))

    story.append(
        Paragraph(
            "Portfolio Summary",
            SECTION_STYLE,
        )
    )

    story.append(
        Paragraph(
            "This page provides a concise snapshot of the "
            "company's latest financial indicators and "
            "year-over-year movement. Trend arrows are "
            "descriptive and are calculated from the latest "
            "two available financial years.",
            NOTE_STYLE,
        )
    )


def footer(canvas, doc):
    canvas.saveState()

    canvas.setStrokeColor(
        colors.HexColor("#CBD5E1")
    )

    canvas.line(
        18 * mm,
        13 * mm,
        192 * mm,
        13 * mm,
    )

    canvas.setFont(
        "Helvetica",
        7,
    )

    canvas.setFillColor(
        colors.HexColor("#64748B")
    )

    canvas.drawString(
        18 * mm,
        8 * mm,
        "Nifty 100 Portfolio Summary",
    )

    canvas.drawRightString(
        192 * mm,
        8 * mm,
        f"Page {doc.page}",
    )

    canvas.restoreState()


def generate_report():
    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True,
    )

    companies, sectors, ratios = load_data()

    target_companies = sorted(
        sectors["company_id"].dropna().unique()
    )

    sector_map = dict(
        zip(
            sectors["company_id"],
            sectors["broad_sector"],
        )
    )

    company_name_map = dict(
        zip(
            companies["id"],
            companies["company_name"],
        )
    )

    doc = SimpleDocTemplate(
        OUTPUT_PDF,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=15 * mm,
        bottomMargin=17 * mm,
        title="Nifty 100 Portfolio Summary",
        author="Nifty100 Analytics",
    )

    story = []

    generated = 0
    skipped = []

    for company_id in target_companies:
        company_ratios = ratios[
            ratios["company_id"] == company_id
        ].copy()

        if company_ratios.empty:
            skipped.append(
                (
                    company_id,
                    "No financial ratio data",
                )
            )
            continue

        company_name = company_name_map.get(
            company_id,
            company_id,
        )

        sector = sector_map.get(
            company_id,
            "N/A",
        )

        build_company_page(
            story,
            company_id,
            company_name,
            sector,
            company_ratios,
        )

        story.append(
            PageBreak()
        )

        generated += 1

    if story and isinstance(story[-1], PageBreak):
        story.pop()

    doc.build(
        story,
        onFirstPage=footer,
        onLaterPages=footer,
    )

    print("DAY 35 PORTFOLIO SUMMARY")
    print("=" * 70)
    print(f"Target companies: {len(target_companies)}")
    print(f"Generated pages: {generated}")
    print(f"Skipped: {len(skipped)}")
    print()
    print(f"Output:")
    print(OUTPUT_PDF)

    if skipped:
        print()
        print("Skipped companies:")
        for company_id, reason in skipped:
            print(
                f"{company_id}: {reason}"
            )


styles = getSampleStyleSheet()

HEADER_STYLE = ParagraphStyle(
    "HeaderStyle",
    parent=styles["Normal"],
    fontName="Helvetica-Bold",
    fontSize=17,
    leading=20,
    textColor=colors.white,
    alignment=TA_LEFT,
)

TICKER_STYLE = ParagraphStyle(
    "TickerStyle",
    parent=styles["Normal"],
    fontName="Helvetica-Bold",
    fontSize=13,
    leading=16,
    textColor=colors.white,
    alignment=TA_LEFT,
)

SECTOR_STYLE = ParagraphStyle(
    "SectorStyle",
    parent=styles["Normal"],
    fontName="Helvetica",
    fontSize=9,
    leading=12,
    textColor=colors.HexColor("#475569"),
)

SECTION_STYLE = ParagraphStyle(
    "SectionStyle",
    parent=styles["Normal"],
    fontName="Helvetica-Bold",
    fontSize=11,
    leading=14,
    textColor=colors.HexColor("#0B1F3A"),
    spaceAfter=2,
)

KPI_STYLE = ParagraphStyle(
    "KPIStyle",
    parent=styles["Normal"],
    fontName="Helvetica",
    fontSize=10,
    leading=15,
    textColor=colors.HexColor("#0F172A"),
)

SMALL_STYLE = ParagraphStyle(
    "SmallStyle",
    parent=styles["Normal"],
    fontName="Helvetica",
    fontSize=8.5,
    leading=11,
    textColor=colors.HexColor("#334155"),
)

NOTE_STYLE = ParagraphStyle(
    "NoteStyle",
    parent=styles["Normal"],
    fontName="Helvetica",
    fontSize=8,
    leading=12,
    textColor=colors.HexColor("#64748B"),
)


if __name__ == "__main__":
    generate_report()