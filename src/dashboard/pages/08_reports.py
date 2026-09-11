import streamlit as st
import pandas as pd
from pathlib import Path

from src.dashboard.utils.db import get_companies, get_documents

st.set_page_config(
    page_title="Reports & Valuation | Nifty 100 Analytics",
    layout="wide"
)

st.title("Reports & Valuation")

companies = get_companies()

if companies.empty:
    st.warning("Company data unavailable.")
    st.stop()

st.header("Annual Reports")

company_ids = companies["id"].tolist()

selected_company = st.selectbox(
    "Search Company / Ticker",
    company_ids,
    format_func=lambda x: companies.loc[
        companies["id"].eq(x),
        "company_name"
    ].iloc[0]
)

company_name = companies.loc[
    companies["id"].eq(selected_company),
    "company_name"
].iloc[0]

st.subheader(company_name)

documents = get_documents(selected_company)

if documents.empty:
    st.info("No annual reports available for this company.")
else:
    documents = documents.copy()

    documents["year"] = pd.to_numeric(
        documents["year"],
        errors="coerce"
    )

    documents = documents.sort_values(
        "year",
        ascending=False
    )

    st.subheader("Available Annual Reports")

    for _, row in documents.iterrows():
        year = row["year"]
        report_url = row.get("annual_report")

        if pd.isna(year):
            continue

        if pd.isna(report_url) or not str(report_url).strip():
            st.markdown(
                f"**{int(year)}**  \n"
                "🔴 Report unavailable"
            )
            continue

        report_url = str(report_url).strip()

        st.markdown(
            f"**{int(year)}**  \n"
            f"[Open BSE Annual Report]({report_url})"
        )

    st.subheader("Report Data")

    display_df = documents[
        ["year", "annual_report"]
    ].copy()

    display_df.columns = [
        "Year",
        "Annual Report URL"
    ]

    display_df["Year"] = display_df["Year"].apply(
        lambda x: int(x) if pd.notna(x) else "N/A"
    )

    st.dataframe(
        display_df,
        width="stretch",
        hide_index=True
    )

st.markdown("---")

st.header("Valuation Analysis")

project_root = Path(__file__).resolve().parents[3]

valuation_file = (
    project_root
    / "output"
    / "valuation_summary.xlsx"
)

flags_file = (
    project_root
    / "output"
    / "valuation_flags.csv"
)

if not valuation_file.exists():
    st.error(
        "Valuation summary not found. "
        "Please run src\\analytics\\valuation.py first."
    )
else:
    valuation = pd.read_excel(valuation_file)

    if valuation.empty:
        st.warning("Valuation summary is empty.")
    else:
        valuation["P/E"] = pd.to_numeric(
            valuation["P/E"],
            errors="coerce"
        )

        valuation["P/B"] = pd.to_numeric(
            valuation["P/B"],
            errors="coerce"
        )

        valuation["EV/EBITDA"] = pd.to_numeric(
            valuation["EV/EBITDA"],
            errors="coerce"
        )

        valuation["FCF_yield_pct"] = pd.to_numeric(
            valuation["FCF_yield_pct"],
            errors="coerce"
        )

        valuation["5yr_median_PE"] = pd.to_numeric(
            valuation["5yr_median_PE"],
            errors="coerce"
        )

        valuation["PE_vs_sector_median_pct"] = pd.to_numeric(
            valuation["PE_vs_sector_median_pct"],
            errors="coerce"
        )

        caution_count = valuation["flag"].eq("Caution").sum()
        discount_count = valuation["flag"].eq("Discount").sum()
        fair_count = valuation["flag"].eq("Fair").sum()

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Companies",
                f"{len(valuation):,}"
            )

        with col2:
            st.metric(
                "Caution",
                f"{caution_count:,}"
            )

        with col3:
            st.metric(
                "Discount",
                f"{discount_count:,}"
            )

        with col4:
            st.metric(
                "Fair",
                f"{fair_count:,}"
            )

        st.subheader("Valuation Summary")

        summary_display = valuation.copy()

        summary_display.columns = [
            "Company ID",
            "Company Name",
            "Sector",
            "P/E",
            "P/B",
            "EV/EBITDA",
            "FCF Yield %",
            "5yr Median P/E",
            "PE vs Sector Median %",
            "Flag"
        ]

        st.dataframe(
            summary_display,
            width="stretch",
            hide_index=True
        )

        st.subheader("Valuation Flags")

        if flags_file.exists():
            flags = pd.read_csv(flags_file)

            if flags.empty:
                st.info("No Caution or Discount companies found.")
            else:
                flags_display = flags.copy()

                st.dataframe(
                    flags_display,
                    width="stretch",
                    hide_index=True
                )
        else:
            st.info("Valuation flags file not found.")

        st.subheader("Download Valuation Outputs")

        col1, col2 = st.columns(2)

        with col1:
            with open(valuation_file, "rb") as file:
                st.download_button(
                    label="Download Valuation Summary Excel",
                    data=file,
                    file_name="valuation_summary.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    width="stretch"
                )

        with col2:
            if flags_file.exists():
                with open(flags_file, "rb") as file:
                    st.download_button(
                        label="Download Valuation Flags CSV",
                        data=file,
                        file_name="valuation_flags.csv",
                        mime="text/csv",
                        width="stretch"
                    )

st.caption(
    "Valuation outputs are generated from the latest available market, financial ratio and sector data."
)