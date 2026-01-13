#!/usr/bin/env python3
"""
Combined Sync Script
Syncs data from both Garmin Connect and Strava
"""

import sys
import argparse
from datetime import datetime, timedelta

# Import sync modules
from sync_garmin import GarminSync
from sync_strava import StravaSync


def main():
    """Sync data from both Garmin and Strava"""
    parser = argparse.ArgumentParser(
        description='Sync data from both Garmin Connect and Strava'
    )
    parser.add_argument(
        'days',
        nargs='?',
        type=int,
        default=7,
        help='Number of days to sync from Garmin (default: 7)'
    )
    parser.add_argument(
        '--fit',
        '-f',
        action='store_true',
        help='Download FIT files for Garmin activities'
    )
    parser.add_argument(
        '--strava-start',
        type=str,
        help='Start date for Strava sync (YYYY-MM-DD). Default: 2 years ago'
    )
    parser.add_argument(
        '--strava-days',
        type=int,
        help='Number of days to sync from Strava (alternative to date range)'
    )
    parser.add_argument(
        '--garmin-only',
        action='store_true',
        help='Sync only from Garmin'
    )
    parser.add_argument(
        '--strava-only',
        action='store_true',
        help='Sync only from Strava'
    )

    args = parser.parse_args()

    print("=" * 70)
    print("🏃 COMBINED SYNC: GARMIN + STRAVA")
    print("=" * 70)
    print()

    success_garmin = True
    success_strava = True

    # Sync Garmin
    if not args.strava_only:
        print("📍 STEP 1/2: Syncing Garmin Connect...")
        print("-" * 70)
        garmin_syncer = GarminSync()
        success_garmin = garmin_syncer.sync_all(days=args.days, download_fit=args.fit)
        print()

    # Sync Strava
    if not args.garmin_only:
        print("📍 STEP 2/2: Syncing Strava...")
        print("-" * 70)

        # Determine date range for Strava
        strava_start = None
        strava_end = None

        if args.strava_days:
            strava_start = datetime.now() - timedelta(days=args.strava_days)
            strava_end = datetime.now()
        elif args.strava_start:
            strava_start = datetime.strptime(args.strava_start, '%Y-%m-%d')
            strava_end = datetime.now()

        strava_syncer = StravaSync()
        success_strava = strava_syncer.sync_all(start_date=strava_start, end_date=strava_end)
        print()

    # Summary
    print()
    print("=" * 70)
    print("✅ COMBINED SYNC COMPLETE")
    print("=" * 70)

    if not args.strava_only:
        status = "✅" if success_garmin else "❌"
        print(f"{status} Garmin Connect: {'Success' if success_garmin else 'Failed'}")

    if not args.garmin_only:
        status = "✅" if success_strava else "❌"
        print(f"{status} Strava: {'Success' if success_strava else 'Failed'}")

    print()
    print("💡 Data from both sources has been merged automatically!")
    print("   - Duplicates are detected by date+distance matching")
    print("   - Garmin data is preferred when duplicates exist")
    print("   - Each activity is marked with its source(s)")
    print()

    # Exit with error if any sync failed
    if not success_garmin or not success_strava:
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
