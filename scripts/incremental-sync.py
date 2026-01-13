#!/usr/bin/env python3
"""
Incremental Data Sync - NEW ARCHITECTURE

This script MERGES activities incrementally into unified-cache.json
NEVER rebuilds from scratch - preserves all historical data and HR enrichments

Architecture:
- unified-cache.json = Single Source of Truth
- Garmin Connect API = Source for new activities
- Always merge, never overwrite

Usage:
  python scripts/incremental-sync.py              # Fetch last 7 days from Garmin
  python scripts/incremental-sync.py --days 30    # Fetch last 30 days
  python scripts/incremental-sync.py --dry-run    # Test without saving
"""

import argparse
import json
import os
import shutil
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from dotenv import load_dotenv

try:
    from garminconnect import Garmin, GarminConnectAuthenticationError, GarminConnectConnectionError
except ImportError:
    print("Error: garminconnect library not found")
    print("Install: pip install garminconnect")
    sys.exit(1)

try:
    import garth
    GARTH_AVAILABLE = True
except ImportError:
    GARTH_AVAILABLE = False

# Load environment
load_dotenv()

# Configuration
GARMIN_EMAIL = os.getenv("GARMIN_EMAIL")
GARMIN_PASSWORD = os.getenv("GARMIN_PASSWORD")
TRACKING_DIR = Path(__file__).parent.parent / "tracking"
UNIFIED_CACHE_FILE = TRACKING_DIR / "unified-cache.json"
BACKUPS_DIR = TRACKING_DIR / "backups"
SESSION_DIR = Path(__file__).parent / ".garth"


class IncrementalSync:
    """Handles incremental syncing of activities into unified cache"""

    def __init__(self, dry_run: bool = False):
        self.garmin_client: Optional[Garmin] = None
        self.unified_data = {}
        self.dry_run = dry_run
        self.stats = {
            'added': 0,
            'updated': 0,
            'skipped': 0,
            'total_before': 0,
            'total_after': 0
        }

    def load_unified_cache(self) -> bool:
        """Load unified cache (source of truth)"""
        if not UNIFIED_CACHE_FILE.exists():
            print("[ERROR] unified-cache.json not found!")
            print(f"Expected location: {UNIFIED_CACHE_FILE}")
            print("\nThis is the first run. Please create an initial unified-cache first:")
            print("  1. Run: python scripts/sync-garmin.py 365")
            print("  2. Run: python scripts/build-unified-cache.py")
            print("  3. Then use this script for incremental updates")
            return False

        try:
            with open(UNIFIED_CACHE_FILE, 'r', encoding='utf-8') as f:
                self.unified_data = json.load(f)

            activity_count = len(self.unified_data.get('activities', []))
            self.stats['total_before'] = activity_count

            print(f"[LOAD] Loaded unified-cache: {activity_count} activities")

            # Show sources breakdown
            sources = {}
            for a in self.unified_data.get('activities', []):
                s = a.get('source', 'unknown')
                sources[s] = sources.get(s, 0) + 1
            print(f"[INFO] By source: {sources}")

            return True

        except Exception as e:
            print(f"[ERROR] Could not load unified-cache: {e}")
            return False

    def save_unified_cache(self) -> bool:
        """Save unified cache with automatic backup"""
        if self.dry_run:
            print("[DRY-RUN] Would save unified-cache (skipping)")
            return True

        try:
            # Create backup before saving
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = BACKUPS_DIR / f"unified-cache-{timestamp}.json"

            BACKUPS_DIR.mkdir(exist_ok=True)
            shutil.copy(UNIFIED_CACHE_FILE, backup_file)
            print(f"[BACKUP] Created: {backup_file.name}")

            # Update metadata
            self.unified_data['last_sync'] = datetime.now().isoformat()
            self.unified_data['sync_method'] = 'incremental'

            # Write updated cache
            with open(UNIFIED_CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.unified_data, f, indent=2, ensure_ascii=False)

            print(f"[SAVE] Updated unified-cache: {self.stats['total_after']} activities")
            return True

        except Exception as e:
            print(f"[ERROR] Could not save unified-cache: {e}")
            return False

    def authenticate_garmin(self) -> bool:
        """Authenticate with Garmin Connect"""
        # Try to load existing session first
        if SESSION_DIR.exists() and list(SESSION_DIR.glob("*")):
            try:
                garth.resume(str(SESSION_DIR))
                self.garmin_client = Garmin()
                self.garmin_client.get_full_name()  # Test session
                print("[AUTH] Using saved Garmin session")
                return True
            except:
                print("[WARN] Saved session expired, re-authenticating...")
                shutil.rmtree(SESSION_DIR, ignore_errors=True)

        # No valid session - need credentials
        if not GARMIN_EMAIL or not GARMIN_PASSWORD:
            print("[ERROR] GARMIN_EMAIL and GARMIN_PASSWORD must be set in .env file")
            return False

        try:
            print(f"[AUTH] Logging in as {GARMIN_EMAIL}...")
            self.garmin_client = Garmin(GARMIN_EMAIL, GARMIN_PASSWORD)
            self.garmin_client.login()

            # Save session
            SESSION_DIR.mkdir(exist_ok=True)
            garth.save(str(SESSION_DIR))
            print("[AUTH] Authentication successful, session saved")
            return True

        except Exception as e:
            print(f"[ERROR] Authentication failed: {e}")
            return False

    def fetch_garmin_activities(self, days: int = 7) -> List[Dict]:
        """Fetch recent activities from Garmin"""
        print(f"\n[FETCH] Fetching last {days} days from Garmin...")

        activities = []
        try:
            raw_activities = self.garmin_client.get_activities(0, days * 2)
            cutoff_date = datetime.now() - timedelta(days=days)

            for activity in raw_activities:
                activity_date = datetime.strptime(activity['startTimeLocal'], '%Y-%m-%d %H:%M:%S')

                if activity_date < cutoff_date:
                    continue

                if activity['activityType']['typeKey'] != 'running':
                    continue

                # Extract activity data
                act_data = {
                    'id': activity['activityId'],
                    'name': activity['activityName'],
                    'type': 'running',
                    'date': activity['startTimeLocal'],
                    'distance_km': round(activity['distance'] / 1000, 2),
                    'duration_seconds': activity['duration'],
                    'avg_pace_min_km': self._meters_per_sec_to_min_per_km(activity.get('averageSpeed')),
                    'elevation_gain_m': activity.get('elevationGain'),
                    'avg_hr': activity.get('averageHR'),
                    'max_hr': activity.get('maxHR'),
                    'calories': activity.get('calories'),
                    'avg_cadence': activity.get('averageRunningCadenceInStepsPerMinute'),
                }

                # Fetch detailed splits (lap data with per-km HR)
                try:
                    splits = self.garmin_client.get_activity_splits(activity['activityId'])
                    if splits and 'lapDTOs' in splits:
                        act_data['splits'] = {
                            'activityId': activity['activityId'],
                            'lapDTOs': []
                        }

                        for lap in splits['lapDTOs']:
                            lap_data = {
                                'lapIndex': lap.get('lapIndex'),
                                'distance': lap.get('distance'),
                                'duration': lap.get('duration'),
                                'averageSpeed': lap.get('averageSpeed'),
                                'averageHR': lap.get('averageHR'),
                                'maxHR': lap.get('maxHR'),
                                'averageRunCadence': lap.get('averageRunCadence'),
                            }
                            act_data['splits']['lapDTOs'].append(lap_data)

                except Exception as e:
                    print(f"[WARN] Could not fetch splits for activity {activity['activityId']}: {e}")

                activities.append(act_data)

            print(f"[FETCH] Retrieved {len(activities)} running activities")
            return activities

        except Exception as e:
            print(f"[ERROR] Failed to fetch Garmin activities: {e}")
            return []

    def _activities_match(self, act1: Dict, act2: Dict) -> bool:
        """Check if two activities represent the same run"""
        try:
            date1 = datetime.strptime(act1['date'], '%Y-%m-%d %H:%M:%S')
            date2 = datetime.strptime(act2['date'], '%Y-%m-%d %H:%M:%S')

            # Must be within 2 hours
            time_diff = abs((date1 - date2).total_seconds())
            if time_diff > 7200:
                return False

            # Must be within 0.1 km distance
            dist1 = act1.get('distance_km', 0)
            dist2 = act2.get('distance_km', 0)
            dist_diff = abs(dist1 - dist2)

            return dist_diff <= 0.1

        except:
            return False

    def merge_activity_fields(self, existing: Dict, new: Dict) -> Dict:
        """Merge new activity data into existing, preserving important fields"""
        merged = existing.copy()

        # Preserve HR data if new activity lacks it but existing has it
        if not new.get('avg_hr') and existing.get('avg_hr'):
            pass  # Keep existing HR
        else:
            merged['avg_hr'] = new.get('avg_hr') or existing.get('avg_hr')

        if not new.get('max_hr') and existing.get('max_hr'):
            pass  # Keep existing max HR
        else:
            merged['max_hr'] = new.get('max_hr') or existing.get('max_hr')

        # Preserve per-km splits if new lacks them
        if not new.get('splits') and existing.get('splits'):
            pass  # Keep existing splits
        else:
            merged['splits'] = new.get('splits') or existing.get('splits')

        # Update other fields from new activity
        for key in ['name', 'distance_km', 'duration_seconds', 'avg_pace_min_km',
                    'elevation_gain_m', 'calories', 'avg_cadence']:
            if key in new:
                merged[key] = new[key]

        # Update source to 'both' if it was Garmin and now getting Strava data
        if existing.get('source') == 'garmin' and new.get('source') == 'strava':
            merged['source'] = 'both'

        return merged

    def merge_activities_incremental(self, new_activities: List[Dict], source: str = 'garmin') -> None:
        """Merge new activities into unified cache (incremental, never overwrites)"""
        existing_activities = self.unified_data.get('activities', [])

        # Build ID index for fast lookup
        if source == 'garmin':
            existing_by_id = {a.get('id'): (i, a) for i, a in enumerate(existing_activities) if a.get('id')}
        else:
            existing_by_id = {a.get('strava_id'): (i, a) for i, a in enumerate(existing_activities) if a.get('strava_id')}

        for new_act in new_activities:
            new_act['source'] = source

            # Check if activity already exists by ID
            activity_id = new_act.get('id') if source == 'garmin' else new_act.get('strava_id')

            if activity_id and activity_id in existing_by_id:
                # Activity exists by ID - update it
                idx, existing = existing_by_id[activity_id]
                merged = self.merge_activity_fields(existing, new_act)
                existing_activities[idx] = merged
                self.stats['updated'] += 1
                print(f"[UPDATE] Activity {activity_id} ({new_act['date'][:10]})")
                continue

            # Check if activity matches by date + distance
            matched = False
            for i, existing in enumerate(existing_activities):
                if self._activities_match(existing, new_act):
                    # Found matching activity
                    merged = self.merge_activity_fields(existing, new_act)

                    # Add cross-reference IDs
                    if source == 'garmin' and 'strava_id' in existing:
                        merged['strava_id'] = existing['strava_id']
                    elif source == 'strava' and 'id' in existing:
                        merged['id'] = existing['id']

                    existing_activities[i] = merged
                    self.stats['updated'] += 1
                    print(f"[MATCH] Activity {new_act['date'][:10]} ({new_act['distance_km']}km)")
                    matched = True
                    break

            if not matched:
                # New activity - add it
                existing_activities.append(new_act)
                self.stats['added'] += 1
                print(f"[ADD] New activity {new_act['date'][:10]} ({new_act['distance_km']}km)")

        # Sort by date (newest first)
        existing_activities.sort(key=lambda x: x.get('date', ''), reverse=True)

        self.unified_data['activities'] = existing_activities
        self.stats['total_after'] = len(existing_activities)

    def safety_check(self) -> bool:
        """Verify sync didn't lose data"""
        before = self.stats['total_before']
        after = self.stats['total_after']
        added = self.stats['added']

        # Rule 1: Total should never decrease (unless explicit delete)
        if after < before:
            print(f"\n[CRITICAL] Activity count DECREASED! {before} -> {after}")
            print("This indicates data loss. Sync aborted.")
            return False

        # Rule 2: Added + updated should roughly match increase
        expected = before + added
        if after != expected:
            # This is just a warning - might happen with duplicates
            print(f"\n[WARN] Count mismatch. Expected {expected}, got {after}")
            print("This may be normal if duplicates were merged.")

        return True

    def run(self, days: int = 7) -> bool:
        """Main sync workflow"""
        print("=" * 60)
        print("INCREMENTAL SYNC - NEW ARCHITECTURE")
        print("=" * 60)

        if self.dry_run:
            print("[DRY-RUN] Test mode - no changes will be saved")

        # Step 1: Load unified cache (source of truth)
        if not self.load_unified_cache():
            return False

        # Step 2: Authenticate with Garmin
        if not self.authenticate_garmin():
            return False

        # Step 3: Fetch recent Garmin activities
        garmin_activities = self.fetch_garmin_activities(days)
        if not garmin_activities:
            print("[WARN] No Garmin activities fetched")

        # Step 4: Merge Garmin activities
        print(f"\n[MERGE] Merging {len(garmin_activities)} Garmin activities...")
        self.merge_activities_incremental(garmin_activities, source='garmin')

        # Step 5: Safety check
        if not self.safety_check():
            print("\n[ABORT] Safety check failed, not saving changes")
            return False

        # Step 6: Save updated cache
        if not self.save_unified_cache():
            return False

        # Step 7: Print summary
        print("\n" + "=" * 60)
        print("SYNC COMPLETE")
        print("=" * 60)
        print(f"Before:  {self.stats['total_before']} activities")
        print(f"Added:   {self.stats['added']} new activities")
        print(f"Updated: {self.stats['updated']} existing activities")
        print(f"After:   {self.stats['total_after']} activities")
        print("=" * 60)

        if not self.dry_run:
            print(f"\nData saved to: {UNIFIED_CACHE_FILE}")
            print("Dashboard will automatically use updated data")

        return True

    @staticmethod
    def _meters_per_sec_to_min_per_km(mps: Optional[float]) -> Optional[str]:
        """Convert m/s to min/km pace"""
        if not mps or mps == 0:
            return None
        min_per_km = 1000 / (mps * 60)
        minutes = int(min_per_km)
        seconds = int((min_per_km - minutes) * 60)
        return f"{minutes}:{seconds:02d}"


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Incremental sync - merge new activities into unified cache',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/incremental-sync.py              # Fetch last 7 days
  python scripts/incremental-sync.py --days 30    # Fetch last 30 days
  python scripts/incremental-sync.py --dry-run    # Test without saving
        """
    )
    parser.add_argument(
        '--days',
        type=int,
        default=7,
        help='Number of days to sync from Garmin (default: 7)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Test mode - fetch and merge but don\'t save changes'
    )

    args = parser.parse_args()

    # Run sync
    syncer = IncrementalSync(dry_run=args.dry_run)
    success = syncer.run(days=args.days)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
