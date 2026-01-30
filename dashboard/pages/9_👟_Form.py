"""
Form & Cadence Dashboard

Track running form metrics: cadence, stride length, and form progress.
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

from utils.data_loader import activities_to_dataframe, load_activities, get_cadence_pace_analysis

# Page config
st.set_page_config(page_title="Form Analysis", page_icon="👟", layout="wide")

st.title("👟 Form & Cadence Analysis")
st.markdown("Track running form metrics and improvement over time")

# Target ranges (based on your running data)
# Note: 180 spm is "elite ideal" but 155-165 is realistic for many recreational runners
CADENCE_TARGET_MIN = 155  # spm - steps per minute (your realistic range)
CADENCE_TARGET_MAX = 170  # Aspirational upper target
STRIDE_EFFICIENCY_THRESHOLD = 1.0  # meters - roughly bodyweight dependent

# Info box about arm swing focus
with st.expander("🎯 Current Form Focus: Arm Swing", expanded=False):
    st.markdown("""
    **Issue Identified (Jan 2026):** Static 90° arm hold with limited anterior-posterior swing
    
    **Correction Plan:**
    - Pre-run drill: 2min standing arm swing before EVERY run
    - During-run: Exaggerated arm swing bursts (3-4 x 30s on easy runs)
    - Post-run: Shoulder exercises (blade squeezes, band pull-aparts)
    
    **Gait Video Schedule:** Weeks 1, 5, 9, 13, 17
    
    **Expected Benefits:** Reduced tension, improved cadence, better breathing
    
    Full guide: `resources/arm-swing-drills-guide.md`
    """)

def extract_lap_metrics(activities):
    """Extract cadence and stride data from activity laps"""
    lap_data = []
    
    for act in activities:
        if act.get('type') != 'running':
            continue
            
        splits = act.get('splits', {})
        laps = splits.get('lapDTOs', []) if isinstance(splits, dict) else []
        
        act_date = act.get('date', '')
        act_name = act.get('name', 'Unknown')
        act_distance = act.get('distance_km', 0)
        
        for lap in laps:
            cadence = lap.get('averageRunCadence')
            stride = lap.get('strideLength')
            pace = lap.get('averageSpeed', 0)  # m/s
            hr = lap.get('averageHR')
            distance = lap.get('distance', 0) / 1000  # Convert to km
            
            if cadence and stride and distance >= 0.5:  # Only include substantial laps
                lap_data.append({
                    'date': act_date,
                    'activity_name': act_name,
                    'activity_distance': act_distance,
                    'lap_index': lap.get('lapIndex', 0),
                    'cadence': cadence,  # Already in steps per minute
                    'stride_m': stride / 100,  # Convert cm to m
                    'pace_ms': pace,
                    'pace_min_km': (1000 / pace / 60) if pace > 0 else 0,
                    'avg_hr': hr,
                    'distance_km': distance
                })
    
    return pd.DataFrame(lap_data)

def get_activity_averages(activities):
    """Get activity-level cadence and stride averages"""
    act_data = []
    
    for act in activities:
        if act.get('type') != 'running':
            continue
            
        splits = act.get('splits', {})
        laps = splits.get('lapDTOs', []) if isinstance(splits, dict) else []
        
        if not laps:
            continue
        
        # Calculate weighted averages
        total_distance = 0
        weighted_cadence = 0
        weighted_stride = 0
        
        for lap in laps:
            dist = lap.get('distance', 0)
            cadence = lap.get('averageRunCadence', 0)
            stride = lap.get('strideLength', 0)
            
            if cadence and stride:
                weighted_cadence += cadence * dist
                weighted_stride += stride * dist
                total_distance += dist
        
        if total_distance > 0:
            act_data.append({
                'date': act.get('date', ''),
                'name': act.get('name', 'Unknown'),
                'distance_km': act.get('distance_km', 0),
                'avg_cadence': weighted_cadence / total_distance,  # Already in steps per minute
                'avg_stride_m': (weighted_stride / total_distance) / 100,  # Meters
                'avg_hr': act.get('avg_hr', 0),
                'avg_pace': act.get('avg_pace_min_km', '')
            })
    
    return pd.DataFrame(act_data)

try:
    activities = load_activities()
    df = activities_to_dataframe()
    
    if not activities or df.empty:
        st.error("No running activities found. Run `python scripts/sync-garmin.py` to sync data.")
        st.stop()

    # Extract metrics
    lap_df = extract_lap_metrics(activities)
    act_df = get_activity_averages(activities)
    
    if act_df.empty:
        st.warning("No cadence/stride data found in activities. Make sure your watch records these metrics.")
        st.stop()
    
    # Parse dates
    act_df['date'] = pd.to_datetime(act_df['date'])
    act_df = act_df.sort_values('date')
    
    if not lap_df.empty:
        lap_df['date'] = pd.to_datetime(lap_df['date'])
        lap_df = lap_df.sort_values('date')

    # Sidebar filters
    st.sidebar.header("Filters")
    range_options = {
        "Last 10 Runs": 10,
        "Last 20 Runs": 20,
        "Last 50 Runs": 50,
        "All Time": len(act_df)
    }
    selected_range = st.sidebar.selectbox("View", list(range_options.keys()), index=1)
    n_runs = range_options[selected_range]
    
    act_filtered = act_df.tail(n_runs)

    # ============================================
    # CURRENT FORM SUMMARY
    # ============================================
    st.subheader("📊 Current Form Metrics")
    
    # Calculate recent averages (last 5 runs)
    recent = act_df.tail(5)
    avg_cadence = recent['avg_cadence'].mean()
    avg_stride = recent['avg_stride_m'].mean()
    
    # Compare to older runs (5-10 runs ago)
    if len(act_df) >= 10:
        older = act_df.tail(10).head(5)
        old_cadence = older['avg_cadence'].mean()
        old_stride = older['avg_stride_m'].mean()
        cadence_delta = avg_cadence - old_cadence
        stride_delta = avg_stride - old_stride
    else:
        cadence_delta = 0
        stride_delta = 0
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        cadence_status = "🟢" if CADENCE_TARGET_MIN <= avg_cadence <= CADENCE_TARGET_MAX else "🟡"
        st.metric(
            "Avg Cadence (5 runs)",
            f"{avg_cadence:.0f} spm",
            delta=f"{cadence_delta:+.1f} spm" if cadence_delta != 0 else None,
            help=f"Target: {CADENCE_TARGET_MIN}-{CADENCE_TARGET_MAX} spm. Higher cadence often = better form."
        )
    
    with col2:
        st.metric(
            "Avg Stride Length",
            f"{avg_stride:.2f} m",
            delta=f"{stride_delta:+.2f} m" if stride_delta != 0 else None,
            help="Stride length naturally varies with pace. Focus on cadence for form."
        )
    
    with col3:
        # Efficiency: cadence × stride = speed
        speed_factor = avg_cadence * avg_stride / 60  # m/s estimate
        pace_estimate = 1000 / speed_factor / 60 if speed_factor > 0 else 0
        st.metric(
            "Form Efficiency",
            f"{speed_factor:.2f} m/s",
            help="Cadence × Stride ÷ 60. Higher = more efficient."
        )
    
    with col4:
        # Cadence consistency (coefficient of variation)
        cv = (recent['avg_cadence'].std() / recent['avg_cadence'].mean() * 100) if avg_cadence > 0 else 0
        consistency_status = "🟢" if cv < 3 else "🟡" if cv < 5 else "🔴"
        st.metric(
            "Cadence Consistency",
            f"{cv:.1f}% CV",
            help="Coefficient of variation. Lower = more consistent form."
        )

    # ============================================
    # CADENCE TREND
    # ============================================
    st.markdown("---")
    st.subheader("📈 Cadence Trend")
    
    fig_cadence = go.Figure()
    
    # Cadence by activity
    colors = ['#2ecc71' if CADENCE_TARGET_MIN <= c <= CADENCE_TARGET_MAX else '#f39c12' 
              for c in act_filtered['avg_cadence']]
    
    fig_cadence.add_trace(go.Scatter(
        x=act_filtered['date'],
        y=act_filtered['avg_cadence'],
        mode='markers+lines',
        name='Cadence',
        line=dict(color='#3498db', width=2),
        marker=dict(size=10, color=colors, line=dict(width=1, color='white')),
        hovertemplate='%{x|%b %d}<br>%{y:.0f} spm<extra></extra>'
    ))
    
    # Add target zone
    fig_cadence.add_hrect(
        y0=CADENCE_TARGET_MIN, y1=CADENCE_TARGET_MAX,
        fillcolor="rgba(46, 204, 113, 0.1)",
        line_width=0,
        annotation_text="Target Zone",
        annotation_position="top right"
    )
    
    # Add trend line
    if len(act_filtered) >= 5:
        z = pd.Series(range(len(act_filtered)))
        trend = act_filtered['avg_cadence'].rolling(5, min_periods=3).mean()
        fig_cadence.add_trace(go.Scatter(
            x=act_filtered['date'],
            y=trend,
            mode='lines',
            name='5-run Trend',
            line=dict(color='#e74c3c', width=2, dash='dash')
        ))
    
    fig_cadence.update_layout(
        xaxis_title="Date",
        yaxis_title="Cadence (steps/min)",
        yaxis_range=[140, 190],
        height=400,
        legend=dict(orientation="h", yanchor="bottom", y=1.02)
    )
    
    st.plotly_chart(fig_cadence, use_container_width=True)

    # ============================================
    # CADENCE VS PACE RELATIONSHIP (NEW)
    # ============================================
    st.markdown("---")
    st.subheader("🔄 Cadence-Pace Relationship")
    
    # Load pre-calculated analysis
    cadence_analysis = get_cadence_pace_analysis()
    
    if cadence_analysis and cadence_analysis.get('lap_data'):
        lap_data = cadence_analysis['lap_data']
        regression = cadence_analysis.get('regression', {})
        bracket_stats = cadence_analysis.get('bracket_stats', {})
        
        # Display key metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            correlation = regression.get('correlation', 0)
            corr_status = "🟢" if abs(correlation) > 0.7 else "🟡"
            st.metric(
                "Correlation",
                f"{correlation:.2f}",
                help="How strongly cadence relates to pace. -0.7 to -1.0 is normal (cadence increases as you run faster)"
            )
        
        with col2:
            slope = regression.get('slope', 0)
            st.metric(
                "Cadence Change",
                f"{slope:.1f} spm/min",
                help="How much your cadence changes per 1 min/km pace change"
            )
        
        with col3:
            r_squared = regression.get('r_squared', 0)
            st.metric(
                "R² (Consistency)",
                f"{r_squared:.2f}",
                help="How consistent your cadence-pace relationship is. Higher = more predictable form."
            )
        
        # Main scatter plot with trendline
        import pandas as pd
        lap_df_analysis = pd.DataFrame(lap_data)
        
        fig_pace_cadence = go.Figure()
        
        # Scatter plot of all laps
        fig_pace_cadence.add_trace(go.Scatter(
            x=lap_df_analysis['pace_min_km'],
            y=lap_df_analysis['cadence'],
            mode='markers',
            name='Laps',
            marker=dict(
                size=8,
                color=lap_df_analysis['pace_min_km'],
                colorscale='RdYlGn_r',
                opacity=0.6,
                showscale=True,
                colorbar=dict(title="Pace (min/km)")
            ),
            hovertemplate='Pace: %{x:.1f} min/km<br>Cadence: %{y:.0f} spm<extra></extra>'
        ))
        
        # Trendline
        slope = regression.get('slope', 0)
        intercept = regression.get('intercept', 0)
        x_range = [lap_df_analysis['pace_min_km'].min(), lap_df_analysis['pace_min_km'].max()]
        y_trend = [slope * x + intercept for x in x_range]
        
        fig_pace_cadence.add_trace(go.Scatter(
            x=x_range,
            y=y_trend,
            mode='lines',
            name=f'Trend: {slope:.1f}×pace + {intercept:.0f}',
            line=dict(color='#e74c3c', width=3, dash='solid')
        ))
        
        # Target zone overlay (optimal cadence ranges by pace)
        # Green zone: recommended cadence for each pace
        target_zones = [
            {'pace_min': 4.5, 'pace_max': 5.0, 'cad_min': 170, 'cad_max': 185, 'label': 'Fast'},
            {'pace_min': 5.0, 'pace_max': 5.5, 'cad_min': 165, 'cad_max': 180, 'label': 'Tempo'},
            {'pace_min': 5.5, 'pace_max': 6.0, 'cad_min': 162, 'cad_max': 175, 'label': 'Moderate'},
            {'pace_min': 6.0, 'pace_max': 6.5, 'cad_min': 158, 'cad_max': 170, 'label': 'Easy'},
            {'pace_min': 6.5, 'pace_max': 7.0, 'cad_min': 155, 'cad_max': 168, 'label': 'Recovery'},
            {'pace_min': 7.0, 'pace_max': 8.0, 'cad_min': 152, 'cad_max': 165, 'label': 'Very Easy'},
        ]
        
        for zone in target_zones:
            fig_pace_cadence.add_shape(
                type="rect",
                x0=zone['pace_min'], x1=zone['pace_max'],
                y0=zone['cad_min'], y1=zone['cad_max'],
                fillcolor="rgba(46, 204, 113, 0.1)",
                line=dict(color="rgba(46, 204, 113, 0.3)", width=1),
            )
        
        fig_pace_cadence.update_layout(
            title="Cadence vs Pace (with optimal zones)",
            xaxis_title="Pace (min/km)",
            yaxis_title="Cadence (spm)",
            xaxis=dict(autorange='reversed'),  # Faster pace on right
            height=450,
            legend=dict(orientation="h", yanchor="bottom", y=1.02)
        )
        
        st.plotly_chart(fig_pace_cadence, use_container_width=True)
        
        # Pace bracket comparison table
        st.markdown("#### 📊 Cadence by Pace Bracket")
        
        # Define bracket labels
        bracket_labels = {
            '1_fast': ('⚡ Fast (<5:00)', '#27ae60'),
            '2_tempo': ('🔥 Tempo (5:00-5:30)', '#2ecc71'),
            '3_moderate': ('🏃 Moderate (5:30-6:00)', '#f1c40f'),
            '4_easy': ('🚶 Easy (6:00-6:30)', '#e67e22'),
            '5_recovery': ('💤 Recovery (6:30-7:00)', '#e74c3c'),
            '6_very_easy': ('🐢 Very Easy (>7:00)', '#c0392b')
        }
        
        # Target cadence by bracket
        target_cadence = {
            '1_fast': (170, 185),
            '2_tempo': (165, 180),
            '3_moderate': (162, 175),
            '4_easy': (158, 170),
            '5_recovery': (155, 168),
            '6_very_easy': (152, 165)
        }
        
        # Create comparison table
        cols = st.columns(len(bracket_stats))
        for i, (bracket, stats) in enumerate(sorted(bracket_stats.items())):
            if bracket in bracket_labels:
                label, color = bracket_labels[bracket]
                target = target_cadence.get(bracket, (150, 175))
                actual = stats['avg_cadence']
                
                # Determine status
                if target[0] <= actual <= target[1]:
                    status = "✅"
                elif actual < target[0]:
                    status = "⚠️ Low"
                else:
                    status = "🟡 High"
                
                with cols[i]:
                    st.markdown(f"**{label.split(' ')[0]}**")
                    st.metric(
                        label.split(' ', 1)[1] if len(label.split(' ', 1)) > 1 else bracket,
                        f"{actual:.0f} spm",
                        delta=f"{status}" if status != "✅" else None,
                        delta_color="off"
                    )
                    st.caption(f"Target: {target[0]}-{target[1]} ({stats['lap_count']} laps)")
        
        # Insight box
        slope = regression.get('slope', 0)
        if abs(slope) > 10:
            insight = "⚠️ **High cadence variation** - Your cadence changes significantly with pace. Focus on maintaining higher cadence at easy paces."
        elif abs(slope) < 5:
            insight = "✅ **Consistent cadence** - Your cadence stays relatively stable across paces. Good form efficiency!"
        else:
            insight = "🟡 **Normal variation** - Your cadence-pace relationship is typical. Room for improvement at easy paces."
        
        st.info(insight)
        
    else:
        st.warning("Cadence-pace analysis not available. Run `python scripts/incremental-sync.py` to calculate.")
    
    # ============================================
    # CADENCE vs STRIDE SCATTER
    # ============================================
    st.markdown("---")
    st.subheader("🎯 Cadence vs Stride")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Scatter plot: cadence vs stride (colored by HR if available)
        if not lap_df.empty:
            lap_recent = lap_df.tail(200)  # Last 200 laps
            
            fig_scatter = px.scatter(
                lap_recent,
                x='cadence',
                y='stride_m',
                color='pace_min_km',
                size='distance_km',
                hover_data=['activity_name', 'lap_index'],
                color_continuous_scale='RdYlGn_r',  # Red = slow, Green = fast
                labels={
                    'cadence': 'Cadence (spm)',
                    'stride_m': 'Stride Length (m)',
                    'pace_min_km': 'Pace (min/km)'
                }
            )
            
            fig_scatter.update_layout(
                title="Cadence vs Stride (colored by pace)",
                height=400
            )
            
            st.plotly_chart(fig_scatter, use_container_width=True)
        else:
            st.info("Lap-level data not available")
    
    with col2:
        # Cadence distribution histogram
        fig_hist = go.Figure()
        
        fig_hist.add_trace(go.Histogram(
            x=act_filtered['avg_cadence'],
            nbinsx=20,
            marker_color='#3498db',
            name='Cadence Distribution'
        ))
        
        # Add target zone
        fig_hist.add_vrect(
            x0=CADENCE_TARGET_MIN, x1=CADENCE_TARGET_MAX,
            fillcolor="rgba(46, 204, 113, 0.2)",
            line_width=0
        )
        
        fig_hist.update_layout(
            title="Cadence Distribution",
            xaxis_title="Cadence (spm)",
            yaxis_title="Number of Runs",
            height=400
        )
        
        st.plotly_chart(fig_hist, use_container_width=True)

    # ============================================
    # STRIDE LENGTH ANALYSIS
    # ============================================
    st.markdown("---")
    st.subheader("📏 Stride Length Trend")
    
    fig_stride = go.Figure()
    
    # Primary: stride length
    fig_stride.add_trace(go.Scatter(
        x=act_filtered['date'],
        y=act_filtered['avg_stride_m'],
        mode='markers+lines',
        name='Stride Length',
        line=dict(color='#9b59b6', width=2),
        marker=dict(size=8),
        yaxis='y'
    ))
    
    # Secondary: distance (to show context)
    fig_stride.add_trace(go.Bar(
        x=act_filtered['date'],
        y=act_filtered['distance_km'],
        name='Distance',
        marker_color='rgba(52, 152, 219, 0.3)',
        yaxis='y2'
    ))
    
    fig_stride.update_layout(
        xaxis_title="Date",
        yaxis=dict(
            title="Stride Length (m)",
            side='left',
            range=[0.8, 1.3]
        ),
        yaxis2=dict(
            title="Distance (km)",
            side='right',
            overlaying='y',
            range=[0, 25]
        ),
        height=400,
        legend=dict(orientation="h", yanchor="bottom", y=1.02)
    )
    
    st.plotly_chart(fig_stride, use_container_width=True)

    # ============================================
    # GAIT VIDEO TRACKER (Manual)
    # ============================================
    st.markdown("---")
    st.subheader("🎥 Gait Video Progress Tracker")
    
    st.markdown("""
    Track your form improvement with scheduled gait videos:
    
    | Week | Date | Status | Notes |
    |------|------|--------|-------|
    | 1 | Jan 10, 2026 | 🟡 Scheduled | Baseline recording |
    | 5 | Feb 7, 2026 | ⬜ Upcoming | Early progress check |
    | 9 | Mar 7, 2026 | ⬜ Upcoming | Mid-base assessment |
    | 13 | Apr 4, 2026 | ⬜ Upcoming | Pre-10K taper |
    | 17 | May 2, 2026 | ⬜ Upcoming | Pre-HM specific |
    
    **How to record:** Film from behind and side during easy running. Save to `media/gait-analysis/`.
    
    **What to look for:**
    - Arm swing: Front-back motion, relaxed shoulders
    - Foot strike: Midfoot landing under hips
    - Hip drop: Minimal lateral movement
    - Cadence: Quick, light steps
    """)

    # ============================================
    # FORM RECOMMENDATIONS
    # ============================================
    st.markdown("---")
    st.subheader("💡 Form Recommendations")
    
    recommendations = []
    
    if avg_cadence < CADENCE_TARGET_MIN:
        deficit = CADENCE_TARGET_MIN - avg_cadence
        recommendations.append(f"🟡 **Cadence below target ({avg_cadence:.0f} vs {CADENCE_TARGET_MIN} spm)** - "
                               f"Try adding {deficit:.0f} spm with metronome drills or shorter, quicker steps")
    elif avg_cadence > CADENCE_TARGET_MAX + 5:
        recommendations.append(f"🟡 **Cadence very high ({avg_cadence:.0f} spm)** - "
                               "This is fine, but check you're not overstriding. Focus on hip drive.")
    
    if cv > 5:
        recommendations.append(f"🟡 **Cadence inconsistent (CV: {cv:.1f}%)** - "
                               "Work on maintaining rhythm. Consider running with music at target cadence.")
    
    # Check for declining trend
    if len(act_df) >= 10:
        recent_avg = act_df.tail(5)['avg_cadence'].mean()
        older_avg = act_df.tail(10).head(5)['avg_cadence'].mean()
        if recent_avg < older_avg - 3:
            recommendations.append("🟡 **Cadence declining** - You may be fatigued. Check recovery metrics.")
    
    if recommendations:
        for rec in recommendations:
            st.markdown(f"- {rec}")
    else:
        st.success("✅ Form metrics look good! Maintain current cadence and focus on arm swing drills.")

    # ============================================
    # DEBUG EXPANDER
    # ============================================
    with st.expander("🔍 Debug: Recent Activity Metrics"):
        st.markdown("**Last 10 Activities:**")
        st.markdown("| Date | Activity | Dist | Cadence | Stride |")
        st.markdown("|------|----------|------|---------|--------|")
        for _, row in act_df.tail(10).iterrows():
            st.markdown(
                f"| {row['date'].strftime('%Y-%m-%d')} | {row['name'][:25]} | "
                f"{row['distance_km']:.1f}km | {row['avg_cadence']:.0f} | {row['avg_stride_m']:.2f}m |"
            )

except Exception as e:
    st.error(f"Error loading data: {e}")
    st.info("Try running `python scripts/sync-garmin.py` to refresh data cache.")
    
    with st.expander("Error details"):
        import traceback
        st.code(traceback.format_exc())
