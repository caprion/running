"""
Build unified cache from multiple data sources

⚠️ WARNING: This script REBUILDS unified-cache from scratch and can cause DATA LOSS! ⚠️

DANGER:
- This script OVERWRITES unified-cache.json completely
- If source caches (garmin-cache, strava-cache) are incomplete, data will be lost
- HR enrichments and manual edits will be erased
- Only use for INITIAL SETUP or DISASTER RECOVERY

For daily/weekly syncs, use: python scripts/incremental-sync.py

Data Sources (in order of preference):
1. Garmin (primary): 2025-03-23 onwards
2. Strava recent splits: Last 8 weeks with detailed lap data
3. Strava historical: 2022-01-01 to 2025-03-22

Output: tracking/unified-cache.json (WILL BE OVERWRITTEN!)
"""

import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict

DATA_DIR = Path(__file__).parent.parent / "tracking"
GARMIN_CACHE = DATA_DIR / "garmin-cache.json"
STRAVA_HISTORICAL = DATA_DIR / "strava-historical-archive.json"
STRAVA_RECENT = DATA_DIR / "strava-recent-splits.json"
UNIFIED_CACHE = DATA_DIR / "unified-cache.json"

# Historical cutoff: Garmin data starts here
GARMIN_START_DATE = "2025-03-23"


def _parse_date(date_str: str) -> datetime:
    """Parse activity date string to datetime"""
    formats = ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%dT%H:%M:%SZ']
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    raise ValueError(f"Could not parse date: {date_str}")


def _activities_match(act1: Dict, act2: Dict) -> bool:
    """Check if two activities are the same (for deduplication)"""
    try:
        date1 = _parse_date(act1['date'])
        date2 = _parse_date(act2['date'])

        # Within 2 hours
        time_diff = abs((date1 - date2).total_seconds())
        if time_diff > 7200:
            return False

        # Distance within 0.1 km
        dist1 = float(act1.get('distance_km', 0) or 0)
        dist2 = float(act2.get('distance_km', 0) or 0)
        dist_diff = abs(dist1 - dist2)

        return dist_diff <= 0.1
    except Exception:
        return False


def load_garmin_data() -> List[Dict]:
    """Load Garmin activities (primary source)"""
    if not GARMIN_CACHE.exists():
        print(f"⚠️  Garmin cache not found: {GARMIN_CACHE}")
        return []

    with open(GARMIN_CACHE) as f:
        data = json.load(f)

    activities = data.get('activities', [])
    print(f"✓ Loaded {len(activities)} Garmin activities")
    return activities


def load_strava_historical() -> List[Dict]:
    """Load historical Strava archive (2022 to Garmin start)"""
    if not STRAVA_HISTORICAL.exists():
        print(f"⚠️  Strava historical archive not found: {STRAVA_HISTORICAL}")
        return []

    with open(STRAVA_HISTORICAL) as f:
        data = json.load(f)

    activities = data.get('activities', [])
    print(f"✓ Loaded {len(activities)} Strava historical activities")
    return activities


def load_strava_recent() -> List[Dict]:
    """Load recent Strava activities with splits (last 8 weeks)"""
    if not STRAVA_RECENT.exists():
        print(f"⚠️  Strava recent splits not found: {STRAVA_RECENT}")
        return []

    with open(STRAVA_RECENT) as f:
        data = json.load(f)

    activities = data.get('activities', [])
    print(f"✓ Loaded {len(activities)} Strava recent activities (with splits)")
    return activities


def merge_all_sources(garmin: List[Dict], strava_historical: List[Dict],
                      strava_recent: List[Dict]) -> List[Dict]:
    """
    Merge activities from all sources with intelligent deduplication

    Priority:
    1. Garmin (most recent, has lap data)
    2. Strava recent splits (8-week transition period)
    3. Strava historical (archived data before Garmin)

    Strategy:
    - Use Garmin as primary for 2025-03-23 onwards
    - Fill gaps with Strava recent (for activities without Garmin match)
    - Use Strava historical for everything before Garmin start date
    """

    merged = []
    strava_recent_matched = set()
    strava_historical_matched = set()

    # Start with all Garmin activities
    for garmin_act in garmin:
        garmin_act['source'] = 'garmin'
        garmin_act['data_quality'] = 'primary'

        # Check for matching Strava recent activity (to copy splits if needed)
        for i, strava_act in enumerate(strava_recent):
            if i in strava_recent_matched:
                continue

            if _activities_match(garmin_act, strava_act):
                garmin_act['source'] = 'both'
                garmin_act['strava_id'] = strava_act.get('strava_id')

                # Copy Strava-specific fields
                if 'suffer_score' in strava_act and strava_act['suffer_score']:
                    garmin_act['suffer_score'] = strava_act['suffer_score']

                # If Garmin doesn't have splits but Strava does, use Strava splits
                if not garmin_act.get('splits') and strava_act.get('splits'):
                    garmin_act['splits'] = strava_act['splits']
                    garmin_act['splits_source'] = 'strava'

                strava_recent_matched.add(i)
                break

        merged.append(garmin_act)

    # Add Strava recent activities that don't match any Garmin activity
    for i, strava_act in enumerate(strava_recent):
        if i not in strava_recent_matched:
            strava_act['source'] = 'strava'
            strava_act['data_quality'] = 'recent_splits'
            merged.append(strava_act)

    # Add all historical Strava activities (before Garmin start date)
    garmin_start = datetime.strptime(GARMIN_START_DATE, '%Y-%m-%d')
    for hist_act in strava_historical:
        try:
            act_date = _parse_date(hist_act['date'])

            # Only include if before Garmin start date
            if act_date < garmin_start:
                hist_act['source'] = 'strava'
                hist_act['data_quality'] = 'historical'
                merged.append(hist_act)
        except Exception:
            # If can't parse date, include it anyway (likely old data)
            hist_act['source'] = 'strava'
            hist_act['data_quality'] = 'historical'
            merged.append(hist_act)

    # Sort by date (most recent first)
    merged.sort(key=lambda x: x.get('date', ''), reverse=True)

    return merged


def build_unified_cache():
    """Build unified cache from all sources"""
    print("\n" + "="*60)
    print("Building Unified Cache")
    print("="*60 + "\n")

    # Load all sources
    print("Loading data sources...")
    garmin = load_garmin_data()
    strava_historical = load_strava_historical()
    strava_recent = load_strava_recent()

    print(f"\nMerging {len(garmin)} Garmin + {len(strava_recent)} Strava recent + {len(strava_historical)} Strava historical...")

    # Merge all sources
    merged = merge_all_sources(garmin, strava_historical, strava_recent)

    # Build unified cache structure
    unified_data = {
        "last_sync": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "build_date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "sources": {
            "garmin": len([a for a in merged if 'garmin' in a.get('source', '')]),
            "strava_recent": len([a for a in merged if a.get('data_quality') == 'recent_splits']),
            "strava_historical": len([a for a in merged if a.get('data_quality') == 'historical']),
            "duplicates_merged": len(garmin) + len(strava_recent) - len([a for a in merged if a.get('source') == 'both'])
        },
        "activities": merged,
        "metadata": {
            "garmin_start_date": GARMIN_START_DATE,
            "total_activities": len(merged),
            "date_range": {
                "first": merged[-1]['date'][:10] if merged else None,
                "last": merged[0]['date'][:10] if merged else None
            }
        }
    }

    # Write unified cache
    with open(UNIFIED_CACHE, 'w') as f:
        json.dump(unified_data, f, indent=2)

    print(f"\n✓ Unified cache built successfully!")
    print(f"  Output: {UNIFIED_CACHE}")
    print(f"  Total activities: {len(merged)}")
    print(f"  Garmin: {unified_data['sources']['garmin']}")
    print(f"  Strava recent: {unified_data['sources']['strava_recent']}")
    print(f"  Strava historical: {unified_data['sources']['strava_historical']}")
    print(f"  Date range: {unified_data['metadata']['date_range']['first']} to {unified_data['metadata']['date_range']['last']}")
    print(f"\n✓ Dashboard will now use: {UNIFIED_CACHE}")


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("⚠️  WARNING: UNIFIED CACHE REBUILD - DATA LOSS RISK ⚠️")
    print("=" * 70)
    print("\nThis script will OVERWRITE unified-cache.json by rebuilding from source caches.")
    print("\nDANGERS:")
    print("  - If garmin-cache.json is incomplete, you will LOSE Garmin activities")
    print("  - HR enrichments from backfill-hr-streams.py will be ERASED")
    print("  - Manual edits to unified-cache will be LOST")
    print("\nBefore proceeding:")
    print("  1. Check garmin-cache.json has complete history (not just 3-7 days)")
    print("  2. Verify: python -c \"import json; print(len(json.load(open('tracking/garmin-cache.json'))['activities']))\"")
    print("  3. Expected: ~85+ activities (not 3-7)")
    print("\nFor daily/weekly syncs, use instead:")
    print("  python scripts/incremental-sync.py")
    print("\n" + "=" * 70)

    confirm = input("\nType 'REBUILD' (all caps) to continue, or anything else to abort: ")

    if confirm != "REBUILD":
        print("\n❌ Rebuild aborted. No changes made.")
        print("   Use: python scripts/incremental-sync.py for safe incremental updates")
        exit(1)

    print("\n⚠️  Proceeding with rebuild...\n")
    build_unified_cache()
