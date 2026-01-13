# Running Analytics Dashboard

Interactive web-based dashboard for analyzing your running training data from Garmin Connect.

## Quick Start

1. **Sync your Garmin data** (if you haven't already):
   ```bash
   python scripts/sync-garmin.py 365
   ```

2. **Launch the dashboard**:
   ```bash
   streamlit run dashboard/app.py
   ```

3. **Open in browser**: The dashboard will automatically open at `http://localhost:8501`

## Pages

### 📊 Consistency Guardian
- Weekly volume bar chart (color-coded: Green/Yellow/Red)
- Current streak tracker
- 4-week rolling average
- Status breakdown (pie chart)
- Period comparisons (2025 collapse vs recovery)
- Detailed weekly table

### 🎯 Season Comparison (Coming soon)
- Side-by-side season analysis
- VO2max progression
- Quality sessions breakdown
- Long run trends

### 🏁 Race Confidence (Coming soon)
- "Can I hold this pace?" calculator
- Race pace database
- Fatigue resistance analysis
- HR stability tracking

## Features

- **Interactive charts**: Hover for details, zoom, pan
- **Real-time updates**: Refresh data by re-running sync script
- **Responsive**: Works on desktop and tablet
- **Fast**: Cached data loading for quick navigation

## Dashboard Structure

```
dashboard/
  app.py                    # Main landing page
  pages/
    1_📊_Consistency.py      # Consistency Guardian
    2_🎯_Season_Compare.py  # (To be built)
    3_🏁_Race_Confidence.py # (To be built)
  utils/
    data_loader.py          # Data loading functions
    metrics.py              # Calculation utilities
```

## Tips

- **Refresh data**: Run sync script, then refresh browser (F5)
- **Change years**: Use the sidebar filter on each page
- **Export charts**: Hover over charts → camera icon to download PNG
- **Keyboard shortcuts**:
  - `R` - Rerun the app
  - `C` - Clear cache

## Troubleshooting

**Error: "NotImplementedError: (dtype('<M8[ns]'), array..."**
This is a cache corruption issue. Fix:
```bash
# Option 1: Use the batch file
Double-click: CLEAR-CACHE.bat

# Option 2: Manual
Delete the .streamlit folder in project root
Restart dashboard
```

**Dashboard won't start:**
```bash
# Reinstall Streamlit
.venv/Scripts/pip.exe install streamlit plotly pandas
```

**No data showing:**
```bash
# Sync Garmin data
python scripts/sync-garmin.py 7
```

**Port already in use:**
```bash
# Use a different port
streamlit run dashboard/app.py --server.port 8502
```

**PyArrow warning:**
Safe to ignore - dashboard works fine without it. This happens on ARM64 Windows because pyarrow doesn't have pre-built wheels.

## Development

To add a new page:
1. Create `pages/X_Name.py` (X = number for ordering)
2. Import utils from `utils/` directory
3. Streamlit will automatically detect the new page

## Requirements

- streamlit>=1.52.0
- plotly>=6.5.0
- pandas>=2.3.0
- python>=3.9
