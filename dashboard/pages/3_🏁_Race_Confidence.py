"""
Race Confidence Analyzer Page

Assess race readiness and build confidence through data-driven analysis.
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from utils.data_loader import activities_to_dataframe, load_activities
from utils.metrics import (
    find_race_pace_segments, calculate_pace_degradation,
)

# Page config
st.set_page_config(page_title="Race Confidence", page_icon="🏁", layout="wide")

st.title("🏁 Race Confidence Analyzer")
st.markdown("Build confidence through data-driven race readiness analysis")

# Load data - NO CACHING to avoid pickle issues with datetime
def load_data():
    df = activities_to_dataframe()
    activities = load_activities()
    return df, activities

def _parse_activity_dt(s: str):
    for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M:%S.%f'):
        try:
            return datetime.strptime(s, fmt)
        except Exception:
            continue
    return None

try:
    df, activities = load_data()

    if df.empty:
        st.error("No running activities found. Run `python scripts/sync-garmin.py` to sync data.")
        st.stop()

    # Sidebar - Race configuration
    st.sidebar.header("Race Configuration")

    race_distance = st.sidebar.selectbox(
        "Race Distance",
        ["Half Marathon (21.1 km)", "10K (10 km)", "Custom"],
        index=0
    )

    if race_distance == "Custom":
        target_distance = st.sidebar.number_input("Distance (km)", min_value=1.0, max_value=50.0, value=21.1, step=0.1)
    elif race_distance == "Half Marathon (21.1 km)":
        target_distance = 21.1
    else:  # 10K
        target_distance = 10.0

    # Target pace input
    st.sidebar.subheader("Target Pace")
    target_min = st.sidebar.number_input("Minutes per km", min_value=3, max_value=10, value=5, step=1)
    target_sec = st.sidebar.number_input("Seconds per km", min_value=0, max_value=59, value=40, step=5)
    target_pace_seconds = target_min * 60 + target_sec
    target_pace_str = f"{target_min}:{target_sec:02d}"

    # Pace tolerance (± seconds) for matching race-pace laps
    tolerance = st.sidebar.slider(
        "Pace Tolerance (± sec)", min_value=5, max_value=30, value=15, step=5,
        help="How tightly to match target pace when counting laps at race pace"
    )
    pace_min = target_pace_seconds - tolerance
    pace_max = target_pace_seconds + tolerance

    # Analysis period
    analysis_weeks = st.sidebar.slider("Analysis Period (weeks)", min_value=4, max_value=24, value=12, step=2)
    cutoff_dt = datetime.now() - timedelta(weeks=analysis_weeks)

    # Filter recent activities using robust datetime parsing
    recent_activities = [a for a in activities if (d:=_parse_activity_dt(a.get('date',''))) and d >= cutoff_dt]
    recent_df = df[df['date'] >= pd.Timestamp(cutoff_dt)]

    st.markdown("---")

    # Main analysis
    st.header(f"Can You Hold {target_pace_str}/km for {target_distance}km?")

    # Find race pace segments
    race_pace_segments = find_race_pace_segments(recent_activities, pace_min, pace_max)

    # Calculate confidence metrics
    total_km_at_pace = race_pace_segments['distance'].sum() if not race_pace_segments.empty else 0
    num_sessions_at_pace = race_pace_segments['date'].nunique() if not race_pace_segments.empty else 0

    # Longest stretch at pace within a session (sum of within-range laps per activity)
    if not race_pace_segments.empty:
        by_activity = race_pace_segments.groupby(['date', 'activity_name'])['distance'].sum().reset_index()
        longest_stretch = float(by_activity['distance'].max())
        longest_stretch_date = by_activity.loc[by_activity['distance'].idxmax(), 'date']
    else:
        longest_stretch = 0.0
        longest_stretch_date = None

    # Faster pace capability (10% faster)
    faster_pace_seconds = target_pace_seconds * 0.9
    faster_segments = find_race_pace_segments(recent_activities, faster_pace_seconds - tolerance, faster_pace_seconds + tolerance)
    faster_km = faster_segments['distance'].sum() if not faster_segments.empty else 0

    # Long run endurance (runs >= 15km)
    long_runs = recent_df[recent_df['distance_km'] >= 15]
    num_long_runs = len(long_runs)

    # Debug: show merged long runs present in the window (using merged activities)
    with st.expander("Debug: Merged long runs in window", expanded=False):
        lines = []
        for a in recent_activities:
            d_km = float(a.get('distance_km', 0) or 0)
            if d_km >= 12:  # show candidates for degradation (>=12km)
                splits = (a.get('splits') or {})
                laps = splits.get('lapDTOs') or []
                lap_count = len(laps)
                has_lap_hr = any(((l.get('averageHR') or 0) > 0) for l in laps) if laps else False
                source = a.get('source', 'unknown')
                splits_source = a.get('splits_source', 'garmin' if laps else 'none')
                lines.append(
                    f"- {a.get('date','')[:10]} — {d_km:.1f} km | source={source}, laps={lap_count}, lapHR={'yes' if has_lap_hr else 'no'}, splits_source={splits_source}"
                )
        st.markdown("\n".join(lines) if lines else "- (none)")

    # Readiness assessment
    confidence_checks = {
        f"Run ≥10km at {target_pace_str}/km pace": longest_stretch >= 10,
        f"Faster than {target_pace_str}/km (sustained ≥5km)": faster_km >= 5,
        f"Total ≥20km at race pace": total_km_at_pace >= 20,
        f"≥3 long runs (≥15km)": num_long_runs >= 3
    }

    confidence_score = sum(bool(v) for v in confidence_checks.values())

    col1, col2 = st.columns([2,1])
    with col1:
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=confidence_score,
            gauge={'axis': {'range': [0, 4]}},
            title={'text': "Confidence Score"}
        ))
        fig_gauge.update_layout(height=260)
        st.plotly_chart(fig_gauge, use_container_width=True)

    with col2:
        st.subheader("Readiness Assessment")
        for label, ok in confidence_checks.items():
            st.write(("✅ " if ok else "❌ ") + label)

    # Pace degradation in long runs (fatigue)
    st.markdown("---")
    st.header("Pace Degradation (Fatigue)")
    degradation_data = []
    for activity in recent_activities:
        if activity.get('distance_km', 0) >= 12:
            try:
                degradation = calculate_pace_degradation(activity)
                degradation_data.append({
                    'date': activity['date'][:10],
                    'name': activity.get('name'),
                    'distance': activity.get('distance_km', 0),
                    'degradation': degradation
                })
            except Exception:
                continue

    if degradation_data:
        deg_df = pd.DataFrame(degradation_data).sort_values('date')
        colors = ['#00cc00' if d <= 3 else '#ffa500' if d <= 7 else '#ff4b4b' for d in deg_df['degradation']]
        fig_deg = go.Figure()
        fig_deg.add_trace(go.Bar(
            x=deg_df['date'], y=deg_df['degradation'], marker_color=colors,
            text=deg_df['degradation'].round(1), textposition='outside', customdata=deg_df['distance'],
            hovertemplate='<b>%{x}</b><br>Degradation: %{y:.1f}%<br>Distance: %{customdata:.1f} km<extra></extra>'
        ))
        fig_deg.add_hline(y=5, line_dash="dash", line_color="orange", annotation_text="Target <5%", annotation_position="right")
        fig_deg.update_layout(xaxis_title="Date", yaxis_title="Pace Degradation (%)", height=400, showlegend=False)
        st.plotly_chart(fig_deg, use_container_width=True)

        with st.expander("Debug: Pace degradation inputs", expanded=False):
            lines = [
                f"- {row['date']}: {row['name']} — {row['distance']:.1f} km, degradation {row['degradation']:.1f}%"
                for _, row in deg_df.iterrows()
            ]
            st.markdown("\n".join(lines) if lines else "- (no entries)")
    else:
        st.info(f"No long runs (≥12km) found in the last {analysis_weeks} weeks to analyze pace degradation.")

    # HR stability analysis
    st.markdown("---")
    st.header("Heart Rate Stability")
    st.markdown("Track HR drift during long runs - stable HR = good aerobic fitness")

    hr_stability_data = []
    total_long_runs = 0
    total_long_runs_with_splits = 0
    for activity in recent_activities:
        if activity.get('distance_km', 0) >= 15:
            total_long_runs += 1
        if activity.get('distance_km', 0) >= 15 and activity.get('splits'):
            lap_dtos = activity['splits'].get('lapDTOs', [])
            if lap_dtos:
                total_long_runs_with_splits += 1
            if len(lap_dtos) >= 4:
                q = max(1, len(lap_dtos)//4)
                first_quarter = lap_dtos[:q]
                last_quarter = lap_dtos[-q:]
                first_hr = sum((l.get('averageHR') or 0) for l in first_quarter) / len(first_quarter)
                last_hr = sum((l.get('averageHR') or 0) for l in last_quarter) / len(last_quarter)
                if first_hr > 0:
                    drift = ((last_hr - first_hr) / first_hr) * 100
                    hr_stability_data.append({
                        'date': activity['date'][:10],
                        'name': activity.get('name'),
                        'distance': activity.get('distance_km', 0),
                        'drift_pct': drift
                    })

    with st.expander("Debug: HR data in analysis window", expanded=False):
        st.markdown(
            f"- analysis_weeks: {analysis_weeks}\n"
            f"- cutoff: {cutoff_dt.strftime('%Y-%m-%d')}\n"
            f"- recent_activities: {len(recent_activities)}\n"
            f"- long_runs_>=15km: {total_long_runs}\n"
            f"- long_runs_with_splits: {total_long_runs_with_splits}"
        )

    if hr_stability_data:
        hr_df = pd.DataFrame(hr_stability_data)
        fig_hr = go.Figure()
        fig_hr.add_trace(go.Scatter(
            x=hr_df['date'], y=hr_df['drift_pct'], mode='lines+markers',
            line=dict(color='#FF6B6B', width=3), marker=dict(size=8),
            hovertemplate='<b>%{x}</b><br>HR Drift: %{y:.1f}%<extra></extra>'
        ))
        fig_hr.add_hline(y=5, line_dash="dash", line_color="orange", annotation_text="Target <5%")
        fig_hr.update_layout(xaxis_title="Date", yaxis_title="HR Drift (%)", height=400, showlegend=False)
        st.plotly_chart(fig_hr, use_container_width=True)
    else:
        if total_long_runs > 0 and total_long_runs_with_splits == 0:
            st.info("Long runs found but without per-km HR splits in this window. If these are Strava-only, backfill Garmin: `python scripts/sync-garmin.py 90`.")
        else:
            st.info(f"No long runs (≥15km) with HR data found in the last {analysis_weeks} weeks.")

except Exception as e:
    st.error(f"Error loading data: {e}")
    import traceback
    st.code(traceback.format_exc())
