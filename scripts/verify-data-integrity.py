#!/usr/bin/env python3
"""
Data Integrity Verification Script

Monitors unified-cache.json to ensure no data loss occurs.
Run this after each sync to verify data integrity.

Checks:
1. Activity count (should never decrease)
2. Garmin activity count and date range
3. HR data completeness
4. Long runs HR enrichment
5. Source distribution

Usage:
  python scripts/verify-data-integrity.py
  python scripts/verify-data-integrity.py --baseline  # Save current state as baseline
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List

TRACKING_DIR = Path(__file__).parent.parent / "tracking"
UNIFIED_CACHE = TRACKING_DIR / "unified-cache.json"
BASELINE_FILE = TRACKING_DIR / ".data-integrity-baseline.json"


def load_unified_cache() -> Dict:
    """Load unified cache"""
    if not UNIFIED_CACHE.exists():
        print(f"[ERROR] Unified cache not found: {UNIFIED_CACHE}")
        sys.exit(1)

    with open(UNIFIED_CACHE, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_baseline() -> Dict:
    """Load baseline snapshot"""
    if not BASELINE_FILE.exists():
        return None

    with open(BASELINE_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_baseline(stats: Dict):
    """Save current state as baseline"""
    baseline = {
        'timestamp': datetime.now().isoformat(),
        'stats': stats
    }

    with open(BASELINE_FILE, 'w', encoding='utf-8') as f:
        json.dump(baseline, f, indent=2)

    print(f"\n[BASELINE] Saved to: {BASELINE_FILE}")


def analyze_activities(activities: List[Dict]) -> Dict:
    """Analyze activity statistics"""
    stats = {
        'total': len(activities),
        'by_source': {},
        'garmin_count': 0,
        'garmin_date_range': {'first': None, 'last': None},
        'with_hr': 0,
        'with_splits_hr': 0,
        'long_runs_total': 0,
        'long_runs_with_hr': 0,
        'long_runs_with_splits_hr': 0,
    }

    # Count by source
    for a in activities:
        source = a.get('source', 'unknown')
        stats['by_source'][source] = stats['by_source'].get(source, 0) + 1

    # Garmin activities
    garmin_activities = [a for a in activities if 'garmin' in a.get('source', '')]
    stats['garmin_count'] = len(garmin_activities)

    if garmin_activities:
        garmin_sorted = sorted(garmin_activities, key=lambda x: x.get('date', ''))
        stats['garmin_date_range']['first'] = garmin_sorted[0].get('date', '')[:10]
        stats['garmin_date_range']['last'] = garmin_sorted[-1].get('date', '')[:10]

    # HR data
    stats['with_hr'] = len([a for a in activities if a.get('avg_hr')])

    # Per-km splits HR
    for a in activities:
        if a.get('splits', {}).get('lapDTOs'):
            laps = a['splits']['lapDTOs']
            if any(lap.get('averageHR') for lap in laps):
                stats['with_splits_hr'] += 1

    # Long runs (>=15km) analysis
    long_runs = [a for a in activities if a.get('distance_km', 0) >= 15]
    stats['long_runs_total'] = len(long_runs)

    for lr in long_runs:
        if lr.get('avg_hr'):
            stats['long_runs_with_hr'] += 1

        if lr.get('splits', {}).get('lapDTOs'):
            laps = lr['splits']['lapDTOs']
            if any(lap.get('averageHR') for lap in laps):
                stats['long_runs_with_splits_hr'] += 1

    return stats


def print_stats(stats: Dict, title: str = "Current State"):
    """Print statistics"""
    print(f"\n{'='*70}")
    print(f"{title}")
    print('='*70)

    print(f"\nTotal activities: {stats['total']}")
    print(f"By source: {stats['by_source']}")

    print(f"\nGarmin activities: {stats['garmin_count']}")
    if stats['garmin_count'] > 0:
        print(f"  Date range: {stats['garmin_date_range']['first']} to {stats['garmin_date_range']['last']}")

    print(f"\nHR Data:")
    hr_pct = 100 * stats['with_hr'] / stats['total'] if stats['total'] > 0 else 0
    print(f"  Activities with HR: {stats['with_hr']} / {stats['total']} ({hr_pct:.1f}%)")

    splits_pct = 100 * stats['with_splits_hr'] / stats['total'] if stats['total'] > 0 else 0
    print(f"  Activities with per-km HR: {stats['with_splits_hr']} / {stats['total']} ({splits_pct:.1f}%)")

    print(f"\nLong Runs (>=15km):")
    print(f"  Total: {stats['long_runs_total']}")
    print(f"  With HR: {stats['long_runs_with_hr']} / {stats['long_runs_total']}")
    print(f"  With per-km HR: {stats['long_runs_with_splits_hr']} / {stats['long_runs_total']}")


def compare_with_baseline(current: Dict, baseline: Dict) -> bool:
    """Compare current stats with baseline and flag issues"""
    print(f"\n{'='*70}")
    print("Comparison with Baseline")
    print('='*70)

    print(f"\nBaseline timestamp: {baseline['timestamp']}")

    baseline_stats = baseline['stats']
    issues_found = False

    # Check 1: Total activities should never decrease
    if current['total'] < baseline_stats['total']:
        print(f"\n❌ CRITICAL: Total activities DECREASED!")
        print(f"   Baseline: {baseline_stats['total']} -> Current: {current['total']}")
        print(f"   Lost: {baseline_stats['total'] - current['total']} activities")
        issues_found = True
    elif current['total'] > baseline_stats['total']:
        print(f"\n✅ Total activities INCREASED")
        print(f"   Baseline: {baseline_stats['total']} -> Current: {current['total']}")
        print(f"   Added: {current['total'] - baseline_stats['total']} activities")
    else:
        print(f"\n✅ Total activities unchanged: {current['total']}")

    # Check 2: Garmin activities should not decrease
    if current['garmin_count'] < baseline_stats['garmin_count']:
        print(f"\n❌ WARNING: Garmin activities DECREASED!")
        print(f"   Baseline: {baseline_stats['garmin_count']} -> Current: {current['garmin_count']}")
        print(f"   Lost: {baseline_stats['garmin_count'] - current['garmin_count']} Garmin activities")
        issues_found = True
    elif current['garmin_count'] > baseline_stats['garmin_count']:
        print(f"\n✅ Garmin activities INCREASED")
        print(f"   Baseline: {baseline_stats['garmin_count']} -> Current: {current['garmin_count']}")
        print(f"   Added: {current['garmin_count'] - baseline_stats['garmin_count']} activities")
    else:
        print(f"\n✅ Garmin activities unchanged: {current['garmin_count']}")

    # Check 3: HR data should not decrease
    if current['with_hr'] < baseline_stats['with_hr']:
        print(f"\n❌ WARNING: Activities with HR DECREASED!")
        print(f"   Baseline: {baseline_stats['with_hr']} -> Current: {current['with_hr']}")
        print(f"   Lost HR data for {baseline_stats['with_hr'] - current['with_hr']} activities")
        issues_found = True
    else:
        print(f"\n✅ HR data maintained or increased")
        print(f"   Baseline: {baseline_stats['with_hr']} -> Current: {current['with_hr']}")

    # Check 4: Per-km HR splits should not decrease
    if current['with_splits_hr'] < baseline_stats['with_splits_hr']:
        print(f"\n❌ WARNING: Per-km HR splits DECREASED!")
        print(f"   Baseline: {baseline_stats['with_splits_hr']} -> Current: {current['with_splits_hr']}")
        print(f"   Lost splits for {baseline_stats['with_splits_hr'] - current['with_splits_hr']} activities")
        issues_found = True
    else:
        print(f"\n✅ Per-km HR splits maintained or increased")
        print(f"   Baseline: {baseline_stats['with_splits_hr']} -> Current: {current['with_splits_hr']}")

    return issues_found


def main():
    """Main verification workflow"""
    parser = argparse.ArgumentParser(
        description='Verify data integrity of unified-cache.json',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/verify-data-integrity.py              # Check current state
  python scripts/verify-data-integrity.py --baseline   # Save as baseline
        """
    )
    parser.add_argument(
        '--baseline',
        action='store_true',
        help='Save current state as baseline for future comparisons'
    )

    args = parser.parse_args()

    # Load unified cache
    cache_data = load_unified_cache()
    activities = cache_data.get('activities', [])

    # Analyze current state
    current_stats = analyze_activities(activities)

    # Print current stats
    print_stats(current_stats)

    # Save baseline if requested
    if args.baseline:
        save_baseline(current_stats)
        print("\n✅ Baseline saved. Run this script without --baseline to compare future syncs.")
        return 0

    # Compare with baseline if it exists
    baseline = load_baseline()
    if baseline:
        issues_found = compare_with_baseline(current_stats, baseline)

        if issues_found:
            print(f"\n{'='*70}")
            print("❌ DATA INTEGRITY ISSUES DETECTED!")
            print('='*70)
            print("\nRecommended actions:")
            print("  1. Check: ls -lh tracking/backups/unified-cache-*.json")
            print("  2. Restore from backup if needed:")
            print("     cp tracking/backups/unified-cache-YYYYMMDD_HHMMSS.json tracking/unified-cache.json")
            print("  3. Investigate what caused the data loss")
            return 1
        else:
            print(f"\n{'='*70}")
            print("✅ All integrity checks passed!")
            print('='*70)
            return 0
    else:
        print(f"\n{'='*70}")
        print("No baseline found. Run with --baseline to create one:")
        print("  python scripts/verify-data-integrity.py --baseline")
        print('='*70)
        return 0


if __name__ == "__main__":
    sys.exit(main())
