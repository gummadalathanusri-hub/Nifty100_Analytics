import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from src.dashboard.utils.db import get_peers, get_ratios

st.set_page_config(
    page_title="Peers | Nifty 100 Analytics",
    layout="wide"
)

st.title("Peer Comparison")

peer_groups = [
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
    "Steel"
]

selected_group = st.selectbox(
    "Select Peer Group",
    peer_groups
)

peers = get_peers(selected_group)

if peers.empty:
    st.warning("No companies found for this peer group.")
    st.stop()

company_options = peers["company_id"].tolist()

selected_company = st.selectbox(
    "Select Company",
    company_options,
    format_func=lambda x: peers.loc[
        peers["company_id"].eq(x), "company_name"
    ].iloc[0]
)

benchmark_rows = peers[peers["is_benchmark"].eq(1)]

if not benchmark_rows.empty:
    benchmark_company = benchmark_rows.iloc[0]["company_id"]
else:
    benchmark_company = selected_company

metrics = [
    "return_on_equity_pct",
    "debt_to_equity",
    "free_cash_flow_cr",
    "revenue_cagr_5yr",
    "pat_cagr_5yr",
    "operating_profit_margin_pct",
    "interest_coverage",
    "asset_turnover"
]

metric_labels = {
    "return_on_equity_pct": "ROE",
    "debt_to_equity": "D/E",
    "free_cash_flow_cr": "FCF",
    "revenue_cagr_5yr": "Revenue CAGR",
    "pat_cagr_5yr": "PAT CAGR",
    "operating_profit_margin_pct": "OPM",
    "interest_coverage": "Interest Coverage",
    "asset_turnover": "Asset Turnover"
}

peer_data = []

for company_id in company_options:
    ratio_data = get_ratios(company_id)

    if ratio_data.empty:
        continue

    latest = ratio_data.sort_values("year").iloc[-1]

    row = {
        "company_id": company_id,
        "company_name": peers.loc[
            peers["company_id"].eq(company_id),
            "company_name"
        ].iloc[0],
        "is_benchmark": int(
            peers.loc[
                peers["company_id"].eq(company_id),
                "is_benchmark"
            ].iloc[0]
        )
    }

    for metric in metrics:
        row[metric] = pd.to_numeric(
            latest.get(metric),
            errors="coerce"
        )

    peer_data.append(row)

peer_df = pd.DataFrame(peer_data)

if peer_df.empty:
    st.warning("Peer financial data unavailable.")
    st.stop()

selected_row = peer_df[
    peer_df["company_id"].eq(selected_company)
].iloc[0]

peer_average = peer_df[metrics].mean(numeric_only=True)

st.subheader(
    f"{selected_row['company_name']} vs {selected_group} Average"
)

radar_values = []

for metric in metrics:
    company_value = selected_row[metric]
    average_value = peer_average[metric]

    if pd.isna(company_value):
        company_value = 0

    if pd.isna(average_value):
        average_value = 0

    radar_values.append(
        [
            metric_labels[metric],
            company_value,
            average_value
        ]
    )

categories = [x[0] for x in radar_values]
company_values = [x[1] for x in radar_values]
average_values = [x[2] for x in radar_values]

categories_closed = categories + [categories[0]]
company_values_closed = company_values + [company_values[0]]
average_values_closed = average_values + [average_values[0]]

fig = go.Figure()

fig.add_trace(
    go.Scatterpolar(
        r=company_values_closed,
        theta=categories_closed,
        fill="toself",
        name=str(selected_row["company_name"])
    )
)

fig.add_trace(
    go.Scatterpolar(
        r=average_values_closed,
        theta=categories_closed,
        fill="toself",
        name=f"{selected_group} Average"
    )
)

fig.update_layout(
    polar=dict(
        radialaxis=dict(
            visible=True
        )
    ),
    height=600,
    margin=dict(l=40, r=40, t=60, b=40)
)

st.plotly_chart(fig, width="stretch")

st.subheader(f"{selected_group} Companies")

display_columns = [
    "company_id",
    "company_name",
    "return_on_equity_pct",
    "debt_to_equity",
    "free_cash_flow_cr",
    "revenue_cagr_5yr",
    "pat_cagr_5yr",
    "operating_profit_margin_pct",
    "interest_coverage",
    "asset_turnover"
]

display_df = peer_df[display_columns].copy()

display_df.columns = [
    "Company ID",
    "Company Name",
    "ROE",
    "D/E",
    "FCF",
    "Revenue CAGR",
    "PAT CAGR",
    "OPM",
    "Interest Coverage",
    "Asset Turnover"
]

numeric_display = display_df.columns[2:]

for column in numeric_display:
    display_df[column] = pd.to_numeric(
        display_df[column],
        errors="coerce"
    ).round(2)

def highlight_benchmark(row):
    if row["Company ID"] == benchmark_company:
        return ["font-weight: bold"] * len(row)
    return [""] * len(row)

st.dataframe(
    display_df.style.apply(highlight_benchmark, axis=1),
    width="stretch",
    hide_index=True
)

st.caption(
    f"Benchmark company: {benchmark_company}"
)