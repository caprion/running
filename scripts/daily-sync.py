#!/usr/bin/env python3
"""
Daily Sync Workflow - INCREMENTAL ARCHITECTURE (Updated Jan 2026)

Uses incremental merge to preserve all historical data and HR enrichments.
NEVER rebuilds from scratch - always merges incrementally.

Workflow:
1. Incremental sync from Garmin (merges into unified-cache)
2. Dashboard automatically uses updated unified-cache

Usage:
  python scripts/daily-sync.py              # Fetch last 7 days from Garmin
  python scripts/daily-sync.py --days 30    # Fetch last 30 days
"""

import argparse
import subprocess
import sys
from pathlib import Path
from datetime import datetime

SCRIPTS_DIR = Path(__file__).parent


def run_script(script_name: str, args: list = None) -> bool:
    """Run a Python script and return success status"""
    cmd = [sys.executable, str(SCRIPTS_DIR / script_name)]
    if args:
        cmd.extend(args)

    print(f"\n{'='*60}")
    print(f"Running: {script_name}")
    print('='*60)

    try:
        result = subprocess.run(cmd, check=True)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"\n❌ {script_name} failed with exit code {e.returncode}")
        return False
    except Exception as e:
        print(f"\n❌ Error running {script_name}: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Daily sync workflow (new architecture)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/daily-sync.py              # Sync last 7 days (default)
  python scripts/daily-sync.py --days 14    # Sync last 14 days
        """
    )
    parser.add_argument(
        '--days',
        type=int,
        default=7,
        help='Number of days to sync from Garmin (default: 7)'
    )

    args = parser.parse_args()

    print("\n" + "="*60)
    print("Daily Sync - Incremental Architecture (Updated Jan 2026)")
    print("="*60)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Mode: Garmin only")
    print(f"Days: {args.days}")
    print("="*60)

    success = True

    # Use incremental-sync.py (NEW ARCHITECTURE - merges into unified-cache)
    # This NEVER rebuilds from scratch - always preserves historical data
    sync_args = ['--days', str(args.days)]

    if not run_script('incremental-sync.py', sync_args):
        print("\n[ERROR] Incremental sync failed")
        return 1

    print("\n" + "="*60)
    if success:
        print("✅ Daily sync completed successfully!")
    else:
        print("⚠️  Daily sync completed with warnings")
    print("="*60)

    print("\n📋 Next steps:")
    print("  - Dashboard will automatically use updated unified-cache.json")
    print("  - Run: streamlit run dashboard/app.py")
    print("\n💡 Architecture change (Jan 2026):")
    print("  - Now using INCREMENTAL sync (preserves all data)")
    print("  - unified-cache.json is the single source of truth")
    print("  - NEVER runs build-unified-cache.py (dangerous rebuild)")

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
