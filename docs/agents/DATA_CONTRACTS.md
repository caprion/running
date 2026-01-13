# Data Contracts (Minimal)

Document fields relied upon by the dashboard. Keep stable unless an ADR approves changes.

## Activities (Merged)
- Source: `dashboard/utils/data_loader.py` (`load_activities`, `merge_activities`)
- Required fields used downstream:
  - `id` (string/int)
  - `name` (string)
  - `type` (expecting `running`)
  - `date` (ISO-like string; parsed to datetime)
  - `distance_km` (float)
  - `avg_hr` (optional, float)
  - `splits.lapDTOs[*].averageSpeed` (m/s) — for pace analysis
  - `source` (`garmin` | `strava` | `both`)

## Derived (DataFrame)
- Created by `activities_to_dataframe()`:
  - `date` (datetime), `date_only` (date)
  - `year`, `month`, `iso_year`, `week`
  - `week_key` (e.g., `2026-W01`)
  - `month_key` (e.g., `2026-01`)

## Weekly Summary
- From `get_weekly_summary(df)`:
  - `week_key`, `distance_km`, `runs`, `avg_hr`, `dates`, `status` (GREEN/YELLOW/RED), `year`, `week`
- Status mapping aligns with floors (see `CONSTANTS.md`):
  - `>=20` → GREEN, `15–<20` → YELLOW, `<15` → RED

## Training Status
- From Garmin cache (`tracking/garmin-cache.json`):
  - `training_status.vo2max` (number/string)
  - `training_status.training_effect_label` (string)

## Contract Changes
- Propose via ADR in `DECISIONS.md` and update this file before implementation

