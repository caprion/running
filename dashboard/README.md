# Running Analytics Dashboard

Interactive web-based dashboard for analyzing your running training data from Garmin Connect.

## Quick Start

1. **Sync your Garmin data** (if you haven't already):
   ```bash
   python scripts/incremental-sync.py --days 90
   ```

2. **Launch the dashboard**:
   ```bash
   streamlit run dashboard/app.py
   ```

3. **Open in browser**: The dashboard opens at `http://localhost:8501` (use `--server.port 8502` if 8501 is in use)

## Try Without Syncing (Demo Mode)

Use sample data—no Garmin account needed:

```bash
# Linux/Mac
export USE_SAMPLE_DATA=true

# Windows PowerShell
$env:USE_SAMPLE_DATA='true'

streamlit run dashboard/app.py
```

## Pages

### 📊 Consistency Guardian
- Weekly volume bar chart (color-coded: Green/Yellow/Red)
- Current streak tracker
- 4-week rolling average
- Status breakdown (pie chart)
- Period comparisons
- Detailed weekly table

### 🎯 Season Compare
- Side-by-side season analysis
- VO2max progression
- Quality sessions breakdown
- Long run trends

### 🏁 Race Confidence
- "Can I hold this pace?" calculator
- Race pace database
- Fatigue resistance analysis
- HR stability tracking

### 📋 Season Plan
- 20-week HM sub-2:00 campaign details
- Weekly volume progression
- Strength training program

### 📝 Weekly Logs
- Week-by-week detailed documentation
- Workout analysis and reflections

### 🚨 Risk Monitor
- Monthly risk assessment (4 years of data)
- School holiday collapse warnings
- April-May firewall strategies
- Real-time risk alerts

### 📈 Training Load
- ACWR (acute:chronic workload ratio)
- Sleep quality and duration
- Heart rate zone distribution
- Resting HR trends

### 💤 Recovery
- Sleep stages analysis
- Resting heart rate trends
- Recovery score tracking

### 👟 Form
- Cadence trends
- Ground contact time
- Stride length analysis

### ✅ Compliance
- Training plan adherence
- Completed vs planned workouts

## Features

- **Interactive charts**: Hover for details, zoom, pan
- **Real-time updates**: Re-run sync script, then refresh browser (F5)
- **Responsive**: Works on desktop and tablet
- **Fast**: Cached data loading for quick navigation

## Dashboard Structure

```
dashboard/
  app.py                    # Main landing page
  pages/
    1_📊_Consistency.py      # Consistency Guardian
    2_🎯_Season_Compare.py   # Season comparison
    3_🏁_Race_Confidence.py  # Race confidence
    4_📋_Season_Plan.py      # Training plan
    5_📝_Weekly_Logs.py     # Weekly logs
    6_🚨_Risk_Monitor.py    # Risk monitor
    7_📈_Training_Load.py    # Training load
    8_💤_Recovery.py        # Recovery
    9_👟_Form.py            # Form analysis
    10_✅_Compliance.py     # Compliance
  utils/
    data_loader.py          # Data loading functions
    metrics.py              # Calculation utilities
```

## Tips

- **Refresh data**: Run sync script, then refresh browser (F5)
- **Change years**: Use the sidebar filter on each page
- **Export charts**: Hover over charts → camera icon to download PNG
- **Keyboard shortcuts**: `R` — Rerun app, `C` — Clear cache

## Troubleshooting

**Error: "NotImplementedError: (dtype('<M8[ns]'), array..."**
Cache corruption. Fix:
```bash
# Delete Streamlit cache
rm -rf .streamlit   # Linux/Mac
# Or double-click CLEAR-CACHE.bat on Windows
```

**Dashboard won't start:**
```bash
pip install streamlit plotly pandas
```

**No data showing:**
```bash
python scripts/incremental-sync.py --days 7
```

**Port already in use:**
```bash
streamlit run dashboard/app.py --server.port 8502
```

**PyArrow warning:** Safe to ignore on ARM64 Windows—dashboard works without it.

## Requirements

- streamlit>=1.29.0
- plotly>=5.18.0
- pandas>=2.1.0
- python>=3.8
