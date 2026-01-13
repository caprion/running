"""
Create frozen Strava historical archive

One-time script to split existing strava-cache.json into:
1. Historical archive (2022-01-01 to 2025-03-22) - FROZEN
2. Keep recent data in strava-cache.json for reference

This is a one-time migration. After this:
- Historical archive is READ-ONLY
- Use sync-strava-recent.py for last 8 weeks
- Use sync-garmin.py for primary data
"""

import json
from pathlib import Path
from datetime import datetime
import shutil

DATA_DIR = Path(__file__).parent.parent / "tracking"
STRAVA_CACHE = DATA_DIR / "strava-cache.json"
STRAVA_HISTORICAL = DATA_DIR / "strava-historical-archive.json"
BACKUP_DIR = DATA_DIR / "backups"

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


def create_archive():
    """Create frozen historical archive from existing Strava cache"""
    print("\n" + "="*60)
    print("Creating Strava Historical Archive")
    print("="*60 + "\n")

    # Check if strava-cache.json exists
    if not STRAVA_CACHE.exists():
        print(f"❌ Error: {STRAVA_CACHE} not found!")
        print("   Run sync-strava.py first to fetch Strava data.")
        return

    # Create backup directory
    BACKUP_DIR.mkdir(exist_ok=True)

    # Backup existing strava-cache.json
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = BACKUP_DIR / f"strava-cache-backup-{timestamp}.json"
    shutil.copy2(STRAVA_CACHE, backup_file)
    print(f"✓ Backed up existing cache to: {backup_file}")

    # Load existing cache
    with open(STRAVA_CACHE) as f:
        strava_data = json.load(f)

    activities = strava_data.get('activities', [])
    print(f"✓ Loaded {len(activities)} Strava activities")

    # Split by date
    cutoff_date = datetime.strptime(GARMIN_START_DATE, '%Y-%m-%d')

    historical = []
    recent = []

    for activity in activities:
        try:
            act_date = _parse_date(activity['date'])

            if act_date < cutoff_date:
                historical.append(activity)
            else:
                recent.append(activity)
        except Exception as e:
            print(f"⚠️  Could not parse date for activity: {activity.get('name', 'Unknown')} - {e}")
            # If can't parse, assume it's historical
            historical.append(activity)

    print(f"\nSplit results:")
    print(f"  Historical (before {GARMIN_START_DATE}): {len(historical)} activities")
    print(f"  Recent (after {GARMIN_START_DATE}): {len(recent)} activities")

    # Create historical archive
    archive_data = {
        "created_date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "cutoff_date": GARMIN_START_DATE,
        "source": "strava",
        "status": "FROZEN - READ ONLY",
        "note": "Historical archive before Garmin sync started. Do not modify.",
        "last_sync": strava_data.get('last_sync'),
        "activities": historical,
        "metadata": {
            "total_activities": len(historical),
            "date_range": {
                "first": min(a['date'][:10] for a in historical) if historical else None,
                "last": max(a['date'][:10] for a in historical) if historical else None
            }
        }
    }

    # Write historical archive
    with open(STRAVA_HISTORICAL, 'w') as f:
        json.dump(archive_data, f, indent=2)

    print(f"\n✓ Historical archive created successfully!")
    print(f"  Output: {STRAVA_HISTORICAL}")
    print(f"  Status: FROZEN (READ-ONLY)")
    print(f"  Activities: {len(historical)}")
    print(f"  Date range: {archive_data['metadata']['date_range']['first']} to {archive_data['metadata']['date_range']['last']}")

    print(f"\n📋 Next steps:")
    print(f"  1. Run: python scripts/sync-strava-recent.py (fetch last 8 weeks with splits)")
    print(f"  2. Run: python scripts/build-unified-cache.py (create merged cache)")
    print(f"  3. Dashboard will automatically use unified-cache.json")
    print(f"\n⚠️  Note: strava-cache.json is no longer used by the dashboard")


if __name__ == "__main__":
    create_archive()
