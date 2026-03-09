# Garmin Workout Automation

## ✅ Auto-Generated from Training Plan

Workouts are automatically parsed from `seasons/2026-spring-hm-sub2/plan.md` — no manual workout definitions needed.

### Quick Start

```bash
# Preview workouts for a week
python scripts/create-garmin-workouts.py --week 10 --dry-run

# Create and schedule workouts in Garmin Connect
python scripts/create-garmin-workouts.py --week 10

# Create specific days only
python scripts/create-garmin-workouts.py --week 10 --days thu,sat

# List all weeks from the plan
python scripts/create-garmin-workouts.py --list
```

### How It Works

The script reads your training plan and auto-generates structured Garmin workouts:

1. **Weeks 9-20** — Parsed from per-week detailed sections (`#### Week N` tables with exact per-day prescriptions)
2. **Weeks 1-8** — Parsed from the summary table (`Weekly Volume Progression`) with percentage-based distance calculation

No manual workout definitions. Update the plan, and the script picks up the changes.

### What It Supports

| Workout Type | Example | Garmin Steps |
|-------------|---------|--------------|
| Easy run | `Easy 8km` | 1 step — open distance |
| Tempo | `Tempo 6km@5:40-5:45` | 3 steps — warmup (lap) → tempo with pace → cooldown (lap) |
| Intervals | `3×2km@5:35` or `4×1.5km@5:35` | 3 steps — warmup (lap) → repeat group → cooldown (lap) |
| Sharpener | `Sharpener 4×600m@5:15` | Same as intervals |
| Structured long run | `Long 21km: 6E + 10@5:45 + 5E` | Multi-step — easy/tempo/easy segments with distances |
| Long w/ tempo | `Long 16km w/ 6km@5:50` | 3 steps — warmup (lap) → tempo → cooldown (lap) |
| Fast finish | `Long 18km fast-finish` | 2 steps — easy + tempo (parsed from details column) |
| Easy w/ tempo | `Easy 8km w/ 2km@5:45` | 3 steps — warmup (lap) → tempo → cooldown (lap) |
| Strides | `Easy 4km + strides` | Repeat group — 4×20s fast / 60s recovery |
| Flat-shoe easy | `Flat-shoe easy 5km` | 1 step — open distance |

### Warmup / Cooldown Convention

- **Tempo, intervals, long-tempo** — Warmup and cooldown use **lap button** (press lap when ready). They are part of the overall run.
- **Structured long runs** — Segments use **distance-based** transitions (auto-advance at each km target).
- **Recovery time** — Parsed from the details column (e.g., "2min jog recovery" → 120s, "90s jog recovery" → 90s).

---

## Requirements

```bash
pip install garminconnect python-dotenv
```

### Environment Setup

Create `.env` file in project root:
```
GARMIN_EMAIL=your@email.com
GARMIN_PASSWORD=yourpassword
```

---

## Modifying Workouts

**To change a workout:** Edit the per-week table in `plan.md`, then re-run the script. The session column is parsed directly.

**Supported session formats in plan.md:**
```
| Tue | Easy 8km             | 6:45-7:15/km                          |
| Thu | **Tempo 6km@5:40**   | Total ~9km with warmup/cooldown       |
| Sat | **Long 21km: 6E + 10@5:45 + 5E** | Race simulation at HM distance |
| Sun | Flat-shoe easy 3-4km | Short recovery                        |
```

**Key formatting rules:**
- Distances: `Nkm` (supports decimals like `1.5km`)
- Paces: `N:NN` or `N:NN-N:NN` for ranges
- Intervals: `N×Nkm@N:NN` (Unicode × or x both work)
- Structured segments: `NE` for easy, `N@N:NN` for paced, joined with ` + `
- Recovery info goes in the Details column (e.g., "2min jog recovery")

---

## Archived Documentation

Low-level API docs (for reference only):
- [Garmin Workout Creation Guide](docs/archived/garmin-workout-creation-guide.md)
- [API Quick Reference](docs/archived/garmin-api-quick-reference.md)
