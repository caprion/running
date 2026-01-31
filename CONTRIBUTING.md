# Contributing to Running Training Tracker

Thank you for your interest in contributing! This project is a personal training system that has grown into a reusable tool. Contributions that improve documentation, fix bugs, or add features that benefit other runners are welcome.

## How to Contribute

### Reporting Issues

- **Bug reports:** Include steps to reproduce, expected vs actual behavior, and your environment (OS, Python version).
- **Feature requests:** Describe the use case and how it would help your training workflow.

### Pull Requests

1. **Fork and clone** the repository
2. **Create a branch** for your change: `git checkout -b fix/your-fix` or `feature/your-feature`
3. **Make your changes** following existing code style
4. **Test** that the dashboard and sync scripts still work
5. **Submit a PR** with a clear description of what changed and why

### Development Setup

```bash
# Clone and install
git clone <repo-url>
cd running
pip install -r scripts/requirements.txt
pip install -r requirements-dashboard.txt

# Use sample data (no Garmin account needed)
export USE_SAMPLE_DATA=true   # Linux/Mac
$env:USE_SAMPLE_DATA='true'   # Windows PowerShell

# Run dashboard
streamlit run dashboard/app.py
```

### Code Style

- **Python:** Follow PEP 8. Use type hints where helpful.
- **Docs:** Markdown for documentation. Keep README sections concise.
- **Scripts:** Add docstrings to new functions. Update `scripts/README.md` for new scripts.

### Project Structure

- `scripts/` — Sync, export, and utility scripts
- `dashboard/` — Streamlit app and pages
- `docs/` — Architecture and guides
- `sample-data/` — Synthetic data for demos

### Areas That Need Help

- **Documentation:** Improving guides, adding examples, fixing broken links
- **Testing:** Unit tests for metrics, data loading, sync logic
- **Accessibility:** Dashboard improvements for screen readers
- **Platform support:** Windows/Linux/Mac compatibility fixes

### Questions?

Open an issue with the "question" label. For architecture decisions, see `docs/ARCHITECTURE.md` and `docs/agents/DECISIONS.md`.
