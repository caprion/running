# Agent Roles & Boundaries

Clear responsibilities so multiple agents can collaborate without friction.

## Docs Agent
- Allowed: Any Markdown docs; indexes; architecture notes; templates
- Not allowed: Code changes, thresholds/business rules changes

## Dashboard Agent
- Allowed: New pages under `dashboard/pages/`; copy updates; Plotly charts; markdown tables
- Not allowed: Change existing page behavior or thresholds; add dependencies
- Use: `utils` loaders (`activities_to_dataframe`, `get_weekly_summary`)

## Data Agent (Utils)
- Allowed: New pure helper functions in `dashboard/utils/metrics.py` and `data_loader.py`
- Not allowed: Breaking schemas/behavior; renaming/removing fields used by pages
- Guidance: Keep functions pure, inputs/outputs explicit; document in `docs/agents/DATA_CONTRACTS.md`

## Scripts Agent
- Allowed: Minor improvements to `scripts/` (auth UX, error handling) that don’t change cache schema
- Not allowed: Breaking output shape of `tracking/*.json`
- Note: If schema must change, propose ADR first (`DECISIONS.md`) and update `DATA_CONTRACTS.md`

## Reviewer Agent
- Responsibilities: Validate changes, run dashboard locally, check docs for clarity
- Artifacts: Update `AGENT_LOG.md`; add/adjust ADRs as needed

