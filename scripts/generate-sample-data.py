#!/usr/bin/env python3
"""
Generate realistic sample running data for GitHub demonstrations.

Creates a synthetic runner profile targeting sub-2hr HM (1:55-2:00) with 12 months
of training data including:
- 180+ activities with realistic pacing, HR, cadence variations
- Workout types: easy runs, tempo, long runs, interval sessions
- Sleep and recovery data
- Training status evolution
- Lap-level splits with pace variations

Usage:
    python scripts/generate-sample-data.py
    
Output:
    sample-data/unified-cache.json
    sample-data/garmin-cache.json
    sample-data/strava-cache.json
"""

import json
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple


# ============================================================================
# RUNNER PROFILE (Sub-2hr HM Target)
# ============================================================================
RUNNER_PROFILE = {
    "target_hm_time": "1:55:00",  # 5:27/km pace
    "target_hm_pace_min_km": 5.45,  # minutes per km
    "vo2max_range": (41, 45),
    "resting_hr_range": (56, 62),
    "max_hr": 185,
    "weekly_volume_range": (15, 35),  # km
    "long_run_range": (15, 22),  # km
}

# HR Zones (based on max HR 185)
HR_ZONES = [
    {"zoneNumber": 1, "zoneLowBoundary": 96, "zoneHighBoundary": 114},   # Z1: 52-62%
    {"zoneNumber": 2, "zoneLowBoundary": 114, "zoneHighBoundary": 133},  # Z2: 62-72%
    {"zoneNumber": 3, "zoneLowBoundary": 133, "zoneHighBoundary": 151},  # Z3: 72-82%
    {"zoneNumber": 4, "zoneLowBoundary": 151, "zoneHighBoundary": 170},  # Z4: 82-92%
    {"zoneNumber": 5, "zoneLowBoundary": 170, "zoneHighBoundary": 185},  # Z5: 92-100%
]


# ============================================================================
# WORKOUT TEMPLATES
# ============================================================================
WORKOUT_TYPES = {
    "easy": {
        "weight": 0.60,  # 60% of all runs
        "pace_range": (6.5, 7.5),  # min/km (slower for easy)
        "distance_range": (5, 12),  # km
        "hr_zone": 2,  # Z2
        "hr_range": (135, 155),
        "cadence_range": (155, 162),
        "names": ["Morning Easy Run", "Recovery Run", "Easy Aerobic Run", "Base Building Run"],
    },
    "tempo": {
        "weight": 0.20,  # 20% of runs
        "pace_range": (5.5, 6.0),  # min/km (tempo pace)
        "distance_range": (8, 14),  # km
        "hr_zone": 3,  # Z3
        "hr_range": (160, 170),
        "cadence_range": (160, 167),
        "names": ["Tempo Run", "Threshold Workout", "Steady State Run", "Marathon Pace Run"],
    },
    "long": {
        "weight": 0.15,  # 15% of runs (1 per week)
        "pace_range": (6.0, 6.75),  # min/km (slower for long runs)
        "distance_range": (15, 22),  # km
        "hr_zone": 2,  # Z2-Z3
        "hr_range": (140, 160),
        "cadence_range": (156, 163),
        "names": ["Long Run", "Sunday Long Run", "Weekend Long Run", "Endurance Run"],
    },
    "intervals": {
        "weight": 0.05,  # 5% of runs
        "pace_range": (5.0, 5.5),  # min/km (faster intervals)
        "distance_range": (8, 12),  # km (including warmup/cooldown)
        "hr_zone": 4,  # Z4
        "hr_range": (165, 178),
        "cadence_range": (162, 170),
        "names": ["Interval Session", "Track Workout", "Speed Work", "VO2max Intervals"],
    },
}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def pace_to_speed_mps(pace_min_km: float) -> float:
    """Convert pace (min/km) to speed (m/s)"""
    return 1000 / (pace_min_km * 60)


def speed_to_pace_str(speed_mps: float) -> str:
    """Convert speed (m/s) to pace string (M:SS)"""
    pace_seconds = 1000 / speed_mps
    minutes = int(pace_seconds // 60)
    seconds = int(pace_seconds % 60)
    return f"{minutes}:{seconds:02d}"


def calculate_hr_zones(avg_hr: int, duration_seconds: float) -> List[Dict]:
    """Generate realistic HR zone distribution"""
    # Find primary zone
    primary_zone = 1
    for zone in HR_ZONES:
        if zone["zoneLowBoundary"] <= avg_hr < zone["zoneHighBoundary"]:
            primary_zone = zone["zoneNumber"]
            break
    
    # Distribute time across zones with primary zone getting most time
    zone_distribution = []
    remaining_seconds = duration_seconds
    
    for zone in HR_ZONES:
        if zone["zoneNumber"] == primary_zone:
            # Primary zone gets 60-80% of time
            secs = duration_seconds * random.uniform(0.60, 0.80)
        elif abs(zone["zoneNumber"] - primary_zone) == 1:
            # Adjacent zones get 10-20% each
            secs = duration_seconds * random.uniform(0.05, 0.15)
        else:
            # Other zones get 0-5%
            secs = duration_seconds * random.uniform(0.0, 0.05)
        
        zone_distribution.append({
            "zoneNumber": zone["zoneNumber"],
            "secsInZone": round(secs, 3),
            "zoneLowBoundary": zone["zoneLowBoundary"]
        })
    
    # Normalize to ensure sum equals duration
    total_secs = sum(z["secsInZone"] for z in zone_distribution)
    for zone in zone_distribution:
        zone["secsInZone"] = round(zone["secsInZone"] * duration_seconds / total_secs, 3)
    
    return zone_distribution


def generate_lap_splits(distance_km: float, avg_pace_min_km: float, avg_hr: int, 
                        avg_cadence: float, workout_type: str) -> List[Dict]:
    """Generate realistic per-kilometer lap splits with variations"""
    num_laps = int(distance_km)
    laps = []
    
    # Pace variation patterns
    if workout_type == "intervals":
        # Intervals: warmup slow, fast repeats, cooldown
        pace_multipliers = [1.15, 1.1] + [0.85, 1.3, 0.85, 1.3, 0.85, 1.3] + [1.2, 1.15]
    elif workout_type == "tempo":
        # Tempo: warmup, steady, slight fade
        pace_multipliers = [1.1, 1.05] + [1.0] * (num_laps - 4) + [1.02, 1.05]
    elif workout_type == "long":
        # Long run: start conservative, slight positive split
        fade_factor = random.uniform(0.02, 0.08)  # 2-8% fade
        pace_multipliers = [1.05] + [1.0 + (i * fade_factor / num_laps) for i in range(1, num_laps)]
    else:
        # Easy run: fairly consistent
        pace_multipliers = [1.0 + random.uniform(-0.03, 0.03) for _ in range(num_laps)]
    
    # Ensure we have enough multipliers
    while len(pace_multipliers) < num_laps:
        pace_multipliers.append(1.0)
    pace_multipliers = pace_multipliers[:num_laps]
    
    cumulative_duration = 0
    for i in range(num_laps):
        lap_pace = avg_pace_min_km * pace_multipliers[i]
        lap_speed = pace_to_speed_mps(lap_pace)
        lap_duration = 1000 / lap_speed
        
        # HR variation (increases slightly over run, more for long runs)
        hr_drift = 0
        if workout_type == "long" and i > num_laps * 0.5:
            hr_drift = int((i / num_laps) * random.uniform(5, 10))
        lap_hr = min(avg_hr + hr_drift + random.randint(-3, 3), 185)
        
        # Cadence variation
        lap_cadence = avg_cadence + random.uniform(-2, 2)
        
        # Stride length (derived from speed and cadence)
        # stride_length (cm) = speed (m/s) / (cadence (steps/min) / 60) * 100
        stride_length = (lap_speed / (lap_cadence / 60)) * 100
        
        laps.append({
            "lapIndex": i + 1,
            "distance": 1000.0,
            "duration": round(lap_duration, 3),
            "averageSpeed": round(lap_speed, 3),
            "averageHR": lap_hr,
            "maxHR": min(lap_hr + random.randint(5, 12), 185),
            "averageRunCadence": round(lap_cadence, 2),
            "strideLength": round(stride_length, 2),
        })
        
        cumulative_duration += lap_duration
    
    # Add final partial lap if needed
    remaining_distance = (distance_km - num_laps) * 1000
    if remaining_distance > 100:  # Only if > 100m
        lap_pace = avg_pace_min_km * pace_multipliers[-1]
        lap_speed = pace_to_speed_mps(lap_pace)
        lap_duration = remaining_distance / lap_speed
        lap_cadence = avg_cadence + random.uniform(-2, 2)
        stride_length = (lap_speed / (lap_cadence / 60)) * 100
        
        laps.append({
            "lapIndex": num_laps + 1,
            "distance": round(remaining_distance, 1),
            "duration": round(lap_duration, 3),
            "averageSpeed": round(lap_speed, 3),
            "averageHR": min(avg_hr + random.randint(-2, 5), 185),
            "maxHR": min(avg_hr + random.randint(5, 15), 185),
            "averageRunCadence": round(lap_cadence, 2),
            "strideLength": round(stride_length, 2),
        })
    
    return laps


def generate_activity(activity_id: int, date: datetime, workout_type: str) -> Dict:
    """Generate a single realistic running activity"""
    template = WORKOUT_TYPES[workout_type]
    
    # Generate base metrics
    distance_km = round(random.uniform(*template["distance_range"]), 2)
    avg_pace_min_km = random.uniform(*template["pace_range"])
    avg_speed_mps = pace_to_speed_mps(avg_pace_min_km)
    duration_seconds = distance_km * 1000 / avg_speed_mps
    
    avg_hr = random.randint(*template["hr_range"])
    max_hr = min(avg_hr + random.randint(10, 20), 185)
    avg_cadence = random.uniform(*template["cadence_range"])
    
    # Elevation (random but realistic for varied terrain)
    elevation_gain_m = round(distance_km * random.uniform(3, 12), 2)
    
    # Calories (rough estimate: 60-80 per km based on intensity)
    cal_per_km = 55 if workout_type == "easy" else 70 if workout_type == "tempo" else 65
    calories = int(distance_km * cal_per_km * random.uniform(0.9, 1.1))
    
    # Generate lap splits
    lap_splits = generate_lap_splits(distance_km, avg_pace_min_km, avg_hr, avg_cadence, workout_type)
    
    # HR zones
    hr_zones = calculate_hr_zones(avg_hr, duration_seconds)
    
    # Activity name
    name = random.choice(template["names"])
    
    # Format datetime
    date_str = date.strftime("%Y-%m-%d %H:%M:%S")
    
    activity = {
        "id": activity_id,
        "name": name,
        "type": "running",
        "date": date_str,
        "distance_km": distance_km,
        "duration_seconds": round(duration_seconds, 2),
        "avg_pace_min_km": speed_to_pace_str(avg_speed_mps),
        "elevation_gain_m": elevation_gain_m,
        "avg_hr": avg_hr,
        "max_hr": max_hr,
        "calories": calories,
        "avg_cadence": round(avg_cadence, 2),
        "splits": {
            "activityId": activity_id,
            "lapDTOs": lap_splits
        },
        "hr_zones": hr_zones,
        "source": "garmin",
    }
    
    return activity


def select_workout_type(week_num: int, day_of_week: int, activities_this_week: int) -> str:
    """Select workout type based on training plan logic"""
    # Saturday/Sunday long run (once per week)
    if day_of_week in [5, 6] and activities_this_week < 4:
        if random.random() < 0.7:  # 70% chance of long run on weekend
            return "long"
    
    # Midweek tempo/intervals
    if day_of_week in [2, 3] and activities_this_week > 0:
        if random.random() < 0.25:  # 25% chance of quality workout
            return "intervals" if random.random() < 0.2 else "tempo"
    
    # Default to weighted random
    rand = random.random()
    cumulative = 0
    for workout_type, template in WORKOUT_TYPES.items():
        cumulative += template["weight"]
        if rand <= cumulative:
            return workout_type
    
    return "easy"


def generate_12_months_activities(start_date: datetime) -> List[Dict]:
    """Generate 12 months of realistic training activities"""
    activities = []
    current_date = start_date
    end_date = start_date + timedelta(days=365)
    activity_id = 10000000000  # Start with realistic ID
    
    week_num = 0
    activities_this_week = 0
    last_week_start = current_date
    
    # Track weekly volume for red weeks (randomized violations)
    red_weeks = set()
    # Generate ~20% red weeks randomly distributed
    total_weeks = 52
    num_red_weeks = int(total_weeks * 0.20)
    red_weeks = set(random.sample(range(total_weeks), num_red_weeks))
    
    while current_date < end_date:
        # Check if new week started
        if (current_date - last_week_start).days >= 7:
            week_num += 1
            activities_this_week = 0
            last_week_start = current_date
        
        day_of_week = current_date.weekday()  # 0=Monday, 6=Sunday
        
        # Determine if we should run today
        # Pattern: typically 3-5 runs per week (Mon, Wed, Fri, Sat/Sun)
        should_run = False
        
        if week_num in red_weeks:
            # Red weeks: only 1-2 runs
            if activities_this_week < 2 and random.random() < 0.3:
                should_run = True
        else:
            # Normal weeks: 3-5 runs
            target_runs = random.randint(3, 5) if week_num not in red_weeks else random.randint(1, 2)
            
            # Prefer Mon, Wed, Fri, Sat, Sun
            if day_of_week in [0, 2, 4, 5, 6]:
                if activities_this_week < target_runs:
                    should_run = random.random() < 0.65
            elif activities_this_week < target_runs - 1:
                should_run = random.random() < 0.3
        
        if should_run:
            # Select workout type
            workout_type = select_workout_type(week_num, day_of_week, activities_this_week)
            
            # Adjust for red weeks (shorter distances)
            if week_num in red_weeks and workout_type == "long":
                workout_type = "easy"  # No long runs in red weeks
            
            # Set time (morning runs, 6-8am)
            run_time = current_date.replace(
                hour=random.randint(6, 8),
                minute=random.randint(0, 59),
                second=random.randint(0, 59)
            )
            
            activity = generate_activity(activity_id, run_time, workout_type)
            activities.append(activity)
            
            activity_id += 1
            activities_this_week += 1
        
        current_date += timedelta(days=1)
    
    return activities


def generate_sleep_data(start_date: datetime, num_days: int = 365) -> List[Dict]:
    """Generate realistic daily sleep data"""
    sleep_records = []
    current_date = start_date
    
    for i in range(num_days):
        day_of_week = current_date.weekday()
        
        # Weekday vs weekend sleep patterns
        if day_of_week < 5:  # Monday-Friday
            sleep_hours = random.uniform(6.5, 7.5)
        else:  # Weekend
            sleep_hours = random.uniform(7.5, 9.0)
        
        sleep_seconds = int(sleep_hours * 3600)
        
        # Sleep stage distribution
        deep_pct = random.uniform(0.12, 0.20)
        light_pct = random.uniform(0.50, 0.60)
        rem_pct = random.uniform(0.18, 0.25)
        awake_pct = 1.0 - deep_pct - light_pct - rem_pct
        
        deep_sleep_seconds = int(sleep_seconds * deep_pct)
        light_sleep_seconds = int(sleep_seconds * light_pct)
        rem_sleep_seconds = int(sleep_seconds * rem_pct)
        awake_seconds = sleep_seconds - deep_sleep_seconds - light_sleep_seconds - rem_sleep_seconds
        
        # Sleep score (higher on weekends, varies)
        base_score = 80 if day_of_week >= 5 else 75
        sleep_score = int(base_score + random.uniform(-10, 15))
        sleep_score = max(50, min(100, sleep_score))
        
        sleep_records.append({
            "date": current_date.strftime("%Y-%m-%d"),
            "sleep_seconds": sleep_seconds,
            "sleep_hours": round(sleep_hours, 1),
            "deep_sleep_seconds": deep_sleep_seconds,
            "light_sleep_seconds": light_sleep_seconds,
            "rem_sleep_seconds": rem_sleep_seconds,
            "awake_seconds": awake_seconds,
            "sleep_score": sleep_score,
        })
        
        current_date += timedelta(days=1)
    
    return sleep_records


def generate_stress_data(start_date: datetime, num_days: int = 365) -> List[Dict]:
    """Generate realistic daily stress data"""
    stress_records = []
    current_date = start_date
    
    for i in range(num_days):
        day_of_week = current_date.weekday()
        
        # Weekday vs weekend stress patterns
        if day_of_week < 5:  # Weekday - higher stress
            avg_stress = random.randint(25, 45)
            max_stress = avg_stress + random.randint(20, 40)
            rest_stress = random.randint(20, 35)
            activity_stress = random.randint(35, 60)
            low_stress_pct = random.randint(45, 65)
            medium_stress_pct = random.randint(25, 40)
        else:  # Weekend - lower stress
            avg_stress = random.randint(15, 30)
            max_stress = avg_stress + random.randint(15, 30)
            rest_stress = random.randint(15, 25)
            activity_stress = random.randint(25, 45)
            low_stress_pct = random.randint(60, 80)
            medium_stress_pct = random.randint(15, 30)
        
        stress_records.append({
            "date": current_date.strftime("%Y-%m-%d"),
            "avg_stress": avg_stress,
            "max_stress": max_stress,
            "rest_stress": rest_stress,
            "activity_stress": activity_stress,
            "low_stress_pct": low_stress_pct,
            "medium_stress_pct": medium_stress_pct,
        })
        
        current_date += timedelta(days=1)
    
    return stress_records


def generate_training_status() -> Dict:
    """Generate current training status metrics"""
    vo2max = round(random.uniform(*RUNNER_PROFILE["vo2max_range"]), 1)
    resting_hr = random.randint(*RUNNER_PROFILE["resting_hr_range"])
    
    return {
        "vo2max": vo2max,
        "vo2max_running": vo2max,
        "training_load_7d": random.randint(250, 450),
        "training_load_28d": random.randint(1000, 1800),
        "training_effect_label": random.choice([
            "Productive", "Productive", "Maintaining", "Productive"
        ]),
        "recovery_time_hours": random.randint(12, 48),
        "resting_hr": resting_hr,
        "resting_hr_7d_avg": resting_hr + random.randint(-2, 2),
        "fetched_at": datetime.now().isoformat(),
    }


def main():
    """Generate complete sample dataset"""
    print("🏃 Generating sample running data for GitHub demonstrations...")
    print(f"📅 Date range: 12 months from Jan 2025")
    print(f"🎯 Runner profile: Sub-2hr HM target (1:55-2:00)")
    print()
    
    # Start date: 12 months ago from today
    start_date = datetime(2025, 1, 18, 6, 0, 0)
    
    # Generate activities
    print("Generating activities...")
    activities = generate_12_months_activities(start_date)
    print(f"  ✓ Created {len(activities)} activities")
    
    # Generate sleep data
    print("Generating sleep data...")
    sleep_data = generate_sleep_data(start_date, num_days=365)
    print(f"  ✓ Created {len(sleep_data)} sleep records")
    
    # Generate stress data
    print("Generating stress data...")
    stress_data = generate_stress_data(start_date, num_days=365)
    print(f"  ✓ Created {len(stress_data)} stress records")
    
    # Generate training status
    print("Generating training status...")
    training_status = generate_training_status()
    print(f"  ✓ Created training status")
    
    # Build unified cache structure
    unified_cache = {
        "last_sync": datetime.now().isoformat(),
        "build_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "sources": {
            "garmin": len(activities),
            "strava_recent": 0,
            "strava_historical": 0,
            "duplicates_merged": 0,
        },
        "activities": activities,
        "training_status": training_status,
        "sleep": sleep_data,
        "stress": stress_data,
    }
    
    # Build garmin cache structure (subset for compatibility)
    garmin_cache = {
        "last_sync": datetime.now().isoformat(),
        "activities": activities,
        "training_status": training_status,
        "sleep": sleep_data,
        "stress": stress_data,
    }
    
    # Build strava cache (empty for sample data)
    strava_cache = {
        "last_sync": datetime.now().isoformat(),
        "activities": [],
        "athlete_profile": {},
    }
    
    # Create sample-data directory
    sample_dir = Path(__file__).parent.parent / "sample-data"
    sample_dir.mkdir(exist_ok=True)
    
    # Write cache files
    print("\nWriting cache files...")
    
    unified_file = sample_dir / "unified-cache.json"
    with open(unified_file, 'w', encoding='utf-8') as f:
        json.dump(unified_cache, f, indent=2)
    print(f"  ✓ {unified_file}")
    
    garmin_file = sample_dir / "garmin-cache.json"
    with open(garmin_file, 'w', encoding='utf-8') as f:
        json.dump(garmin_cache, f, indent=2)
    print(f"  ✓ {garmin_file}")
    
    strava_file = sample_dir / "strava-cache.json"
    with open(strava_file, 'w', encoding='utf-8') as f:
        json.dump(strava_cache, f, indent=2)
    print(f"  ✓ {strava_file}")
    
    # Summary statistics
    print("\n" + "="*60)
    print("📊 SAMPLE DATA SUMMARY")
    print("="*60)
    print(f"Total activities: {len(activities)}")
    print(f"Date range: {activities[0]['date']} to {activities[-1]['date']}")
    print(f"Total distance: {sum(a['distance_km'] for a in activities):.1f} km")
    print(f"Avg weekly volume: {sum(a['distance_km'] for a in activities) / 52:.1f} km")
    
    # Workout type distribution
    workout_counts = {}
    for activity in activities:
        name_prefix = activity['name'].split()[0]
        workout_counts[name_prefix] = workout_counts.get(name_prefix, 0) + 1
    
    print("\nWorkout distribution:")
    for workout, count in sorted(workout_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {workout}: {count} ({count/len(activities)*100:.1f}%)")
    
    print(f"\nVO2max: {training_status['vo2max']}")
    print(f"Resting HR: {training_status['resting_hr']} bpm")
    print(f"Training Load (7d): {training_status['training_load_7d']}")
    print(f"Training Effect: {training_status['training_effect_label']}")
    
    print("\n✅ Sample data generation complete!")
    print("\n💡 To use this data in the dashboard:")
    print("   $env:USE_SAMPLE_DATA='true'; streamlit run dashboard/app.py")
    print("\n💡 To return to your personal data:")
    print("   Remove-Item Env:\\USE_SAMPLE_DATA; streamlit run dashboard/app.py")


if __name__ == "__main__":
    main()
