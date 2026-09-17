from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
    PageBreak,
)


ROOT = Path(__file__).resolve().parents[2]

DB_PATH = ROOT / "nifty100.db"
PROS_CONS_PATH = ROOT / "output" / "pros_cons_generated.csv"
CASHFLOW_PATH = ROOT / "output" / "cashflow_intelligence.xlsx"
CAPITAL_ALLOCATION_PATH = ROOT / "output" / "capital_allocation.csv"

TEST_OUTPUT = ROOT / "reports" / "tearsheet_test"
CHART_OUTPUT = TEST_OUTPUT / "charts"

NAVY = colors.HexColor("#0B1F3A")
GREEN = colors.HexColor("#16803C")
RED = colors.HexColor("#B42318")
LIGHT_BLUE = colors.HexColor("#EAF1F8")
LIGHT_GREEN = colors.HexColor("#EAF6EE")
LIGHT_RED = colors.HexColor("#FDECEC")
DARK_GREY = colors.HexColor("#374151")
WHITE = colors.white


def get_connection():
    return sqlite3.connect(DB_PATH)


def get_company(company_id):
    conn = get_connection()

    df = pd.read_sql_query(
        """
        SELECT *
        FROM companies
        WHERE id = ?
        """,
        conn,
        params=(company_id,),
    )

    conn.close()

    if df.empty:
        raise ValueError(f"Company not found: {company_id}")

    return df.iloc[0]


def get_profit_loss(company_id):
    conn = get_connection()

    df = pd.read_sql_query(
        """
        SELECT *
        FROM profitandloss
        WHERE company_id = ?
        ORDER BY year
        """,
        conn,
        params=(company_id,),
    )

    conn.close()

    return df


def get_balance_sheet(company_id):
    conn = get_connection()

    df = pd.read_sql_query(
        """
        SELECT *
        FROM balancesheet
        WHERE company_id = ?
        ORDER BY year
        """,
        conn,
        params=(company_id,),
    )

    conn.close()

    return df


def get_cash_flow(company_id):
    conn = get_connection()

    df = pd.read_sql_query(
        """
        SELECT *
        FROM cashflow
        WHERE company_id = ?
        ORDER BY year
        """,
        conn,
        params=(company_id,),
    )

    conn.close()

    return df


def get_ratios(company_id):
    conn = get_connection()

    df = pd.read_sql_query(
        """
        SELECT *
        FROM financial_ratios
        WHERE company_id = ?
        ORDER BY year
        """,
        conn,
        params=(company_id,),
    )

    conn.close()

    return df


def get_market_cap(company_id):
    conn = get_connection()

    df = pd.read_sql_query(
        """
        SELECT *
        FROM market_cap
        WHERE company_id = ?
        ORDER BY year
        """,
        conn,
        params=(company_id,),
    )

    conn.close()

    return df


def get_sector(company_id):
    conn = get_connection()

    df = pd.read_sql_query(
        """
        SELECT broad_sector
        FROM sectors
        WHERE company_id = ?
        LIMIT 1
        """,
        conn,
        params=(company_id,),
    )

    conn.close()

    if df.empty:
        return "Unknown"

    value = df.iloc[0]["broad_sector"]

    if pd.isna(value):
        return "Unknown"

    return str(value)


def get_pros_cons(company_id):
    if not PROS_CONS_PATH.exists():
        return pd.DataFrame()

    df = pd.read_csv(PROS_CONS_PATH)

    return df[
        df["company_id"] == company_id
    ].copy()


def get_cashflow_intelligence(company_id):
    if not CASHFLOW_PATH.exists():
        return pd.DataFrame()

    df = pd.read_excel(CASHFLOW_PATH)

    return df[
        df["company_id"] == company_id
    ].copy()


def get_capital_allocation(company_id):
    if not CAPITAL_ALLOCATION_PATH.exists():
        return pd.DataFrame()

    df = pd.read_csv(
        CAPITAL_ALLOCATION_PATH
    )

    df = df[
        df["company_id"] == company_id
    ].copy()

    if df.empty:
        return df

    df["year"] = pd.to_numeric(
        df["year"],
        errors="coerce",
    )

    return df.sort_values("year")


def format_number(value):
    if value is None or pd.isna(value):
        return "N/A"

    value = float(value)

    return f"{value:,.2f}"


def format_pct(value):
    if value is None or pd.isna(value):
        return "N/A"

    return f"{float(value):.2f}%"


def make_styles():
    styles = getSampleStyleSheet()

    styles.add(
        ParagraphStyle(
            name="TearTitle",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=20,
            leading=22,
            textColor=WHITE,
        )
    )

    styles.add(
        ParagraphStyle(
            name="TearSubtitle",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=11,
            textColor=WHITE,
        )
    )

    styles.add(
        ParagraphStyle(
            name="SectionTitle",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=13,
            textColor=NAVY,
            spaceBefore=3,
            spaceAfter=5,
        )
    )

    styles.add(
        ParagraphStyle(
            name="Small",
            parent=styles["Normal"],
            fontSize=7.5,
            leading=9,
            textColor=DARK_GREY,
        )
    )

    styles.add(
        ParagraphStyle(
            name="BulletGreen",
            parent=styles["Normal"],
            fontSize=7.5,
            leading=9,
            textColor=GREEN,
            leftIndent=7,
            firstLineIndent=-5,
            spaceAfter=3,
        )
    )

    styles.add(
        ParagraphStyle(
            name="BulletRed",
            parent=styles["Normal"],
            fontSize=7.5,
            leading=9,
            textColor=RED,
            leftIndent=7,
            firstLineIndent=-5,
            spaceAfter=3,
        )
    )

    styles.add(
        ParagraphStyle(
            name="TileLabel",
            parent=styles["Normal"],
            fontSize=6.5,
            leading=8,
            textColor=DARK_GREY,
            alignment=1,
        )
    )

    styles.add(
        ParagraphStyle(
            name="TileValue",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=12,
            textColor=NAVY,
            alignment=1,
        )
    )

    styles.add(
        ParagraphStyle(
            name="Badge",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=11,
            textColor=WHITE,
            alignment=1,
        )
    )

    return styles


def header_table(company, sector, styles):
    company_id = str(company["id"])
    company_name = str(company["company_name"])

    data = [
        [
            Paragraph(
                company_name,
                styles["TearTitle"],
            )
        ],
        [
            Paragraph(
                f"{company_id}  |  {sector}",
                styles["TearSubtitle"],
            )
        ],
    ]

    table = Table(
        data,
        colWidths=[180 * mm],
        rowHeights=[11 * mm, 6 * mm],
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    NAVY,
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    3,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    2,
                ),
            ]
        )
    )

    return table


def get_latest(df):
    if df.empty:
        return None

    data = df.copy()

    data["year"] = pd.to_numeric(
        data["year"],
        errors="coerce",
    )

    data = data.dropna(
        subset=["year"]
    ).sort_values("year")

    if data.empty:
        return None

    return data.iloc[-1]


def get_numeric(row, column):
    if row is None:
        return None

    if column not in row.index:
        return None

    value = pd.to_numeric(
        row[column],
        errors="coerce",
    )

    if pd.isna(value):
        return None

    return float(value)


def kpi_tiles(
    company,
    pl,
    ratios,
    market_cap,
    styles,
):
    latest_pl = get_latest(pl)
    latest_ratios = get_latest(ratios)
    latest_market_cap = get_latest(market_cap)

    revenue = get_numeric(
        latest_pl,
        "sales",
    )

    net_profit = get_numeric(
        latest_pl,
        "net_profit",
    )

    roe = get_numeric(
        latest_ratios,
        "return_on_equity_pct",
    )

    roce = get_numeric(
        company,
        "roce_percentage",
    )

    pe = get_numeric(
        latest_market_cap,
        "pe_ratio",
    )

    debt_equity = get_numeric(
        latest_ratios,
        "debt_to_equity",
    )

    tiles = [
        (
            "Revenue",
            format_number(revenue),
        ),
        (
            "Net Profit",
            format_number(net_profit),
        ),
        (
            "ROE",
            format_pct(roe),
        ),
        (
            "ROCE",
            format_pct(roce),
        ),
        (
            "P/E",
            format_number(pe),
        ),
        (
            "Debt / Equity",
            format_number(debt_equity),
        ),
    ]

    rows = []

    for i in range(0, 6, 3):
        row = []

        for label, value in tiles[i:i + 3]:
            cell = [
                Paragraph(
                    label,
                    styles["TileLabel"],
                ),
                Spacer(
                    1,
                    1.5 * mm,
                ),
                Paragraph(
                    value,
                    styles["TileValue"],
                ),
            ]

            row.append(cell)

        rows.append(row)

    table = Table(
        rows,
        colWidths=[
            59 * mm,
            59 * mm,
            59 * mm,
        ],
        rowHeights=[
            18 * mm,
            18 * mm,
        ],
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    LIGHT_BLUE,
                ),
                (
                    "INNERGRID",
                    (0, 0),
                    (-1, -1),
                    2,
                    WHITE,
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "ALIGN",
                    (0, 0),
                    (-1, -1),
                    "CENTER",
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    4,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    4,
                ),
            ]
        )
    )

    return table


def create_revenue_profit_chart(
    pl,
    company_id,
):
    if pl.empty:
        return None

    data = pl[
        [
            "year",
            "sales",
            "net_profit",
        ]
    ].copy()

    data["year"] = pd.to_numeric(
        data["year"],
        errors="coerce",
    )

    data["sales"] = pd.to_numeric(
        data["sales"],
        errors="coerce",
    )

    data["net_profit"] = pd.to_numeric(
        data["net_profit"],
        errors="coerce",
    )

    data = data.dropna(
        subset=["year"]
    ).sort_values("year").tail(10)

    if data.empty:
        return None

    path = (
        CHART_OUTPUT
        / f"{company_id}_revenue_profit.png"
    )

    fig, ax = plt.subplots(
        figsize=(5.4, 2.5)
    )

    x = range(len(data))
    width = 0.38

    ax.bar(
        [
            i - width / 2
            for i in x
        ],
        data["sales"].fillna(0),
        width,
        label="Revenue",
    )

    ax.bar(
        [
            i + width / 2
            for i in x
        ],
        data["net_profit"].fillna(0),
        width,
        label="Net Profit",
    )

    ax.set_xticks(list(x))

    ax.set_xticklabels(
        data["year"]
        .astype(int)
        .astype(str),
        rotation=45,
        ha="right",
    )

    ax.set_title(
        "Revenue and Net Profit — 10 Years",
        fontsize=9,
    )

    ax.tick_params(
        labelsize=7
    )

    ax.legend(
        fontsize=7
    )

    ax.grid(
        axis="y",
        alpha=0.25,
    )

    fig.tight_layout()

    fig.savefig(
        path,
        dpi=160,
        bbox_inches="tight",
    )

    plt.close(fig)

    return path


def create_roe_roce_chart(
    ratios,
    company,
    company_id,
):
    if ratios.empty:
        return None

    data = ratios[
        [
            "year",
            "return_on_equity_pct",
        ]
    ].copy()

    data["year"] = pd.to_numeric(
        data["year"],
        errors="coerce",
    )

    data[
        "return_on_equity_pct"
    ] = pd.to_numeric(
        data["return_on_equity_pct"],
        errors="coerce",
    )

    data = data.dropna(
        subset=["year"]
    ).sort_values("year").tail(10)

    roce = pd.to_numeric(
        company.get("roce_percentage"),
        errors="coerce",
    )

    if data.empty:
        return None

    path = (
        CHART_OUTPUT
        / f"{company_id}_roe_roce.png"
    )

    fig, ax1 = plt.subplots(
        figsize=(5.4, 2.5)
    )

    ax2 = ax1.twinx()

    ax1.plot(
        data["year"],
        data["return_on_equity_pct"],
        marker="o",
        linewidth=1.5,
        label="ROE",
    )

    if pd.notna(roce):
        ax2.plot(
            data["year"],
            [float(roce)] * len(data),
            marker="s",
            linewidth=1.3,
            linestyle="--",
            label="ROCE",
        )

    ax1.set_title(
        "ROE and ROCE Trend",
        fontsize=9,
    )

    ax1.set_xlabel(
        "Year",
        fontsize=7,
    )

    ax1.set_ylabel(
        "ROE (%)",
        fontsize=7,
    )

    ax2.set_ylabel(
        "ROCE (%)",
        fontsize=7,
    )

    ax1.tick_params(
        labelsize=7
    )

    ax2.tick_params(
        labelsize=7
    )

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()

    ax1.legend(
        lines1 + lines2,
        labels1 + labels2,
        fontsize=7,
        loc="best",
    )

    ax1.grid(
        alpha=0.25
    )

    fig.tight_layout()

    fig.savefig(
        path,
        dpi=160,
        bbox_inches="tight",
    )

    plt.close(fig)

    return path


def create_balance_chart(
    bs,
    company_id,
):
    if bs.empty:
        return None

    data = bs[
        [
            "year",
            "equity_capital",
            "reserves",
            "borrowings",
            "other_liabilities",
        ]
    ].copy()

    for column in data.columns:
        if column != "year":
            data[column] = pd.to_numeric(
                data[column],
                errors="coerce",
            ).fillna(0)

    data["year"] = pd.to_numeric(
        data["year"],
        errors="coerce",
    )

    data = data.dropna(
        subset=["year"]
    ).sort_values("year").tail(10)

    if data.empty:
        return None

    data["equity"] = (
        data["equity_capital"]
        + data["reserves"]
    )

    path = (
        CHART_OUTPUT
        / f"{company_id}_balance_sheet.png"
    )

    fig, ax = plt.subplots(
        figsize=(10.5, 2.5)
    )

    ax.bar(
        data["year"],
        data["equity"],
        label="Equity",
    )

    ax.bar(
        data["year"],
        data["borrowings"],
        bottom=data["equity"],
        label="Borrowings",
    )

    bottom = (
        data["equity"]
        + data["borrowings"]
    )

    ax.bar(
        data["year"],
        data["other_liabilities"],
        bottom=bottom,
        label="Other Liabilities",
    )

    ax.set_title(
        "Balance Sheet Composition — 10 Years",
        fontsize=9,
    )

    ax.tick_params(
        labelsize=7
    )

    ax.legend(
        fontsize=7
    )

    ax.grid(
        axis="y",
        alpha=0.25,
    )

    fig.tight_layout()

    fig.savefig(
        path,
        dpi=160,
        bbox_inches="tight",
    )

    plt.close(fig)

    return path


def create_cashflow_chart(
    cf,
    company_id,
):
    latest = get_latest(cf)

    if latest is None:
        return None

    cfo = get_numeric(
        latest,
        "operating_activity",
    )

    cfi = get_numeric(
        latest,
        "investing_activity",
    )

    cff = get_numeric(
        latest,
        "financing_activity",
    )

    net_cash = get_numeric(
        latest,
        "net_cash_flow",
    )

    if cfo is None and cfi is None and cff is None:
        return None

    cfo = 0 if cfo is None else cfo
    cfi = 0 if cfi is None else cfi
    cff = 0 if cff is None else cff

    components = [
        ("CFO", cfo),
        ("CFI", cfi),
        ("CFF", cff),
    ]

    running = 0
    bottoms = []
    heights = []

    for _, value in components:
        new_value = running + value

        bottoms.append(
            min(running, new_value)
        )

        heights.append(
            abs(value)
        )

        running = new_value

    if net_cash is None:
        net_cash = running

    labels = [
        "CFO",
        "CFI",
        "CFF",
        "Net Cash Flow",
    ]

    values = [
        cfo,
        cfi,
        cff,
        net_cash,
    ]

    path = (
        CHART_OUTPUT
        / f"{company_id}_cashflow.png"
    )

    fig, ax = plt.subplots(
        figsize=(5.4, 2.5)
    )

    positions = range(4)

    ax.bar(
        [0],
        [heights[0]],
        bottom=[bottoms[0]],
        width=0.55,
    )

    ax.bar(
        [1],
        [heights[1]],
        bottom=[bottoms[1]],
        width=0.55,
    )

    ax.bar(
        [2],
        [heights[2]],
        bottom=[bottoms[2]],
        width=0.55,
    )

    ax.bar(
        [3],
        [net_cash],
        bottom=[0 if net_cash >= 0 else net_cash],
        width=0.55,
    )

    cumulative_values = [
        cfo,
        cfo + cfi,
        cfo + cfi + cff,
    ]

    for index, cumulative in enumerate(
        cumulative_values
    ):
        if index < 2:
            ax.plot(
                [index + 0.275, index + 1 - 0.275],
                [cumulative, cumulative],
                linewidth=0.8,
                linestyle="--",
            )

    ax.set_xticks(
        list(positions)
    )

    ax.set_xticklabels(
        labels,
        fontsize=7,
    )

    ax.set_title(
        f"Cash Flow Waterfall — {int(latest['year'])}",
        fontsize=9,
    )

    ax.tick_params(
        labelsize=7
    )

    ax.axhline(
        0,
        linewidth=0.8,
    )

    ax.grid(
        axis="y",
        alpha=0.25,
    )

    fig.tight_layout()

    fig.savefig(
        path,
        dpi=160,
        bbox_inches="tight",
    )

    plt.close(fig)

    return path


def pros_cons_section(
    company_id,
    styles,
):
    data = get_pros_cons(company_id)

    if data.empty:
        pros = pd.DataFrame()
        cons = pd.DataFrame()
    else:
        pros = data[
            data["type"].str.lower()
            == "pro"
        ].copy()

        cons = data[
            data["type"].str.lower()
            == "con"
        ].copy()

    pros = pros.sort_values(
        "confidence_pct",
        ascending=False,
    ).head(5)

    cons = cons.sort_values(
        "confidence_pct",
        ascending=False,
    ).head(5)

    left = [
        Paragraph(
            "Pros",
            styles["SectionTitle"],
        )
    ]

    for _, row in pros.iterrows():
        left.append(
            Paragraph(
                f"• {row['text']}",
                styles["BulletGreen"],
            )
        )

    if len(left) == 1:
        left.append(
            Paragraph(
                "• No generated pros available",
                styles["BulletGreen"],
            )
        )

    right = [
        Paragraph(
            "Cons",
            styles["SectionTitle"],
        )
    ]

    for _, row in cons.iterrows():
        right.append(
            Paragraph(
                f"• {row['text']}",
                styles["BulletRed"],
            )
        )

    if len(right) == 1:
        right.append(
            Paragraph(
                "• No generated cons available",
                styles["BulletRed"],
            )
        )

    table = Table(
        [[left, right]],
        colWidths=[
            88 * mm,
            88 * mm,
        ],
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (0, 0),
                    LIGHT_GREEN,
                ),
                (
                    "BACKGROUND",
                    (1, 0),
                    (1, 0),
                    LIGHT_RED,
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP",
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

    return table


def capital_badge(
    company_id,
    styles,
):
    data = get_cashflow_intelligence(
        company_id
    )

    label = "N/A"

    if not data.empty:
        value = data.iloc[0].get(
            "capital_allocation_label"
        )

        if pd.notna(value):
            label = str(value)

    table = Table(
        [
            [
                Paragraph(
                    f"Capital Allocation: {label}",
                    styles["Badge"],
                )
            ]
        ],
        colWidths=[176 * mm],
        rowHeights=[10 * mm],
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    NAVY,
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "ALIGN",
                    (0, 0),
                    (-1, -1),
                    "CENTER",
                ),
            ]
        )
    )

    return table


def generate_tearsheet(
    company_id,
    output_path,
):
    TEST_OUTPUT.mkdir(
        parents=True,
        exist_ok=True,
    )

    CHART_OUTPUT.mkdir(
        parents=True,
        exist_ok=True,
    )

    company = get_company(
        company_id
    )

    sector = get_sector(
        company_id
    )

    pl = get_profit_loss(
        company_id
    )

    bs = get_balance_sheet(
        company_id
    )

    cf = get_cash_flow(
        company_id
    )

    ratios = get_ratios(
        company_id
    )

    market_cap = get_market_cap(
        company_id
    )

    styles = make_styles()

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        rightMargin=15 * mm,
        leftMargin=15 * mm,
        topMargin=12 * mm,
        bottomMargin=12 * mm,
        title=f"{company_id} Company Tearsheet",
    )

    story = []

    story.append(
        header_table(
            company,
            sector,
            styles,
        )
    )

    story.append(
        Spacer(
            1,
            4 * mm,
        )
    )

    story.append(
        kpi_tiles(
            company,
            pl,
            ratios,
            market_cap,
            styles,
        )
    )

    story.append(
        Spacer(
            1,
            4 * mm,
        )
    )

    revenue_chart = (
        create_revenue_profit_chart(
            pl,
            company_id,
        )
    )

    roe_chart = (
        create_roe_roce_chart(
            ratios,
            company,
            company_id,
        )
    )

    chart_cells = []

    if revenue_chart:
        chart_cells.append(
            Image(
                str(revenue_chart),
                width=86 * mm,
                height=40 * mm,
            )
        )
    else:
        chart_cells.append(
            Paragraph(
                "Revenue / Net Profit chart unavailable.",
                styles["Small"],
            )
        )

    if roe_chart:
        chart_cells.append(
            Image(
                str(roe_chart),
                width=86 * mm,
                height=40 * mm,
            )
        )
    else:
        chart_cells.append(
            Paragraph(
                "ROE / ROCE chart unavailable.",
                styles["Small"],
            )
        )

    charts = Table(
        [chart_cells],
        colWidths=[
            88 * mm,
            88 * mm,
        ],
    )

    charts.setStyle(
        TableStyle(
            [
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "ALIGN",
                    (0, 0),
                    (-1, -1),
                    "CENTER",
                ),
            ]
        )
    )

    story.append(charts)

    story.append(
        PageBreak()
    )

    story.append(
        Paragraph(
            "Balance Sheet Composition",
            styles["SectionTitle"],
        )
    )

    balance_chart = (
        create_balance_chart(
            bs,
            company_id,
        )
    )

    if balance_chart:
        story.append(
            Image(
                str(balance_chart),
                width=176 * mm,
                height=40 * mm,
            )
        )
    else:
        story.append(
            Paragraph(
                "Balance sheet composition unavailable.",
                styles["Small"],
            )
        )

    story.append(
        Spacer(
            1,
            2 * mm,
        )
    )

    story.append(
        Paragraph(
            "Latest Cash Flow",
            styles["SectionTitle"],
        )
    )

    cashflow_chart = (
        create_cashflow_chart(
            cf,
            company_id,
        )
    )

    if cashflow_chart:
        story.append(
            Image(
                str(cashflow_chart),
                width=88 * mm,
                height=40 * mm,
            )
        )
    else:
        story.append(
            Paragraph(
                "Cash flow chart unavailable.",
                styles["Small"],
            )
        )

    story.append(
        Spacer(
            1,
            2 * mm,
        )
    )

    story.append(
        pros_cons_section(
            company_id,
            styles,
        )
    )

    story.append(
        Spacer(
            1,
            3 * mm,
        )
    )

    story.append(
        capital_badge(
            company_id,
            styles,
        )
    )

    doc.build(story)

    print(
        f"Generated: {output_path}"
    )


def main():
    companies = [
        "TCS",
        "HDFCBANK",
        "RELIANCE",
        "SUNPHARMA",
        "TATASTEEL",
    ]

    print()
    print("DAY 33 TEARSHEET TEST")
    print("=" * 50)
    print()

    for company_id in companies:
        output_path = (
            TEST_OUTPUT
            / f"{company_id}_tearsheet.pdf"
        )

        try:
            generate_tearsheet(
                company_id,
                output_path,
            )
        except Exception as exc:
            print(
                f"FAILED {company_id}: {exc}"
            )

    print()
    print(
        "Test output directory:"
    )
    print(TEST_OUTPUT)


if __name__ == "__main__":
    main()