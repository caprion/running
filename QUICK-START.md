# 5-Minute Quick Start

Get up and running with Garmin sync in 5 minutes.

## Step 1: Install Dependencies (2 min)

```bash
pip install -r scripts/requirements.txt
```

**What this installs:**
- `garminconnect` - Garmin Connect API
- `garth` - Session management
- `python-dotenv` - Environment variables
- `fitparse` - FIT file parsing (optional)
- `requests` - HTTP client
- `python-dateutil` - Date utilities

## Step 2: Import Garmin Cookies (2 min)

```bash
python scripts/import-session.py
```

**What this does:**
1. Opens browser instructions
2. Asks you to export Garmin Connect cookies
3. Saves session to `scripts/.garth/` directory

**Cookie export:**
- Chrome: Use "Get cookies.txt LOCALLY" extension
- Firefox: Use "cookies.txt" extension
- Export from `connect.garmin.com`

## Step 3: First Sync (1 min)

```bash
python scripts/incremental-sync.py --days 90
```

**What this does:**
1. Fetches last 90 days of running activities from Garmin Connect
2. Saves to `tracking/unified-cache.json`
3. Creates automatic backup in `tracking/backups/`

**Expected output:**
```
[LOAD] Loaded unified-cache: 0 activities
[FETCH] Fetching last 90 days from Garmin...
[FETCH] Retrieved 45 running activities
[MERGE] Merging 45 Garmin activities...
[ADD] New activity 2026-01-10 (9.32km)
...
[SAVE] Updated unified-cache: 45 activities
```

## Step 4: Daily Sync (ongoing)

```bash
python scripts/daily-sync.py
```

Run this daily to sync latest activities (last 7 days by default).

## Optional: View Dashboard

```bash
pip install streamlit pandas plotly
streamlit run dashboard/app.py
```

Open browser to `http://localhost:8501` to view:
- Activity list with filters
- Monthly volume analysis
- Pace progression charts
- Heart rate zones
- Training load tracking
- Risk monitoring
- And 4 more analysis pages

## Troubleshooting

### "Authentication failed"

```bash
python scripts/import-session.py
```

Re-import cookies from browser. Garmin sessions expire after ~2 weeks.

### "No activities found"

Check:
- Garmin Connect has running activities in the date range
- Try increasing days: `--days 180`
- Check activity type filter (only "running" activities synced)

### "Module not found"

```bash
pip install -r scripts/requirements.txt
```

Make sure you're in the project root directory.

### "File not found: unified-cache.json"

This is normal on first run. The script will create it automatically.

## Data Safety

- **Automatic backups**: Every sync creates a timestamped backup in `tracking/backups/`
- **Incremental merge**: Never rebuilds from scratch - always preserves existing data
- **Safety checks**: Alerts if activity count decreases unexpectedly
- **Restore command**: `cp tracking/backups/unified-cache-YYYYMMDD_HHMMSS.json tracking/unified-cache.json`

## Next Steps

- **Schedule daily sync**: Setup cron job (Linux/Mac) or Task Scheduler (Windows)
- **Explore dashboard**: Check out all 10 analysis pages
- **Read detailed docs**: See [WORKFLOW.md](WORKFLOW.md) for advanced usage
- **Customize**: Edit training plans in `seasons/` directory

## Demo Mode (Try Without Syncing)

Want to explore the dashboard before syncing your data? Use the included sample dataset:

```bash
# Linux/Mac
export USE_SAMPLE_DATA=true
streamlit run dashboard/app.py

# Windows PowerShell
$env:USE_SAMPLE_DATA='true'
streamlit run dashboard/app.py
```

The sample data simulates a sub-2hr half marathon training campaign with:
- 161 activities over 12 months
- Varied workout types (easy, tempo, long runs, intervals)
- Heart rate zones and cadence metrics
- Sleep and recovery data

See [sample-data/README.md](sample-data/README.md) and pre-generated [HTML dashboards](media/dashboard-snapshots/) for a preview.

## Advanced Options

### Dry run (test without saving)

```bash
python scripts/incremental-sync.py --days 30 --dry-run
```

### Sync specific date range

```bash
# Last 30 days
python scripts/incremental-sync.py --days 30

# Last 180 days (6 months)
python scripts/incremental-sync.py --days 180
```

### Check data integrity

```bash
python scripts/verify-data-integrity.py
```

Shows activity count, sources breakdown, and data health.

## File Locations

- **Activity data**: `tracking/unified-cache.json` (single source of truth)
- **Backups**: `tracking/backups/unified-cache-*.json`
- **Session tokens**: `scripts/.garth/` (auto-generated, expires ~2 weeks)
- **FIT files**: `tracking/fit_files/` (optional, for detailed analysis)

## What Gets Synced

For each running activity:
- Basic metrics: distance, duration, pace, calories
- Heart rate: average, max, per-km splits (if available)
- Cadence: average running cadence
- Elevation: total elevation gain
- Detailed splits: lap data with per-km breakdowns
- Activity metadata: name, date, activity ID

## Privacy & Security

- **All data stored locally** - No cloud uploads
- **Session cookies** - Stored in `scripts/.garth/`, same as using Garmin website
- **No password storage** - Only session tokens (expire after ~2 weeks)
- **Open source** - Review all code in `scripts/` directory

---

**Ready to sync?** Run `python scripts/incremental-sync.py --days 90` to get started!
