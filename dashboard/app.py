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

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Main page
st.markdown('<div class="main-header">🏃 Running Analytics Dashboard</div>', unsafe_allow_html=True)

# Sync status
last_sync = get_last_sync_time()
if last_sync:
    st.markdown(f'<div class="sub-header">Last synced: {last_sync}</div>', unsafe_allow_html=True)
else:
    st.warning("⚠️ No data found. Run: `python scripts/sync-garmin.py`")

st.markdown("---")

# Risk Alert (if in high-risk month)
current_month = datetime.now().month
month_names = ["", "January", "February", "March", "April", "May", "June",
               "July", "August", "September", "October", "November", "December"]

# High-risk months: Feb (46.2%), Apr (38.5%), May (27.8%)
HIGH_RISK_MONTHS = {
    2: ("CRITICAL", "🔴", 46.2, "Winter slump - worst month historically"),
    4: ("CRITICAL", "🔴", 38.5, "School holidays - major collapse risk"),
    5: ("CRITICAL", "🔴", 27.8, "School holidays continuation"),
}

MEDIUM_RISK_MONTHS = {
    1: ("MEDIUM", "🟡", 31.2, "Post-holiday recovery period"),
    3: ("MEDIUM", "🟡", 25.0, "Training cycle reset"),
    6: ("MEDIUM", "🟡", 20.0, "Extended holiday impact"),
}

if current_month in HIGH_RISK_MONTHS:
    level, icon, rate, note = HIGH_RISK_MONTHS[current_month]
    st.error(f"""
    ### 🚨 HIGH RISK ALERT: {month_names[current_month]}

    **Historical Violation Rate: {rate}%** (vs. 22.3% average)

    **Risk Factor:** {note}

    **⚠️ FIREWALL RULES ACTIVE:**
    - Minimum **20km per week** (elevated floor - not 15km!)
    - Minimum **3 runs per week**
    - **Zero-day weeks NOT allowed**
    - If quality workout missed → replace with easy run

    **2025 Pattern:** Weeks 15-18 in Apr-May collapsed to 5-10km/week. DO NOT REPEAT.

    👉 See **Risk Monitor** page for detailed strategies.
    """)
elif current_month in MEDIUM_RISK_MONTHS:
    level, icon, rate, note = MEDIUM_RISK_MONTHS[current_month]
    st.warning(f"""
    ### {icon} Moderate Risk Period: {month_names[current_month]}

    **Historical Violation Rate: {rate}%** (vs. 22.3% average)

    **Note:** {note}

    Standard 15km floor applies. Monitor for early warning signs.
    """)

st.markdown("---")

# Welcome section
st.header("Welcome!")

st.markdown("""
This dashboard provides deep insights into your running training:

**📊 Consistency Guardian** - Track weekly volume and floor violations
- Visual heatmaps of training consistency
- Weekly volume trends with color-coded status
- Streak tracking and violation patterns

**🎯 Season Comparison** - Compare training across seasons
- Side-by-side season analysis
- VO2max progression tracking
- Quality sessions and long run trends

**🏁 Race Confidence** - Analyze race readiness
- "Can I hold this pace?" calculator
- Race pace database and fatigue resistance
- HR stability and pace degradation analysis

**📋 Season Plan** - View current training plan
- 20-week HM sub-2:00 campaign details
- Weekly volume progression
- Strength training program
- Race execution strategies

**📝 Weekly Logs** - Review training logs
- Week-by-week detailed documentation
- Workout analysis and reflections
- Progress tracking

**🚨 Risk Monitor** - Historical violation patterns ⭐ NEW
- Monthly risk assessment based on 4 years of data
- School holiday collapse warnings
- April-May firewall strategies
- Real-time risk alerts

---

### Navigation
Use the sidebar to navigate between pages.

### Quick Actions
""")

col1, col2, col3 = st.columns(3)

with col1:
    st.info("""
    **📈 Check Consistency**

    View your current weekly streak and identify any floor violations.
    """)

with col2:
    st.info("""
    **🔄 Compare Seasons**

    Analyze how your 2026 training compares to 2025 patterns.
    """)

with col3:
    st.info("""
    **💪 Race Confidence**

    Calculate your readiness for sub-2:00 HM (5:40/km pace).
    """)

col4, col5, col6 = st.columns(3)

with col4:
    st.info("""
    **📋 Season Plan**

    View the full 20-week training plan and strategy.
    """)

with col5:
    st.info("""
    **📝 Weekly Logs**

    Browse detailed logs for each training week.
    """)

with col6:
    st.error("""
    **🚨 Risk Monitor** ⭐

    Check current month risk based on historical patterns. CRITICAL for Apr-May!
    """)

# Sidebar
with st.sidebar:
    st.header("About")
    st.markdown("""
    **Running Analytics Dashboard**

    Built with Streamlit and Plotly

    Data sources: Garmin Connect + Strava (merged)

    Use the navigation above to explore:
    - 📊 Consistency tracking
    - 🎯 Season comparisons
    - 🏁 Race confidence analysis
    - 📋 Season plan details
    - 📝 Weekly training logs
    - 🚨 Risk monitor (NEW!)
    """)

    st.markdown("---")

    # Data summary
    try:
        data = load_garmin_data()
        st.metric("Total Activities", len(data.get('activities', [])))
        st.metric("VO2max", data.get('training_status', {}).get('vo2max', 'N/A'))
        st.metric("Training Status", data.get('training_status', {}).get('training_effect_label', 'N/A'))
    except Exception as e:
        st.error(f"Error loading data: {e}")
