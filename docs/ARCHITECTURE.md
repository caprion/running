# Architecture Overview

This document explains how data flows through the system and how the main components fit together. It’s reference-only and does not change runtime behavior.

## Components

- Scripts (`scripts/`)
  - Sync data from Garmin Connect to local JSON caches.
  - Primary entry points: `incremental-sync.py`, `daily-sync.py`.
- Tracking (`tracking/`)
  - Cache files written by scripts: `garmin-cache.json`, `strava-cache.json`.
  - Weekly summary markdowns for human review.
- Dashboard (`dashboard/`)
  - `app.py` — Landing page and global notices (e.g., risk month alerts).
  - `pages/` — Feature pages (Consistency, Season Compare, Race Confidence, Plan, Logs, Risk Monitor).
  - `utils/` — Data access and metrics (`data_loader.py`, `metrics.py`).
- Seasons & Docs (`seasons/`, top-level docs)
  - Training plan, weekly logs, guidance, and project context.

## Data Flow

1. Sync
   - Run `python scripts/incremental-sync.py --days N` or `python scripts/daily-sync.py`.
   - Outputs: `tracking/unified-cache.json` (primary), `tracking/garmin-cache.json`.

2. Load & Merge
   - `dashboard/utils/data_loader.py`:
     - `load_garmin_data()` / `load_strava_data()` read caches.
     - `merge_activities()` deduplicates Garmin/Strava activities.
     - `load_activities()` returns unified list.
     - `activities_to_dataframe()` converts to pandas DataFrame and derives fields:
       - `date`, `year`, `month`, `iso_year`, `week`, `week_key`, `month_key`, etc.
     - `get_weekly_summary()` / `get_monthly_summary()` aggregate totals and statuses.

3. Analyze & Display
   - Pages import helpers and compute summaries.
   - Plotly: interactive charts.
   - Tables: markdown (avoid `st.dataframe`/`st.table`).

## Key Boundaries

- Don’t mutate caches in `tracking/` manually — only scripts write them.
- Avoid adding dependencies (esp. `pyarrow`) — ARM Windows constraints.
- Keep tables as markdown to maintain portability.
- When adding metrics, prefer new helper functions over altering existing ones.

## Important Thresholds & Conventions

- Weekly floor: 15km (general), 20km during critical months (April–May firewall).
- Status colors (via `metrics.py`):
  - `<15km` → RED, `15–20km` → YELLOW, `≥20km` → GREEN.
- Page order: `N_Title.py` naming in `dashboard/pages/`.

## How to Extend Safely

- New page: add `dashboard/pages/7_My_Page.py`, import utils, use Plotly + markdown tables.
- New metric: add helper in `dashboard/utils/metrics.py` (pure functions, clear inputs/outputs).
- New aggregation: add to `data_loader.py` (return DataFrame with derived/aggregated columns).
- Document new features in `docs/README.md` and, if useful, a short `docs/<feature>.md`.

## Troubleshooting Pointers

- Cache errors or datetime pickling: clear Streamlit cache (`CLEAR-CACHE.bat`).
- PyArrow missing: expected on ARM Windows — use markdown tables.
- See `docs/archived/KNOWN-ISSUES.md` and `docs/archived/FINAL-FIX-PYARROW.md` for prior fixes and patterns.

