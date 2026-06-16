# EEG Pipeline Startup Guide

## Quick Start with start.sh

The `start.sh` script handles all environment setup and node launching. Navigate to the project root and run:

```bash
./launch/start.sh
```

This will:
- Create/activate Python virtual environment (default: `~/hcmd-venv`)
- Source ROS2 setup (default: Jazzy)
- Install missing Python dependencies (numpy, scipy, matplotlib, mne, etc.)
- Build workspace packages if needed
- Start the complete 4-node EEG pipeline:
  1. **EEG Simulator**, **Neurosity Driver**, or **OpenBCI Driver** (depending on USE_ACQUISITION or device)
  2. **Raw EEG Saver** - saves to daily files like `eeg_data/eeg_raw_data_YYYY-MM-DD.jsonl`
  3. **EEG Preprocessor** - applies bandpass filter (0.5-45 Hz) and CAR
  4. **Preprocessed EEG Saver** - saves to daily files like `eeg_data/eeg_preprocessed_data_YYYY-MM-DD.jsonl`
- Daily JSONL retention is enabled: files older than 4 days are automatically deleted.

## Environment Variables

Control script behavior with these variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `USE_ACQUISITION` | `0` | Data source: `0`=simulator, `1`=OpenBCI, `2`=Neurosity |
| `USE_ROSBAG` | `0` | Storage format: `0`=JSON (dual savers), `1`=MCAP rosbag (all topics) |
| `OPENBCI_PORT` | `/dev/ttyUSB0` | Serial port for OpenBCI device |
| `OPENBCI_CHANNELS` | `8` | Number of OpenBCI channels (8 or 16 with daisy) |
| `RUN_NODE` | `1` | Set to `0` to only setup environment without starting nodes |
| `RUN_TESTS` | `0` | Set to `1` to run unit and integration tests before starting nodes |
| `NO_BUILD` | `0` | Set to `1` to skip building packages |
| `REBUILD` | `0` | Set to `1` to force rebuild packages |
| `VENV_PATH` | `~/hcmd-venv` | Path to Python virtual environment |
| `WORKSPACE` | `~/ros2_ws` | Path to ROS2 workspace |
| `ROS_DISTRO` | `jazzy` | ROS2 distribution name |
| `VISUALIZATION_MODE` | `none` | Set to `comparison` for offline plotting |
| `PRODUCTION` | `0` | Production preset: simulator + online visualization |

## Common Usage Examples

**Three EEG data source options:**
1. **Simulator** - Generates synthetic EEG data (no hardware needed)
2. **Neurosity** - Real EEG headset with WiFi connectivity (requires credentials)
3. **OpenBCI** - Real EEG board with USB serial connection (requires hardware)

**All data sources publish to standardized topics:**
- `/eeg/raw` - Raw EEG data messages
- `/eeg/raw_info` - EEG metadata (channels, sampling rate, electrode positions, etc.)
- `/eeg/processed` - Preprocessed EEG data (after filtering and CAR)
- `/eeg/processed_info` - Preprocessed data metadata

### Run with simulator (no device needed)
```bash
USE_ACQUISITION=0 ./launch/start.sh
# Or simply (0 is default):
./launch/start.sh
```

### Production preset (simulator + online visualization)
```bash
PRODUCTION=1 ./launch/start.sh
```

### Run with real Neurosity device
```bash
USE_ACQUISITION=2 ./launch/start.sh
```
*Requires `.env` file with credentials in `nodes/data_acquisition/neurosity_driver/.env`*

### Run with OpenBCI device
```bash
USE_ACQUISITION=1 ./launch/start.sh

# With custom port and 16 channels (with daisy board)
USE_ACQUISITION=1 OPENBCI_PORT=/dev/ttyUSB1 OPENBCI_CHANNELS=16 ./launch/start.sh
```
*Requires OpenBCI board connected via USB.*

### Setup only (don't start nodes)
```bash
RUN_NODE=0 ./launch/start.sh
```

### Skip building (if already built)
```bash
NO_BUILD=1 USE_ACQUISITION=0 ./launch/start.sh
```

### Run with offline comparison plotting
```bash
USE_ACQUISITION=0 VISUALIZATION_MODE=comparison ./launch/start.sh
```

### Use rosbag (MCAP format) instead of JSON
```bash
USE_ACQUISITION=0 USE_ROSBAG=1 ./launch/start.sh
```

### Enable Real-Time Latency Monitoring with Dashboard
```bash
# Production setup with latency monitoring (recommended for performance analysis)
PRODUCTION=1 ./launch/start.sh
```

This enables:
- Real-time EEG visualization (Raw vs Preprocessed)
- End-to-End Latency Metrics on the dashboard
- InfluxDB time-series database (5-minute data retention)
- Web dashboard at http://localhost:8080

Monitor latency metrics directly in the dashboard:
- Raw>Proc: Time from acquisition to preprocessing (typical: 8-20ms)
- E2E: Total end-to-end latency (typical: 30-100ms)
- EMA: Exponential moving average over last 100 samples

For detailed latency analysis, see [LATENCY_MONITORING_EN.md](../docs/LATENCY_MONITORING_EN.md)
*Records all topics to MCAP format in `nodes/rosbag_data/`. View with `ros2 bag info nodes/rosbag_data/`*

### Run automated tests (unit + integration)
```bash
RUN_TESTS=1 RUN_NODE=0 ./launch/start.sh
```
*Runs unit tests and integration tests (with temporary simulator), then exits.*

### Run tests then start pipeline
```bash
RUN_TESTS=1 USE_ACQUISITION=0 ./launch/start.sh
```
*Validates system with tests, then starts simulator and full pipeline.*

## Monitor Running Pipeline

### View logs in real-time
```bash
# From project root
tail -f logs/eeg_simulator.log          # Simulator output
tail -f logs/neurosity_driver.log       # Neurosity driver output
tail -f logs/openbci_driver.log         # OpenBCI driver output
tail -f logs/eeg_json_saver_raw.log     # Raw data saver
tail -f logs/eeg_preprocessor.log       # Preprocessing node
tail -f logs/eeg_json_saver_preprocessed.log  # Preprocessed data saver
```

### Check process status
```bash
# PIDs are stored in logs/ directory
cat logs/eeg_simulator.pid
cat logs/neurosity_driver.pid
cat logs/openbci_driver.pid
cat logs/eeg_json_saver_raw.pid
cat logs/eeg_preprocessor.pid
cat logs/eeg_json_saver_preprocessed.pid
```

### View data files
```bash
# From project root
TODAY=$(date +%F)
head -3 "eeg_data/eeg_raw_data_${TODAY}.jsonl" | python3 -m json.tool
head -3 "eeg_data/eeg_preprocessed_data_${TODAY}.jsonl" | python3 -m json.tool

# File sizes
ls -lh eeg_data/
```

## Stop the Pipeline

### Stop all nodes
```bash
# Kill by PID files
kill $(cat logs/eeg_simulator.pid logs/eeg_json_saver_raw.pid logs/eeg_preprocessor.pid logs/eeg_json_saver_preprocessed.pid)

# Or stop all Python processes (more aggressive)
pkill -f "eeg_simulator|eeg_json_saver|preprocessing"
```

## Configuration

### Required for Neurosity Device
Create `nodes/data_acquisition/neurosity_driver/.env` from the template:
```bash
cd nodes/data_acquisition/neurosity_driver/
cp .env.example .env
# Edit .env with your actual credentials
```

### Required for OpenBCI Device
OpenBCI driver is now integrated into start.sh. Configure via environment variables:
- `USE_ACQUISITION=1` - Enable OpenBCI mode
- `OPENBCI_PORT` - Serial port (default: `/dev/ttyUSB0`)
- `OPENBCI_CHANNELS` - Number of channels: 8 or 16 (default: 8)

Example:
```bash
USE_ACQUISITION=1 OPENBCI_PORT=/dev/ttyUSB1 OPENBCI_CHANNELS=16 ./launch/start.sh
```

### Optional Parameters
Edit `config/params.yaml` for advanced node configuration (currently placeholder).

## Visualization Options

### Offline Comparison Plot
Generates side-by-side comparison of raw vs preprocessed data:
```bash
VISUALIZATION_MODE=comparison ./launch/start.sh
# Or run directly:
python3 nodes/visualization/plotting/plot_eeg_comparison.py
```

### Online dashboard (InfluxDB + Nginx)
```bash
USE_INFLUXDB=1 ./launch/start.sh
```
Dashboard URLs:
- http://localhost:8080/ (recommended)
- https://localhost/ (optional TLS endpoint)

## Troubleshooting

### Check environment setup
```bash
# Verify Python venv
which python3
# Should show: /home/<user>/hcmd-venv/bin/python3

# Verify ROS2 sourced
echo $ROS_DISTRO
# Should show: jazzy
```

### Build issues
```bash
# Force rebuild
REBUILD=1 ./launch/start.sh

# Or manually
cd ~/ros2_ws
colcon build --packages-select healthcare_msgs --symlink-install
source install/setup.bash
```

### Missing dependencies
The script auto-installs packages, but you can manually install:
```bash
source ~/hcmd-venv/bin/activate
pip install numpy scipy matplotlib mne neurosity python-dotenv pyyaml
```

### No data being saved
```bash
# Check if nodes are running
ps aux | grep -E "eeg_simulator|eeg_json_saver|preprocessing"

# Check for errors in logs
grep -i error logs/*.log

# Verify data directory exists
ls -la eeg_data/
```

### Run diagnostic tests
```bash
# Quick validation - setup environment and run all tests
RUN_TESTS=1 RUN_NODE=0 ./launch/start.sh

# This will:
# 1. Setup Python venv and install dependencies
# 2. Build ROS2 packages if needed
# 3. Run unit tests (8 tests - signal generation, JSONL format, validation)
# 4. Run integration tests (6 tests - file format, message structure, data consistency)
# 5. Display summary of passed/failed tests
```
