"""
Consistency Guardian Page

Track weekly volume and floor violations with visual analytics.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from utils.data_loader import activities_to_dataframe, get_weekly_summary
from utils.metrics import FLOOR_THRESHOLD, YELLOW_THRESHOLD, calculate_streak

# Page config
st.set_page_config(page_title="Consistency Guardian", page_icon="📊", layout="wide")

st.title("Consistency Guardian")
st.markdown("Track your weekly running volume and identify floor violations")

# Info box
with st.expander("ℹ️ How to use this page", expanded=False):
    st.markdown("""
    **View Options (in sidebar):**
    - **Last 4 Weeks** (Default) - Always shows recent training, even across years
    - **Last 12 Weeks** - Quarterly view for trend analysis
    - **Last 26 Weeks** - 6-month view with optional year filter
    - **Current Year** - Focus on this year's training only
    - **All Time** - Complete training history (188 weeks!)

    **Tip:** Start with "Last 4 Weeks" to see your current momentum, then switch to "All Time" to view historical patterns.
    """)

# Load data - NO CACHING to avoid pickle issues with datetime
def load_data():
    df = activities_to_dataframe()
    weekly = get_weekly_summary(df)
    return df, weekly

try:
    df, weekly = load_data()

    if df.empty:
        st.error("No running activities found. Run `python scripts/incremental-sync.py --days 90` to sync data.")
        st.stop()

    # Filters
    st.sidebar.header("Filters")

    # View selector
    view_options = {
        "Last 4 Weeks": 4,
        "Last 12 Weeks": 12,
        "Last 26 Weeks (6 months)": 26,
        "Current Year": "current_year",
        "All Time": "all"
    }

    selected_view = st.sidebar.selectbox(
        "View",
        list(view_options.keys()),
        index=0,  # Default to "Last 4 Weeks"
        help="Choose time range to display"
    )

    view_value = view_options[selected_view]

    # Apply filter based on selection
    if view_value == "current_year":
        # Current year view
        current_year = datetime.now().year
        df_filtered = df[df['year'] == current_year]
        weekly_filtered = weekly[weekly['year'] == current_year]
        view_label = f"{current_year}"
    elif view_value == "all":
        # All time view
        df_filtered = df.copy()
        weekly_filtered = weekly.copy()
        view_label = "All Time"
    else:
        # Last N weeks view
        weekly_filtered = weekly.tail(view_value)
        # Get date range from filtered weeks
        if not weekly_filtered.empty:
            week_keys = weekly_filtered['week_key'].tolist()
            df_filtered = df[df['week_key'].isin(week_keys)]
        else:
            df_filtered = pd.DataFrame()
        view_label = selected_view

    # Additional year filter (optional, for drilling down)
    if view_value in ["all", 26] and not weekly_filtered.empty:
        available_years = sorted(weekly_filtered['year'].unique(), reverse=True)
        if len(available_years) > 1:
            use_year_filter = st.sidebar.checkbox("Filter by specific year", False)
            if use_year_filter:
                selected_year = st.sidebar.selectbox("Select Year", available_years)
                df_filtered = df_filtered[df_filtered['year'] == selected_year]
                weekly_filtered = weekly_filtered[weekly_filtered['year'] == selected_year]
                view_label = f"{view_label} ({selected_year})"

    # Calculate metrics
    total_weeks = len(weekly_filtered)
    green_weeks = len(weekly_filtered[weekly_filtered['status'] == 'GREEN'])
    yellow_weeks = len(weekly_filtered[weekly_filtered['status'] == 'YELLOW'])
    red_weeks = len(weekly_filtered[weekly_filtered['status'] == 'RED'])

    # Calculate streak (use most recent year in filtered data)
    if not weekly_filtered.empty:
        latest_year = weekly_filtered['year'].max()
        current_streak = calculate_streak(weekly_filtered, latest_year)
    else:
        current_streak = 0

    total_km = df_filtered['distance_km'].sum()
    avg_per_week = total_km / total_weeks if total_weeks > 0 else 0

    # Top metrics
    st.header(f"{view_label} Overview")

    # Show date range
    if not weekly_filtered.empty:
        first_week = weekly_filtered['week_key'].iloc[0]
        last_week = weekly_filtered['week_key'].iloc[-1]
        st.caption(f"Showing weeks {first_week} to {last_week}")

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("Current Streak", f"{current_streak} weeks", help="Consecutive weeks >= 15km")

    with col2:
        st.metric("Weeks Tracked", total_weeks)

    with col3:
        st.metric("Total Distance", f"{total_km:.1f} km")

    with col4:
        st.metric("Avg/Week", f"{avg_per_week:.1f} km")

    with col5:
        violation_pct = (red_weeks / total_weeks * 100) if total_weeks > 0 else 0
        st.metric("Violations", f"{red_weeks} ({violation_pct:.0f}%)")

    st.markdown("---")

    # Weekly bar chart
    st.header("Weekly Volume Trend")

    # Prepare data for chart
    colors = []
    for status in weekly_filtered['status']:
        if status == 'RED':
            colors.append('#ff4b4b')
        elif status == 'YELLOW':
            colors.append('#ffa500')
        else:
            colors.append('#00cc00')

    fig_bars = go.Figure()

    fig_bars.add_trace(go.Bar(
        x=weekly_filtered['week_key'],
        y=weekly_filtered['distance_km'],
        marker_color=colors,
        text=weekly_filtered['distance_km'].round(1),
        textposition='outside',
        hovertemplate='<b>%{x}</b><br>' +
                      'Distance: %{y:.1f} km<br>' +
                      'Runs: %{customdata[0]}<br>' +
                      '<extra></extra>',
        customdata=weekly_filtered[['runs']].values
    ))

    # Add threshold lines
    fig_bars.add_hline(y=FLOOR_THRESHOLD, line_dash="dash", line_color="red",
                       annotation_text=f"Floor ({FLOOR_THRESHOLD}km)",
                       annotation_position="right")
    fig_bars.add_hline(y=YELLOW_THRESHOLD, line_dash="dash", line_color="orange",
                       annotation_text=f"Target ({YELLOW_THRESHOLD}km)",
                       annotation_position="right")

    fig_bars.update_layout(
        xaxis_title="Week",
        yaxis_title="Distance (km)",
        height=500,
        showlegend=False,
        hovermode='x unified'
    )

    st.plotly_chart(fig_bars, use_container_width=True)

    # Rolling average
    st.subheader("4-Week Rolling Average")

    # Calculate rolling average
    weekly_sorted = weekly_filtered.sort_values(['year', 'week'])
    weekly_sorted['rolling_avg'] = weekly_sorted['distance_km'].rolling(window=4, min_periods=1).mean()

    fig_rolling = go.Figure()

    fig_rolling.add_trace(go.Scatter(
        x=weekly_sorted['week_key'],
        y=weekly_sorted['rolling_avg'],
        mode='lines+markers',
        line=dict(color='blue', width=3),
        marker=dict(size=8),
        name='4-week avg'
    ))

    fig_rolling.add_hline(y=FLOOR_THRESHOLD, line_dash="dash", line_color="red",
                          annotation_text="Floor")
    fig_rolling.add_hline(y=YELLOW_THRESHOLD, line_dash="dash", line_color="orange",
                          annotation_text="Target")

    fig_rolling.update_layout(
        xaxis_title="Week",
        yaxis_title="Distance (km)",
        height=400,
        showlegend=False
    )

    st.plotly_chart(fig_rolling, use_container_width=True)

    # Detailed weekly table
    st.markdown("---")
    st.header("Weekly Details")

    # Display table with all weeks
    display_df = weekly_filtered[['week_key', 'runs', 'distance_km', 'status', 'dates']].copy()
    display_df.columns = ['Week', 'Runs', 'Distance (km)', 'Status', 'Run Dates']

    # Display as markdown table (no pyarrow needed)
    status_emoji = {'GREEN': '✅', 'YELLOW': '⚠️', 'RED': '❌'}

    st.markdown("| Week | Runs | Distance (km) | Status | Run Dates |")
    st.markdown("|------|------|---------------|--------|-----------|")
    for _, row in weekly_filtered.iterrows():
        emoji = status_emoji[row['status']]
        st.markdown(
            f"| {row['week_key']} | {row['runs']} | {row['distance_km']:.1f} | "
            f"{emoji} {row['status']} | {row['dates'][:50]}... |"
        )

except Exception as e:
    st.error(f"Error loading data: {str(e)}")
    import traceback
    st.code(traceback.format_exc())
