"""
Data loading utilities for running analytics dashboard
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import pandas as pd


# Environment variable to use sample data (for GitHub demos)
# Default: false (use real personal data in tracking/)
USE_SAMPLE_DATA = os.getenv("USE_SAMPLE_DATA", "false").lower() == "true"
DATA_DIR = "sample-data" if USE_SAMPLE_DATA else "tracking"

# Path to cache files (configurable based on USE_SAMPLE_DATA)
BASE_DIR = Path(__file__).parent.parent.parent
GARMIN_CACHE_FILE = BASE_DIR / DATA_DIR / "garmin-cache.json"
STRAVA_CACHE_FILE = BASE_DIR / DATA_DIR / "strava-cache.json"
UNIFIED_CACHE_FILE = BASE_DIR / DATA_DIR / "unified-cache.json"

# Log which data source is being used
if USE_SAMPLE_DATA:
    print(f"📊 Using SAMPLE DATA from {DATA_DIR}/")
else:
    print(f"📊 Using PERSONAL DATA from {DATA_DIR}/")


def load_garmin_data() -> Dict:
    """Load all data from Garmin cache"""
    if not GARMIN_CACHE_FILE.exists():
        return {"activities": [], "training_status": {}, "sleep": [], "last_sync": None}

    with open(GARMIN_CACHE_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_strava_data() -> Dict:
    """Load all data from Strava cache"""
    if not STRAVA_CACHE_FILE.exists():
        return {"activities": [], "athlete_profile": {}, "last_sync": None}

    with open(STRAVA_CACHE_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def _activities_match(act1: Dict, act2: Dict, tolerance_km: float = 0.1, tolerance_hours: int = 2) -> bool:
    """
    Check if two activities are the same (likely duplicates from different sources)

    Args:
        act1: First activity
        act2: Second activity
        tolerance_km: Distance difference tolerance in km (default: 0.1km = 100m)
        tolerance_hours: Time difference tolerance in hours (default: 2 hours)

    Returns:
        True if activities are likely the same
    """
    # Parse dates
    try:
        date1 = datetime.strptime(act1['date'], '%Y-%m-%d %H:%M:%S')
    except:
        try:
            date1 = datetime.strptime(act1['date'], '%Y-%m-%d %H:%M:%S.%f')
        except:
            return False

    try:
        date2 = datetime.strptime(act2['date'], '%Y-%m-%d %H:%M:%S')
    except:
        try:
            date2 = datetime.strptime(act2['date'], '%Y-%m-%d %H:%M:%S.%f')
        except:
            return False

    # Check if dates are within tolerance
    time_diff = abs((date1 - date2).total_seconds())
    if time_diff > tolerance_hours * 3600:
        return False

    # Check if distances are within tolerance
    dist1 = act1.get('distance_km', 0)
    dist2 = act2.get('distance_km', 0)
    dist_diff = abs(dist1 - dist2)

    if dist_diff > tolerance_km:
        return False

    return True


def merge_activities(garmin_activities: List[Dict], strava_activities: List[Dict]) -> List[Dict]:
    """
    Merge activities from Garmin and Strava, removing duplicates

    Strategy:
    - Prefer Garmin data when both sources have the same activity (better HR zones, training metrics)
    - Keep Strava-only activities that don't match any Garmin activity
    - Mark each activity with its source(s)

    Args:
        garmin_activities: Activities from Garmin
        strava_activities: Activities from Strava

    Returns:
        Merged list of activities with duplicates removed
    """
    merged = []
    strava_matched = set()

    # First pass: Add all Garmin activities
    for garmin_act in garmin_activities:
        # Mark as Garmin source
        garmin_act['source'] = 'garmin'

        # Check if this Garmin activity matches any Strava activity
        for i, strava_act in enumerate(strava_activities):
            if i in strava_matched:
                continue

            if _activities_match(garmin_act, strava_act):
                # Found a match! Mark as both sources
                garmin_act['source'] = 'both'
                garmin_act['strava_id'] = strava_act.get('strava_id')

                # Copy Strava-specific fields if available
                if 'suffer_score' in strava_act and strava_act['suffer_score']:
                    garmin_act['suffer_score'] = strava_act['suffer_score']

                # If Garmin lacks per-km splits (or has only a single lap), but Strava has splits,
                # adopt Strava-derived lapDTOs to enable pace/HR drift analyses.
                try:
                    garmin_laps = (garmin_act.get('splits') or {}).get('lapDTOs') or []
                except Exception:
                    garmin_laps = []
                try:
                    strava_laps = (strava_act.get('splits') or {}).get('lapDTOs') or []
                except Exception:
                    strava_laps = []

                if (not garmin_laps or len(garmin_laps) <= 1) and strava_laps and len(strava_laps) >= 2:
                    garmin_act['splits'] = {'lapDTOs': strava_laps}
                    garmin_act['splits_source'] = 'strava'

                strava_matched.add(i)
                break

        merged.append(garmin_act)

    # Second pass: Add Strava-only activities (not matched with Garmin)
    for i, strava_act in enumerate(strava_activities):
        if i not in strava_matched:
            # This is a Strava-only activity
            strava_act['source'] = 'strava'
            merged.append(strava_act)

    # Sort by date (newest first)
    merged.sort(key=lambda x: x['date'], reverse=True)

    return merged


def load_activities() -> List[Dict]:
    """
    Load activities from unified cache (preferred) or legacy sources

    Priority:
    1. Use unified-cache.json if it exists (pre-merged, fastest)
    2. Fall back to merging Garmin + Strava caches (legacy mode)

    Returns:
        List of activities with duplicates removed
    """
    # Check for unified cache first (new architecture)
    if UNIFIED_CACHE_FILE.exists():
        try:
            with open(UNIFIED_CACHE_FILE, 'r', encoding='utf-8') as f:
                unified_data = json.load(f)
                return unified_data.get('activities', [])
        except Exception as e:
            print(f"Warning: Could not load unified cache: {e}")
            print("Falling back to legacy merge mode...")

    # Fall back to legacy merge mode (for backward compatibility)
    garmin_data = load_garmin_data()
    strava_data = load_strava_data()

    garmin_activities = garmin_data.get('activities', [])
    strava_activities = strava_data.get('activities', [])

    # If only one source has data, return it directly
    if not garmin_activities and not strava_activities:
        return []
    if not garmin_activities:
        for act in strava_activities:
            act['source'] = 'strava'
        return strava_activities
    if not strava_activities:
        for act in garmin_activities:
            act['source'] = 'garmin'
        return garmin_activities

    # Merge and deduplicate
    return merge_activities(garmin_activities, strava_activities)


def activities_to_dataframe() -> pd.DataFrame:
    """Convert activities to pandas DataFrame for analysis"""
    activities = load_activities()

    if not activities:
        return pd.DataFrame()

    # Convert to DataFrame
    df = pd.DataFrame(activities)

    # Parse date
    df['date'] = pd.to_datetime(df['date'])

    # Add derived columns
    df['year'] = df['date'].dt.year
    df['month'] = df['date'].dt.month
    df['week'] = df['date'].dt.isocalendar().week
    df['iso_year'] = df['date'].dt.isocalendar().year
    df['day_of_week'] = df['date'].dt.day_name()
    df['date_only'] = df['date'].dt.date

    # Week key for grouping
    df['week_key'] = df['iso_year'].astype(str) + '-W' + df['week'].astype(str).str.zfill(2)

    # Month key for grouping
    df['month_key'] = df['date'].dt.strftime('%Y-%m')

    # Filter to running activities only
    df = df[df['type'] == 'running'].copy()

    # Sort by date
    df = df.sort_values('date')

    return df


def get_training_status() -> Dict:
    """Get current training status metrics"""
    data = load_garmin_data()
    return data.get('training_status', {})


def get_sleep_data() -> List[Dict]:
    """Get sleep data"""
    data = load_garmin_data()
    return data.get('sleep', [])


def get_last_sync_time() -> Optional[str]:
    """Get last sync timestamp from unified cache or individual sources"""
    # Check unified cache first
    if UNIFIED_CACHE_FILE.exists():
        try:
            with open(UNIFIED_CACHE_FILE, 'r', encoding='utf-8') as f:
                unified_data = json.load(f)
                last_sync = unified_data.get('last_sync') or unified_data.get('build_date')
                if last_sync:
                    dt = datetime.fromisoformat(last_sync)
                    return f"Unified: {dt.strftime('%Y-%m-%d %H:%M')}"
        except Exception:
            pass

    # Fall back to individual sources
    garmin_data = load_garmin_data()
    strava_data = load_strava_data()

    garmin_sync = garmin_data.get('last_sync')
    strava_sync = strava_data.get('last_sync')

    parts = []
    if garmin_sync:
        dt = datetime.fromisoformat(garmin_sync)
        parts.append(f"Garmin: {dt.strftime('%Y-%m-%d %H:%M')}")
    if strava_sync:
        dt = datetime.fromisoformat(strava_sync)
        parts.append(f"Strava: {dt.strftime('%Y-%m-%d %H:%M')}")

    if parts:
        return " | ".join(parts)
    return None


def get_weekly_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate weekly summary statistics"""
    if df.empty:
        return pd.DataFrame()

    weekly = df.groupby('week_key').agg({
        'distance_km': 'sum',
        'id': 'count',
        'avg_hr': 'mean',
        'date_only': lambda x: ', '.join(sorted([str(d) for d in set(x)]))
    }).reset_index()

    weekly.columns = ['week_key', 'distance_km', 'runs', 'avg_hr', 'dates']

    # Add status
    weekly['status'] = weekly['distance_km'].apply(
        lambda x: 'GREEN' if x >= 20 else ('YELLOW' if x >= 15 else 'RED')
    )

    # Parse week key to get year and week number for sorting
    weekly[['year', 'week']] = weekly['week_key'].str.split('-W', expand=True)
    weekly['year'] = weekly['year'].astype(int)
    weekly['week'] = weekly['week'].astype(int)

    weekly = weekly.sort_values(['year', 'week'])

    return weekly


def get_monthly_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate monthly summary statistics"""
    if df.empty:
        return pd.DataFrame()

    monthly = df.groupby('month_key').agg({
        'distance_km': 'sum',
        'id': 'count',
        'avg_hr': 'mean'
    }).reset_index()

    monthly.columns = ['month', 'distance_km', 'runs', 'avg_hr']

    # Calculate avg km per week (rough estimate: 4.33 weeks/month)
    monthly['avg_km_per_week'] = monthly['distance_km'] / 4.33

    # Add status based on avg per week
    monthly['status'] = monthly['avg_km_per_week'].apply(
        lambda x: 'GREEN' if x >= 20 else ('YELLOW' if x >= 15 else 'RED')
    )

    return monthly
