# Documentation Index

This repository already has rich documentation. This index groups what exists so you can find the right guide fast.

## Getting Started

- `QUICK-START.md` — One-page quick start for syncing and running the dashboard
- `README.md` — Current season dashboard status and links
- `dashboard/README.md` — Launching and using the Streamlit dashboard

## Workflows

- `WORKFLOW.md` — Daily, weekly check-in, and gait analysis workflows
- `SESSION-SUMMARY.md` — Consolidated session summary and pointers

## Data Sync & Integrations

- `scripts/README.md` — Garmin sync setup and usage
- `STRAVA-SETUP.md` — Strava integration notes
- Scripts:
  - `scripts/sync-garmin.py`
  - `scripts/sync-strava.py`
  - `scripts/sync-all.py`
  - `scripts/weekly-summary.py`
  - `scripts/import-session.py`

## Dashboard

- `DASHBOARD-SUMMARY.md` — Dashboard features and usage
- `KNOWN-ISSUES.md` — Active issues and tracker
- Fix logs:
  - `FIXED-PYARROW-ISSUE.md`
  - `FINAL-FIX-PYARROW.md`
  - `FIXED-CACHE-ISSUE.md`
  - `BUGFIX-2026-01-09.md`

## Architecture & Data

- `docs/ARCHITECTURE.md` — Components, data flow, and boundaries
- Source utils:
  - `dashboard/utils/data_loader.py`
  - `dashboard/utils/metrics.py`

## Agents (Multi-Agent Collaboration)

- `AGENTS.md` — Top-level guide, safety rails, conventions
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

- `analysis/floor-violation-patterns.md` — Historical consistency/risk analysis
- `CLAUDE.md` — Project context, goals, weekly plan anchors

## Training & Seasons

- Current season plan: `seasons/2026-spring-hm-sub2/plan.md`
- Weekly logs: `seasons/2026-spring-hm-sub2/weekly-logs/`
- Historical review: `seasons/2025-fall-chennai-hm/season-review.md`

## Tracking & Reports

- Weekly summaries: `tracking/weekly-summary-YYYY-MM-DD.md`
- Caches: `tracking/garmin-cache.json`, `tracking/strava-cache.json`

## Resources & Templates

- Arm swing drills: `resources/arm-swing-drills-guide.md`
- Training plan (Excel): `resources/20_Week_Training_Plan.xlsx`
- Templates:
  - `templates/weekly-log-template.md`
  - `templates/daily-run-log-template.md`

## Utilities

- Launchers: `RUN-DASHBOARD.bat`, `CLEAR-CACHE.bat`
- Status: `UPDATES.md`, `sync_output.txt`

Notes
- Many documents contain repeated high-level context for convenience. Prefer linking instead of duplicating content when extending docs.
- All additions here are documentation-only and do not affect runtime.
