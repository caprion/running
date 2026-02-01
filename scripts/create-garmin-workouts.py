#!/usr/bin/env python3
"""
Create Garmin workouts for a specific week - auto-generated from plan.md

Usage:
    python scripts/create-garmin-workouts.py --week 3
    python scripts/create-garmin-workouts.py --week 4 --dry-run
    python scripts/create-garmin-workouts.py --week 5 --list  # Show parsed plan
"""

import sys
import os
import re
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

# Load credentials
load_dotenv()
GARMIN_EMAIL = os.getenv("GARMIN_EMAIL")
GARMIN_PASSWORD = os.getenv("GARMIN_PASSWORD")

# Season config
SEASON_START = datetime(2026, 1, 5)  # Week 1 starts Jan 5, 2026
PLAN_PATH = Path(__file__).parent.parent / "seasons" / "2026-spring-hm-sub2" / "plan.md"

# Running days: Tue=0, Thu=2, Sat=4, Sun=5 (offset from Monday)
RUNNING_DAYS = {
    "tue": 1,  # Tuesday
    "thu": 3,  # Thursday (quality day)
    "sat": 5,  # Saturday (long run)
    "sun": 6,  # Sunday
}


def pace_to_speed(pace_str):
    """Convert pace string like '5:50' to m/s."""
    parts = pace_str.split(":")
    minutes = int(parts[0])
    seconds = int(parts[1]) if len(parts) > 1 else 0
    total_seconds = minutes * 60 + seconds
    return 1000 / total_seconds  # m/s


def parse_plan():
    """Parse plan.md to extract weekly progression and pace tables."""
    with open(PLAN_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Parse Weekly Volume Progression table
    weeks = {}
    pattern = r"\|\s*(\d+)\s*\|\s*([^|]+)\|\s*(\d+)\s*\|\s*[^|]+\|\s*([^|]+)\|"
    
    # Find the Weekly Volume Progression section
    volume_section = re.search(
        r"## Weekly Volume Progression.*?\n\n",
        content,
        re.DOTALL
    )
    
    if volume_section:
        section_start = volume_section.start()
        section_text = content[section_start:section_start + 2000]
        
        for match in re.finditer(pattern, section_text):
            week_num = int(match.group(1))
            phase = match.group(2).strip().replace("*", "")
            volume = int(match.group(3))
            key_workout = match.group(4).strip()
            
            weeks[week_num] = {
                "phase": phase,
                "volume": volume,
                "key_workout": key_workout
            }
    
    # Parse Target Paces by Phase table
    paces = {}
    pace_pattern = r"\|\s*(\w+)\s*\|\s*([\d:]+(?:-[\d:]+)?|None)\s*\|\s*([\d:]+(?:-[\d:]+)?|None)\s*\|\s*([\d:]+(?:-[\d:]+)?|None)\s*\|\s*([^|]+)\|"
    
    pace_section = re.search(r"## Target Paces by Phase", content)
    if pace_section:
        section_text = content[pace_section.start():pace_section.start() + 1000]
        
        for match in re.finditer(pace_pattern, section_text):
            phase = match.group(1).strip()
            easy = match.group(2).strip()
            tempo = match.group(3).strip()
            intervals = match.group(4).strip()
            long_run = match.group(5).strip()
            
            if phase.lower() not in ["phase", "---"]:
                paces[phase.lower()] = {
                    "easy": easy,
                    "tempo": tempo,
                    "intervals": intervals,
                    "long_run": long_run
                }
    
    return weeks, paces


def get_week_dates(week_number):
    """Get the Monday date for a given week number."""
    week_start = SEASON_START + timedelta(weeks=week_number - 1)
    return week_start


def parse_key_workout(key_workout):
    """
    Parse key workout string to extract type and parameters.
    Examples:
        'Tempo 5km@5:50' -> {'type': 'tempo', 'distance': 5000, 'pace': '5:50'}
        'Intervals 5×1km@5:40' -> {'type': 'intervals', 'reps': 5, 'distance': 1000, 'pace': '5:40'}
        'Strides only' -> {'type': 'strides'}
        'Easy runs only' -> {'type': 'easy_only'}
    """
    workout = key_workout.lower()
    
    # Tempo: "Tempo 5km@5:50" or "First tempo (4km@5:55)"
    tempo_match = re.search(r"tempo.*?(\d+)km@([\d:]+)", workout)
    if tempo_match:
        return {
            "type": "tempo",
            "distance": int(tempo_match.group(1)) * 1000,
            "pace": tempo_match.group(2)
        }
    
    # Intervals: "Intervals 5×1km@5:40" or "First intervals (5×1km@5:40)"
    interval_match = re.search(r"(\d+)[×x](\d+)(?:m|km)?@([\d:]+)", workout)
    if interval_match:
        reps = int(interval_match.group(1))
        dist = int(interval_match.group(2))
        # If distance is small (like 1, 2), it's km; if large (800, 600), it's meters
        if dist <= 10:
            dist *= 1000
        return {
            "type": "intervals",
            "reps": reps,
            "distance": dist,
            "pace": interval_match.group(3)
        }
    
    # VO2max: "VO2max 5×800m@5:15-5:25"
    vo2_match = re.search(r"vo2max.*?(\d+)[×x](\d+)m?@([\d:-]+)", workout)
    if vo2_match:
        return {
            "type": "vo2max",
            "reps": int(vo2_match.group(1)),
            "distance": int(vo2_match.group(2)),
            "pace": vo2_match.group(3).split("-")[0]  # Use faster pace
        }
    
    # Sharpener: "Sharpener 4×600m@5:15"
    sharp_match = re.search(r"sharpener.*?(\d+)[×x](\d+)m?@([\d:]+)", workout)
    if sharp_match:
        return {
            "type": "sharpener",
            "reps": int(sharp_match.group(1)),
            "distance": int(sharp_match.group(2)),
            "pace": sharp_match.group(3)
        }
    
    # Long run with pace: "Long run 8km@5:50"
    long_pace_match = re.search(r"long run.*?(\d+)km@([\d:-]+)", workout)
    if long_pace_match:
        return {
            "type": "long_tempo",
            "distance": int(long_pace_match.group(1)) * 1000,
            "pace": long_pace_match.group(2).split("-")[0]
        }
    
    # HM rehearsal
    if "hm rehearsal" in workout:
        rehearsal_match = re.search(r"(\d+)km@([\d:]+)", workout)
        if rehearsal_match:
            return {
                "type": "hm_rehearsal",
                "distance": int(rehearsal_match.group(1)) * 1000,
                "pace": rehearsal_match.group(2)
            }
    
    # Progressive threshold
    if "progressive" in workout:
        return {"type": "progressive"}
    
    # Fartlek
    if "fartlek" in workout:
        return {"type": "fartlek"}
    
    # Strides only (deload)
    if "strides" in workout:
        return {"type": "strides"}
    
    # Easy runs only
    if "easy" in workout:
        return {"type": "easy_only"}
    
    # Recovery week
    if "recovery" in workout:
        return {"type": "recovery"}
    
    # Race
    if "race" in workout:
        return {"type": "race"}
    
    return {"type": "unknown", "raw": key_workout}


def get_phase_paces(phase, paces):
    """Get pace targets for a phase, with fallback to Base."""
    phase_lower = phase.lower().replace(" (deload)", "").replace("10k ", "").replace("hm ", "")
    
    if phase_lower in paces:
        return paces[phase_lower]
    elif "base" in phase_lower:
        return paces.get("base", paces.get("recovery"))
    elif "build" in phase_lower:
        return paces.get("build", paces.get("base"))
    elif "specific" in phase_lower:
        return paces.get("specific", paces.get("build"))
    elif "taper" in phase_lower:
        return paces.get("specific", paces.get("build"))
    else:
        return paces.get("base", {})


def calculate_run_distances(total_volume, key_workout_info, is_deload=False):
    """
    Calculate distances for each run day based on total volume and key workout.
    Returns: dict with tue, thu, sat, sun distances
    """
    # Default distribution: Tue 20%, Thu 20%, Sat 40%, Sun 20%
    # Adjust for key workout
    
    if is_deload:
        # Deload: shorter long run, easier distribution
        return {
            "tue": int(total_volume * 0.20),
            "thu": int(total_volume * 0.20),
            "sat": int(total_volume * 0.40),
            "sun": int(total_volume * 0.20)
        }
    
    key_type = key_workout_info.get("type", "easy_only")
    
    if key_type in ["tempo", "intervals", "vo2max", "sharpener"]:
        # Quality workout on Thursday - account for warmup/cooldown
        quality_distance = key_workout_info.get("distance", 5000)
        thu_total = quality_distance + 3000  # ~1.5km warmup + 1.5km cooldown
        
        remaining = total_volume - thu_total
        return {
            "tue": int(remaining * 0.25),
            "thu": thu_total,
            "sat": int(remaining * 0.50),
            "sun": int(remaining * 0.25)
        }
    
    elif key_type == "long_tempo":
        # Long run has tempo section
        return {
            "tue": int(total_volume * 0.18),
            "thu": int(total_volume * 0.18),
            "sat": int(total_volume * 0.46),
            "sun": int(total_volume * 0.18)
        }
    
    else:
        # Default easy distribution
        return {
            "tue": int(total_volume * 0.20),
            "thu": int(total_volume * 0.20),
            "sat": int(total_volume * 0.40),
            "sun": int(total_volume * 0.20)
        }


def create_easy_run_workout(distance_m):
    """Create a simple easy run workout."""
    return [{
        "type": "ExecutableStepDTO",
        "stepOrder": 1,
        "stepType": {"stepTypeId": 3},  # Run
        "endCondition": {"conditionTypeId": 3},  # Distance
        "endConditionValue": float(distance_m),
        "targetType": {"workoutTargetTypeId": 1}  # No target
    }]


def create_tempo_workout(distance_m, pace_str):
    """Create tempo workout: warmup + tempo + cooldown."""
    pace_parts = pace_str.replace(" ", "").split("-")
    slow_pace = pace_parts[-1] if len(pace_parts) > 1 else pace_str
    fast_pace = pace_parts[0]
    
    return [
        {
            "type": "ExecutableStepDTO",
            "stepOrder": 1,
            "stepType": {"stepTypeId": 1},  # Warmup
            "endCondition": {"conditionTypeId": 1},  # Lap button
            "endConditionValue": 1.0,
            "targetType": {"workoutTargetTypeId": 1}
        },
        {
            "type": "ExecutableStepDTO",
            "stepOrder": 2,
            "stepType": {"stepTypeId": 3},  # Run
            "endCondition": {"conditionTypeId": 3},  # Distance
            "endConditionValue": float(distance_m),
            "targetType": {"workoutTargetTypeId": 6},  # Pace
            "targetValueOne": pace_to_speed(slow_pace),
            "targetValueTwo": pace_to_speed(fast_pace)
        },
        {
            "type": "ExecutableStepDTO",
            "stepOrder": 3,
            "stepType": {"stepTypeId": 2},  # Cooldown
            "endCondition": {"conditionTypeId": 1},  # Lap button
            "endConditionValue": 1.0,
            "targetType": {"workoutTargetTypeId": 1}
        }
    ]


def create_interval_workout(reps, distance_m, pace_str, recovery_time=90):
    """Create interval workout: warmup + repeats + cooldown."""
    pace_parts = pace_str.replace(" ", "").split("-")
    slow_pace = pace_parts[-1] if len(pace_parts) > 1 else pace_str
    fast_pace = pace_parts[0]
    
    return [
        {
            "type": "ExecutableStepDTO",
            "stepOrder": 1,
            "stepType": {"stepTypeId": 1},  # Warmup
            "endCondition": {"conditionTypeId": 1},  # Lap button
            "endConditionValue": 1.0,
            "targetType": {"workoutTargetTypeId": 1}
        },
        {
            "type": "RepeatGroupDTO",
            "stepOrder": 2,
            "numberOfIterations": reps,
            "repeatType": {"repeatTypeId": 1},
            "workoutSteps": [
                {
                    "type": "ExecutableStepDTO",
                    "stepOrder": 1,
                    "stepType": {"stepTypeId": 4},  # Interval
                    "endCondition": {"conditionTypeId": 3},  # Distance
                    "endConditionValue": float(distance_m),
                    "targetType": {"workoutTargetTypeId": 6},  # Pace
                    "targetValueOne": pace_to_speed(slow_pace),
                    "targetValueTwo": pace_to_speed(fast_pace)
                },
                {
                    "type": "ExecutableStepDTO",
                    "stepOrder": 2,
                    "stepType": {"stepTypeId": 4},  # Recovery
                    "endCondition": {"conditionTypeId": 2},  # Time
                    "endConditionValue": float(recovery_time),
                    "targetType": {"workoutTargetTypeId": 1}
                }
            ]
        },
        {
            "type": "ExecutableStepDTO",
            "stepOrder": 3,
            "stepType": {"stepTypeId": 2},  # Cooldown
            "endCondition": {"conditionTypeId": 1},  # Lap button
            "endConditionValue": 1.0,
            "targetType": {"workoutTargetTypeId": 1}
        }
    ]


def create_strides_workout(easy_distance_m):
    """Create easy run with strides: easy + 4x20s strides."""
    return [
        {
            "type": "ExecutableStepDTO",
            "stepOrder": 1,
            "stepType": {"stepTypeId": 3},  # Run
            "endCondition": {"conditionTypeId": 3},  # Distance
            "endConditionValue": float(easy_distance_m - 1000),
            "targetType": {"workoutTargetTypeId": 1}
        },
        {
            "type": "RepeatGroupDTO",
            "stepOrder": 2,
            "numberOfIterations": 4,
            "repeatType": {"repeatTypeId": 1},
            "workoutSteps": [
                {
                    "type": "ExecutableStepDTO",
                    "stepOrder": 1,
                    "stepType": {"stepTypeId": 4},  # Interval
                    "endCondition": {"conditionTypeId": 2},  # Time
                    "endConditionValue": 20.0,
                    "targetType": {"workoutTargetTypeId": 6},  # Pace
                    "targetValueOne": pace_to_speed("5:00"),
                    "targetValueTwo": pace_to_speed("4:30")
                },
                {
                    "type": "ExecutableStepDTO",
                    "stepOrder": 2,
                    "stepType": {"stepTypeId": 4},  # Recovery
                    "endCondition": {"conditionTypeId": 2},  # Time
                    "endConditionValue": 60.0,
                    "targetType": {"workoutTargetTypeId": 1}
                }
            ]
        },
        {
            "type": "ExecutableStepDTO",
            "stepOrder": 3,
            "stepType": {"stepTypeId": 2},  # Cooldown
            "endCondition": {"conditionTypeId": 1},  # Lap button
            "endConditionValue": 1.0,
            "targetType": {"workoutTargetTypeId": 1}
        }
    ]


def create_long_tempo_workout(total_distance_m, tempo_distance_m, pace_str):
    """Create long run with tempo section in the middle."""
    pace_parts = pace_str.replace(" ", "").split("-")
    slow_pace = pace_parts[-1] if len(pace_parts) > 1 else pace_str
    fast_pace = pace_parts[0]
    
    warmup_distance = 3000  # 3km easy warmup
    cooldown_distance = total_distance_m - warmup_distance - tempo_distance_m
    
    return [
        {
            "type": "ExecutableStepDTO",
            "stepOrder": 1,
            "stepType": {"stepTypeId": 1},  # Warmup
            "endCondition": {"conditionTypeId": 3},  # Distance
            "endConditionValue": float(warmup_distance),
            "targetType": {"workoutTargetTypeId": 1}
        },
        {
            "type": "ExecutableStepDTO",
            "stepOrder": 2,
            "stepType": {"stepTypeId": 3},  # Run (tempo)
            "endCondition": {"conditionTypeId": 3},  # Distance
            "endConditionValue": float(tempo_distance_m),
            "targetType": {"workoutTargetTypeId": 6},  # Pace
            "targetValueOne": pace_to_speed(slow_pace),
            "targetValueTwo": pace_to_speed(fast_pace)
        },
        {
            "type": "ExecutableStepDTO",
            "stepOrder": 3,
            "stepType": {"stepTypeId": 2},  # Cooldown
            "endCondition": {"conditionTypeId": 3},  # Distance
            "endConditionValue": float(max(cooldown_distance, 1000)),
            "targetType": {"workoutTargetTypeId": 1}
        }
    ]


def create_fartlek_workout(distance_m):
    """Create fartlek workout: alternating fast/easy segments."""
    return [
        {
            "type": "ExecutableStepDTO",
            "stepOrder": 1,
            "stepType": {"stepTypeId": 1},  # Warmup
            "endCondition": {"conditionTypeId": 3},  # Distance
            "endConditionValue": 2000.0,
            "targetType": {"workoutTargetTypeId": 1}
        },
        {
            "type": "RepeatGroupDTO",
            "stepOrder": 2,
            "numberOfIterations": 6,
            "repeatType": {"repeatTypeId": 1},
            "workoutSteps": [
                {
                    "type": "ExecutableStepDTO",
                    "stepOrder": 1,
                    "stepType": {"stepTypeId": 4},  # Fast
                    "endCondition": {"conditionTypeId": 2},  # Time
                    "endConditionValue": 60.0,  # 1 min fast
                    "targetType": {"workoutTargetTypeId": 1}
                },
                {
                    "type": "ExecutableStepDTO",
                    "stepOrder": 2,
                    "stepType": {"stepTypeId": 4},  # Easy
                    "endCondition": {"conditionTypeId": 2},  # Time
                    "endConditionValue": 90.0,  # 90s easy
                    "targetType": {"workoutTargetTypeId": 1}
                }
            ]
        },
        {
            "type": "ExecutableStepDTO",
            "stepOrder": 3,
            "stepType": {"stepTypeId": 2},  # Cooldown
            "endCondition": {"conditionTypeId": 1},  # Lap button
            "endConditionValue": 1.0,
            "targetType": {"workoutTargetTypeId": 1}
        }
    ]


def get_week_workouts(week_number):
    """
    Generate workouts for a specific week based on plan.md.
    """
    weeks, paces = parse_plan()
    
    if week_number not in weeks:
        return []
    
    week_info = weeks[week_number]
    phase = week_info["phase"]
    volume = week_info["volume"] * 1000  # Convert to meters
    key_workout_raw = week_info["key_workout"]
    key_workout = parse_key_workout(key_workout_raw)
    
    # Skip race weeks
    if key_workout["type"] == "race":
        print(f"Week {week_number} is a race week - create workouts manually")
        return []
    
    is_deload = "deload" in phase.lower()
    phase_paces = get_phase_paces(phase, paces)
    
    # Calculate run distances
    distances = calculate_run_distances(volume, key_workout, is_deload)
    
    # Get week start date (Monday)
    week_start = get_week_dates(week_number)
    
    workouts = []
    
    # Tuesday - Easy run (or strides on deload weeks)
    tue_date = week_start + timedelta(days=RUNNING_DAYS["tue"])
    if is_deload and key_workout["type"] == "strides":
        workouts.append({
            "date": tue_date.strftime("%Y-%m-%d"),
            "name": f"Week {week_number}: Easy {distances['tue']//1000}km + Strides",
            "description": "Easy run Zone 2 + 4x20s strides",
            "steps": create_strides_workout(distances["tue"])
        })
    else:
        workouts.append({
            "date": tue_date.strftime("%Y-%m-%d"),
            "name": f"Week {week_number}: Easy {distances['tue']//1000}km",
            "description": "Easy run - Zone 2",
            "steps": create_easy_run_workout(distances["tue"])
        })
    
    # Thursday - Quality workout
    thu_date = week_start + timedelta(days=RUNNING_DAYS["thu"])
    
    if key_workout["type"] == "tempo":
        workouts.append({
            "date": thu_date.strftime("%Y-%m-%d"),
            "name": f"Week {week_number}: Tempo {key_workout['distance']//1000}km @ {key_workout['pace']}",
            "description": f"Warmup (lap) + Tempo {key_workout['distance']//1000}km @ {key_workout['pace']}/km + Cooldown (lap)",
            "steps": create_tempo_workout(key_workout["distance"], key_workout["pace"])
        })
    elif key_workout["type"] in ["intervals", "vo2max", "sharpener"]:
        dist_display = f"{key_workout['distance']}m" if key_workout["distance"] < 1000 else f"{key_workout['distance']//1000}km"
        workouts.append({
            "date": thu_date.strftime("%Y-%m-%d"),
            "name": f"Week {week_number}: {key_workout['reps']}x{dist_display} @ {key_workout['pace']}",
            "description": f"Warmup + {key_workout['reps']}x{dist_display} @ {key_workout['pace']}/km + Cooldown",
            "steps": create_interval_workout(key_workout["reps"], key_workout["distance"], key_workout["pace"])
        })
    elif key_workout["type"] == "fartlek":
        workouts.append({
            "date": thu_date.strftime("%Y-%m-%d"),
            "name": f"Week {week_number}: Fartlek {distances['thu']//1000}km",
            "description": "Warmup + 6x(1min fast / 90s easy) + Cooldown",
            "steps": create_fartlek_workout(distances["thu"])
        })
    elif key_workout["type"] == "progressive":
        # Progressive threshold - tempo with increasing pace
        tempo_pace = phase_paces.get("tempo", "5:45")
        if "-" in tempo_pace:
            tempo_pace = tempo_pace.split("-")[0]
        workouts.append({
            "date": thu_date.strftime("%Y-%m-%d"),
            "name": f"Week {week_number}: Progressive Tempo 5km",
            "description": "Warmup + 5km starting easy, finishing at tempo pace + Cooldown",
            "steps": create_tempo_workout(5000, tempo_pace)
        })
    elif key_workout["type"] == "hm_rehearsal":
        workouts.append({
            "date": thu_date.strftime("%Y-%m-%d"),
            "name": f"Week {week_number}: HM Rehearsal {key_workout['distance']//1000}km @ {key_workout['pace']}",
            "description": f"Warmup + {key_workout['distance']//1000}km @ HM pace ({key_workout['pace']}/km) + Cooldown",
            "steps": create_tempo_workout(key_workout["distance"], key_workout["pace"])
        })
    else:
        # Easy/recovery/strides - just easy run on Thursday
        workouts.append({
            "date": thu_date.strftime("%Y-%m-%d"),
            "name": f"Week {week_number}: Easy {distances['thu']//1000}km",
            "description": "Easy run - Zone 2",
            "steps": create_easy_run_workout(distances["thu"])
        })
    
    # Saturday - Long run
    sat_date = week_start + timedelta(days=RUNNING_DAYS["sat"])
    
    if key_workout["type"] == "long_tempo":
        total_long = distances["sat"]
        tempo_dist = key_workout["distance"]
        workouts.append({
            "date": sat_date.strftime("%Y-%m-%d"),
            "name": f"Week {week_number}: Long Run {total_long//1000}km w/ {tempo_dist//1000}km @ {key_workout['pace']}",
            "description": f"Easy warmup + {tempo_dist//1000}km @ {key_workout['pace']}/km + Easy cooldown",
            "steps": create_long_tempo_workout(total_long, tempo_dist, key_workout["pace"])
        })
    else:
        workouts.append({
            "date": sat_date.strftime("%Y-%m-%d"),
            "name": f"Week {week_number}: Long Run {distances['sat']//1000}km",
            "description": "Long run - easy pace, Zone 2",
            "steps": create_easy_run_workout(distances["sat"])
        })
    
    # Sunday - Easy recovery
    sun_date = week_start + timedelta(days=RUNNING_DAYS["sun"])
    workouts.append({
        "date": sun_date.strftime("%Y-%m-%d"),
        "name": f"Week {week_number}: Easy {distances['sun']//1000}km",
        "description": "Easy recovery run - Zone 2",
        "steps": create_easy_run_workout(distances["sun"])
    })
    
    return workouts


def list_plan():
    """Display parsed plan for all weeks."""
    weeks, paces = parse_plan()
    
    print("\n=== Parsed Training Plan ===\n")
    print(f"{'Week':<6} {'Phase':<18} {'Volume':<10} {'Key Workout':<40}")
    print("-" * 80)
    
    for week_num in sorted(weeks.keys()):
        w = weeks[week_num]
        key = parse_key_workout(w["key_workout"])
        print(f"{week_num:<6} {w['phase']:<18} {w['volume']:<10} {w['key_workout']:<40}")
    
    print("\n=== Target Paces by Phase ===\n")
    for phase, pace_info in paces.items():
        print(f"{phase.title()}: Easy={pace_info['easy']}, Tempo={pace_info['tempo']}, Intervals={pace_info['intervals']}")


def create_workouts(week_number, dry_run=False):
    """Create and schedule workouts for a specific week."""
    
    workouts = get_week_workouts(week_number)
    
    if not workouts:
        print(f"No workouts generated for Week {week_number}")
        return
    
    if dry_run:
        print(f"\n=== Week {week_number} Workouts (DRY RUN) ===\n")
        for w in workouts:
            print(f"  {w['date']}: {w['name']}")
            print(f"    {w['description']}")
            print(f"    Steps: {len(w['steps'])}")
        
        # Show volume calculation
        weeks, _ = parse_plan()
        if week_number in weeks:
            print(f"\nPlanned volume: {weeks[week_number]['volume']}km")
            print(f"Key workout: {weeks[week_number]['key_workout']}")
        
        print(f"\nTotal: {len(workouts)} workouts")
        print("\nRun without --dry-run to create these workouts in Garmin Connect")
        return
    
    # Check credentials
    if not GARMIN_EMAIL or not GARMIN_PASSWORD:
        print("ERROR: GARMIN_EMAIL and GARMIN_PASSWORD must be set in .env file")
        sys.exit(1)
    
    # Login
    print(f"Creating Week {week_number} workouts...")
    print("Authenticating with Garmin Connect...")
    
    from garminconnect import Garmin
    
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
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"\n✓ Successfully created: {len(created)}/{len(workouts)}\n")
    
    if created:
        for w in created:
            scheduled = "" if w.get('scheduled', True) else " (not scheduled)"
            print(f"  • {w['date']}: {w['name']}{scheduled}")
    
    if failed:
        print(f"\n✗ Failed: {len(failed)}\n")
        for w in failed:
            print(f"  • {w['name']}: {w['error']}")
    
    print("\n" + "=" * 60)
    print("Next: Sync your Garmin watch via Garmin Connect app")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description='Create Garmin workouts for a specific week (auto-generated from plan.md)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/create-garmin-workouts.py --week 3
  python scripts/create-garmin-workouts.py --week 4 --dry-run
  python scripts/create-garmin-workouts.py --list
        """
    )
    parser.add_argument(
        '--week',
        type=int,
        help='Week number (1-20)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview workouts without creating them'
    )
    parser.add_argument(
        '--list',
        action='store_true',
        help='List all weeks from plan.md'
    )
    
    args = parser.parse_args()
    
    if args.list:
        list_plan()
        return
    
    if not args.week:
        parser.error("--week is required unless using --list")
    
    if args.week < 1 or args.week > 20:
        print("Error: Week must be between 1 and 20")
        sys.exit(1)
    
    create_workouts(args.week, args.dry_run)


if __name__ == '__main__':
    main()
