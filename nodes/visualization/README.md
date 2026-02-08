NA by EMail without the help of the documents 2# EEG Visualization

This folder contains all visualization tools for the EEG healthcare system.

## Web Dashboard (Real-time)

### Files
- `influxdb_realtime_dashboard.template.html` - Dashboard template (tracked in git)
- `influxdb_realtime_dashboard.html` - Generated dashboard with credentials (git-ignored)
- `dashboard/generate_dashboard.py` - Script to inject credentials into template

### Generate Dashboard

```bash
# From project root
python3 nodes/visualization/dashboard/generate_dashboard.py
```

This reads credentials from `env_credentials/.env.influxdb` and generates the dashboard HTML.

### Access Dashboard

The dashboard is served by Nginx (Docker):
- **URL:** http://localhost:8080
- **Refresh Rate:** 150 Hz (6.67ms intervals)
- **Data:** Real-time EEG from InfluxDB

**Features:**
- 4-channel visualization (FP1, FP2, F3, F4)
- Statistics per channel: mean, min, max, samples
- Toggle between raw and preprocessed data
- Live latency monitoring

## Offline Plotting Tools

### plot_eeg_comparison.py
Generate comparison plots of raw vs preprocessed EEG data from JSONL files.

```bash
python3 nodes/visualization/plot_eeg_comparison.py
```

**Output:** `plots/eeg_comparison_XXX.svg`

### plot_eeg_offline.py
Alternative offline plotting tool.

## RQT Plugin (Optional)

The `eeg_visualization_rqt/` folder contains a ROS2 RQT plugin for live EEG visualization.

**Note:** Currently disabled (COLCON_IGNORE) - Use web dashboard for real-time visualization.

---

## Docker Integration

The web dashboard is automatically served by the Nginx container defined in `docker-compose.yml`.

**To update dashboard:**
1. Edit `env_credentials/.env.influxdb` credentials
2. Run: `python3 nodes/visualization/dashboard/generate_dashboard.py`
3. Restart: `docker restart healthcare-nginx`
