#!/usr/bin/env python3
"""Quick script to check cadence across recent runs."""

import json
from pathlib import Path

# Load unified cache
cache_path = Path(__file__).parent.parent / "tracking" / "unified-cache.json"
with open(cache_path, 'r') as f:
    data = json.load(f)

activities = data.get('activities', [])

# Filter runs and get cadence data
runs = []
for a in activities:
    if a.get('type') == 'Run':
        date = a.get('start_date', '')[:10]
        cadence = a.get('average_cadence', 0)
        if cadence:
            # Strava stores cadence as steps per foot, multiply by 2 for SPM
            cadence = cadence * 2
        runs.append({
            'date': date,
            'name': a.get('name', ''),
            'distance': a.get('distance', 0) / 1000,
            'cadence': cadence,
            'pace_mps': a.get('average_speed', 0)
        })

# Sort by date
runs.sort(key=lambda x: x['date'], reverse=True)

print('Recent runs with cadence (spm = steps per minute):')
print('-' * 85)
print(f'{"Date":<12} {"Name":<40} {"Dist":>6} {"Cadence":>10}')
print('-' * 85)

for r in runs[:20]:
    cadence_str = f"{r['cadence']:.0f} spm" if r['cadence'] else "N/A"
    print(f"{r['date']:<12} {r['name'][:39]:<40} {r['distance']:>5.1f}km {cadence_str:>10}")

# Calculate averages
runs_with_cadence = [r for r in runs if r['cadence'] > 0]
if runs_with_cadence:
    print('\n' + '-' * 85)
    print('CADENCE ANALYSIS:')
    print('-' * 85)
    
    # Find Feb 1 run
    feb1_runs = [r for r in runs_with_cadence if r['date'] == '2026-02-01']
    other_runs = [r for r in runs_with_cadence if r['date'] != '2026-02-01']
    
    if feb1_runs:
        feb1_cadence = feb1_runs[0]['cadence']
        print(f"\nFeb 1, 2026 cadence: {feb1_cadence:.0f} spm")
        
        if other_runs:
            avg_other = sum(r['cadence'] for r in other_runs) / len(other_runs)
            diff = feb1_cadence - avg_other
            pct = (diff / avg_other) * 100
            print(f"Average cadence (other runs): {avg_other:.0f} spm")
            print(f"Difference: {diff:+.0f} spm ({pct:+.1f}%)")
            
            # Recent trend
            print(f"\nRecent 10 runs cadence trend:")
            for r in runs_with_cadence[:10]:
                bar = '█' * int(r['cadence'] / 5)
                print(f"  {r['date']}: {r['cadence']:3.0f} spm {bar}")
