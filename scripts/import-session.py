#!/usr/bin/env python3
"""
Manual Garmin Session Import
Allows you to paste session cookies from your browser instead of using email/password
"""

import json
from pathlib import Path

SESSION_FILE = Path(__file__).parent / ".garmin_session.json"


def import_oauth_tokens():
    """Import OAuth1 and OAuth2 tokens manually"""
    print("=" * 60)
    print("GARMIN SESSION IMPORT (Manual Cookie Method)")
    print("=" * 60)
    print()
    print("You'll need to extract these values from your browser after")
    print("logging into Garmin Connect (https://connect.garmin.com)")
    print()
    print("How to find these:")
    print("1. Login to Garmin Connect in your browser")
    print("2. Open DevTools (F12)")
    print("3. Go to Application/Storage > Cookies > connect.garmin.com")
    print("4. Look for these cookies:")
    print("   - OAuth_token")
    print("   - OAuth_token_secret")
    print()
    print("=" * 60)
    print()

    # Get OAuth1 tokens
    oauth1_token = input("Paste OAuth_token: ").strip()
    oauth1_secret = input("Paste OAuth_token_secret: ").strip()

    if not oauth1_token or not oauth1_secret:
        print("\n❌ Error: Both tokens are required")
        return False

    # Create session data structure
    session_data = {
        "oauth1_token": oauth1_token,
        "oauth1_token_secret": oauth1_secret
    }

    # Ask for OAuth2 tokens (optional, but recommended)
    print("\nOptional: OAuth2 tokens (improves compatibility)")
    print("Look for: oauth_consumer")
    oauth2 = input("Paste oauth_consumer (or press Enter to skip): ").strip()

    if oauth2:
        session_data["oauth_consumer"] = oauth2

    # Save session file
    try:
        with open(SESSION_FILE, 'w') as f:
            json.dump(session_data, f, indent=2)

        print(f"\n✅ Session saved to: {SESSION_FILE}")
        print("You can now run sync-garmin.py without needing email/password!")
        return True

    except Exception as e:
        print(f"\n❌ Error saving session: {e}")
        return False


def import_full_session_json():
    """Import complete session JSON (advanced users)"""
    print("=" * 60)
    print("GARMIN SESSION IMPORT (Full JSON Method)")
    print("=" * 60)
    print()
    print("If you have the complete session data from garminconnect library,")
    print("you can paste the entire JSON object here.")
    print()
    print("Paste your session JSON (Ctrl+Z then Enter when done on Windows):")
    print()

    # Read multiline input
    lines = []
    try:
        while True:
            line = input()
            lines.append(line)
    except EOFError:
        pass

    session_json = '\n'.join(lines).strip()

    if not session_json:
        print("\n❌ Error: No session data provided")
        return False

    try:
        # Parse and validate JSON
        session_data = json.loads(session_json)

        # Save session file
        with open(SESSION_FILE, 'w') as f:
            json.dump(session_data, f, indent=2)

        print(f"\n✅ Session saved to: {SESSION_FILE}")
        print("You can now run sync-garmin.py!")
        return True

    except json.JSONDecodeError as e:
        print(f"\n❌ Error: Invalid JSON - {e}")
        return False
    except Exception as e:
        print(f"\n❌ Error saving session: {e}")
        return False


def import_cookie_header():
    """Import from cookie header string (easiest method!)"""
    print("=" * 60)
    print("GARMIN SESSION IMPORT (Cookie Header Method)")
    print("=" * 60)
    print()
    print("This is the EASIEST method!")
    print()
    print("How to get your cookie header:")
    print("1. Login to Garmin Connect (https://connect.garmin.com)")
    print("2. Open DevTools (F12)")
    print("3. Go to Network tab")
    print("4. Refresh the page")
    print("5. Click any request to connect.garmin.com")
    print("6. Find 'Request Headers' section")
    print("7. Copy the entire 'Cookie:' value")
    print()
    print("=" * 60)
    print()

    cookie_header = input("Paste your cookie header string: ").strip()

    if not cookie_header:
        print("\n❌ Error: No cookie data provided")
        return False

    # Parse cookie string
    try:
        cookies = {}
        for cookie in cookie_header.split(';'):
            cookie = cookie.strip()
            if '=' in cookie:
                key, value = cookie.split('=', 1)
                cookies[key.strip()] = value.strip()

        # Build session data from cookies
        session_data = {}

        # Look for important cookies
        important_cookies = [
            'session',
            'JWT_WEB',
            'SESSIONID',
            'GARMIN-SSO-CUST-GUID',
            'OAuth_token',
            'OAuth_token_secret',
            'oauth_consumer'
        ]

        found_cookies = []
        for key in important_cookies:
            if key in cookies:
                session_data[key] = cookies[key]
                found_cookies.append(key)

        if not session_data:
            print("\n❌ Error: No valid Garmin session cookies found")
            print("   Make sure you copied the cookie header from connect.garmin.com")
            return False

        print(f"\n✅ Found {len(found_cookies)} session cookies:")
        for cookie in found_cookies:
            print(f"   - {cookie}")

        # Save session file
        with open(SESSION_FILE, 'w') as f:
            json.dump(session_data, f, indent=2)

        print(f"\n💾 Session saved to: {SESSION_FILE}")
        print("You can now run sync-garmin.py!")
        return True

    except Exception as e:
        print(f"\n❌ Error parsing cookies: {e}")
        return False


def main():
    """Main menu"""
    print("\nChoose import method:")
    print("1. Cookie header string (EASIEST - just copy/paste entire cookie)")
    print("2. Individual OAuth cookies")
    print("3. Full session JSON (advanced)")
    print()

    choice = input("Enter choice (1, 2, or 3): ").strip()

    if choice == "1":
        import_cookie_header()
    elif choice == "2":
        import_oauth_tokens()
    elif choice == "3":
        import_full_session_json()
    else:
        print("Invalid choice")


if __name__ == "__main__":
    main()
