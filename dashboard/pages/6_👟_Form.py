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

st.title("Form & Cadence Analysis")
st.markdown("Track running form metrics and improvement over time")

# Target ranges (based on your running data)
# Note: 180 spm is "elite ideal" but 155-165 is realistic for many recreational runners
CADENCE_TARGET_MIN = 155  # spm - steps per minute (your realistic range)
CADENCE_TARGET_MAX = 170  # Aspirational upper target
STRIDE_EFFICIENCY_THRESHOLD = 1.0  # meters - roughly bodyweight dependent

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
        st.error("No running activities found. Run `python scripts/incremental-sync.py --days 90` to sync data.")
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
    st.subheader("Current Form Metrics")
    
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
    
    # Cadence consistency (coefficient of variation) - used in recommendations below
    cv = (recent['avg_cadence'].std() / recent['avg_cadence'].mean() * 100) if avg_cadence > 0 else 0

    col1, col2, col3 = st.columns(3)
    
    with col1:
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
        st.metric(
            "Cadence Consistency",
            f"{cv:.1f}% CV",
            help="Coefficient of variation. Lower = more consistent form across runs."
        )

    # ============================================
    # CADENCE TREND
    # ============================================
    st.markdown("---")
    st.subheader("Cadence Trend")
    
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
    # CADENCE BY PACE BRACKET (Simplified & Actionable)
    # ============================================
    st.markdown("---")
    st.subheader("Cadence by Pace Bracket")
    st.caption("Are you hitting target cadence at each pace? Compares last 5 vs previous 5 laps per bracket.")
    
    # Define pace brackets and targets
    pace_brackets = {
        'Fast': {'min': 0, 'max': 6.0, 'target': (162, 175)},
        'Moderate': {'min': 6.0, 'max': 6.5, 'target': (158, 168)},
        'Easy': {'min': 6.5, 'max': 7.0, 'target': (155, 165)},
        'Recovery': {'min': 7.0, 'max': 10.0, 'target': (150, 160)},
    }
    
    # Extract lap data with dates for trend analysis
    lap_data_with_dates = []
    for act in activities:
        if act.get('type') != 'running':
            continue
        
        act_date = act.get('date', '')[:10]
        splits = act.get('splits', {})
        laps = splits.get('lapDTOs', []) if isinstance(splits, dict) else []
        
        for lap in laps:
            cadence = lap.get('averageRunCadence')
            pace_ms = lap.get('averageSpeed', 0)
            distance = lap.get('distance', 0)
            
            if cadence and pace_ms > 0 and distance >= 500:
                pace_min_km = (1000 / pace_ms) / 60
                lap_data_with_dates.append({
                    'date': act_date,
                    'cadence': cadence,
                    'pace_min_km': pace_min_km
                })
    
    if lap_data_with_dates:
        # Sort by date descending
        lap_data_with_dates.sort(key=lambda x: x['date'], reverse=True)
        
        # Analyze each bracket
        bracket_analysis = {}
        
        for bracket_name, bracket_config in pace_brackets.items():
            # Filter laps in this bracket
            bracket_laps = [
                lap for lap in lap_data_with_dates
                if bracket_config['min'] <= lap['pace_min_km'] < bracket_config['max']
            ]
            
            if len(bracket_laps) >= 3:
                # Recent 5 laps vs previous 5 laps
                recent_laps = bracket_laps[:5]
                previous_laps = bracket_laps[5:10] if len(bracket_laps) >= 10 else bracket_laps[5:]
                
                recent_avg = sum(l['cadence'] for l in recent_laps) / len(recent_laps)
                previous_avg = sum(l['cadence'] for l in previous_laps) / len(previous_laps) if previous_laps else recent_avg
                
                trend = recent_avg - previous_avg
                target_min, target_max = bracket_config['target']
                
                # Status
                if target_min <= recent_avg <= target_max:
                    status = '✅ Good'
                elif recent_avg < target_min:
                    status = '⚠️ Low'
                else:
                    status = '🔵 High'
                
                # Trend indicator
                if trend > 2:
                    trend_icon = '📈'
                    trend_text = f'+{trend:.0f}'
                elif trend < -2:
                    trend_icon = '📉'
                    trend_text = f'{trend:.0f}'
                else:
                    trend_icon = '➡️'
                    trend_text = '~'
                
                bracket_analysis[bracket_name] = {
                    'recent_avg': recent_avg,
                    'previous_avg': previous_avg,
                    'trend': trend,
                    'trend_icon': trend_icon,
                    'trend_text': trend_text,
                    'status': status,
                    'target': bracket_config['target'],
                    'lap_count': len(recent_laps),
                    'total_laps': len(bracket_laps)
                }
        
        # Display as table
        if bracket_analysis:
            st.markdown("| Pace | Recent (5) | Previous (5) | Trend | Target | Status |")
            st.markdown("|------|------------|--------------|-------|--------|--------|")
            
            for bracket_name, data in bracket_analysis.items():
                prev_str = f"{data['previous_avg']:.0f}" if data['previous_avg'] != data['recent_avg'] else "—"
                st.markdown(
                    f"| **{bracket_name}** | "
                    f"{data['recent_avg']:.0f} spm | "
                    f"{prev_str} spm | "
                    f"{data['trend_text']} | "
                    f"{data['target'][0]}-{data['target'][1]} | "
                    f"{data['status']} |"
                )
            
            # Summary insight
            improving_brackets = [name for name, data in bracket_analysis.items() if data['trend'] > 2]
            declining_brackets = [name for name, data in bracket_analysis.items() if data['trend'] < -2]
            low_brackets = [name for name, data in bracket_analysis.items() if '⚠️' in data['status']]
            
            st.markdown("")
            if improving_brackets:
                st.success(f"**Improving:** {', '.join(improving_brackets)} -- cadence trending up")
            if declining_brackets:
                st.warning(f"**Watch:** {', '.join(declining_brackets)} -- cadence dropping")
            if low_brackets and not improving_brackets:
                st.info(f"**Tip:** Focus on maintaining {low_brackets[0]} cadence above {pace_brackets[low_brackets[0]]['target'][0]} spm")
            elif not improving_brackets and not declining_brackets and not low_brackets:
                st.success("Cadence looking stable across all pace brackets")
            
            # Show how many laps analyzed
            total_laps = sum(data['total_laps'] for data in bracket_analysis.values())
            st.caption(f"Based on {total_laps} laps from recent runs")
        else:
            st.info("Not enough lap data yet. Need at least 3 laps per pace bracket.")
    else:
        st.warning("No lap-level cadence data available.")
    
    # ============================================
    # CADENCE PROGRESS TABLE (Pace-Normalized)
    # ============================================
    st.markdown("---")
    st.subheader("Cadence Progress (Pace-Normalized)")
    st.caption("Compare cadence at similar paces to track real improvement vs just running faster")
    
    # Build activity data with proper metrics
    progress_data = []
    for act in activities:
        if act.get('type') != 'running':
            continue
        
        date = act.get('date', '')[:10]
        if date < '2026-01':  # Focus on recent season
            continue
            
        name = act.get('name', 'Unknown')
        dist_km = act.get('distance_km', 0)
        dur_sec = act.get('duration_seconds', 0)
        cadence = act.get('avg_cadence', 0)
        
        if not cadence or not dur_sec or dist_km < 3:
            continue
        
        # Calculate pace
        pace_sec_km = dur_sec / dist_km if dist_km > 0 else 0
        pace_min = int(pace_sec_km // 60)
        pace_s = int(pace_sec_km % 60)
        pace_str = f"{pace_min}:{pace_s:02d}"
        
        # Get stride from splits
        splits = act.get('splits', {}).get('lapDTOs', []) if isinstance(act.get('splits'), dict) else []
        if splits:
            strides = [s.get('strideLength', 0) for s in splits if s.get('strideLength')]
            stride_cm = sum(strides) / len(strides) if strides else 0
        else:
            stride_cm = 0
        
        progress_data.append({
            'date': date,
            'name': name[:30],
            'distance_km': dist_km,
            'pace_sec': pace_sec_km,
            'pace': pace_str,
            'cadence': cadence,
            'stride_cm': stride_cm
        })
    
    if progress_data:
        progress_df = pd.DataFrame(progress_data).sort_values('date', ascending=False)
        
        # Calculate pace bracket for each run
        def get_pace_bracket(pace_sec):
            pace_min = pace_sec / 60
            if pace_min < 6.0:
                return "Fast (<6:00)"
            elif pace_min < 6.5:
                return "Moderate (6:00-6:30)"
            elif pace_min < 7.0:
                return "Easy (6:30-7:00)"
            else:
                return "Recovery (>7:00)"
        
        progress_df['pace_bracket'] = progress_df['pace_sec'].apply(get_pace_bracket)
        
        # Find the most recent run for comparison
        most_recent = progress_df.iloc[0]
        recent_bracket = most_recent['pace_bracket']
        
        # Find other runs in similar pace bracket
        similar_runs = progress_df[progress_df['pace_bracket'] == recent_bracket].iloc[1:]  # Exclude most recent
        
        # Display comparison
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.markdown("##### Latest Run")
            st.metric("Date", most_recent['date'])
            st.metric("Pace", most_recent['pace'])
            st.metric("Cadence", f"{most_recent['cadence']:.0f} spm")
            if most_recent['stride_cm'] > 0:
                st.metric("Stride", f"{most_recent['stride_cm']:.0f} cm")
        
        with col2:
            st.markdown(f"##### Comparison at Similar Pace ({recent_bracket})")
            
            if len(similar_runs) > 0:
                avg_cad = similar_runs['cadence'].mean()
                avg_stride = similar_runs[similar_runs['stride_cm'] > 0]['stride_cm'].mean() if len(similar_runs[similar_runs['stride_cm'] > 0]) > 0 else 0
                
                cad_diff = most_recent['cadence'] - avg_cad
                stride_diff = most_recent['stride_cm'] - avg_stride if avg_stride > 0 and most_recent['stride_cm'] > 0 else 0
                
                # Status indicators
                if cad_diff > 2:
                    cad_status = "✅ Improved"
                elif cad_diff < -2:
                    cad_status = "⚠️ Lower"
                else:
                    cad_status = "➡️ Similar"
                
                if stride_diff > 2:
                    stride_status = "✅ Longer"
                elif stride_diff < -2:
                    stride_status = "⚠️ Shorter"
                else:
                    stride_status = "➡️ Similar"
                
                st.markdown(f"""
                | Metric | Latest | Avg ({len(similar_runs)} runs) | Diff | Status |
                |--------|--------|------|------|--------|
                | Cadence | {most_recent['cadence']:.0f} spm | {avg_cad:.0f} spm | {cad_diff:+.0f} | {cad_status} |
                | Stride | {most_recent['stride_cm']:.0f} cm | {avg_stride:.0f} cm | {stride_diff:+.0f} | {stride_status} |
                """)
                
                st.caption("ℹ️ Comparing runs at similar pace isolates real form improvement from speed effects")
            else:
                st.info(f"Not enough runs at {recent_bracket} pace for comparison yet.")
        
        # Detailed table
        with st.expander("Full Run Comparison Table", expanded=False):
            st.markdown("Recent runs with cadence and stride data:")
            
            # Format as markdown table instead of st.dataframe (avoids pyarrow dependency)
            display_df = progress_df.head(15)[['date', 'name', 'distance_km', 'pace', 'cadence', 'stride_cm', 'pace_bracket']].copy()
            
            st.markdown("| Date | Run | Dist | Pace | Cadence | Stride | Bracket |")
            st.markdown("|------|-----|------|------|---------|--------|---------|")
            for _, row in display_df.iterrows():
                stride_str = f"{row['stride_cm']:.0f} cm" if row['stride_cm'] > 0 else "N/A"
                st.markdown(f"| {row['date']} | {row['name'][:25]} | {row['distance_km']:.1f}km | {row['pace']} | {row['cadence']:.0f} spm | {stride_str} | {row['pace_bracket'][:8]} |")
    
    # ============================================
    # STRIDE LENGTH ANALYSIS
    # ============================================
    st.markdown("---")
    st.subheader("Stride Length Trend")
    
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
    # FORM RECOMMENDATIONS
    # ============================================
    st.markdown("---")
    st.subheader("Form Recommendations")
    
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
    with st.expander("Debug: Recent Activity Metrics"):
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
    st.info("Try running `python scripts/incremental-sync.py --days 7` to refresh data cache.")
    
    with st.expander("Error details"):
        import traceback
        st.code(traceback.format_exc())
