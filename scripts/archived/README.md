# Archived Scripts

These scripts are deprecated and kept for reference only. **Do not use them.**

## Why Archived

| Script | Reason | Date Archived |
|--------|--------|---------------|
| `build-unified-cache.py` | **DATA LOSS RISK**: Rebuilds unified-cache from scratch. Replaced by `incremental-sync.py` which merges safely. | Jan 2026 |
| `sync-wrapper.py` | Minimal shell wrapper, no longer needed | Jan 2026 |
| `test-merge-logic.py` | One-time development test script | Jan 2026 |

## For New Users

Use these scripts instead:
- `python scripts/incremental-sync.py` - Safe incremental sync
- `python scripts/daily-sync.py` - Daily wrapper

See `scripts/README.md` for full documentation.

## Historical Context

These scripts were part of the original data migration when transitioning from Strava to Garmin-only tracking. The architecture was refactored in January 2026 to prevent data loss incidents.

For details, see: `docs/archived/SYNC-FIX-SUMMARY.md`
