import streamlit as st
import pandas as pd
import plotly.express as px

from src.dashboard.utils.db import get_sectors, get_ratios

st.set_page_config(
    page_title="Sectors | Nifty 100 Analytics",
    layout="wide"
)

st.title("Sector Analysis")

sectors = get_sectors()

if sectors.empty:
    st.warning("Sector data unavailable.")
    st.stop()

sector_names = sorted(
    sectors["broad_sector"].dropna().unique().tolist()
)

selected_sector = st.selectbox(
    "Select Sector",
    sector_names
)

sector_df = sectors[
    sectors["broad_sector"].eq(selected_sector)
].copy()

company_rows = []

for company_id in sector_df["company_id"].drop_duplicates():
    ratios = get_ratios(company_id)

    if ratios.empty:
        continue

    ratios = ratios.sort_values("year")
    latest = ratios.iloc[-1]

    company_name = sector_df.loc[
        sector_df["company_id"].eq(company_id),
        "company_name"
    ].iloc[0]

    sub_sector = sector_df.loc[
        sector_df["company_id"].eq(company_id),
        "sub_sector"
    ].iloc[0]

    market_cap = pd.to_numeric(
        latest.get("market_cap_cr"),
        errors="coerce"
    )

    revenue = pd.to_numeric(
        latest.get("sales"),
        errors="coerce"
    )

    roe = pd.to_numeric(
        latest.get("return_on_equity_pct"),
        errors="coerce"
    )

    if pd.isna(market_cap):
        market_cap = 1.0

    if pd.isna(revenue):
        revenue = 0.0

    if pd.isna(roe):
        roe = 0.0

    company_rows.append({
        "company_id": company_id,
        "company_name": company_name,
        "sub_sector": sub_sector,
        "revenue": revenue,
        "roe": roe,
        "market_cap": market_cap
    })

plot_df = pd.DataFrame(company_rows)

if plot_df.empty:
    st.warning("Financial data unavailable for this sector.")
    st.stop()

st.subheader(f"{selected_sector} — Company Overview")

fig = px.scatter(
    plot_df,
    x="revenue",
    y="roe",
    size="market_cap",
    color="sub_sector",
    hover_name="company_name",
    hover_data={
        "company_id": True,
        "revenue": ":,.2f",
        "roe": ":.2f",
        "market_cap": ":,.2f"
    },
    labels={
        "revenue": "Revenue",
        "roe": "ROE (%)",
        "market_cap": "Market Cap",
        "sub_sector": "Sub-Sector"
    },
    title=f"{selected_sector} — Revenue vs ROE"
)

fig.update_layout(
    height=600,
    margin=dict(l=40, r=40, t=60, b=40)
)

st.plotly_chart(
    fig,
    width="stretch"
)

st.subheader("Sector Median KPIs")

median_df = pd.DataFrame({
    "Metric": [
        "Median ROE",
        "Median Revenue",
        "Median Market Cap"
    ],
    "Value": [
        plot_df["roe"].median(),
        plot_df["revenue"].median(),
        plot_df["market_cap"].median()
    ]
})

median_df["Value"] = median_df["Value"].round(2)

fig_median = px.bar(
    median_df,
    x="Metric",
    y="Value",
    title=f"{selected_sector} — Median KPIs",
    text="Value"
)

fig_median.update_layout(
    height=450,
    margin=dict(l=40, r=40, t=60, b=40)
)

st.plotly_chart(
    fig_median,
    width="stretch"
)

st.subheader("Companies in Sector")

display_df = plot_df.copy()

display_df.columns = [
    "Company ID",
    "Company Name",
    "Sub-Sector",
    "Revenue",
    "ROE",
    "Market Cap"
]

for column in ["Revenue", "ROE", "Market Cap"]:
    display_df[column] = pd.to_numeric(
        display_df[column],
        errors="coerce"
    ).round(2)

st.dataframe(
    display_df,
    width="stretch",
    hide_index=True
)

st.caption(
    "Sector metrics are calculated from the latest available financial record for each company."
)