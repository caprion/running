# Session Note

- Date/time: 2026-01-09
- Agent/task: Repo documentation scaffold + Race Confidence fixes
- Context: Multi-agent repo; ARM64 Windows (no pyarrow); Streamlit dashboard with Garmin + Strava caches. Race Confidence page had incorrect pace conversion and filtering; docs needed multi-agent structure.

## Plan
- Add agents docs (onboarding, roles, way-of-working, decisions, playbooks, data contracts) without touching runtime.
- Fix Race Confidence issues (pace conversion, robust date filtering, tolerance control), keep pyarrow out.
- Add debug expanders for transparency (HR stability, fatigue inputs).

## Files read
- README.md, WORKFLOW.md, QUICK-START.md, DASHBOARD-SUMMARY.md, KNOWN-ISSUES.md
- dashboard/app.py, dashboard/pages/*, dashboard/utils/data_loader.py, dashboard/utils/metrics.py
- tracking/garmin-cache.json, tracking/strava-cache.json

## Files changed
- AGENTS.md (new)
- docs/README.md (new + updated later to add Agents section)
- docs/ARCHITECTURE.md (new)
- docs/agents/ONBOARDING.md (new)
- docs/agents/ROLES.md (new)
- docs/agents/WAY-OF-WORKING.md (new)
- docs/agents/DECISIONS.md (new)
- docs/agents/PLAYBOOKS.md (new)
- docs/agents/DATA_CONTRACTS.md (new)
- docs/agents/CONSTANTS.md (new)
- docs/agents/GLOSSARY.md (new)
- docs/agents/AGENT_LOG.md (new)
- docs/agents/sessions/SESSION_TEMPLATE.md (new)
- dashboard/utils/metrics.py (fix pace conversion m/s → s/km)
- dashboard/pages/3_🏁_Race_Confidence.py (robust datetime filtering; pace tolerance slider; pyarrow-safe debug; faster segment uses tolerance; HR/fatigue debug expanders)

## Decisions
- Use markdown tables and avoid pyarrow (reinforced in DECISIONS.md) — ARM64 constraint.
- Add Pace Tolerance (± sec) control to capture real-world lap variance.
- Filter by parsed datetimes for both DataFrame and dict activities to avoid string-compare issues.

## Outcomes
- Race readiness now recognizes segments at target pace; faster check uses same tolerance.
- HR Stability and Pace Degradation have debug panels and avoid pyarrow.
- Clear multi-agent guides in docs/agents/* with index and architecture.

## Open questions
- Do we want to add a “Race pace segments by activity” expander to show per-run km at target pace ± tolerance?
- Should HR stability fallback compare halves when <4 laps are present?
- Merge audit: explicitly guarantee Garmin splits win on duplicates (logic prefers Garmin, but add a verification step?).

## Next steps / TODO
- [ ] Verify Jan 4 HM and Dec 7 runs appear in Pace Degradation debug list with analysis window ≥12 weeks.
- [ ] If missing: deeper Garmin backfill (`python scripts/sync-garmin.py 90`) and recheck.
- [ ] Optionally add “race pace segments by activity” expander for transparency.
- [ ] If requested, relax HR stability to halves when laps <4.

