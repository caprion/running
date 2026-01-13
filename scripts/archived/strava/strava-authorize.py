#!/usr/bin/env python3
"""
Strava Authorization Helper
Generates the OAuth2 URL to authorize your app with correct scopes
"""

import os
from dotenv import load_dotenv

load_dotenv()

STRAVA_CLIENT_ID = os.getenv("STRAVA_CLIENT_ID")
STRAVA_CLIENT_SECRET = os.getenv("STRAVA_CLIENT_SECRET")

if not STRAVA_CLIENT_ID:
    print("❌ Error: STRAVA_CLIENT_ID not found in .env file")
    exit(1)

print("=" * 70)
print("🔐 STRAVA AUTHORIZATION HELPER")
print("=" * 70)
print()
print("You need to reauthorize your Strava app with the correct scopes.")
print()
print("Current scope: 'read' (only basic profile)")
print("Required scope: 'activity:read_all' (access to all activities)")
print()
print("=" * 70)
print("STEP 1: Open this URL in your browser")
print("=" * 70)
print()

print("First, what redirect URI did you configure in your Strava app?")
print("(Go to https://www.strava.com/settings/api to check)")
print()
print("Common options:")
print("  1. http://localhost")
print("  2. http://localhost:8000")
print("  3. Custom URL")
print()
redirect_uri = input("Redirect URI [default: http://localhost]: ").strip()
if not redirect_uri:
    redirect_uri = "http://localhost"

print()

# OAuth2 authorization URL with correct scopes
auth_url = (
    f"https://www.strava.com/oauth/authorize"
    f"?client_id={STRAVA_CLIENT_ID}"
    f"&redirect_uri={redirect_uri}"
    f"&response_type=code"
    f"&scope=activity:read_all,read"
)

print(auth_url)
print()
print("=" * 70)
print("STEP 2: Authorize the app")
print("=" * 70)
print()
print("⚠️  IMPORTANT: You DO NOT need a server running at localhost!")
print()
print("1. Click 'Authorize' to grant permissions")
print(f"2. Your browser will try to redirect to: {redirect_uri}/?state=&code=XXXXX")
print("   (The page won't load - that's OK!)")
print("3. Copy the 'code' parameter from the browser's address bar")
print("   Example: If URL is http://localhost/?state=&code=abc123xyz")
print("            Copy: abc123xyz")
print()
print("=" * 70)
print("STEP 3: Paste the authorization code here")
print("=" * 70)
print()

auth_code = input("Authorization code: ").strip()

if not auth_code:
    print("❌ No code provided. Exiting.")
    exit(1)

print()
print("🔐 Exchanging authorization code for tokens...")
print()

# Exchange code for tokens
import requests

response = requests.post(
    "https://www.strava.com/oauth/token",
    data={
        "client_id": STRAVA_CLIENT_ID,
        "client_secret": STRAVA_CLIENT_SECRET,
        "code": auth_code,
        "grant_type": "authorization_code"
    }
)

if response.status_code != 200:
    print(f"❌ Token exchange failed: {response.status_code}")
    print(f"   Response: {response.text}")
    exit(1)

token_data = response.json()

print("✅ Authorization successful!")
print()
print("=" * 70)
print("STEP 4: Update your .env file with these new tokens")
print("=" * 70)
print()
print("Add these lines to your .env file:")
print()
print(f"STRAVA_CLIENT_ID={STRAVA_CLIENT_ID}")
print(f"STRAVA_CLIENT_SECRET={STRAVA_CLIENT_SECRET}")
print(f"STRAVA_REFRESH_TOKEN={token_data['refresh_token']}")
print()
print("=" * 70)
print("Token Details")
print("=" * 70)
print(f"Access Token: {token_data['access_token']}")
print(f"Refresh Token: {token_data['refresh_token']}")
print(f"Expires At: {token_data['expires_at']}")
print(f"Scope: {token_data.get('scope', 'N/A')}")
print()
print("✅ Your app now has permission to read activities!")
print("   Run: python scripts/sync-strava.py --days 30")
print()
