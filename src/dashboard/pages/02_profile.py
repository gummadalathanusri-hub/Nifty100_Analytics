import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from src.dashboard.utils.db import (
    get_companies,
    get_ratios,
    get_pl,
    get_bs,
    get_sectors,
    get_pros_cons,
)

st.set_page_config(
    page_title="Company Profile | Nifty 100 Analytics",
    layout="wide"
)

companies = get_companies()

company_options = companies["id"].dropna().astype(str).tolist()

if not company_options:
    st.error("No companies available.")
    st.stop()

selected_ticker = st.selectbox(
    "Search company / ticker",
    company_options,
    index=0
)

company_row = companies[
    companies["id"].astype(str) == selected_ticker
]

if company_row.empty:
    st.error("Ticker not found — please try another")
    st.stop()

company = company_row.iloc[0]

ratios = get_ratios(selected_ticker)
pl = get_pl(selected_ticker)
bs = get_bs(selected_ticker)
sectors = get_sectors()
pros_cons = get_pros_cons(selected_ticker)

sector_row = sectors[
    sectors["company_id"].astype(str) == selected_ticker
]

if not sector_row.empty:
    sector = sector_row.iloc[0]["broad_sector"]
    sub_sector = sector_row.iloc[0]["sub_sector"]
else:
    sector = "N/A"
    sub_sector = "N/A"

st.title("Company Profile")
st.subheader(company["company_name"])

info1, info2, info3, info4 = st.columns(4)

with info1:
    st.markdown("**Sector**")
    st.write(sector if pd.notna(sector) else "N/A")

with info2:
    st.markdown("**Sub-sector**")
    st.write(sub_sector if pd.notna(sub_sector) else "N/A")

with info3:
    st.markdown("**NSE Ticker**")
    st.write(selected_ticker)

with info4:
    st.markdown("**Company ID**")
    st.write(company["id"])

about = company.get("about_company")

if pd.notna(about) and str(about).strip():
    st.markdown("**About Company**")
    st.write(str(about).strip())
else:
    st.info("About company information unavailable.")

st.markdown("---")

if ratios.empty:
    st.warning("Financial ratio data unavailable for this company.")
    latest_ratio = None
else:
    ratio_years = pd.to_numeric(
        ratios["year"],
        errors="coerce"
    )

    ratios = ratios.copy()
    ratios["year"] = ratio_years

    latest_ratio_df = (
        ratios
        .dropna(subset=["year"])
        .sort_values("year")
        .tail(1)
    )

    latest_ratio = (
        latest_ratio_df.iloc[0]
        if not latest_ratio_df.empty
        else None
    )

if latest_ratio is not None:
    roe = latest_ratio.get("return_on_equity_pct")
    de = latest_ratio.get("debt_to_equity")
    revenue_cagr = latest_ratio.get("revenue_cagr_5yr")
    fcf = latest_ratio.get("free_cash_flow_cr")
else:
    roe = None
    de = None
    revenue_cagr = None
    fcf = None

if not pl.empty:
    pl = pl.copy()

    pl["year"] = pd.to_numeric(
        pl["year"],
        errors="coerce"
    )

    latest_pl = (
        pl
        .dropna(subset=["year"])
        .sort_values("year")
        .tail(1)
    )
else:
    latest_pl = pd.DataFrame()

if not latest_pl.empty:
    latest_pl_row = latest_pl.iloc[0]

    net_profit = pd.to_numeric(
        pd.Series([latest_pl_row.get("net_profit")]),
        errors="coerce"
    ).iloc[0]

    sales = pd.to_numeric(
        pd.Series([latest_pl_row.get("sales")]),
        errors="coerce"
    ).iloc[0]

    if pd.notna(net_profit) and pd.notna(sales) and sales != 0:
        npm = (net_profit / sales) * 100
    else:
        npm = None
else:
    npm = None

pl_for_roce = pl.copy()
bs_for_roce = bs.copy()

if not pl_for_roce.empty:
    if "operating_profit" in pl_for_roce.columns:
        pl_for_roce["operating_profit"] = pd.to_numeric(
            pl_for_roce["operating_profit"],
            errors="coerce"
        )

if not bs_for_roce.empty:
    for column in [
        "equity_capital",
        "reserves",
        "borrowings"
    ]:
        if column in bs_for_roce.columns:
            bs_for_roce[column] = pd.to_numeric(
                bs_for_roce[column],
                errors="coerce"
            )

required_pl_columns = [
    "year",
    "operating_profit"
]

required_bs_columns = [
    "year",
    "equity_capital",
    "reserves",
    "borrowings"
]

if (
    not pl_for_roce.empty
    and not bs_for_roce.empty
    and all(
        column in pl_for_roce.columns
        for column in required_pl_columns
    )
    and all(
        column in bs_for_roce.columns
        for column in required_bs_columns
    )
):
    roce_df = pl_for_roce[
        required_pl_columns
    ].merge(
        bs_for_roce[
            required_bs_columns
        ],
        on="year",
        how="inner"
    )
else:
    roce_df = pd.DataFrame(
        columns=[
            "year",
            "operating_profit",
            "equity_capital",
            "reserves",
            "borrowings",
            "capital_employed",
            "roce"
        ]
    )

if not roce_df.empty:
    roce_df["capital_employed"] = (
        roce_df["equity_capital"].fillna(0)
        + roce_df["reserves"].fillna(0)
        + roce_df["borrowings"].fillna(0)
    )

    roce_df["roce"] = (
        roce_df["operating_profit"]
        / roce_df["capital_employed"]
        * 100
    )

    roce_df.loc[
        roce_df["capital_employed"] == 0,
        "roce"
    ] = None

    latest_roce = (
        roce_df
        .dropna(subset=["roce"])
        .sort_values("year")
        .tail(1)
    )

    if not latest_roce.empty:
        roce = latest_roce.iloc[0]["roce"]
    else:
        roce = None
else:
    roce = None

if "roce" not in roce_df.columns:
    roce_df["roce"] = pd.Series(
        dtype="float64"
    )

def format_percent(value):
    if value is None or pd.isna(value):
        return "N/A"

    return f"{float(value):,.2f}%"

def format_number(value):
    if value is None or pd.isna(value):
        return "N/A"

    return f"{float(value):,.2f}"

st.subheader("Key Financial Metrics")

k1, k2, k3 = st.columns(3)
k4, k5, k6 = st.columns(3)

with k1:
    st.metric(
        "ROE",
        format_percent(roe)
    )

with k2:
    st.metric(
        "ROCE",
        format_percent(roce)
    )

with k3:
    st.metric(
        "Net Profit Margin",
        format_percent(npm)
    )

with k4:
    st.metric(
        "D/E",
        format_number(de)
    )

with k5:
    st.metric(
        "Revenue CAGR 5yr",
        format_percent(revenue_cagr)
    )

with k6:
    st.metric(
        "FCF Latest Year",
        format_number(fcf)
    )

st.markdown("---")

st.subheader("Revenue and Net Profit — 10 Year Trend")

if not pl.empty and all(
    column in pl.columns
    for column in ["year", "sales", "net_profit"]
):
    chart_df = pl[
        ["year", "sales", "net_profit"]
    ].copy()

    chart_df["year"] = pd.to_numeric(
        chart_df["year"],
        errors="coerce"
    )

    chart_df["sales"] = pd.to_numeric(
        chart_df["sales"],
        errors="coerce"
    )

    chart_df["net_profit"] = pd.to_numeric(
        chart_df["net_profit"],
        errors="coerce"
    )

    chart_df = (
        chart_df
        .dropna(subset=["year"])
        .sort_values("year")
        .tail(10)
    )
else:
    chart_df = pd.DataFrame()

if not chart_df.empty:
    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=chart_df["year"],
            y=chart_df["sales"],
            name="Revenue"
        )
    )

    fig.add_trace(
        go.Bar(
            x=chart_df["year"],
            y=chart_df["net_profit"],
            name="Net Profit"
        )
    )

    fig.update_layout(
        barmode="group",
        height=500,
        xaxis_title="Year",
        yaxis_title="Amount (₹ Cr)",
        hovermode="x unified"
    )

    st.plotly_chart(
        fig,
        width="stretch"
    )
else:
    st.info(
        "Revenue and profit data unavailable."
    )

st.subheader("ROE and ROCE — 10 Year Trend")

if (
    not ratios.empty
    and "year" in ratios.columns
    and "return_on_equity_pct" in ratios.columns
):
    roe_df = ratios[
        ["year", "return_on_equity_pct"]
    ].copy()

    roe_df["year"] = pd.to_numeric(
        roe_df["year"],
        errors="coerce"
    )

    roe_df["roe"] = pd.to_numeric(
        roe_df["return_on_equity_pct"],
        errors="coerce"
    )

    roe_df = roe_df[
        ["year", "roe"]
    ]
else:
    roe_df = pd.DataFrame(
        columns=["year", "roe"]
    )

if "roce" not in roce_df.columns:
    roce_df["roce"] = pd.Series(
        dtype="float64"
    )

performance_df = roe_df.merge(
    roce_df[
        ["year", "roce"]
    ],
    on="year",
    how="outer"
)

performance_df = (
    performance_df
    .dropna(subset=["year"])
    .sort_values("year")
    .tail(10)
)

if not performance_df.empty:
    fig2 = go.Figure()

    fig2.add_trace(
        go.Scatter(
            x=performance_df["year"],
            y=performance_df["roe"],
            name="ROE",
            mode="lines+markers"
        )
    )

    fig2.add_trace(
        go.Scatter(
            x=performance_df["year"],
            y=performance_df["roce"],
            name="ROCE",
            mode="lines+markers"
        )
    )

    fig2.update_layout(
        height=500,
        xaxis_title="Year",
        yaxis_title="Percentage",
        hovermode="x unified"
    )

    st.plotly_chart(
        fig2,
        width="stretch"
    )
else:
    st.info(
        "ROE/ROCE history unavailable."
    )

st.subheader("Pros & Cons")

if not pros_cons.empty:
    pros_value = pros_cons.iloc[0].get("pros")
    cons_value = pros_cons.iloc[0].get("cons")

    col_pros, col_cons = st.columns(2)

    with col_pros:
        st.markdown("### ✓ Pros")

        if (
            pd.notna(pros_value)
            and str(pros_value).strip()
        ):
            for item in str(pros_value).split("\n"):
                if item.strip():
                    st.success(item.strip())
        else:
            st.info("No pros available.")

    with col_cons:
        st.markdown("### ✗ Cons")

        if (
            pd.notna(cons_value)
            and str(cons_value).strip()
        ):
            for item in str(cons_value).split("\n"):
                if item.strip():
                    st.error(item.strip())
        else:
            st.info("No cons available.")
else:
    st.info(
        "Pros and cons information unavailable."
    )

st.caption(
    f"Showing available financial history for {selected_ticker}."
)