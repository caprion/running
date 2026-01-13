# Consistency Guardian

Track your weekly running volume and identify floor violations.

## What It Does

- Analyzes weekly running volume from your Garmin data
- Flags weeks that fall below the 15km floor (RED ❌)
- Warns about weeks in the 15-20km yellow zone (YELLOW ⚠️)
- Shows weeks above 20km as GREEN ✅
- Compares periods (2025 collapse vs recovery, 2026 current)
- Tracks your current streak of weeks above the floor

## Usage

### View all weeks
```bash
python scripts/consistency-guardian.py
```

### View specific year
```bash
python scripts/consistency-guardian.py --year 2025
```

### View with comparisons and monthly summary
```bash
python scripts/consistency-guardian.py --compare --monthly
```

## Understanding the Output

### Weekly Report
Shows each week with:
- Week number (e.g., 2025-W45)
- Number of runs
- Total distance
- Status (✅ GREEN / ⚠️ YELLOW / ❌ RED)
- Dates of runs

### Period Comparison
Compares:
- **2025 Jan-Jul (Collapse)**: Your low-volume period
- **2025 Aug-Dec (Recovery)**: Chennai HM prep
- **2026 YTD (Current)**: Your current season

Shows violations as a percentage to track improvement.

### Monthly Summary
Average km/week per month with status indicator.

### Current Streak
Shows how many consecutive weeks you've been above the 15km floor.

## Key Thresholds

- **<15km**: ❌ FLOOR VIOLATION - Risk of detraining
- **15-20km**: ⚠️ YELLOW - Minimum viable volume
- **≥20km**: ✅ GREEN - Sustainable training volume

## Tips

1. **Run this weekly** after syncing Garmin data:
   ```bash
   python scripts/sync-garmin.py 7
   python scripts/consistency-guardian.py --year 2026 --compare
   ```

2. **Set a goal**: Aim for 0 floor violations in 2026

3. **Track your streak**: Try to build the longest green streak possible

4. **Use as motivation**: Seeing red weeks is a wake-up call to get back on track

## Integration with Weekly Check-ins

During your weekly check-ins with Claude, run:
```bash
python scripts/consistency-guardian.py --year 2026 --compare
```

This gives you:
- Current week status
- Year-to-date pattern
- Comparison to 2025 collapse/recovery periods
- Immediate feedback if you're trending toward a floor violation
