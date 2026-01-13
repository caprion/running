# Constants & Where They’re Enforced

Use this as a reference for key thresholds and where they appear. Do not change these without explicit instruction.

- Weekly floor thresholds
  - General: 15km
  - Firewall (Apr–May): 20km
  - Where:
    - `dashboard/utils/metrics.py` (`FLOOR_THRESHOLD`, `YELLOW_THRESHOLD`)
    - `dashboard/utils/data_loader.py` (`get_weekly_summary` status mapping)
    - `dashboard/app.py` (risk banner copy)
    - `dashboard/pages/6_🚨_Risk_Monitor.py` (risk month logic, floor display)

- Risk months (copy/UI)
  - High risk: Feb, Apr, May
  - Medium risk: Jan, Mar, Jun
  - Where:
    - `dashboard/app.py` (HIGH_RISK_MONTHS, MEDIUM_RISK_MONTHS)
    - `dashboard/pages/6_🚨_Risk_Monitor.py` (`MONTH_RISK`)

- Table rendering
  - Use markdown tables with `st.markdown`.
  - Avoid `st.dataframe` / `st.table`.
  - Where: all pages using tables (Consistency, Season Compare, Race Confidence).

