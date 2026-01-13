#!/usr/bin/env python3
"""
Strava Data Sync Script
Pulls historical training data from Strava and caches it locally
"""

import json
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
STRAVA_CLIENT_ID = os.getenv("STRAVA_CLIENT_ID")
STRAVA_CLIENT_SECRET = os.getenv("STRAVA_CLIENT_SECRET")
STRAVA_REFRESH_TOKEN = os.getenv("STRAVA_REFRESH_TOKEN")
CACHE_DIR = Path(__file__).parent.parent / "tracking"
CACHE_FILE = CACHE_DIR / "strava-cache.json"
TOKEN_FILE = Path(__file__).parent / ".strava_tokens.json"


class StravaSync:
    """Handles syncing data from Strava"""

    def __init__(self):
        self.access_token: Optional[str] = None
        self.data = {
            "last_sync": None,
            "activities": [],
            "athlete_profile": {}
        }
        self._load_existing_cache()

    def _load_existing_cache(self):
        """Load existing cache file if it exists"""
        if CACHE_FILE.exists():
            try:
                with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                    existing = json.load(f)
                    self.data = existing
                    print(f"📂 Loaded existing cache with {len(self.data.get('activities', []))} activities")
            except Exception as e:
                print(f"⚠️  Could not load existing cache: {e}")
                print("   Starting fresh")

    def authenticate(self) -> bool:
        """Authenticate with Strava using OAuth2 token refresh"""

        if not STRAVA_CLIENT_ID or not STRAVA_CLIENT_SECRET or not STRAVA_REFRESH_TOKEN:
            print("❌ Error: STRAVA_CLIENT_ID, STRAVA_CLIENT_SECRET, and STRAVA_REFRESH_TOKEN must be set in .env file")
            print("   Copy .env.example to .env and fill in your Strava API credentials")
            return False

        # Try to load existing access token
        if self._load_access_token():
            print("✅ Using saved access token")
            return True

        # Refresh the access token
        return self._refresh_access_token()

    def _load_access_token(self) -> bool:
        """Load saved access token if it's still valid"""
        if not TOKEN_FILE.exists():
            return False

        try:
            with open(TOKEN_FILE, 'r') as f:
                token_data = json.load(f)

            # Check if token is expired (with 5-minute buffer)
            expires_at = token_data.get('expires_at', 0)
            if expires_at > time.time() + 300:
                self.access_token = token_data['access_token']
                print(f"🔓 Loaded saved token (expires at {datetime.fromtimestamp(expires_at).strftime('%Y-%m-%d %H:%M:%S')})")
                return True
            else:
                print("⚠️  Saved token expired, refreshing...")
                return False

        except Exception as e:
            print(f"⚠️  Could not load token: {e}")
            return False

    def _refresh_access_token(self) -> bool:
        """Refresh the access token using refresh token"""
        print("🔐 Refreshing access token...")

        try:
            response = requests.post(
                "https://www.strava.com/oauth/token",
                data={
                    "client_id": STRAVA_CLIENT_ID,
                    "client_secret": STRAVA_CLIENT_SECRET,
                    "grant_type": "refresh_token",
                    "refresh_token": STRAVA_REFRESH_TOKEN
                }
            )

            if response.status_code != 200:
                print(f"❌ Token refresh failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False

            token_data = response.json()
            self.access_token = token_data['access_token']

            # Save tokens for future use
            token_file_data = {
                'access_token': token_data['access_token'],
                'refresh_token': token_data.get('refresh_token', STRAVA_REFRESH_TOKEN),
                'expires_at': token_data['expires_at']
            }

            TOKEN_FILE.parent.mkdir(exist_ok=True)
            with open(TOKEN_FILE, 'w') as f:
                json.dump(token_file_data, f, indent=2)

            print(f"✅ Token refreshed (expires at {datetime.fromtimestamp(token_data['expires_at']).strftime('%Y-%m-%d %H:%M:%S')})")
            return True

        except Exception as e:
            print(f"❌ Error refreshing token: {e}")
            return False

    def _api_request(self, url: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """Make authenticated API request to Strava"""
        headers = {"Authorization": f"Bearer {self.access_token}"}

        try:
            response = requests.get(url, headers=headers, params=params)

            if response.status_code == 401:
                # Token expired, try to refresh
                print("⚠️  Token expired during request, refreshing...")
                if self._refresh_access_token():
                    # Retry request with new token
                    headers = {"Authorization": f"Bearer {self.access_token}"}
                    response = requests.get(url, headers=headers, params=params)
                else:
                    return None

            if response.status_code == 429:
                # Rate limit exceeded
                print("⚠️  Rate limit exceeded, waiting 15 minutes...")
                time.sleep(900)  # Wait 15 minutes
                return self._api_request(url, params)  # Retry

            if response.status_code != 200:
                print(f"⚠️  API request failed: {response.status_code} - {response.text}")
                return None

            return response.json()

        except Exception as e:
            print(f"⚠️  API request error: {e}")
            return None

    def fetch_activities(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None, fetch_splits: bool = False) -> List[Dict]:
        """Fetch activities from Strava within date range

        Args:
            start_date: Start date for activity fetch
            end_date: End date for activity fetch
            fetch_splits: If True, fetch detailed per-km splits (uses extra API calls, can be slow)
        """

        if start_date is None:
            # Default: fetch last 2 years
            start_date = datetime.now() - timedelta(days=730)

        if end_date is None:
            end_date = datetime.now()

        print(f"\n📊 Fetching activities from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}...")
        if fetch_splits:
            print("⚠️  Fetching detailed splits - this will take longer and use more API requests")

        activities = []
        page = 1
        per_page = 200  # Max allowed by Strava

        # Convert dates to Unix timestamps
        after_timestamp = int(start_date.timestamp())
        before_timestamp = int(end_date.timestamp())

        while True:
            print(f"  → Fetching page {page}...")

            params = {
                'after': after_timestamp,
                'before': before_timestamp,
                'page': page,
                'per_page': per_page
            }

            page_activities = self._api_request(
                "https://www.strava.com/api/v3/athlete/activities",
                params=params
            )

            if not page_activities:
                break

            if len(page_activities) == 0:
                break

            # Process each activity
            for activity in page_activities:
                # Only process running activities
                activity_type = activity.get('type', '').lower()
                sport_type = activity.get('sport_type', '').lower()

                if 'run' not in activity_type.lower() and 'run' not in sport_type.lower():
                    continue

                # Map to our schema
                activity_data = {
                    'id': f"strava_{activity['id']}",  # Prefix to distinguish from Garmin IDs
                    'strava_id': activity['id'],
                    'name': activity.get('name'),
                    'type': 'running',
                    'date': activity['start_date_local'].replace('T', ' ').replace('Z', ''),
                    'distance_km': round(activity.get('distance', 0) / 1000, 2),
                    'duration_seconds': activity.get('moving_time'),
                    'elapsed_time_seconds': activity.get('elapsed_time'),
                    'elevation_gain_m': activity.get('total_elevation_gain'),
                    'avg_hr': activity.get('average_heartrate'),
                    'max_hr': activity.get('max_heartrate'),
                    'calories': activity.get('calories'),
                    'avg_pace_min_km': self._speed_to_pace(activity.get('average_speed')),
                    'avg_cadence': activity.get('average_cadence'),
                    'suffer_score': activity.get('suffer_score'),
                    'has_heartrate': activity.get('has_heartrate', False),
                    'manual': activity.get('manual', False),
                    'source': 'strava'
                }

                # Optionally fetch detailed per-km splits via Streams API (rate limit aware)
                if fetch_splits:
                    try:
                        splits = self._fetch_activity_splits(activity['id'])
                        if splits:
                            activity_data['splits'] = splits
                            activity_data['splits_source'] = 'strava_streams'
                    except Exception as e:
                        # Don't fail entire sync if one activity's splits fail
                        print(f"      ⚠️  Could not fetch splits for activity {activity['id']}: {e}")
                        pass

                activities.append(activity_data)

            print(f"      ✓ Found {len(page_activities)} activities (running: {len([a for a in page_activities if 'run' in a.get('type', '').lower()])})")

            # If we got less than per_page, we've reached the end
            if len(page_activities) < per_page:
                break

            page += 1

            # Rate limit: max 100 requests per 15 minutes
            # Add small delay between pages
            time.sleep(1)

        print(f"✅ Fetched {len(activities)} running activities from Strava")

        # Sort by date (newest first)
        activities.sort(key=lambda x: x['date'], reverse=True)

        return activities

    def _fetch_activity_splits(self, activity_id: int) -> Optional[Dict]:
        """Fetch detailed splits (per km) for an activity using Streams API.

        Returns a dict shaped like Garmin's cache:
        { 'lapDTOs': [ { 'lapIndex': int, 'distance': meters,
                         'averageSpeed': m_per_s, 'averageHR': bpm or None,
                         'averageRunCadence': value or None } ... ] }
        """
        # Note: Additional API calls; be mindful of rate limits.
        streams = self._api_request(
            f"https://www.strava.com/api/v3/activities/{activity_id}/streams",
            params={
                'keys': 'time,distance,heartrate,cadence',
                'key_by_type': True
            }
        )

        if not streams or 'distance' not in streams or 'time' not in streams:
            return None

        dist = streams['distance'].get('data') or []  # meters
        time_s = streams['time'].get('data') or []    # seconds from start
        hr = (streams.get('heartrate') or {}).get('data') or []
        cad = (streams.get('cadence') or {}).get('data') or []

        if not dist or not time_s or len(dist) != len(time_s):
            return None

        laps = []
        last_idx = 0
        next_km = 1000.0
        lap_index = 1

        for i in range(1, len(dist)):
            if dist[i] >= next_km or i == len(dist) - 1:
                # Segment from last_idx..i
                d1, d2 = dist[last_idx], dist[i]
                t1, t2 = time_s[last_idx], time_s[i]
                seg_dist = max(0.0, float(d2 - d1))
                seg_time = max(0.000001, float(t2 - t1))

                avg_speed = seg_dist / seg_time  # m/s

                # Average HR and cadence in the segment (if present)
                if hr and len(hr) == len(dist):
                    seg_hr = hr[last_idx:i+1]
                    avg_hr = sum(seg_hr) / len(seg_hr) if seg_hr else None
                else:
                    avg_hr = None

                if cad and len(cad) == len(dist):
                    seg_cad = cad[last_idx:i+1]
                    avg_cad = sum(seg_cad) / len(seg_cad) if seg_cad else None
                else:
                    avg_cad = None

                laps.append({
                    'lapIndex': lap_index,
                    'distance': seg_dist,
                    'averageSpeed': avg_speed,
                    'averageHR': avg_hr,
                    'averageRunCadence': avg_cad,
                })

                lap_index += 1
                last_idx = i
                next_km += 1000.0

        if not laps:
            return None

        return {'lapDTOs': laps}

    def _merge_activities(self, existing: List[Dict], new: List[Dict]) -> List[Dict]:
        """Merge existing activities with newly fetched ones

        Strategy:
        - Keep all existing activities
        - Update activities that exist in both (by strava_id)
        - Add new activities that don't exist yet

        Args:
            existing: List of existing activities from cache
            new: List of newly fetched activities

        Returns:
            Merged list of activities
        """
        # Create a map of existing activities by strava_id
        existing_map = {a.get('strava_id'): a for a in existing if a.get('strava_id')}

        print(f"\n🔄 Merging activities...")
        print(f"   Existing in cache: {len(existing)}")
        print(f"   Newly fetched: {len(new)}")

        updated_count = 0
        added_count = 0

        # Process new activities
        for new_activity in new:
            strava_id = new_activity.get('strava_id')
            if strava_id in existing_map:
                # Update existing activity with new data
                existing_map[strava_id] = new_activity
                updated_count += 1
            else:
                # Add new activity
                existing_map[strava_id] = new_activity
                added_count += 1

        # Convert back to list and sort by date
        merged = list(existing_map.values())
        merged.sort(key=lambda x: x.get('date', ''), reverse=True)

        print(f"   Updated: {updated_count}")
        print(f"   Added: {added_count}")
        print(f"   Total after merge: {len(merged)}")

        return merged

    def fetch_athlete_profile(self) -> Dict:
        """Fetch athlete profile from Strava"""
        print("\n👤 Fetching athlete profile...")

        athlete = self._api_request("https://www.strava.com/api/v3/athlete")

        if not athlete:
            print("❌ Error fetching athlete profile")
            return {}

        profile_data = {
            'id': athlete.get('id'),
            'username': athlete.get('username'),
            'firstname': athlete.get('firstname'),
            'lastname': athlete.get('lastname'),
            'city': athlete.get('city'),
            'country': athlete.get('country'),
            'sex': athlete.get('sex'),
            'weight_kg': athlete.get('weight'),
            'created_at': athlete.get('created_at'),
        }

        print(f"  ✓ Profile: {profile_data['firstname']} {profile_data['lastname']}")
        return profile_data

    def sync_all(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None, fetch_splits: bool = False) -> bool:
        """Sync all data from Strava

        Args:
            start_date: Start date for activity fetch
            end_date: End date for activity fetch
            fetch_splits: If True, fetch detailed per-km splits (slower, more API calls)
        """
        print("=" * 60)
        print("🏃 STRAVA DATA SYNC")
        print("=" * 60)

        if not self.authenticate():
            return False

        # Fetch new activities
        new_activities = self.fetch_activities(start_date, end_date, fetch_splits)

        # Merge with existing activities
        existing_activities = self.data.get('activities', [])
        merged_activities = self._merge_activities(existing_activities, new_activities)

        self.data['activities'] = merged_activities
        self.data['athlete_profile'] = self.fetch_athlete_profile()
        self.data['last_sync'] = datetime.now().isoformat()

        # Save to cache
        self.save_cache()

        print("\n" + "=" * 60)
        print("✅ SYNC COMPLETE")
        print("=" * 60)
        print(f"📁 Data cached to: {CACHE_FILE}")
        print(f"📊 Total activities in cache: {len(self.data['activities'])}")
        print(f"📅 Date range: {self.data['activities'][-1]['date'][:10] if self.data['activities'] else 'N/A'} to {self.data['activities'][0]['date'][:10] if self.data['activities'] else 'N/A'}")

        return True

    def save_cache(self):
        """Save data to cache file"""
        CACHE_DIR.mkdir(exist_ok=True)
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)

    @staticmethod
    def _speed_to_pace(speed_mps: Optional[float]) -> Optional[str]:
        """Convert m/s to min/km pace"""
        if not speed_mps or speed_mps == 0:
            return None

        min_per_km = 1000 / (speed_mps * 60)
        minutes = int(min_per_km)
        seconds = int((min_per_km - minutes) * 60)
        return f"{minutes}:{seconds:02d}"


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Sync data from Strava')
    parser.add_argument('--start-date', type=str,
                       help='Start date (YYYY-MM-DD). Default: 2 years ago')
    parser.add_argument('--end-date', type=str,
                       help='End date (YYYY-MM-DD). Default: today')
    parser.add_argument('--days', type=int,
                       help='Number of days to sync (alternative to date range)')
    parser.add_argument('--fetch-splits', action='store_true',
                       help='Fetch detailed per-km splits (slower, uses more API calls)')

    args = parser.parse_args()

    # Parse dates
    start_date = None
    end_date = None

    if args.days:
        start_date = datetime.now() - timedelta(days=args.days)
        end_date = datetime.now()
    else:
        if args.start_date:
            start_date = datetime.strptime(args.start_date, '%Y-%m-%d')
        if args.end_date:
            end_date = datetime.strptime(args.end_date, '%Y-%m-%d')

    # Run sync
    syncer = StravaSync()
    success = syncer.sync_all(start_date=start_date, end_date=end_date, fetch_splits=args.fetch_splits)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
