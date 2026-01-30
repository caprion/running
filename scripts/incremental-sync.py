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
GARMIN_CACHE_FILE = TRACKING_DIR / "garmin-cache.json"
BACKUPS_DIR = TRACKING_DIR / "backups"
SESSION_DIR = Path(__file__).parent / ".garth"


class IncrementalSync:
    """Handles incremental syncing of activities into unified cache"""

    def __init__(self, dry_run: bool = False):
        self.garmin_client: Optional[Garmin] = None
        self.unified_data = {}
        self.garmin_data = {}  # For training_status, sleep, hrv, stress
        self.dry_run = dry_run
        self.stats = {
            'added': 0,
            'updated': 0,
            'skipped': 0,
            'total_before': 0,
            'total_after': 0,
            'sleep_records': 0,
            'hrv_records': 0,
            'stress_records': 0
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

    def load_garmin_cache(self) -> bool:
        """Load garmin-cache.json for training_status, sleep, hrv, stress data"""
        if not GARMIN_CACHE_FILE.exists():
            print("[WARN] garmin-cache.json not found, will create new one")
            self.garmin_data = {
                "last_sync": None,
                "activities": [],
                "training_status": {},
                "sleep": [],
                "hrv": [],
                "stress": [],
                "user_profile": {}
            }
            return True

        try:
            with open(GARMIN_CACHE_FILE, 'r', encoding='utf-8') as f:
                self.garmin_data = json.load(f)
            
            sleep_count = len(self.garmin_data.get('sleep', []))
            hrv_count = len(self.garmin_data.get('hrv', []))
            stress_count = len(self.garmin_data.get('stress', []))
            print(f"[LOAD] Loaded garmin-cache: {sleep_count} sleep, {hrv_count} HRV, {stress_count} stress records")
            return True

        except Exception as e:
            print(f"[ERROR] Could not load garmin-cache: {e}")
            return False

    def save_garmin_cache(self) -> bool:
        """Save garmin-cache.json with training_status, sleep, hrv, stress"""
        if self.dry_run:
            print("[DRY-RUN] Would save garmin-cache (skipping)")
            return True

        try:
            self.garmin_data['last_sync'] = datetime.now().isoformat()
            
            with open(GARMIN_CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.garmin_data, f, indent=2, ensure_ascii=False)
            
            print(f"[SAVE] Updated garmin-cache.json")
            return True

        except Exception as e:
            print(f"[ERROR] Could not save garmin-cache: {e}")
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
                                'maxRunCadence': lap.get('maxRunCadence'),
                                'strideLength': lap.get('strideLength'),  # Required for Form page
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

    def fetch_training_status(self) -> Dict:
        """Fetch current training status and metrics"""
        print(f"\n[FETCH] Fetching training status...")

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
                user_summary = self.garmin_client.get_user_summary(date_to_try)
                if user_summary:
                    resting_hr = user_summary.get('restingHeartRate')
                    resting_hr_7d = user_summary.get('lastSevenDaysAvgRestingHeartRate')
                    
                    if resting_hr:
                        status_data['resting_hr'] = resting_hr
                        status_data['resting_hr_7d_avg'] = resting_hr_7d
                        print(f"[INFO] Resting HR: {resting_hr} bpm (7-day avg: {resting_hr_7d} bpm)")
                        break
            except Exception as e:
                continue

        # Try to get VO2max and training status
        for date_to_try in [today, yesterday]:
            try:
                training_status = self.garmin_client.get_training_status(date_to_try)
                if training_status:
                    # Extract VO2max
                    vo2max_obj = training_status.get('mostRecentVO2Max')
                    if vo2max_obj:
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
                        
                        running_vo2 = vo2max_obj.get('running')
                        if running_vo2:
                            if isinstance(running_vo2, dict):
                                status_data['vo2max_running'] = running_vo2.get('value') or running_vo2.get('vo2Max')
                            else:
                                status_data['vo2max_running'] = running_vo2
                        
                        if status_data['vo2max']:
                            print(f"[INFO] VO2max: {status_data['vo2max']}")

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
                            print(f"[INFO] Training Load 7d: {status_data['training_load_7d']}")

                    # Extract training status label
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
                            print(f"[INFO] Training Status: {status_data['training_effect_label']}")

                    if status_data['vo2max'] or status_data['training_load_7d']:
                        break
            except Exception as e:
                continue

        return status_data

    def fetch_sleep(self, days: int = 7) -> List[Dict]:
        """Fetch sleep data from last N days"""
        print(f"\n[FETCH] Fetching sleep data from last {days} days...")

        sleep_data = []
        existing_dates = {s['date'] for s in self.garmin_data.get('sleep', [])}
        
        for i in range(days):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            
            try:
                sleep = self.garmin_client.get_sleep_data(date)
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
                    
                    status = "NEW" if date not in existing_dates else "UPDATE"
                    print(f"[{status}] {date}: {sleep_entry['sleep_hours']}h (score: {sleep_entry['sleep_score']})")
            except Exception:
                continue

        print(f"[FETCH] Retrieved {len(sleep_data)} sleep records")
        self.stats['sleep_records'] = len(sleep_data)
        return sleep_data

    def fetch_hrv(self, days: int = 7) -> List[Dict]:
        """Fetch HRV data from last N days"""
        print(f"\n[FETCH] Fetching HRV data from last {days} days...")

        hrv_data = []
        existing_dates = {h['date'] for h in self.garmin_data.get('hrv', [])}
        
        for i in range(days):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            
            try:
                hrv = self.garmin_client.get_hrv_data(date)
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
                    
                    status = "NEW" if date not in existing_dates else "UPDATE"
                    print(f"[{status}] {date}: {hrv_entry['last_night_avg']}ms (status: {hrv_entry['status']})")
            except Exception:
                continue

        if hrv_data:
            print(f"[FETCH] Retrieved {len(hrv_data)} HRV records")
        else:
            print("[INFO] No HRV data available (may not be supported by your device)")
        
        self.stats['hrv_records'] = len(hrv_data)
        return hrv_data

    def fetch_stress(self, days: int = 7) -> List[Dict]:
        """Fetch stress data from last N days"""
        print(f"\n[FETCH] Fetching stress data from last {days} days...")

        stress_data = []
        existing_dates = {s['date'] for s in self.garmin_data.get('stress', [])}
        
        for i in range(days):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            
            try:
                stress = self.garmin_client.get_stress_data(date)
                if stress:
                    stress_entry = {
                        'date': date,
                        'avg_stress': stress.get('avgStressLevel'),
                        'max_stress': stress.get('maxStressLevel'),
                        'rest_stress': stress.get('restStressAvg'),
                        'activity_stress': stress.get('activityStressAvg'),
                    }
                    
                    # Convert ms to hours for duration fields
                    low_ms = stress.get('lowStressDurationInMs')
                    med_ms = stress.get('mediumStressDurationInMs')
                    high_ms = stress.get('highStressDurationInMs')
                    
                    if low_ms:
                        stress_entry['low_stress_hours'] = round(low_ms / 3600000, 1)
                    if med_ms:
                        stress_entry['medium_stress_hours'] = round(med_ms / 3600000, 1)
                    if high_ms:
                        stress_entry['high_stress_hours'] = round(high_ms / 3600000, 1)
                    
                    stress_data.append(stress_entry)
                    
                    status = "NEW" if date not in existing_dates else "UPDATE"
                    print(f"[{status}] {date}: avg={stress_entry['avg_stress']}, rest={stress_entry['rest_stress']}")
            except Exception:
                continue

        if stress_data:
            print(f"[FETCH] Retrieved {len(stress_data)} stress records")
        else:
            print("[INFO] No stress data available")
        
        self.stats['stress_records'] = len(stress_data)
        return stress_data

    def merge_daily_data(self, new_data: List[Dict], existing_key: str) -> List[Dict]:
        """Merge new daily data (sleep/hrv/stress) into existing, replacing by date"""
        existing = self.garmin_data.get(existing_key, [])
        existing_by_date = {item['date']: item for item in existing}
        
        # Update/add new records
        for item in new_data:
            existing_by_date[item['date']] = item
        
        # Sort by date (newest first)
        merged = sorted(existing_by_date.values(), key=lambda x: x['date'], reverse=True)
        return merged

    def calculate_cadence_pace_analysis(self) -> Dict:
        """Calculate cadence vs pace relationship from lap data"""
        print(f"\n[CALC] Analyzing cadence-pace relationship...")
        
        activities = self.unified_data.get('activities', [])
        
        # Extract lap data
        laps = []
        for act in activities:
            if act.get('type') != 'running':
                continue
            splits = act.get('splits', {})
            lap_list = splits.get('lapDTOs', []) if isinstance(splits, dict) else []
            
            for lap in lap_list:
                cadence = lap.get('averageRunCadence')
                speed = lap.get('averageSpeed', 0)
                distance = lap.get('distance', 0)
                stride = lap.get('strideLength')
                
                if cadence and speed and distance >= 800:
                    pace_min_km = (1000 / speed) / 60 if speed > 0 else 0
                    laps.append({
                        'date': act['date'][:10],
                        'cadence': cadence,
                        'pace_min_km': pace_min_km,
                        'stride_cm': stride
                    })
        
        if len(laps) < 10:
            print("[WARN] Not enough lap data for cadence-pace analysis")
            return {}
        
        # Define pace brackets
        def pace_bracket(pace):
            if pace < 5.0:
                return "1_fast"
            elif pace < 5.5:
                return "2_tempo"
            elif pace < 6.0:
                return "3_moderate"
            elif pace < 6.5:
                return "4_easy"
            elif pace < 7.0:
                return "5_recovery"
            else:
                return "6_very_easy"
        
        # Calculate stats by bracket
        from collections import defaultdict
        bracket_data = defaultdict(lambda: {'cadences': [], 'strides': [], 'paces': []})
        
        for lap in laps:
            bracket = pace_bracket(lap['pace_min_km'])
            bracket_data[bracket]['cadences'].append(lap['cadence'])
            bracket_data[bracket]['paces'].append(lap['pace_min_km'])
            if lap['stride_cm']:
                bracket_data[bracket]['strides'].append(lap['stride_cm'])
        
        bracket_stats = {}
        for bracket, data in bracket_data.items():
            if data['cadences']:
                bracket_stats[bracket] = {
                    'avg_cadence': round(sum(data['cadences']) / len(data['cadences']), 1),
                    'avg_pace': round(sum(data['paces']) / len(data['paces']), 2),
                    'lap_count': len(data['cadences']),
                    'avg_stride_cm': round(sum(data['strides']) / len(data['strides']), 1) if data['strides'] else None
                }
        
        # Calculate regression (pace vs cadence)
        paces = [lap['pace_min_km'] for lap in laps]
        cadences = [lap['cadence'] for lap in laps]
        
        n = len(laps)
        sum_x = sum(paces)
        sum_y = sum(cadences)
        sum_xy = sum(p * c for p, c in zip(paces, cadences))
        sum_x2 = sum(p * p for p in paces)
        sum_y2 = sum(c * c for c in cadences)
        
        # Slope and intercept
        denom = n * sum_x2 - sum_x * sum_x
        if denom != 0:
            slope = (n * sum_xy - sum_x * sum_y) / denom
            intercept = (sum_y - slope * sum_x) / n
        else:
            slope, intercept = 0, 0
        
        # Correlation coefficient
        num = n * sum_xy - sum_x * sum_y
        denom = ((n * sum_x2 - sum_x**2) * (n * sum_y2 - sum_y**2)) ** 0.5
        correlation = num / denom if denom != 0 else 0
        r_squared = correlation ** 2
        
        analysis = {
            'total_laps': len(laps),
            'date_range': {
                'start': min(lap['date'] for lap in laps),
                'end': max(lap['date'] for lap in laps)
            },
            'pace_range': {
                'min': round(min(paces), 2),
                'max': round(max(paces), 2)
            },
            'cadence_range': {
                'min': round(min(cadences), 0),
                'max': round(max(cadences), 0)
            },
            'regression': {
                'slope': round(slope, 2),
                'intercept': round(intercept, 1),
                'correlation': round(correlation, 3),
                'r_squared': round(r_squared, 3)
            },
            'bracket_stats': bracket_stats,
            'lap_data': laps[-200:],  # Store last 200 laps for plotting
            'calculated_at': datetime.now().isoformat()
        }
        
        print(f"[CALC] Analyzed {len(laps)} laps, correlation: {correlation:.3f}")
        print(f"[CALC] Regression: cadence = {slope:.1f} × pace + {intercept:.1f}")
        
        return analysis

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

        # Step 1: Load unified cache (source of truth for activities)
        if not self.load_unified_cache():
            return False

        # Step 1b: Load garmin-cache (for training_status, sleep, hrv, stress)
        if not self.load_garmin_cache():
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

        # Step 5: Fetch training status (current snapshot)
        training_status = self.fetch_training_status()
        self.garmin_data['training_status'] = training_status

        # Step 6: Fetch sleep, HRV, and stress data
        sleep_data = self.fetch_sleep(days)
        hrv_data = self.fetch_hrv(days)
        stress_data = self.fetch_stress(days)

        # Step 7: Merge daily data into garmin-cache
        print(f"\n[MERGE] Merging daily metrics...")
        self.garmin_data['sleep'] = self.merge_daily_data(sleep_data, 'sleep')
        self.garmin_data['hrv'] = self.merge_daily_data(hrv_data, 'hrv')
        self.garmin_data['stress'] = self.merge_daily_data(stress_data, 'stress')

        # Step 8: Calculate cadence-pace analysis (form metrics)
        cadence_pace_analysis = self.calculate_cadence_pace_analysis()
        self.garmin_data['cadence_pace_analysis'] = cadence_pace_analysis

        # Step 9: Safety check for activities
        if not self.safety_check():
            print("\n[ABORT] Safety check failed, not saving changes")
            return False

        # Step 10: Save updated caches
        if not self.save_unified_cache():
            return False
        
        if not self.save_garmin_cache():
            return False

        # Step 11: Print summary
        print("\n" + "=" * 60)
        print("SYNC COMPLETE")
        print("=" * 60)
        print(f"Activities Before:  {self.stats['total_before']}")
        print(f"Activities Added:   {self.stats['added']}")
        print(f"Activities Updated: {self.stats['updated']}")
        print(f"Activities After:   {self.stats['total_after']}")
        print(f"Sleep Records:      {self.stats['sleep_records']}")
        print(f"HRV Records:        {self.stats['hrv_records']}")
        print(f"Stress Records:     {self.stats['stress_records']}")
        print("=" * 60)

        if not self.dry_run:
            print(f"\nActivities saved to: {UNIFIED_CACHE_FILE}")
            print(f"Metrics saved to:    {GARMIN_CACHE_FILE}")
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
