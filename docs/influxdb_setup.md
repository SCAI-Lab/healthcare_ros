# InfluxDB Integration Guide

This guide explains how to set up InfluxDB for real-time EEG data visualization via the Explorer UI web interface.

## Overview

The `eeg_influxdb_bridge.py` node subscribes to both raw and preprocessed EEG topics and writes data to InfluxDB in real-time. This enables:

- **Web-based visualization** - View live EEG data in your browser
- **Time-series analysis** - Query and analyze historical EEG data
- **Dual stream comparison** - Compare raw vs preprocessed data side-by-side
- **Remote access** - View data from any device on the network

## Architecture

```
ROS2 Topics                    InfluxDB Bridge              InfluxDB
-------------                  ----------------              ---------
/eeg/raw          ─────────>   eeg_influxdb_bridge   ───>   eeg_raw
/eeg/raw_info     ─────────>         (Python)        ───>   eeg_raw_metadata
/eeg/processed    ─────────>                         ───>   eeg_preprocessed
/eeg/processed_info ───────>                         ───>   eeg_preprocessed_metadata
```

## Installation

### 1. Install InfluxDB 3.0 (or InfluxDB OSS 2.x)

**Option A: Docker (Recommended for Testing)**
```bash
# Run InfluxDB in Docker
docker run -d \
  --name influxdb \
  -p 8086:8086 \
  -v influxdb-data:/var/lib/influxdb2 \
  -v influxdb-config:/etc/influxdb2 \
  influxdb:latest
```

**Option B: Native Installation (Ubuntu/Debian)**
```bash
# Add InfluxData repository
wget -q https://repos.influxdata.com/influxdata-archive_compat.key
echo '393e8779c89ac8d958f81f942f9ad7fb82a25e133faddaf92e15b16e6ac9ce4c influxdata-archive_compat.key' | sha256sum -c && cat influxdata-archive_compat.key | gpg --dearmor | sudo tee /etc/apt/trusted.gpg.d/influxdata-archive_compat.gpg > /dev/null
echo 'deb [signed-by=/etc/apt/trusted.gpg.d/influxdata-archive_compat.gpg] https://repos.influxdata.com/debian stable main' | sudo tee /etc/apt/sources.list.d/influxdata.list

# Install InfluxDB
sudo apt-get update
sudo apt-get install influxdb2

# Start service
sudo systemctl enable influxdb
sudo systemctl start influxdb
```

### 2. Initial InfluxDB Setup

Open your browser to `http://localhost:8086` and complete the setup wizard:

1. **Create Initial User**
   - Username: `admin`
   - Password: (choose a secure password)
   - Organization: `healthcare`
   - Bucket: `eeg_data`

2. **Generate API Token**
   - Go to: Data → API Tokens → Generate API Token → All Access Token
   - Copy the token (you'll need this later)

### 3. Install Python InfluxDB Client

```bash
# Activate your Python virtual environment
source ~/hcmd-venv/bin/activate

# Install InfluxDB client library
pip install influxdb-client
```

## Configuration

### Environment Variables

Set these before starting the bridge node:

```bash
export INFLUXDB_URL="http://localhost:8086"
export INFLUXDB_TOKEN="your-api-token-here"
export INFLUXDB_ORG="healthcare"
export INFLUXDB_BUCKET="eeg_data"
```

**For permanent setup**, add to `~/.bashrc`:
```bash
echo 'export INFLUXDB_TOKEN="your-api-token-here"' >> ~/.bashrc
echo 'export INFLUXDB_ORG="healthcare"' >> ~/.bashrc
echo 'export INFLUXDB_BUCKET="eeg_data"' >> ~/.bashrc
source ~/.bashrc
```

## Usage

### Start the InfluxDB Bridge

**Method 1: Standalone**
```bash
cd ~/ros2_ws/src/healthcare_demo

# Set up environment
source ~/hcmd-venv/bin/activate
source /opt/ros/jazzy/setup.bash
source ~/ros2_ws/install/setup.bash

# Set InfluxDB credentials
export INFLUXDB_TOKEN="your-token-here"

# Run bridge node
python3 nodes/saver/eeg_influxdb_bridge.py
```

**Method 2: With Launch Script (Automatic)**
```bash
# Add to your startup workflow
USE_INFLUXDB=1 ./launch/start.sh
```

### Start Data Flow

In separate terminals:

**Terminal 1: Start simulator**
```bash
./launch/start.sh
```

**Terminal 2: Start InfluxDB bridge**
```bash
cd ~/ros2_ws/src/healthcare_demo
source ~/hcmd-venv/bin/activate
source /opt/ros/jazzy/setup.bash
source ~/ros2_ws/install/setup.bash
export INFLUXDB_TOKEN="your-token-here"
python3 nodes/saver/eeg_influxdb_bridge.py
```

## Visualizing Data in InfluxDB Explorer UI

### Access the UI
Open your browser to: `http://localhost:8086`

### Create Dashboards

#### 1. View Raw EEG Data

Navigate to: **Explore** (left sidebar)

**Query Builder:**
- **FROM**: `eeg_data` bucket
- **Measurement**: `eeg_raw`
- **Field**: `mean`
- **Group by**: `channel`
- **Window**: `1s` (auto-refresh)

**Flux Query (Advanced):**
```flux
from(bucket: "eeg_data")
  |> range(start: -30s)
  |> filter(fn: (r) => r["_measurement"] == "eeg_raw")
  |> filter(fn: (r) => r["_field"] == "mean")
  |> group(columns: ["channel"])
```

#### 2. Compare Raw vs Preprocessed

**Query Builder:**
```flux
// Raw data
raw = from(bucket: "eeg_data")
  |> range(start: -30s)
  |> filter(fn: (r) => r["_measurement"] == "eeg_raw")
  |> filter(fn: (r) => r["_field"] == "mean")
  |> map(fn: (r) => ({r with _value: r._value, type: "raw"}))

// Preprocessed data
preprocessed = from(bucket: "eeg_data")
  |> range(start: -30s)
  |> filter(fn: (r) => r["_measurement"] == "eeg_preprocessed")
  |> filter(fn: (r) => r["_field"] == "mean")
  |> map(fn: (r) => ({r with _value: r._value, type: "preprocessed"}))

// Union and display
union(tables: [raw, preprocessed])
  |> group(columns: ["channel", "type"])
```

#### 3. Monitor Signal Quality

```flux
from(bucket: "eeg_data")
  |> range(start: -1m)
  |> filter(fn: (r) => r["_measurement"] == "eeg_raw")
  |> filter(fn: (r) => r["_field"] == "quality")
  |> group(columns: ["channel"])
```

#### 4. View Multiple Channels

Create a dashboard with 4 cells (one per channel):

**Cell 1 (FP1):**
```flux
from(bucket: "eeg_data")
  |> range(start: -30s)
  |> filter(fn: (r) => r["_measurement"] == "eeg_raw")
  |> filter(fn: (r) => r["channel"] == "FP1")
  |> filter(fn: (r) => r["_field"] == "mean")
```

Repeat for FP2, F3, F4...

## Data Schema

### Measurements

#### `eeg_raw` (Raw EEG data)
- **Tags**: `channel`, `session_id`, `frame_id`
- **Fields**:
  - `mean` - Average amplitude for this message
  - `min` - Minimum amplitude
  - `max` - Maximum amplitude
  - `quality` - Signal quality (0.0-1.0)
  - `sample_count` - Number of samples

#### `eeg_preprocessed` (Preprocessed EEG data)
- Same schema as `eeg_raw`

#### `eeg_raw_metadata` (Configuration metadata)
- **Tags**: `session_id`, `preprocessing`
- **Fields**:
  - `channel_count` - Number of channels
  - `units` - Signal units (microvolts)
  - `montage_type` - Electrode montage
  - `signal_mode` - Surface/depth recording

## Troubleshooting

### Connection Refused
```bash
# Check if InfluxDB is running
sudo systemctl status influxdb

# Check port
sudo netstat -tlnp | grep 8086
```

### Authentication Errors
```bash
# Verify token is set
echo $INFLUXDB_TOKEN

# Test connection
curl -H "Authorization: Token $INFLUXDB_TOKEN" http://localhost:8086/health
```

### No Data Appearing

1. **Check bridge is running**:
   ```bash
   ps aux | grep eeg_influxdb_bridge
   ```

2. **Check ROS topics are publishing**:
   ```bash
   source ~/ros2_ws/install/setup.bash
   ros2 topic echo /eeg/raw --once
   ```

3. **Check InfluxDB logs**:
   ```bash
   sudo journalctl -u influxdb -f
   ```

### Bridge Import Errors
```bash
# Ensure influxdb-client is installed
pip list | grep influxdb

# Reinstall if needed
pip install --upgrade influxdb-client
```

## Advanced Configuration

### Custom Time Windows
Modify retention policies for long-term storage:

```bash
# Create retention policy (keep data for 7 days)
influx bucket create \
  --name eeg_data_archive \
  --org healthcare \
  --retention 168h
```

### High-Frequency Sampling
For storing individual samples (warning: high storage usage):

Uncomment this section in `eeg_influxdb_bridge.py`:
```python
# Optionally store all samples (can be large - comment out if needed)
for sample_idx, sample_value in enumerate(channel_samples):
    point = point.field(f'sample_{sample_idx}', float(sample_value))
```

### Remote Access
To access InfluxDB from other machines:

1. **Configure InfluxDB to listen on all interfaces**:
   Edit `/etc/influxdb/influxdb.conf`:
   ```
   bind-address = "0.0.0.0:8086"
   ```

2. **Update bridge URL**:
   ```bash
   export INFLUXDB_URL="http://your-server-ip:8086"
   ```

## Performance Notes

- **Data Volume**: With default settings (statistics only), ~1KB per message
- **Storage**: ~3.6 MB/hour for 4 channels at 256 Hz (10 messages/sec)
- **Latency**: <10ms typical write latency
- **Retention**: Default 30 days, configurable per bucket

## Integration with Existing Pipeline

The InfluxDB bridge runs **alongside** existing savers:
- **JSONL files** continue to work (`eeg_json_saver.py`)
- **Rosbag files** continue to work (`eeg_rosbag_saver.py`)
- **RQT visualization** continues to work
- All savers receive the same data simultaneously

## Next Steps

1. Create custom dashboards for your specific analysis needs
2. Set up alerts for signal quality degradation
3. Configure downsampling rules for long-term storage
4. Integrate with Grafana for more advanced visualization options

## Resources

- [InfluxDB Documentation](https://docs.influxdata.com/influxdb/v2/)
- [Flux Query Language](https://docs.influxdata.com/flux/v0/)
- [Python Client Library](https://github.com/influxdata/influxdb-client-python)
