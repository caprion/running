#!/usr/bin/env python3
"""
Weekly Training Summary Generator
Reads garmin-cache.json and generates a markdown summary for weekly reflections
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List


CACHE_FILE = Path(__file__).parent.parent / "tracking" / "garmin-cache.json"


def load_cache() -> Dict:
    """Load Garmin cache data"""
    with open(CACHE_FILE, 'r') as f:
        return json.load(f)


def format_duration(seconds: float) -> str:
    """Convert seconds to HH:MM:SS"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def analyze_activities(activities: List[Dict]) -> Dict:
    """Analyze running activities"""
    if not activities:
        return {
            'count': 0,
            'total_distance': 0,
            'total_time': 0,
            'avg_pace': None,
            'runs': []
        }

    total_distance = sum(a['distance_km'] for a in activities)
    total_time = sum(a['duration_seconds'] for a in activities)
    avg_pace_sec_per_km = (total_time / total_distance) if total_distance > 0 else 0

    runs = []
    for activity in activities:
        # Calculate HR zone distribution
        hr_zones = activity.get('hr_zones', [])
        total_hr_time = sum(z['secsInZone'] for z in hr_zones)

        zone_distribution = {}
        if total_hr_time > 0:
            for zone in hr_zones:
                zone_num = zone['zoneNumber']
                pct = (zone['secsInZone'] / total_hr_time) * 100
                if pct > 5:  # Only show zones >5%
                    zone_distribution[f"Z{zone_num}"] = round(pct)

        runs.append({
            'date': activity['date'],
            'name': activity['name'],
            'distance': activity['distance_km'],
            'duration': format_duration(activity['duration_seconds']),
            'pace': activity['avg_pace_min_km'],
            'avg_hr': activity.get('avg_hr'),
            'max_hr': activity.get('max_hr'),
            'elevation': activity.get('elevation_gain_m'),
            'cadence': activity.get('splits', {}).get('lapDTOs', [{}])[0].get('averageRunCadence'),
            'hr_zones': zone_distribution
        })

    return {
        'count': len(activities),
        'total_distance': round(total_distance, 1),
        'total_time': format_duration(total_time),
        'avg_pace': f"{int(avg_pace_sec_per_km // 60)}:{int(avg_pace_sec_per_km % 60):02d}",
        'runs': runs
    }


def analyze_sleep(sleep_data: List[Dict]) -> Dict:
    """Analyze sleep patterns"""
    if not sleep_data:
        return {}

    avg_sleep = sum(s['sleep_hours'] for s in sleep_data) / len(sleep_data)
    nights_under_6h = sum(1 for s in sleep_data if s['sleep_hours'] < 6.0)

    # Calculate deep sleep percentage (should be 13-23%)
    deep_sleep_pct = []
    for night in sleep_data:
        if night['sleep_seconds'] and night['deep_sleep_seconds']:
            pct = (night['deep_sleep_seconds'] / night['sleep_seconds']) * 100
            deep_sleep_pct.append(pct)

    avg_deep_pct = sum(deep_sleep_pct) / len(deep_sleep_pct) if deep_sleep_pct else None

    return {
        'nights': len(sleep_data),
        'avg_hours': round(avg_sleep, 1),
        'nights_under_6h': nights_under_6h,
        'avg_deep_pct': round(avg_deep_pct, 1) if avg_deep_pct else None,
        'details': sleep_data
    }


def get_flags(activities: List[Dict], sleep_data: List[Dict], training_status: Dict) -> List[str]:
    """Generate warning flags based on contingency rules"""
    flags = []

    # Sleep <6h warnings
    for sleep in sleep_data:
        if sleep['sleep_hours'] < 6.0:
            flags.append(f"⚠️  **Sleep Alert**: {sleep['date']} only {sleep['sleep_hours']}h - consider converting next quality run to easy")

    # Training status warnings
    status = training_status.get('training_effect_label', '')
    if status == 'Unproductive':
        flags.append(f"⚠️  **Training Status**: {status} - high load without fitness gain. Consider recovery week.")
    elif status == 'Overreaching':
        flags.append(f"⚠️  **Training Status**: {status} - risk of overtraining. Reduce volume/intensity.")

    # High training load
    load_7d = training_status.get('training_load_7d')
    if load_7d and load_7d > 600:
        flags.append(f"⚠️  **High Training Load**: {load_7d} (7-day avg) - monitor fatigue and recovery")

    # Resting HR warnings (key recovery indicator)
    resting_hr = training_status.get('resting_hr')
    resting_hr_7d = training_status.get('resting_hr_7d_avg')
    if resting_hr and resting_hr_7d:
        diff = resting_hr - resting_hr_7d
        if diff > 5:
            flags.append(f"🚨 **Resting HR Alert**: {resting_hr} bpm (7-day avg: {resting_hr_7d}) - Elevated by {diff} bpm. Possible illness, overtraining, or stress. Consider rest day.")
        elif diff > 2:
            flags.append(f"⚠️  **Resting HR Caution**: {resting_hr} bpm (7-day avg: {resting_hr_7d}) - Slightly elevated. Monitor recovery and consider easy training.")

    # HR zone distribution for long runs (>15km should be mostly Z2-Z3)
    for activity in activities:
        if activity['distance_km'] > 15:
            hr_zones = activity.get('hr_zones', [])
            total_hr_time = sum(z['secsInZone'] for z in hr_zones)
            if total_hr_time > 0:
                z4_z5_time = sum(z['secsInZone'] for z in hr_zones if z['zoneNumber'] >= 4)
                z4_z5_pct = (z4_z5_time / total_hr_time) * 100
                if z4_z5_pct > 50:
                    flags.append(f"⚠️  **Long Run Pacing**: {activity['name']} was {round(z4_z5_pct)}% Z4-Z5. Long runs should be mostly easy (Z2-Z3)")

    return flags


def generate_summary(data: Dict) -> str:
    """Generate markdown summary"""
    last_sync = datetime.fromisoformat(data['last_sync']).strftime('%Y-%m-%d %H:%M')

    activities_summary = analyze_activities(data['activities'])
    sleep_summary = analyze_sleep(data['sleep'])
    training_status = data['training_status']
    flags = get_flags(data['activities'], data['sleep'], training_status)

    # Build markdown
    md = f"""# Weekly Training Summary
**Sync Date:** {last_sync}

---

## 📊 Running Summary

**Weekly Totals:**
- **Runs:** {activities_summary['count']}
- **Distance:** {activities_summary['total_distance']} km
- **Time:** {activities_summary['total_time']}
- **Avg Pace:** {activities_summary['avg_pace']}/km

### Individual Runs
"""

    for run in activities_summary['runs']:
        md += f"\n**{run['date']} - {run['name']}**\n"
        md += f"- Distance: {run['distance']} km | Duration: {run['duration']} | Pace: {run['pace']}/km\n"
        if run['avg_hr']:
            md += f"- HR: Avg {run['avg_hr']}, Max {run['max_hr']}"
            if run['hr_zones']:
                zones_str = ", ".join([f"{k}: {v}%" for k, v in run['hr_zones'].items()])
                md += f" ({zones_str})"
            md += "\n"
        if run['elevation']:
            md += f"- Elevation: {round(run['elevation'])}m gain\n"
        if run['cadence']:
            md += f"- Cadence: {round(run['cadence'])} spm\n"

    # Training metrics
    md += f"""
---

## 🎯 Training Metrics

**Current Fitness:**
- **VO2max:** {training_status.get('vo2max', 'N/A')}
- **Training Load (7d):** {training_status.get('training_load_7d', 'N/A')}
- **Training Status:** {training_status.get('training_effect_label', 'N/A')}
"""

    if training_status.get('recovery_time_hours'):
        md += f"- **Recovery Time:** {training_status['recovery_time_hours']}h\n"

    # Resting HR - Enhanced analysis
    resting_hr = training_status.get('resting_hr')
    resting_hr_7d = training_status.get('resting_hr_7d_avg')
    if resting_hr or resting_hr_7d:
        md += f"\n**Resting Heart Rate (Recovery Indicator):**\n"
        if resting_hr:
            md += f"- **Current:** {resting_hr} bpm"
            if resting_hr_7d:
                diff = resting_hr - resting_hr_7d
                if diff < -2:
                    trend = " ⬇️ **Improving recovery**"
                    status = "excellent"
                elif diff > 5:
                    trend = " ⬆️⬆️ **Significant elevation - possible fatigue/illness**"
                    status = "warning"
                elif diff > 2:
                    trend = " ⬆️ **Slightly elevated - monitor fatigue**"
                    status = "caution"
                elif diff < 0:
                    trend = " ⬇️ Recovering well"
                    status = "good"
                else:
                    trend = " ↔️ Stable"
                    status = "normal"

                md += f" (7-day avg: {resting_hr_7d} bpm{trend})\n"
                md += f"- **Interpretation:** "

                if status == "excellent":
                    md += "Your body is recovering well. Good time for quality training.\n"
                elif status == "good":
                    md += "Recovery is on track. Continue with planned training.\n"
                elif status == "normal":
                    md += "Stable HR indicates good adaptation to training load.\n"
                elif status == "caution":
                    md += "Slightly elevated - consider if you're stressed, dehydrated, or not sleeping well.\n"
                elif status == "warning":
                    md += "Elevated RHR suggests significant fatigue or possible illness. Consider easy day or rest.\n"
            else:
                md += "\n"

    # Sleep
    md += f"""
---

## 😴 Sleep Analysis

**Weekly Sleep:**
- **Avg Sleep:** {sleep_summary.get('avg_hours', 'N/A')}h/night ({sleep_summary.get('nights', 0)} nights tracked)
"""

    if sleep_summary.get('nights_under_6h', 0) > 0:
        md += f"- **⚠️  Nights <6h:** {sleep_summary['nights_under_6h']}\n"

    if sleep_summary.get('avg_deep_pct'):
        status = "✅ Good" if 13 <= sleep_summary['avg_deep_pct'] <= 23 else "⚠️  Low" if sleep_summary['avg_deep_pct'] < 13 else "⚠️  High"
        md += f"- **Deep Sleep:** {sleep_summary['avg_deep_pct']}% ({status}, target: 13-23%)\n"

    md += "\n**Nightly Details:**\n"
    for night in sleep_summary.get('details', [])[:7]:
        md += f"- {night['date']}: {night['sleep_hours']}h"
        if night['sleep_hours'] < 6.0:
            md += " ⚠️"
        md += "\n"

    # Flags and warnings
    if flags:
        md += "\n---\n\n## 🚩 Flags & Warnings\n\n"
        for flag in flags:
            md += f"{flag}\n\n"

    # Footer
    md += f"""---

## 📝 Notes

*Add your subjective notes here:*
- Energy levels:
- Niggles/soreness:
- Life stress:
- Next week focus:

---

*Generated by weekly-summary.py on {datetime.now().strftime('%Y-%m-%d %H:%M')}*
"""

    return md


def main():
    """Main entry point"""
    print("=" * 60)
    print("WEEKLY TRAINING SUMMARY")
    print("=" * 60)

    data = load_cache()
    summary = generate_summary(data)

    # Print to console (handle encoding for Windows)
    try:
        print(summary)
    except UnicodeEncodeError:
        # Fallback for Windows console
        print(summary.encode('ascii', 'replace').decode('ascii'))

    # Optionally save to file
    output_file = Path(__file__).parent.parent / "tracking" / f"weekly-summary-{datetime.now().strftime('%Y-%m-%d')}.md"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(summary)

    print("\n" + "=" * 60)
    print(f"✅ Summary saved to: {output_file}")
    print("=" * 60)


if __name__ == "__main__":
    main()
