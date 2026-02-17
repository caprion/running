"""
AI Metrics Engine for running analytics.

Computes per-run and weekly metrics from activity data.
Pure Python -- no LLM calls. Copilot generates narratives on demand.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple


def _is_running_split(split: Dict) -> bool:
    """
    Filter out walk/rest splits that skew cadence and stride metrics.
    A split is considered "running" if:
      - distance >= 500m (full or near-full km)
      - pace < 8:00/km (averageSpeed > 2.08 m/s)
    Walk recovery intervals between reps have very short distance
    AND very slow pace, which drags down cadence/stride averages.
    """
    dist = split.get("distance", 0)
    speed = split.get("averageSpeed", 0)
    if dist < 500:
        # Short segment — only keep if it was actually running pace
        return speed > 2.08  # faster than 8:00/km
    return True


def _running_splits(splits: List[Dict]) -> List[Dict]:
    """Return only splits where the runner was actually running."""
    return [s for s in splits if _is_running_split(s)]


def compute_pace_drift(splits: List[Dict]) -> Optional[float]:
    """
    Compute pace drift as % change from first quarter to last quarter of splits.
    Negative = got faster (good). Positive = slowed down.
    Returns None if insufficient splits.
    """
    km_splits = _running_splits([s for s in splits if s.get("distance", 0) >= 500])
    if len(km_splits) < 4:
        return None

    quarter = max(1, len(km_splits) // 4)
    first_q = km_splits[:quarter]
    last_q = km_splits[-quarter:]

    # Speed is in m/s -- higher = faster, so we invert for pace
    first_avg_speed = sum(s["averageSpeed"] for s in first_q) / len(first_q)
    last_avg_speed = sum(s["averageSpeed"] for s in last_q) / len(last_q)

    if first_avg_speed == 0:
        return None

    # Pace drift: positive = slowed down, negative = sped up
    return round(((first_avg_speed - last_avg_speed) / first_avg_speed) * 100, 1)


def compute_elevation_per_split(splits: List[Dict]) -> List[Dict]:
    """
    Extract per-split elevation data for context.
    Returns list of {lap, gain, loss, net} for each km split.
    """
    result = []
    for s in splits:
        if s.get("distance", 0) < 500:
            continue
        gain = s.get("elevationGain") or 0
        loss = s.get("elevationLoss") or 0
        result.append({
            "lap": s.get("lapIndex", 0),
            "gain_m": round(gain, 1),
            "loss_m": round(loss, 1),
            "net_m": round(gain - loss, 1),
        })
    return result


def classify_split_terrain(gain: float, loss: float) -> str:
    """Classify a 1km split as flat, uphill, downhill, or rolling."""
    net = gain - loss
    total = gain + loss
    if total < 5:
        return "flat"
    if net > 5:
        return "uphill"
    if net < -5:
        return "downhill"
    return "rolling"


def compute_hr_drift(splits: List[Dict]) -> Optional[float]:
    """
    Compute HR drift as % change from first quarter to last quarter of splits.
    Positive = HR crept up (expected). High values (>10%) may indicate fatigue.
    Returns None if insufficient data.
    """
    hr_splits = [s for s in _running_splits(splits) if s.get("averageHR", 0) > 0 and s.get("distance", 0) >= 500]
    if len(hr_splits) < 4:
        return None

    quarter = max(1, len(hr_splits) // 4)
    first_q = hr_splits[:quarter]
    last_q = hr_splits[-quarter:]

    first_avg_hr = sum(s["averageHR"] for s in first_q) / len(first_q)
    last_avg_hr = sum(s["averageHR"] for s in last_q) / len(last_q)

    if first_avg_hr == 0:
        return None

    return round(((last_avg_hr - first_avg_hr) / first_avg_hr) * 100, 1)


def compute_cadence_stats(splits: List[Dict]) -> Dict:
    """Compute cadence average and coefficient of variation from running splits only."""
    cad_splits = [s for s in _running_splits(splits) if s.get("averageRunCadence", 0) > 0 and s.get("distance", 0) >= 500]
    if not cad_splits:
        return {"avg": 0, "cv_pct": 0}

    cadences = [s["averageRunCadence"] for s in cad_splits]
    avg = sum(cadences) / len(cadences)
    if avg == 0:
        return {"avg": 0, "cv_pct": 0}

    variance = sum((c - avg) ** 2 for c in cadences) / len(cadences)
    std = variance ** 0.5
    cv = (std / avg) * 100

    return {"avg": round(avg, 1), "cv_pct": round(cv, 1)}


def compute_stride_stats(splits: List[Dict]) -> Dict:
    """Compute stride length average and speed index from running splits only."""
    stride_splits = [s for s in _running_splits(splits)
                     if s.get("strideLength", 0) > 0 and s.get("distance", 0) >= 500]
    if not stride_splits:
        return {"avg_cm": 0, "speed_index": 0}

    strides = [s["strideLength"] for s in stride_splits]
    cadences = [s.get("averageRunCadence", 0) for s in stride_splits if s.get("averageRunCadence", 0) > 0]

    avg_stride = sum(strides) / len(strides)
    avg_cadence = sum(cadences) / len(cadences) if cadences else 0
    # Speed index = cadence * stride_length_m = m/min (higher = faster)
    speed_index = avg_cadence * (avg_stride / 100) if avg_cadence > 0 else 0

    return {
        "avg_cm": round(avg_stride, 1),
        "speed_index": round(speed_index, 0),
    }


def compute_risk_flags(month: int, week_volume: float, target_volume: float,
                       streak_weeks: int) -> List[str]:
    """Compute risk flags based on current state."""
    from .plan_data import HIGH_RISK_MONTHS, MEDIUM_RISK_MONTHS, FLOOR_THRESHOLD_KM

    flags = []

    if month in HIGH_RISK_MONTHS:
        flags.append("high_risk_month")
    elif month in MEDIUM_RISK_MONTHS:
        flags.append("moderate_risk_month")

    if target_volume > 0 and week_volume < target_volume * 0.9:
        flags.append("below_90_compliance")

    if target_volume > 0 and week_volume < target_volume * 0.7:
        flags.append("below_70_compliance")

    if week_volume < FLOOR_THRESHOLD_KM:
        flags.append("below_floor")

    if streak_weeks >= 8:
        flags.append("strong_streak")

    return flags


def compute_streak(weekly_volumes: List[float], floor: float = 15.0,
                   exclude_last: bool = True) -> int:
    """
    Count consecutive recent weeks at or above the floor, working backwards.
    Excludes the current (in-progress) week by default.
    """
    vols = weekly_volumes[:-1] if exclude_last and len(weekly_volumes) > 1 else weekly_volumes
    streak = 0
    for vol in reversed(vols):
        if vol >= floor:
            streak += 1
        else:
            break
    return streak


def classify_run_type(name: str, distance_km: float) -> str:
    """Classify a run as easy, tempo, interval, or long based on name and distance."""
    lower = name.lower()
    if "interval" in lower or "x1km" in lower or "x800" in lower or "x600" in lower:
        return "interval"
    if "@" in lower and ("x" in lower.split("@")[0]):
        return "interval"
    if "tempo" in lower or "threshold" in lower:
        return "tempo"
    if distance_km >= 14 or "long" in lower:
        return "long"
    return "easy"


def grade_hr_drift(hr_drift_pct: Optional[float], pace_drift_pct: Optional[float],
                   run_type: str) -> Dict:
    """
    Grade HR drift with context about negative splits.
    Returns {grade, target, note}.
    """
    from .plan_data import HR_DRIFT_TARGETS

    if hr_drift_pct is None:
        return {"grade": "N/A", "target": None, "note": ""}

    targets = HR_DRIFT_TARGETS.get(run_type, HR_DRIFT_TARGETS["easy"])
    is_negative_split = pace_drift_pct is not None and pace_drift_pct < -2

    if hr_drift_pct <= targets["ideal"]:
        grade = "excellent"
    elif hr_drift_pct <= targets["acceptable"]:
        grade = "ok"
    elif hr_drift_pct <= targets["concern"]:
        grade = "high"
    else:
        grade = "concern"

    note = ""
    if is_negative_split and grade in ("high", "concern"):
        # Negative splits naturally push HR up — context matters
        note = "negative_split_inflated"
        if hr_drift_pct <= targets["concern"]:
            grade = "ok_with_context"

    return {
        "grade": grade,
        "target_pct": targets["acceptable"],
        "note": note,
    }


def compute_run_metrics(activity: Dict, week_activities: List[Dict],
                        campaign_week: int, plan_phase: str,
                        target_volume: float, key_workout: str,
                        all_weekly_volumes: List[float]) -> Dict:
    """
    Compute metrics for a single run in plan context.

    Args:
        activity: The activity dict from unified-cache
        week_activities: All activities in the same campaign week
        campaign_week: Which week of the 20-week plan (0 if pre-campaign)
        plan_phase: Phase name (Recovery, Base, Build, etc.)
        target_volume: Plan target km for this week
        key_workout: Key workout description for this week
        all_weekly_volumes: List of weekly volumes for streak calculation
    """
    splits = []
    if activity.get("splits") and activity["splits"].get("lapDTOs"):
        splits = activity["splits"]["lapDTOs"]

    pace_drift = compute_pace_drift(splits)
    hr_drift = compute_hr_drift(splits)
    cad_stats = compute_cadence_stats(splits)
    stride_stats = compute_stride_stats(splits)
    elevation_splits = compute_elevation_per_split(splits)

    run_type = classify_run_type(activity.get("name", ""), activity.get("distance_km", 0))
    hr_grade = grade_hr_drift(hr_drift, pace_drift, run_type)

    # Elevation summary for the run
    total_gain = activity.get("elevation_gain_m", 0) or 0
    if not total_gain and elevation_splits:
        total_gain = sum(s["gain_m"] for s in elevation_splits)
    total_loss = sum(s["loss_m"] for s in elevation_splits) if elevation_splits else 0

    # Classify terrain per split for context
    terrain_counts = {"flat": 0, "uphill": 0, "downhill": 0, "rolling": 0}
    for es in elevation_splits:
        t = classify_split_terrain(es["gain_m"], es["loss_m"])
        terrain_counts[t] += 1

    week_volume = sum(a.get("distance_km", 0) for a in week_activities)
    streak = compute_streak(all_weekly_volumes)

    run_date = datetime.strptime(activity["date"][:10], "%Y-%m-%d")
    risk_flags = compute_risk_flags(
        run_date.month, week_volume, target_volume, streak
    )

    return {
        "activity_id": activity.get("id"),
        "date": activity["date"][:10],
        "name": activity.get("name", ""),
        "computed_at": datetime.now().isoformat(timespec="seconds"),
        "metrics": {
            "distance_km": round(activity.get("distance_km", 0), 2),
            "avg_pace": activity.get("avg_pace_min_km", ""),
            "avg_hr": activity.get("avg_hr", 0),
            "max_hr": activity.get("max_hr", 0),
            "pace_drift_pct": pace_drift,
            "hr_drift_pct": hr_drift,
            "hr_drift_grade": hr_grade,
            "run_type": run_type,
            "cadence_avg": cad_stats["avg"],
            "cadence_cv_pct": cad_stats["cv_pct"],
            "stride_avg_cm": stride_stats["avg_cm"],
            "speed_index": stride_stats["speed_index"],
            "elevation_gain_m": round(total_gain, 1),
            "elevation_loss_m": round(total_loss, 1),
            "elevation_per_km": elevation_splits,
            "terrain_profile": terrain_counts,
            "campaign_week": campaign_week,
            "plan_phase": plan_phase,
            "plan_target_km": target_volume,
            "key_workout": key_workout,
            "week_volume_so_far": round(week_volume, 1),
            "week_compliance_pct": round((week_volume / target_volume * 100) if target_volume > 0 else 0, 1),
            "weekly_streak": streak,
            "risk_flags": risk_flags,
        },
    }


def compute_weekly_metrics(week_key: str, campaign_week: int,
                           week_activities: List[Dict],
                           plan_phase: str, target_volume: float,
                           key_workout: str,
                           all_weekly_volumes: List[float],
                           recent_4wk_volumes: List[float]) -> Dict:
    """
    Compute aggregated metrics for a full week.
    """
    volume = sum(a.get("distance_km", 0) for a in week_activities)
    runs = len(week_activities)
    streak = compute_streak(all_weekly_volumes)

    hrs = [a.get("avg_hr", 0) for a in week_activities if a.get("avg_hr", 0) > 0]
    avg_hr = round(sum(hrs) / len(hrs), 0) if hrs else 0

    paces_sec = []
    for a in week_activities:
        pace_str = a.get("avg_pace_min_km", "")
        if pace_str and ":" in pace_str:
            parts = pace_str.split(":")
            paces_sec.append(int(parts[0]) * 60 + int(parts[1]))
    avg_pace_sec = sum(paces_sec) / len(paces_sec) if paces_sec else 0
    avg_pace = f"{int(avg_pace_sec // 60)}:{int(avg_pace_sec % 60):02d}" if avg_pace_sec else ""

    distances = [a.get("distance_km", 0) for a in week_activities]
    longest = max(distances) if distances else 0

    cadences = [a.get("avg_cadence", 0) for a in week_activities if a.get("avg_cadence", 0) > 0]
    avg_cadence = round(sum(cadences) / len(cadences), 0) if cadences else 0

    # Compute clean stride from splits (excludes walk breaks)
    strides_per_run = []
    for a in week_activities:
        if a.get("splits") and a["splits"].get("lapDTOs"):
            run_splits = _running_splits(a["splits"]["lapDTOs"])
            sl = [s["strideLength"] for s in run_splits if s.get("strideLength", 0) > 0]
            if sl:
                strides_per_run.append(sum(sl) / len(sl))
    avg_stride = round(sum(strides_per_run) / len(strides_per_run), 1) if strides_per_run else 0
    speed_index = round(avg_cadence * avg_stride / 100, 0) if avg_cadence and avg_stride else 0

    run_date = datetime.strptime(week_activities[0]["date"][:10], "%Y-%m-%d") if week_activities else datetime.now()
    risk_flags = compute_risk_flags(run_date.month, volume, target_volume, streak)

    return {
        "week": week_key,
        "campaign_week": campaign_week,
        "computed_at": datetime.now().isoformat(timespec="seconds"),
        "metrics": {
            "volume_km": round(volume, 1),
            "target_km": target_volume,
            "compliance_pct": round((volume / target_volume * 100) if target_volume > 0 else 0, 1),
            "runs": runs,
            "avg_pace": avg_pace,
            "avg_hr": avg_hr,
            "cadence_avg": avg_cadence,
            "stride_avg_cm": avg_stride,
            "speed_index": speed_index,
            "longest_run_km": round(longest, 1),
            "streak_weeks": streak,
            "volume_trend_4wk": [round(v, 1) for v in recent_4wk_volumes],
            "key_workout": key_workout,
            "plan_phase": plan_phase,
            "risk_flags": risk_flags,
        },
    }
