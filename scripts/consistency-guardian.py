#!/usr/bin/env python3
"""
Consistency Guardian - Track running volume and floor violations

Monitors weekly running volume against the 15-20km floor from training plan.
Helps identify patterns of consistency vs collapse across seasons.
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple

# Configuration
CACHE_FILE = Path(__file__).parent.parent / "tracking" / "garmin-cache.json"
FLOOR_THRESHOLD = 15  # km - minimum viable volume
YELLOW_THRESHOLD = 20  # km - transition to "good" volume


def load_activities() -> List[Dict]:
    """Load activities from cache"""
    with open(CACHE_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get('activities', [])


def get_week_key(date_str: str) -> Tuple[int, int]:
    """Convert date string to (year, week_number) tuple"""
    date = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
    # Use ISO week (Monday start) for consistency
    iso_year, iso_week, _ = date.isocalendar()
    return (iso_year, iso_week)


def calculate_weekly_volumes(activities: List[Dict]) -> Dict:
    """Calculate weekly distance and run counts"""
    weekly_data = defaultdict(lambda: {'distance': 0.0, 'runs': 0, 'dates': []})

    for activity in activities:
        if activity.get('type') == 'running':
            week_key = get_week_key(activity['date'])
            weekly_data[week_key]['distance'] += activity['distance_km']
            weekly_data[week_key]['runs'] += 1
            weekly_data[week_key]['dates'].append(activity['date'][:10])

    return weekly_data


def get_week_status(distance: float) -> Tuple[str, str]:
    """Return (status_emoji, status_text) for a given distance"""
    if distance < FLOOR_THRESHOLD:
        return ('❌', 'FLOOR VIOLATION')
    elif distance < YELLOW_THRESHOLD:
        return ('⚠️ ', 'YELLOW')
    else:
        return ('✅', 'GREEN')


def calculate_streak(weekly_data: Dict, year: int) -> int:
    """Calculate current streak of weeks above floor threshold"""
    # Get all weeks for the year, sorted
    year_weeks = sorted([k for k in weekly_data.keys() if k[0] == year], reverse=True)

    streak = 0
    for week_key in year_weeks:
        distance = weekly_data[week_key]['distance']
        if distance >= FLOOR_THRESHOLD:
            streak += 1
        else:
            break

    return streak


def print_weekly_report(weekly_data: Dict, year: int = None):
    """Print detailed weekly volume report"""
    if year:
        weeks = sorted([k for k in weekly_data.keys() if k[0] == year])
        title = f"WEEKLY VOLUME REPORT - {year}"
    else:
        weeks = sorted(weekly_data.keys())
        title = "WEEKLY VOLUME REPORT - ALL TIME"

    print("=" * 70)
    print(title)
    print("=" * 70)
    print(f"{'Week':<12} | {'Runs':>4} | {'Distance':>8} | {'Status':>6} | {'Dates'}")
    print("-" * 70)

    violations = []
    yellow_weeks = []
    green_weeks = []

    for week_key in weeks:
        data = weekly_data[week_key]
        distance = data['distance']
        runs = data['runs']
        dates = ', '.join(sorted(set(data['dates'])))

        status_emoji, status_text = get_week_status(distance)
        week_label = f"{week_key[0]}-W{week_key[1]:02d}"

        print(f"{week_label:<12} | {runs:>4} | {distance:>6.1f}km | {status_emoji} | {dates[:40]}")

        if distance < FLOOR_THRESHOLD:
            violations.append(week_key)
        elif distance < YELLOW_THRESHOLD:
            yellow_weeks.append(week_key)
        else:
            green_weeks.append(week_key)

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Total weeks tracked: {len(weeks)}")
    print(f"  ✅ GREEN weeks (≥{YELLOW_THRESHOLD}km):   {len(green_weeks)} ({len(green_weeks)/len(weeks)*100:.0f}%)")
    print(f"  ⚠️  YELLOW weeks ({FLOOR_THRESHOLD}-{YELLOW_THRESHOLD-1}km): {len(yellow_weeks)} ({len(yellow_weeks)/len(weeks)*100:.0f}%)")
    print(f"  ❌ RED weeks (<{FLOOR_THRESHOLD}km):     {len(violations)} ({len(violations)/len(weeks)*100:.0f}%)")

    if year:
        streak = calculate_streak(weekly_data, year)
        print(f"\n🔥 Current streak (weeks ≥{FLOOR_THRESHOLD}km): {streak} weeks")


def print_comparison(weekly_data: Dict):
    """Compare different time periods"""
    # Separate 2025 and 2026
    data_2025 = {k: v for k, v in weekly_data.items() if k[0] == 2025}
    data_2026 = {k: v for k, v in weekly_data.items() if k[0] == 2026}

    # 2025 split: Jan-Jul vs Aug-Dec
    jan_jul_2025 = {k: v for k, v in data_2025.items() if k[1] <= 27}  # Week 27 ≈ end of June
    aug_dec_2025 = {k: v for k, v in data_2025.items() if k[1] > 27}

    print("\n" + "=" * 70)
    print("PERIOD COMPARISON")
    print("=" * 70)

    periods = [
        ("2025 Jan-Jul (Collapse)", jan_jul_2025),
        ("2025 Aug-Dec (Recovery)", aug_dec_2025),
        ("2026 YTD (Current)", data_2026),
    ]

    print(f"{'Period':<25} | {'Weeks':>5} | {'Total km':>8} | {'Avg/week':>9} | {'Violations':>11}")
    print("-" * 70)

    for period_name, period_data in periods:
        if not period_data:
            continue

        total_weeks = len(period_data)
        total_km = sum(v['distance'] for v in period_data.values())
        avg_per_week = total_km / total_weeks if total_weeks > 0 else 0
        violations = sum(1 for v in period_data.values() if v['distance'] < FLOOR_THRESHOLD)

        print(f"{period_name:<25} | {total_weeks:>5} | {total_km:>7.1f}k | {avg_per_week:>7.1f}km | {violations:>4}/{total_weeks:>2} ({violations/total_weeks*100:>3.0f}%)")


def print_monthly_summary(activities: List[Dict]):
    """Print monthly volume summary"""
    monthly = defaultdict(lambda: {'distance': 0.0, 'runs': 0})

    for activity in activities:
        if activity.get('type') == 'running':
            month_key = activity['date'][:7]  # YYYY-MM
            monthly[month_key]['distance'] += activity['distance_km']
            monthly[month_key]['runs'] += 1

    print("\n" + "=" * 70)
    print("MONTHLY SUMMARY")
    print("=" * 70)
    print(f"{'Month':<10} | {'Runs':>4} | {'Distance':>8} | {'Avg/week':>9}")
    print("-" * 70)

    for month in sorted(monthly.keys()):
        data = monthly[month]
        # Rough estimate: 4.33 weeks per month
        avg_per_week = data['distance'] / 4.33
        status_emoji, _ = get_week_status(avg_per_week)

        print(f"{month:<10} | {data['runs']:>4} | {data['distance']:>6.1f}km | {avg_per_week:>7.1f}km {status_emoji}")


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Analyze running consistency and volume')
    parser.add_argument('--year', type=int, help='Filter to specific year (e.g., 2025)')
    parser.add_argument('--compare', action='store_true', help='Show period comparisons')
    parser.add_argument('--monthly', action='store_true', help='Show monthly summary')

    args = parser.parse_args()

    # Load data
    activities = load_activities()

    if not activities:
        print("❌ No activities found in cache")
        print("   Run: python scripts/sync-garmin.py")
        return 1

    # Calculate weekly volumes
    weekly_data = calculate_weekly_volumes(activities)

    # Print weekly report
    print_weekly_report(weekly_data, year=args.year)

    # Optional comparisons
    if args.compare or not args.year:
        print_comparison(weekly_data)

    # Optional monthly summary
    if args.monthly:
        print_monthly_summary(activities)

    return 0


if __name__ == "__main__":
    sys.exit(main())
