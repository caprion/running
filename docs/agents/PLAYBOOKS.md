# Agent Playbooks

Step-by-step recipes for common tasks.

## Weekly Check-in (Docs + Dashboard)
1. Run sync (typical): `python scripts/sync-garmin.py 7`
2. Open dashboard: `streamlit run dashboard/app.py`
3. Review Consistency, Risk Monitor, and current week in `README.md`
4. Update weekly log under `seasons/2026-spring-hm-sub2/weekly-logs/`
5. Summarize findings and next steps in the week log; link to any analysis

## Add a New Dashboard Page (Safe)
1. Create `dashboard/pages/7_My_Page.py`
2. Import: `from utils.data_loader import activities_to_dataframe, get_weekly_summary`
3. Use Plotly for charts; render tables with markdown
4. No changes to existing pages/utilities; no new deps

## Diagnose Cache/Datetime Errors
1. Clear cache: run `CLEAR-CACHE.bat` or delete `.streamlit/`
2. Remove/limit caching decorators (`@st.cache_data`); if needed, set `ttl=300`
3. Ensure data conversion avoids `.astype(str)` on datetimes; use `str(d)` per item

## Confirm Data Availability
1. Check activities loaded:
   - `python -c "from dashboard.utils.data_loader import load_activities; print(len(load_activities()))"`
2. If zero, ensure `tracking/garmin-cache.json` or `tracking/strava-cache.json` exist and re-run sync

