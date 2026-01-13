# New Incremental Sync Workflow (Jan 2026)

## Architecture Change

**Old (Broken):**
```
garmin-cache + strava-cache → build-unified-cache.py → unified-cache
                               (REBUILDS FROM SCRATCH - DATA LOSS RISK)
```

**New (Safe):**
```
unified-cache (source of truth) ← incremental-sync.py ← Garmin API
                                   (MERGES ONLY - NO DATA LOSS)
```

## Key Changes

### 1. unified-cache.json is now the SINGLE SOURCE OF TRUTH
- Never rebuilt from scratch
- Always updated incrementally
- Preserves all historical data and HR enrichments
- Contains 543 activities (86 Garmin, 457 Strava)

### 2. New Scripts

#### `scripts/incremental-sync.py` (NEW - PRIMARY SYNC)
- Fetches recent activities from Garmin
- Merges into unified-cache (never overwrites)
- Deduplicates by activity ID + date/distance
- Preserves HR data from both sources
- Creates automatic backups before updates
- Has safety checks to prevent data loss

#### `scripts/verify-data-integrity.py` (NEW - MONITORING)
- Checks activity counts
- Monitors HR data completeness
- Compares with baseline to detect data loss
- Alerts if counts decrease

### 3. Modified Scripts

#### `scripts/daily-sync.py` (UPDATED)
- Now calls `incremental-sync.py` instead of `build-unified-cache.py`
- Safe for daily use
- Never loses data

#### `scripts/build-unified-cache.py` (DEPRECATED)
- Added strong warnings
- Requires "REBUILD" confirmation
- Only for disaster recovery
- NOT for daily use

#### `scripts/backfill-hr-streams.py` (DOCUMENTED)
- Already updates unified-cache correctly
- Creates backups before updating
- Safe to run multiple times

## Daily Workflow

### Regular Sync (Recommended)
```bash
# Fetch last 7 days and merge into unified-cache
python scripts/daily-sync.py

# Or use incremental-sync directly
python scripts/incremental-sync.py

# Verify data integrity
python scripts/verify-data-integrity.py
```

### Weekly/Monthly Sync
```bash
# Fetch last 30 days to catch any gaps
python scripts/incremental-sync.py --days 30

# Verify
python scripts/verify-data-integrity.py
```

### Initial Setup (One-Time)
```bash
# 1. Backup everything
cd tracking/backups
cp ../unified-cache.json unified-cache-BEFORE-MIGRATION-$(date +%Y%m%d_%H%M%S).json

# 2. Verify current state
python scripts/verify-data-integrity.py --baseline

# 3. Run first incremental sync
python scripts/incremental-sync.py --days 14

# 4. Verify changes
python scripts/verify-data-integrity.py
```

## What to NEVER Do

### ❌ DO NOT run `build-unified-cache.py` unless:
- This is initial setup AND garmin-cache has complete history (85+ activities)
- This is disaster recovery after consulting backups
- You understand you will lose data if source caches are incomplete

### ❌ DO NOT delete unified-cache.json
- It's the source of truth
- Contains all historical data and HR enrichments
- If deleted, must restore from backup immediately

### ❌ DO NOT run sync-garmin.py + build-unified-cache.py workflow
- This was the old broken workflow
- Causes data loss
- Use `incremental-sync.py` or `daily-sync.py` instead

## Verification Checklist

After each sync, verify:

```bash
# 1. Check activity count increased or stayed same
python -c "import json; uc = json.load(open('tracking/unified-cache.json')); print(f'Total: {len(uc[\"activities\"])} activities')"

# 2. Check Garmin activities
python -c "import json; uc = json.load(open('tracking/unified-cache.json')); garmin = [a for a in uc['activities'] if 'garmin' in a.get('source', '')]; print(f'Garmin: {len(garmin)} activities')"

# 3. Run integrity check
python scripts/verify-data-integrity.py
```

Expected results:
- Total activities: Should NEVER decrease (unless explicit delete)
- Garmin activities: Should NEVER decrease
- HR data: Should be maintained or increased

## Backup Strategy

### Automatic Backups
- `incremental-sync.py` creates backup before each save
- Located in: `tracking/backups/unified-cache-YYYYMMDD_HHMMSS.json`
- Kept indefinitely (manual cleanup as needed)

### Manual Backups
```bash
# Before major operations
cd tracking/backups
cp ../unified-cache.json unified-cache-MANUAL-$(date +%Y%m%d_%H%M%S).json
```

### Restore from Backup
```bash
# List backups
ls -lh tracking/backups/unified-cache-*.json

# Restore
cp tracking/backups/unified-cache-YYYYMMDD_HHMMSS.json tracking/unified-cache.json

# Verify
python scripts/verify-data-integrity.py
```

## Current State (Jan 13, 2026)

### Data
- **Total activities:** 543
- **Garmin activities:** 86 (Mar 23, 2025 → Jan 10, 2026)
- **Strava activities:** 457
- **HR data:** 87.5% of activities
- **Per-km HR splits:** 86 activities (15.8%)
- **Long runs with per-km HR:** 8 out of 86

### Files
- `tracking/unified-cache.json` - Source of truth (543 activities)
- `tracking/.data-integrity-baseline.json` - Verification baseline
- `tracking/backups/unified-cache-*` - Automatic backups
- `scripts/incremental-sync.py` - Primary sync script
- `scripts/verify-data-integrity.py` - Monitoring script

## Migration Complete

**Status:** ✅ COMPLETE

All scripts updated to use incremental architecture:
- ✅ `incremental-sync.py` created and tested
- ✅ `daily-sync.py` updated to use incremental-sync
- ✅ `build-unified-cache.py` marked as deprecated with warnings
- ✅ `backfill-hr-streams.py` documented (already correct)
- ✅ `verify-data-integrity.py` created for monitoring
- ✅ Baseline created (543 activities)
- ✅ Initial test successful (added 1 activity, no data loss)

## Support

If you encounter issues:

1. **Data loss detected:**
   ```bash
   # Check backups
   ls -lh tracking/backups/

   # Restore latest backup
   cp tracking/backups/unified-cache-YYYYMMDD_HHMMSS.json tracking/unified-cache.json

   # Verify restoration
   python scripts/verify-data-integrity.py
   ```

2. **Sync fails:**
   ```bash
   # Try dry-run to diagnose
   python scripts/incremental-sync.py --dry-run

   # Check Garmin authentication
   # Sessions expire after ~2 weeks, re-auth is automatic
   ```

3. **HR data missing:**
   ```bash
   # Check which activities lack HR
   python -c "import json; uc = json.load(open('tracking/unified-cache.json')); no_hr = [a for a in uc['activities'] if not a.get('avg_hr') and a.get('source') == 'garmin']; print(f'Garmin activities without HR: {len(no_hr)}')"

   # Run backfill for long runs
   python scripts/backfill-hr-streams.py
   ```

## Future Enhancements

1. **Strava integration in incremental-sync.py**
   - Currently only Garmin is supported
   - Strava will be added in future iteration

2. **Automatic cleanup of old backups**
   - Currently backups are kept indefinitely
   - Add retention policy (e.g., keep last 30 days)

3. **Email/notification on data loss**
   - Alert if verify-data-integrity detects issues
   - Integration with monitoring tools

4. **Web dashboard for verification**
   - Visual display of integrity checks
   - Historical trends
