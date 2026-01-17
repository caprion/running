"""
Weekly Logs Viewer

Browse and view weekly training logs for the current season.
"""

import streamlit as st
import os
from pathlib import Path
import re

# Page config
st.set_page_config(page_title="Weekly Logs", page_icon="📝", layout="wide")

st.title("📝 Weekly Training Logs")
st.markdown("Review detailed logs for each week of training")

# Check if using sample data
USE_SAMPLE_DATA = os.getenv("USE_SAMPLE_DATA", "false").lower() == "true"

if USE_SAMPLE_DATA:
    # Use sample data path
    base_dir = Path(__file__).parent.parent.parent / "sample-data"
    logs_dir = base_dir / "seasons" / "2025-sample-runner"
else:
    # Use personal data path
    logs_dir = Path(__file__).parent.parent.parent / "seasons" / "2026-spring-hm-sub2" / "weekly-logs"

try:
    if not logs_dir.exists():
        st.error(f"Weekly logs directory not found at: {logs_dir}")
        if USE_SAMPLE_DATA:
            st.info("Expected location: `sample-data/seasons/2025-sample-runner/`")
        else:
            st.info("Expected location: `seasons/2026-spring-hm-sub2/weekly-logs/`")
        st.stop()

    # Get all weekly log files (different patterns for sample vs personal)
    if USE_SAMPLE_DATA:
        log_files = sorted(logs_dir.glob("weekly-log-*.md"))
    else:
        log_files = sorted(logs_dir.glob("week-*.md"))

    if not log_files:
        st.warning("No weekly log files found yet.")
        st.info("Weekly logs will appear here as you document your training.")
        st.stop()

    # Extract week numbers/dates and create display names
    week_options = []
    for log_file in log_files:
        if USE_SAMPLE_DATA:
            # Sample data format: weekly-log-YYYY-MM-DD.md
            match = re.search(r'weekly-log-(\d{4}-\d{2}-\d{2})', log_file.name)
            if match:
                date_str = match.group(1)
                week_options.append((f"Week of {date_str}", log_file))
        else:
            # Personal data format: week-N.md
            match = re.search(r'week-(\d+)', log_file.name)
            if match:
                week_num = int(match.group(1))
                week_options.append((f"Week {week_num}", log_file))

    # Sidebar - week selection
    st.sidebar.header("Select Week")
    selected_week = st.sidebar.selectbox(
        "Week",
        options=[opt[0] for opt in week_options],
        index=len(week_options) - 1  # Default to most recent week
    )

    # Find the selected log file
    selected_file = None
    for display_name, file_path in week_options:
        if display_name == selected_week:
            selected_file = file_path
            break

    if selected_file:
        # Display the log content
        with open(selected_file, 'r', encoding='utf-8') as f:
            log_content = f.read()

        st.markdown(log_content)

        # Show file info
        st.markdown("---")
        st.caption(f"📄 File: `{selected_file.relative_to(logs_dir.parent.parent.parent)}`")
    else:
        st.error("Could not load selected week.")

except Exception as e:
    st.error(f"Error loading weekly logs: {str(e)}")
    import traceback
    st.code(traceback.format_exc())
