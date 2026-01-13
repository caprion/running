# Agents FAQ

Quick answers to recurring questions agents have while working in this repo.

## What can I change without asking?
- Documentation (Markdown) anywhere, including adding new docs and indexes.
- New Streamlit pages in `dashboard/pages/` that don’t alter existing behavior.

## What must I NOT change unless explicitly asked?
- Existing page behavior, filenames, or structure.
- Thresholds (15/20km floors), risk-month logic, or business rules.
- Introduce new runtime deps (e.g., `pyarrow`).

## How do I show tables without pyarrow?
- Use `st.markdown` with pipe tables. Do not use `st.dataframe` or `st.table`.

## Why avoid heavy caching?
- Streamlit + pandas datetime pickling can error. If caching, prefer `@st.cache_data(ttl=300)` and keep objects simple.

## Where do I read data from?
- Use helpers in `dashboard/utils/data_loader.py`, e.g., `activities_to_dataframe()`, `get_weekly_summary()`.

## How do I add a new page?
- Create `dashboard/pages/N_Name.py` (N = order). Import from `dashboard/utils`. Use Plotly charts and markdown tables.

## Where is the overall architecture explained?
- See `docs/ARCHITECTURE.md` and the index at `docs/README.md`.

## Where do decisions live?
- `docs/agents/DECISIONS.md` (lightweight ADRs). Add a one-liner to `docs/agents/AGENT_LOG.md` when you add a decision.

