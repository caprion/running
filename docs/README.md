# Documentation Index

This repository has rich documentation. This index groups what exists so you can find the right guide fast.

## Getting Started

- `QUICK-START.md` — One-page quick start for syncing and running the dashboard
- `README.md` — Project overview and links
- `dashboard/README.md` — Launching and using the Streamlit dashboard

## Workflows

- `WORKFLOW.md` — Daily, weekly check-in, and gait analysis workflows
- `docs/archived/SESSION-SUMMARY.md` — Consolidated session summary (archived)

## Data Sync & Integrations

- `scripts/README.md` — Garmin sync setup and usage
- Scripts:
  - `scripts/incremental-sync.py` — Primary sync (use this)
  - `scripts/daily-sync.py` — Convenience wrapper
  - `scripts/weekly-summary.py` — Training reports
  - `scripts/import-session.py` — Auth setup
- Strava: `docs/archived/STRAVA-SETUP.md` (archived, phased out)

## Dashboard

- `dashboard/README.md` — Dashboard features and usage
- Archived fix logs: `docs/archived/` (DASHBOARD-SUMMARY, KNOWN-ISSUES, BUGFIX-*, FIXED-*)

## Architecture & Data

- `docs/ARCHITECTURE.md` — Components, data flow, and boundaries
- Source utils:
  - `dashboard/utils/data_loader.py`
  - `dashboard/utils/metrics.py`

## Agents (Multi-Agent Collaboration)

- `docs/agents/ONBOARDING.md` — 1-page quick start for agents
- `docs/agents/WAY-OF-WORKING.md` — Preambles, plans, approvals, memory
- `docs/agents/ROLES.md` — Responsibilities/allowed changes per role
- `docs/agents/DECISIONS.md` — Lightweight ADRs (durable choices)
- `docs/agents/AGENT_LOG.md` — High-level session summaries
- `docs/agents/PLAYBOOKS.md` — Recipes for common tasks
- `docs/agents/DATA_CONTRACTS.md` — Minimal schemas used by the UI
- `docs/agents/CONSTANTS.md` — Thresholds and where enforced
- `docs/agents/GLOSSARY.md` — Domain terms in plain language
- Templates: `docs/agents/templates/CHANGE_PROPOSAL.md`, `docs/agents/sessions/SESSION_TEMPLATE.md`

## Analysis & Strategy

- `analysis/floor-violation-patterns.md` — Historical consistency/risk analysis (if present)
- `CLAUDE.md` — Project context, goals, weekly plan anchors

## Training & Seasons

- Current season plan: `seasons/2026-spring-hm-sub2/plan.md`
- Weekly logs: `seasons/2026-spring-hm-sub2/weekly-logs/`
- Historical review: `seasons/2025-fall-chennai-hm/season-review.md`

## Tracking & Reports

- Weekly summaries: `tracking/weekly-summary-YYYY-MM-DD.md`
- Caches: `tracking/unified-cache.json` (primary), `tracking/garmin-cache.json`

## Resources & Templates

- Arm swing drills: `resources/arm-swing-drills-guide.md`
- Garmin watch settings: `resources/garmin-watch-settings-guide.md`
- Training plan (Excel): `resources/20_Week_Training_Plan.xlsx`
- Templates:
  - `templates/weekly-log-template.md`
  - `templates/daily-run-log-template.md`

## Notes

- Many documents contain repeated high-level context for convenience. Prefer linking instead of duplicating content when extending docs.
- All additions here are documentation-only and do not affect runtime.
