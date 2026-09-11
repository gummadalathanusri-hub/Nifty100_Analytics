import streamlit as st
import pandas as pd
import plotly.express as px

from src.dashboard.utils.db import (
    get_companies,
    get_all_ratios,
    get_sectors,
)

st.set_page_config(
    page_title="Home | Nifty 100 Analytics",
    layout="wide"
)

st.title("Nifty 100 Analytics")
st.subheader("Industry Overview")

years = list(range(2019, 2025))

selected_year = st.sidebar.selectbox(
    "Select Year",
    years,
    index=len(years) - 1
)

companies = get_companies()
ratios = get_all_ratios(selected_year)
sectors = get_sectors()

numeric_columns = [
    "return_on_equity_pct",
    "debt_to_equity",
    "revenue_cagr_5yr",
    "composite_quality_score",
]

for column in numeric_columns:
    if column in ratios.columns:
        ratios[column] = pd.to_numeric(
            ratios[column],
            errors="coerce"
        )


from src.dashboard.utils.db import _read_sql

valuation = _read_sql("""
    SELECT
        mc.company_id,
        mc.pe_ratio
    FROM market_cap mc
    WHERE mc.year = ?
""", [selected_year])

valuation["pe_ratio"] = pd.to_numeric(
    valuation["pe_ratio"],
    errors="coerce"
)


avg_roe = ratios["return_on_equity_pct"].mean()
median_de = ratios["debt_to_equity"].median()
median_revenue_cagr = ratios["revenue_cagr_5yr"].median()

pe_values = valuation["pe_ratio"].dropna()
median_pe = pe_values.median() if not pe_values.empty else None

debt_free_count = (
    ratios.loc[
        ratios["debt_to_equity"].fillna(-1).eq(0),
        "company_id"
    ]
    .nunique()
)

total_companies = companies["id"].nunique()


def format_value(value, suffix=""):
    if pd.isna(value):
        return "N/A"
    return f"{value:,.2f}{suffix}"


col1, col2, col3 = st.columns(3)
col4, col5, col6 = st.columns(3)

with col1:
    st.metric(
        "Average ROE",
        format_value(avg_roe, "%")
    )

with col2:
    st.metric(
        "Median P/E",
        format_value(median_pe)
    )

with col3:
    st.metric(
        "Median D/E",
        format_value(median_de)
    )

with col4:
    st.metric(
        "Total Companies",
        f"{total_companies:,}"
    )

with col5:
    st.metric(
        "Median Revenue CAGR 5yr",
        format_value(median_revenue_cagr, "%")
    )

with col6:
    st.metric(
        "Debt-Free Companies",
        f"{debt_free_count:,}"
    )

st.markdown("---")

st.subheader("Sector Breakdown")

sector_counts = (
    sectors["broad_sector"]
    .dropna()
    .value_counts()
    .reset_index()
)

sector_counts.columns = ["Sector", "Company Count"]

if not sector_counts.empty:
    fig_sector = px.pie(
        sector_counts,
        names="Sector",
        values="Company Count",
        hole=0.45,
        title=f"Companies by Sector — {selected_year}"
    )

    fig_sector.update_layout(
        height=450,
        margin=dict(l=20, r=20, t=60, b=20)
    )

    st.plotly_chart(
        fig_sector,
        use_container_width=True
    )
else:
    st.info("Sector data unavailable.")


st.subheader(
    f"Top 5 Companies by Composite Quality Score — {selected_year}"
)

top5 = ratios[
    [
        "company_id",
        "company_name",
        "composite_quality_score"
    ]
].copy()

top5 = top5.dropna(
    subset=["composite_quality_score"]
)

top5 = (
    top5
    .sort_values(
        "composite_quality_score",
        ascending=False
    )
    .head(5)
)

if not top5.empty:
    sector_lookup = (
        sectors[
            ["company_id", "broad_sector"]
        ]
        .drop_duplicates("company_id")
    )

    top5 = top5.merge(
        sector_lookup,
        on="company_id",
        how="left"
    )

    top5["composite_quality_score"] = top5[
        "composite_quality_score"
    ].round(2)

    top5 = top5[
        [
            "company_id",
            "company_name",
            "broad_sector",
            "composite_quality_score"
        ]
    ]

    top5.columns = [
        "Company ID",
        "Company Name",
        "Sector",
        "Quality Score"
    ]

    st.dataframe(
        top5,
        use_container_width=True,
        hide_index=True
    )
else:
    st.info(
        "Composite quality score data unavailable "
        f"for {selected_year}."
    )

st.caption(
    f"Dashboard metrics are calculated from available "
    f"database records for {selected_year}."
)