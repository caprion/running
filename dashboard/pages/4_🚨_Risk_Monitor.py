"""
Risk Monitor Dashboard Page
Shows floor violation risk based on historical patterns
"""

import streamlit as st
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from utils.data_loader import load_activities, activities_to_dataframe, get_weekly_summary

# Page config
st.set_page_config(page_title="Risk Monitor", page_icon="🚨", layout="wide")

# Title
st.title("🚨 Floor Violation Risk Monitor")
st.markdown("**Historical patterns + current week risk assessment**")
st.divider()

# Current date and week
today = datetime.now()
current_month = today.month
current_week = today.isocalendar()[1]

# Month risk levels (from historical analysis)
MONTH_RISK = {
    1: ("MEDIUM", "🟡", 31.2, "Post-holiday recovery period"),
    2: ("HIGH", "🔴", 46.2, "Worst month historically - winter slump"),
    3: ("MEDIUM", "🟡", 25.0, "Training cycle reset period"),
    4: ("CRITICAL", "🔴", 38.5, "SCHOOL HOLIDAYS - Major collapse risk"),
    5: ("CRITICAL", "🔴", 27.8, "SCHOOL HOLIDAYS continuation"),
    6: ("MEDIUM", "🟡", 20.0, "Extended holiday impact"),
    7: ("LOW", "🟢", 13.3, "Best training consistency"),
    8: ("LOW", "🟢", 17.6, "Excellent training month"),
    9: ("LOW", "🟢", 11.8, "Peak consistency period"),
    10: ("LOW", "🟢", 20.0, "Good training month"),
    11: ("BEST", "🟢", 6.2, "Best month - only 6% violations"),
    12: ("LOW", "🟢", 17.6, "Good end-of-year consistency")
}

month_names = ["", "January", "February", "March", "April", "May", "June",
               "July", "August", "September", "October", "November", "December"]

# Get current month risk
risk_level, risk_icon, historical_rate, risk_note = MONTH_RISK[current_month]

# Display current risk status
st.markdown("## 📍 Current Status")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        label="Current Month",
        value=month_names[current_month],
        delta=f"Week {current_week}"
    )

with col2:
    st.metric(
        label="Risk Level",
        value=risk_level,
        delta=f"{risk_icon} {historical_rate}% historical violation rate"
    )

with col3:
    # Calculate current week distance
    df = activities_to_dataframe()
    if not df.empty:
        current_year = today.year
        current_week_key = f"{current_year}-W{current_week:02d}"

        current_week_data = df[df['week_key'] == current_week_key]
        current_distance = current_week_data['distance_km'].sum() if not current_week_data.empty else 0

        # Determine floor based on month
        floor = 20 if current_month in [4, 5, 6] else 15

        status = "✅" if current_distance >= floor else "⚠️"
        delta_text = f"Floor: {floor}km"

        st.metric(
            label="This Week (so far)",
            value=f"{current_distance:.1f}km",
            delta=delta_text
        )
    else:
        st.metric(label="This Week", value="No data")

# Risk alert banner
if risk_level in ["CRITICAL", "HIGH"]:
    st.error(f"""
    🚨 **HIGH RISK PERIOD ACTIVE**

    {risk_note}

    **Firewall Rules Active:**
    - Minimum 20km per week (elevated floor)
    - Minimum 3 runs per week
    - Zero-day weeks NOT allowed
    - If quality workout missed → replace with easy run
    """)
elif risk_level == "MEDIUM":
    st.warning(f"""
    ⚠️ **MODERATE RISK PERIOD**

    {risk_note}

    **Standard Rules:**
    - Minimum 15km per week
    - Monitor for early warning signs
    - Don't miss two consecutive runs
    """)
else:
    st.success(f"""
    ✅ **LOW RISK PERIOD**

    {risk_note}

    This is your most consistent training period historically. Take advantage!
    """)

st.divider()

# Monthly risk calendar
st.markdown("## 📅 2026 Risk Calendar")

# Create 4x3 grid for months
rows = 3
cols = 4

for row in range(rows):
    columns = st.columns(cols)
    for col in range(cols):
        month_num = row * cols + col + 1
        if month_num <= 12:
            risk_level, risk_icon, historical_rate, risk_note = MONTH_RISK[month_num]

            with columns[col]:
                # Highlight current month
                if month_num == current_month:
                    border = "🔹"
                else:
                    border = ""

                st.markdown(f"""
                <div style="padding: 10px; border: 2px solid {'#ff4444' if risk_level == 'CRITICAL' else ('#ffaa00' if risk_level == 'HIGH' else ('#ffdd00' if risk_level == 'MEDIUM' else '#44ff44'))}; border-radius: 5px; margin: 5px;">
                    <p style="margin: 0; font-weight: bold;">{border} {month_names[month_num]} {border}</p>
                    <p style="margin: 5px 0; font-size: 24px;">{risk_icon}</p>
                    <p style="margin: 0; font-size: 14px;">{historical_rate}% violations</p>
                    <p style="margin: 0; font-size: 12px; color: #666;">{risk_level}</p>
                </div>
                """, unsafe_allow_html=True)

st.divider()

# Historical collapse periods
st.markdown("## 📊 Historical Collapse Periods")

st.markdown("""
Based on 4 years of data (2022-2025), here are the major training collapses:

**5 major collapses identified** (3+ consecutive weeks below 15km)
""")

collapse_data = [
    {
        "period": "2022-W15 to W18",
        "dates": "April-May 2022",
        "weeks": 3,
        "avg_km": 11.1,
        "cause": "School Holidays",
        "critical": True
    },
    {
        "period": "2023-W01 to W08",
        "dates": "Jan-Feb 2023",
        "weeks": 6,
        "avg_km": 9.1,
        "cause": "New Year Reset",
        "critical": False
    },
    {
        "period": "2025-W15 to W18",
        "dates": "April-May 2025",
        "weeks": 3,
        "avg_km": 7.1,
        "cause": "School Holidays",
        "critical": True
    },
    {
        "period": "2025-W23 to W26",
        "dates": "June 2025",
        "weeks": 3,
        "avg_km": 9.1,
        "cause": "Extended Holiday Impact",
        "critical": True
    },
    {
        "period": "2025-W38 to W42",
        "dates": "Sep-Oct 2025",
        "weeks": 3,
        "avg_km": 9.7,
        "cause": "Isolated Slump",
        "critical": False
    }
]

for i, collapse in enumerate(collapse_data, 1):
    icon = "🔴" if collapse["critical"] else "🟡"

    with st.expander(f"{icon} Collapse {i}: {collapse['period']} - {collapse['dates']}"):
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Duration", f"{collapse['weeks']} weeks")
        with col2:
            st.metric("Avg Distance", f"{collapse['avg_km']:.1f} km/week")
        with col3:
            st.metric("Root Cause", collapse['cause'])

        if collapse["critical"]:
            st.error("⚠️ School holiday related - high risk of repeat in 2026")

st.divider()

# 2026 Spring HM Critical Dates
st.markdown("## 🎯 2026 Spring HM Campaign: Critical Dates")

st.markdown("""
**High-risk period coincides with peak training phase:**
""")

campaign_weeks = [
    {"week": "W14", "dates": "Apr 6-12", "phase": "Tempo 6km + LR 18km", "risk": "🔴 HIGH"},
    {"week": "W15", "dates": "Apr 13-19", "phase": "Deload week", "risk": "🟡 MEDIUM"},
    {"week": "W16", "dates": "Apr 20-26", "phase": "Tempo 7km + LR 19km", "risk": "🔴 HIGH"},
    {"week": "W17", "dates": "Apr 27-May 3", "phase": "Tempo 8km + LR 20km", "risk": "🔴 CRITICAL"},
    {"week": "W18", "dates": "May 4-10", "phase": "Race week prep", "risk": "🔴 CRITICAL"},
]

for week_data in campaign_weeks:
    cols = st.columns([1, 2, 4, 2])
    with cols[0]:
        st.markdown(f"**{week_data['week']}**")
    with cols[1]:
        st.markdown(week_data['dates'])
    with cols[2]:
        st.markdown(week_data['phase'])
    with cols[3]:
        st.markdown(week_data['risk'])

st.warning("""
**Historical Pattern:** 60% of major collapses occurred during weeks 15-18.

**2025 Same Period:** Weeks 15-18 averaged 7.1 km/week (collapsed)

**2026 Consequence:** Missing HM sub-2:00 goal if pattern repeats
""")

st.divider()

# Firewall strategies
st.markdown("## 🛡️ April-May Firewall Strategies")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### ✅ DO")
    st.markdown("""
    - **Elevate floor to 20km** (not 15km)
    - **Minimum 3 runs per week**
    - **Convert missed quality to easy** (never zero-day)
    - **Maintain long run** (reduce by max 20% if needed)
    - **Accept easy-only weeks** during travel
    - **Pre-commit to firewall weeks** 14-18
    """)

with col2:
    st.markdown("### ❌ DON'T")
    st.markdown("""
    - ~~Skip week because "it's not quality"~~
    - ~~Drop below 20km "just this once"~~
    - ~~Miss two consecutive runs~~
    - ~~Cancel long run (most critical workout)~~
    - ~~Think "I'll make it up next week"~~
    - ~~Ignore early warning signs~~
    """)

st.info("""
**2026 Mantra:** *"No zero-day weeks in April-May. 20km floor, non-negotiable."*

A 20km easy-run week is infinitely better than a 5km "I tried" week.
""")

st.divider()

# Weekly tracking
st.markdown("## 📈 Recent Weeks Tracking")

weekly = get_weekly_summary(df)
if not weekly.empty:
    # Show last 8 weeks
    recent = weekly.tail(8).copy()
    recent = recent.sort_values(['year', 'week'], ascending=False)

    st.markdown("**Last 8 weeks:**")

    for _, row in recent.iterrows():
        week_key = row['week_key']
        distance = row['distance_km']
        runs = int(row['runs'])
        status = row['status']

        # Determine icon
        if status == 'GREEN':
            icon = "🟢"
            color = "#44ff44"
        elif status == 'YELLOW':
            icon = "🟡"
            color = "#ffdd00"
        else:
            icon = "🔴"
            color = "#ff4444"

        st.markdown(f"""
        <div style="padding: 8px; margin: 5px 0; border-left: 4px solid {color};">
            {icon} <strong>{week_key}</strong>: {distance:.1f}km ({runs} runs) - {status}
        </div>
        """, unsafe_allow_html=True)
else:
    st.warning("No recent data available")

st.divider()

# Link to full analysis
st.markdown("## 📄 Full Analysis Document")
st.markdown("""
**Complete historical analysis:** `analysis/floor-violation-patterns.md`

This document contains:
- Detailed month-by-month breakdown
- All 5 collapse periods analyzed
- Seasonal success formulas
- Year-by-year progression
- Contingency protocols
""")

if st.button("📖 View Full Analysis"):
    analysis_file = Path(__file__).parent.parent.parent / "analysis" / "floor-violation-patterns.md"
    if analysis_file.exists():
        with open(analysis_file, 'r', encoding='utf-8') as f:
            content = f.read()
        st.markdown(content)
    else:
        st.error("Analysis file not found")

st.divider()

# Footer
st.markdown("---")
st.caption("Risk Monitor | Based on 188 weeks of historical data (2022-2026) | Last updated: Jan 9, 2026")
