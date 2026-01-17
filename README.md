# Running Training Tracker

Track your Garmin Connect running activities locally with a visual dashboard.

## Features

- 🏃 Sync activities from Garmin Connect
- 📊 Streamlit dashboard with 10 analysis pages
- 💓 Heart rate data & per-km splits
- 📈 Training load & volume tracking
- 🎯 Season planning & race readiness
- 🔒 All data stored locally (no cloud)

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

- **[Quick Start Guide](QUICK-START.md)** - 5-minute setup
- **[Complete Workflow](docs/WORKFLOW.md)** - Detailed usage (coming soon)
- **[Scripts Documentation](scripts/README.md)** - Script reference (coming soon)

## Project Structure

```
running/
├── scripts/               # Sync scripts
├── dashboard/             # Streamlit visualization (optional)
├── tracking/              # Local data cache (auto-generated)
├── seasons/               # Training plans & logs
└── analysis/              # Historical analysis
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

## Roadmap

- [ ] Simplified setup wizard
- [ ] Auto-scheduled sync (cron/Task Scheduler)
- [ ] Mobile-friendly dashboard
- [ ] Export to Excel/CSV

## License

MIT License - Free to use and modify for your own training tracking.
