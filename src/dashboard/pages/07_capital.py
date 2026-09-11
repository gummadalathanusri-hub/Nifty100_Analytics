import streamlit as st
import pandas as pd
import plotly.express as px

from src.dashboard.utils.db import get_companies, get_ratios

st.set_page_config(
    page_title="Capital Allocation | Nifty 100 Analytics",
    layout="wide"
)

st.title("Capital Allocation")

companies = get_companies()

if companies.empty:
    st.warning("Company data unavailable.")
    st.stop()

patterns = [
    "High Growth & Reinvestment",
    "Dividend Focused",
    "Debt Reduction",
    "Acquisition / Investment",
    "Balanced Allocation",
    "Cash Accumulation",
    "High Capex",
    "Conservative Allocation"
]

company_rows = []

for company_id in companies["id"].drop_duplicates():
    ratios = get_ratios(company_id)

    if ratios.empty:
        continue

    ratios = ratios.sort_values("year")

    latest = ratios.iloc[-1]

    company_name = companies.loc[
        companies["id"].eq(company_id),
        "company_name"
    ].iloc[0]

    fcf = pd.to_numeric(
        latest.get("free_cash_flow_cr"),
        errors="coerce"
    )

    capex = pd.to_numeric(
        latest.get("capex_cr"),
        errors="coerce"
    )

    dividend = pd.to_numeric(
        latest.get("dividend_payout_ratio_pct"),
        errors="coerce"
    )

    debt = pd.to_numeric(
        latest.get("debt_to_equity"),
        errors="coerce"
    )

    revenue_cagr = pd.to_numeric(
        latest.get("revenue_cagr_5yr"),
        errors="coerce"
    )

    if pd.isna(fcf):
        fcf = 0.0

    if pd.isna(capex):
        capex = 0.0

    if pd.isna(dividend):
        dividend = 0.0

    if pd.isna(debt):
        debt = 0.0

    if pd.isna(revenue_cagr):
        revenue_cagr = 0.0

    if capex > 0 and revenue_cagr >= 15:
        pattern = "High Growth & Reinvestment"
    elif dividend >= 50 and fcf > 0:
        pattern = "Dividend Focused"
    elif debt > 0 and debt < 0.2 and fcf > 0:
        pattern = "Debt Reduction"
    elif capex > fcf and capex > 0:
        pattern = "High Capex"
    elif fcf > 0 and dividend >= 20:
        pattern = "Balanced Allocation"
    elif fcf > 0 and dividend < 10 and capex < fcf:
        pattern = "Cash Accumulation"
    elif capex > 0 and fcf < 0:
        pattern = "Acquisition / Investment"
    else:
        pattern = "Conservative Allocation"

    company_rows.append({
        "company_id": company_id,
        "company_name": company_name,
        "pattern": pattern,
        "fcf": fcf,
        "capex": capex,
        "dividend_payout": dividend,
        "debt_to_equity": debt,
        "revenue_cagr": revenue_cagr
    })

allocation_df = pd.DataFrame(company_rows)

if allocation_df.empty:
    st.warning("Capital allocation data unavailable.")
    st.stop()

st.subheader("Capital Allocation Patterns")

pattern_counts = (
    allocation_df["pattern"]
    .value_counts()
    .reindex(patterns, fill_value=0)
    .reset_index()
)

pattern_counts.columns = ["Pattern", "Company Count"]

fig = px.treemap(
    pattern_counts,
    path=["Pattern"],
    values="Company Count",
    title="Nifty 100 Capital Allocation Patterns"
)

fig.update_layout(
    height=600,
    margin=dict(l=20, r=20, t=60, b=20)
)

st.plotly_chart(
    fig,
    width="stretch"
)

selected_pattern = st.selectbox(
    "Select Capital Allocation Pattern",
    patterns
)

selected_df = allocation_df[
    allocation_df["pattern"].eq(selected_pattern)
].copy()

st.subheader(
    f"{selected_pattern} — {len(selected_df)} Companies"
)

display_df = selected_df[
    [
        "company_id",
        "company_name",
        "fcf",
        "capex",
        "dividend_payout",
        "debt_to_equity",
        "revenue_cagr"
    ]
].copy()

display_df.columns = [
    "Company ID",
    "Company Name",
    "FCF",
    "Capex",
    "Dividend Payout %",
    "D/E",
    "Revenue CAGR 5yr"
]

for column in display_df.columns[2:]:
    display_df[column] = pd.to_numeric(
        display_df[column],
        errors="coerce"
    ).round(2)

st.dataframe(
    display_df,
    width="stretch",
    hide_index=True
)

st.subheader("Pattern Summary")

summary = (
    allocation_df
    .groupby("pattern")
    .agg(
        Companies=("company_id", "count"),
        Median_FCF=("fcf", "median"),
        Median_Capex=("capex", "median"),
        Median_Dividend_Payout=("dividend_payout", "median"),
        Median_DE=("debt_to_equity", "median"),
        Median_Revenue_CAGR=("revenue_cagr", "median")
    )
    .reset_index()
)

summary.columns = [
    "Pattern",
    "Companies",
    "Median FCF",
    "Median Capex",
    "Median Dividend Payout %",
    "Median D/E",
    "Median Revenue CAGR"
]

for column in summary.columns[2:]:
    summary[column] = pd.to_numeric(
        summary[column],
        errors="coerce"
    ).round(2)

st.dataframe(
    summary,
    width="stretch",
    hide_index=True
)