"""
AI Enrichment Compute Engine.

Reads unified-cache.json, computes per-run and weekly metrics,
writes tracking/ai-insights.json.

Usage:
    python -m scripts.ai.compute                    # enrich unenriched runs
    python -m scripts.ai.compute --days 60          # backfill last 60 days
    python -m scripts.ai.compute --force            # re-enrich all runs
"""

import argparse
import json
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List

from .plan_data import (
    CAMPAIGN_START,
    WEEKLY_PLAN,
    get_campaign_week,
    get_key_workout,
    get_phase_for_week,
    get_target_volume,
)
from .metrics import compute_run_metrics, compute_weekly_metrics

BASE_DIR = Path(__file__).parent.parent.parent
UNIFIED_CACHE = BASE_DIR / "tracking" / "unified-cache.json"
INSIGHTS_FILE = BASE_DIR / "tracking" / "ai-insights.json"


def load_insights() -> Dict:
    """Load existing insights or return empty structure."""
    if INSIGHTS_FILE.exists():
        with open(INSIGHTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"runs": {}, "weeks": {}, "last_computed": None}


def save_insights(insights: Dict) -> None:
    """Write insights to disk."""
    insights["last_computed"] = datetime.now().isoformat(timespec="seconds")
    with open(INSIGHTS_FILE, "w", encoding="utf-8") as f:
        json.dump(insights, f, indent=2, ensure_ascii=False)
    print(f"Saved insights to {INSIGHTS_FILE}")


def load_running_activities() -> List[Dict]:
    """Load running activities from unified cache."""
    if not UNIFIED_CACHE.exists():
        print(f"Cache not found: {UNIFIED_CACHE}")
        return []

    with open(UNIFIED_CACHE, "r", encoding="utf-8") as f:
        cache = json.load(f)

    activities = [a for a in cache.get("activities", []) if a.get("type") == "running"]
    activities.sort(key=lambda x: x["date"])
    return activities


def group_by_week(activities: List[Dict]) -> Dict[str, List[Dict]]:
    """Group activities by ISO week key (YYYY-Wnn)."""
    weeks: Dict[str, List[Dict]] = defaultdict(list)
    for a in activities:
        dt = datetime.strptime(a["date"][:10], "%Y-%m-%d")
        iso = dt.isocalendar()
        wk = f"{iso[0]}-W{iso[1]:02d}"
        weeks[wk].append(a)
    return dict(weeks)


def compute_weekly_volumes(weeks: Dict[str, List[Dict]]) -> Dict[str, float]:
    """Compute total volume per week."""
    return {wk: sum(a.get("distance_km", 0) for a in acts) for wk, acts in weeks.items()}


def enrich(days: int = 0, force: bool = False) -> None:
    """
    Main enrichment pipeline.

    Args:
        days: Only process runs from last N days (0 = only unenriched)
        force: Re-compute all runs even if already enriched
    """
    activities = load_running_activities()
    if not activities:
        print("No running activities found.")
        return

    insights = load_insights()
    weeks_by_key = group_by_week(activities)
    weekly_volumes = compute_weekly_volumes(weeks_by_key)
    sorted_week_keys = sorted(weeks_by_key.keys())

    # Build ordered list of weekly volumes for streak calculation
    # Fill in ALL campaign weeks (including weeks with 0 runs) so streak detects gaps
    campaign_start_iso = CAMPAIGN_START.isocalendar()
    campaign_start_wk = f"{campaign_start_iso[0]}-W{campaign_start_iso[1]:02d}"
    from datetime import datetime as _dt
    current_iso = _dt.now().isocalendar()
    current_wk = f"{current_iso[0]}-W{current_iso[1]:02d}"

    # Generate all ISO week keys from campaign start to now
    all_campaign_weeks = []
    d = CAMPAIGN_START
    while True:
        iso = d.isocalendar()
        wk = f"{iso[0]}-W{iso[1]:02d}"
        if wk > current_wk:
            break
        if wk >= campaign_start_wk and wk not in all_campaign_weeks:
            all_campaign_weeks.append(wk)
        d += timedelta(days=7)

    volume_list = [weekly_volumes.get(wk, 0) for wk in all_campaign_weeks]

    # Determine which activities to process
    if days > 0:
        cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        to_process = [a for a in activities if a["date"][:10] >= cutoff]
    elif force:
        to_process = activities
    else:
        # Only unenriched runs
        existing_ids = set(insights.get("runs", {}).keys())
        to_process = [a for a in activities if str(a.get("id")) not in existing_ids]

    if not to_process:
        print("All runs already enriched. Use --force to re-compute.")
        return

    print(f"Enriching {len(to_process)} runs...")

    # Per-run metrics
    run_count = 0
    for activity in to_process:
        act_date = datetime.strptime(activity["date"][:10], "%Y-%m-%d")
        campaign_week = get_campaign_week(act_date)
        plan_phase = get_phase_for_week(campaign_week)
        target_volume = get_target_volume(campaign_week)
        key_workout = get_key_workout(campaign_week)

        # Find all activities in the same week
        iso = act_date.isocalendar()
        week_key = f"{iso[0]}-W{iso[1]:02d}"
        week_activities = weeks_by_key.get(week_key, [])

        run_metrics = compute_run_metrics(
            activity=activity,
            week_activities=week_activities,
            campaign_week=campaign_week,
            plan_phase=plan_phase,
            target_volume=target_volume,
            key_workout=key_workout,
            all_weekly_volumes=volume_list,
        )

        insights.setdefault("runs", {})[str(activity["id"])] = run_metrics
        run_count += 1

    # Weekly rollups for affected weeks
    affected_weeks = set()
    for activity in to_process:
        act_date = datetime.strptime(activity["date"][:10], "%Y-%m-%d")
        iso = act_date.isocalendar()
        affected_weeks.add(f"{iso[0]}-W{iso[1]:02d}")

    week_count = 0
    for week_key in sorted(affected_weeks):
        week_activities = weeks_by_key.get(week_key, [])
        if not week_activities:
            continue

        first_date = datetime.strptime(week_activities[0]["date"][:10], "%Y-%m-%d")
        campaign_week = get_campaign_week(first_date)
        plan_phase = get_phase_for_week(campaign_week)
        target_volume = get_target_volume(campaign_week)
        key_workout = get_key_workout(campaign_week)

        # Get recent 4-week volumes for trend
        wk_idx = sorted_week_keys.index(week_key) if week_key in sorted_week_keys else -1
        if wk_idx >= 3:
            recent_4wk = [weekly_volumes[sorted_week_keys[i]] for i in range(wk_idx - 3, wk_idx + 1)]
        else:
            recent_4wk = [weekly_volumes[sorted_week_keys[i]] for i in range(0, wk_idx + 1)]

        weekly = compute_weekly_metrics(
            week_key=week_key,
            campaign_week=campaign_week,
            week_activities=week_activities,
            plan_phase=plan_phase,
            target_volume=target_volume,
            key_workout=key_workout,
            all_weekly_volumes=volume_list,
            recent_4wk_volumes=recent_4wk,
        )

        insights.setdefault("weeks", {})[week_key] = weekly
        week_count += 1

    save_insights(insights)
    print(f"Enriched {run_count} runs, {week_count} weeks.")


def main():
    parser = argparse.ArgumentParser(description="Compute AI metrics for running activities")
    parser.add_argument("--days", type=int, default=0, help="Backfill last N days (0 = unenriched only)")
    parser.add_argument("--force", action="store_true", help="Re-compute all runs")
    args = parser.parse_args()

    enrich(days=args.days, force=args.force)


if __name__ == "__main__":
    main()
