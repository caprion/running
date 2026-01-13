#!/usr/bin/env python3
"""
FIT File Parser for Running Data

Extracts detailed workout data from Garmin FIT files.
Useful for weekly check-in analysis and performance tracking.

Usage:
    python parse-fit.py <path-to-fit-file>
    python parse-fit.py <path-to-fit-file> --json
    python parse-fit.py <path-to-fit-file> --markdown
"""

import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

try:
    from fitparse import FitFile
except ImportError:
    print("Error: fitparse not installed. Run: pip install fitparse")
    sys.exit(1)


def parse_fit_file(filepath: str) -> dict:
    """Parse a FIT file and extract workout data."""
    fit = FitFile(filepath)
    
    data = {
        "file": Path(filepath).name,
        "session": {},
        "heart_rate": {
            "data_points": [],
            "avg": None,
            "max": None,
            "min": None,
        },
        "pace": {
            "avg_per_km": None,
            "best_per_km": None,
        },
        "laps": [],
        "summary": {},
    }
    
    # Extract session data
    for record in fit.get_messages("session"):
        for field in record.fields:
            if field.value is not None:
                if field.name == "timestamp":
                    data["session"]["end_time"] = str(field.value)
                elif field.name == "start_time":
                    data["session"]["start_time"] = str(field.value)
                elif field.name == "total_elapsed_time":
                    data["session"]["duration_seconds"] = field.value
                elif field.name == "total_distance":
                    data["session"]["distance_meters"] = field.value
                elif field.name == "total_calories":
                    data["session"]["calories"] = field.value
                elif field.name == "avg_heart_rate":
                    data["heart_rate"]["avg"] = field.value
                elif field.name == "max_heart_rate":
                    data["heart_rate"]["max"] = field.value
                elif field.name == "avg_running_cadence":
                    data["session"]["avg_cadence"] = field.value
                elif field.name == "total_ascent":
                    data["session"]["elevation_gain"] = field.value
                elif field.name == "total_descent":
                    data["session"]["elevation_loss"] = field.value
                elif field.name == "enhanced_avg_speed":
                    data["session"]["avg_speed_mps"] = field.value
                elif field.name == "enhanced_max_speed":
                    data["session"]["max_speed_mps"] = field.value
                elif field.name == "sport":
                    data["session"]["sport"] = str(field.value)
                elif field.name == "total_training_effect":
                    data["session"]["training_effect_aerobic"] = field.value
                elif field.name == "total_anaerobic_training_effect":
                    data["session"]["training_effect_anaerobic"] = field.value
    
    # Extract HR data points for HRV calculation
    hr_data = []
    for record in fit.get_messages("record"):
        hr = None
        for field in record.fields:
            if field.name == "heart_rate" and field.value:
                hr = field.value
        if hr:
            hr_data.append(hr)
    
    if hr_data:
        data["heart_rate"]["data_points"] = hr_data
        data["heart_rate"]["min"] = min(hr_data)
        if not data["heart_rate"]["avg"]:
            data["heart_rate"]["avg"] = round(sum(hr_data) / len(hr_data), 1)
        if not data["heart_rate"]["max"]:
            data["heart_rate"]["max"] = max(hr_data)
    
    # Calculate pace metrics
    if data["session"].get("avg_speed_mps") and data["session"]["avg_speed_mps"] > 0:
        # Convert m/s to min/km
        avg_pace_sec_per_km = 1000 / data["session"]["avg_speed_mps"]
        data["pace"]["avg_per_km"] = format_pace(avg_pace_sec_per_km)
        data["pace"]["avg_seconds_per_km"] = avg_pace_sec_per_km
    
    if data["session"].get("max_speed_mps") and data["session"]["max_speed_mps"] > 0:
        best_pace_sec_per_km = 1000 / data["session"]["max_speed_mps"]
        data["pace"]["best_per_km"] = format_pace(best_pace_sec_per_km)
    
    # Build summary
    data["summary"] = build_summary(data)
    
    return data


def format_pace(seconds_per_km: float) -> str:
    """Format pace as M:SS/km."""
    minutes = int(seconds_per_km // 60)
    seconds = int(seconds_per_km % 60)
    return f"{minutes}:{seconds:02d}/km"


def format_duration(seconds: float) -> str:
    """Format duration as HH:MM:SS."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def build_summary(data: dict) -> dict:
    """Build a human-readable summary."""
    summary = {}
    
    session = data.get("session", {})
    
    if session.get("distance_meters"):
        summary["distance_km"] = round(session["distance_meters"] / 1000, 2)
    
    if session.get("duration_seconds"):
        summary["duration"] = format_duration(session["duration_seconds"])
    
    if data["pace"].get("avg_per_km"):
        summary["avg_pace"] = data["pace"]["avg_per_km"]
    
    if data["heart_rate"].get("avg"):
        summary["avg_hr"] = data["heart_rate"]["avg"]
    
    if data["heart_rate"].get("max"):
        summary["max_hr"] = data["heart_rate"]["max"]
    
    if session.get("elevation_gain"):
        summary["elevation_gain_m"] = session["elevation_gain"]
    
    if session.get("avg_cadence"):
        summary["avg_cadence_spm"] = session["avg_cadence"] * 2  # Convert to steps/min
    
    if session.get("training_effect_aerobic"):
        summary["training_effect"] = session["training_effect_aerobic"]
    
    return summary


def output_json(data: dict) -> str:
    """Output data as JSON."""
    # Remove raw HR data points for cleaner output
    output = data.copy()
    output["heart_rate"] = {k: v for k, v in data["heart_rate"].items() 
                           if k != "data_points"}
    output["heart_rate"]["total_samples"] = len(data["heart_rate"]["data_points"])
    return json.dumps(output, indent=2, default=str)


def output_markdown(data: dict) -> str:
    """Output data as Markdown for weekly log."""
    lines = []
    summary = data.get("summary", {})
    session = data.get("session", {})
    
    # Header
    start_time = session.get("start_time", "Unknown")
    if start_time and start_time != "Unknown":
        try:
            dt = datetime.fromisoformat(str(start_time).replace(" ", "T"))
            date_str = dt.strftime("%Y-%m-%d")
            lines.append(f"## Run: {date_str}")
        except:
            lines.append(f"## Run: {data.get('file', 'Unknown')}")
    else:
        lines.append(f"## Run: {data.get('file', 'Unknown')}")
    
    lines.append("")
    
    # Main metrics table
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    
    if summary.get("distance_km"):
        lines.append(f"| **Distance** | {summary['distance_km']} km |")
    
    if summary.get("duration"):
        lines.append(f"| **Duration** | {summary['duration']} |")
    
    if summary.get("avg_pace"):
        lines.append(f"| **Avg Pace** | {summary['avg_pace']} |")
    
    if summary.get("avg_hr"):
        lines.append(f"| **Avg HR** | {summary['avg_hr']} bpm |")
    
    if summary.get("max_hr"):
        lines.append(f"| **Max HR** | {summary['max_hr']} bpm |")
    
    if summary.get("elevation_gain_m"):
        lines.append(f"| **Elevation Gain** | {summary['elevation_gain_m']} m |")
    
    if summary.get("avg_cadence_spm"):
        lines.append(f"| **Avg Cadence** | {summary['avg_cadence_spm']} spm |")
    
    if summary.get("training_effect"):
        lines.append(f"| **Training Effect** | {summary['training_effect']} |")

    return "\n".join(lines)


def output_text(data: dict) -> str:
    """Output data as plain text."""
    lines = []
    summary = data.get("summary", {})

    lines.append("=" * 50)
    lines.append(f"FIT File Analysis: {data.get('file', 'Unknown')}")
    lines.append("=" * 50)
    lines.append("")

    lines.append("WORKOUT SUMMARY")
    lines.append("-" * 30)
    for key, value in summary.items():
        lines.append(f"  {key.replace('_', ' ').title()}: {value}")

    lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Parse FIT files for running data and HRV metrics"
    )
    parser.add_argument("file", help="Path to FIT file")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--markdown", "-md", action="store_true", 
                       help="Output as Markdown for weekly log")
    
    args = parser.parse_args()
    
    if not Path(args.file).exists():
        print(f"Error: File not found: {args.file}")
        sys.exit(1)
    
    try:
        data = parse_fit_file(args.file)
        
        if args.json:
            print(output_json(data))
        elif args.markdown:
            print(output_markdown(data))
        else:
            print(output_text(data))
            
    except Exception as e:
        print(f"Error parsing FIT file: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
