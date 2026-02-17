"""
Plan Compliance Dashboard

Track actual training vs planned targets for the 20-week HM campaign.
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
sys.path.append(str(Path(__file__).parent.parent.parent))

from utils.data_loader import activities_to_dataframe, get_weekly_summary
from scripts.ai.plan_data import (
    CAMPAIGN_START, WEEKLY_PLAN, PHASE_PACES, KEY_DATES,
    get_campaign_week, get_phase_for_week,
)

# Page config
st.set_page_config(page_title="Plan Compliance", page_icon="✅", layout="wide")

st.title("Plan Compliance")
st.markdown("Track actual training vs 20-week plan targets")

try:
    df = activities_to_dataframe()
    weekly = get_weekly_summary(df)
    
    if df.empty:
        st.error("No running activities found. Run `python scripts/incremental-sync.py --days 90` to sync data.")
        st.stop()

    # Filter to campaign period
    campaign_df = df[df['date'] >= CAMPAIGN_START].copy()
    campaign_df['campaign_week'] = campaign_df['date'].apply(get_campaign_week)
    
    # Current week info
    current_week = get_campaign_week(datetime.now())
    current_phase = get_phase_for_week(current_week)
    
    # ============================================
    # CAMPAIGN OVERVIEW
    # ============================================
    st.subheader("📅 Campaign Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Current Week",
            f"Week {current_week}",
            delta=current_phase,
            delta_color="off"
        )
    
    with col2:
        days_to_10k = (KEY_DATES["10K Race"] - datetime.now()).days
        st.metric(
            "Days to 10K",
            f"{days_to_10k} days",
            help="April 12, 2026"
        )
    
    with col3:
        days_to_hm = (KEY_DATES["HM Race"] - datetime.now()).days
        st.metric(
            "Days to HM",
            f"{days_to_hm} days",
            help="May 24, 2026"
        )
    
    with col4:
        weeks_completed = max(0, current_week - 1)
        completion = (weeks_completed / 20) * 100
        st.metric(
            "Plan Progress",
            f"{completion:.0f}%",
            delta=f"{weeks_completed}/20 weeks"
        )

    # ============================================
    # CURRENT WEEK STATUS
    # ============================================
    st.markdown("---")
    st.subheader(f"📊 Week {current_week} Status: {current_phase}")
    
    if current_week in WEEKLY_PLAN:
        plan = WEEKLY_PLAN[current_week]
        
        # Get this week's actual data
        this_week_runs = campaign_df[campaign_df['campaign_week'] == current_week]
        actual_volume = this_week_runs['distance_km'].sum()
        actual_runs = len(this_week_runs)
        target_volume = plan['volume_km']
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            pct_complete = (actual_volume / target_volume * 100) if target_volume > 0 else 0
            volume_status = "🟢" if pct_complete >= 90 else "🟡" if pct_complete >= 70 else "🔴"
            st.metric(
                f"{volume_status} Volume",
                f"{actual_volume:.1f} / {target_volume} km",
                delta=f"{pct_complete:.0f}% of target"
            )
        
        with col2:
            st.metric(
                "Runs Logged",
                f"{actual_runs}",
                help="Target: 3-4 runs per week"
            )
        
        with col3:
            st.metric(
                "Key Workout",
                plan['key_workout'][:30] + "..." if len(plan['key_workout']) > 30 else plan['key_workout'],
                help=plan['key_workout']
            )
        
        # This week's runs table
        if not this_week_runs.empty:
            st.markdown("**This Week's Runs:**")
            st.markdown("| Date | Activity | Distance | Pace | Avg HR |")
            st.markdown("|------|----------|----------|------|--------|")
            for _, row in this_week_runs.iterrows():
                pace = row.get('avg_pace_min_km', 'N/A') if 'avg_pace_min_km' in row else 'N/A'
                hr = f"{row['avg_hr']:.0f}" if pd.notna(row.get('avg_hr')) else 'N/A'
                st.markdown(f"| {row['date'].strftime('%a %b %d')} | {row['name'][:25]} | {row['distance_km']:.1f}km | {pace} | {hr} |")
        else:
            st.info("No runs logged this week yet.")
    else:
        st.warning("Campaign week not found in plan.")

    # ============================================
    # WEEKLY COMPLIANCE CHART
    # ============================================
    st.markdown("---")
    st.subheader("📈 Weekly Volume: Planned vs Actual")
    
    # Build comparison data
    comparison_data = []
    for week_num in range(1, min(current_week + 1, 21)):
        if week_num in WEEKLY_PLAN:
            plan = WEEKLY_PLAN[week_num]
            week_runs = campaign_df[campaign_df['campaign_week'] == week_num]
            actual = week_runs['distance_km'].sum()
            target = plan['volume_km']
            compliance = (actual / target * 100) if target > 0 else 0
            
            comparison_data.append({
                'week': f"W{week_num}",
                'week_num': week_num,
                'phase': plan['phase'],
                'target': target,
                'actual': actual,
                'compliance': compliance
            })
    
    if comparison_data:
        comp_df = pd.DataFrame(comparison_data)
        
        fig = go.Figure()
        
        # Target bars (background)
        fig.add_trace(go.Bar(
            x=comp_df['week'],
            y=comp_df['target'],
            name='Target',
            marker_color='rgba(200, 200, 200, 0.5)',
            text=[f"{t}km" for t in comp_df['target']],
            textposition='outside'
        ))
        
        # Actual bars (foreground with color coding)
        colors = ['#2ecc71' if c >= 90 else '#f39c12' if c >= 70 else '#e74c3c' 
                  for c in comp_df['compliance']]
        
        fig.add_trace(go.Bar(
            x=comp_df['week'],
            y=comp_df['actual'],
            name='Actual',
            marker_color=colors,
            text=[f"{a:.1f}km" for a in comp_df['actual']],
            textposition='inside'
        ))
        
        fig.update_layout(
            barmode='overlay',
            xaxis_title="Week",
            yaxis_title="Volume (km)",
            height=400,
            legend=dict(orientation="h", yanchor="bottom", y=1.02)
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Compliance summary
        avg_compliance = comp_df['compliance'].mean()
        weeks_on_target = len(comp_df[comp_df['compliance'] >= 90])
        
        st.markdown(f"""
        **Compliance Summary:** {avg_compliance:.0f}% average | 
        {weeks_on_target}/{len(comp_df)} weeks on target (≥90%)
        """)

    # ============================================
    # PHASE COMPLIANCE TABLE
    # ============================================
    st.markdown("---")
    st.subheader("📋 Full Plan Status")
    
    # Show all 20 weeks
    st.markdown("| Week | Phase | Target | Actual | Status | Key Workout |")
    st.markdown("|------|-------|--------|--------|--------|-------------|")
    
    for week_num in range(1, 21):
        if week_num in WEEKLY_PLAN:
            plan = WEEKLY_PLAN[week_num]
            week_runs = campaign_df[campaign_df['campaign_week'] == week_num]
            actual = week_runs['distance_km'].sum()
            target = plan['volume_km']
            
            if week_num > current_week:
                status = "⬜ Upcoming"
                actual_str = "-"
            elif week_num == current_week:
                pct = (actual / target * 100) if target > 0 else 0
                status = "🔵 In Progress" if pct < 100 else "🟢 Complete"
                actual_str = f"{actual:.1f}km"
            else:
                pct = (actual / target * 100) if target > 0 else 0
                if pct >= 90:
                    status = "🟢 Hit"
                elif pct >= 70:
                    status = "🟡 Close"
                else:
                    status = "🔴 Missed"
                actual_str = f"{actual:.1f}km"
            
            phase_display = plan['phase']
            if "RACE" in phase_display:
                phase_display = f"**{phase_display}**"
            
            key_workout = plan['key_workout'][:35] + "..." if len(plan['key_workout']) > 35 else plan['key_workout']
            
            st.markdown(f"| {week_num} | {phase_display} | {target}km | {actual_str} | {status} | {key_workout} |")

    # ============================================
    # UPCOMING KEY WORKOUTS
    # ============================================
    st.markdown("---")
    st.subheader("🎯 Upcoming Key Workouts")
    
    upcoming_weeks = range(current_week, min(current_week + 4, 21))
    for week_num in upcoming_weeks:
        if week_num in WEEKLY_PLAN:
            plan = WEEKLY_PLAN[week_num]
            week_start = CAMPAIGN_START + timedelta(weeks=week_num - 1)
            
            if week_num == current_week:
                marker = "👉 **This Week**"
            else:
                marker = f"Week {week_num}"
            
            st.markdown(f"""
            **{marker}** ({week_start.strftime('%b %d')}) - {plan['phase']}
            - Volume: {plan['volume_km']}km
            - Key: {plan['key_workout']}
            """)

    # ============================================
    # GOAL REVIEW CHECKPOINT
    # ============================================
    if current_week >= 6 and current_week <= 8:
        st.markdown("---")
        st.warning("📋 **Goal Review Checkpoint (Week 6-8)**")
        st.markdown("""
        Time to assess and potentially adjust goals based on:
        - Weekly volume consistency: Are we hitting 35-40 km/week?
        - Tempo pace progression: Can we sustain 5:50-6:00/km for 4-5km?
        - VO2max trend: Moving toward 42-43?
        - Recovery metrics: Sleep, RHR stable?
        
        See plan.md for adjustment protocol.
        """)

    # ============================================
    # FULL TRAINING PLAN (merged from Season Plan page)
    # ============================================
    st.markdown("---")
    with st.expander("View Full Training Plan", expanded=False):
        import os as _os
        _use_sample = _os.getenv("USE_SAMPLE_DATA", "false").lower() == "true"
        if _use_sample:
            _plan_path = Path(__file__).parent.parent.parent / "sample-data" / "seasons" / "2025-sample-runner" / "plan.md"
        else:
            _plan_path = Path(__file__).parent.parent.parent / "seasons" / "2026-spring-hm-sub2" / "plan.md"
        if _plan_path.exists():
            with open(_plan_path, 'r', encoding='utf-8') as _f:
                st.markdown(_f.read())
        else:
            st.info(f"Plan file not found: {_plan_path}")

    # ============================================
    # DEBUG EXPANDER
    # ============================================
    with st.expander("🔍 Debug: Campaign Data"):
        st.markdown(f"**Campaign Start:** {CAMPAIGN_START.strftime('%Y-%m-%d')}")
        st.markdown(f"**Current Date:** {datetime.now().strftime('%Y-%m-%d')}")
        st.markdown(f"**Current Campaign Week:** {current_week}")
        st.markdown(f"**Runs in Campaign Period:** {len(campaign_df)}")
        
        if not campaign_df.empty:
            st.markdown("\n**Recent Campaign Runs:**")
            for _, row in campaign_df.tail(5).iterrows():
                st.markdown(f"- W{row['campaign_week']}: {row['name']} - {row['distance_km']:.1f}km")

except Exception as e:
    st.error(f"Error loading data: {e}")
    st.info("Try running `python scripts/incremental-sync.py --days 7` to refresh data cache.")
    
    with st.expander("Error details"):
        import traceback
        st.code(traceback.format_exc())
