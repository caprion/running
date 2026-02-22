#!/usr/bin/env python3
"""
Download FIT file for a specific Garmin activity.

Usage:
    python scripts/download-fit.py <activity_id>
    python scripts/download-fit.py 21933316016

Reuses garth session from scripts/.garth/
Saves to tracking/fit_files/<activity_id>.fit
"""

import io
import os
import sys
import zipfile
from pathlib import Path

from dotenv import load_dotenv

try:
    import garth
    from garminconnect import Garmin
except ImportError:
    print("Error: garminconnect/garth not installed")
    print("Run: pip install garminconnect garth")
    sys.exit(1)

load_dotenv()

SESSION_DIR = Path(__file__).parent / ".garth"
FIT_DIR = Path(__file__).parent.parent / "tracking" / "fit_files"


def get_client() -> Garmin:
    """Authenticate with Garmin, trying saved session first, then credentials."""
    # Try garth session
    if SESSION_DIR.exists() and list(SESSION_DIR.glob("*")):
        try:
            garth.resume(str(SESSION_DIR))
            client = Garmin()
            client.get_full_name()
            print("Authenticated via saved session")
            return client
        except Exception:
            print("Saved session expired, trying credentials...")

    # Fall back to credentials
    email = os.getenv("GARMIN_EMAIL")
    password = os.getenv("GARMIN_PASSWORD")
    if not email or not password:
        print("No valid session and no credentials in .env")
        sys.exit(1)

    client = Garmin(email, password)
    client.login()
    SESSION_DIR.mkdir(exist_ok=True)
    garth.save(str(SESSION_DIR))
    print(f"Authenticated as {email}, session saved")
    return client


def download_fit(activity_id: int) -> Path:
    """Download FIT file for a given activity ID."""
    FIT_DIR.mkdir(parents=True, exist_ok=True)
    
    output_path = FIT_DIR / f"{activity_id}.fit"
    if output_path.exists():
        print(f"Already exists: {output_path}")
        return output_path

    client = get_client()

    # Download
    print(f"Downloading FIT for activity {activity_id}...")
    fit_data = client.download_activity(
        activity_id,
        dl_fmt=Garmin.ActivityDownloadFormat.ORIGINAL
    )

    # Extract from ZIP
    zip_buffer = io.BytesIO(fit_data)
    with zipfile.ZipFile(zip_buffer, 'r') as zf:
        fit_filename = [n for n in zf.namelist() if n.endswith('.fit')][0]
        fit_content = zf.read(fit_filename)

    with open(output_path, 'wb') as f:
        f.write(fit_content)

    print(f"Saved: {output_path} ({len(fit_content)} bytes)")
    return output_path


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/download-fit.py <activity_id>")
        sys.exit(1)

    activity_id = int(sys.argv[1])
    download_fit(activity_id)
