import os
import sqlite3
import math

import pandas as pd
import matplotlib.pyplot as plt

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
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
    "sector",
)


PEER_GROUPS = [
    "Automobiles",
    "Consumer Finance",
    "FMCG",
    "IT Services",
    "Life Insurance",
    "Oil & Gas",
    "Pharmaceuticals",
    "Power & Utilities",
    "Private Banks",
    "Public Sector Banks",
    "Steel",
]


RATIO_METRICS = {
    "ROE (%)": "return_on_equity_pct",
    "Debt/Equity": "debt_to_equity",
    "OPM (%)": "operating_profit_margin_pct",
    "NPM (%)": "net_profit_margin_pct",
    "Revenue CAGR 5Y (%)": "revenue_cagr_5yr",
    "PAT CAGR 5Y (%)": "pat_cagr_5yr",
}


MARKET_METRICS = {
    "P/E": "pe_ratio",
    "Dividend Yield (%)": "dividend_yield_pct",
}


def get_connection():
    return sqlite3.connect(DB_PATH)


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


def format_value(value, decimals=2):
    value = clean_number(value)

    if value is None:
        return "N/A"

    return f"{value:.{decimals}f}"


def get_peer_companies(peer_group):
    conn = get_connection()

    query = """
        SELECT
            pg.peer_group_name,
            pg.company_id,
            pg.is_benchmark,
            c.company_name
        FROM peer_groups pg
        LEFT JOIN companies c
            ON pg.company_id = c.id
        WHERE pg.peer_group_name = ?
        ORDER BY
            pg.is_benchmark DESC,
            pg.company_id
    """

    df = pd.read_sql_query(
        query,
        conn,
        params=(peer_group,),
    )

    conn.close()

    return df


def get_latest_ratios(company_id):
    conn = get_connection()

    query = """
        SELECT *
        FROM financial_ratios
        WHERE company_id = ?
        ORDER BY year DESC
        LIMIT 1
    """

    df = pd.read_sql_query(
        query,
        conn,
        params=(company_id,),
    )

    conn.close()

    if df.empty:
        return {}

    return df.iloc[0].to_dict()


def get_latest_market_cap(company_id):
    conn = get_connection()

    query = """
        SELECT *
        FROM market_cap
        WHERE company_id = ?
        ORDER BY year DESC
        LIMIT 1
    """

    df = pd.read_sql_query(
        query,
        conn,
        params=(company_id,),
    )

    conn.close()

    if df.empty:
        return {}

    return df.iloc[0].to_dict()


def build_peer_dataframe(peer_group):
    companies = get_peer_companies(peer_group)

    rows = []

    for _, company in companies.iterrows():
        company_id = company["company_id"]

        ratios = get_latest_ratios(company_id)
        market_cap = get_latest_market_cap(company_id)

        row = {
            "company_id": company_id,
            "company_name": company["company_name"]
            if pd.notna(company["company_name"])
            else company_id,
            "benchmark": (
                "Yes"
                if int(company["is_benchmark"]) == 1
                else ""
            ),
        }

        for label, column in RATIO_METRICS.items():
            row[label] = clean_number(
                ratios.get(column)
            )

        for label, column in MARKET_METRICS.items():
            row[label] = clean_number(
                market_cap.get(column)
            )

        rows.append(row)

    return pd.DataFrame(rows)


def median_summary(df):
    summary = {}

    for metric in list(RATIO_METRICS.keys()) + list(
        MARKET_METRICS.keys()
    ):
        values = pd.to_numeric(
            df[metric],
            errors="coerce",
        )

        if values.notna().any():
            summary[metric] = values.median()
        else:
            summary[metric] = None

    return summary


def make_styles():
    styles = getSampleStyleSheet()

    styles.add(
        ParagraphStyle(
            name="SectorTitle",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=18,
            leading=22,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#17365D"),
            spaceAfter=5 * mm,
        )
    )

    styles.add(
        ParagraphStyle(
            name="Subtitle",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#555555"),
            spaceAfter=5 * mm,
        )
    )

    styles.add(
        ParagraphStyle(
            name="SectionHeading",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            textColor=colors.HexColor("#17365D"),
            spaceBefore=3 * mm,
            spaceAfter=2 * mm,
        )
    )

    styles.add(
        ParagraphStyle(
            name="Small",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=7.5,
            leading=10,
        )
    )

    styles.add(
        ParagraphStyle(
            name="SmallCenter",
            parent=styles["Small"],
            alignment=TA_CENTER,
        )
    )

    return styles


def build_table_data(df, styles):
    headers = [
        "Company",
        "Benchmark",
        "ROE %",
        "D/E",
        "OPM %",
        "NPM %",
        "Rev CAGR %",
        "PAT CAGR %",
        "P/E",
        "Div Yield %",
    ]

    data = [
        [
            Paragraph(
                f"<b>{header}</b>",
                styles["SmallCenter"],
            )
            for header in headers
        ]
    ]

    for _, row in df.iterrows():
        company_name = str(row["company_name"])

        if len(company_name) > 28:
            company_name = (
                company_name[:25] + "..."
            )

        data.append(
            [
                Paragraph(
                    company_name,
                    styles["Small"],
                ),
                Paragraph(
                    str(row["benchmark"]),
                    styles["SmallCenter"],
                ),
                Paragraph(
                    format_value(row["ROE (%)"]),
                    styles["SmallCenter"],
                ),
                Paragraph(
                    format_value(row["Debt/Equity"]),
                    styles["SmallCenter"],
                ),
                Paragraph(
                    format_value(row["OPM (%)"]),
                    styles["SmallCenter"],
                ),
                Paragraph(
                    format_value(row["NPM (%)"]),
                    styles["SmallCenter"],
                ),
                Paragraph(
                    format_value(
                        row["Revenue CAGR 5Y (%)"]
                    ),
                    styles["SmallCenter"],
                ),
                Paragraph(
                    format_value(
                        row["PAT CAGR 5Y (%)"]
                    ),
                    styles["SmallCenter"],
                ),
                Paragraph(
                    format_value(row["P/E"]),
                    styles["SmallCenter"],
                ),
                Paragraph(
                    format_value(
                        row["Dividend Yield (%)"]
                    ),
                    styles["SmallCenter"],
                ),
            ]
        )

    return data


def build_median_table(summary, styles):
    labels = [
        "ROE %",
        "D/E",
        "OPM %",
        "NPM %",
        "Rev CAGR %",
        "PAT CAGR %",
        "P/E",
        "Div Yield %",
    ]

    values = [
        format_value(summary["ROE (%)"]),
        format_value(summary["Debt/Equity"]),
        format_value(summary["OPM (%)"]),
        format_value(summary["NPM (%)"]),
        format_value(
            summary["Revenue CAGR 5Y (%)"]
        ),
        format_value(
            summary["PAT CAGR 5Y (%)"]
        ),
        format_value(summary["P/E"]),
        format_value(
            summary["Dividend Yield (%)"]
        ),
    ]

    return [
        [
            Paragraph(
                f"<b>{label}</b>",
                styles["SmallCenter"],
            )
            for label in labels
        ],
        [
            Paragraph(
                value,
                styles["SmallCenter"],
            )
            for value in values
        ],
    ]


def generate_sector_report(peer_group):
    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True,
    )

    df = build_peer_dataframe(
        peer_group
    )

    if df.empty:
        print(
            f"SKIPPED {peer_group}: no companies"
        )
        return False

    summary = median_summary(df)

    safe_name = (
        peer_group
        .replace("&", "and")
        .replace("/", "_")
        .replace(" ", "_")
    )

    output_path = os.path.join(
        OUTPUT_DIR,
        f"{safe_name}_sector_report.pdf",
    )

    styles = make_styles()

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=12 * mm,
        leftMargin=12 * mm,
        topMargin=12 * mm,
        bottomMargin=12 * mm,
        title=f"{peer_group} Peer Group Report",
    )

    story = []

    story.append(
        Paragraph(
            f"{peer_group} Peer Group Report",
            styles["SectorTitle"],
        )
    )

    story.append(
        Paragraph(
            f"{len(df)} companies | Latest available financial data",
            styles["Subtitle"],
        )
    )

    story.append(
        Paragraph(
            "Peer Group Median KPIs",
            styles["SectionHeading"],
        )
    )

    median_data = build_median_table(
        summary,
        styles,
    )

    median_table = Table(
        median_data,
        colWidths=[
            20 * mm
        ] * 8,
        repeatRows=1,
    )

    median_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#17365D"),
                ),
                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.white,
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.4,
                    colors.HexColor("#BBBBBB"),
                ),
                (
                    "BACKGROUND",
                    (0, 1),
                    (-1, 1),
                    colors.HexColor("#F2F5F8"),
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
            ]
        )
    )

    story.append(median_table)
    story.append(Spacer(1, 5 * mm))

    benchmark_rows = df[
        df["benchmark"] == "Yes"
    ]

    if not benchmark_rows.empty:
        benchmark = benchmark_rows.iloc[0]

        story.append(
            Paragraph(
                f"<b>Benchmark company:</b> "
                f"{benchmark['company_name']} "
                f"({benchmark['company_id']})",
                styles["Small"],
            )
        )

        story.append(Spacer(1, 3 * mm))

    story.append(
        Paragraph(
            "Company-Level Peer Comparison",
            styles["SectionHeading"],
        )
    )

    table_data = build_table_data(
        df,
        styles,
    )

    company_table = Table(
        table_data,
        colWidths=[
            32 * mm,
            15 * mm,
            16 * mm,
            14 * mm,
            16 * mm,
            16 * mm,
            18 * mm,
            18 * mm,
            14 * mm,
            18 * mm,
        ],
        repeatRows=1,
    )

    company_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#17365D"),
                ),
                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.white,
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.35,
                    colors.HexColor("#BBBBBB"),
                ),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [
                        colors.white,
                        colors.HexColor("#F7F9FB"),
                    ],
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "ALIGN",
                    (1, 0),
                    (-1, -1),
                    "CENTER",
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    4,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    4,
                ),
            ]
        )
    )

    story.append(company_table)
    story.append(Spacer(1, 4 * mm))

    story.append(
        Paragraph(
            "Metrics are based on each company's latest available "
            "financial-ratio and market-cap records. Median values "
            "are calculated across companies in this peer group.",
            styles["Small"],
        )
    )

    doc.build(story)

    print(
        f"Generated: {output_path}"
    )

    return True


def main():
    print(
        "DAY 34 SECTOR REPORT TEST"
    )
    print("=" * 60)

    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True,
    )

    for peer_group in PEER_GROUPS:
        generate_sector_report(
            peer_group
        )

    print()
    print(
        "Sector report test generation complete."
    )
    print(
        f"Output directory: {OUTPUT_DIR}"
    )


if __name__ == "__main__":
    main()