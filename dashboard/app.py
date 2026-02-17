"""
Running Analytics Dashboard

Multi-page Streamlit app for analyzing training data from Garmin Connect.
"""

import streamlit as st
from datetime import datetime
from utils.data_loader import get_last_sync_time, load_garmin_data

# Page configuration
st.set_page_config(
    page_title="Running Analytics",
    page_icon="🏃",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Indian Earth design system CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Libre+Baskerville:wght@400;700&family=IBM+Plex+Sans:wght@300;400;500;600&display=swap');

    .main-header {
        font-family: 'Libre Baskerville', Georgia, serif;
        font-size: 2.25rem;
        font-weight: 400;
        color: #3d2b1f;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-family: 'IBM Plex Sans', sans-serif;
        font-size: 1rem;
        color: #8b7560;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #ffffff;
        border: 1px solid #ede4d5;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        box-shadow: 0 1px 2px rgba(61, 43, 31, 0.04);
    }

    /* Streamlit element overrides */
    .stMetric label { color: #8b7560 !important; }
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Libre Baskerville', Georgia, serif !important;
        font-weight: 400 !important;
        color: #3d2b1f !important;
    }
    .stMarkdown p { color: #6b5443; }
    hr { border-color: #ede4d5 !important; }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #f5efe5 !important;
        border-right: 1px solid #ede4d5 !important;
    }
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2 {
        color: #3d2b1f !important;
    }

    /* Info/warning/error boxes */
    .stAlert > div {
        border-radius: 8px !important;
        border-left-width: 3px !important;
    }
</style>
""", unsafe_allow_html=True)

# Main page
st.markdown('<div class="main-header">Running Analytics</div>', unsafe_allow_html=True)

# Sync status
last_sync = get_last_sync_time()
if last_sync:
    st.markdown(f'<div class="sub-header">Last synced: {last_sync}</div>', unsafe_allow_html=True)
else:
    st.warning("No data found. Run: `python scripts/incremental-sync.py --days 90`")

st.markdown("---")

# Risk Alert (if in high-risk month)
current_month = datetime.now().month
month_names = ["", "January", "February", "March", "April", "May", "June",
               "July", "August", "September", "October", "November", "December"]

# High-risk months: Feb (46.2%), Apr (38.5%), May (27.8%)
HIGH_RISK_MONTHS = {
    2: ("CRITICAL", 46.2, "Winter slump - worst month historically"),
    4: ("CRITICAL", 38.5, "School holidays - major collapse risk"),
    5: ("CRITICAL", 27.8, "School holidays continuation"),
}

MEDIUM_RISK_MONTHS = {
    1: ("MEDIUM", 31.2, "Post-holiday recovery period"),
    3: ("MEDIUM", 25.0, "Training cycle reset"),
    6: ("MEDIUM", 20.0, "Extended holiday impact"),
}

if current_month in HIGH_RISK_MONTHS:
    level, rate, note = HIGH_RISK_MONTHS[current_month]
    st.error(f"""
    ### HIGH RISK: {month_names[current_month]}

    **Historical Violation Rate: {rate}%** (vs. 22.3% average)

    **Risk Factor:** {note}

    **Firewall Rules Active:**
    - Minimum **20km per week** (elevated floor)
    - Minimum **3 runs per week**
    - **Zero-day weeks NOT allowed**
    - If quality workout missed, replace with easy run

    See **Risk Monitor** page for detailed strategies.
    """)
elif current_month in MEDIUM_RISK_MONTHS:
    level, rate, note = MEDIUM_RISK_MONTHS[current_month]
    st.warning(f"""
    ### Moderate Risk: {month_names[current_month]}

    **Historical Violation Rate: {rate}%** (vs. 22.3% average)

    **Note:** {note}

    Standard 15km floor applies. Monitor for early warning signs.
    """)

st.markdown("---")

# Welcome section
st.header("Dashboard")

st.markdown("""
This dashboard tracks training data from Garmin Connect across seven pages:

**Consistency** - Weekly volume tracking, floor violations, streak monitoring

**Season Compare** - Side-by-side season analysis, VO2max progression

**Race Confidence** - Pace sustainability calculator, HR stability, fatigue resistance

**Risk Monitor** - Historical violation patterns, monthly risk assessment, firewall strategies

**Training Load** - Volume trends, intensity distribution, load progression

**Form** - Cadence analysis, stride length trends, gait tracking

**Compliance** - Planned vs actual volume, 20-week campaign status, full training plan
""")

st.markdown("---")

col1, col2, col3 = st.columns(3)

with col1:
    st.info("""
    **Check Consistency**

    View your current weekly streak and identify any floor violations.
    """)

with col2:
    st.info("""
    **Compare Seasons**

    Analyze how your 2026 training compares to 2025 patterns.
    """)

with col3:
    st.info("""
    **Race Confidence**

    Calculate your readiness for sub-2:00 HM (5:40/km pace).
    """)

# Sidebar
with st.sidebar:
    st.header("About")
    st.markdown("""
    **Running Analytics Dashboard**

    Built with Streamlit and Plotly

    Data source: Garmin Connect

    Use the sidebar navigation to explore pages.
    """)

    st.markdown("---")

    # Data summary
    try:
        data = load_garmin_data()
        st.metric("VO2max", data.get('training_status', {}).get('vo2max', 'N/A'))
        st.metric("Training Status", data.get('training_status', {}).get('training_effect_label', 'N/A'))
    except Exception as e:
        st.error(f"Error loading data: {e}")
