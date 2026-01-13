# Agents Guide for the Running Project

This guide orients AI/code agents working in this repository. It defines scope, safety rails, file layout, and conventions so changes remain helpful and non-disruptive.

## Scope & Defaults

- Scope: Entire repository (`C:\Learn\running`).
- Default mode: Documentation-first. Do not change behavior or break the dashboard. If code changes are explicitly requested, keep them surgical and reversible.
- Keep existing filenames, routes, and interfaces intact. No renames or mass refactors.

## What’s Here (High Level)

- Dashboard (Streamlit): `dashboard/`
  - Entry: `dashboard/app.py`
  - Pages: `dashboard/pages/` (number-prefixed for order)
  - Utils: `dashboard/utils/` (`data_loader.py`, `metrics.py`)
- Data caches: `tracking/garmin-cache.json`, `tracking/strava-cache.json` (written by sync scripts)
- Sync scripts: `scripts/` (Garmin + Strava)
- Season materials: `seasons/` (plans, weekly logs, reviews)
- Docs: multiple top-level `.md` files; see `docs/README.md` for an index

## Environment Assumptions

- OS: Windows 11 (ARM) primary.
- Python: 3.9+ (3.13 used during development).
- Streamlit >= 1.52, Plotly >= 6.5, Pandas >= 2.3.
- No `pyarrow` on ARM Windows. Avoid `st.dataframe`/`st.table`; prefer markdown tables.

## Safety Rails (Do/Don’t)

- Do:
  - Add/extend documentation (Markdown) freely.
  - Add new Streamlit pages in `dashboard/pages/` without changing existing behavior.
  - Use Plotly for charts and markdown tables for tabular data.
  - Read data via `dashboard/utils/data_loader.py` helpers.
  - Link to existing docs instead of duplicating content.

- Don’t:
  - Rename/move existing files or pages.
  - Introduce new runtime dependencies without explicit approval.
  - Re-enable `st.dataframe`/`st.table` (pyarrow not available).
  - Change thresholds (e.g., 15/20km floors) or business logic unless requested.

## Coding Conventions (Dashboard)

- New page filenames: `N_Name.py` (N = integer order). Example: `7_🧭_New_Insight.py` (emoji optional).
- Imports: use `dashboard/utils` helpers (e.g., `activities_to_dataframe`, `get_weekly_summary`).
- Caching: avoid complex pickling of datetimes. If used, prefer `@st.cache_data(ttl=300)` sparingly.
- Tables: render with `st.markdown` pipes; avoid pyarrow-dependent widgets.
- Charts: use Plotly; set `use_container_width=True`.

## Data Flow

1. `scripts/sync-garmin.py` and `scripts/sync-strava.py` write caches into `tracking/`.
2. `dashboard/utils/data_loader.py` loads and merges activities (`load_activities`, `activities_to_dataframe`).
3. Pages consume DataFrame summaries (`get_weekly_summary`, `get_monthly_summary`) and `metrics.py` helpers.

## Known Pitfalls

- Streamlit cache + datetime pickling can error. If caching is used, set a TTL and keep objects simple.
- ARM64 Windows lacks `pyarrow`. All table renders must be markdown.
- Clearing cache: use `CLEAR-CACHE.bat` or delete `.streamlit/`.

## Add a New Page (Safe Pattern)

1. Create `dashboard/pages/7_My_Page.py`.
2. Import from `dashboard/utils`:
   - `from utils.data_loader import activities_to_dataframe, get_weekly_summary`
   - `from utils.metrics import FLOOR_THRESHOLD, YELLOW_THRESHOLD, ...`
3. Build charts with Plotly; tables with markdown.
4. Avoid modifying existing utils; if needed, add new helpers with conservative defaults.

## Documentation Conventions

- Central index: `docs/README.md`. Add new docs there under a relevant category.
- Architecture overviews: `docs/ARCHITECTURE.md`.
- Troubleshooting/bug logs: keep using `KNOWN-ISSUES.md`, `FIXED-*.md`.

## Validation & Non-Regression

- Run: `streamlit run dashboard/app.py` and navigate all pages.
- If you add a script or page, ensure it runs with existing dependencies only.
- Do not modify caches in `tracking/` directly; scripts own those files.

## Quick References

- Quick start: `QUICK-START.md`
- Workflow: `WORKFLOW.md`
- Dashboard usage: `dashboard/README.md`, `DASHBOARD-SUMMARY.md`
- Scripts: `scripts/README.md`, `STRAVA-SETUP.md`
- Context: `CLAUDE.md`
- Analysis: `analysis/floor-violation-patterns.md`

Prefer documentation and small, isolated additions over changes to established behavior.

