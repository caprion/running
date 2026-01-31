"""
Training Load & Recovery Dashboard

Monitor training stress, recovery metrics, and physiological trends.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from utils.data_loader import (
    activities_to_dataframe, 
    get_weekly_summary, 
    get_training_status,
    get_sleep_data,
    load_garmin_data
)
from utils.metrics import FLOOR_THRESHOLD, YELLOW_THRESHOLD

# Page config
st.set_page_config(page_title="Training Load", page_icon="📈", layout="wide")

st.title("📈 Training Load & Recovery")
st.markdown("Monitor training stress, recovery metrics, and physiological adaptation")

# Threshold constants (adjustable)
RHR_YELLOW = 5  # bpm above baseline = yellow
RHR_RED = 8  # bpm above baseline = red
SLEEP_TARGET = 7.5  # hours
DEEP_SLEEP_TARGET = 15  # percent

# Dynamic baseline calculation
def get_max_hr_from_activities(df):
    """Scan activities from last 12 months and return highest observed max HR"""
    if df.empty or 'max_hr' not in df.columns:
        return 197  # Fallback default
    
    # Filter to last 12 months for current fitness relevance
    cutoff_date = datetime.now() - timedelta(days=365)
    recent_df = df[df['date'] >= cutoff_date]
    
    if recent_df.empty:
        max_hr = df['max_hr'].max()  # Fall back to all data if no recent
    else:
        max_hr = recent_df['max_hr'].max()
    
    return int(max_hr) if pd.notna(max_hr) and max_hr > 0 else 197

def get_baseline_rhr(training_status):
    """Get RHR baseline from training status or use default"""
    rhr_7d = training_status.get('resting_hr_7d_avg')
    if rhr_7d and rhr_7d > 0:
        return rhr_7d
    return 59  # Fallback to Jan 2026 baseline

# Load data
def load_all_data():
    """Load all data sources for training load analysis"""
    df = activities_to_dataframe()
    weekly = get_weekly_summary(df)
    training_status = get_training_status()
    sleep_data = get_sleep_data()
    return df, weekly, training_status, sleep_data

try:
    df, weekly, training_status, sleep_data = load_all_data()
    
    # Calculate dynamic baselines from actual data
    MAX_HR = get_max_hr_from_activities(df)
    BASELINE_RHR = get_baseline_rhr(training_status)
    
    if df.empty:
        st.error("No running activities found. Run `python scripts/incremental-sync.py --days 90` to sync data.")
        st.stop()

    # Show dynamic baselines in sidebar
    st.sidebar.markdown("### 📐 Current Baselines")
    st.sidebar.markdown(f"**Max HR:** {MAX_HR} bpm")
    st.sidebar.markdown(f"**RHR Baseline:** {BASELINE_RHR} bpm")
    st.sidebar.caption("_Auto-calculated from your data. New max HR efforts will update zones automatically._")

    # ============================================
    # CURRENT STATUS CARDS
    # ============================================
    st.subheader("📊 Current Training Status")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        vo2max = training_status.get('vo2max', 0)
        vo2max_display = f"{vo2max}" if vo2max else "N/A"
        st.metric(
            "VO2max", 
            vo2max_display,
            help="Garmin's estimated VO2max. Target: 43+ for sub-2:00 HM"
        )
    
    with col2:
        load_7d = training_status.get('training_load_7d', 0)
        load_display = f"{load_7d}" if load_7d else "N/A"
        st.metric(
            "7-Day Load",
            load_display,
            help="Garmin's Training Load (acute stress). Higher = more recent stress."
        )
    
    with col3:
        rhr = training_status.get('resting_hr', 0)
        rhr_7d = training_status.get('resting_hr_7d_avg', BASELINE_RHR)
        if rhr and rhr_7d:
            delta = rhr - BASELINE_RHR
            delta_display = f"{delta:+.0f} vs baseline"
            delta_color = "inverse" if delta > 0 else "normal"
        else:
            delta_display = None
            delta_color = "off"
        st.metric(
            "Resting HR",
            f"{rhr_7d} bpm" if rhr_7d else "N/A",
            delta=delta_display,
            delta_color=delta_color,
            help=f"7-day avg RHR. Baseline: {BASELINE_RHR} bpm. Elevated RHR = fatigue/stress."
        )
    
    with col4:
        status_label = training_status.get('training_effect_label', 'Unknown')
        # Color code the status
        status_colors = {
            'Productive': '🟢',
            'Peaking': '🟢',
            'Maintaining': '🟡',
            'Recovery': '🟡',
            'Unproductive': '🔴',
            'Detraining': '🔴',
            'Overreaching': '🔴'
        }
        status_icon = status_colors.get(status_label, '⚪')
        st.metric(
            "Training Status",
            f"{status_icon} {status_label}",
            help="Garmin's assessment of training effectiveness"
        )

    # ============================================
    # RECOVERY METRICS (Sleep & RHR)
    # ============================================
    st.markdown("---")
    st.subheader("😴 Recovery Metrics")
    
    if sleep_data:
        # Process sleep data
        sleep_df = pd.DataFrame(sleep_data)
        sleep_df['date'] = pd.to_datetime(sleep_df['date'])
        sleep_df = sleep_df.sort_values('date')
        
        # Calculate deep sleep percentage
        sleep_df['deep_pct'] = (sleep_df['deep_sleep_seconds'] / sleep_df['sleep_seconds'] * 100).round(1)
        
        # Get last 7 days
        last_7_days = sleep_df.tail(14)  # Show 2 weeks for context
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Sleep duration trend
            fig_sleep = go.Figure()
            
            # Add sleep hours bars
            colors = ['#2ecc71' if h >= SLEEP_TARGET else '#f39c12' if h >= 6 else '#e74c3c' 
                      for h in last_7_days['sleep_hours']]
            
            fig_sleep.add_trace(go.Bar(
                x=last_7_days['date'],
                y=last_7_days['sleep_hours'],
                marker_color=colors,
                name='Sleep Duration',
                text=[f"{h:.1f}h" for h in last_7_days['sleep_hours']],
                textposition='outside'
            ))
            
            # Add target line
            fig_sleep.add_hline(
                y=SLEEP_TARGET, 
                line_dash="dash", 
                line_color="green",
                annotation_text=f"Target: {SLEEP_TARGET}h",
                annotation_position="right"
            )
            
            fig_sleep.update_layout(
                title="Sleep Duration (Last 14 Days)",
                xaxis_title="Date",
                yaxis_title="Hours",
                yaxis_range=[0, 10],
                showlegend=False,
                height=350
            )
            
            st.plotly_chart(fig_sleep, use_container_width=True)
        
        with col2:
            # Deep sleep percentage trend
            fig_deep = go.Figure()
            
            colors_deep = ['#2ecc71' if p >= DEEP_SLEEP_TARGET else '#f39c12' if p >= 10 else '#e74c3c' 
                           for p in last_7_days['deep_pct']]
            
            fig_deep.add_trace(go.Bar(
                x=last_7_days['date'],
                y=last_7_days['deep_pct'],
                marker_color=colors_deep,
                name='Deep Sleep %',
                text=[f"{p:.0f}%" for p in last_7_days['deep_pct']],
                textposition='outside'
            ))
            
            # Add target line
            fig_deep.add_hline(
                y=DEEP_SLEEP_TARGET, 
                line_dash="dash", 
                line_color="green",
                annotation_text=f"Target: {DEEP_SLEEP_TARGET}%",
                annotation_position="right"
            )
            
            fig_deep.update_layout(
                title="Deep Sleep % (Last 14 Days)",
                xaxis_title="Date",
                yaxis_title="Percentage",
                yaxis_range=[0, 30],
                showlegend=False,
                height=350
            )
            
            st.plotly_chart(fig_deep, use_container_width=True)
        
        # Sleep summary stats
        recent_sleep = sleep_df.tail(7)
        avg_sleep = recent_sleep['sleep_hours'].mean()
        avg_deep = recent_sleep['deep_pct'].mean()
        
        sleep_status = "🟢" if avg_sleep >= SLEEP_TARGET else "🟡" if avg_sleep >= 6 else "🔴"
        deep_status = "🟢" if avg_deep >= DEEP_SLEEP_TARGET else "🟡" if avg_deep >= 10 else "🔴"
        
        st.markdown(f"""
        **7-Day Averages:** {sleep_status} Sleep: **{avg_sleep:.1f}h** (target: {SLEEP_TARGET}h) | 
        {deep_status} Deep Sleep: **{avg_deep:.1f}%** (target: {DEEP_SLEEP_TARGET}%)
        """)
    else:
        st.info("No sleep data available. Sync from Garmin to see recovery metrics.")

    # ============================================
    # TRAINING LOAD TREND
    # ============================================
    st.markdown("---")
    st.subheader("🏃 Training Load Trend")
    
    # Calculate weekly load proxy (distance × avg HR factor)
    # This is an approximation since Garmin doesn't provide historical load
    weekly_for_load = weekly.tail(12).copy()
    
    if not weekly_for_load.empty:
        # Create a simple load proxy: distance × (avg_hr / 150) as intensity factor
        # Higher HR sessions count more
        weekly_for_load['load_proxy'] = weekly_for_load.apply(
            lambda row: row['distance_km'] * (row['avg_hr'] / 150 if pd.notna(row['avg_hr']) and row['avg_hr'] > 0 else 1),
            axis=1
        ).round(0)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Volume trend
            fig_volume = go.Figure()
            
            # Color by status
            colors_vol = ['#2ecc71' if s == 'GREEN' else '#f39c12' if s == 'YELLOW' else '#e74c3c' 
                          for s in weekly_for_load['status']]
            
            fig_volume.add_trace(go.Bar(
                x=weekly_for_load['week_key'],
                y=weekly_for_load['distance_km'],
                marker_color=colors_vol,
                name='Volume',
                text=[f"{d:.0f}km" for d in weekly_for_load['distance_km']],
                textposition='outside'
            ))
            
            # Add floor threshold
            fig_volume.add_hline(
                y=FLOOR_THRESHOLD, 
                line_dash="dash", 
                line_color="red",
                annotation_text=f"Floor: {FLOOR_THRESHOLD}km",
                annotation_position="right"
            )
            
            fig_volume.update_layout(
                title="Weekly Volume (Last 12 Weeks)",
                xaxis_title="Week",
                yaxis_title="Distance (km)",
                showlegend=False,
                height=400
            )
            
            st.plotly_chart(fig_volume, use_container_width=True)
        
        with col2:
            # Load proxy trend
            fig_load = go.Figure()
            
            fig_load.add_trace(go.Scatter(
                x=weekly_for_load['week_key'],
                y=weekly_for_load['load_proxy'],
                mode='lines+markers',
                name='Training Load',
                line=dict(color='#3498db', width=3),
                marker=dict(size=10)
            ))
            
            # Add average line
            avg_load = weekly_for_load['load_proxy'].mean()
            fig_load.add_hline(
                y=avg_load, 
                line_dash="dash", 
                line_color="gray",
                annotation_text=f"Avg: {avg_load:.0f}",
                annotation_position="right"
            )
            
            fig_load.update_layout(
                title="Estimated Training Load (Volume × Intensity)",
                xaxis_title="Week",
                yaxis_title="Load Units",
                showlegend=False,
                height=400
            )
            
            st.plotly_chart(fig_load, use_container_width=True)
        
        # Week-over-week change
        if len(weekly_for_load) >= 2:
            current_week = weekly_for_load.iloc[-1]
            prev_week = weekly_for_load.iloc[-2]
            
            vol_change = current_week['distance_km'] - prev_week['distance_km']
            vol_pct = (vol_change / prev_week['distance_km'] * 100) if prev_week['distance_km'] > 0 else 0
            
            load_change = current_week['load_proxy'] - prev_week['load_proxy']
            load_pct = (load_change / prev_week['load_proxy'] * 100) if prev_week['load_proxy'] > 0 else 0
            
            st.markdown(f"""
            **Week-over-Week Change:** 
            Volume: **{vol_change:+.1f}km** ({vol_pct:+.0f}%) | 
            Load: **{load_change:+.0f}** ({load_pct:+.0f}%)
            """)

    # ============================================
    # HR ZONES DISTRIBUTION (Recent Activities)
    # ============================================
    st.markdown("---")
    st.subheader("❤️ Heart Rate Analysis")
    
    # Get recent activities with HR data
    recent_activities = df.tail(20).copy()
    recent_with_hr = recent_activities[recent_activities['avg_hr'].notna()].copy()
    
    if not recent_with_hr.empty:
        col1, col2 = st.columns(2)
        
        # Calculate dynamic zone thresholds based on MAX_HR
        z1_max = int(MAX_HR * 0.60)  # 60% of max
        z2_max = int(MAX_HR * 0.70)  # 70% of max  
        z3_max = int(MAX_HR * 0.80)  # 80% of max
        z4_max = int(MAX_HR * 0.90)  # 90% of max
        
        with col1:
            # Avg HR by activity
            fig_hr = go.Figure()
            
            # Define HR zones dynamically
            def get_hr_zone(hr):
                if hr < z1_max: return 'Z1 Recovery'
                elif hr < z2_max: return 'Z2 Easy'
                elif hr < z3_max: return 'Z3 Tempo'
                elif hr < z4_max: return 'Z4 Threshold'
                else: return 'Z5 Max'
            
            recent_with_hr['hr_zone'] = recent_with_hr['avg_hr'].apply(get_hr_zone)
            
            # Color by zone
            zone_colors = {
                'Z1 Recovery': '#3498db',
                'Z2 Easy': '#2ecc71',
                'Z3 Tempo': '#f39c12',
                'Z4 Threshold': '#e74c3c',
                'Z5 Max': '#9b59b6'
            }
            colors_hr = [zone_colors.get(z, 'gray') for z in recent_with_hr['hr_zone']]
            
            fig_hr.add_trace(go.Scatter(
                x=recent_with_hr['date'],
                y=recent_with_hr['avg_hr'],
                mode='markers',
                marker=dict(
                    size=recent_with_hr['distance_km'] * 2,  # Size by distance
                    color=colors_hr,
                    line=dict(width=1, color='white')
                ),
                text=[f"{row['name']}<br>{row['distance_km']:.1f}km @ {row['avg_hr']:.0f}bpm" 
                      for _, row in recent_with_hr.iterrows()],
                hoverinfo='text'
            ))
            
            # Add zone lines
            fig_hr.add_hline(y=z1_max, line_dash="dot", line_color="#2ecc71", annotation_text="Z2", annotation_position="left")
            fig_hr.add_hline(y=z2_max, line_dash="dot", line_color="#f39c12", annotation_text="Z3", annotation_position="left")
            fig_hr.add_hline(y=z3_max, line_dash="dot", line_color="#e74c3c", annotation_text="Z4", annotation_position="left")
            
            fig_hr.update_layout(
                title="Average HR by Activity (Last 20 Runs)",
                xaxis_title="Date",
                yaxis_title="Avg HR (bpm)",
                yaxis_range=[100, 180],
                showlegend=False,
                height=400
            )
            
            st.plotly_chart(fig_hr, use_container_width=True)
        
        with col2:
            # Zone distribution pie
            zone_counts = recent_with_hr['hr_zone'].value_counts()
            
            fig_pie = go.Figure(data=[go.Pie(
                labels=zone_counts.index,
                values=zone_counts.values,
                marker_colors=[zone_colors.get(z, 'gray') for z in zone_counts.index],
                hole=0.4
            )])
            
            fig_pie.update_layout(
                title="HR Zone Distribution (Last 20 Runs)",
                height=400
            )
            
            st.plotly_chart(fig_pie, use_container_width=True)
        
        # Zone summary table
        st.markdown(f"**HR Zone Guide (based on Max HR {MAX_HR}, RHR {BASELINE_RHR}):**")
        zone_table = f"""
| Zone | Name | BPM Range | Purpose |
|------|------|-----------|--------|
| Z1 | Recovery | <{z1_max} | Active recovery |
| Z2 | Easy/Aerobic | {z1_max}-{z2_max} | Base building (most runs) |
| Z3 | Tempo | {z2_max}-{z3_max} | Threshold development |
| Z4 | Threshold | {z3_max}-{z4_max} | VO2max, intervals |
| Z5 | Max | {z4_max}-{MAX_HR} | Race finish, strides |
"""
        st.markdown(zone_table)

    # ============================================
    # RECOVERY RECOMMENDATIONS
    # ============================================
    st.markdown("---")
    st.subheader("🎯 Recovery Assessment")
    
    # Build recommendations based on current data
    recommendations = []
    status_overall = "🟢"
    
    # Check RHR
    rhr_7d = training_status.get('resting_hr_7d_avg', BASELINE_RHR)
    if rhr_7d:
        rhr_delta = rhr_7d - BASELINE_RHR
        if rhr_delta > RHR_RED:
            recommendations.append(f"🔴 **RHR elevated by {rhr_delta} bpm** - Consider rest day or very easy running")
            status_overall = "🔴"
        elif rhr_delta > RHR_YELLOW:
            recommendations.append(f"🟡 **RHR elevated by {rhr_delta} bpm** - Monitor fatigue, consider easier intensity")
            if status_overall != "🔴": status_overall = "🟡"
    
    # Check Training Status
    status_label = training_status.get('training_effect_label', '')
    if status_label in ['Unproductive', 'Detraining', 'Overreaching']:
        recommendations.append(f"🔴 **Training Status: {status_label}** - Review load and recovery balance")
        status_overall = "🔴"
    elif status_label in ['Maintaining', 'Recovery']:
        recommendations.append(f"🟡 **Training Status: {status_label}** - Consistency is key, may need load adjustment")
        if status_overall != "🔴": status_overall = "🟡"
    
    # Check Sleep
    if sleep_data:
        recent_sleep = pd.DataFrame(sleep_data).tail(7)
        avg_sleep = recent_sleep['sleep_hours'].mean() if 'sleep_hours' in recent_sleep else 0
        if avg_sleep < 6:
            recommendations.append(f"🔴 **Sleep averaging {avg_sleep:.1f}h** - Prioritize sleep before training")
            status_overall = "🔴"
        elif avg_sleep < SLEEP_TARGET:
            recommendations.append(f"🟡 **Sleep averaging {avg_sleep:.1f}h** - Try to get {SLEEP_TARGET}h+ per night")
            if status_overall != "🔴": status_overall = "🟡"
    
    # Display overall status
    status_text = {
        "🟢": "Good to Train",
        "🟡": "Monitor & Adjust", 
        "🔴": "Recovery Needed"
    }
    
    st.markdown(f"### Overall Recovery Status: {status_overall} {status_text[status_overall]}")
    
    if recommendations:
        for rec in recommendations:
            st.markdown(f"- {rec}")
    else:
        st.markdown("✅ All recovery metrics look good. Proceed with planned training!")

    # ============================================
    # DEBUG/DETAILS EXPANDER
    # ============================================
    with st.expander("🔍 Debug: Raw Training Status Data"):
        st.json(training_status)
        
        if sleep_data:
            st.markdown("**Recent Sleep Data (last 7 days):**")
            recent_sleep_display = pd.DataFrame(sleep_data).tail(7)
            # Display as markdown table
            st.markdown("| Date | Hours | Deep % |")
            st.markdown("|------|-------|--------|")
            for _, row in recent_sleep_display.iterrows():
                deep_pct = (row['deep_sleep_seconds'] / row['sleep_seconds'] * 100) if row['sleep_seconds'] else 0
                st.markdown(f"| {row['date']} | {row['sleep_hours']:.1f}h | {deep_pct:.0f}% |")

except Exception as e:
    st.error(f"Error loading data: {e}")
    st.info("Try running `python scripts/incremental-sync.py --days 7` to refresh data cache.")
    
    with st.expander("Error details"):
        import traceback
        st.code(traceback.format_exc())
