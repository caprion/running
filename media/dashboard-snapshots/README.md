# Dashboard Snapshots

This directory contains **interactive HTML dashboards** generated from sample data.

## 🌐 View Dashboards

**To view these dashboards:**
1. Clone this repository
2. Open any `.html` file in your browser
3. Or run `index.html` for a navigation menu

### Available Dashboards

1. **overview.html** - 12-week volume trends and key metrics
2. **consistency.html** - Weekly status bars and distribution
3. **training-load.html** - Sleep analysis and HR zones
4. **form.html** - Cadence distribution and trends  
5. **race-confidence.html** - Pace degradation on long runs
6. **recovery.html** - Sleep stages breakdown

All charts are **fully interactive** with Plotly:
- Hover for detailed data
- Zoom and pan
- Download as PNG
- No server or installation needed

## 📊 Sample Data Profile

The dashboards demonstrate a synthetic runner profile:
- **Goal:** Sub-2hr half marathon (1:55-2:00)
- **Data Range:** January 2025 - January 2026 (12 months)
- **Total Activities:** 161 running sessions
- **Total Distance:** 1,888 km
- **Avg Weekly Volume:** 36 km
- **VO2max:** 44.6
- **Resting HR:** 59 bpm

All data is anonymized and generated for demonstration purposes. No personal information or GPS data is included.

## 🔄 Regenerate Dashboards

To regenerate with updated sample data:

```powershell
.\.venv\Scripts\python.exe scripts/export-dashboards-html.py
```

This will recreate all HTML files in this directory using the current sample data.

## 📸 Static Screenshots (Optional)

If you prefer static images instead of interactive HTML:

### 1. Launch Dashboard with Sample Data

```powershell
# Set environment variable to use sample data
$env:USE_SAMPLE_DATA='true'

# Run dashboard (install streamlit first if needed)
pip install streamlit plotly pandas
streamlit run dashboard/app.py
```

### 2. Navigate Through Pages

Visit each page in the sidebar and capture screenshots:

1. **📊 Consistency** - Weekly status bars, pie chart, rolling average
2. **🎯 Season Compare** - Multi-season comparison charts
3. **🏁 Race Confidence** - Confidence gauge, pace degradation, HR drift
4. **📋 Season Plan** - Training plan markdown (configure path to sample-data/seasons)
5. **📝 Weekly Logs** - Weekly log markdown (configure path to sample-data/seasons)
6. **🚨 Risk Monitor** - Risk calendar, violation patterns
7. **📈 Training Load** - Sleep charts, HR zones, training load
8. **💤 Recovery** - Sleep stages, stress levels
9. **👟 Form** - Cadence trends, stride length analysis
10. **✅ Compliance** - 20-week plan tracking

### 3. Screenshot Naming Convention

Save screenshots as:
- `01-consistency-weekly-status.png`
- `01-consistency-status-pie.png`
- `02-season-compare-volume.png`
- `03-race-confidence-gauge.png`
- `03-race-confidence-pace-degradation.png`
- `07-training-load-sleep.png`
- `07-training-load-hr-zones.png`
- `08-recovery-sleep-stages.png`
- `09-form-cadence-trend.png`
- `09-form-cadence-scatter.png`
- `10-compliance-plan-overlay.png`

### 4. Return to Personal Data

```powershell
Remove-Item Env:\USE_SAMPLE_DATA
streamlit run dashboard/app.py
```

## Using Full Streamlit Dashboard

To run the complete dashboard with sample data:

```bash
export USE_SAMPLE_DATA=true  # Linux/Mac
# or
$env:USE_SAMPLE_DATA='true'  # Windows

streamlit run dashboard/app.py
```

This gives you access to all 10 dashboard pages including season plans and weekly logs.
