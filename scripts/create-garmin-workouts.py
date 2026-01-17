#!/usr/bin/env python3
"""
Create Garmin workouts for a specific week.

Usage:
    python scripts/create-garmin-workouts.py --week 3
    python scripts/create-garmin-workouts.py --week 4
"""

import sys
import os
import argparse
from dotenv import load_dotenv
from garminconnect import Garmin

# Load credentials
load_dotenv()
GARMIN_EMAIL = os.getenv("GARMIN_EMAIL")
GARMIN_PASSWORD = os.getenv("GARMIN_PASSWORD")

if not GARMIN_EMAIL or not GARMIN_PASSWORD:
    print("ERROR: GARMIN_EMAIL and GARMIN_PASSWORD must be set in .env file")
    sys.exit(1)


def get_week_workouts(week_number):
    """
    Define workouts for each week.
    
    Returns: List of workout definitions with date, name, description, and steps.
    """
    
    # Week 3 (Jan 20-25, 2026) - Base phase
    if week_number == 3:
        return [
            {
                "date": "2026-01-20",
                "name": "Week 3: Easy 7km",
                "description": "Easy run - Zone 2",
                "steps": [
                    {
                        "type": "ExecutableStepDTO",
                        "stepOrder": 1,
                        "stepType": {"stepTypeId": 3},
                        "endCondition": {"conditionTypeId": 3},
                        "endConditionValue": 7000.0,
                        "targetType": {"workoutTargetTypeId": 1}
                    }
                ]
            },
            {
                "date": "2026-01-22",
                "name": "Week 3: Tempo 4km @ 5:55",
                "description": "Warmup (lap) + Tempo 4km @ 5:55-6:00/km + Cooldown (lap)",
                "steps": [
                    {
                        "type": "ExecutableStepDTO",
                        "stepOrder": 1,
                        "stepType": {"stepTypeId": 1},
                        "endCondition": {"conditionTypeId": 1},
                        "endConditionValue": 1.0,
                        "targetType": {"workoutTargetTypeId": 1}
                    },
                    {
                        "type": "ExecutableStepDTO",
                        "stepOrder": 2,
                        "stepType": {"stepTypeId": 3},
                        "endCondition": {"conditionTypeId": 3},
                        "endConditionValue": 4000.0,
                        "targetType": {"workoutTargetTypeId": 6},
                        "targetValueOne": 2.778,
                        "targetValueTwo": 2.817
                    },
                    {
                        "type": "ExecutableStepDTO",
                        "stepOrder": 3,
                        "stepType": {"stepTypeId": 2},
                        "endCondition": {"conditionTypeId": 1},
                        "endConditionValue": 1.0,
                        "targetType": {"workoutTargetTypeId": 1}
                    }
                ]
            },
            {
                "date": "2026-01-24",
                "name": "Week 3: Long Run 14km",
                "description": "Long run - easy pace, Zone 2",
                "steps": [
                    {
                        "type": "ExecutableStepDTO",
                        "stepOrder": 1,
                        "stepType": {"stepTypeId": 3},
                        "endCondition": {"conditionTypeId": 3},
                        "endConditionValue": 14000.0,
                        "targetType": {"workoutTargetTypeId": 1}
                    }
                ]
            },
            {
                "date": "2026-01-25",
                "name": "Week 3: Easy 6km",
                "description": "Easy recovery run - Zone 2",
                "steps": [
                    {
                        "type": "ExecutableStepDTO",
                        "stepOrder": 1,
                        "stepType": {"stepTypeId": 3},
                        "endCondition": {"conditionTypeId": 3},
                        "endConditionValue": 6000.0,
                        "targetType": {"workoutTargetTypeId": 1}
                    }
                ]
            }
        ]
    
    # Week 4 - Add workouts here when ready
    elif week_number == 4:
        return []  # TODO: Define Week 4 workouts
    
    else:
        return []


def create_workouts(week_number, dry_run=False):
    """Create and schedule workouts for a specific week."""
    
    workouts = get_week_workouts(week_number)
    
    if not workouts:
        print(f"No workouts defined for Week {week_number}")
        return
    
    if dry_run:
        print(f"\n=== Week {week_number} Workouts (DRY RUN) ===\n")
        for w in workouts:
            print(f"  {w['date']}: {w['name']}")
            print(f"    {w['description']}")
            print(f"    Steps: {len(w['steps'])}")
        print(f"\nTotal: {len(workouts)} workouts")
        print("\nRun without --dry-run to create these workouts in Garmin Connect")
        return
    
    # Login
    print(f"Creating Week {week_number} workouts...")
    print("Authenticating with Garmin Connect...")
    try:
        client = Garmin(GARMIN_EMAIL, GARMIN_PASSWORD)
        client.login()
        print("✓ Authenticated\n")
    except Exception as e:
        print(f"✗ Auth failed: {e}")
        sys.exit(1)
    
    # Create all workouts
    created = []
    failed = []
    
    for workout_def in workouts:
        print(f"Creating: {workout_def['name']} ({workout_def['date']})...")
        
        workout_json = {
            "workoutName": workout_def['name'],
            "description": workout_def['description'],
            "sportType": {"sportTypeId": 1},
            "workoutSegments": [{
                "segmentOrder": 1,
                "sportType": {"sportTypeId": 1},
                "workoutSteps": workout_def['steps']
            }]
        }
        
        try:
            # Create workout
            response = client.connectapi(
                "/workout-service/workout",
                method="POST",
                json=workout_json
            )
            
            if isinstance(response, dict) and 'workoutId' in response:
                workout_id = response['workoutId']
                
                # Schedule workout
                try:
                    client.connectapi(
                        f"/workout-service/schedule/{workout_id}",
                        method="POST",
                        json={"date": workout_def['date']}
                    )
                    created.append({
                        'id': workout_id,
                        'name': workout_def['name'],
                        'date': workout_def['date']
                    })
                    print(f"  ✓ Created and scheduled (ID: {workout_id})\n")
                except Exception as e:
                    created.append({
                        'id': workout_id,
                        'name': workout_def['name'],
                        'date': workout_def['date'],
                        'scheduled': False
                    })
                    print(f"  ✓ Created (ID: {workout_id}) but scheduling failed: {e}\n")
            else:
                failed.append({'name': workout_def['name'], 'error': 'Invalid response'})
                print(f"  ✗ Failed: Invalid response\n")
                
        except Exception as e:
            failed.append({'name': workout_def['name'], 'error': str(e)})
            print(f"  ✗ Failed: {e}\n")
    
    # Summary
    print("="*60)
    print("SUMMARY")
    print("="*60)
    print(f"\n✓ Successfully created: {len(created)}/{len(workouts)}\n")
    
    if created:
        for w in created:
            scheduled = "" if w.get('scheduled', True) else " (not scheduled)"
            print(f"  • {w['date']}: {w['name']}{scheduled}")
    
    if failed:
        print(f"\n✗ Failed: {len(failed)}\n")
        for w in failed:
            print(f"  • {w['name']}: {w['error']}")
    
    print("\n" + "="*60)
    print("Next: Sync your Garmin watch via Garmin Connect app")
    print("="*60)


def main():
    parser = argparse.ArgumentParser(
        description='Create Garmin workouts for a specific week',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/create-garmin-workouts.py --week 3
  python scripts/create-garmin-workouts.py --week 4 --dry-run
        """
    )
    parser.add_argument(
        '--week',
        type=int,
        required=True,
        help='Week number (1-20)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview workouts without creating them'
    )
    
    args = parser.parse_args()
    
    if args.week < 1 or args.week > 20:
        print("Error: Week must be between 1 and 20")
        sys.exit(1)
    
    create_workouts(args.week, args.dry_run)


if __name__ == '__main__':
    main()
