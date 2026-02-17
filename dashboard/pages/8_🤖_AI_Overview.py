"""
AI Run Overview

Displays pre-computed AI metrics for recent runs and weekly trends.
For full narrative analysis, ask Copilot: "analyze my latest runs"
"""

import streamlit as st
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent.parent.parent))

st.set_page_config(page_title="AI Overview", page_icon="🤖", layout="wide")

st.title("AI Run Overview")

INSIGHTS_FILE = Path(__file__).parent.parent.parent / "tracking" / "ai-insights.json"


def load_insights():
    if not INSIGHTS_FILE.exists():
        return None
    with open(INSIGHTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


insights = load_insights()

if not insights or not insights.get("runs"):
    st.warning("No AI insights found. Run sync with --enrich flag:")
    st.code("python scripts/incremental-sync.py --days 7 --enrich")
    st.info("Or compute metrics directly:")
    st.code("python -m scripts.ai.compute --days 60")
    st.stop()

# Sort runs by date (newest first)
runs = sorted(insights["runs"].values(), key=lambda x: x["date"], reverse=True)
weeks = sorted(insights["weeks"].values(), key=lambda x: x["week"], reverse=True)

# ============================================
# LATEST RUN
# ============================================
latest = runs[0]
m = latest["metrics"]

st.subheader(f"Latest Run: {latest['name']}")
st.caption(f"{latest['date']} | Computed: {latest.get('computed_at', 'N/A')}")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Distance", f"{m['distance_km']}km", delta=m['avg_pace'] + "/km")

with col2:
    hr_delta = None
    if m.get("hr_drift_pct") is not None:
        hr_label = f"+{m['hr_drift_pct']}%" if m["hr_drift_pct"] > 0 else f"{m['hr_drift_pct']}%"
        hr_color = "inverse" if m["hr_drift_pct"] > 10 else "off"
        st.metric("Avg HR", f"{m['avg_hr']:.0f} bpm", delta=f"drift {hr_label}", delta_color=hr_color)
    else:
        st.metric("Avg HR", f"{m['avg_hr']:.0f} bpm")

with col3:
    if m.get("pace_drift_pct") is not None:
        pace_label = f"+{m['pace_drift_pct']}%" if m["pace_drift_pct"] > 0 else f"{m['pace_drift_pct']}%"
        # Negative drift = got faster = good
        pace_color = "normal" if m["pace_drift_pct"] <= 0 else "inverse"
        st.metric("Pace Drift", pace_label, delta="slower" if m["pace_drift_pct"] > 0 else "faster", delta_color=pace_color)
    else:
        st.metric("Pace Drift", "N/A")

with col4:
    st.metric("Cadence", f"{m['cadence_avg']:.0f} spm",
              delta=f"CV {m['cadence_cv_pct']}%" if m.get("cadence_cv_pct") else None,
              delta_color="off")

# Elevation profile if available
elev_splits = m.get("elevation_per_km", [])
has_elevation = any(s.get("gain_m", 0) > 0 or s.get("loss_m", 0) > 0 for s in elev_splits)

if has_elevation:
    terrain = m.get("terrain_profile", {})
    st.markdown(
        f"**Elevation:** +{m.get('elevation_gain_m', 0):.0f}m / -{m.get('elevation_loss_m', 0):.0f}m | "
        f"Terrain: {terrain.get('flat', 0)} flat, {terrain.get('uphill', 0)} up, "
        f"{terrain.get('downhill', 0)} down, {terrain.get('rolling', 0)} rolling"
    )

# Plan context
if m.get("campaign_week", 0) > 0:
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col1:
        compliance_color = "normal" if m["week_compliance_pct"] >= 90 else "inverse"
        st.metric(
            f"Week {m['campaign_week']} ({m['plan_phase']})",
            f"{m['week_volume_so_far']}km / {m['plan_target_km']}km",
            delta=f"{m['week_compliance_pct']:.0f}% of target",
            delta_color=compliance_color,
        )
    with col2:
        st.metric("Streak", f"{m['weekly_streak']} weeks", delta="above 15km floor", delta_color="off")
    with col3:
        st.metric("Key Workout", m.get("key_workout", "")[:30])

# Risk flags
if m.get("risk_flags"):
    flag_labels = {
        "high_risk_month": "High-risk month (historical violation pattern)",
        "moderate_risk_month": "Moderate risk month",
        "below_90_compliance": "Below 90% weekly target",
        "below_70_compliance": "Below 70% weekly target",
        "below_floor": "Below 15km weekly floor",
        "strong_streak": "Strong consistency streak",
    }
    for flag in m["risk_flags"]:
        if flag == "strong_streak":
            st.success(flag_labels.get(flag, flag))
        elif "below" in flag:
            st.error(flag_labels.get(flag, flag))
        else:
            st.warning(flag_labels.get(flag, flag))

# ============================================
# WEEKLY TRENDS
# ============================================
st.markdown("---")
st.subheader("Weekly Trends")

if weeks:
    # Volume trend table
    st.markdown("| Week | Phase | Volume | Target | Compliance | Runs | Streak | Longest |")
    st.markdown("|------|-------|--------|--------|------------|------|--------|---------|")

    for w in weeks[:8]:
        wm = w["metrics"]
        compliance_icon = ""
        if wm["compliance_pct"] >= 90:
            compliance_icon = "OK"
        elif wm["compliance_pct"] >= 70:
            compliance_icon = "--"
        else:
            compliance_icon = "LOW"

        st.markdown(
            f"| {w['week']} (CW{w['campaign_week']}) | {wm.get('plan_phase', '')} | "
            f"{wm['volume_km']:.1f}km | {wm['target_km']}km | "
            f"{wm['compliance_pct']:.0f}% {compliance_icon} | {wm['runs']} | "
            f"{wm['streak_weeks']}wk | {wm['longest_run_km']:.1f}km |"
        )

    # 4-week volume trend
    if weeks[0]["metrics"].get("volume_trend_4wk"):
        trend = weeks[0]["metrics"]["volume_trend_4wk"]
        trend_str = " -> ".join(f"{v:.0f}" for v in trend)
        avg = sum(trend) / len(trend)
        st.markdown(f"**4-week volume trend:** {trend_str} km (avg {avg:.0f}km/week)")

# ============================================
# RECENT RUNS TABLE
# ============================================
st.markdown("---")
st.subheader("Recent Runs")

st.markdown("| Date | Run | Dist | Pace | HR | Drift | Cadence | Phase |")
st.markdown("|------|-----|------|------|----|-------|---------|-------|")

for r in runs[:10]:
    rm = r["metrics"]
    pace_drift = f"{rm['pace_drift_pct']:+.1f}%" if rm.get("pace_drift_pct") is not None else "N/A"
    hr_drift = f"{rm['hr_drift_pct']:+.1f}%" if rm.get("hr_drift_pct") is not None else "N/A"
    st.markdown(
        f"| {r['date']} | {r['name'][:25]} | {rm['distance_km']}km | "
        f"{rm['avg_pace']} | {rm['avg_hr']:.0f} | P:{pace_drift} H:{hr_drift} | "
        f"{rm['cadence_avg']:.0f} | {rm.get('metrics', {}).get('plan_phase', '')} |"
    )

# ============================================
# COPILOT PROMPT
# ============================================
st.markdown("---")
st.info(
    "For a full AI narrative analysis, ask Copilot in the terminal:\n\n"
    "`@copilot analyze my latest runs from the running project`"
)

# Debug
with st.expander("Debug: Raw Insights"):
    st.markdown(f"**Runs enriched:** {len(insights.get('runs', {}))}")
    st.markdown(f"**Weeks enriched:** {len(insights.get('weeks', {}))}")
    st.markdown(f"**Last computed:** {insights.get('last_computed', 'N/A')}")
    st.markdown(f"**Insights file:** `{INSIGHTS_FILE}`")
