# Nifty 100 Analytics

A FinTech analytics project for analyzing Nifty 100 companies using financial statements, financial ratios, screening, peer comparison, sector analysis, capital allocation, and valuation analytics.

## Project Overview

This project provides an end-to-end analytics platform covering:

- Financial data foundation
- Financial ratio analysis
- Company screening
- Peer comparison
- Trend analysis
- Sector analysis
- Capital allocation analysis
- Annual report access
- Valuation analysis
- Interactive Streamlit dashboard

## Dashboard

The project includes an 8-screen Streamlit dashboard:

1. Home
2. Company Profile
3. Screener
4. Peers
5. Trends
6. Sectors
7. Capital Allocation
8. Annual Reports

The dashboard also provides valuation analysis through the Annual Reports screen.

## How to Run the Dashboard

Open Command Prompt in the project directory and activate the virtual environment:

    .venv\Scripts\activate

Run the Streamlit application:

    streamlit run src\dashboard\app.py

The dashboard runs on:

    http://localhost:8501

## Dashboard Features

### Home

Provides:

- Average ROE
- Median P/E
- Median D/E
- Total Companies
- Median Revenue CAGR 5yr
- Debt-Free Companies
- Sector breakdown
- Top companies by composite quality score
- Year selector from 2019 to 2024

### Company Profile

Provides:

- Company information
- Sector and sub-sector
- ROE
- ROCE
- Net Profit Margin
- Debt-to-Equity
- Revenue CAGR
- Free Cash Flow
- 10-year revenue and net profit trend
- ROE and ROCE trend
- Pros and cons

Partial-data companies are handled without crashing and unavailable values are displayed as N/A.

### Screener

Provides:

- ROE filtering
- Debt-to-Equity filtering
- FCF filtering
- Revenue CAGR filtering
- PAT CAGR filtering
- OPM filtering
- P/E filtering
- P/B filtering
- Dividend Yield filtering
- Interest Coverage filtering

Six screening presets are available:

- Quality
- Value
- Growth
- Dividend
- Debt-Free
- Turnaround

Filtered results can be exported as CSV.

### Peers

Provides:

- 11 peer groups
- Peer company selection
- Peer average comparison
- 8-metric radar chart
- Benchmark company highlighting

### Trends

Provides:

- Company search
- Multi-metric selection
- 10-year financial trends
- Year-over-year change analysis

### Sectors

Provides:

- Sector selection
- Revenue vs ROE bubble analysis
- Market capitalization bubble sizing
- Sub-sector comparison
- Sector median KPI analysis

### Capital Allocation

Classifies companies into capital allocation patterns and provides:

- Treemap visualization
- Capital allocation pattern selection
- Company-level lists

### Annual Reports

Provides:

- Company search
- Available annual report years
- Annual report links
- Report availability status

### Valuation

The valuation module calculates:

- FCF Yield
- 5-year median P/E
- Sector median P/E
- P/E vs sector median
- P/E valuation flag

Valuation flags:

- Caution
- Discount
- Fair

Generated files:

    output\valuation_summary.xlsx
    output\valuation_flags.csv

## Data

The project uses financial data including:

- Companies
- Profit and Loss
- Balance Sheet
- Cash Flow
- Financial Ratios
- Market Capitalization
- Sectors
- Peer Groups
- Annual Reports
- Pros and Cons

The main SQLite database is:

    nifty100.db

## Project Structure

    Nifty100_Analytics/
    │
    ├── config/
    ├── data/
    ├── db/
    ├── docs/
    ├── notebooks/
    ├── output/
    ├── reports/
    ├── src/
    │   ├── analytics/
    │   ├── api/
    │   ├── dashboard/
    │   │   ├── pages/
    │   │   └── utils/
    │   └── screener/
    ├── tests/
    ├── nifty100.db
    ├── requirements.txt
    ├── Makefile
    └── README.md

## Sprint 4 Deliverables

Completed Sprint 4 deliverables include:

- Streamlit dashboard scaffold
- 8 dashboard screens
- Cached database utilities
- Company profile analytics
- Interactive screener
- Peer comparison
- Trend analysis
- Sector analysis
- Capital allocation analysis
- Annual report screen
- Valuation analytics
- Valuation summary Excel output
- Valuation flags CSV output
- Dashboard QA testing

## QA Status

Sprint 4 dashboard validation completed successfully.

Tested areas include:

- All 8 screens load successfully
- Company profiles load successfully
- Partial-data companies do not crash
- Five company profiles load within 3 seconds
- Screener extreme filter values do not crash
- Screener CSV export works
- Trends screen loads successfully
- Sectors charts load successfully
- Capital allocation treemap loads successfully
- Annual Reports screen loads successfully
- Valuation output contains 92 companies
- Valuation flags contain Caution and Discount cases

## Technologies

- Python
- Pandas
- NumPy
- SQLite
- Plotly
- Streamlit
- Excel
- Git

## Run Command

    streamlit run src\dashboard\app.py