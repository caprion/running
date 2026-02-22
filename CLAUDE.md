# Running Training Project

## Project Purpose
This is a long-term running training and performance tracking system for continuous improvement across multiple training seasons. The goal is to become a fitter, better, faster runner by measuring progress season by season and year by year.

## Current Season: Spring 2026 HM Sub-2:00 Campaign
**Duration:** Jan 5 - May 24, 2026 (20 weeks)
**Primary Goal:** Half Marathon sub-2:00 (A-goal), 2:03 (B-goal)
**10K Tune-up:** April 12-13, 2026 - Target 52:00-54:00
**HM Race:** May 23-24, 2026

## Athlete Profile
- **Age:** 40+ endurance runner
- **Current HM PR:** 2:08:26 (Chennai, Jan 4, 2026)
- **Training capability:** 5:33/km flat-equivalent demonstrated
- **Weekly volume:** 35-50km sustainable (current); want to increase
- **Training pattern:** 4 run days (Tue/Thu/Sat/Sun) + 2 strength sessions (Mon/Wed)
- **Key limiter:** Race execution confidence, NOT fitness

## Historical Context
- **2025 Pattern:** Inconsistent volume - collapsed to 5-20km/week during Apr-Jul (travel/family)
- **Root problem:** No minimum viable volume floor (15-20km/week) during disruptions
- **2025 Progress:** VO2max 39→42, Training Status Productive/Maintaining

## Current Season Plan Location
- **Full plan:** `seasons/2026-spring-hm-sub2/plan.md`
- **Excel details:** `resources/20_Week_Training_Plan.xlsx`
- **Weekly logs:** `seasons/2026-spring-hm-sub2/weekly-logs/`
- **Training journal:** `seasons/2026-spring-hm-sub2/training-journal.md` (AI-generated, updated biweekly)

## AI Enrichment
- **Metrics:** `python -m scripts.ai.compute --days 60` computes per-run and weekly metrics
- **Insights file:** `tracking/ai-insights.json` (pace drift, HR drift, elevation, plan compliance, risk flags)
- **Sync with enrichment:** `python scripts/incremental-sync.py --days 7 --enrich`
- **Narrative analysis:** Ask Copilot "analyze my latest runs" — reads ai-insights.json + unified-cache
- **Training journal:** Copilot appends biweekly entries to training-journal.md

## Unified Cache: Schema & How to Query Runs

**Primary data source:** `tracking/unified-cache.json` — single source of truth (535+ runs, 2022–2026).

Weekly logs in `seasons/*/weekly-logs/` may be unfilled — always read unified-cache.json for actual run data.

### Top-level activity fields
```
id, name, type, date, distance_km, duration_seconds, avg_pace_min_km,
elevation_gain_m, avg_hr, max_hr, calories, avg_cadence, splits, source
```
- **type** is `"running"` (lowercase) for runs; filter with `type.lower() in ['run', 'running']`
- **date** is `"YYYY-MM-DD HH:MM:SS"` string, sort descending for latest
- **splits.lapDTOs** contains per-km split data (array of objects)

### Per-km split fields (`splits.lapDTOs[]`)
```
lapIndex, distance (1000.0), duration (seconds for 1km), averageSpeed,
averageHR, maxHR, averageRunCadence, maxRunCadence, strideLength,
elevationGain, elevationLoss, startElevation, endElevation
```
- **Pace** = `duration` seconds → `min:sec/km` (e.g., 400s = 6:40/km)
- **Elevation** per km: `elevationGain` and `elevationLoss` in meters

### Common analysis patterns

**Get latest N runs:**
```python
import json
data = json.load(open('tracking/unified-cache.json'))
runs = sorted(
    [a for a in data['activities'] if a.get('type','').lower() in ['run','running']],
    key=lambda x: x.get('date',''), reverse=True
)
latest = runs[0]  # most recent run
```

**Elevation-adjusted HR (flat-equivalent):**
Rule of thumb: uphill inflates HR ~1 bpm per 10m gain; downhill saves ~0.5 bpm per 10m loss.
```python
def flat_equivalent_hr(split):
    hr = split['averageHR']
    return hr - (split['elevationGain'] / 10.0) + (split['elevationLoss'] / 10.0 * 0.5)
```

**Weekly volume (last N weeks):**
```python
from datetime import datetime, timedelta
cutoff = (datetime.now() - timedelta(weeks=N)).strftime('%Y-%m-%d')
recent = [r for r in runs if r['date'] >= cutoff]
total_km = sum(r['distance_km'] for r in recent)
```

### PowerShell/Python tips
- For complex analysis with f-strings, write a `.py` file to session workspace and run it — PowerShell escaping breaks f-strings with dict keys.
- Always use forward slashes in `open()` paths even on Windows.
- The cache has ~558 total activities (535 runs + non-run activities).

## Key Principles
1. **Consistency > Volume** - Better to do 15-20km/week floor than skip entirely
2. **Progressive overload** - Build base → intensity → race-specific
3. **Integrated strength** - 2x/week, periodized with running phases
4. **Smart recovery** - Deload weeks built in (weeks 4, 8, 13, 15)
5. **Execution practice** - 10K race as dress rehearsal for HM pacing
6. **Cadence > Stride** - Increase turnover, let stride shorten naturally
7. **Full foot contact** - Focus on whole-foot landing, not heel strike

## Biomechanics Baseline (Feb 2026)

### Current Mechanics Profile
- **Cadence:** 162-165 spm locked in across all shoes and paces. Ceiling ~168 spm in training, 171 in hard intervals.
- **Speed gain mechanism:** Predominantly stride length (+20%) over cadence (+4%). Stride:cadence ratio 5-11:1 depending on shoe.
- **Stride at easy pace:** 84-92cm. At tempo: 103-105cm. At race: up to 110cm.
- **Warmup pattern:** Km 1 cadence starts at 152-157, takes 500-1000m to reach 162+. Consistent across all runs.

### Cadence-Pace Relationship (from 15+ runs)
| Pace Zone | Cadence |
|-----------|---------|
| 7:00-7:29/km | 154 spm |
| 6:30-6:59/km | 161 spm |
| 6:00-6:29/km | 165 spm |
| 5:30-5:59/km | 167 spm |
| 5:00-5:29/km | 171 spm |

### Hill Behavior by Shoe (Established Feb 2026)
| Shoe | Downhill stride vs Uphill stride | Pattern |
|------|--------------------------------|---------|
| Kinvara (race) | +17.8cm on steep hills | Bombs downhills with long strides |
| Pegasus (train) | +1 to +4cm | Moderate/consistent |
| Flat shoes | **-4.0cm** | Cautious downhill — shorter, protective |

### Key Biomechanics Goals
1. **Short-term (May 2026 HM):** Push cadence to 167-168 sustained at race pace. 167 spm × 103cm = 5:49/km. Need 167 × 105cm OR 170 × 103cm for 5:41/km (sub-2:00).
2. **Medium-term (18 months):** Raise baseline cadence to 170+ at easy pace. Reduce stride:cadence ratio from 5-11:1 toward 3:1.
3. **Long-term:** Full barefoot/flat shoe running with naturally high cadence and short stride.

## Shoe Rotation & Barefoot Transition

### Current Shoes
- **Saucony Kinvara 15** (4mm drop) × 2 pairs — natural shoe, race shoe, best feel
- **Nike Pegasus 39** (10mm drop) × 1 pair — training, unintentionally builds cadence
- **Flat/zero-cushion shoes** — for Sunday easy runs (started Feb 22, 2026)

### Weekly Shoe Rotation
| Day | Shoe | Session |
|-----|------|---------|
| Tue | Pegasus or Kinvara | Easy 6-8km |
| Thu | Kinvara | Quality/intervals |
| Sat | Alternate Peg/Kinvara | Long run (Kinvara for race-sim weeks) |
| **Sun** | **Flat shoes** | **Easy 3→6km (building)** |
| Race day | **Kinvara** | Fastest by data |

### Barefoot Transition Plan (18-month goal: ~Aug 2027)
**Goal:** Transition fully to flat/barefoot running. No new shoe purchases — use remaining Kinvara (×2) and Pegasus (×1) until they're done.

**Phase 1 (Feb-May 2026):** Sunday flat-shoe easy runs. 3km → 6km over 8 weeks. Monitor calf/Achilles adaptation.
**Phase 2 (Jun-Dec 2026):** Add Tuesday easy in flat shoes. 2 of 4 runs in flat shoes.
**Phase 3 (Jan-Aug 2027):** Long runs in flat shoes. Quality sessions last to transition.

**Flat shoe run ramp:** Add 500m/week if no calf soreness. If sore Monday morning, repeat same distance next week.
**Watch for:** Calf tightness beyond day 3, metatarsal soreness, Achilles morning tenderness.
**DO NOT:** Race in flat shoes this season. Do long runs >10km in flat shoes until Phase 3.

### Shoe Data Insights
- Kinvara: locks cadence at 163-164 with SD 2.05 (most consistent rhythm), enables long stride
- Pegasus: slightly higher cadence 163-166 with SD 2.96, naturally caps stride
- Flat shoes: cadence 164-165 with SD 2.25, shortest stride, fastest proprioceptive warmup, reverses downhill bombing pattern

## How to Evaluate Runs (Standard Analysis Framework)

### For every run analysis, check these in order:

**1. Basic Stats** — Load from `tracking/unified-cache.json`
- Pace, HR, distance, elevation, cadence
- Compare to plan target

**2. Splits Analysis** — From `splits.lapDTOs[]`
- Per-km pace, HR, cadence, stride, elevation
- Identify negative/positive split pattern
- Flag traffic stops (slowest pace >16:00/km = stop, not form issue)

**3. Cadence Check (PRIMARY FOCUS)**
- Km 1 cadence vs settled cadence (gap should be shrinking over time)
- Time to lock in (target: <500m)
- Any dips mid-run? Correlate with elevation
- Compare to baseline table above — is cadence improving at each pace zone?

**4. Stride Assessment**
- At easy pace: should be 84-90cm (shorter = better for barefoot transition)
- At tempo: 100-105cm is fine
- Downhill vs uphill delta: trending toward 0 or negative = good

**5. Hill Response**
- Good pattern: maintain cadence, accept slower pace, shorten stride on climbs
- Bad pattern: extend stride on downhills, cadence drops on climbs
- Compute elevation-adjusted HR if significant climbing

**6. Shoe-Specific Context**
- Note which shoe was worn (ask if not stated)
- Compare metrics to same-shoe baseline, not cross-shoe

**7. FIT File Deep Dive (monthly or on request)**
- Download: `python scripts/download-fit.py <activity_id>`
- Parse with fitparse for per-second records
- 250m segment analysis for within-km variance
- Steep hill (>3% grade) cadence/stride behavior
- Cadence distribution histogram

### Key Reference Runs (FIT files downloaded)
| Run | ID | Shoe | Significance |
|-----|-----|------|-------------|
| Dec 7, 2025 | 21189171305 | Kinvara | Best feel run — 5:58/km, 164spm, stride-dominant |
| Jan 4, 2026 | 21435729986 | Kinvara | Chennai HM race — 6:11/km, PR 2:08:26 |
| Feb 14, 2026 | 21861063425 | Pegasus | Long 17km — gradual negative split, best race-sim pacing |
| Feb 21, 2026 | 21933316016 | Pegasus | Long 16km — surge negative split, HR spike at finish |
| Feb 22, 2026 | 21948878721 | Flat | First flat-shoe run — 4.79km, cautious downhill pattern ✅ |

## Form Improvement Focus: Arm Swing (NEW - Jan 2026)

**Issue:** Static 90° arm hold with limited anterior-posterior swing (identified via gait analysis)
**Impact:** Energy waste, reduced cadence, breathing restriction
**Goal:** Dynamic "drumming" arm swing with relaxed shoulders

**Implementation:**
- **Pre-run drill:** 2min standing arm swing before EVERY run
- **During-run:** Exaggerated arm swing bursts (3-4 x 30s on easy runs)
- **Post-run:** Shoulder exercises Tue/Sun (blade squeezes, band pull-aparts)
- **Strength:** Scapular push-ups added to Session B
- **Gait videos:** Weeks 1, 5, 9, 13, 17 (track progress)

**Full guide:** `resources/arm-swing-drills-guide.md`

**IMPORTANT for weekly check-ins:**
- Always ask about pre-run drill completion
- Track gait video progress every 4 weeks
- Monitor shoulder soreness (expected weeks 1-3)
- Compare gait videos when captured

## Training Structure
- **Running days:** Tue (easy 6-8km), Thu (quality), Sat (long run), Sun (easy 3-6km in flat shoes)
- **Strength days:** Mon (Session A - 35-45min), Wed (Session B - 35-45min)
- **Post-run activation:** Tue/Sun (10min)
- **Pre-run warmup:** Dynamic mobility + 3-4 × 60-80m strides before EVERY run (especially to fix km 1 cadence lag)
- **Cadence drills (1×/week, Tue easy):** Cadence ladder — 5× (2min forced 170+ spm / 2min natural)
- **Barefoot grass strides:** Optional Sun pre-run — 4×80m on grass, no shoes, to teach 170+ cadence pattern
- **Shoe rotation:** Pegasus/Kinvara weekdays, flat shoes Sunday (see Shoe Rotation section)

## Historical Pattern Warnings

**CRITICAL: April-May School Holiday Risk**

Based on 4 years of data (2022-2025), April-May has a **28.3% floor violation rate** - double the rate of other months. 3 out of 5 major training collapses occurred during school holidays.

**Key learnings:**
- 2022: Weeks 15-18 collapsed to 11km/week
- 2025: Weeks 15-18 collapsed to 7km/week (SAME weeks!)
- Pattern repeats: 60% of collapses during Apr-Jun

**2026 Risk:** Weeks 14-17 (Apr 6 - May 3) are peak training phase for HM campaign.

**Full analysis:** `analysis/floor-violation-patterns.md`
**Dashboard:** Risk Monitor page shows real-time alerts

## How Claude Can Help

### Weekly Check-ins (Primary Use)
- Review previous week: planned vs actual
- Analyze workout quality from Strava screenshots
- Identify patterns (fatigue, consistency, missed runs)
- Apply contingency rules when needed
- **Check risk monitor** - Are we in high-risk month? Is firewall active?
- Plan next week adjustments
- Update weekly log

### Workout Analysis
- **Primary method:** Read `tracking/unified-cache.json` directly for splits, HR, pace, elevation
- **Always note which shoe** was worn — mechanics differ significantly by shoe type
- Also review Strava screenshots from `media/workouts/` when available
- Assess splits, pacing, effort distribution
- **Cadence is the primary metric** — check km 1 warmup lag, mid-run consistency, compare to baseline table
- Compute elevation-adjusted HR for hilly runs (see schema section above)
- Check hill behavior: stride delta between uphill/downhill segments (should be trending toward 0)
- Compare to previous similar workouts (query by name pattern or date range)
- Track pace progressions across weeks
- For "how was my last run" questions: load unified-cache, sort by date desc, analyze latest
- **FIT file download** (monthly or on request): `python scripts/download-fit.py <activity_id>` — gives per-second records for deep cadence/stride/elevation analysis

### Gait Analysis
- Analyze videos from `media/gait-analysis/`
- Check form: foot strike, cadence, hip drop, knee alignment, **ARM SWING**
- Compare current video to previous baseline (Weeks 1, 5, 9, 13, 17)
- Assess arm swing improvement: range of motion, shoulder relaxation, rhythm
- Suggest drills or strength focus
- Track form improvements over time

### Race Preparation
- Review taper execution
- Finalize race strategy based on training
- Post-race analysis and learnings

### Volume Increase Strategy
- Want to increase from 35-50km → 45-55km peak
- Options: Add 5th run day (Friday easy), extend long runs, or extend base phase
- Monitor: sleep, energy, niggles before increasing

### Season-by-Season Tracking
- Compare volumes, paces, consistency across seasons
- Identify what training leads to PRs
- Track injury/illness patterns
- Document progressions

## File Organization

```
running/
├── CLAUDE.md                          # This file - project context
├── README.md                          # Running dashboard (current state)
├── WORKFLOW.md                        # How to use this system
│
├── scripts/
│   ├── download-fit.py               # Download FIT file: python scripts/download-fit.py <activity_id>
│   ├── incremental-sync.py           # Sync activities: python scripts/incremental-sync.py --days 7
│   ├── parse-fit.py                  # Parse FIT file for detailed analysis
│   └── ...                           # Other scripts (see scripts/README.md)
│
├── seasons/
│   ├── 2026-spring-hm-sub2/          # Current season
│   │   ├── plan.md                   # 20-week training plan
│   │   ├── weekly-logs/              # Week-by-week detailed logs
│   │   ├── key-workouts/             # Important session analysis
│   │   └── races/                    # Race plans & reports
│   └── 2025-fall-chennai-hm/         # Historical seasons
│
├── tracking/
│   ├── unified-cache.json            # SINGLE SOURCE OF TRUTH — all run data
│   ├── fit_files/                    # Downloaded FIT files for deep analysis
│   ├── ai-insights.json              # AI-computed metrics
│   ├── monthly-summary.md
│   ├── injury-log.md
│   └── pr-history.md
│
├── analysis/
│   ├── floor-violation-patterns.md   # Historical collapse analysis (2022-2025)
│   ├── pace-progression.md
│   ├── volume-consistency.md
│   └── season-comparisons.md
│
├── media/
│   ├── workouts/                     # Strava screenshots, race videos
│   └── gait-analysis/                # Form check videos
│
├── resources/
│   └── 20_Week_Training_Plan.xlsx
│
└── templates/
    └── weekly-log-template.md
```

## Contingency Rules (Quick Reference)
- Miss 1 run: continue plan, don't double up
- Miss 2+ runs: repeat week or reduce 20%
- Travel week: 15-20km floor (3×5-7km easy) + 1 bodyweight strength
- Minor pain <3/10: skip intervals, keep easy
- Sleep <6hr: convert next quality to easy
- 3 consecutive bad workouts: take 3 extra easy days

## Communication Style
- Be direct and objective about training analysis
- Focus on data and patterns, not motivation/cheerleading
- Flag risks (overtraining, injury signs) clearly
- Suggest adjustments based on plan's contingency rules
- Celebrate PRs and milestones, but keep it grounded

## Current Week (Week 1: Jan 5-11, 2026)
- **Phase:** Recovery
- **Target volume:** 19km
- **Workouts:** Easy runs only (no quality)
- **Strength:** Week 1-2 loads (conservative)
- **Focus:** Rebuild habit after Chennai race
