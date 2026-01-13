# Agents Onboarding (1-page)

Purpose: Help any agent start quickly, safely, and consistently.

## Goals
- Keep the dashboard working at all times (no breaking changes)
- Prefer documentation-first changes; code only when explicitly requested
- Make decisions visible and easy to follow for the next agent

## 5 Rules
1. Non-destructive by default: add docs or new pages; don’t change existing behavior.
2. No new runtime dependencies without approval (ARM64 Windows constraints).
3. Use markdown tables (no `st.dataframe`/`st.table`).
4. Read data via utils: `dashboard/utils/data_loader.py`.
5. Record durable decisions in `docs/agents/DECISIONS.md` and add a one-liner to `AGENT_LOG.md`.

## Start Here (10 minutes)
1. Read: `AGENTS.md`, `docs/README.md`, `docs/ARCHITECTURE.md`.
2. Skim: `KNOWN-ISSUES.md`, `DASHBOARD-SUMMARY.md`.
3. If you will change anything, prepare a brief plan and (optionally) a `docs/agents/templates/CHANGE_PROPOSAL.md`.

## Safe Change Checklist
- [ ] I’m only adding docs or a new page, or I have explicit approval to modify code
- [ ] I won’t rename/move existing files
- [ ] No new dependencies
- [ ] I used Plotly + markdown tables
- [ ] I updated `AGENT_LOG.md` and, if needed, `DECISIONS.md`

## Common Tasks
- Weekly check-in: see `docs/agents/PLAYBOOKS.md`
- Add a page: see `AGENTS.md` → Add a New Page and `PLAYBOOKS.md`
- Debug cache errors: see `PLAYBOOKS.md` and `KNOWN-ISSUES.md`

## Where to Ask (in-repo)
- Quick questions: `docs/agents/AGENTS-FAQ.md`
- Decisions: `docs/agents/DECISIONS.md`
- Terms: `docs/agents/GLOSSARY.md`

