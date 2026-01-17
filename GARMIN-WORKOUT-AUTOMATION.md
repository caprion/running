# Garmin Workout Automation

## ✅ WORKING: Automated Workout Creation

**Simple, clean solution for creating Garmin workouts from your training plan.**

### Quick Start

```bash
# Preview workouts for a week (dry run)
python scripts/create-garmin-workouts.py --week 3 --dry-run

# Create and schedule workouts for a week
python scripts/create-garmin-workouts.py --week 3
```

### What It Does

- ✓ Creates structured workouts in Garmin Connect
- ✓ Schedules them to the correct dates
- ✓ Supports tempo runs with pace targets
- ✓ Uses lap button for flexible warmup/cooldown
- ✓ Simple Python script - no complex dependencies

### Week 3 Example (Created Jan 17, 2026)

| Date | Day | Workout |
|------|-----|---------|
| Jan 20 | Tue | Easy 7km |
| Jan 22 | Thu | Tempo 4km @ 5:55/km |
| Jan 24 | Sat | Long Run 14km |
| Jan 25 | Sun | Easy 6km |

### Adding New Weeks

Edit `scripts/create-garmin-workouts.py` and add workout definitions to the `get_week_workouts()` function.

See Week 3 as a template - copy the structure and adjust distances/paces.

**Documentation:**
- [Full Guide](docs/garmin-workout-creation-guide.md) - API format and examples
- [Quick Reference](docs/garmin-api-quick-reference.md) - IDs and common patterns

---

## Technical Details

### Garmin API Format

**Required structure for each workout step:**
```json
{
  "type": "ExecutableStepDTO",  // REQUIRED
  "stepOrder": 1,
  "stepType": {"stepTypeId": 3},
  "endCondition": {"conditionTypeId": 3},
  "endConditionValue": 5000.0,
  "targetType": {"workoutTargetTypeId": 1}
}
```

**Key IDs:**
- Step Types: 1=warmup, 2=cooldown, 3=interval
- End Conditions: 1=lap button, 2=time, 3=distance
- Target Types: 1=open, 4=HR zone, 6=pace

**Pace conversion:** min/km to m/s
```python
# 6:00/km = 1000m / 360s = 2.778 m/s
# 5:55/km = 1000m / 355s = 2.817 m/s
```

See [Quick Reference](docs/garmin-api-quick-reference.md) for complete API documentation.

---

## Requirements

```bash
pip install garminconnect python-dotenv
```

### Environment Setup

Create `.env` file:
```
GARMIN_EMAIL=your@email.com
GARMIN_PASSWORD=yourpassword
```

---

## Archived/Unused Components

The following were explored but not used in the final solution:
- Excel parser (we define workouts directly in Python)
- JSON builder module (inline creation is simpler)
- Separate client wrapper (using garminconnect library directly)

These have been removed to keep the codebase clean and maintainable.

---

## Usage Examples

### Create Week 3 Workouts
```bash
python scripts/create-garmin-workouts.py --week 3
```

### Preview Week 4 (Dry Run)
```bash
python scripts/create-garmin-workouts.py --week 4 --dry-run
```

### Adding a New Week

1. Open `scripts/create-garmin-workouts.py`
2. Find the `get_week_workouts()` function
3. Add a new `elif` block for your week number
4. Copy the Week 3 structure and modify dates/distances/paces

Example:
```python
elif week_number == 4:
    return [
        {
            "date": "2026-01-27",
            "name": "Week 4: Easy 6km",
            "description": "Easy run - Zone 2",
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
        },
        # ... more workouts
    ]
```

---

## Summary

**Status:** ✅ Working solution for automated Garmin workout creation

**What it does:**
- Creates structured workouts in Garmin Connect
- Schedules to correct dates
- Supports pace targets, lap button, HR zones
- Simple Python script, no complex dependencies

**Going forward:**
- Use `python scripts/create-garmin-workouts.py --week N` to create each week
- Add workout definitions as needed in the script
- Sync Garmin watch to receive workouts

**Documentation:**
- [Garmin Workout Creation Guide](docs/garmin-workout-creation-guide.md)
- [API Quick Reference](docs/garmin-api-quick-reference.md)

