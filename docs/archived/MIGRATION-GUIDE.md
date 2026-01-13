# Data Storage Architecture Migration Guide

## Overview

We're transitioning from **on-the-fly merging** to **pre-built unified cache** for better performance and cleaner architecture.

### Why This Change?

**Before (Legacy):**
- Dashboard merged Garmin + Strava data on every page load
- Slow and inefficient
- Risk of data loss during incremental syncs (overwriting historical data)

**After (New):**
- Pre-merged unified cache built once
- Dashboard loads single cache file (faster)
- Clean separation: historical archive + recent splits + Garmin primary
- No risk of data loss

## New Storage Architecture

```
tracking/
├── garmin-cache.json                 # PRIMARY: Rolling 180 days (sync daily)
├── strava-historical-archive.json    # FROZEN: 2022-01-01 to 2025-03-22
├── strava-recent-splits.json         # TRANSITION: Last 8 weeks with splits
└── unified-cache.json                # DASHBOARD USES THIS (pre-merged)
```

### Data Sources by Date Range

| Date Range | Source | Status | Notes |
|------------|--------|--------|-------|
| 2022-01-01 to 2025-03-22 | Strava | FROZEN | Historical archive (434 activities) |
| 2025-01-01 to 2025-03-22 | Strava | FROZEN | Gap period (28 activities) |
| 2025-03-23 onwards | Garmin | PRIMARY | Current training (85 activities) |
| Last 8 weeks | Strava | TRANSITION | Per-km splits (temporary) |

### Key Dates

- **Garmin Start Date**: 2025-03-23 (when lap tracking was enabled)
- **Historical Cutoff**: 2025-03-22 (last day of Strava-only data)
- **Transition Period**: Last 8 weeks (until all Garmin runs have laps)

## One-Time Migration Steps

### Step 1: Create Historical Archive

Split existing `strava-cache.json` into historical archive:

```bash
python scripts/create-strava-archive.py
```

**What this does:**
- Backs up existing `strava-cache.json`
- Creates `strava-historical-archive.json` (2022-01-01 to 2025-03-22)
- Marks archive as FROZEN (read-only)

**Expected output:**
```
✓ Backed up existing cache to: tracking/backups/strava-cache-backup-20260109_HHMMSS.json
✓ Loaded 517 Strava activities

Split results:
  Historical (before 2025-03-23): 434 activities
  Recent (after 2025-03-23): 83 activities

✓ Historical archive created successfully!
  Output: tracking/strava-historical-archive.json
  Status: FROZEN (READ-ONLY)
  Activities: 434
  Date range: 2022-XX-XX to 2025-03-22
```

### Step 2: Fetch Recent Strava Splits

Fetch last 8 weeks from Strava with detailed per-km splits:

```bash
python scripts/sync-strava-recent.py
```

**What this does:**
- Fetches last 8 weeks of activities
- Gets detailed per-km splits for each activity
- Saves to `strava-recent-splits.json`

**Expected output:**
```
✅ Fetched XX activities from last 8 weeks
📊 Fetching detailed splits for XX activities...
✓ Saved XX activities to tracking/strava-recent-splits.json
```

**Note:** This step is only needed during the transition period (next 8 weeks). After that, all new runs will have Garmin laps.

### Step 3: Build Unified Cache

Merge all sources into single pre-built cache:

```bash
python scripts/build-unified-cache.py
```

**What this does:**
- Loads Garmin cache (primary)
- Loads Strava historical archive
- Loads Strava recent splits
- Intelligently merges and deduplicates
- Saves to `unified-cache.json`

**Expected output:**
```
Loading data sources...
✓ Loaded 85 Garmin activities
✓ Loaded 434 Strava historical activities
✓ Loaded XX Strava recent activities (with splits)

Merging 85 Garmin + XX Strava recent + 434 Strava historical...

✓ Unified cache built successfully!
  Output: tracking/unified-cache.json
  Total activities: 520
  Garmin: 85
  Strava recent: XX
  Strava historical: 434
  Date range: 2022-XX-XX to 2026-01-08

✓ Dashboard will now use: tracking/unified-cache.json
```

### Step 4: Test Dashboard

Start the dashboard and verify everything works:

```bash
streamlit run dashboard/app.py
```

**Check:**
- [ ] Landing page shows "Unified" sync time
- [ ] Consistency Guardian shows all 188 weeks
- [ ] Race Confidence shows historical long runs
- [ ] No errors in console

## Daily Workflow (After Migration)

### Standard Daily Sync

```bash
# Sync Garmin (rolling 180 days)
python scripts/sync-garmin.py 7

# Rebuild unified cache (merges new Garmin data)
python scripts/build-unified-cache.py
```

### During Transition Period (Next 8 Weeks)

If you need splits for recent activities without Garmin laps:

```bash
# Sync both
python scripts/sync-garmin.py 7
python scripts/sync-strava-recent.py

# Rebuild unified cache
python scripts/build-unified-cache.py
```

### After Transition (8+ Weeks from Now)

Once all Garmin activities have laps, you can stop syncing Strava:

```bash
# Only sync Garmin
python scripts/sync-garmin.py 7

# Rebuild unified cache
python scripts/build-unified-cache.py
```

## What Each Script Does

### `create-strava-archive.py` (One-time)
- Splits existing Strava data into historical archive
- Creates backup before modifying
- Marks archive as FROZEN

### `sync-strava-recent.py` (Transition period)
- Fetches last 8 weeks only
- Gets detailed per-km splits
- Used during transition until Garmin has all laps

### `build-unified-cache.py` (Daily)
- Merges all sources into single cache
- Smart deduplication (prefers Garmin)
- Dashboard uses this file

### `sync-garmin.py` (Daily)
- Primary data source going forward
- Rolling 180 days
- Has lap data for all new runs

## Rollback Plan

If something goes wrong, you can roll back:

1. **Restore backup:**
   ```bash
   cp tracking/backups/strava-cache-backup-YYYYMMDD_HHMMSS.json tracking/strava-cache.json
   ```

2. **Delete new files:**
   ```bash
   rm tracking/unified-cache.json
   rm tracking/strava-historical-archive.json
   rm tracking/strava-recent-splits.json
   ```

3. **Dashboard will automatically fall back to legacy merge mode**

## Architecture Benefits

### Performance
- **Before**: Merge 520 activities on every page load
- **After**: Load pre-merged cache (10x faster)

### Data Safety
- Historical archive is FROZEN (can't be overwritten)
- Incremental syncs update unified cache, not historical data
- Backups created automatically

### Simplicity
- Dashboard code is simpler (no merge logic)
- Clear separation of concerns
- Easy to understand what data comes from where

### Future-Proof
- Garmin becomes sole data source
- Strava data preserved as historical archive
- No more sync conflicts

## FAQ

**Q: What happens to my existing strava-cache.json?**
A: It's backed up automatically. After migration, it's no longer used by the dashboard.

**Q: How long is the transition period?**
A: 8 weeks from now (until all Garmin activities have laps). After that, stop syncing Strava.

**Q: What if I want to re-fetch Strava data?**
A: The historical archive is FROZEN. If you need to re-fetch, rename it first to preserve the archive.

**Q: Do I need to rebuild unified cache every time?**
A: Yes, after every Garmin sync. It's fast (<1 second) and ensures dashboard has latest data.

**Q: What if Garmin sync fails?**
A: Unified cache still has previous data. Dashboard continues to work.

**Q: Can I delete the old Strava cache?**
A: Keep it as backup for a few weeks. Once you're confident, you can archive it.

## Troubleshooting

### Error: "Could not load unified cache"
- Check if `unified-cache.json` exists
- Run `python scripts/build-unified-cache.py`
- Dashboard will fall back to legacy mode if unified cache is missing

### Missing Activities
- Check date ranges in unified cache metadata
- Verify historical archive has expected activities
- Check Garmin start date (2025-03-23)

### Slow Dashboard
- Ensure unified cache exists
- Check dashboard logs for "Using unified cache" message
- If using legacy mode, rebuild unified cache

### Duplicate Activities
- Run `build-unified-cache.py` again
- Check merge logic prefers Garmin
- Verify no manual edits to cache files

## Next Steps

After successful migration:

1. Update `QUICK-START.md` with new workflow
2. Update `.gitignore` to exclude new cache files
3. Document transition period end date (8 weeks from now)
4. Plan to remove Strava sync after transition
