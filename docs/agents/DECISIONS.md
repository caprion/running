# Decisions (Lightweight ADRs)

Format: Context → Decision → Rationale → Impact → Revisit When

## ADR-0001: Use markdown tables instead of Streamlit dataframes
- Context: ARM64 Windows lacks `pyarrow`; Streamlit 1.52+ requires pyarrow for tables.
- Decision: Render all tables via `st.markdown` pipe tables.
- Rationale: Avoid dependency issues; guaranteed portability.
- Impact: Slightly more verbose code when rendering tables.
- Revisit When: If/when `pyarrow` becomes available/stable in target env.

## ADR-0002: Keep weekly floor thresholds at 15km (general) and 20km (Apr–May firewall)
- Context: Business rules drive consistency and risk mitigation.
- Decision: Do not change thresholds without explicit instruction.
- Rationale: Preserves analytical consistency and season goals.
- Impact: All analyses/alerts remain aligned to current expectations.
- Revisit When: Season goals/strategy change.

## ADR-0003: Avoid heavy cache pickling of datetimes
- Context: Streamlit cache + pandas datetimes caused pickling errors.
- Decision: If caching, use `@st.cache_data(ttl=300)`; keep objects simple or avoid caching for critical paths.
- Rationale: Reliability in ARM64 Windows environment.
- Impact: Slightly more compute; fewer cache-related failures.
- Revisit When: Streamlit/pandas handling improves.

