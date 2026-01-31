# Running Project Workflow Guide

This document explains how to use this project structure for training tracking, analysis, and season-by-season improvement.

## Quick Start

### Daily/After Workout
1. Complete your workout
2. Screenshot Strava summary (splits, HR, pace, etc.)
3. Save to `media/workouts/YYYY-MM-DD-description.jpg`
4. (Optional) Ask Claude to analyze the workout immediately

### Weekly Check-in (Every Sunday)
1. Open Claude Code in this directory: `cd c:\Learn\running`
2. Say: "Let's do the weekly check-in"
3. Claude will:
   - Review your weekly log
   - Analyze all workout screenshots
   - Update the weekly log with analysis
   - Provide recommendations for next week
   - Update README.md dashboard
4. You fill in subjective notes and weekly rating

### Monthly (First Sunday of Month)
1. Review progress on README.md dashboard
2. Check pace progressions and consistency
3. Celebrate wins and identify patterns

## Detailed Workflows

## 1. Workout Analysis Workflow

### Immediate Post-Workout (5 minutes)
After your run:

1. **Screenshot Strava data**
   - Open Strava on phone/web
   - Capture: Summary (pace, distance, time), Splits (lap paces), Heart rate zones
   - Save as: `YYYY-MM-DD-description.jpg`

2. **Save to project**
   - Place in: `media/workouts/`
   - Naming: `2026-01-06-tuesday-easy.jpg`

3. **Quick analysis (optional)**
   - Open Claude Code: `claude`
   - Say: "Analyze my workout from today" or "Review my Tuesday easy run"
   - Claude reads screenshot and provides feedback

### What Claude Analyzes
- **Pacing:** Were splits consistent? Too fast/slow?
- **Effort:** HR zones appropriate for workout type?
- **Progression:** Compare to similar previous workouts
- **Recovery:** Signs of fatigue or freshness
- **Plan alignment:** Did it match the training plan?

### Example Prompts
- "Analyze my tempo workout from Thursday"
- "Was my long run pacing appropriate?"
- "Compare today's intervals to last week's"
- "Why did my pace drop in the second half?"

---

## 2. Weekly Check-in Workflow

**When:** Every Sunday evening (or Monday morning)
**Duration:** 15-20 minutes
**Purpose:** Review week, update logs, plan ahead

### Step-by-Step Process

#### Step 1: Sync Garmin Data
Pull the latest data from Garmin Connect:
```bash
cd c:\Learn\running
python scripts/incremental-sync.py --days 7
```

This fetches:
- Activities (runs with pace, HR, splits)
- Training metrics (VO2max, training load, training status)
- Sleep data (duration, deep sleep %)
- Resting heart rate trends (key recovery indicator)

#### Step 2: Generate Weekly Summary
Create automated training report:
```bash
python scripts/weekly-summary.py
```

This generates `tracking/weekly-summary-YYYY-MM-DD.md` with:
- Running summary (volume, pace, HR zones)
- Training metrics and VO2max
- Resting HR trend analysis (recovery indicator)
- Sleep analysis (duration, quality)
- Automated flags and warnings (sleep alerts, HR trends, pacing issues)

#### Step 3: Gather Your Week's Data
Before starting check-in with Claude, have ready:
- Generated weekly summary (from step 2)
- All workout screenshots from the week (if doing detailed analysis)
- Strength training notes (weights, reps completed)
- Subjective notes (energy, motivation, any pain/niggles)

#### Step 4: Start Check-in with Claude
Open Claude Code:
```bash
cd c:\Learn\running
claude
```

Say: **"Let's do the weekly check-in for Week X"**

Provide Claude with your generated weekly summary and any additional context.

#### Step 5: Claude's Analysis
Claude will:
1. Read your weekly log (`seasons/2026-spring-hm-sub2/weekly-logs/week-XX.md`)
2. Check all workout screenshots from `media/workouts/`
3. Compare planned vs actual volume/workouts
4. Analyze workout quality and pacing
5. Assess consistency and recovery status
6. Identify any red flags (overtraining, injury risk)
7. Review the automated flags from weekly summary (sleep alerts, RHR warnings, pacing issues)

#### Step 6: You Provide Subjective Input
Answer these questions (Claude will ask):
- **Energy:** Overall energy level 1-10
- **Motivation:** Training motivation 1-10
- **Soreness:** Any lingering fatigue or niggles
- **External factors:** Work stress, travel, life events
- **Notes on flagged issues:** Context for any warnings (e.g., "poor sleep due to work deadline")

#### Step 7: Claude Updates Weekly Log
Claude fills in:
- **Actual volume and runs completed**
- **Workout analysis section**
- **Pace progression notes**
- **Recovery assessment** (incorporating resting HR trends)
- **Recommendations for next week**

#### Step 8: You Complete Subjective Sections
You add to the weekly summary's Notes section:
- **Energy levels:** How you felt overall
- **Niggles/soreness:** Any issues or concerns
- **Life stress:** External factors affecting training
- **Next week focus:** One primary goal

#### Step 9: Update Dashboard & Plan Next Week
Claude updates `README.md`:
- Current week stats
- Season totals
- Consistency metrics
- Upcoming key workouts

Then, plan next week by:
- Reviewing next week's planned workouts
- Make any adjustments based on this week
- Apply contingency rules if needed
- Set one primary focus

### Key Questions for Check-in
- Did I hit planned volume? If not, why?
- Were quality workouts executed well?
- Am I progressing in pace/effort?
- Any signs of overtraining or injury?
- Should we adjust next week's plan?

### Contingency Rules Application
Claude will suggest if needed:
- **Missed 1 run:** Continue plan, don't make up
- **Missed 2+ runs:** Repeat week or reduce 20%
- **Fatigue signs:** Convert next quality to easy
- **Pain/niggles:** Skip intervals, medical eval if persistent
- **Sleep <6hr:** Reduce intensity next week

---

## 3. Gait Analysis Workflow

**When:** Every 4-6 weeks, or when something feels off
**Duration:** 15 minutes capture + 10 minutes analysis

### Recording Gait Video

#### Equipment Needed
- Smartphone with video
- Tripod or stable surface (chair, box)
- Treadmill OR 30m straight outdoor space

#### Camera Setup

**Side View (Most Important)**
- Position: 10-15m perpendicular to running path
- Height: Hip level
- Capture: Full body in frame, 10-15 seconds
- Pace: Easy/comfortable (your natural gait)

**Rear View**
- Position: Directly behind, 10-15m away
- Height: Hip level
- Capture: Full body, 10-15 seconds
- Focus: Leg alignment, hip drop, foot placement

**Front View (Optional)**
- Position: Facing you, 10-15m away
- Shows: Arm crossover, symmetry

#### Best Practices
- Wear: Fitted shorts/tights (see leg movement)
- Run naturally - don't try to "fix" anything
- Run at easy pace (6:30-7:00/km for you)
- 10-15 seconds is enough
- Film multiple angles if possible

### Saving Video
```
media/gait-analysis/
├── 2026-01-15-treadmill-side.mp4
├── 2026-01-15-treadmill-rear.mp4
└── 2026-02-15-outdoor-side.mp4
```

### Claude Analysis
Say: **"Analyze my gait from [date]"**

Claude will assess:
- **Foot strike:** Heel/midfoot/forefoot pattern
- **Cadence:** Steps per minute (target 170-180)
- **Vertical oscillation:** Bouncing (minimize)
- **Overstriding:** Foot landing ahead of body
- **Knee alignment:** Valgus collapse, tracking
- **Hip drop:** Trendelenburg sign (weak glutes)
- **Arm swing:** Crossover, tension
- **Posture:** Forward lean, hip extension
- **Push-off:** Toe-off power

### What You Get
- Specific form issues identified
- Strength exercises to address weaknesses
- Drills to improve technique
- Comparison to previous gait videos
- Risk factors for injury

---

## 4. Race Preparation Workflow

### 2 Weeks Before Race

**Check-in Focus:** Taper execution
- Review last 2-3 weeks of training
- Confirm fitness markers hit
- Plan taper week details
- Reduce strength training volume

**Say to Claude:** "Let's review my training for the [10K/HM] race in 2 weeks"

### 1 Week Before Race

**Finalize Race Strategy**
- Review goal times based on training
- Set A/B/C goals
- Plan pacing strategy (start/middle/finish)
- Create race day checklist

**Say to Claude:** "Help me finalize my race strategy for [race name]"

Claude will:
- Analyze recent training paces
- Recommend goal times
- Create segment-by-segment pacing plan
- Provide pre-race checklist

### Race Day

**Morning Of:**
- Follow pre-race checklist
- Screenshot race plan on phone
- Trust the training

### Post-Race (Within 48 hours)

**Create Race Report**
Say: **"Let's create a race report for [race name]"**

Provide:
- Official time and placement
- Strava/watch data (screenshots)
- Split times
- How you felt (start/middle/finish)
- Conditions (weather, course)
- What went well/poorly

Claude creates race report in:
`seasons/2026-spring-hm-sub2/races/YYYY-MM-DD-race-name.md`

**Analysis Includes:**
- Pacing execution vs plan
- Effort assessment
- Goal achievement
- Learnings for next race
- Training implications
- Recovery recommendations

---

## 5. Monthly Review Workflow

**When:** First Sunday of each month
**Duration:** 10 minutes

### What to Review

#### Volume Trends
- Weekly average for month
- Consistency (weeks with 3+ runs)
- Compare to plan

#### Pace Progression
- Are easy runs feeling easier?
- Quality workouts hitting targets?
- Long run paces improving?

#### Consistency Tracking
- Missed workouts: why?
- Minimum floor maintained (15-20km)?
- Strength sessions completed?

### Update Monthly Summary
Say: **"Let's create the monthly summary for [Month]"**

Claude creates: `tracking/monthly-summary.md`

Includes:
- Total volume
- Runs completed
- Key workouts achieved
- Pace progressions
- Consistency metrics
- Highlights and lowlights
- Next month focus

---

## 6. Season Transition Workflow

**When:** After goal race + recovery weeks
**Duration:** 30-45 minutes

### Step 1: Season Review
Say: **"Let's create the season review for [Season Name]"**

Together, analyze:
- Goals vs results
- Total volume and consistency
- Training progressions
- Race performances
- What worked / didn't work
- Injuries/setbacks
- Key learnings

Claude creates:
`seasons/YYYY-season-name/season-review.md`

### Step 2: Compare Seasons
Say: **"Compare this season to previous seasons"**

Claude analyzes:
- Volume trends year-over-year
- Pace improvements
- Consistency patterns
- What training leads to PRs
- Injury/illness patterns

Updates: `analysis/season-comparisons.md`

### Step 3: Plan Next Season
Based on learnings, Claude helps:
- Set new season goals
- Choose race targets
- Adjust training approach
- Plan volume progression
- Incorporate learnings

---

## 7. Injury/Setback Workflow

**When:** Experiencing pain, illness, or forced break

### Immediate Assessment
Say: **"I'm experiencing [pain/issue], let's assess"**

Provide:
- Location and severity (1-10)
- When it started
- What makes it worse/better
- Any recent training changes

Claude will:
- Reference contingency rules
- Suggest appropriate modifications
- Recommend if medical evaluation needed
- Plan training adjustments

### Update Injury Log
Document in: `tracking/injury-log.md`
- Date and description
- Severity and duration
- Training modifications
- Treatment approach
- Resolution and learnings

### Return to Training
Say: **"Plan my return to training after [injury/illness]"**

Claude creates:
- Gradual progression plan
- Modified workouts
- Volume rebuild strategy
- Monitoring checkpoints

---

## 8. Garmin Data Sync

**When:** Before weekly check-ins, or anytime you want updated data
**Duration:** 30 seconds
**Setup required:** See `scripts/README.md` for authentication setup

### Sync Latest Data
```powershell
# Sync last 7 days (default)
python scripts/daily-sync.py

# Sync custom number of days
python scripts/incremental-sync.py --days 14
```

### Generate Weekly Summary
```powershell
python scripts/weekly-summary.py
```

This creates `tracking/weekly-summary-YYYY-MM-DD.md` with:
- Running volume, pace, HR zones
- VO2max, training load, training status
- **Resting heart rate trends** (primary recovery indicator)
- Sleep analysis with alerts
- Automated warnings and flags

### What Data is Available
- **Activities:** Distance, pace, HR, elevation, cadence, splits
- **Training Metrics:** VO2max, training load (7d), training status
- **Sleep:** Duration, deep sleep %, nightly breakdown
- **Resting HR:** Current + 7-day average (key recovery metric)
- **Stress:** Daily stress scores (7 days)

### Using in Check-ins
1. Run sync before Sunday check-in
2. Generate weekly summary
3. Paste summary content into Claude conversation
4. Claude interprets flags and trends
5. You add subjective context

See `scripts/README.md` for troubleshooting and setup details.

---

## 9. Quick Commands

### Garmin Sync
- "python scripts/incremental-sync.py --days 7"
- "python scripts/weekly-summary.py"

### Workout Analysis
- "Analyze my workout from [date]"
- "Review today's tempo run"
- "Compare my intervals to last week"

### Weekly Check-in
- "Let's do the weekly check-in"
- "Review this week's training"
- "Update my weekly log"

### Planning
- "What's planned for next week?"
- "Should I adjust my training plan?"
- "Apply the travel week contingency"

### Gait/Form
- "Analyze my gait from [date]"
- "What form issues should I work on?"

### Race Prep
- "Help me plan race strategy"
- "Create my race day checklist"
- "Analyze my race performance"

### Progress Tracking
- "Show my pace progressions"
- "How's my consistency this season?"
- "Compare this month to last month"

---

## Tips for Best Results

### For Claude Code
1. **Use clear dates:** "January 6" or "2026-01-06"
2. **Reference files:** Claude can read all files in this project
3. **Be specific:** "Thursday tempo" vs "my workout"
4. **Ask follow-ups:** Claude remembers the conversation context

### For Claude Desktop
1. **Use @ references:** `@weekly-logs/week-01.md`
2. **Same folder access:** Both apps read same files
3. **Import MCP servers:** `claude mcp add-from-claude-desktop`

### For Screenshots
1. **Clear naming:** Date + workout type
2. **Include all data:** Splits, HR, elevation
3. **Save immediately:** Don't lose workout data

### For Consistency
1. **Sunday check-ins:** Non-negotiable weekly ritual
2. **Screenshot everything:** Even "boring" easy runs
3. **Quick notes:** Jot subjective feel immediately post-run

---

## File Organization Reference

### Active Season Files
```
seasons/2026-spring-hm-sub2/
├── plan.md                    # Training plan details
├── weekly-logs/
│   ├── week-01.md            # Detailed weekly tracking
│   ├── week-02.md
│   └── ...
├── key-workouts/             # Deep dives on important sessions
└── races/                    # Race plans and reports
```

### Media Files
```
media/
├── workouts/                 # Strava screenshots
│   ├── 2026-01-06-tuesday-easy.jpg
│   └── ...
└── gait-analysis/           # Form videos
    ├── 2026-01-15-side.mp4
    └── ...
```

### Tracking Files
```
tracking/
├── monthly-summary.md       # Month-by-month stats
├── injury-log.md           # Issues and resolutions
└── pr-history.md           # Personal records
```

### Analysis Files
```
analysis/
├── pace-progression.md     # How paces evolve
├── volume-consistency.md   # Consistency patterns
└── season-comparisons.md   # Year-over-year
```

---

## 10. Continuous Improvement

This system is designed to **evolve with you**. As you use it, you'll discover:
- What tracking methods work best
- Which analyses are most valuable
- How to optimize your check-in routine

**Feel free to adjust:**
- Weekly log template
- Check-in frequency
- Level of detail
- Analysis focus areas

The goal is **sustainable progress tracking** that helps you become a better runner season after season.

---

## 11. Getting Started Checklist

- [x] Folder structure created
- [x] CLAUDE.md (project context) created
- [x] README.md (dashboard) created
- [x] Week 1 log ready
- [x] Historical Chennai season documented
- [x] Garmin sync scripts setup (incremental-sync.py, weekly-summary.py)
- [x] OAuth session authenticated
- [ ] Complete first workout and screenshot it
- [ ] Run first Garmin sync and weekly summary
- [ ] Do first weekly check-in (Sunday, Jan 11)
- [ ] Record first gait video (Week 4-6)
- [ ] Complete first month review (Feb 2)

---

**You're all set!** Start training, screenshot your workouts, and we'll do the first check-in on Sunday, January 11, 2026.
