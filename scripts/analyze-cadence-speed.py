#!/usr/bin/env python3
"""Analyze cadence vs speed to determine if cadence improvement is real."""

import json
from pathlib import Path

cache_path = Path(__file__).parent.parent / "tracking" / "unified-cache.json"
with open(cache_path) as f:
    d = json.load(f)

runs = [a for a in d['activities'] 
        if 'running' in str(a.get('type','')).lower() 
        and a.get('avg_cadence') 
        and a.get('date','') >= '2026-01']

print('CADENCE vs SPEED ANALYSIS (Jan-Feb 2026)')
print('=' * 85)
print(f"{'Date':<12} {'Name':<28} {'Pace':>7} {'Cadence':>9} {'Stride':>9}")
print('-' * 85)

results = []
for a in runs:
    date = a.get('date','')[:10]
    name = a.get('name','')[:27]
    
    dist = a.get('distance_km', 0) * 1000
    dur = a.get('duration_seconds', 1)
    speed_ms = dist / dur if dur else 0
    
    if speed_ms <= 0:
        continue
    
    pace_sec = 1000 / speed_ms
    pace_min = int(pace_sec // 60)
    pace_s = int(pace_sec % 60)
    pace_str = f'{pace_min}:{pace_s:02d}'
    
    cadence = a.get('avg_cadence', 0)
    
    splits = a.get('splits', {}).get('lapDTOs', [])
    if splits:
        strides = [s.get('strideLength', 0) for s in splits if s.get('strideLength')]
        stride_cm = sum(strides) / len(strides) if strides else 0
    else:
        stride_cm = 0
    
    results.append({
        'date': date,
        'name': name,
        'pace': pace_str,
        'pace_sec': pace_sec,
        'speed': speed_ms,
        'cadence': cadence,
        'stride_cm': stride_cm
    })
    
    stride_str = f'{stride_cm:.0f} cm' if stride_cm else 'N/A'
    print(f"{date:<12} {name:<28} {pace_str:>7} {cadence:>7.0f}spm {stride_str:>8}")

print()
print('=' * 85)
print('ANALYSIS: Is Feb 1 cadence improvement real or just due to faster pace?')
print('=' * 85)

# Find Feb 1 run
feb1_runs = [r for r in results if r['date'] == '2026-02-01']
if not feb1_runs:
    print("No Feb 1 run found")
    exit()

feb1 = feb1_runs[0]

# Find runs at similar pace (within 20 seconds of Feb 1's pace)
similar_pace = [r for r in results 
                if r['date'] != '2026-02-01' 
                and abs(r['pace_sec'] - feb1['pace_sec']) < 20]

print()
print(f"Feb 1 run: {feb1['pace']} pace, {feb1['cadence']:.0f} spm, {feb1['stride_cm']:.0f} cm stride")
print()
print(f"Runs at SIMILAR pace (within 20 sec of {feb1['pace']}):")

for r in sorted(similar_pace, key=lambda x: x['date']):
    print(f"  {r['date']}: {r['pace']} pace, {r['cadence']:.0f} spm, {r['stride_cm']:.0f} cm stride")

if similar_pace:
    avg_cad = sum(r['cadence'] for r in similar_pace) / len(similar_pace)
    avg_stride = sum(r['stride_cm'] for r in similar_pace) / len(similar_pace)
    print()
    print(f"Average at similar pace: {avg_cad:.0f} spm, {avg_stride:.0f} cm stride")
    print(f"Feb 1 difference:        {feb1['cadence'] - avg_cad:+.0f} spm, {feb1['stride_cm'] - avg_stride:+.0f} cm stride")
    
    print()
    print('=' * 85)
    print('INTERPRETATION:')
    print('=' * 85)
    
    cad_diff = feb1['cadence'] - avg_cad
    stride_diff = feb1['stride_cm'] - avg_stride
    
    if cad_diff > 2:
        print(f"✅ CADENCE: +{cad_diff:.0f} spm at same pace = REAL improvement (not just speed)")
    elif cad_diff < -2:
        print(f"⚠️  CADENCE: {cad_diff:.0f} spm at same pace = Lower than usual")
    else:
        print(f"➡️  CADENCE: Similar to other runs at this pace")
    
    if stride_diff > 2:
        print(f"✅ STRIDE: +{stride_diff:.0f} cm = Longer stride (more power per step)")
    elif stride_diff < -2:
        print(f"⚠️  STRIDE: {stride_diff:.0f} cm = Shorter stride (more turnover)")
    else:
        print(f"➡️  STRIDE: Similar to other runs at this pace")
    
    print()
    print("Speed = Cadence × Stride Length")
    print("Higher cadence + similar stride = more efficient running")
    print("Higher cadence + shorter stride = same speed, just quicker turnover")
