#!/usr/bin/env python3
"""
Generate static HTML dashboards from sample data for GitHub demonstrations.

Creates standalone HTML files for each dashboard page that can be viewed
directly in a browser without running Streamlit.

Usage:
    python scripts/export-dashboards-html.py
    
Output:
    media/dashboard-snapshots/*.html
"""

import os
import sys
from pathlib import Path
import json

# Set environment to use sample data
os.environ['USE_SAMPLE_DATA'] = 'true'

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dashboard.utils.data_loader import load_activities, load_garmin_data
from dashboard.utils.metrics import (
    get_status, calculate_streak, get_pace_in_seconds, seconds_to_pace,
    calculate_pace_degradation
)
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta


def create_consistency_page():
    """Generate Consistency Guardian dashboard"""
    print("  Generating Consistency page...")
    
    activities = load_activities()
    df = pd.DataFrame(activities)
    df['date'] = pd.to_datetime(df['date'])
    df['week'] = df['date'].dt.to_period('W').apply(lambda r: r.start_time)
    
    # Weekly aggregation
    weekly = df.groupby('week').agg({
        'distance_km': 'sum',
        'date': 'count'
    }).rename(columns={'date': 'runs'})
    weekly = weekly.reset_index()
    weekly['week_str'] = weekly['week'].dt.strftime('%Y-%m-%d')
    
    # Add status
    weekly['status'] = weekly['distance_km'].apply(
        lambda x: 'GREEN' if x >= 20 else 'YELLOW' if x >= 15 else 'RED'
    )
    weekly['color'] = weekly['status'].map({
        'GREEN': '#00ff00',
        'YELLOW': '#ffff00',
        'RED': '#ff6b6b'
    })
    
    # Create weekly bar chart
    fig1 = go.Figure()
    fig1.add_trace(go.Bar(
        x=weekly['week_str'],
        y=weekly['distance_km'],
        marker_color=weekly['color'],
        text=[f"{d:.1f}km" for d in weekly['distance_km']],
        textposition='outside',
        hovertemplate='<b>Week %{x}</b><br>Distance: %{y:.1f} km<br>Status: %{customdata}<extra></extra>',
        customdata=weekly['status']
    ))
    
    fig1.add_hline(y=20, line_dash="dash", line_color="green", 
                   annotation_text="GREEN (≥20km)")
    fig1.add_hline(y=15, line_dash="dash", line_color="orange",
                   annotation_text="YELLOW (15-20km)")
    
    fig1.update_layout(
        title="Weekly Running Volume - Last 52 Weeks",
        xaxis_title="Week",
        yaxis_title="Distance (km)",
        height=500,
        showlegend=False,
        hovermode='x unified'
    )
    
    # Create status pie chart
    status_counts = weekly['status'].value_counts()
    fig2 = go.Figure(data=[go.Pie(
        labels=status_counts.index,
        values=status_counts.values,
        marker_colors=['#00ff00', '#ffff00', '#ff6b6b'],
        hole=0.3
    )])
    
    fig2.update_layout(
        title="Weekly Status Distribution",
        height=400
    )
    
    # Combine both charts
    from plotly.subplots import make_subplots
    combined_fig = make_subplots(
        rows=2, cols=1,
        row_heights=[0.65, 0.35],
        subplot_titles=("Weekly Running Volume", "Status Distribution"),
        specs=[[{"type": "bar"}], [{"type": "pie"}]]
    )
    
    combined_fig.add_trace(
        go.Bar(x=weekly['week_str'], y=weekly['distance_km'], 
               marker_color=weekly['color'],
               showlegend=False),
        row=1, col=1
    )
    
    combined_fig.add_trace(
        go.Pie(labels=status_counts.index, values=status_counts.values,
               marker_colors=['#00ff00', '#ffff00', '#ff6b6b']),
        row=2, col=1
    )
    
    # Add horizontal lines manually as shapes
    combined_fig.add_shape(
        type="line",
        x0=0, x1=1, xref="x domain",
        y0=20, y1=20, yref="y",
        line=dict(color="green", width=2, dash="dash"),
        row=1, col=1
    )
    combined_fig.add_shape(
        type="line",
        x0=0, x1=1, xref="x domain",
        y0=15, y1=15, yref="y",
        line=dict(color="orange", width=2, dash="dash"),
        row=1, col=1
    )
    
    combined_fig.update_layout(
        title_text="📊 Consistency Guardian - Weekly Status & Distribution",
        height=800,
        showlegend=False
    )
    
    combined_fig.update_yaxes(title_text="Distance (km)", row=1, col=1)
    combined_fig.update_xaxes(title_text="Week", row=1, col=1)
    
    return combined_fig


def create_training_load_page():
    """Generate Training Load dashboard"""
    print("  Generating Training Load page...")
    
    activities = load_activities()
    garmin_data = load_garmin_data()
    sleep_data = garmin_data.get('sleep', [])
    
    # Sleep chart (last 14 days)
    sleep_df = pd.DataFrame(sleep_data[-14:])
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=sleep_df['date'],
        y=sleep_df['sleep_hours'],
        marker_color='steelblue',
        name='Sleep Hours'
    ))
    
    fig.add_hline(y=7, line_dash="dash", line_color="green",
                  annotation_text="Target: 7h")
    
    fig.update_layout(
        title="Sleep Duration - Last 14 Days",
        xaxis_title="Date",
        yaxis_title="Hours",
        height=400
    )
    
    # HR zones from recent activities
    df = pd.DataFrame(activities[-20:])  # Last 20 activities
    
    hr_data = []
    for _, activity in df.iterrows():
        if 'splits' in activity and 'lapDTOs' in activity['splits']:
            for lap in activity['splits']['lapDTOs']:
                if 'averageHR' in lap and 'averageSpeed' in lap:
                    pace = 1000 / (lap['averageSpeed'] * 60)  # min/km
                    hr_data.append({
                        'pace': pace,
                        'hr': lap['averageHR'],
                        'date': activity['date']
                    })
    
    hr_df = pd.DataFrame(hr_data)
    
    fig2 = px.scatter(
        hr_df,
        x='pace',
        y='hr',
        color='hr',
        title='Heart Rate vs Pace',
        labels={'pace': 'Pace (min/km)', 'hr': 'Heart Rate (bpm)'},
        color_continuous_scale='Reds',
        height=400
    )
    
    # Combine charts
    from plotly.subplots import make_subplots
    combined = make_subplots(
        rows=2, cols=1,
        subplot_titles=("Sleep Duration (14 days)", "Heart Rate vs Pace (Recent)"),
        row_heights=[0.5, 0.5]
    )
    
    combined.add_trace(
        go.Bar(x=sleep_df['date'], y=sleep_df['sleep_hours'],
               marker_color='steelblue', showlegend=False),
        row=1, col=1
    )
    
    combined.add_trace(
        go.Scatter(x=hr_df['pace'], y=hr_df['hr'],
                   mode='markers',
                   marker=dict(color=hr_df['hr'], colorscale='Reds'),
                   showlegend=False),
        row=2, col=1
    )
    
    combined.add_hline(y=7, line_dash="dash", line_color="green", row=1, col=1)
    
    combined.update_layout(
        title_text="📈 Training Load - Sleep & Heart Rate Analysis",
        height=800
    )
    
    combined.update_xaxes(title_text="Date", row=1, col=1)
    combined.update_xaxes(title_text="Pace (min/km)", row=2, col=1)
    combined.update_yaxes(title_text="Hours", row=1, col=1)
    combined.update_yaxes(title_text="Heart Rate (bpm)", row=2, col=1)
    
    return combined


def create_form_page():
    """Generate Form Analysis dashboard"""
    print("  Generating Form page...")
    
    activities = load_activities()
    df = pd.DataFrame(activities)
    df['date'] = pd.to_datetime(df['date'])
    
    # Filter last 30 days
    recent_df = df[df['date'] > (df['date'].max() - timedelta(days=30))]
    
    fig = px.scatter(
        recent_df,
        x='avg_cadence',
        y='distance_km',
        color='avg_pace_min_km',
        size='distance_km',
        title='Cadence vs Distance (Last 30 Days)',
        labels={
            'avg_cadence': 'Cadence (spm)',
            'distance_km': 'Distance (km)',
            'avg_pace_min_km': 'Pace'
        },
        height=500
    )
    
    # Target cadence range
    fig.add_vrect(x0=160, x1=170, fillcolor="green", opacity=0.1,
                  annotation_text="Target Zone", annotation_position="top left")
    
    fig.update_layout(
        title_text="👟 Form Analysis - Cadence Distribution"
    )
    
    return fig


def create_race_confidence_page():
    """Generate Race Confidence dashboard"""
    print("  Generating Race Confidence page...")
    
    activities = load_activities()
    
    # Calculate pace degradation for long runs
    long_runs = [a for a in activities if a['distance_km'] >= 15][-10:]  # Last 10 long runs
    
    degradation_data = []
    for activity in long_runs:
        if 'splits' in activity and 'lapDTOs' in activity['splits']:
            laps = activity['splits']['lapDTOs']
            if len(laps) >= 8:
                # First 25% vs last 25%
                first_quarter = laps[:len(laps)//4]
                last_quarter = laps[-len(laps)//4:]
                
                if first_quarter and last_quarter:
                    first_pace = sum(l['averageSpeed'] for l in first_quarter) / len(first_quarter)
                    last_pace = sum(l['averageSpeed'] for l in last_quarter) / len(last_quarter)
                    
                    degradation = ((first_pace - last_pace) / first_pace) * 100
                    
                    degradation_data.append({
                        'date': activity['date'],
                        'distance': activity['distance_km'],
                        'degradation': degradation
                    })
    
    deg_df = pd.DataFrame(degradation_data)
    
    fig = go.Figure()
    
    colors = ['green' if d < 5 else 'orange' if d < 10 else 'red' 
              for d in deg_df['degradation']]
    
    fig.add_trace(go.Bar(
        x=deg_df['date'],
        y=deg_df['degradation'],
        marker_color=colors,
        text=[f"{d:.1f}%" for d in deg_df['degradation']],
        textposition='outside'
    ))
    
    fig.add_hline(y=5, line_dash="dash", line_color="green",
                  annotation_text="Good (<5%)")
    fig.add_hline(y=10, line_dash="dash", line_color="orange",
                  annotation_text="Acceptable (5-10%)")
    
    fig.update_layout(
        title="🏁 Race Confidence - Pace Degradation on Long Runs",
        xaxis_title="Date",
        yaxis_title="Pace Degradation (%)",
        height=500,
        showlegend=False
    )
    
    return fig


def create_recovery_page():
    """Generate Recovery dashboard"""
    print("  Generating Recovery page...")
    
    garmin_data = load_garmin_data()
    sleep_data = garmin_data.get('sleep', [])
    
    # Last 30 days of sleep
    sleep_df = pd.DataFrame(sleep_data[-30:])
    
    # Convert seconds to hours for sleep stages
    sleep_df['deep_hours'] = sleep_df['deep_sleep_seconds'] / 3600
    sleep_df['light_hours'] = sleep_df['light_sleep_seconds'] / 3600
    sleep_df['rem_hours'] = sleep_df['rem_sleep_seconds'] / 3600
    sleep_df['awake_hours'] = sleep_df['awake_seconds'] / 3600
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=sleep_df['date'],
        y=sleep_df['deep_hours'],
        stackgroup='one',
        name='Deep Sleep',
        fillcolor='darkblue'
    ))
    
    fig.add_trace(go.Scatter(
        x=sleep_df['date'],
        y=sleep_df['light_hours'],
        stackgroup='one',
        name='Light Sleep',
        fillcolor='lightblue'
    ))
    
    fig.add_trace(go.Scatter(
        x=sleep_df['date'],
        y=sleep_df['rem_hours'],
        stackgroup='one',
        name='REM Sleep',
        fillcolor='purple'
    ))
    
    fig.add_trace(go.Scatter(
        x=sleep_df['date'],
        y=sleep_df['awake_hours'],
        stackgroup='one',
        name='Awake',
        fillcolor='lightgray'
    ))
    
    fig.update_layout(
        title="💤 Recovery - Sleep Stages (Last 30 Days)",
        xaxis_title="Date",
        yaxis_title="Hours",
        height=500,
        hovermode='x unified'
    )
    
    return fig


def create_overview_page():
    """Generate overview/summary page"""
    print("  Generating Overview page...")
    
    activities = load_activities()
    garmin_data = load_garmin_data()
    training_status = garmin_data.get('training_status', {})
    
    df = pd.DataFrame(activities)
    df['date'] = pd.to_datetime(df['date'])
    
    # Last 12 weeks volume
    df['week'] = df['date'].dt.to_period('W').apply(lambda r: r.start_time)
    weekly = df.groupby('week')['distance_km'].sum().reset_index()
    weekly = weekly.tail(12)
    weekly['week_str'] = weekly['week'].dt.strftime('%Y-%m-%d')
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=weekly['week_str'],
        y=weekly['distance_km'],
        marker_color='steelblue',
        text=[f"{d:.0f}km" for d in weekly['distance_km']],
        textposition='outside'
    ))
    
    fig.update_layout(
        title=f"📊 Training Overview - Last 12 Weeks<br><sub>VO2max: {training_status.get('vo2max', 'N/A')} | Resting HR: {training_status.get('resting_hr', 'N/A')} bpm | Training Load (7d): {training_status.get('training_load_7d', 'N/A')}</sub>",
        xaxis_title="Week",
        yaxis_title="Distance (km)",
        height=500
    )
    
    return fig


def main():
    """Generate all HTML dashboards"""
    print("🎨 Generating static HTML dashboards from sample data...")
    print(f"📊 Using sample data for demonstrations\n")
    
    # Create output directory
    output_dir = Path(__file__).parent.parent / "media" / "dashboard-snapshots"
    output_dir.mkdir(exist_ok=True, parents=True)
    
    # Generate each dashboard
    dashboards = {
        'overview': ('Overview', create_overview_page),
        'consistency': ('Consistency Guardian', create_consistency_page),
        'training-load': ('Training Load', create_training_load_page),
        'form': ('Form Analysis', create_form_page),
        'race-confidence': ('Race Confidence', create_race_confidence_page),
        'recovery': ('Recovery', create_recovery_page),
    }
    
    generated_files = []
    
    for filename, (title, generator_func) in dashboards.items():
        try:
            fig = generator_func()
            
            # Save as standalone HTML
            output_file = output_dir / f"{filename}.html"
            fig.write_html(
                str(output_file),
                include_plotlyjs='cdn',
                config={'displayModeBar': True, 'displaylogo': False}
            )
            
            generated_files.append((filename, title, output_file))
            print(f"  ✓ {output_file.name}")
            
        except Exception as e:
            print(f"  ✗ Error generating {filename}: {e}")
            import traceback
            traceback.print_exc()
    
    # Create index.html that links to all dashboards
    print("\n  Generating index page...")
    index_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Running Analytics Dashboard - Sample Data</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }
        h1 {
            color: #333;
            border-bottom: 3px solid #4CAF50;
            padding-bottom: 10px;
        }
        .dashboard-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 20px;
            margin-top: 30px;
        }
        .dashboard-card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .dashboard-card:hover {
            transform: translateY(-4px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        }
        .dashboard-card h3 {
            margin-top: 0;
            color: #4CAF50;
        }
        .dashboard-card a {
            display: inline-block;
            margin-top: 10px;
            padding: 8px 16px;
            background: #4CAF50;
            color: white;
            text-decoration: none;
            border-radius: 4px;
            transition: background 0.2s;
        }
        .dashboard-card a:hover {
            background: #45a049;
        }
        .info-box {
            background: #e3f2fd;
            border-left: 4px solid #2196F3;
            padding: 15px;
            margin: 20px 0;
            border-radius: 4px;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }
        .stat-card {
            background: white;
            padding: 15px;
            border-radius: 6px;
            text-align: center;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        .stat-card .value {
            font-size: 24px;
            font-weight: bold;
            color: #4CAF50;
        }
        .stat-card .label {
            font-size: 12px;
            color: #666;
            margin-top: 5px;
        }
    </style>
</head>
<body>
    <h1>🏃 Running Analytics Dashboard</h1>
    
    <div class="info-box">
        <strong>📊 Sample Data Demonstration</strong><br>
        This dashboard shows 12 months of synthetic running data for a sub-2hr half marathon training campaign.
        All data is anonymized and generated for demonstration purposes.
    </div>
    
    <div class="stats">
        <div class="stat-card">
            <div class="value">161</div>
            <div class="label">Total Activities</div>
        </div>
        <div class="stat-card">
            <div class="value">1,888 km</div>
            <div class="label">Total Distance</div>
        </div>
        <div class="stat-card">
            <div class="value">36 km</div>
            <div class="label">Avg Weekly Volume</div>
        </div>
        <div class="stat-card">
            <div class="value">44.6</div>
            <div class="label">VO2max</div>
        </div>
        <div class="stat-card">
            <div class="value">59 bpm</div>
            <div class="label">Resting HR</div>
        </div>
        <div class="stat-card">
            <div class="value">1:55-2:00</div>
            <div class="label">HM Target</div>
        </div>
    </div>
    
    <h2>Dashboard Pages</h2>
    <div class="dashboard-grid">
"""
    
    for filename, title, _ in generated_files:
        index_html += f"""
        <div class="dashboard-card">
            <h3>{title}</h3>
            <p>Interactive visualization with Plotly charts</p>
            <a href="{filename}.html">View Dashboard →</a>
        </div>
"""
    
    index_html += """
    </div>
    
    <div class="info-box" style="margin-top: 40px;">
        <strong>💡 Getting Started</strong><br>
        To use this system with your own Garmin data:<br>
        1. Clone the repository<br>
        2. Follow the <a href="../../QUICK-START.md">Quick Start Guide</a><br>
        3. Sync your Garmin activities<br>
        4. Run the full Streamlit dashboard locally
    </div>
</body>
</html>
"""
    
    index_file = output_dir / "index.html"
    with open(index_file, 'w', encoding='utf-8') as f:
        f.write(index_html)
    
    print(f"  ✓ {index_file.name}")
    
    print("\n" + "="*60)
    print("✅ HTML Dashboard Generation Complete!")
    print("="*60)
    print(f"\nGenerated {len(generated_files)} dashboard pages:")
    for filename, title, filepath in generated_files:
        print(f"  • {title}: {filepath.name}")
    
    print(f"\n📁 Output directory: {output_dir}")
    print(f"🌐 Open in browser: {index_file}")
    print("\n💡 These files can be viewed directly on GitHub or locally")
    print("   GitHub will render them in the repository file viewer")


if __name__ == "__main__":
    main()
