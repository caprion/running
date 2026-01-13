# Strava Integration Setup Guide

## What's Been Built

✅ **sync-strava.py** - Fetches historical activities from Strava
✅ **sync-all.py** - Runs both Garmin + Strava syncs together
✅ **data_loader.py** - Automatically merges and deduplicates data
✅ **Dashboard integration** - Existing dashboards now show both sources

## Quick Setup (5 minutes)

### Step 1: Add Strava Credentials to `.env`

Edit `c:\Learn\running\.env` and replace the placeholders:

```bash
STRAVA_CLIENT_ID=116815
STRAVA_CLIENT_SECRET=<paste_your_client_secret>
STRAVA_REFRESH_TOKEN=<paste_your_refresh_token>
```

Get these from: https://www.strava.com/settings/api

### Step 2: Test Strava Sync

```bash
cd c:\Learn\running
python scripts/sync-strava.py
```

This will:
- Refresh your access token automatically (it expires every 6 hours)
- Fetch all running activities from last 2 years (default)
- Save to `tracking/strava-cache.json`
- Show progress and activity count

### Step 3: Backfill Historical Data

To fetch ALL activities from a specific start date:

```bash
# Fetch everything from Jan 1, 2023
python scripts/sync-strava.py --start-date 2023-01-01

# Or fetch last 1000 days
python scripts/sync-strava.py --days 1000
```

### Step 4: Run Combined Sync

For daily syncing, use the combined script:

```bash
# Sync last 7 days from Garmin + 2 years from Strava
python scripts/sync-all.py

# Sync last 30 days from Garmin + all Strava
python scripts/sync-all.py 30 --strava-days 1000

# Garmin only (with FIT files)
python scripts/sync-all.py 7 --fit --garmin-only

# Strava only (full backfill)
python scripts/sync-all.py --strava-only --strava-start 2020-01-01
```

## How Data Merging Works

### Deduplication Strategy

The system automatically detects and removes duplicates:

1. **Matching Logic**: Activities match if:
   - Date/time within 2 hours
   - Distance within 0.1km (100m)

2. **Data Priority**: When duplicates found:
   - ✅ **Prefer Garmin** (better HR zones, training metrics, sleep, HRV)
   - ✅ **Copy Strava-specific fields** (Suffer Score)
   - ✅ **Mark source as "both"**

3. **Source Tracking**: Each activity tagged with:
   - `"source": "garmin"` - Only in Garmin
   - `"source": "strava"` - Only in Strava
   - `"source": "both"` - Found in both (Garmin data used)

### What Data is Synced

| Data Type | Garmin | Strava | Notes |
|-----------|--------|--------|-------|
| **Activities** | ✅ | ✅ | Both sources |
| Distance, Duration, Pace | ✅ | ✅ | Both |
| Heart Rate | ✅ | ⚠️ | Strava: Only if HR strap used |
| Cadence | ✅ | ⚠️ | Strava: Often missing |
| Elevation | ✅ | ✅ | Both |
| Splits/Laps | ✅ | ⚠️ | Strava: Requires streams API (rate limited) |
| HR Zones | ✅ | ❌ | Garmin exclusive |
| **Training Status** | ✅ | ❌ | Garmin exclusive |
| VO2max | ✅ | ❌ | Garmin exclusive |
| Training Load | ✅ | ❌ | Garmin exclusive |
| **Sleep** | ✅ | ❌ | Garmin exclusive |
| **HRV** | ✅ | ❌ | Garmin exclusive |
| **Stress** | ✅ | ❌ | Garmin exclusive |
| Suffer Score | ❌ | ✅ | Strava exclusive |

### Example Merge Scenario

**Before Merge:**
- Garmin: 50 activities (Jan 2026 only)
- Strava: 300 activities (2023-2026, including Jan 2026)

**After Merge:**
- Total: 295 unique activities
- 50 marked as "both" (Jan 2026 overlap, using Garmin data)
- 250 marked as "strava" (historical data missing from Garmin)

## Dashboard Changes

### Last Sync Time
Now shows both sources:
```
Last Sync: Garmin: 2026-01-09 13:35 | Strava: 2026-01-09 14:00
```

### Activity Cards
Each activity shows its source icon:
- 🟢 Garmin only
- 🔵 Strava only
- 🟣 Both (merged)

### Consistency Guardian
Includes all activities from both sources in weekly volume calculations.

## Automation

### Daily Sync (Recommended)

Add to cron/Task Scheduler:

```bash
# Daily at 6am: Sync last 7 days from both sources
0 6 * * * cd /path/to/running && python scripts/sync-all.py 7
```

### One-Time Historical Backfill

```bash
# Fetch ALL Strava data from when you started running
python scripts/sync-strava.py --start-date 2020-01-01
```

This will:
- Fetch ~300-500 activities (if 3+ years of data)
- Take 5-10 minutes (rate limited: 1 second between pages)
- Use ~30-50 API requests (well under 1000/day limit)

## Rate Limits

### Strava API Limits
- **Read calls**: 100 requests per 15 minutes, 1,000 per day
- **Overall**: 200 requests per 15 minutes, 2,000 per day

### Smart Sync Strategy
- **Daily sync**: Uses ~5-10 requests (activities + athlete profile)
- **Full backfill**: Uses ~30-100 requests depending on history
- **Splits fetch**: 1 extra request per activity (disabled by default)

## Troubleshooting

### Token Expired Error
```
❌ Token refresh failed: 401
```

**Fix**: Get a new refresh token from https://www.strava.com/settings/api

### Rate Limit Error
```
⚠️ Rate limit exceeded, waiting 15 minutes...
```

**Fix**: Script auto-waits. Or run `--strava-days 30` for smaller sync.

### No Strava Data
```
❌ Error: STRAVA_CLIENT_ID, STRAVA_CLIENT_SECRET, and STRAVA_REFRESH_TOKEN must be set
```

**Fix**: Add credentials to `.env` file (see Step 1).

### Duplicate Activities
```
Warning: Found 50 duplicate activities
```

**Fix**: This is normal! The system removes duplicates automatically. Check `source` field to see which data was kept.

## Files Created/Modified

### New Files
- `scripts/sync-strava.py` - Strava sync script
- `scripts/sync-all.py` - Combined sync script
- `scripts/.strava_tokens.json` - Saved access tokens (auto-generated)
- `tracking/strava-cache.json` - Strava data cache (auto-generated)

### Modified Files
- `dashboard/utils/data_loader.py` - Added merge logic
- `.env.example` - Added Strava config template
- `.env` - Added your Strava credentials

### Unchanged
- All dashboard pages work without changes
- Garmin sync still works independently
- All existing scripts compatible

## Next Steps

1. **Test basic sync**: `python scripts/sync-strava.py --days 30`
2. **Backfill history**: `python scripts/sync-strava.py --start-date 2023-01-01`
3. **Check dashboard**: `streamlit run dashboard/app.py`
4. **Verify merge**: Check that activities show correct `source` field
5. **Set up automation**: Add `sync-all.py` to daily cron/scheduler

## Support

If you see activities missing in Garmin that exist in Strava, the merge is working correctly! Those Strava-only activities will now appear in your dashboards.

To verify:
```python
# Check sources in Python console
import json
with open('tracking/garmin-cache.json') as f:
    garmin = len(json.load(f)['activities'])
with open('tracking/strava-cache.json') as f:
    strava = len(json.load(f)['activities'])
print(f"Garmin: {garmin}, Strava: {strava}")
```

Then check dashboard for total count (should be close to `strava` if Garmin has gaps).
