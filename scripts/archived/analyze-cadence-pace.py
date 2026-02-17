#!/usr/bin/env python3
"""
Analyze cadence vs pace relationship from lap data
"""

import json
import pandas as pd
from pathlib import Path

# Load data
data_file = Path(__file__).parent.parent / "tracking" / "unified-cache.json"
data = json.load(open(data_file))

# Extract lap data with cadence and pace
laps = []
for act in data['activities']:
    if act.get('type') != 'running':
        continue
    splits = act.get('splits', {})
    lap_list = splits.get('lapDTOs', []) if isinstance(splits, dict) else []
    
    for lap in lap_list:
        cadence = lap.get('averageRunCadence')
        speed = lap.get('averageSpeed', 0)  # m/s
        distance = lap.get('distance', 0)
        stride = lap.get('strideLength')
        
        if cadence and speed and distance >= 800:  # Only full-ish km laps
            pace_min_km = (1000 / speed) / 60 if speed > 0 else 0
            laps.append({
                'date': act['date'][:10],
                'cadence': cadence,
                'pace_min_km': pace_min_km,
                'speed_ms': speed,
                'stride_cm': stride if stride else None
            })

df = pd.DataFrame(laps)
print(f"Total laps with cadence data: {len(df)}")
print(f"Date range: {df['date'].min()} to {df['date'].max()}")
print(f"\nPace range: {df['pace_min_km'].min():.2f} to {df['pace_min_km'].max():.2f} min/km")
print(f"Cadence range: {df['cadence'].min():.0f} to {df['cadence'].max():.0f} spm")

# Define pace brackets
def pace_bracket(pace):
    if pace < 5.0:
        return "1. Fast (<5:00)"
    elif pace < 5.5:
        return "2. Tempo (5:00-5:30)"
    elif pace < 6.0:
        return "3. Moderate (5:30-6:00)"
    elif pace < 6.5:
        return "4. Easy (6:00-6:30)"
    elif pace < 7.0:
        return "5. Recovery (6:30-7:00)"
    else:
        return "6. Very Easy (>7:00)"

df['pace_bracket'] = df['pace_min_km'].apply(pace_bracket)

# Analyze by pace bracket
print("\n" + "="*60)
print("CADENCE BY PACE BRACKET")
print("="*60)
bracket_stats = df.groupby('pace_bracket').agg({
    'cadence': ['mean', 'std', 'count'],
    'pace_min_km': 'mean'
}).round(1)
bracket_stats.columns = ['Avg Cadence', 'Std Dev', 'Laps', 'Avg Pace']
print(bracket_stats.to_string())

# Calculate correlation
correlation = df['pace_min_km'].corr(df['cadence'])
print(f"\n\nCorrelation (pace vs cadence): {correlation:.3f}")
print("  (Negative = cadence increases as pace gets faster, which is expected)")

# Cadence change per min/km pace change
from scipy import stats
slope, intercept, r_value, p_value, std_err = stats.linregress(df['pace_min_km'], df['cadence'])
print(f"\nRegression: Cadence = {slope:.1f} × Pace + {intercept:.1f}")
print(f"  → For every 1 min/km slower, cadence changes by {slope:.1f} spm")
print(f"  → R² = {r_value**2:.3f}")

# Recent trend (last 30 days)
recent = df[df['date'] >= '2025-12-30']
print(f"\n" + "="*60)
print(f"RECENT DATA (since Dec 30, 2025): {len(recent)} laps")
print("="*60)
if len(recent) > 0:
    recent_stats = recent.groupby('pace_bracket').agg({
        'cadence': ['mean', 'count']
    }).round(1)
    recent_stats.columns = ['Avg Cadence', 'Laps']
    print(recent_stats.to_string())

# Stride length analysis (if available)
stride_df = df[df['stride_cm'].notna()]
if len(stride_df) > 10:
    print(f"\n" + "="*60)
    print(f"STRIDE LENGTH ANALYSIS ({len(stride_df)} laps with stride data)")
    print("="*60)
    stride_stats = stride_df.groupby('pace_bracket').agg({
        'stride_cm': ['mean', 'count'],
        'cadence': 'mean'
    }).round(1)
    stride_stats.columns = ['Avg Stride (cm)', 'Laps', 'Avg Cadence']
    print(stride_stats.to_string())
    
    # How stride and cadence contribute to speed
    stride_df['calc_speed'] = (stride_df['stride_cm']/100) * (stride_df['cadence']/60) * 2  # m/s
    print(f"\nSpeed contribution analysis:")
    print(f"  Stride range: {stride_df['stride_cm'].min():.0f} - {stride_df['stride_cm'].max():.0f} cm")
    print(f"  Cadence range: {stride_df['cadence'].min():.0f} - {stride_df['cadence'].max():.0f} spm")
