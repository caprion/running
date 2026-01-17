# Sample Data - Synthetic Runner Profile

This directory contains anonymized sample data for GitHub demonstrations and testing.

## About the Sample Runner

**Profile:**
- Target: Sub-2 hour half marathon (1:55:00 - 2:00:00)
- Goal pace: 5:27/km - 5:41/km
- VO2max: 42-45 range
- Resting HR: 56-62 bpm
- Max HR: 185 bpm

**Training History:**
- 12 months of data (January 2025 - January 2026)
- 161 total running activities
- Total distance: 1,888 km
- Average weekly volume: 36 km

## Data Characteristics

### Activity Distribution
- **Easy Runs (60%):** 6:30-7:30/km pace, HR 135-155, 5-12km
- **Tempo Runs (20%):** 5:30-6:00/km pace, HR 160-170, 8-14km
- **Long Runs (15%):** 6:00-6:45/km pace, HR 140-160, 15-22km
- **Intervals (5%):** 5:00-5:30/km pace, HR 165-178, 8-12km

### Training Patterns
- 3-5 runs per week
- Weekly long run (Saturday/Sunday)
- Quality sessions midweek
- ~20% red weeks (< 15km) randomly distributed
- Realistic HR drift on long runs (0-10%)
- Pace degradation: <5% on good runs, 5-15% when fatigued

### Additional Data
- **Sleep:** Daily records, 6-9 hours
  - Weekdays: 6.5-7.5 hours
  - Weekends: 7.5-9 hours
  - Sleep stages: Deep (12-20%), Light (50-60%), REM (18-25%)
- **Stress:** Daily metrics
  - Weekday avg: 25-45
  - Weekend avg: 15-30
- **Training Status:**
  - VO2max: 44.6
  - Resting HR: 59 bpm
  - Training Load (7d): 363
  - Training Effect: Productive

## Data Files

- `unified-cache.json` - Complete merged dataset (preferred)
- `garmin-cache.json` - Garmin-only data (legacy compatibility)
- `strava-cache.json` - Empty (sample uses Garmin only)

## Season Plan

Located in `seasons/2025-sample-runner/`:
- `plan.md` - 20-week HM training plan
- `weekly-log-2025-01-18.md` - Sample weekly log (Week 1)

## Privacy & Anonymization

All personal identifiers have been removed or anonymized:
- ✅ No GPS coordinates (set to 0 or random)
- ✅ Generic activity names ("Morning Easy Run", "Tempo Workout")
- ✅ Synthetic activity IDs
- ✅ No personal routes or locations
- ✅ Representative but not actual data

## Using Sample Data

### Dashboard
```powershell
$env:USE_SAMPLE_DATA='true'
streamlit run dashboard/app.py
```

### Return to Personal Data
```powershell
Remove-Item Env:\USE_SAMPLE_DATA
streamlit run dashboard/app.py
```

## Regeneration

To regenerate with different random seed:
```powershell
python scripts/generate-sample-data.py
```

This will create fresh sample data with different random variations while maintaining realistic training patterns.

## Dashboard Screenshots

See `media/dashboard-snapshots/` for visual examples of all dashboard pages using this sample data.
