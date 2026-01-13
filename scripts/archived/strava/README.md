# Strava Integration (Archived)

**Strava integration was phased out in January 2026.** These scripts are kept for historical reference only.

## Archived Scripts

| Script | Purpose | LOC |
|--------|---------|-----|
| `sync-strava.py` | Full Strava API sync | 518 |
| `sync-strava-recent.py` | Incremental Strava sync | 332 |
| `strava-authorize.py` | OAuth token setup | 128 |
| `create-strava-archive.py` | One-time historical export | 126 |
| `sync-all.py` | Old wrapper (Garmin + Strava) | 122 |

## Why Phase Out Strava?

1. **Complexity**: OAuth tokens, rate limits, API management
2. **Redundancy**: Garmin Connect is the primary data source
3. **New user friction**: Strava setup was confusing for users who only use Garmin
4. **Maintenance burden**: Two sync paths to maintain

## For Historical Data

If you have historical Strava data:
- It's preserved in `tracking/strava-historical-archive.json`
- Already merged into `tracking/unified-cache.json`
- No action needed

## Migration Complete

As of January 2026:
- ✅ Historical Strava data archived (457 activities)
- ✅ Garmin-only sync workflow established
- ✅ Incremental sync prevents data loss
- ✅ Dashboard works with unified-cache only

## Documentation

For setup instructions see `docs/archived/STRAVA-SETUP.md` (historical reference only).
