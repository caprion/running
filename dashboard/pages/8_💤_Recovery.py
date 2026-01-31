"""
Recovery Dashboard

Monitor sleep quality, stress levels, and recovery trends.
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
    get_sleep_data,
    get_training_status,
    load_garmin_data
)

# Page config
st.set_page_config(page_title="Recovery", page_icon="💤", layout="wide")

st.title("💤 Recovery & Sleep")
st.markdown("Monitor sleep quality, stress levels, and recovery readiness")

# Targets
SLEEP_TARGET = 7.5  # hours
DEEP_SLEEP_TARGET = 15  # percent
REM_TARGET = 20  # percent
STRESS_LOW_TARGET = 30  # avg stress below this is good

def load_recovery_data():
    """Load all recovery-related data"""
    garmin_data = load_garmin_data()
    sleep_data = get_sleep_data()
    stress_data = garmin_data.get('stress', [])
    training_status = get_training_status()
    return sleep_data, stress_data, training_status

try:
    sleep_data, stress_data, training_status = load_recovery_data()
    
    if not sleep_data:
        st.warning("No sleep data available. Make sure Garmin sync includes sleep data.")
        st.stop()

    # Convert to DataFrames
    sleep_df = pd.DataFrame(sleep_data)
    sleep_df['date'] = pd.to_datetime(sleep_df['date'])
    sleep_df = sleep_df.sort_values('date')
    
    # Calculate percentages
    sleep_df['deep_pct'] = (sleep_df['deep_sleep_seconds'] / sleep_df['sleep_seconds'] * 100).round(1)
    sleep_df['light_pct'] = (sleep_df['light_sleep_seconds'] / sleep_df['sleep_seconds'] * 100).round(1)
    sleep_df['rem_pct'] = (sleep_df['rem_sleep_seconds'] / sleep_df['sleep_seconds'] * 100).round(1)
    sleep_df['awake_pct'] = (sleep_df['awake_seconds'] / sleep_df['sleep_seconds'] * 100).round(1)

    # Sidebar filters
    st.sidebar.header("Time Range")
    range_options = {
        "Last 7 Days": 7,
        "Last 14 Days": 14,
        "Last 30 Days": 30,
        "Last 90 Days": 90,
        "All Time": len(sleep_df)
    }
    selected_range = st.sidebar.selectbox("View", list(range_options.keys()), index=1)
    n_days = range_options[selected_range]
    
    sleep_filtered = sleep_df.tail(n_days)

    # ============================================
    # CURRENT STATUS CARDS
    # ============================================
    st.subheader("📊 Recovery Status")
    
    # Calculate 7-day averages for status
    last_7 = sleep_df.tail(7)
    avg_sleep = last_7['sleep_hours'].mean()
    avg_deep = last_7['deep_pct'].mean()
    avg_rem = last_7['rem_pct'].mean()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        sleep_status = "🟢" if avg_sleep >= SLEEP_TARGET else "🟡" if avg_sleep >= 6.5 else "🔴"
        delta = avg_sleep - SLEEP_TARGET
        st.metric(
            "Avg Sleep (7d)",
            f"{avg_sleep:.1f}h",
            delta=f"{delta:+.1f}h vs target",
            delta_color="normal" if delta >= 0 else "inverse",
            help=f"Target: {SLEEP_TARGET}h. 7-day rolling average."
        )
    
    with col2:
        deep_status = "🟢" if avg_deep >= DEEP_SLEEP_TARGET else "🟡" if avg_deep >= 10 else "🔴"
        st.metric(
            "Avg Deep Sleep (7d)",
            f"{avg_deep:.1f}%",
            delta=f"{avg_deep - DEEP_SLEEP_TARGET:+.1f}% vs target",
            delta_color="normal" if avg_deep >= DEEP_SLEEP_TARGET else "inverse",
            help=f"Target: {DEEP_SLEEP_TARGET}%. Critical for physical recovery."
        )
    
    with col3:
        rem_status = "🟢" if avg_rem >= REM_TARGET else "🟡" if avg_rem >= 15 else "🔴"
        st.metric(
            "Avg REM Sleep (7d)",
            f"{avg_rem:.1f}%",
            delta=f"{avg_rem - REM_TARGET:+.1f}% vs target",
            delta_color="normal" if avg_rem >= REM_TARGET else "inverse",
            help=f"Target: {REM_TARGET}%. Important for mental recovery."
        )
    
    with col4:
        # RHR from training status
        rhr = training_status.get('resting_hr_7d_avg', 0)
        rhr_current = training_status.get('resting_hr', 0)
        if rhr and rhr_current:
            delta_rhr = rhr_current - rhr
            st.metric(
                "Resting HR (7d avg)",
                f"{rhr} bpm",
                delta=f"{delta_rhr:+.0f} today",
                delta_color="inverse" if delta_rhr > 0 else "normal",
                help="Lower is better. Elevated RHR indicates fatigue/stress."
            )
        else:
            st.metric("Resting HR", "N/A")

    # ============================================
    # SLEEP DURATION TREND
    # ============================================
    st.markdown("---")
    st.subheader("🛏️ Sleep Duration Trend")
    
    fig_duration = go.Figure()
    
    # Color bars by target
    colors = ['#2ecc71' if h >= SLEEP_TARGET else '#f39c12' if h >= 6.5 else '#e74c3c' 
              for h in sleep_filtered['sleep_hours']]
    
    fig_duration.add_trace(go.Bar(
        x=sleep_filtered['date'],
        y=sleep_filtered['sleep_hours'],
        marker_color=colors,
        name='Sleep Duration',
        hovertemplate='%{x|%b %d}<br>%{y:.1f} hours<extra></extra>'
    ))
    
    # Add target line
    fig_duration.add_hline(
        y=SLEEP_TARGET, 
        line_dash="dash", 
        line_color="green",
        annotation_text=f"Target: {SLEEP_TARGET}h",
        annotation_position="right"
    )
    
    # Add 7-day rolling average
    if len(sleep_filtered) >= 7:
        sleep_filtered_copy = sleep_filtered.copy()
        sleep_filtered_copy['rolling_avg'] = sleep_filtered_copy['sleep_hours'].rolling(7, min_periods=3).mean()
        fig_duration.add_trace(go.Scatter(
            x=sleep_filtered_copy['date'],
            y=sleep_filtered_copy['rolling_avg'],
            mode='lines',
            name='7-day Avg',
            line=dict(color='#3498db', width=3, dash='dot')
        ))
    
    fig_duration.update_layout(
        xaxis_title="Date",
        yaxis_title="Hours",
        yaxis_range=[0, 10],
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        height=400
    )
    
    st.plotly_chart(fig_duration, use_container_width=True)

    # ============================================
    # SLEEP STAGES BREAKDOWN
    # ============================================
    st.markdown("---")
    st.subheader("📊 Sleep Stages")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Stacked area chart of sleep stages
        fig_stages = go.Figure()
        
        fig_stages.add_trace(go.Scatter(
            x=sleep_filtered['date'],
            y=sleep_filtered['deep_pct'],
            mode='lines',
            name='Deep',
            fill='tozeroy',
            line=dict(color='#3498db'),
            stackgroup='one'
        ))
        
        fig_stages.add_trace(go.Scatter(
            x=sleep_filtered['date'],
            y=sleep_filtered['light_pct'],
            mode='lines',
            name='Light',
            fill='tonexty',
            line=dict(color='#95a5a6'),
            stackgroup='one'
        ))
        
        fig_stages.add_trace(go.Scatter(
            x=sleep_filtered['date'],
            y=sleep_filtered['rem_pct'],
            mode='lines',
            name='REM',
            fill='tonexty',
            line=dict(color='#9b59b6'),
            stackgroup='one'
        ))
        
        fig_stages.update_layout(
            title="Sleep Stage Distribution Over Time",
            xaxis_title="Date",
            yaxis_title="Percentage",
            yaxis_range=[0, 100],
            height=400,
            legend=dict(orientation="h", yanchor="bottom", y=1.02)
        )
        
        st.plotly_chart(fig_stages, use_container_width=True)
    
    with col2:
        # Average pie chart
        avg_stages = {
            'Deep': sleep_filtered['deep_pct'].mean(),
            'Light': sleep_filtered['light_pct'].mean(),
            'REM': sleep_filtered['rem_pct'].mean(),
            'Awake': sleep_filtered['awake_pct'].mean()
        }
        
        fig_pie = go.Figure(data=[go.Pie(
            labels=list(avg_stages.keys()),
            values=list(avg_stages.values()),
            marker_colors=['#3498db', '#95a5a6', '#9b59b6', '#e74c3c'],
            hole=0.4
        )])
        
        fig_pie.update_layout(
            title=f"Average Sleep Composition ({selected_range})",
            height=400
        )
        
        st.plotly_chart(fig_pie, use_container_width=True)
    
    # Sleep stage targets reference
    st.markdown("""
    **Sleep Stage Targets:**
    | Stage | Target | Purpose |
    |-------|--------|---------|
    | Deep | 13-23% | Physical recovery, muscle repair, immune function |
    | REM | 20-25% | Mental recovery, memory consolidation, learning |
    | Light | 50-60% | Transition stage, light restoration |
    | Awake | <5% | Brief awakenings are normal |
    """)

    # ============================================
    # STRESS LEVELS (if available)
    # ============================================
    if stress_data:
        stress_df = pd.DataFrame(stress_data)
        stress_df['date'] = pd.to_datetime(stress_df['date'])
        stress_df = stress_df.sort_values('date')
        
        # Filter to same range and only rows with data
        stress_filtered = stress_df.tail(n_days)
        stress_filtered = stress_filtered[stress_filtered['avg_stress'].notna()]
        
        if not stress_filtered.empty:
            st.markdown("---")
            st.subheader("😰 Stress Levels")
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                fig_stress = go.Figure()
                
                # Color by stress level
                colors_stress = ['#2ecc71' if s <= 25 else '#f39c12' if s <= 50 else '#e74c3c' 
                                 for s in stress_filtered['avg_stress']]
                
                fig_stress.add_trace(go.Scatter(
                    x=stress_filtered['date'],
                    y=stress_filtered['avg_stress'],
                    mode='lines+markers',
                    name='Avg Stress',
                    line=dict(color='#3498db', width=2),
                    marker=dict(size=6, color=colors_stress)
                ))
                
                # Add max stress as area
                fig_stress.add_trace(go.Scatter(
                    x=stress_filtered['date'],
                    y=stress_filtered['max_stress'],
                    mode='lines',
                    name='Max Stress',
                    line=dict(color='#e74c3c', width=1, dash='dot'),
                    fill='tonexty',
                    fillcolor='rgba(231, 76, 60, 0.1)'
                ))
                
                # Add threshold lines
                fig_stress.add_hline(y=25, line_dash="dash", line_color="green", 
                                     annotation_text="Low", annotation_position="left")
                fig_stress.add_hline(y=50, line_dash="dash", line_color="orange",
                                     annotation_text="Medium", annotation_position="left")
                
                fig_stress.update_layout(
                    title="Daily Stress Trend",
                    xaxis_title="Date",
                    yaxis_title="Stress Score",
                    yaxis_range=[0, 100],
                    height=350,
                    legend=dict(orientation="h", yanchor="bottom", y=1.02)
                )
                
                st.plotly_chart(fig_stress, use_container_width=True)
            
            with col2:
                # Stress summary
                avg_stress = stress_filtered['avg_stress'].mean()
                max_stress = stress_filtered['max_stress'].max()
                low_stress_days = len(stress_filtered[stress_filtered['avg_stress'] <= 25])
                
                stress_status = "🟢 Low" if avg_stress <= 25 else "🟡 Moderate" if avg_stress <= 50 else "🔴 High"
                
                st.markdown(f"""
                ### Stress Summary
                
                **Status:** {stress_status}
                
                **Avg Stress:** {avg_stress:.0f}/100
                
                **Peak Stress:** {max_stress:.0f}/100
                
                **Low Stress Days:** {low_stress_days}/{len(stress_filtered)}
                
                ---
                
                **Stress Guide:**
                - 0-25: Rest/Low activity
                - 26-50: Normal/Moderate
                - 51-75: High stress
                - 76-100: Very high stress
                """)

    # ============================================
    # WEEKLY RECOVERY SUMMARY
    # ============================================
    st.markdown("---")
    st.subheader("📅 Weekly Recovery Summary")
    
    # Group by week
    sleep_df['week'] = sleep_df['date'].dt.strftime('%Y-W%W')
    weekly_sleep = sleep_df.groupby('week').agg({
        'sleep_hours': 'mean',
        'deep_pct': 'mean',
        'rem_pct': 'mean',
        'date': 'count'
    }).reset_index()
    weekly_sleep.columns = ['Week', 'Avg Hours', 'Avg Deep %', 'Avg REM %', 'Nights']
    
    # Get last 8 weeks
    weekly_display = weekly_sleep.tail(8)
    
    # Create status indicators
    def get_status(row):
        score = 0
        if row['Avg Hours'] >= SLEEP_TARGET: score += 1
        if row['Avg Deep %'] >= DEEP_SLEEP_TARGET: score += 1
        if row['Avg REM %'] >= REM_TARGET: score += 1
        return "🟢" if score >= 2 else "🟡" if score >= 1 else "🔴"
    
    weekly_display['Status'] = weekly_display.apply(get_status, axis=1)
    
    # Display as markdown table
    st.markdown("| Week | Nights | Avg Hours | Deep % | REM % | Status |")
    st.markdown("|------|--------|-----------|--------|-------|--------|")
    for _, row in weekly_display.iterrows():
        hours_color = "**" if row['Avg Hours'] >= SLEEP_TARGET else ""
        deep_color = "**" if row['Avg Deep %'] >= DEEP_SLEEP_TARGET else ""
        rem_color = "**" if row['Avg REM %'] >= REM_TARGET else ""
        st.markdown(
            f"| {row['Week']} | {row['Nights']} | {hours_color}{row['Avg Hours']:.1f}h{hours_color} | "
            f"{deep_color}{row['Avg Deep %']:.0f}%{deep_color} | {rem_color}{row['Avg REM %']:.0f}%{rem_color} | {row['Status']} |"
        )

    # ============================================
    # RECOVERY RECOMMENDATIONS
    # ============================================
    st.markdown("---")
    st.subheader("💡 Recovery Recommendations")
    
    recommendations = []
    
    # Sleep duration
    if avg_sleep < 6.5:
        recommendations.append("🔴 **Critical: Sleep below 6.5h average** - Prioritize sleep over training intensity")
    elif avg_sleep < SLEEP_TARGET:
        recommendations.append(f"🟡 **Sleep averaging {avg_sleep:.1f}h** - Try to get to bed 30 min earlier")
    
    # Deep sleep
    if avg_deep < 10:
        recommendations.append("🔴 **Deep sleep very low** - Avoid alcohol, keep bedroom cool (65-68°F)")
    elif avg_deep < DEEP_SLEEP_TARGET:
        recommendations.append(f"🟡 **Deep sleep at {avg_deep:.0f}%** - Consider earlier dinners, reduce screen time")
    
    # REM sleep
    if avg_rem < 15:
        recommendations.append("🟡 **REM sleep low** - Avoid alarm clock when possible, complete sleep cycles")
    
    # Stress (if available)
    if stress_data:
        stress_filtered_check = pd.DataFrame(stress_data).tail(7)
        stress_filtered_check = stress_filtered_check[stress_filtered_check['avg_stress'].notna()]
        if not stress_filtered_check.empty:
            avg_stress_7d = stress_filtered_check['avg_stress'].mean()
            if avg_stress_7d > 50:
                recommendations.append(f"🔴 **Stress elevated ({avg_stress_7d:.0f}/100)** - Consider rest day, breathing exercises")
            elif avg_stress_7d > 35:
                recommendations.append(f"🟡 **Moderate stress ({avg_stress_7d:.0f}/100)** - Monitor recovery, keep training easy")
    
    if recommendations:
        for rec in recommendations:
            st.markdown(f"- {rec}")
    else:
        st.success("✅ All recovery metrics look good! You're well-rested and ready to train.")

    # ============================================
    # DEBUG EXPANDER
    # ============================================
    with st.expander("🔍 Debug: Raw Data"):
        st.markdown("**Recent Sleep Data:**")
        st.markdown("| Date | Hours | Deep % | REM % | Light % |")
        st.markdown("|------|-------|--------|-------|---------|")
        for _, row in sleep_df.tail(7).iterrows():
            st.markdown(f"| {row['date'].strftime('%Y-%m-%d')} | {row['sleep_hours']:.1f}h | {row['deep_pct']:.0f}% | {row['rem_pct']:.0f}% | {row['light_pct']:.0f}% |")
        
        if stress_data:
            st.markdown("\n**Recent Stress Data:**")
            stress_recent = pd.DataFrame(stress_data).tail(7)
            st.markdown("| Date | Avg | Max |")
            st.markdown("|------|-----|-----|")
            for _, row in stress_recent.iterrows():
                avg = row.get('avg_stress', 'N/A')
                max_s = row.get('max_stress', 'N/A')
                st.markdown(f"| {row['date']} | {avg} | {max_s} |")

except Exception as e:
    st.error(f"Error loading data: {e}")
    st.info("Try running `python scripts/incremental-sync.py --days 7` to refresh data cache.")
    
    with st.expander("Error details"):
        import traceback
        st.code(traceback.format_exc())
