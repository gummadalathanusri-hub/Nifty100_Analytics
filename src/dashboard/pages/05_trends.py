import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from src.dashboard.utils.db import get_companies, get_ratios

st.set_page_config(
    page_title="Trends | Nifty 100 Analytics",
    layout="wide"
)

st.title("Company Trends")

companies = get_companies()

if companies.empty:
    st.warning("Company data unavailable.")
    st.stop()

company_ids = companies["id"].tolist()

selected_company = st.selectbox(
    "Search Company / Ticker",
    company_ids,
    format_func=lambda x: companies.loc[
        companies["id"].eq(x), "company_name"
    ].iloc[0]
)

metric_options = {
    "Revenue": "sales",
    "Net Profit": "net_profit",
    "ROE": "return_on_equity_pct",
    "ROCE": "roce_percentage",
    "Operating Profit Margin": "operating_profit_margin_pct",
    "Net Profit Margin": "net_profit_margin_pct",
    "Debt to Equity": "debt_to_equity",
    "Free Cash Flow": "free_cash_flow_cr",
    "EPS": "earnings_per_share"
}

selected_metrics = st.multiselect(
    "Select Metrics",
    list(metric_options.keys()),
    default=["Revenue", "Net Profit"],
    max_selections=3
)

if not selected_metrics:
    st.info("Please select at least one metric.")
    st.stop()

ratios = get_ratios(selected_company)

if ratios.empty:
    st.warning("No trend data available for this company.")
    st.stop()

ratios = ratios.sort_values("year").copy()

if "sales" not in ratios.columns or "net_profit" not in ratios.columns:
    from src.dashboard.utils.db import get_pl

    pl = get_pl(selected_company)

    if not pl.empty:
        pl = pl[["year", "sales", "net_profit"]].copy()
        ratios = ratios.merge(
            pl,
            on="year",
            how="left"
        )

companies_lookup = companies[
    ["id", "company_name"]
].drop_duplicates()

company_name = companies_lookup.loc[
    companies_lookup["id"].eq(selected_company),
    "company_name"
].iloc[0]

st.subheader(f"{company_name} — 10-Year Trend")

trend_df = ratios.copy()

trend_df["year"] = pd.to_numeric(
    trend_df["year"],
    errors="coerce"
)

trend_df = trend_df[
    trend_df["year"].between(2015, 2024)
].copy()

trend_df = trend_df.sort_values("year")

if trend_df.empty:
    st.info("No 10-year trend data available.")
    st.stop()

fig = go.Figure()

for metric_label in selected_metrics:
    column = metric_options[metric_label]

    if column not in trend_df.columns:
        continue

    values = pd.to_numeric(
        trend_df[column],
        errors="coerce"
    )

    if values.notna().sum() == 0:
        continue

    fig.add_trace(
        go.Scatter(
            x=trend_df["year"],
            y=values,
            mode="lines+markers",
            name=metric_label,
            hovertemplate=(
                f"{metric_label}: %{{y:.2f}}"
                "<br>Year: %{x}"
                "<extra></extra>"
            )
        )
    )

if not fig.data:
    st.warning("Selected metrics are unavailable for this company.")
    st.stop()

fig.update_layout(
    xaxis_title="Year",
    yaxis_title="Value",
    height=550,
    hovermode="x unified",
    margin=dict(l=40, r=40, t=50, b=40)
)

st.plotly_chart(
    fig,
    width="stretch"
)

st.subheader("Year-over-Year Change")

yoy_rows = []

for metric_label in selected_metrics:
    column = metric_options[metric_label]

    if column not in trend_df.columns:
        continue

    values = pd.to_numeric(
        trend_df[column],
        errors="coerce"
    )

    yoy = values.pct_change() * 100

    for year, value, change in zip(
        trend_df["year"],
        values,
        yoy
    ):
        yoy_rows.append(
            {
                "Year": year,
                "Metric": metric_label,
                "Value": value,
                "YoY Change %": change
            }
        )

yoy_df = pd.DataFrame(yoy_rows)

if not yoy_df.empty:
    yoy_df["Value"] = yoy_df["Value"].round(2)
    yoy_df["YoY Change %"] = yoy_df["YoY Change %"].round(2)

    st.dataframe(
        yoy_df,
        width="stretch",
        hide_index=True
    )

st.caption(
    "Trend data uses the available financial records. YoY change is calculated from consecutive available years."
)