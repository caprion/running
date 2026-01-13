#!/usr/bin/env python3
"""Test the merge logic for Garmin sync"""

import json
from pathlib import Path

# Load current cache
CACHE_FILE = Path(__file__).parent.parent / "tracking" / "garmin-cache.json"
with open(CACHE_FILE, 'r', encoding='utf-8') as f:
    cache_data = json.load(f)

print(f"Current cache: {len(cache_data['activities'])} activities")
print(f"Activity IDs: {[a['id'] for a in cache_data['activities']]}")

# Simulate the merge logic
def merge_activities(existing_data, new_activities):
    """Merge new activities with existing ones, avoiding duplicates"""
    existing = existing_data.get('activities', [])
    existing_ids = {a['id'] for a in existing}

    # Add new activities that don't exist yet
    added = 0
    for new_act in new_activities:
        if new_act['id'] not in existing_ids:
            existing.append(new_act)
            added += 1

    # Sort by date (newest first)
    existing.sort(key=lambda x: x['date'], reverse=True)

    print(f"Merged: {added} new activities added, {len(new_activities) - added} already existed")
    return existing

# Test 1: Add a duplicate activity (should not be added)
print("\n--- Test 1: Add duplicate activity ---")
duplicate = cache_data['activities'][0].copy()
result1 = merge_activities(cache_data.copy(), [duplicate])
print(f"Result: {len(result1)} activities (expected: 3)")
assert len(result1) == 3, "Duplicate was added!"

# Test 2: Add a new activity (should be added)
print("\n--- Test 2: Add new activity ---")
new_activity = {
    'id': 999999999,
    'name': 'Test Run',
    'date': '2026-01-12 06:00:00',
    'distance_km': 5.0
}
cache_copy = cache_data.copy()
result2 = merge_activities(cache_copy, [new_activity])
print(f"Result: {len(result2)} activities (expected: 4)")
assert len(result2) == 4, "New activity was not added!"
assert result2[0]['id'] == 999999999, "New activity not at the top (newest first)!"

# Test 3: Add mix of new and duplicate (should add only new)
print("\n--- Test 3: Add mix of new and duplicate ---")
new_activity2 = {
    'id': 888888888,
    'name': 'Test Run 2',
    'date': '2026-01-11 06:00:00',
    'distance_km': 6.0
}
cache_copy = cache_data.copy()
result3 = merge_activities(cache_copy, [duplicate, new_activity, new_activity2])
print(f"Result: {len(result3)} activities (expected: 5)")
assert len(result3) == 5, "Expected 5 activities after merge!"

print("\n✅ All merge tests passed!")
print("\nThe merge logic is working correctly:")
print("- Duplicates are skipped")
print("- New activities are added")
print("- Activities are sorted by date (newest first)")
