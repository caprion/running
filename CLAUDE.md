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

## Key Principles
1. **Consistency > Volume** - Better to do 15-20km/week floor than skip entirely
2. **Progressive overload** - Build base → intensity → race-specific
3. **Integrated strength** - 2x/week, periodized with running phases
4. **Smart recovery** - Deload weeks built in (weeks 4, 8, 13, 15)
5. **Execution practice** - 10K race as dress rehearsal for HM pacing

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
- **Running days:** Tue (easy 6-8km), Thu (quality), Sat (long run), Sun (easy 5-7km)
- **Strength days:** Mon (Session A - 35-45min), Wed (Session B - 35-45min)
- **Post-run activation:** Tue/Sun (10min)
- **Current phase:** Week 1-2 Recovery (20-30km, easy only)

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
- Review Strava screenshots from `media/workouts/`
- Assess splits, pacing, effort distribution
- Compare to previous similar workouts
- Track pace progressions

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
├── seasons/
│   ├── 2026-spring-hm-sub2/          # Current season
│   │   ├── plan.md                   # 20-week training plan
│   │   ├── weekly-logs/              # Week-by-week detailed logs
│   │   ├── key-workouts/             # Important session analysis
│   │   └── races/                    # Race plans & reports
│   └── 2025-fall-chennai-hm/         # Historical seasons
│
├── tracking/
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
