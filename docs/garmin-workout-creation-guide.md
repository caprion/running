# Garmin Workout Creation - Working Solution

## ✓ Successfully Created Week 3 Workouts

All 4 Week 3 workouts created and scheduled in Garmin Connect:

| Date | Day | Workout | Type | Distance |
|------|-----|---------|------|----------|
| Jan 20 | Tue | Easy 7km | Easy run | 7km |
| Jan 22 | Thu | Tempo 4km @ 5:55 | Tempo with pace target | 4km + warmup/cooldown |
| Jan 24 | Sat | Long Run 14km | Long run | 14km |
| Jan 25 | Sun | Easy 6km | Easy recovery | 6km |

**Total Weekly Volume:** 25km structured workouts

---

## Key Learnings: Garmin Workout API Format

### Critical Format Requirements

The 500 errors we encountered were caused by incorrect JSON structure. Here's what works:

#### 1. **Required Step Structure**
```json
{
  "type": "ExecutableStepDTO",  // ← REQUIRED! Missing this = 500 error
  "stepOrder": 1,
  "stepType": {"stepTypeId": 3},
  "endCondition": {"conditionTypeId": 3},
  "endConditionValue": 5000.0,  // ← Use this, NOT nested "value"
  "targetType": {"workoutTargetTypeId": 1}
}
```

**Key Points:**
- `type`: "ExecutableStepDTO" is **mandatory** for each step
- `endConditionValue` goes at the top level, NOT inside `endCondition`
- Don't need the "Key" fields (like `stepTypeKey`, `conditionTypeKey`) when creating

#### 2. **Step Type IDs**
```python
1 = warmup
2 = cooldown  
3 = interval (main work)
4 = recovery
5 = rest
```

#### 3. **End Condition Type IDs**
```python
1 = lap button press (user-controlled)
2 = time (seconds)
3 = distance (meters)
4 = heart rate
```

#### 4. **Target Type IDs**
```python
1 = no target (open)
4 = heart rate zone
6 = pace zone
```

#### 5. **Pace Values**
When using pace targets (targetTypeId: 6):
- Values are in **meters per second (m/s)**
- Slower pace = lower m/s value
- Example: 
  - 6:00/km = 1000m / 360s = **2.778 m/s**
  - 5:55/km = 1000m / 355s = **2.817 m/s**
- `targetValueOne` = slower pace (lower bound)
- `targetValueTwo` = faster pace (upper bound)

---

## Best Practices for Workout Design

### Warmup/Cooldown Steps
**Use lap button for flexibility:**
```json
{
  "type": "ExecutableStepDTO",
  "stepOrder": 1,
  "stepType": {"stepTypeId": 1},  // warmup
  "endCondition": {"conditionTypeId": 1},  // lap button
  "endConditionValue": 1.0,
  "targetType": {"workoutTargetTypeId": 1}  // no target (open)
}
```
- Lets athlete control warmup/cooldown duration
- Press lap when ready to move to next step

### Tempo/Interval Steps
**Use pace targets:**
```json
{
  "type": "ExecutableStepDTO",
  "stepOrder": 2,
  "stepType": {"stepTypeId": 3},  // interval
  "endCondition": {"conditionTypeId": 3},  // distance
  "endConditionValue": 4000.0,  // 4km
  "targetType": {"workoutTargetTypeId": 6},  // pace
  "targetValueOne": 2.778,  // 6:00/km (slower)
  "targetValueTwo": 2.817   // 5:55/km (faster)
}
```
- Provides clear pace guidance on watch
- Alerts if running too fast/slow

### Easy Runs
**Use open target (no restriction):**
```json
{
  "type": "ExecutableStepDTO",
  "stepOrder": 1,
  "stepType": {"stepTypeId": 3},  // interval
  "endCondition": {"conditionTypeId": 3},  // distance
  "endConditionValue": 7000.0,  // 7km
  "targetType": {"workoutTargetTypeId": 1}  // no target
}
```
- No pace/HR alerts
- Just tracks distance

---

## Working Scripts

### Main Script: Create Workouts by Week

**Use this going forward:** [create-garmin-workouts.py](../scripts/create-garmin-workouts.py)

```bash
# Preview workouts for a week
python scripts/create-garmin-workouts.py --week 3 --dry-run

# Create and schedule workouts
python scripts/create-garmin-workouts.py --week 3
```

**Adding new weeks:**
Edit the `get_week_workouts()` function in the script and add your workout definitions.

### Example: Week 3 Definition
```python
# 1. Define workouts with steps
workouts = [
    {
        "date": "2026-01-21",
        "name": "Week 3: Easy 7km",
        "steps": [...]
    }
]

# 2. Login
client = Garmin(email, password)
client.login()

# 3. Create each workout
for workout_def in workouts:
    response = client.connectapi(
        "/workout-service/workout",
        method="POST",
        json=workout_json
    )
    workout_id = response['workoutId']
    
    # 4. Schedule it
    client.connectapi(
        f"/workout-service/schedule/{workout_id}",
        method="POST",
        json={"date": workout_def['date']}
    )
```

---

## Response Handling

The API returns a dict directly (not a Response object):
```python
response = client.connectapi("/workout-service/workout", method="POST", json=data)

# Response is already parsed JSON (dict)
if 'workoutId' in response:
    workout_id = response['workoutId']
```

---

## Common Errors & Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| 500 Server Error | Missing `type: ExecutableStepDTO` | Add to every step |
| 500 Server Error | Nested `value` in endCondition | Use `endConditionValue` at top level |
| TypeError on response | Expecting `.status_code` | Response is dict, not Response object |
| Pace not working | Wrong units | Use m/s, not min/km |

---

## Next Steps

1. **Sync watch** - Open Garmin Connect app to sync workouts to watch
2. **Verify on watch** - Check Training > Workouts on device
3. **Execute workouts** - Follow structured workouts during training

For automation: Use [create-week3-all.py](scripts/create-week3-all.py) pattern to batch-create future weeks.
