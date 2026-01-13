#!/usr/bin/env python3
"""
Strava Recent Activities Sync (Last 8 Weeks with Splits)

Fetches recent activities from Strava with detailed per-km splits.
This is used during the transition period when Garmin laps weren't enabled.

After transition (once Garmin has all data), this script is no longer needed.
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
CACHE_FILE = CACHE_DIR / "strava-recent-splits.json"
TOKEN_FILE = Path(__file__).parent / ".strava_tokens.json"

# Fetch last 8 weeks
WEEKS_TO_FETCH = 8


class StravaRecentSync:
    """Handles syncing recent activities from Strava with splits"""

    def __init__(self):
        self.access_token: Optional[str] = None
        self.data = {
            "last_sync": None,
            "weeks_fetched": WEEKS_TO_FETCH,
            "activities": []
        }

    def authenticate(self) -> bool:
        """Authenticate with Strava using OAuth2 token refresh"""

        if not STRAVA_CLIENT_ID or not STRAVA_CLIENT_SECRET or not STRAVA_REFRESH_TOKEN:
            print("❌ Error: STRAVA_CLIENT_ID, STRAVA_CLIENT_SECRET, and STRAVA_REFRESH_TOKEN must be set in .env file")
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
                return True
            else:
                return False

        except Exception:
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

            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data['access_token']

                # Save token for future use
                TOKEN_FILE.parent.mkdir(exist_ok=True)
                with open(TOKEN_FILE, 'w') as f:
                    json.dump(token_data, f, indent=2)

                print("✅ Access token refreshed successfully")
                return True
            else:
                print(f"❌ Failed to refresh token: {response.status_code}")
                print(response.text)
                return False

        except Exception as e:
            print(f"❌ Error refreshing token: {e}")
            return False

    def _make_request(self, url: str, params: Dict = None) -> Optional[Dict]:
        """Make an authenticated request to Strava API"""
        headers = {"Authorization": f"Bearer {self.access_token}"}

        try:
            response = requests.get(url, headers=headers, params=params)

            if response.status_code == 200:
                return response.json()
            else:
                print(f"⚠️  API request failed: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            print(f"⚠️  Request error: {e}")
            return None

    def _fetch_activity_splits(self, activity_id: int) -> Optional[Dict]:
        """Fetch detailed per-km splits for an activity using streams API"""
        url = f"https://www.strava.com/api/v3/activities/{activity_id}/streams"

        params = {
            'keys': 'distance,time,heartrate,velocity_smooth',
            'key_by_type': True
        }

        streams = self._make_request(url, params)
        if not streams:
            return None

        # Convert streams to lap-like structure
        distance_data = streams.get('distance', {}).get('data', [])
        time_data = streams.get('time', {}).get('data', [])
        hr_data = streams.get('heartrate', {}).get('data', [])
        velocity_data = streams.get('velocity_smooth', {}).get('data', [])

        if not distance_data or not time_data:
            return None

        # Create 1km laps
        laps = []
        current_km = 0
        lap_start_idx = 0

        for i, dist in enumerate(distance_data):
            dist_km = dist / 1000.0

            if dist_km >= current_km + 1:
                # Complete this km
                lap_distance = distance_data[i] - (distance_data[lap_start_idx] if lap_start_idx < len(distance_data) else 0)
                lap_time = time_data[i] - (time_data[lap_start_idx] if lap_start_idx < len(time_data) else 0)

                # Calculate average HR for this lap
                lap_hr_values = hr_data[lap_start_idx:i+1] if hr_data else []
                avg_hr = sum(lap_hr_values) / len(lap_hr_values) if lap_hr_values else 0

                # Calculate average pace (min/km)
                pace_min_per_km = (lap_time / 60.0) / (lap_distance / 1000.0) if lap_distance > 0 else 0

                laps.append({
                    'startDistanceInMeters': distance_data[lap_start_idx] if lap_start_idx < len(distance_data) else 0,
                    'totalDistanceInMeters': lap_distance,
                    'totalTimeInSeconds': lap_time,
                    'averageHR': int(avg_hr) if avg_hr > 0 else None,
                    'paceMinPerKm': round(pace_min_per_km, 2)
                })

                current_km += 1
                lap_start_idx = i

        return {'lapDTOs': laps} if laps else None

    def fetch_recent_activities(self) -> bool:
        """Fetch recent activities (last 8 weeks) with splits"""
        print(f"\n📥 Fetching last {WEEKS_TO_FETCH} weeks of activities from Strava...")

        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(weeks=WEEKS_TO_FETCH)
        after_timestamp = int(start_date.timestamp())

        print(f"   Date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")

        page = 1
        per_page = 30
        all_activities = []

        while True:
            print(f"\n   Fetching page {page}...", end=" ")

            params = {
                "after": after_timestamp,
                "per_page": per_page,
                "page": page
            }

            activities_page = self._make_request(
                "https://www.strava.com/api/v3/athlete/activities",
                params=params
            )

            if not activities_page:
                print("❌ Failed")
                break

            if not activities_page:
                print("✓ Done (no more activities)")
                break

            # Filter for runs only
            runs = [a for a in activities_page if a.get('type') in ('Run', 'VirtualRun')]
            print(f"✓ Got {len(runs)} runs")

            all_activities.extend(runs)

            # Check if we have more pages
            if len(activities_page) < per_page:
                break

            page += 1
            time.sleep(1)  # Rate limiting

        print(f"\n✅ Fetched {len(all_activities)} activities from last {WEEKS_TO_FETCH} weeks")

        # Fetch splits for each activity
        print(f"\n📊 Fetching detailed splits for {len(all_activities)} activities...")
        activities_with_splits = []

        for i, activity in enumerate(all_activities, 1):
            activity_id = activity['id']
            name = activity.get('name', 'Unknown')
            date = activity['start_date'][:10]
            distance_km = activity['distance'] / 1000.0

            print(f"   [{i}/{len(all_activities)}] {date} - {name} ({distance_km:.1f}km)...", end=" ")

            # Convert to our format
            activity_data = {
                'strava_id': activity_id,
                'date': activity['start_date'].replace('T', ' ').replace('Z', ''),
                'name': name,
                'distance_km': round(distance_km, 2),
                'duration_seconds': activity.get('moving_time', 0),
                'elevation_gain': activity.get('total_elevation_gain', 0),
                'average_heartrate': activity.get('average_heartrate'),
                'max_heartrate': activity.get('max_heartrate'),
                'average_speed': activity.get('average_speed'),
                'suffer_score': activity.get('suffer_score'),
                'source': 'strava'
            }

            # Fetch splits
            try:
                splits = self._fetch_activity_splits(activity_id)
                if splits:
                    activity_data['splits'] = splits
                    activity_data['splits_source'] = 'strava'
                    print("✓ Got splits")
                else:
                    print("⚠️  No splits")

                activities_with_splits.append(activity_data)

            except Exception as e:
                print(f"❌ Error: {e}")
                # Include activity without splits
                activities_with_splits.append(activity_data)

            time.sleep(0.5)  # Rate limiting

        self.data['activities'] = activities_with_splits
        return True

    def save_data(self):
        """Save data to cache file"""
        CACHE_DIR.mkdir(exist_ok=True)

        self.data['last_sync'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)

        print(f"\n✅ Saved {len(self.data['activities'])} activities to {CACHE_FILE}")

    def sync(self) -> bool:
        """Run full sync"""
        if not self.authenticate():
            return False

        if not self.fetch_recent_activities():
            return False

        self.save_data()
        return True


def main():
    print("="*60)
    print("Strava Recent Activities Sync (Last 8 Weeks)")
    print("="*60)

    sync = StravaRecentSync()

    if not sync.sync():
        print("\n❌ Sync failed")
        sys.exit(1)

    print("\n" + "="*60)
    print("✅ Sync completed successfully!")
    print("="*60)
    print(f"\n📋 Next step: Run 'python scripts/build-unified-cache.py' to merge all data sources")


if __name__ == "__main__":
    main()
