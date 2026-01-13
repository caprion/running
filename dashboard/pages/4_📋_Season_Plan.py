"""
Season Plan Viewer

Display the current season's training plan with all details.
"""

import streamlit as st
from pathlib import Path

# Page config
st.set_page_config(page_title="Season Plan", page_icon="📋", layout="wide")

st.title("📋 2026 Spring HM Sub-2:00 Campaign")
st.markdown("**Duration:** Jan 5 - May 24, 2026 (20 weeks)")

# Path to plan file
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
