import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st

st.set_page_config(
    page_title="Nifty 100 Analytics",
    layout="wide",
    initial_sidebar_state="expanded"
)


pages = [
    st.Page(
        "pages/01_home.py",
        title="Home",
        icon="🏠"
    ),
    st.Page(
        "pages/02_profile.py",
        title="Company Profile",
        icon="🏢"
    ),
    st.Page(
        "pages/03_screener.py",
        title="Screener",
        icon="🔎"
    ),
    st.Page(
        "pages/04_peers.py",
        title="Peers",
        icon="📊"
    ),
    st.Page(
        "pages/05_trends.py",
        title="Trends",
        icon="📈"
    ),
    st.Page(
        "pages/06_sectors.py",
        title="Sectors",
        icon="🏭"
    ),
    st.Page(
        "pages/07_capital.py",
        title="Capital Allocation",
        icon="💰"
    ),
    st.Page(
        "pages/08_reports.py",
        title="Annual Reports",
        icon="📄"
    ),
]


st.sidebar.title("Nifty 100 Analytics")
st.sidebar.caption("FinTech Analytics Dashboard")
st.sidebar.markdown("---")


pg = st.navigation(pages)


st.sidebar.markdown("---")
st.sidebar.caption("Sprint 4 • Nifty 100 Analytics")


pg.run()