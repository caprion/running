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
USE_SAMPLE_DATA = os.getenv("USE_SAMPLE_DATA", "false").lower() == "true"
DATA_DIR = "sample-data" if USE_SAMPLE_DATA else "tracking"

# Path to cache files
BASE_DIR = Path(__file__).parent.parent.parent
GARMIN_CACHE_FILE = BASE_DIR / DATA_DIR / "garmin-cache.json"
UNIFIED_CACHE_FILE = BASE_DIR / DATA_DIR / "unified-cache.json"

if USE_SAMPLE_DATA:
    print(f"Using SAMPLE DATA from {DATA_DIR}/")
else:
    print(f"Using PERSONAL DATA from {DATA_DIR}/")


def load_garmin_data() -> Dict:
    """Load all data from Garmin cache"""
    if not GARMIN_CACHE_FILE.exists():
        return {"activities": [], "training_status": {}, "sleep": [], "last_sync": None}

    with open(GARMIN_CACHE_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_activities() -> List[Dict]:
    """
    Load activities from unified cache (preferred) or Garmin cache

    Priority:
    1. Use unified-cache.json if it exists (pre-merged, fastest)
    2. Fall back to garmin-cache.json

    Returns:
        List of activities
    """
    if UNIFIED_CACHE_FILE.exists():
        try:
            with open(UNIFIED_CACHE_FILE, 'r', encoding='utf-8') as f:
                unified_data = json.load(f)
                return unified_data.get('activities', [])
        except Exception as e:
            print(f"Warning: Could not load unified cache: {e}")

    # Fall back to Garmin cache
    garmin_data = load_garmin_data()
    activities = garmin_data.get('activities', [])
    for act in activities:
        act['source'] = 'garmin'
    return activities


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


def get_cadence_pace_analysis() -> Dict:
    """Get pre-calculated cadence vs pace analysis"""
    data = load_garmin_data()
    return data.get('cadence_pace_analysis', {})


def get_last_sync_time() -> Optional[str]:
    """Get last sync timestamp from unified cache or Garmin cache"""
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

    garmin_data = load_garmin_data()
    garmin_sync = garmin_data.get('last_sync')
    if garmin_sync:
        dt = datetime.fromisoformat(garmin_sync)
        return f"Garmin: {dt.strftime('%Y-%m-%d %H:%M')}"
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
