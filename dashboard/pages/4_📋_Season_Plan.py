"""
Season Plan Viewer

Display the current season's training plan with all details.
"""

import streamlit as st
import os
from pathlib import Path

# Page config
st.set_page_config(page_title="Season Plan", page_icon="📋", layout="wide")

# Check if using sample data
USE_SAMPLE_DATA = os.getenv("USE_SAMPLE_DATA", "false").lower() == "true"

if USE_SAMPLE_DATA:
    st.title("📋 2025 Half Marathon Training Plan")
    st.markdown("**Duration:** Sub-2 Hour HM Campaign (Sample Data)")
    base_dir = Path(__file__).parent.parent.parent / "sample-data"
    plan_path = base_dir / "seasons" / "2025-sample-runner" / "plan.md"
else:
    st.title("📋 2026 Spring HM Sub-2:00 Campaign")
    st.markdown("**Duration:** Jan 5 - May 24, 2026 (20 weeks)")
    plan_path = Path(__file__).parent.parent.parent / "seasons" / "2026-spring-hm-sub2" / "plan.md"

try:
    if plan_path.exists():
        with open(plan_path, 'r', encoding='utf-8') as f:
            plan_content = f.read()

        # Display the markdown content
        st.markdown(plan_content)
    else:
        st.error(f"Plan file not found at: {plan_path}")
        st.info("Expected location: `seasons/2026-spring-hm-sub2/plan.md`")

except Exception as e:
    st.error(f"Error loading plan: {str(e)}")
    import traceback
    st.code(traceback.format_exc())
