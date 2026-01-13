# Garmin Sync Fix Summary

**Date:** January 12, 2026

## Problem Identified

The Garmin sync was **overwriting historical data** instead of merging incrementally.

### What Happened

**Before the fix (Jan 9 backup):**
- 542 total activities in unified cache
- 85 from Garmin (Mar 23, 2025 → Jan 8, 2026)
- 457 from Strava

**After running sync-garmin.py (broken state):**
- 460 total activities
- **Only 3 from Garmin** (Jan 6-10, 2026)
- 457 from Strava
- **Lost 82 Garmin activities!**

### Root Cause

The `sync-garmin.py` script had a fatal design flaw:

```python
# Old behavior (BROKEN):
def sync_all(self, days: int = 7):
    # Fetch only last N days
    self.data['activities'] = self.fetch_activities(days)  # OVERWRITES!
    self.save_cache()  # Saves only the last N days
```

Every sync would:
1. Fetch ONLY the last 7 days from Garmin
2. **OVERWRITE** the entire cache with just those 7 days
3. Lose all historical data older than 7 days
4. Break the dashboards expecting continuous data

## Solution Implemented

### Changes Made to `sync-garmin.py`

1. **Added `load_cache()` method**
   - Loads existing garmin-cache.json on startup
   - Preserves historical data

2. **Added `_merge_activities()` method**
   - Merges new activities with existing ones
   - Deduplicates by activity ID
   - Sorts by date (newest first)

3. **Added `_merge_time_series()` method**
   - Merges sleep, HRV, stress data by date
   - Avoids duplicate date entries

4. **Modified `sync_all()` method**
   - Now MERGES instead of OVERWRITES
   - Preserves all historical activities

```python
# New behavior (FIXED):
def sync_all(self, days: int = 7):
    # Load existing cache first
    self.load_cache()  # Contains all historical data

    # Fetch last N days
    new_activities = self.fetch_activities(days)

    # MERGE with existing (doesn't overwrite)
    self.data['activities'] = self._merge_activities(new_activities)
    self.save_cache()  # Saves merged data
```

### Testing

Created `test-merge-logic.py` to verify:
- ✅ Duplicates are correctly skipped
- ✅ New activities are correctly added
- ✅ Activities are sorted by date (newest first)

All tests passed.

## Current State

### Restored Data

- **unified-cache.json**: ✅ Restored from Jan 9 backup
  - 542 total activities
  - 85 from Garmin (Mar 23, 2025 → Jan 8, 2026)
  - 457 from Strava

- **garmin-cache.json**: 3 activities (Jan 6-10, 2026)
  - This is intentionally not restored
  - Will rebuild gradually with merge logic on future syncs

### Why garmin-cache is out of sync

The two caches serve different purposes:
- **garmin-cache.json**: Source data from Garmin Connect (updated by `sync-garmin.py`)
- **unified-cache.json**: Merged data from Garmin + Strava (built by `build-unified-cache.py`)

We restored unified-cache because:
1. The dashboard reads from unified-cache.json
2. It has the full historical data (542 activities)
3. garmin-cache will rebuild incrementally with the merge fix

## Important Next Steps

### DO NOT run `build-unified-cache.py` yet!

If you run it now, it will:
- Read garmin-cache.json (only 3 activities)
- Rebuild unified-cache.json
- **LOSE 82 Garmin activities again!**

### Safe Workflow Going Forward

**Option A: Gradual rebuild (Recommended)**
1. Continue using `daily-sync.py` as normal
2. The merge logic will incrementally add new activities
3. garmin-cache will grow: 3 → 5 → 8 → etc.
4. After you have ~85 activities in garmin-cache, you can rebuild unified-cache

**Option B: Full resync (Clean slate)**
1. Fetch ALL Garmin history at once:
   ```bash
   python scripts/sync-garmin.py 365  # or more days
   ```
2. This will merge all historical activities into garmin-cache
3. Then rebuild unified-cache:
   ```bash
   python scripts/build-unified-cache.py
   ```

### Monitoring

Check sync results:
```bash
# Check garmin-cache size
python -c "import json; data = json.load(open('tracking/garmin-cache.json')); print(f'{len(data[\"activities\"])} activities')"

# Check unified-cache size
python -c "import json; data = json.load(open('tracking/unified-cache.json')); print(f'{len(data[\"activities\"])} activities')"
```

Expected behavior:
- garmin-cache: Should GROW with each sync (3 → 5 → 8 → etc.)
- unified-cache: Should stay stable or grow (never shrink!)

## Dashboard Status

✅ **Dashboards should be working now**

The dashboards read from unified-cache.json, which has been restored with:
- 542 total activities
- 85 from Garmin (full history Mar 23, 2025 → Jan 8, 2026)
- 457 from Strava

## Files Modified

1. `scripts/sync-garmin.py`
   - Added load_cache() method
   - Added _merge_activities() method
   - Added _merge_time_series() method
   - Modified sync_all() to merge instead of overwrite

2. `scripts/test-merge-logic.py` (new)
   - Unit tests for merge logic

3. `tracking/unified-cache.json`
   - Restored from backup

## Recommendations

1. **Run full resync soon** to rebuild garmin-cache properly:
   ```bash
   python scripts/sync-garmin.py 365
   ```

2. **Monitor the merge messages** in future syncs:
   ```
   [CACHE] Loaded existing cache: N activities
   [MERGE] Merging with existing cache...
      Merged: X new activities added, Y already existed
   ```

3. **Create backup job** to prevent future data loss:
   ```bash
   # Before each sync, backup the caches
   cp tracking/garmin-cache.json tracking/backups/garmin-cache-$(date +%Y%m%d_%H%M%S).json
   cp tracking/unified-cache.json tracking/backups/unified-cache-$(date +%Y%m%d_%H%M%S).json
   ```

4. **Add monitoring** to alert if activity count decreases

## Lessons Learned

- Always merge time-series data incrementally
- Never overwrite historical data
- Test with backups before making sync changes
- Add deduplication logic by ID, not just date
- Keep backups of cache files before major operations
