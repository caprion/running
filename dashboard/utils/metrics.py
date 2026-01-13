"""
Metrics calculation utilities
"""

from datetime import datetime
from typing import Dict, List, Tuple
import pandas as pd


# Thresholds
FLOOR_THRESHOLD = 15  # km
YELLOW_THRESHOLD = 20  # km


def get_status(distance: float) -> Tuple[str, str]:
    """Return (status_name, color) for a given distance"""
    if distance < FLOOR_THRESHOLD:
        return ('RED', '#ff4b4b')
    elif distance < YELLOW_THRESHOLD:
        return ('YELLOW', '#ffa500')
    else:
        return ('GREEN', '#00cc00')


def calculate_streak(weekly_df: pd.DataFrame, year: int = None) -> int:
    """Calculate current streak of weeks above floor threshold"""
    if weekly_df.empty:
        return 0

    # Filter to year if specified
    if year:
        weekly_df = weekly_df[weekly_df['year'] == year]

    # Sort by date (descending - most recent first)
    weekly_df = weekly_df.sort_values(['year', 'week'], ascending=False)

    streak = 0
    for _, row in weekly_df.iterrows():
        if row['distance_km'] >= FLOOR_THRESHOLD:
            streak += 1
        else:
            break

    return streak


def calculate_period_stats(df: pd.DataFrame, start_date: str, end_date: str) -> Dict:
    """Calculate statistics for a specific period"""
    period_df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]

    if period_df.empty:
        return {
            'total_runs': 0,
            'total_km': 0,
            'avg_km_per_week': 0,
            'weeks': 0,
            'violations': 0
        }

    # Calculate weekly volumes
    weekly = period_df.groupby('week_key')['distance_km'].sum()
    total_weeks = len(weekly)
    violations = sum(weekly < FLOOR_THRESHOLD)

    return {
        'total_runs': len(period_df),
        'total_km': period_df['distance_km'].sum(),
        'avg_km_per_week': period_df['distance_km'].sum() / total_weeks if total_weeks > 0 else 0,
        'weeks': total_weeks,
        'violations': violations,
        'violation_pct': (violations / total_weeks * 100) if total_weeks > 0 else 0
    }


def get_pace_in_seconds(pace_str: str) -> float:
    """Convert pace string (M:SS) to seconds per km"""
    if not pace_str or pace_str == 'None':
        return 0

    parts = pace_str.split(':')
    if len(parts) == 2:
        minutes = int(parts[0])
        seconds = int(parts[1])
        return minutes * 60 + seconds
    return 0


def seconds_to_pace(seconds: float) -> str:
    """Convert seconds per km to M:SS format"""
    if seconds == 0:
        return '0:00'

    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f'{minutes}:{secs:02d}'


def find_race_pace_segments(activities: List[Dict], target_pace_min: float, target_pace_max: float) -> pd.DataFrame:
    """
    Find all km splits within target race pace range

    Args:
        activities: List of activity dicts
        target_pace_min: Min pace in seconds/km (e.g., 5:35 = 335s)
        target_pace_max: Max pace in seconds/km (e.g., 5:45 = 345s)

    Returns:
        DataFrame with race pace segments
    """
    segments = []

    for activity in activities:
        if not activity.get('splits'):
            continue

        lap_dtos = activity['splits'].get('lapDTOs', [])
        for lap in lap_dtos:
            # Convert m/s to seconds per km
            avg_speed = lap.get('averageSpeed')
            if not avg_speed or avg_speed == 0:
                continue

            # pace (s/km) = 1000 meters / (meters/second)
            pace_seconds = 1000 / avg_speed

            # Check if within target range
            if target_pace_min <= pace_seconds <= target_pace_max:
                segments.append({
                    'date': activity['date'],
                    'activity_name': activity['name'],
                    'distance': lap.get('distance', 0) / 1000,  # Convert to km
                    'pace_seconds': pace_seconds,
                    'pace_str': seconds_to_pace(pace_seconds),
                    'avg_hr': lap.get('averageHR'),
                    'cadence': lap.get('averageRunCadence')
                })

    return pd.DataFrame(segments)


def calculate_pace_degradation(activity: Dict) -> float:
    """
    Calculate pace degradation (% slower in last 25% vs first 25%)

    Returns negative if speeding up (negative split)
    """
    if not activity.get('splits'):
        return 0

    lap_dtos = activity['splits'].get('lapDTOs', [])
    if len(lap_dtos) < 4:
        return 0

    # Get first 25% and last 25% splits
    first_quarter_count = max(1, len(lap_dtos) // 4)
    last_quarter_count = max(1, len(lap_dtos) // 4)

    first_splits = lap_dtos[:first_quarter_count]
    last_splits = lap_dtos[-last_quarter_count:]

    # Calculate average pace
    first_avg_speed = sum(s.get('averageSpeed', 0) for s in first_splits) / len(first_splits)
    last_avg_speed = sum(s.get('averageSpeed', 0) for s in last_splits) / len(last_splits)

    if first_avg_speed == 0:
        return 0

    # Speed decrease = pace degradation
    # If last_avg_speed < first_avg_speed, you slowed down (positive degradation)
    degradation_pct = ((first_avg_speed - last_avg_speed) / first_avg_speed) * 100

    return degradation_pct
