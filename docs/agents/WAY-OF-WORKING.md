# Way of Working (Multi-Agent)

Consistent collaboration process so outcomes are predictable and easy to review.

## Session Flow
1. Read context (see Onboarding)
2. Draft a short plan (5–7 steps max)
3. Announce your next action (1–2 sentences)
4. Make minimal changes (docs-first)
5. Validate (open dashboard if applicable)
6. Summarize and record memory (session note or AGENT_LOG line)

## Preambles
- Before running commands/changes, write a short preamble: what you’re about to do and why

## Plans
- Keep a small step list; update statuses as you go
- Avoid filler steps; only include the meaningful ones

## File References & Output Style
- Use inline code for paths (e.g., `dashboard/app.py:42`)
- Keep summaries short, scannable, and link to files

## Approvals
- Ask before: adding dependencies, deleting/renaming files, network operations, or destructive actions
- Prefer alternatives that don’t need escalation

## Memory & Decisions
- Durable decisions → `docs/agents/DECISIONS.md` + one line in `AGENT_LOG.md`
- Per-session notes (optional) → `docs/agents/sessions/`

