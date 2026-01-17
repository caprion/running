# Garmin Workout API - Quick Reference

## Minimal Working Example

```python
from garminconnect import Garmin

workout = {
    "workoutName": "Easy 5km",
    "sportType": {"sportTypeId": 1},  # running
    "workoutSegments": [{
        "segmentOrder": 1,
        "sportType": {"sportTypeId": 1},
        "workoutSteps": [{
            "type": "ExecutableStepDTO",  # REQUIRED!
            "stepOrder": 1,
            "stepType": {"stepTypeId": 3},
            "endCondition": {"conditionTypeId": 3},
            "endConditionValue": 5000.0,  # 5km in meters
            "targetType": {"workoutTargetTypeId": 1}  # open/no target
        }]
    }]
}

client = Garmin(email, password)
client.login()
response = client.connectapi("/workout-service/workout", method="POST", json=workout)
workout_id = response['workoutId']

# Schedule it
client.connectapi(
    f"/workout-service/schedule/{workout_id}",
    method="POST",
    json={"date": "2026-01-23"}
)
```

## ID Reference

### Step Types
- `1` = Warmup
- `2` = Cooldown
- `3` = Interval/Work
- `4` = Recovery
- `5` = Rest

### End Conditions
- `1` = Lap button press
- `2` = Time (seconds)
- `3` = Distance (meters)
- `4` = Heart rate

### Target Types
- `1` = No target (open)
- `4` = Heart rate zone (1-5)
- `6` = Pace (m/s)

## Pace Conversion

```python
# min/km to m/s
pace_min_per_km = 6.0  # 6:00/km
seconds_per_km = pace_min_per_km * 60  # 360s
meters_per_second = 1000 / seconds_per_km  # 2.778 m/s

# Common paces
# 5:00/km = 3.333 m/s
# 5:30/km = 3.030 m/s
# 6:00/km = 2.778 m/s
# 6:30/km = 2.564 m/s
# 7:00/km = 2.381 m/s
```

## Common Patterns

### Warmup (Lap Button)
```python
{
    "type": "ExecutableStepDTO",
    "stepOrder": 1,
    "stepType": {"stepTypeId": 1},
    "endCondition": {"conditionTypeId": 1},  # lap button
    "endConditionValue": 1.0,
    "targetType": {"workoutTargetTypeId": 1}  # open
}
```

### Tempo Run (Pace Target)
```python
{
    "type": "ExecutableStepDTO",
    "stepOrder": 2,
    "stepType": {"stepTypeId": 3},
    "endCondition": {"conditionTypeId": 3},  # distance
    "endConditionValue": 4000.0,  # 4km
    "targetType": {"workoutTargetTypeId": 6},  # pace
    "targetValueOne": 2.778,  # 6:00/km (slower)
    "targetValueTwo": 2.817   # 5:55/km (faster)
}
```

### Interval (Distance + Pace)
```python
{
    "type": "ExecutableStepDTO",
    "stepOrder": 3,
    "stepType": {"stepTypeId": 3},
    "endCondition": {"conditionTypeId": 3},  # distance
    "endConditionValue": 800.0,  # 800m
    "targetType": {"workoutTargetTypeId": 6},  # pace
    "targetValueOne": 3.125,  # 5:20/km (slower)
    "targetValueTwo": 3.226   # 5:10/km (faster)
}
```

### Recovery (Time + HR Zone)
```python
{
    "type": "ExecutableStepDTO",
    "stepOrder": 4,
    "stepType": {"stepTypeId": 4},  # recovery
    "endCondition": {"conditionTypeId": 2},  # time
    "endConditionValue": 120.0,  # 2 minutes
    "targetType": {"workoutTargetTypeId": 4},  # HR zone
    "targetValueOne": 2,  # Zone 2
    "targetValueTwo": 2
}
```

### Cooldown (Lap Button)
```python
{
    "type": "ExecutableStepDTO",
    "stepOrder": 5,
    "stepType": {"stepTypeId": 2},
    "endCondition": {"conditionTypeId": 1},  # lap button
    "endConditionValue": 1.0,
    "targetType": {"workoutTargetTypeId": 1}  # open
}
```

## Critical Rules

1. ✓ Always include `"type": "ExecutableStepDTO"` in each step
2. ✓ Use `endConditionValue` at top level, not nested
3. ✓ Pace values are in m/s (slower pace = lower value)
4. ✓ Distance in meters, time in seconds
5. ✓ Response is a dict, not a Response object
