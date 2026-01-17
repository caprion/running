# Running Training Tracker

Track your Garmin Connect running activities locally with a visual dashboard.

## Features

### Core Functionality
- 🏃 **Sync activities** from Garmin Connect (incremental merge)
- 📊 **Interactive dashboard** with 10 analysis pages
- 💓 **Heart rate data** with per-km splits and zone analysis
- 📈 **Training load** tracking and volume monitoring
- 🎯 **Season planning** with race readiness metrics
- 🔒 **Local storage** - all data stays on your machine

### Advanced Features
- 🏋️ **Create Garmin workouts** - Build structured workouts and schedule to watch
- ⚡ **Weekly summaries** - Automated training reports
- 🎪 **Consistency tracking** - Volume floor monitoring
- 🔍 **Data validation** - Integrity checks and backups
- 📝 **FIT file parsing** - Deep-dive per-second analysis

## Quick Start

### 1. Install

```bash
git clone <repo-url>
cd running
pip install -r scripts/requirements.txt
```

### 2. Setup Garmin Authentication

```bash
python scripts/import-session.py
```

Follow prompts to import Garmin Connect cookies from your browser.

### 3. Sync Activities

```bash
# First time: sync last 90 days
python scripts/incremental-sync.py --days 90

# Daily: sync last 7 days
python scripts/daily-sync.py
```

### 4. View Dashboard (Optional)

```bash
pip install streamlit pandas plotly
streamlit run dashboard/app.py
```

### Dashboard Pages

The dashboard includes 10 interactive analysis pages:

1. **📊 Consistency Guardian** - Weekly volume tracking with color-coded status (green/yellow/red), streaks, and rolling averages
2. **🎯 Season Compare** - Side-by-side comparison of training seasons with VO2max progression and quality session breakdowns
3. **🏁 Race Confidence** - Pace sustainability analysis, race calculator, and fatigue resistance metrics
4. **📋 Season Plan** - Training plan calendar with workout scheduling and volume tracking
5. **📝 Weekly Logs** - Detailed weekly training summaries with subjective notes and ratings
6. **🚨 Risk Monitor** - Injury risk indicators based on load spikes, consistency violations, and recovery metrics
7. **📈 Training Load** - ACWR (acute:chronic workload ratio), sleep quality, and heart rate zone distribution
8. **💤 Recovery** - Sleep stages analysis, resting heart rate trends, and recovery score tracking
9. **👟 Form** - Running form metrics including cadence trends, ground contact time, and stride analysis
10. **✅ Compliance** - Training plan adherence tracking with completed vs. planned workouts

## Demo Mode with Sample Data

Explore the dashboard features before setting up your own Garmin sync!

### 📊 View Interactive Dashboards

Browse 6 interactive HTML dashboards in [media/dashboard-snapshots/](media/dashboard-snapshots/):

- **[Overview](media/dashboard-snapshots/overview.html)** - 12-week volume trends
- **[Consistency Guardian](media/dashboard-snapshots/consistency.html)** - Weekly status analysis
- **[Training Load](media/dashboard-snapshots/training-load.html)** - Sleep & HR zones
- **[Form Analysis](media/dashboard-snapshots/form.html)** - Cadence trends
- **[Race Confidence](media/dashboard-snapshots/race-confidence.html)** - Pace degradation
- **[Recovery](media/dashboard-snapshots/recovery.html)** - Sleep stages

*Note: Download the HTML files and open in your browser for full interactivity*

### Run Full Dashboard Locally

```bash
# Use sample data (no Garmin sync required)
export USE_SAMPLE_DATA=true  # Linux/Mac
# or
$env:USE_SAMPLE_DATA='true'  # Windows PowerShell

streamlit run dashboard/app.py
```

The sample dataset includes 161 activities over 12 months with realistic pacing, heart rate zones, cadence, sleep, and recovery data. See [sample-data/README.md](sample-data/README.md) for details.

## Documentation

### Getting Started
- **[Quick Start Guide](QUICK-START.md)** - 5-minute setup for syncing
- **[Sample Dashboards](media/dashboard-snapshots/)** - View examples before installing

### Detailed Guides
- **[Scripts Reference](scripts/README.md)** - Complete documentation of all scripts
- **[Workflow Guide](WORKFLOW.md)** - Daily/weekly check-in processes and gait analysis
- **[Garmin Workout Creation](GARMIN-WORKOUT-AUTOMATION.md)** - Build and schedule structured workouts
- **[Garmin API Reference](docs/garmin-api-quick-reference.md)** - API endpoints and workout format
- **[Architecture](docs/ARCHITECTURE.md)** - System design and data flow
- **[Dashboard Guide](dashboard/README.md)** - Using the Streamlit dashboard

### Common Tasks
| Task | Command |
|------|---------|
| Initial sync (90 days) | `python scripts/incremental-sync.py --days 90` |
| Daily sync | `python scripts/daily-sync.py` |
| View dashboard | `streamlit run dashboard/app.py` |
| Create workout | `python scripts/create-garmin-workouts.py --week 3` |
| Weekly summary | `python scripts/weekly-summary.py` |
| Verify data | `python scripts/verify-data-integrity.py` |
| Parse FIT file | `python scripts/parse-fit.py path/to/file.fit` |

### Training Resources
- **[Arm Swing Drills](resources/arm-swing-drills-guide.md)** - Form improvement exercises
- **[Garmin Watch Settings](resources/garmin-watch-settings-guide.md)** - Optimal watch configuration
- **[Training Plan Template](resources/20_Week_Training_Plan.xlsx)** - Excel-based plan builder

## Project Structure

```
running/
├── scripts/                      # Automation scripts
│   ├── incremental-sync.py      # Primary sync (use this)
│   ├── daily-sync.py            # Convenience wrapper
│   ├── create-garmin-workouts.py # Build workouts
│   ├── weekly-summary.py        # Training reports
│   ├── verify-data-integrity.py # Data validation
│   ├── consistency-guardian.py  # Volume tracking
│   ├── parse-fit.py             # FIT file parser
│   ├── import-session.py        # Auth setup
│   ├── generate-sample-data.py  # Demo data generator
│   └── export-dashboards-html.py # HTML dashboard exporter
│
├── dashboard/                   # Streamlit visualization
│   ├── app.py                   # Main dashboard
│   └── pages/                   # 10 analysis pages
│
├── tracking/                    # Local data cache (gitignored)
│   ├── unified-cache.json       # Single source of truth
│   ├── garmin-cache.json        # Garmin API data
│   ├── backups/                 # Auto backups
│   └── fit_files/               # Raw FIT files
│
├── sample-data/                 # Demo dataset
│   ├── unified-cache.json       # Sample activities
│   └── seasons/                 # Sample training plans
│
├── seasons/                     # Your training plans (gitignored)
│   └── [season-name]/
│       ├── plan.md              # Training plan
│       └── weekly-logs/         # Weekly reflections
│
├── media/                       # Media files (gitignored)
│   └── dashboard-snapshots/     # HTML dashboards (public)
│
└── docs/                        # Documentation
    ├── garmin-workout-creation-guide.md
    ├── garmin-api-quick-reference.md
    └── ARCHITECTURE.md
```

## Requirements

- Python 3.8+
- Garmin Connect account
- Chrome/Firefox (for cookie import)

## How It Works

1. **Authentication**: Import Garmin Connect session cookies (valid ~2 weeks)
2. **Sync**: Fetch activities from Garmin Connect API
3. **Storage**: Save to `tracking/unified-cache.json` (single source of truth)
4. **Dashboard**: Visualize data with Streamlit (optional)

## Data Flow

```
Garmin Connect API
    ↓
incremental-sync.py (merge new activities)
    ↓
tracking/unified-cache.json (single source of truth)
    ↓
Dashboard (visualization)
```

## Advanced Usage

### Create Structured Workouts

Build and schedule workouts to your Garmin watch:

```bash
# Preview workouts for week 3
python scripts/create-garmin-workouts.py --week 3 --dry-run

# Create and schedule to Garmin Connect
python scripts/create-garmin-workouts.py --week 3
```

See [docs/garmin-workout-creation-guide.md](docs/garmin-workout-creation-guide.md) for customization.

### Generate Training Reports

```bash
# Weekly summary (auto-detects current week)
python scripts/weekly-summary.py

# Analyze consistency patterns
python scripts/consistency-guardian.py

# Validate data integrity
python scripts/verify-data-integrity.py
```

### Parse FIT Files

Deep-dive into per-second metrics:

```bash
# Text summary
python scripts/parse-fit.py tracking/fit_files/12345.fit

# JSON output
python scripts/parse-fit.py path/to/file.fit --json

# Markdown format
python scripts/parse-fit.py path/to/file.fit --markdown
```

### Schedule Automatic Syncs

**Linux/Mac (cron):**
```bash
# Add to crontab (runs daily at 8 PM)
0 20 * * * cd /path/to/running && python scripts/daily-sync.py
```

**Windows (Task Scheduler):**
```powershell
# Create scheduled task
$action = New-ScheduledTaskAction -Execute 'python' -Argument 'scripts/daily-sync.py' -WorkingDirectory 'C:\path\to\running'
$trigger = New-ScheduledTaskTrigger -Daily -At 8PM
Register-ScheduledTask -TaskName "GarminSync" -Action $action -Trigger $trigger
```

## Roadmap

- [x] Garmin activity sync with incremental merge
- [x] Interactive dashboard with 10 pages
- [x] Garmin workout creation and scheduling
- [x] Sample data for demonstrations
- [x] Data validation and integrity checks
- [ ] Strava integration (phased out, see `scripts/archived/strava/`)
- [ ] Simplified setup wizard
- [ ] Mobile-friendly dashboard
- [ ] Export to Excel/CSV

## License

MIT License - Free to use and modify for your own training tracking.
