#!/usr/bin/env python3
"""
Capture a screenshot of the dashboard for README/GitHub preview.

Requires: pip install playwright && playwright install chromium

Usage:
    python scripts/capture-dashboard-screenshot.py

Output:
    media/dashboard-snapshots/dashboard-preview.png
"""

import sys
from pathlib import Path

# Resolve paths
script_dir = Path(__file__).parent
project_root = script_dir.parent
index_html = project_root / "media" / "dashboard-snapshots" / "index.html"
output_path = project_root / "media" / "dashboard-snapshots" / "dashboard-preview.png"


def main():
    if not index_html.exists():
        print("Error: index.html not found. Run export-dashboards-html.py first.")
        sys.exit(1)

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Playwright not installed. Run:")
        print("  pip install playwright")
        print("  playwright install chromium")
        sys.exit(1)

    # Use file:// URL for local HTML
    file_url = index_html.as_uri()

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1200, "height": 800})
        page.goto(file_url, wait_until="networkidle")
        page.wait_for_timeout(500)  # Let charts render
        output_path.parent.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(output_path), full_page=True)
        browser.close()

    print(f"Screenshot saved: {output_path}")


if __name__ == "__main__":
    main()
