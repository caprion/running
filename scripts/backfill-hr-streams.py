#!/usr/bin/env python3
"""
Backfill HR Streams for Long Runs

Problem: Long runs have HR data but only 1 lap (no per-km splits)
Solution: Fetch HR + distance streams from Garmin and create per-km laps with HR

This script:
1. Finds long runs (>=15km) from last 8 weeks with <=3 laps
2. Fetches HR and distance streams from Garmin API
3. Creates per-km laps with average HR for each km
4. Updates unified-cache.json DIRECTLY (preserves all data)

⚠️ ARCHITECTURE NOTE (Jan 2026):
- This script correctly updates unified-cache.json (single source of truth)
- Creates automatic backups before updating
- Does NOT require rebuild after running
- Safe to run multiple times (only updates activities lacking detailed splits)

Going forward: Enable auto-lap on Garmin watch (1km) to avoid this issue

Usage:
  python scripts/backfill-hr-streams.py

After running:
  - Dashboard will automatically use updated data
  - No need to run build-unified-cache.py (deprecated)
  - HR enrichments are now permanent in unified-cache
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

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

from dotenv import load_dotenv
import os

# Load environment
load_dotenv()

GARMIN_EMAIL = os.getenv("GARMIN_EMAIL")
GARMIN_PASSWORD = os.getenv("GARMIN_PASSWORD")
SESSION_DIR = Path(__file__).parent / ".garth"
UNIFIED_CACHE = Path(__file__).parent.parent / "tracking" / "unified-cache.json"
BACKUP_DIR = Path(__file__).parent.parent / "tracking" / "backups"

# Only process last 8 weeks
WEEKS_TO_PROCESS = 8


class GarminHRStreamFetcher:
    """Fetch HR and distance streams from Garmin for activity analysis"""

    def __init__(self):
        self.client = None
        self._authenticate()

    def _authenticate(self):
        """Authenticate with Garmin Connect using session tokens"""
        # Try to load existing session first
        if self._load_session():
            print("Using saved Garmin session")
            return

        # No valid session - need to login with credentials
        if not GARMIN_EMAIL or not GARMIN_PASSWORD:
            print("Error: GARMIN_EMAIL and GARMIN_PASSWORD must be set in .env file")
            sys.exit(1)

        try:
            print(f"Logging in as {GARMIN_EMAIL}...")
            self.client = Garmin(GARMIN_EMAIL, GARMIN_PASSWORD)
            self.client.login()

            # Save session for future use
            self._save_session()
            print("Authentication successful")

        except GarminConnectAuthenticationError as e:
            print(f"Authentication failed: {e}")
            sys.exit(1)
        except GarminConnectConnectionError as e:
            print(f"Connection error: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"Error authenticating: {e}")
            sys.exit(1)

    def _load_session(self) -> bool:
        """Load and use saved session tokens"""
        if not GARTH_AVAILABLE or not SESSION_DIR.exists() or not list(SESSION_DIR.glob("*")):
            return False

        try:
            garth.configure(domain="garmin.com", garmin_client_id=None)
            garth.resume(str(SESSION_DIR))
            self.client = Garmin()

            # Test if session is still valid
            self.client.get_full_name()
            return True
        except:
            return False

    def _save_session(self):
        """Save session tokens for future use"""
        if not GARTH_AVAILABLE:
            return

        try:
            garth.configure(domain="garmin.com", garmin_client_id=None)
            garth.save(str(SESSION_DIR))
        except:
            pass

    def fetch_activity_streams(self, activity_id: int) -> Optional[Dict]:
        """
        Fetch detailed streams (HR, distance, time) for an activity

        Returns dict with:
          - hr_data: List[int] - heart rate per second
          - distance_data: List[float] - cumulative distance in meters
          - time_data: List[float] - elapsed time in seconds
        """
        try:
            # Fetch activity details with streams using garminconnect's internal API
            url = f"/activity-service/activity/{activity_id}/details"

            try:
                data = self.client.connectapi(url)
            except Exception as e:
                print(f"      API call failed: {e}")
                return None

            if not data:
                print(f"      No data returned from API")
                return None

            # Extract metric descriptors and samples
            metric_descriptors = data.get('metricDescriptors', [])
            activity_detail_metrics = data.get('activityDetailMetrics', [])

            if not metric_descriptors or not activity_detail_metrics:
                print(f"      No stream data available")
                return None

            # Debug: Show available metrics (commented out after initial testing)
            # print(f"      DEBUG: Found {len(metric_descriptors)} metric descriptors")
            # for desc in metric_descriptors:
            #     print(f"        - key={desc.get('key')}, metricsIndex={desc.get('metricsIndex')}, unit={desc.get('unit', {}).get('key')}")

            # Find metric indices by name (metrics is a list, not dict)
            hr_index = None
            distance_index = None

            for desc in metric_descriptors:
                key = desc.get('key')
                index = desc.get('metricsIndex')

                if key == 'directHeartRate':
                    hr_index = index
                elif key == 'sumDistance':
                    distance_index = index

            # print(f"      DEBUG: hr_index={hr_index}, distance_index={distance_index}")

            if hr_index is None or distance_index is None:
                print(f"      Missing HR or distance stream")
                return None

            # Extract values by index (metrics is a list)
            hr_data = []
            distance_data = []

            for metric in activity_detail_metrics:
                metrics = metric.get('metrics', [])

                # metrics is a list, access by index
                if isinstance(metrics, list):
                    if len(metrics) > hr_index:
                        hr_val = metrics[hr_index]
                        hr_data.append(int(hr_val) if hr_val else 0)
                    else:
                        hr_data.append(0)

                    if len(metrics) > distance_index:
                        dist_val = metrics[distance_index]
                        distance_data.append(float(dist_val) if dist_val else 0.0)
                    else:
                        distance_data.append(0.0)

            # Create time data (assume 1 sample per second)
            time_data = list(range(len(hr_data)))

            return {
                'hr_data': hr_data,
                'distance_data': distance_data,
                'time_data': time_data
            }

        except Exception as e:
            print(f"      Error fetching streams: {e}")
            import traceback
            traceback.print_exc()
            return None

    def create_per_km_laps(self, streams: Dict, total_distance: float) -> Optional[List[Dict]]:
        """
        Create per-km laps with average HR from streams

        Args:
            streams: Dict with hr_data, distance_data, time_data
            total_distance: Total activity distance in km

        Returns:
            List of lap dicts with HR data
        """
        hr_data = streams['hr_data']
        distance_data = streams['distance_data']
        time_data = streams['time_data']

        if not hr_data or not distance_data:
            return None

        laps = []
        current_km_mark = 1000.0  # First km mark in meters
        lap_start_idx = 0

        for i, dist_m in enumerate(distance_data):
            # Check if we've crossed the current km mark
            if dist_m >= current_km_mark:
                # Calculate lap metrics
                lap_distance = distance_data[i] - (distance_data[lap_start_idx] if lap_start_idx < len(distance_data) else 0)
                lap_time = time_data[i] - (time_data[lap_start_idx] if lap_start_idx < len(time_data) else 0)

                # Calculate average HR for this lap
                lap_hr_values = [hr for hr in hr_data[lap_start_idx:i+1] if hr > 0]
                avg_hr = sum(lap_hr_values) / len(lap_hr_values) if lap_hr_values else 0

                # Calculate pace (min/km)
                pace_min_per_km = (lap_time / 60.0) / (lap_distance / 1000.0) if lap_distance > 0 else 0

                laps.append({
                    'startDistanceInMeters': distance_data[lap_start_idx] if lap_start_idx < len(distance_data) else 0,
                    'totalDistanceInMeters': lap_distance,
                    'totalTimeInSeconds': lap_time,
                    'averageHR': int(avg_hr) if avg_hr > 0 else None,
                    'paceMinPerKm': round(pace_min_per_km, 2)
                })

                current_km_mark += 1000.0  # Next km mark
                lap_start_idx = i

        return laps if laps else None


def load_unified_cache() -> Dict:
    """Load unified cache"""
    if not UNIFIED_CACHE.exists():
        print(f"❌ Error: Unified cache not found: {UNIFIED_CACHE}")
        print("   Run: python scripts/build-unified-cache.py first")
        sys.exit(1)

    with open(UNIFIED_CACHE, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_unified_cache(data: Dict):
    """Save updated unified cache"""
    # Create backup first
    BACKUP_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = BACKUP_DIR / f"unified-cache-backup-{timestamp}.json"

    if UNIFIED_CACHE.exists():
        with open(UNIFIED_CACHE, 'r') as f_in:
            with open(backup_file, 'w') as f_out:
                f_out.write(f_in.read())
        print(f"✅ Backed up unified cache to: {backup_file}")

    # Save updated cache
    with open(UNIFIED_CACHE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"✅ Saved updated unified cache")


def main():
    print("\n" + "="*70)
    print("ONE-TIME: Backfill HR Streams for Long Runs (Last 8 Weeks)")
    print("="*70 + "\n")

    # Load unified cache
    print("Loading unified cache...")
    cache_data = load_unified_cache()
    activities = cache_data.get('activities', [])
    print(f"✅ Loaded {len(activities)} activities\n")

    # Find long runs in last 8 weeks that need processing
    cutoff = datetime.now() - timedelta(weeks=WEEKS_TO_PROCESS)

    candidates = []
    for activity in activities:
        try:
            act_date = datetime.strptime(activity['date'][:10], '%Y-%m-%d')
            distance = activity.get('distance_km', 0)

            # Only process:
            # 1. Garmin activities (have activity_id for API)
            # 2. Long runs (>=15km)
            # 3. Recent (last 8 weeks)
            # 4. Missing per-km laps (<=3 laps)

            source = activity.get('source', '')
            if 'garmin' not in source:
                continue

            if distance < 15:
                continue

            if act_date < cutoff:
                continue

            splits = activity.get('splits', {})
            lap_count = len(splits.get('lapDTOs', []))

            if lap_count > 3:  # Already has per-km laps
                continue

            candidates.append(activity)

        except Exception:
            continue

    if not candidates:
        print("✅ No long runs need processing - all good!")
        print("   (Either have per-km laps already or outside 8-week window)")
        return

    print(f"Found {len(candidates)} long runs to process:")
    print("-"*70)
    for act in candidates:
        date = act['date'][:10]
        name = act.get('name', 'Unknown')
        distance = act.get('distance_km', 0)
        laps = len(act.get('splits', {}).get('lapDTOs', []))
        print(f"  {date} | {distance:5.1f}km | {laps} laps | {name[:30]}")
    print()

    # Initialize Garmin client
    fetcher = GarminHRStreamFetcher()

    # Process each candidate
    updated_count = 0
    failed_count = 0

    for i, activity in enumerate(candidates, 1):
        date = activity['date'][:10]
        name = activity.get('name', 'Unknown')
        distance = activity.get('distance_km', 0)
        activity_id = activity.get('id')  # Garmin uses 'id' field

        print(f"[{i}/{len(candidates)}] {date} - {name} ({distance:.1f}km)")

        if not activity_id:
            print("      ⚠️  No activity_id, skipping")
            failed_count += 1
            continue

        # Fetch streams
        print(f"      Fetching HR + distance streams...")
        streams = fetcher.fetch_activity_streams(activity_id)

        if not streams:
            print("      ❌ Failed to fetch streams")
            failed_count += 1
            continue

        # Create per-km laps
        print(f"      Creating per-km laps...")
        laps = fetcher.create_per_km_laps(streams, distance)

        if not laps:
            print("      ❌ Failed to create laps")
            failed_count += 1
            continue

        # Update activity
        activity['splits'] = {'lapDTOs': laps}
        activity['splits_source'] = 'garmin_streams'

        print(f"      ✅ Created {len(laps)} laps with HR data")
        updated_count += 1

    # Save updated cache
    print("\n" + "-"*70)
    print(f"Processed: {len(candidates)} long runs")
    print(f"Updated: {updated_count}")
    print(f"Failed: {failed_count}")

    if updated_count > 0:
        print("\nSaving updated cache...")
        save_unified_cache(cache_data)

        print("\n" + "="*70)
        print("✅ Backfill completed!")
        print("="*70)
        print("\n📋 Next steps:")
        print("  1. Refresh dashboard to see HR stability data")
        print("  2. Check Race Confidence page for HR drift charts")
        print("  3. Archive this script (won't be needed again)")
        print("\n💡 Going forward: Enable auto-lap (1km) on Garmin watch")
    else:
        print("\n⚠️  No activities were updated")


if __name__ == "__main__":
    main()
