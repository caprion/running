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

Want to explore the dashboard without syncing your own Garmin data?

### 📊 **[View Interactive Dashboards](media/dashboard-snapshots/index.html)** ← Start Here!

Browse 6 interactive HTML dashboards showing 12 months of synthetic training data for a sub-2hr half marathon campaign. No installation required - works directly on GitHub!

### Run Locally with Sample Data

```powershell
# Windows PowerShell
$env:USE_SAMPLE_DATA='true'
streamlit run dashboard/app.py

# Return to personal data
Remove-Item Env:\USE_SAMPLE_DATA
streamlit run dashboard/app.py
```

The sample data contains 161 activities over 12 months with realistic pacing, heart rate zones, cadence metrics, sleep, and recovery data. See [sample-data/README.md](sample-data/README.md) for details.

**⚠️ Privacy Note:** Your personal data in `tracking/`, `seasons/`, and `media/` is protected by `.gitignore` and will never be committed to version control. Sample data is for GitHub demonstrations only.

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

Personal project - MIT License

## Personal Training Dashboard

For the author's personal training tracking, see [TRAINING-DASHBOARD.md](TRAINING-DASHBOARD.md).
