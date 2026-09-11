import streamlit as st
import pandas as pd

from src.screener.engine import load_financial_ratios, apply_filters

st.set_page_config(
    page_title="Screener | Nifty 100 Analytics",
    layout="wide"
)

st.title("Nifty 100 Stock Screener")

st.sidebar.subheader("Presets")

presets = {
    "Quality": {
        "roe_min": 15,
        "de_max": 1.0,
        "fcf_min": 0,
        "revenue_cagr_5yr_min": 10,
        "pat_cagr_5yr_min": 10,
        "opm_min": 15,
        "pe_max": 100,
        "pb_max": 10,
        "dividend_yield_min": 0,
        "icr_min": 3
    },
    "Value": {
        "roe_min": 10,
        "de_max": 2.0,
        "fcf_min": 0,
        "revenue_cagr_5yr_min": 0,
        "pat_cagr_5yr_min": 0,
        "opm_min": 0,
        "pe_max": 25,
        "pb_max": 3,
        "dividend_yield_min": 1,
        "icr_min": 0
    },
    "Growth": {
        "roe_min": 15,
        "de_max": 1.0,
        "fcf_min": 0,
        "revenue_cagr_5yr_min": 15,
        "pat_cagr_5yr_min": 15,
        "opm_min": 10,
        "pe_max": 100,
        "pb_max": 10,
        "dividend_yield_min": 0,
        "icr_min": 3
    },
    "Dividend": {
        "roe_min": 10,
        "de_max": 2.0,
        "fcf_min": 0,
        "revenue_cagr_5yr_min": 0,
        "pat_cagr_5yr_min": 0,
        "opm_min": 0,
        "pe_max": 100,
        "pb_max": 10,
        "dividend_yield_min": 3,
        "icr_min": 0
    },
    "Debt-Free": {
        "roe_min": 10,
        "de_max": 0.01,
        "fcf_min": 0,
        "revenue_cagr_5yr_min": 0,
        "pat_cagr_5yr_min": 0,
        "opm_min": 0,
        "pe_max": 100,
        "pb_max": 10,
        "dividend_yield_min": 0,
        "icr_min": 0,
        "de_exact": True
    },
    "Turnaround": {
        "roe_min": 0,
        "de_max": 3.0,
        "fcf_min": 0,
        "revenue_cagr_5yr_min": 0,
        "pat_cagr_5yr_min": 0,
        "opm_min": 0,
        "pe_max": 100,
        "pb_max": 10,
        "dividend_yield_min": 0,
        "icr_min": 0
    }
}

preset = st.sidebar.selectbox(
    "Select Preset",
    ["Custom"] + list(presets.keys())
)

defaults = presets.get(
    preset,
    {
        "roe_min": 0,
        "de_max": 10,
        "fcf_min": -100000,
        "revenue_cagr_5yr_min": -100,
        "pat_cagr_5yr_min": -100,
        "opm_min": -100,
        "pe_max": 200,
        "pb_max": 50,
        "dividend_yield_min": 0,
        "icr_min": 0
    }
)

roe_min = st.sidebar.slider(
    "ROE Min (%)",
    0.0,
    100.0,
    float(defaults["roe_min"])
)

de_max = st.sidebar.slider(
    "D/E Max",
    0.0,
    10.0,
    float(defaults["de_max"])
)

fcf_min = st.sidebar.slider(
    "FCF Min (₹ Cr)",
    -100000.0,
    100000.0,
    float(defaults["fcf_min"])
)

revenue_cagr_min = st.sidebar.slider(
    "Revenue CAGR Min (%)",
    -100.0,
    100.0,
    float(defaults["revenue_cagr_5yr_min"])
)

pat_cagr_min = st.sidebar.slider(
    "PAT CAGR Min (%)",
    -100.0,
    100.0,
    float(defaults["pat_cagr_5yr_min"])
)

opm_min = st.sidebar.slider(
    "OPM Min (%)",
    -100.0,
    100.0,
    float(defaults["opm_min"])
)

pe_max = st.sidebar.slider(
    "P/E Max",
    0.0,
    200.0,
    float(defaults["pe_max"])
)

pb_max = st.sidebar.slider(
    "P/B Max",
    0.0,
    50.0,
    float(defaults["pb_max"])
)

dividend_yield_min = st.sidebar.slider(
    "Dividend Yield Min (%)",
    0.0,
    20.0,
    float(defaults["dividend_yield_min"])
)

icr_min = st.sidebar.slider(
    "ICR Min",
    0.0,
    50.0,
    float(defaults["icr_min"])
)

data = load_financial_ratios()

if data.empty:
    st.warning("No screener data available.")
    st.stop()

numeric_columns = [
    "return_on_equity_pct",
    "debt_to_equity",
    "free_cash_flow_cr",
    "revenue_cagr_5yr",
    "pat_cagr_5yr",
    "operating_profit_margin_pct",
    "pe_ratio",
    "pb_ratio",
    "dividend_yield_pct",
    "interest_coverage",
    "composite_quality_score",
    "market_cap_cr",
    "net_profit_cr",
    "sales_cr"
]

for column in numeric_columns:
    if column in data.columns:
        data[column] = pd.to_numeric(
            data[column],
            errors="coerce"
        )

filters = {
    "roe_min": roe_min,
    "de_max": de_max,
    "fcf_min": fcf_min,
    "revenue_cagr_5yr_min": revenue_cagr_min,
    "pat_cagr_5yr_min": pat_cagr_min,
    "opm_min": opm_min,
    "pe_max": pe_max,
    "pb_max": pb_max,
    "dividend_yield_min": dividend_yield_min,
    "icr_min": icr_min
}

if preset == "Debt-Free":
    filters["de_exact"] = True

results = apply_filters(
    data,
    filters
)

st.subheader("Screener Results")

st.metric(
    "Companies Found",
    len(results)
)

if results.empty:
    st.info("No companies match the selected criteria.")
    st.stop()

display_columns = [
    "company_id",
    "company_name",
    "broad_sector",
    "composite_quality_score",
    "return_on_equity_pct",
    "debt_to_equity",
    "free_cash_flow_cr",
    "revenue_cagr_5yr",
    "pat_cagr_5yr",
    "operating_profit_margin_pct",
    "pe_ratio",
    "pb_ratio",
    "dividend_yield_pct",
    "interest_coverage"
]

available_columns = [
    column
    for column in display_columns
    if column in results.columns
]

output = results[available_columns].copy()

output = output.rename(
    columns={
        "company_id": "Company ID",
        "company_name": "Company Name",
        "broad_sector": "Sector",
        "composite_quality_score": "Quality Score",
        "return_on_equity_pct": "ROE %",
        "debt_to_equity": "D/E",
        "free_cash_flow_cr": "FCF ₹ Cr",
        "revenue_cagr_5yr": "Revenue CAGR 5yr %",
        "pat_cagr_5yr": "PAT CAGR 5yr %",
        "operating_profit_margin_pct": "OPM %",
        "pe_ratio": "P/E",
        "pb_ratio": "P/B",
        "dividend_yield_pct": "Dividend Yield %",
        "interest_coverage": "ICR"
    }
)

numeric_display_columns = [
    "Quality Score",
    "ROE %",
    "D/E",
    "FCF ₹ Cr",
    "Revenue CAGR 5yr %",
    "PAT CAGR 5yr %",
    "OPM %",
    "P/E",
    "P/B",
    "Dividend Yield %",
    "ICR"
]

for column in numeric_display_columns:
    if column in output.columns:
        output[column] = pd.to_numeric(
            output[column],
            errors="coerce"
        ).round(2)

st.dataframe(
    output,
    width="stretch",
    hide_index=True
)

csv_data = output.to_csv(
    index=False
).encode("utf-8")

st.download_button(
    "Download Screener Results CSV",
    data=csv_data,
    file_name="screener_output.csv",
    mime="text/csv",
    width="stretch"
)