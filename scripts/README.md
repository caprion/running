# Scripts Documentation

## Garmin Workout Creation

### `create-garmin-workouts.py` - Create Structured Workouts

Creates and schedules workouts in Garmin Connect.

**Usage:**
```bash
# Preview workouts (dry run)
python scripts/create-garmin-workouts.py --week 3 --dry-run

# Create and schedule workouts
python scripts/create-garmin-workouts.py --week 3
```

**What it does:**
1. Authenticates with Garmin Connect
2. Creates structured workouts with pace targets, HR zones
3. Schedules workouts to correct dates
4. Supports warmup/cooldown with lap button
5. Easy runs with no targets

**Adding new weeks:**
Edit `get_week_workouts()` function in the script. Copy Week 3 structure.

See [GARMIN-WORKOUT-AUTOMATION.md](../GARMIN-WORKOUT-AUTOMATION.md) for details.

---

## Data Sync Scripts

### `incremental-sync.py` - Primary Sync Script

Fetches recent activities from Garmin Connect and merges into local cache.

**Usage:**
```bash
python scripts/incremental-sync.py              # Last 7 days
python scripts/incremental-sync.py --days 30    # Last 30 days
python scripts/incremental-sync.py --dry-run    # Test without saving
```

**What it does:**
1. Loads existing `unified-cache.json` (or creates if first run)
2. Authenticates with Garmin Connect (uses saved session)
3. Fetches activities from last N days
4. Merges new activities (deduplicates by ID + date/distance)
5. Preserves HR data and per-km splits
6. Creates automatic backup before saving
7. Safety checks (alerts if data lost)

**First run:**
```bash
python scripts/incremental-sync.py --days 90
```

---

### `daily-sync.py` - Wrapper for Regular Runs

Convenience wrapper that calls `incremental-sync.py` with defaults.

**Usage:**
```bash
python scripts/daily-sync.py              # Last 7 days
python scripts/daily-sync.py --days 30    # Last 30 days
```

**Recommended:** Schedule this to run daily (cron/Task Scheduler).

---

### `sync-garmin.py` - Low-Level Garmin Sync

Direct Garmin Connect API access. Used internally by `incremental-sync.py`.

**Usage:**
```bash
python scripts/sync-garmin.py 7     # Fetch last 7 days
```

**Output:** `tracking/garmin-cache.json` (intermediate cache)

**Note:** Use `incremental-sync.py` instead for normal workflow.

---

## Setup Scripts

### `import-session.py` - Garmin Authentication Setup

One-time setup to import Garmin Connect cookies from your browser.

**Usage:**
```bash
python scripts/import-session.py
```

**What it does:**
1. Prompts for browser cookie file (exported from Garmin Connect)
2. Saves session to `scripts/.garth/` directory
3. Session valid for ~2 weeks, then re-run

**Cookie export:**
- Chrome: "Get cookies.txt LOCALLY" extension
- Firefox: "cookies.txt" extension
- Export from `connect.garmin.com`

---

## Optional Scripts

### `parse-fit.py` - FIT File Parser

Parses Garmin FIT files for detailed per-second data.

**Usage:**
```bash
python scripts/parse-fit.py tracking/fit_files/12345.fit
python scripts/parse-fit.py path/to/file.fit --json
python scripts/parse-fit.py path/to/file.fit --markdown
```

**Output formats:**
- Default: Text summary
- `--json`: JSON output (for scripting)
- `--markdown`: Markdown format (for logs)

**Use case:** Deep-dive analysis of specific runs (cadence, elevation, power).

---

### `backfill-hr-streams.py` - HR Data Enrichment

Fetches per-km heart rate data for long runs lacking detailed splits.

**Usage:**
```bash
python scripts/backfill-hr-streams.py
```

**When to run:**
- After initial sync, if long runs (≥15km) show only 1 lap
- Automatically detects activities needing enrichment
- Safe to run multiple times (idempotent)

---

### `verify-data-integrity.py` - Data Validation

Monitors unified-cache for data loss or corruption.

**Usage:**
```bash
python scripts/verify-data-integrity.py              # Check current state
python scripts/verify-data-integrity.py --baseline   # Save baseline
```

**Run after each sync to verify:**
- Activity count didn't decrease
- HR data maintained
- Garmin activities preserved

---

### `weekly-summary.py` - Generate Reports

Creates markdown summary of weekly training volume.

**Usage:**
```bash
python scripts/weekly-summary.py
```

**Output:** `tracking/weekly-summary-YYYY-WW.md`

---

### `consistency-guardian.py` - Volume Tracking

Analyzes historical training consistency and floor violations.

**Usage:**
```bash
python scripts/consistency-guardian.py
```

Used by dashboard "Risk Monitor" page.

---

## Archived Scripts

See `scripts/archived/` for deprecated scripts:
- `build-unified-cache.py` - OLD: Rebuilds from scratch (data loss risk)
- `sync-wrapper.py` - OLD: Minimal shell wrapper
- Others

See `scripts/archived/strava/` for Strava integration (phased out Jan 2026):
- `sync-strava.py` - Full Strava API sync
- `sync-strava-recent.py` - Incremental Strava sync
- `strava-authorize.py` - OAuth token setup
- Others

**Do not use archived scripts** - they're kept for reference only.

---

## File Structure

```
scripts/
├── incremental-sync.py         # Primary sync (use this)
├── daily-sync.py               # Wrapper
├── sync-garmin.py              # Low-level Garmin API
├── import-session.py           # Setup auth
├── parse-fit.py                # FIT parser
├── verify-data-integrity.py    # Data checks
├── weekly-summary.py           # Reports
├── backfill-hr-streams.py      # HR enrichment
├── consistency-guardian.py     # Volume analysis
├── requirements.txt            # Dependencies
├── .garth/                     # Session tokens (auto-generated)
└── archived/                   # Deprecated scripts
```

---

## Data Flow

```
Garmin Connect API
    ↓
sync-garmin.py (fetch)
    ↓
incremental-sync.py (merge)
    ↓
tracking/unified-cache.json (single source of truth)
    ↓
Dashboard (visualization)
```

---

## What Data Gets Synced

### Activities (Runs/Workouts)
- Basic: name, type, date, distance, duration
- Performance: pace, elevation gain, calories
- Heart rate: avg HR, max HR, per-km splits
- Cadence: avg running cadence
- Splits: lap-by-lap breakdown with per-km HR

### Activity Details
For each running activity:
- `id` - Garmin activity ID
- `name` - Activity name
- `date` - Start time (local)
- `distance_km` - Distance in kilometers
- `duration_seconds` - Total duration
- `avg_pace_min_km` - Average pace
- `elevation_gain_m` - Total elevation gain
- `avg_hr` - Average heart rate
- `max_hr` - Maximum heart rate
- `calories` - Estimated calories burned
- `avg_cadence` - Average cadence (steps per minute)
- `splits` - Per-km lap data with HR

---

## Authentication Setup

### Option 1: Browser Cookie Import (Recommended)

1. **Export cookies from browser:**
   - Chrome: Install "Get cookies.txt LOCALLY" extension
   - Firefox: Install "cookies.txt" extension
   - Export cookies from `connect.garmin.com`
   - Save as `cookies.txt`

2. **Import cookies:**
   ```bash
   python scripts/import-session.py
   ```
   Follow the prompts to import your cookie file.

3. **Session persistence:**
   - Saved to `scripts/.garth/` directory
   - Valid for ~2 weeks
   - Re-run import when session expires

### Option 2: Email/Password (Alternative)

1. **Create `.env` file:**
   ```bash
   cp .env.example .env
   ```

2. **Add credentials:**
   ```
   GARMIN_EMAIL=your.email@example.com
   GARMIN_PASSWORD=your_password_here
   ```

3. **First run authenticates automatically:**
   ```bash
   python scripts/incremental-sync.py --days 90
   ```

**Security notes:**
- `.env` and session files are in `.gitignore`
- Cookie method more secure (no password storage)
- Session tokens stored locally, never shared
- Sessions last ~2 weeks before needing refresh

---

## Troubleshooting

### "Authentication failed"

```bash
python scripts/import-session.py
```

Re-import cookies from browser. Sessions expire after ~2 weeks.

### "No activities found"

Increase days: `python scripts/incremental-sync.py --days 180`

Check:
- Garmin Connect has running activities in the date range
- Activity type filter (only "running" activities synced)

### "Module not found"

```bash
pip install -r scripts/requirements.txt
```

Make sure you're in the project root directory.

### "Activity count decreased"

Check data integrity:
```bash
python scripts/verify-data-integrity.py
```

Restore from backup:
```bash
cp tracking/backups/unified-cache-YYYYMMDD_HHMMSS.json tracking/unified-cache.json
```

### Connection Errors

- Check internet connection
- Garmin Connect servers may be down (rare)
- Try again in a few minutes

### Rate Limiting

If you get blocked:
- Wait 15-30 minutes before retrying
- Don't run the script too frequently (once per day is fine)
- The script uses official web API endpoints

---

## Automation

### Windows Task Scheduler

Set up automatic daily syncs:

1. Open Task Scheduler
2. Create Basic Task
3. Trigger: Daily (8pm)
4. Action: Start a program
   - Program: `python`
   - Arguments: `C:\Learn\running\scripts\daily-sync.py`
   - Start in: `C:\Learn\running`

### Linux/Mac (cron)

Add to crontab:
```bash
0 20 * * * cd /path/to/running && python scripts/daily-sync.py
```

---

## Data Privacy

- All data stays local on your machine
- No data sent anywhere except from Garmin to your local cache
- `.env` credentials never committed to git
- Session tokens stored in `.garth/` (also gitignored)
- Backups created automatically before each sync

---

## Advanced Usage

### Dry Run (Test Mode)

```bash
python scripts/incremental-sync.py --days 30 --dry-run
```

Tests sync without saving changes.

### Check Data Integrity

```bash
# Check current state
python scripts/verify-data-integrity.py

# Save baseline
python scripts/verify-data-integrity.py --baseline
```

### Parse FIT Files

```bash
# Text output
python scripts/parse-fit.py path/to/file.fit

# JSON output
python scripts/parse-fit.py path/to/file.fit --json

# Markdown output
python scripts/parse-fit.py path/to/file.fit --markdown
```

### Weekly Summary

```bash
python scripts/weekly-summary.py
```

Generates `tracking/weekly-summary-YYYY-WW.md`.

---

## Next Steps

Once you're syncing successfully:

1. **Explore dashboard**: `streamlit run dashboard/app.py`
2. **Schedule daily sync**: Setup cron/Task Scheduler
3. **Review data**: Check `tracking/unified-cache.json`
4. **Analyze trends**: Use dashboard pages for insights

For detailed workflow, see [WORKFLOW.md](../WORKFLOW.md).
