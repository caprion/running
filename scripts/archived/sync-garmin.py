#!/usr/bin/env python3
"""
Garmin Connect Data Sync Script
Pulls training data from Garmin Connect and caches it locally
"""

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

from dotenv import load_dotenv
from garminconnect import Garmin, GarminConnectAuthenticationError, GarminConnectConnectionError

try:
    import garth
    GARTH_AVAILABLE = True
except ImportError:
    GARTH_AVAILABLE = False

# Load environment variables
load_dotenv()

# Configuration
GARMIN_EMAIL = os.getenv("GARMIN_EMAIL")
GARMIN_PASSWORD = os.getenv("GARMIN_PASSWORD")
CACHE_DIR = Path(__file__).parent.parent / "tracking"
CACHE_FILE = CACHE_DIR / "garmin-cache.json"
SESSION_FILE = Path(__file__).parent / ".garmin_session.json"


class GarminSync:
    """Handles syncing data from Garmin Connect"""

    def __init__(self):
        self.client: Optional[Garmin] = None
        self.data = {
            "last_sync": None,
            "activities": [],
            "training_status": {},
            "sleep": [],
            "hrv": [],
            "user_profile": {}
        }
        # Load existing cache to preserve historical data
        self.load_cache()

    def load_cache(self):
        """Load existing cache file if it exists to preserve historical data"""
        if CACHE_FILE.exists():
            try:
                with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
                    self.data = existing_data
                    print(f"[CACHE] Loaded existing cache: {len(self.data.get('activities', []))} activities")
            except Exception as e:
                print(f"[WARN] Could not load existing cache: {e}")
                print("       Starting with fresh cache")

    def authenticate(self) -> bool:
        """Authenticate with Garmin Connect using session tokens"""

        # Try to load existing session first
        if self._load_session():
            print(" Using saved session")
            return True

        # No valid session - need to login with credentials
        if not GARMIN_EMAIL or not GARMIN_PASSWORD:
            print(" Error: GARMIN_EMAIL and GARMIN_PASSWORD must be set in .env file")
            print("   Copy .env.example to .env and fill in your credentials")
            print("   These are only needed for the first login to create a session.")
            return False

        try:
            print(f" No saved session found. Logging in as {GARMIN_EMAIL}...")
            self.client = Garmin(GARMIN_EMAIL, GARMIN_PASSWORD)
            self.client.login()

            # Save session for future use
            self._save_session()
            print(" Authentication successful and session saved")
            print(f"   Future syncs will use the saved session (no password needed)")

            return True

        except GarminConnectAuthenticationError as e:
            print(f" Authentication failed: {e}")
            print("   Check your email/password in .env file")
            return False

        except GarminConnectConnectionError as e:
            print(f" Connection error: {e}")
            print("   Check your internet connection")
            return False

        except Exception as e:
            print(f" Unexpected error during authentication: {e}")
            return False

    def _load_session(self) -> bool:
        """Load and use saved session tokens"""
        session_dir = SESSION_FILE.parent / ".garth"

        # Check if session directory exists and has files
        if not session_dir.exists() or not list(session_dir.glob("*")):
            return False

        try:
            # Configure garth to use our session directory
            garth.configure(domain="garmin.com")

            # Try to resume the session
            garth.resume(str(session_dir))

            # Create Garmin client (will use garth's session automatically)
            self.client = Garmin()

            # Test if session is still valid
            try:
                self.client.get_full_name()
                print(" Loaded saved session successfully")
                return True
            except:
                print("  Saved session expired, will re-authenticate...")
                # Clean up expired session
                import shutil
                shutil.rmtree(session_dir, ignore_errors=True)
                return False

        except Exception as e:
            print(f"  Could not load session: {e}")
            # Clean up corrupted session
            import shutil
            shutil.rmtree(session_dir, ignore_errors=True)
            return False

    def _save_session(self) -> bool:
        """Save session tokens for future use"""
        try:
            session_dir = SESSION_FILE.parent / ".garth"
            session_dir.mkdir(exist_ok=True)

            # Save garth session
            garth.save(str(session_dir))

            print(f" Session saved to {session_dir}")
            return True

        except Exception as e:
            print(f"  Could not save session: {e}")
            return False

    def fetch_activities(self, days: int = 7) -> List[Dict]:
        """Fetch activities from last N days"""
        print(f"\n Fetching activities from last {days} days...")

        activities = []
        try:
            # Get activities
            raw_activities = self.client.get_activities(0, days * 2)  # Fetch more to ensure we get enough

            cutoff_date = datetime.now() - timedelta(days=days)

            for activity in raw_activities:
                activity_date = datetime.strptime(activity['startTimeLocal'], '%Y-%m-%d %H:%M:%S')

                if activity_date < cutoff_date:
                    continue

                # Get detailed activity data
                activity_id = activity['activityId']

                try:
                    # Basic activity info
                    activity_data = {
                        'id': activity_id,
                        'name': activity.get('activityName'),
                        'type': activity.get('activityType', {}).get('typeKey'),
                        'date': activity['startTimeLocal'],
                        'distance_km': round(activity.get('distance', 0) / 1000, 2),
                        'duration_seconds': activity.get('duration'),
                        'elevation_gain_m': activity.get('elevationGain'),
                        'avg_hr': activity.get('averageHR'),
                        'max_hr': activity.get('maxHR'),
                        'calories': activity.get('calories'),
                        'avg_pace_min_km': self._meters_per_sec_to_min_per_km(activity.get('averageSpeed')),
                    }

                    # Try to get splits/laps
                    try:
                        splits = self.client.get_activity_splits(activity_id)
                        activity_data['splits'] = splits
                    except:
                        activity_data['splits'] = None

                    # Try to get HR zones
                    try:
                        hr_zones = self.client.get_activity_hr_in_timezones(activity_id)
                        activity_data['hr_zones'] = hr_zones
                    except:
                        activity_data['hr_zones'] = None

                    activities.append(activity_data)
                    print(f"   {activity_data['date']}: {activity_data['name']} - {activity_data['distance_km']}km")

                except Exception as e:
                    print(f"    Could not fetch details for activity {activity_id}: {e}")
                    continue

            print(f" Fetched {len(activities)} activities")
            return activities

        except Exception as e:
            print(f" Error fetching activities: {e}")
            return []

    def fetch_training_status(self) -> Dict:
        """Fetch current training status and metrics"""
        print("\n Fetching training status...")

        today = datetime.now().strftime('%Y-%m-%d')
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        status_data = {
            'vo2max': None,
            'vo2max_running': None,
            'training_load_7d': None,
            'training_load_28d': None,
            'training_effect_label': None,
            'recovery_time_hours': None,
            'resting_hr': None,
            'resting_hr_7d_avg': None,
            'fetched_at': datetime.now().isoformat()
        }

        # Try to get data from user summary (try today first, then yesterday)
        for date_to_try in [today, yesterday]:
            try:
                print(f"   Trying get_user_summary() for {date_to_try}...")
                user_summary = self.client.get_user_summary(date_to_try)

                if user_summary:
                    # Extract resting HR
                    resting_hr = user_summary.get('restingHeartRate')
                    resting_hr_7d = user_summary.get('lastSevenDaysAvgRestingHeartRate')
                    
                    if resting_hr:
                        status_data['resting_hr'] = resting_hr
                        status_data['resting_hr_7d_avg'] = resting_hr_7d
                        print(f"   Resting HR: {resting_hr} bpm (7-day avg: {resting_hr_7d} bpm)")
                        break  # Got data, no need to try yesterday
                    elif date_to_try == today:
                        print(f"   No resting HR for today, trying yesterday...")

            except Exception as e:
                print(f"    get_user_summary({date_to_try}) failed: {type(e).__name__}: {e}")

        # Try to get VO2max and training status (try today first, then yesterday)
        for date_to_try in [today, yesterday]:
            try:
                print(f"   Trying get_training_status() for {date_to_try}...")
                training_status = self.client.get_training_status(date_to_try)

                if training_status:
                    # Extract VO2max from nested object
                    vo2max_obj = training_status.get('mostRecentVO2Max')
                    if vo2max_obj:
                        # Try 'generic' for running VO2max
                        generic_vo2 = vo2max_obj.get('generic')
                        if generic_vo2:
                            if isinstance(generic_vo2, dict):
                                status_data['vo2max'] = (
                                    generic_vo2.get('vo2MaxValue') or
                                    generic_vo2.get('vo2MaxPreciseValue') or
                                    generic_vo2.get('value')
                                )
                            else:
                                status_data['vo2max'] = generic_vo2

                        # Try 'running' if it exists
                        running_vo2 = vo2max_obj.get('running')
                        if running_vo2:
                            if isinstance(running_vo2, dict):
                                status_data['vo2max_running'] = running_vo2.get('value') or running_vo2.get('vo2Max')
                            else:
                                status_data['vo2max_running'] = running_vo2

                        if status_data['vo2max'] or status_data['vo2max_running']:
                            print(f"   VO2max: {status_data['vo2max']} (Running: {status_data['vo2max_running']})")

                    # Extract training load
                    load_balance = training_status.get('mostRecentTrainingLoadBalance')
                    if load_balance:
                        metrics_map = load_balance.get('metricsTrainingLoadBalanceDTOMap')
                        if metrics_map and isinstance(metrics_map, dict):
                            for key, value in metrics_map.items():
                                if isinstance(value, dict):
                                    status_data['training_load_7d'] = value.get('sevenDayAvgLoad')
                                    status_data['training_load_28d'] = value.get('twentyEightDayAvgLoad')
                                    break

                        if status_data['training_load_7d']:
                            print(f"   Training Load 7d: {status_data['training_load_7d']}")

                    # Extract training status
                    training_status_obj = training_status.get('mostRecentTrainingStatus')
                    if training_status_obj:
                        latest_data = training_status_obj.get('latestTrainingStatusData')
                        if latest_data and isinstance(latest_data, dict):
                            for device_id, device_data in latest_data.items():
                                if isinstance(device_data, dict):
                                    status_data['training_effect_label'] = device_data.get('trainingStatusFeedbackPhrase')
                                    
                                    if not status_data['training_effect_label']:
                                        numeric_status = device_data.get('trainingStatus')
                                        status_map = {
                                            1: 'Detraining', 2: 'Recovery', 3: 'Maintaining',
                                            4: 'Productive', 5: 'Peaking', 6: 'Overreaching',
                                            7: 'Unproductive', 8: 'No Status', 9: 'Recovery'
                                        }
                                        status_data['training_effect_label'] = status_map.get(numeric_status, f'Unknown ({numeric_status})')

                                    status_data['recovery_time_hours'] = device_data.get('recoveryTimeInHours')
                                    
                                    if not status_data['training_load_7d']:
                                        status_data['training_load_7d'] = device_data.get('weeklyTrainingLoad')
                                    break

                        if status_data['training_effect_label']:
                            print(f"   Training Status: {status_data['training_effect_label']}")
                        if status_data['recovery_time_hours']:
                            print(f"   Recovery Time: {status_data['recovery_time_hours']}h")

                    # If we got meaningful data, stop trying other dates
                    if status_data['vo2max'] or status_data['training_load_7d'] or status_data['training_effect_label']:
                        break
                    elif date_to_try == today:
                        print(f"   No training data for today, trying yesterday...")

            except Exception as e:
                print(f"    get_training_status({date_to_try}) failed: {type(e).__name__}: {e}")

        # Check if we got any data
        if any(v for k, v in status_data.items() if k != 'fetched_at'):
            print(" Training status fetch completed (partial data)")
        else:
            print(" No training status data available")
            print("   This may be normal if:")
            print("   - Your watch needs to sync recent activities")
            print("   - VO2max requires more training history")
            print("   - Garmin needs time to calculate training load")

        return status_data

    def fetch_sleep(self, days: int = 7) -> List[Dict]:
        """Fetch sleep data from last N days"""
        print(f"\n Fetching sleep data from last {days} days...")

        sleep_data = []
        try:
            for i in range(days):
                date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')

                try:
                    sleep = self.client.get_sleep_data(date)

                    if sleep and 'dailySleepDTO' in sleep:
                        sleep_dto = sleep['dailySleepDTO']
                        sleep_entry = {
                            'date': date,
                            'sleep_seconds': sleep_dto.get('sleepTimeSeconds'),
                            'sleep_hours': round(sleep_dto.get('sleepTimeSeconds', 0) / 3600, 1),
                            'deep_sleep_seconds': sleep_dto.get('deepSleepSeconds'),
                            'light_sleep_seconds': sleep_dto.get('lightSleepSeconds'),
                            'rem_sleep_seconds': sleep_dto.get('remSleepSeconds'),
                            'awake_seconds': sleep_dto.get('awakeSleepSeconds'),
                            'sleep_score': sleep_dto.get('sleepScores', {}).get('overall', {}).get('value'),
                        }
                        sleep_data.append(sleep_entry)
                        print(f"   {date}: {sleep_entry['sleep_hours']}h (score: {sleep_entry['sleep_score']})")

                except Exception as e:
                    print(f"    No sleep data for {date}")
                    continue

            print(f" Fetched {len(sleep_data)} sleep records")
            return sleep_data

        except Exception as e:
            print(f" Error fetching sleep: {e}")
            return []

    def fetch_hrv(self, days: int = 7) -> List[Dict]:
        """Fetch HRV data from last N days"""
        print(f"\n  Fetching HRV data from last {days} days...")

        hrv_data = []
        try:
            for i in range(days):
                date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')

                try:
                    hrv = self.client.get_hrv_data(date)

                    if hrv and 'hrvSummary' in hrv:
                        hrv_summary = hrv['hrvSummary']
                        hrv_entry = {
                            'date': date,
                            'weekly_avg': hrv_summary.get('weeklyAvg'),
                            'last_night_avg': hrv_summary.get('lastNightAvg'),
                            'last_night_5min_high': hrv_summary.get('lastNight5MinHigh'),
                            'status': hrv_summary.get('status'),
                        }
                        hrv_data.append(hrv_entry)
                        print(f"   {date}: {hrv_entry['last_night_avg']}ms (status: {hrv_entry['status']})")

                except Exception as e:
                    # HRV not available for all users/dates
                    continue

            if hrv_data:
                print(f" Fetched {len(hrv_data)} HRV records")
            else:
                print("  No HRV data available (may not be supported by your device)")

            return hrv_data

        except Exception as e:
            print(f"  HRV data not available: {e}")
            return []

    def fetch_stress(self, days: int = 7) -> List[Dict]:
        """Fetch stress data from last N days (useful recovery metric)"""
        print(f"\n Fetching stress data from last {days} days...")

        stress_data = []
        try:
            for i in range(days):
                date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')

                try:
                    stress = self.client.get_stress_data(date)

                    if stress:
                        stress_entry = {
                            'date': date,
                            'avg_stress': stress.get('avgStressLevel'),
                            'max_stress': stress.get('maxStressLevel'),
                            'rest_stress': stress.get('restStressAvg'),
                            'activity_stress': stress.get('activityStressAvg'),
                            'low_stress_pct': stress.get('lowStressDurationInMs'),
                            'medium_stress_pct': stress.get('mediumStressDurationInMs'),
                            'high_stress_pct': stress.get('highStressDurationInMs'),
                        }
                        # Convert ms to hours for readability
                        for key in ['low_stress_pct', 'medium_stress_pct', 'high_stress_pct']:
                            if stress_entry[key]:
                                stress_entry[key.replace('_pct', '_hours')] = round(stress_entry[key] / 3600000, 1)
                                del stress_entry[key]

                        stress_data.append(stress_entry)
                        print(f"   {date}: avg={stress_entry['avg_stress']}, rest={stress_entry['rest_stress']}")

                except Exception as e:
                    continue

            if stress_data:
                print(f" Fetched {len(stress_data)} stress records")
            else:
                print("  No stress data available")

            return stress_data

        except Exception as e:
            print(f"  Stress data not available: {e}")
            return []

    def download_fit_file(self, activity_id: int, output_dir: Path = None) -> Optional[Path]:
        """Download original FIT file for an activity"""
        if output_dir is None:
            output_dir = CACHE_DIR / "fit_files"

        output_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Download in ORIGINAL format (FIT file)
            fit_data = self.client.download_activity(
                activity_id,
                dl_fmt=Garmin.ActivityDownloadFormat.ORIGINAL
            )

            # The response is a ZIP file containing the FIT file
            import zipfile
            import io

            # Extract FIT file from ZIP
            zip_buffer = io.BytesIO(fit_data)
            with zipfile.ZipFile(zip_buffer, 'r') as zf:
                fit_filename = [n for n in zf.namelist() if n.endswith('.fit')][0]
                fit_content = zf.read(fit_filename)

            # Save FIT file
            output_path = output_dir / f"{activity_id}.fit"
            with open(output_path, 'wb') as f:
                f.write(fit_content)

            return output_path

        except Exception as e:
            print(f"    Could not download FIT file: {e}")
            return None

    def download_recent_fit_files(self, days: int = 7) -> List[Path]:
        """Download FIT files for recent activities"""
        print(f"\n Downloading FIT files for activities...")

        downloaded = []
        fit_dir = CACHE_DIR / "fit_files"

        for activity in self.data.get('activities', []):
            activity_id = activity['id']
            fit_path = fit_dir / f"{activity_id}.fit"

            # Skip if already downloaded
            if fit_path.exists():
                print(f"    {activity['date']}: Already downloaded")
                downloaded.append(fit_path)
                continue

            print(f"    {activity['date']}: {activity['name']}...")
            path = self.download_fit_file(activity_id)
            if path:
                downloaded.append(path)
                print(f"       Saved to {path.name}")

        print(f" {len(downloaded)} FIT files available")
        return downloaded

    def fetch_user_profile(self) -> Dict:
        """Fetch user profile info"""
        print("\n Fetching user profile...")

        try:
            profile = self.client.get_user_profile()

            profile_data = {
                'display_name': profile.get('displayName'),
                'age': profile.get('age'),
                'gender': profile.get('gender'),
                'weight_kg': profile.get('weight') / 1000 if profile.get('weight') else None,
                'height_cm': profile.get('height'),
            }

            print(f"   Profile: {profile_data['display_name']}")
            return profile_data

        except Exception as e:
            print(f" Error fetching profile: {e}")
            return {}

    def sync_all(self, days: int = 7, download_fit: bool = False) -> bool:
        """Sync all data from Garmin Connect"""
        print("=" * 60)
        print("GARMIN CONNECT DATA SYNC")
        print("=" * 60)

        if not self.authenticate():
            return False

        # Fetch new data
        new_activities = self.fetch_activities(days)
        new_sleep = self.fetch_sleep(days)
        new_hrv = self.fetch_hrv(days)
        new_stress = self.fetch_stress(days)

        # Merge with existing data (preserves historical records)
        print("\n[MERGE] Merging with existing cache...")
        self.data['activities'] = self._merge_activities(new_activities)
        self.data['sleep'] = self._merge_time_series(new_sleep, 'sleep', 'date')
        self.data['hrv'] = self._merge_time_series(new_hrv, 'hrv', 'date')
        self.data['stress'] = self._merge_time_series(new_stress, 'stress', 'date')

        # These are always updated to latest
        self.data['training_status'] = self.fetch_training_status()
        self.data['user_profile'] = self.fetch_user_profile()
        self.data['last_sync'] = datetime.now().isoformat()

        # Download FIT files if requested
        if download_fit:
            self.download_recent_fit_files(days)

        # Save to cache
        self.save_cache()

        print("\n" + "=" * 60)
        print("SYNC COMPLETE")
        print("=" * 60)
        print(f" Data cached to: {CACHE_FILE}")
        print(f" Activities: {len(self.data['activities'])}")
        print(f" Sleep records: {len(self.data['sleep'])}")
        print(f"  HRV records: {len(self.data['hrv'])}")
        print(f" Stress records: {len(self.data.get('stress', []))}")

        return True

    def save_cache(self):
        """Save data to cache file"""
        CACHE_DIR.mkdir(exist_ok=True)
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)

    def _merge_activities(self, new_activities: List[Dict]) -> List[Dict]:
        """Merge new activities with existing ones, avoiding duplicates"""
        existing = self.data.get('activities', [])
        existing_ids = {a['id'] for a in existing}

        # Add new activities that don't exist yet
        added = 0
        for new_act in new_activities:
            if new_act['id'] not in existing_ids:
                existing.append(new_act)
                added += 1

        # Sort by date (newest first)
        existing.sort(key=lambda x: x['date'], reverse=True)

        print(f"   Merged: {added} new activities added, {len(new_activities) - added} already existed")
        return existing

    def _merge_time_series(self, new_data: List[Dict], field_name: str, date_key: str = 'date') -> List[Dict]:
        """Merge time-series data (sleep, hrv, stress) by date"""
        existing = self.data.get(field_name, [])
        existing_dates = {item[date_key] for item in existing if date_key in item}

        # Add new records that don't exist yet
        added = 0
        for new_item in new_data:
            if date_key in new_item and new_item[date_key] not in existing_dates:
                existing.append(new_item)
                added += 1

        # Sort by date (newest first)
        existing.sort(key=lambda x: x.get(date_key, ''), reverse=True)

        print(f"   Merged {field_name}: {added} new records added")
        return existing

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
    import argparse

    parser = argparse.ArgumentParser(description='Sync data from Garmin Connect')
    parser.add_argument('days', nargs='?', type=int, default=7,
                       help='Number of days to sync (default: 7)')
    parser.add_argument('--fit', '-f', action='store_true',
                       help='Also download FIT files for activities')

    args = parser.parse_args()

    # Run sync
    syncer = GarminSync()
    success = syncer.sync_all(days=args.days, download_fit=args.fit)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
