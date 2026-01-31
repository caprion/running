"""
Season Comparison Page

Compare training patterns across different seasons to identify what works.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from utils.data_loader import activities_to_dataframe, get_training_status
from utils.metrics import FLOOR_THRESHOLD, YELLOW_THRESHOLD, get_pace_in_seconds

# Page config
st.set_page_config(page_title="Season Comparison", page_icon="🎯", layout="wide")

st.title("🎯 Season Comparison")
st.markdown("Analyze and compare training patterns across different seasons")

# Load data
@st.cache_data(ttl=300)  # Cache for 5 minutes to avoid pickle issues
def load_data():
    return activities_to_dataframe()

try:
    df = load_data()

    if df.empty:
        st.error("No running activities found. Run `python scripts/incremental-sync.py --days 90` to sync data.")
        st.stop()

    # Define seasons
    seasons = {
        "2025 Fall - Chennai HM": {
            "start": "2025-08-01",
            "end": "2025-12-31",
            "description": "Chennai HM prep (Aug-Dec 2025)",
            "goal": "Half Marathon PR",
            "color": "#FF6B6B"
        },
        "2026 Spring - Sub 2:00 HM": {
            "start": "2026-01-05",
            "end": "2026-05-24",
            "description": "Current season - Sub-2:00 HM (Jan-May 2026)",
            "goal": "Sub 2:00 Half Marathon",
            "color": "#4ECDC4"
        }
    }

    # Sidebar - season selection
    st.sidebar.header("Season Selection")
    selected_seasons = st.sidebar.multiselect(
        "Compare Seasons",
        list(seasons.keys()),
        default=list(seasons.keys())[:2] if len(seasons) >= 2 else list(seasons.keys())
    )

    if len(selected_seasons) < 1:
        st.warning("Please select at least one season to analyze.")
        st.stop()

    # Calculate metrics for each season
    season_metrics = []

    for season_name in selected_seasons:
        season = seasons[season_name]
        season_df = df[(df['date'] >= season['start']) & (df['date'] <= season['end'])]

        if season_df.empty:
            continue

        # Calculate weekly volumes
        weekly = season_df.groupby('week_key')['distance_km'].sum()

        # Quality sessions (runs with pace < 5:30/km or avg pace in top 25%)
        quality_threshold = season_df['avg_hr'].quantile(0.75) if len(season_df) > 4 else 150
        quality_sessions = season_df[season_df['avg_hr'] >= quality_threshold]

        # Long runs (>15km)
        long_runs = season_df[season_df['distance_km'] >= 15]

        metrics = {
            'season': season_name,
            'color': season['color'],
            'total_runs': len(season_df),
            'total_km': season_df['distance_km'].sum(),
            'weeks': len(weekly),
            'avg_km_per_week': season_df['distance_km'].sum() / len(weekly) if len(weekly) > 0 else 0,
            'peak_week': weekly.max() if len(weekly) > 0 else 0,
            'quality_sessions': len(quality_sessions),
            'long_runs': len(long_runs),
            'longest_run': season_df['distance_km'].max(),
            'avg_hr': season_df['avg_hr'].mean(),
            'floor_violations': sum(weekly < FLOOR_THRESHOLD),
            'green_weeks': sum(weekly >= YELLOW_THRESHOLD)
        }

        season_metrics.append(metrics)

    metrics_df = pd.DataFrame(season_metrics)

    # Overview comparison
    st.header("Season Overview")

    # Key metrics cards
    cols = st.columns(len(selected_seasons))

    for idx, season_name in enumerate(selected_seasons):
        season_data = metrics_df[metrics_df['season'] == season_name].iloc[0]

        with cols[idx]:
            st.markdown(f"""
            <div style='background-color: {season_data['color']}22; padding: 1rem; border-radius: 0.5rem; border-left: 4px solid {season_data['color']}'>
                <h3>{season_name}</h3>
                <p style='color: #666; font-size: 0.9rem'>{seasons[season_name]['description']}</p>
            </div>
            """, unsafe_allow_html=True)

            st.metric("Total Distance", f"{season_data['total_km']:.0f} km")
            st.metric("Avg/Week", f"{season_data['avg_km_per_week']:.1f} km")
            st.metric("Peak Week", f"{season_data['peak_week']:.1f} km")
            st.metric("Quality Sessions", f"{season_data['quality_sessions']}")
            st.metric("Long Runs (≥15km)", f"{season_data['long_runs']}")

    st.markdown("---")

    # Side-by-side weekly volume comparison
    st.header("Weekly Volume Progression")

    fig_weekly = go.Figure()

    for season_name in selected_seasons:
        season = seasons[season_name]
        season_df = df[(df['date'] >= season['start']) & (df['date'] <= season['end'])]

        if season_df.empty:
            continue

        # Calculate weekly volumes with week numbers
        weekly_data = season_df.groupby(['year', 'week']).agg({
            'distance_km': 'sum'
        }).reset_index()

        # Create week sequence number (1, 2, 3...)
        weekly_data = weekly_data.sort_values(['year', 'week'])
        weekly_data['week_num'] = range(1, len(weekly_data) + 1)

        fig_weekly.add_trace(go.Scatter(
            x=weekly_data['week_num'],
            y=weekly_data['distance_km'],
            mode='lines+markers',
            name=season_name,
            line=dict(color=season['color'], width=3),
            marker=dict(size=8)
        ))

    # Add threshold lines
    fig_weekly.add_hline(y=FLOOR_THRESHOLD, line_dash="dash", line_color="red",
                         annotation_text=f"Floor ({FLOOR_THRESHOLD}km)")
    fig_weekly.add_hline(y=YELLOW_THRESHOLD, line_dash="dash", line_color="orange",
                         annotation_text=f"Target ({YELLOW_THRESHOLD}km)")

    fig_weekly.update_layout(
        xaxis_title="Week Number",
        yaxis_title="Distance (km)",
        height=500,
        hovermode='x unified',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    st.plotly_chart(fig_weekly, use_container_width=True)

    # Metrics comparison table
    st.header("Detailed Metrics Comparison")

    comparison_table = metrics_df[[
        'season', 'weeks', 'total_km', 'avg_km_per_week', 'peak_week',
        'quality_sessions', 'long_runs', 'longest_run', 'floor_violations', 'green_weeks'
    ]].copy()

    comparison_table.columns = [
        'Season', 'Weeks', 'Total km', 'Avg/Week', 'Peak Week',
        'Quality', 'Long Runs', 'Longest', 'Violations', 'Green Weeks'
    ]

    # Display as markdown table (no pyarrow needed)
    st.markdown("| Season | Weeks | Total km | Avg/Week | Peak Week | Quality | Long Runs | Longest | Violations | Green Weeks |")
    st.markdown("|--------|-------|----------|----------|-----------|---------|-----------|---------|------------|-------------|")
    for _, row in comparison_table.iterrows():
        st.markdown(
            f"| {row['Season']} | {row['Weeks']} | {row['Total km']:.0f} km | {row['Avg/Week']:.1f} km | "
            f"{row['Peak Week']:.1f} km | {row['Quality']} | {row['Long Runs']} | {row['Longest']:.1f} km | "
            f"{int(row['Violations'])} | {int(row['Green Weeks'])} |"
        )

    # Volume distribution
    st.header("Volume Distribution")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Average Weekly Volume")

        fig_avg = go.Figure()

        fig_avg.add_trace(go.Bar(
            x=metrics_df['season'],
            y=metrics_df['avg_km_per_week'],
            marker_color=metrics_df['color'],
            text=metrics_df['avg_km_per_week'].round(1),
            textposition='outside'
        ))

        fig_avg.add_hline(y=YELLOW_THRESHOLD, line_dash="dash", line_color="orange")

        fig_avg.update_layout(
            yaxis_title="km/week",
            height=400,
            showlegend=False
        )

        st.plotly_chart(fig_avg, use_container_width=True)

    with col2:
        st.subheader("Quality Sessions vs Long Runs")

        fig_quality = go.Figure()

        fig_quality.add_trace(go.Bar(
            name='Quality Sessions',
            x=metrics_df['season'],
            y=metrics_df['quality_sessions'],
            marker_color='#FF6B6B'
        ))

        fig_quality.add_trace(go.Bar(
            name='Long Runs (≥15km)',
            x=metrics_df['season'],
            y=metrics_df['long_runs'],
            marker_color='#4ECDC4'
        ))

        fig_quality.update_layout(
            barmode='group',
            yaxis_title="Count",
            height=400,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )

        st.plotly_chart(fig_quality, use_container_width=True)

    # Long run progression
    st.header("Long Run Progression")

    fig_long = go.Figure()

    for season_name in selected_seasons:
        season = seasons[season_name]
        season_df = df[(df['date'] >= season['start']) & (df['date'] <= season['end'])]

        if season_df.empty:
            continue

        # Get long runs only
        long_runs = season_df[season_df['distance_km'] >= 10].sort_values('date')

        if not long_runs.empty:
            fig_long.add_trace(go.Scatter(
                x=list(range(1, len(long_runs) + 1)),
                y=long_runs['distance_km'],
                mode='lines+markers',
                name=season_name,
                line=dict(color=season['color'], width=3),
                marker=dict(size=10),
                text=long_runs['date'].dt.strftime('%Y-%m-%d'),
                hovertemplate='<b>Long Run #%{x}</b><br>' +
                              'Distance: %{y:.1f} km<br>' +
                              'Date: %{text}<br>' +
                              '<extra></extra>'
            ))

    fig_long.update_layout(
        xaxis_title="Long Run Number",
        yaxis_title="Distance (km)",
        height=400,
        hovermode='x unified'
    )

    st.plotly_chart(fig_long, use_container_width=True)

    # Training status & VO2max
    st.header("Fitness Metrics")

    training_status = get_training_status()

    col1, col2, col3 = st.columns(3)

    with col1:
        vo2max = training_status.get('vo2max', 'N/A')
        st.metric("Current VO2max", vo2max)

    with col2:
        training_load = training_status.get('training_load_7d', 'N/A')
        st.metric("Training Load (7d)", training_load)

    with col3:
        status = training_status.get('training_effect_label', 'N/A')
        st.metric("Training Status", status)

    # Insights
    st.markdown("---")
    st.header("Key Insights")

    if len(metrics_df) >= 2:
        # Compare first two seasons
        season1 = metrics_df.iloc[0]
        season2 = metrics_df.iloc[1]

        insights = []

        # Volume comparison
        volume_diff = season2['avg_km_per_week'] - season1['avg_km_per_week']
        if abs(volume_diff) > 2:
            emoji = "📈" if volume_diff > 0 else "📉"
            insights.append(f"{emoji} **Volume Change**: {abs(volume_diff):.1f} km/week {'higher' if volume_diff > 0 else 'lower'} in {season2['season']}")

        # Quality sessions
        quality_diff = season2['quality_sessions'] - season1['quality_sessions']
        if abs(quality_diff) > 2:
            emoji = "💪" if quality_diff > 0 else "🔽"
            insights.append(f"{emoji} **Quality Work**: {abs(quality_diff)} {'more' if quality_diff > 0 else 'fewer'} quality sessions in {season2['season']}")

        # Consistency
        violation_change = season2['floor_violations'] - season1['floor_violations']
        if violation_change < 0:
            insights.append(f"✅ **Improved Consistency**: {abs(violation_change)} fewer floor violations in {season2['season']}")
        elif violation_change > 0:
            insights.append(f"⚠️ **Consistency Alert**: {violation_change} more floor violations in {season2['season']}")

        # Long runs
        long_run_diff = season2['long_runs'] - season1['long_runs']
        if abs(long_run_diff) > 1:
            emoji = "🏃" if long_run_diff > 0 else "🔽"
            insights.append(f"{emoji} **Long Run Volume**: {abs(long_run_diff)} {'more' if long_run_diff > 0 else 'fewer'} long runs in {season2['season']}")

        if insights:
            for insight in insights:
                st.markdown(f"- {insight}")
        else:
            st.info("Seasons are very similar in structure and volume.")

except Exception as e:
    st.error(f"Error loading data: {str(e)}")
    import traceback
    st.code(traceback.format_exc())
