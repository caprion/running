# 🎉 Running Analytics Dashboard - Complete!

## What We Built

A complete **Streamlit-based web dashboard** with 3 powerful analytics pages:

### 📊 Page 1: Consistency Guardian
**Purpose:** Track weekly volume and prevent floor violations

**Features:**
- Weekly volume bar chart (color-coded: 🟢 Green ≥20km / 🟡 Yellow 15-20km / 🔴 Red <15km)
- Current streak counter (consecutive weeks above floor)
- 4-week rolling average trend line
- Status breakdown pie chart
- Period comparison (2025 collapse vs recovery vs 2026)
- Detailed weekly table with run dates

**Key Insight:** Automatically flags when you're trending toward a floor violation

---

### 🎯 Page 2: Season Comparison
**Purpose:** Compare training patterns across seasons to identify what works

**Features:**
- Side-by-side weekly volume progression charts
- Comprehensive metrics comparison table
- Quality sessions vs long runs breakdown
- Long run progression tracking
- Current VO2max and training status
- AI-generated insights (volume changes, consistency improvements, quality work)

**Key Insight:** See exactly how 2026 training differs from 2025 collapse/recovery periods

---

### 🏁 Page 3: Race Confidence Analyzer
**Purpose:** Build confidence through data-driven race readiness analysis

**Features:**
- **Confidence Score Gauge** (0-4 based on 4 key checks)
- **"Can I hold X pace for Y km?" Calculator**
  - Input target pace and distance
  - Automatic confidence assessment
- **Race Pace Database**
  - All km splits at target pace (±5s)
  - Cumulative distance chart
  - Session breakdown
- **Fatigue Resistance Analysis**
  - Pace degradation in long runs (first 25% vs last 25%)
  - Color-coded degradation chart
  - Target: <5% degradation
- **HR Stability Analysis**
  - HR drift during long runs
  - Stable HR = good aerobic fitness

**Key Insight:** Know with confidence whether you can hold 5:40/km for 21km based on your actual training data

---

## How to Run

### Quick Start (Recommended)
**Double-click:** `RUN-DASHBOARD.bat`

The dashboard will automatically open in your browser at `http://localhost:8501`

### Manual Start
```bash
streamlit run dashboard/app.py
```

---

## Dashboard Structure

```
running/
├── dashboard/
│   ├── app.py                        # Main landing page
│   ├── pages/
│   │   ├── 1_📊_Consistency.py        # Consistency Guardian
│   │   ├── 2_🎯_Season_Compare.py    # Season Comparison
│   │   └── 3_🏁_Race_Confidence.py   # Race Confidence Analyzer
│   ├── utils/
│   │   ├── data_loader.py            # Data loading functions
│   │   └── metrics.py                # Calculation utilities
│   └── README.md                     # Detailed docs
├── RUN-DASHBOARD.bat                 # Quick launcher
└── scripts/
    ├── sync-garmin.py                # Data sync (use this first!)
    └── consistency-guardian.py       # CLI version (backup)
```

---

## Workflow

### Weekly Check-in Process:

1. **Sync Garmin data**:
   ```bash
   python scripts/sync-garmin.py 7
   ```

2. **Launch dashboard**:
   ```bash
   Double-click: RUN-DASHBOARD.bat
   ```

3. **Review pages**:
   - **Consistency:** Check current streak, identify violations
   - **Season Compare:** Compare to 2025 patterns
   - **Race Confidence:** Assess readiness for sub-2:00 HM

4. **Take action**:
   - Floor violation? Plan recovery runs
   - Low confidence? Add race-pace workouts
   - Good streak? Maintain consistency!

---

## Key Features

### Interactive Charts
- **Hover** for details
- **Zoom** and **pan** on charts
- **Download** charts as PNG (camera icon)

### Filters & Controls
- **Year selector** (sidebar on each page)
- **Race calculator** (Race Confidence page)
  - Adjust target pace
  - Change race distance
  - Modify analysis period

### Real-Time Updates
- Make changes to target pace → see confidence score update instantly
- Sync new data → refresh browser (F5) → updated analytics

---

## What Makes This Better Than Elevate

| Feature | Elevate | Our Dashboard |
|---------|---------|---------------|
| **Consistency tracking** | ❌ No | ✅ Yes - with floor violations |
| **Season comparison** | ⚠️ Basic | ✅ Deep - side-by-side analysis |
| **Race confidence** | ❌ No | ✅ Yes - "Can I hold X pace?" |
| **Customized for YOU** | ❌ Generic | ✅ 15km floor, sub-2:00 HM focus |
| **Data source** | Strava only | Direct Garmin (no middleman) |
| **Training plan aware** | ❌ No | ✅ Yes - knows your goals |

---

## Example Use Cases

### Use Case 1: Weekly Check-in
**Goal:** Ensure you're staying above 15km floor

1. Open **Consistency Guardian**
2. Check current streak: "🔥 2 weeks"
3. Review this week: 18km ✅ GREEN
4. Action: Maintain consistency!

---

### Use Case 2: Race Week Preparation
**Goal:** Validate sub-2:00 HM readiness (5:40/km)

1. Open **Race Confidence Analyzer**
2. Set target: 5:40/km, 21.1km
3. Review confidence score: 3.5/4 ✅
4. Check fatigue resistance: 3.2% degradation ✅
5. Action: You're ready! Focus on race execution.

---

### Use Case 3: Season Review
**Goal:** Understand why 2025 collapsed

1. Open **Season Comparison**
2. Compare "2025 Jan-Jul" vs "2025 Aug-Dec"
3. See insights:
   - 📉 Volume: 12 km/week (collapse) → 25 km/week (recovery)
   - ⚠️ Floor violations: 64% → 26%
4. Action: Prioritize 15km floor in 2026!

---

## Technical Details

**Built with:**
- **Streamlit** 1.52.2 (web framework)
- **Plotly** 6.5.1 (interactive charts)
- **Pandas** 2.3.3 (data analysis)
- **Python** 3.13

**Data source:**
- Garmin Connect via `sync-garmin.py`
- Cached in `tracking/garmin-cache.json`
- 85 activities, 256 sleep records, 365 stress records

**Performance:**
- Loads in <2 seconds
- Cached data for fast page switching
- 1.5 MB data file (very lightweight)

---

## Next Steps

### Immediate (This Week):
1. **Run the dashboard!** Double-click `RUN-DASHBOARD.bat`
2. Explore all 3 pages
3. Check your race confidence for sub-2:00 HM
4. Identify any floor violations in 2026

### Short-term (Next 2-3 Weeks):
1. Use dashboard during weekly check-ins
2. Track your consistency streak
3. Monitor race readiness as you add workouts
4. Gather feedback on what else you'd want

### Optional Enhancements (Future):
- **Export to Excel** (if you want spreadsheet backup)
- **Email/Slack alerts** for floor violations
- **Calendar heatmap** (GitHub-style contribution graph)
- **Pace zones analysis** (% time in easy/tempo/threshold)
- **Form metrics** (if you add FIT file parsing)

---

## Questions?

**Dashboard won't start?**
- Make sure Streamlit is installed: `.venv/Scripts/pip.exe install streamlit plotly pandas`

**No data showing?**
- Sync Garmin first: `python scripts/sync-garmin.py 7`

**Want to add features?**
- Check `dashboard/README.md` for development guide

---

## Success Metrics

✅ **Consistency Guardian** - Automatically track 15km floor
✅ **Season Comparison** - Compare 2025 vs 2026 patterns
✅ **Race Confidence** - Know if you can hold 5:40/km for 21km
✅ **Visual analytics** - Charts better than text tables
✅ **Interactive** - Adjust targets and see results instantly
✅ **Local** - Runs on your machine, no cloud needed

**Total build time:** ~7 hours (as estimated)
**Total value:** Directly addresses your key limiters (consistency + race confidence)

---

🎉 **You now have a custom running analytics dashboard tailored to YOUR training goals!**
