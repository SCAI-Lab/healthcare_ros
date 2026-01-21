# Healthcare Messages Demonstration - EEG Pipeline

**ROS2-based EEG data acquisition, preprocessing, and storage pipeline using `healthcare_msgs`**

## Overview

This project demonstrates a complete EEG data processing pipeline using ROS2 and the `healthcare_msgs` package. It supports multiple EEG hardware devices, real-time preprocessing, flexible data storage, and visualization tools.

**Supported OS:** Linux (tested on Ubuntu with ROS2 Jazzy)

## Quick Start

```bash
cd ~/ros2_ws/src/-healthcare_demo

# Start with simulator (no hardware needed)
USE_ACQUISITION=0 ./launch/start.sh

# Or with real hardware
USE_ACQUISITION=1 ./launch/start.sh  # OpenBCI
USE_ACQUISITION=2 ./launch/start.sh  # Neurosity
```

For detailed usage and configuration options, see [`launch/STARTUP_COMMANDS.md`](launch/STARTUP_COMMANDS.md).

## Architecture

### Pipeline Overview

```
┌─────────────────┐      ┌──────────────┐      ┌─────────────┐
│  Data Source    │─────▶│ Preprocessor │─────▶│   Savers    │
│  (Acquisition)  │      │  (Optional)  │      │ (JSON/MCAP) │
└─────────────────┘      └──────────────┘      └─────────────┘
       │                        │                      │
       ▼                        ▼                      ▼
  /eeg/raw              /eeg/processed         eeg_data/*.jsonl
  /eeg/raw_info         /eeg/processed_info    rosbag_data/*.mcap
```

### Components

**1. Data Acquisition** (`nodes/data_acquisition/`)
- **Simulator** - Synthetic EEG data for testing (`eeg_simulator.py`)
- **Neurosity** - Neurosity Crown headset via ROS2 package (`neurosity_driver/`)
- **OpenBCI** - OpenBCI Cyton board via ROS2 package (`openbci_driver/`)

**2. Preprocessing** (`nodes/preprocessing/`)
- **EEG Preprocessor** - Bandpass filtering (0.5-45 Hz) and Common Average Reference (CAR)

**3. Data Savers** (`nodes/saver/`)
- **JSON Saver** - Stores data in JSONL format with metadata (overwrites on startup)
- **Rosbag Saver** - Records to MCAP format for ROS2 playback

**4. Visualization** (`nodes/visualization/`)
- **RQT Plugin** - Real-time plotting GUI
- **Offline Plotter** - Static comparison plots (auto-numbered, saves to `plots/`)

### Standardized Topics

| Topic | Message Type | QoS | Description |
|-------|-------------|-----|-------------|
| `/eeg/raw` | `healthcare_msgs/EEG` | Default | Raw EEG data from acquisition |
| `/eeg/raw_info` | `healthcare_msgs/EEGInfo` | Latching | Raw data metadata |
| `/eeg/processed` | `healthcare_msgs/EEG` | Default | Preprocessed EEG data |
| `/eeg/processed_info` | `healthcare_msgs/EEGInfo` | Latching | Preprocessing metadata |

**Latching QoS** ensures late subscribers receive metadata.

## Installation

### Prerequisites

- ROS2 (Jazzy or compatible)
- Python 3.10+
- Linux (Ubuntu 22.04+ recommended)

### Setup

```bash
cd ~/ros2_ws/src
git clone <repository-url> -healthcare_demo
cd -healthcare_demo
./launch/start.sh
```

The script automatically:
- Creates virtual environment (`~/hcmd-venv`)
- Installs dependencies
- Sources ROS2
- Builds packages
- Starts pipeline

### Configuration

**Neurosity Device:**
```bash
cp nodes/data_acquisition/neurosity_driver/.env.example nodes/data_acquisition/neurosity_driver/.env
# Edit with your credentials
```

**OpenBCI Device:**
```bash
USE_ACQUISITION=1 OPENBCI_PORT=/dev/ttyUSB0 OPENBCI_CHANNELS=8 ./launch/start.sh
```

## Usage

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `USE_ACQUISITION` | `0` | Data source: 0=simulator, 1=OpenBCI, 2=Neurosity |
| `OPENBCI_PORT` | `/dev/ttyUSB0` | Serial port for OpenBCI |
| `OPENBCI_CHANNELS` | `8` | OpenBCI channels (8 or 16) |
| `RUN_TESTS` | `0` | Set to 1 to run tests |
| `VENV_PATH` | `~/hcmd-venv` | Virtual environment path |
| `VISUALIZATION_MODE` | `none` | `comparison` or `rqt` |

### Common Commands

```bash
# Start with different data sources
USE_ACQUISITION=0 ./launch/start.sh  # Simulator
USE_ACQUISITION=1 ./launch/start.sh  # OpenBCI
USE_ACQUISITION=2 ./launch/start.sh  # Neurosity

# Run tests
RUN_TESTS=1 RUN_NODE=0 ./launch/start.sh

# With visualization
VISUALIZATION_MODE=rqt ./launch/start.sh
VISUALIZATION_MODE=comparison ./launch/start.sh

# Monitor logs
tail -f logs/eeg_simulator.log
tail -f logs/eeg_json_saver_raw.log
tail -f logs/eeg_preprocessor.log

# View data
head -3 eeg_data/eeg_raw_data.jsonl | python3 -m json.tool
cat eeg_data/eeg_raw_data.info.json

# Stop all nodes
kill $(cat logs/*.pid)
```

## Data Format

### JSONL Files

```json
{
  "header": {
    "stamp": {"sec": 1234567890, "nanosec": 123456789},
    "frame_id": "eeg_sensor"
  },
  "session_id": "session_uuid",
  "sample_size": 64,
  "eeg": [/* flattened array: channels * samples */],
  "quality": [0.95, 0.92, 0.88, 0.90]
}
```

### Metadata (.info.json)

```json
{
  "channel_size": 4,
  "sampling_rate": 256.0,
  "channel_location": ["Fp1", "Fp2", "F3", "F4"],
  "unit": "microvolts",
  "device_info": {
    "session_id": "session_uuid",
    "device_id": "device_name"
  },
  "selected_preprocessing": [4]
}
```

## Testing

### Run All Tests
```bash
RUN_TESTS=1 RUN_NODE=0 ./launch/start.sh
```

### Test Suites

**Unit Tests** (15 tests):
- Signal generation
- JSONL format
- Data validation
- EEGInfo structure
- Node imports

**Integration Tests** (11 tests):
- End-to-end pipeline
- Data format/structure
- Channel/sample consistency
- Quality validation
- Metadata verification

## Data Acquisition

### Simulator
Generates synthetic 4-channel EEG with realistic brain signals (alpha, beta, theta waves).
Located in `nodes/data_acquisition/eeg_simulator.py`.

### Neurosity Crown
WiFi connection via Neurosity SDK. Implemented as ROS2 package in `nodes/data_acquisition/neurosity_driver/`.
Requires `.env` credentials in the driver package directory.

### OpenBCI Cyton
USB serial connection via ROS2 package in `nodes/data_acquisition/openbci_driver/`.
Supports 8 or 16 channels (with Daisy board). Configured via ROS2 parameters.

**Details:** See [`nodes/data_acquisition/README.md`](nodes/data_acquisition/README.md)

## Visualization

### Real-time (rqt)
```bash
VISUALIZATION_MODE=rqt ./launch/start.sh
```

### Offline Plotting
```bash
# Generate 2-second comparison plot (auto-numbered)
python nodes/visualization/plot_eeg_comparison.py

# Or start with visualization mode
VISUALIZATION_MODE=comparison ./launch/start.sh
```
Plots are saved to `plots/eeg_comparison_NNN.png` with auto-incrementing numbers.

**Details:** See [`nodes/visualization/README.md`](nodes/visualization/README.md)

## Troubleshooting

### Import Errors
```bash
source ~/hcmd-venv/bin/activate
source /opt/ros/jazzy/setup.bash
source ~/ros2_ws/install/setup.bash
```

### No Data Saved
```bash
# Check running nodes
ps aux | grep -E "eeg_simulator|eeg_json_saver|eeg_preprocessing"

# Check logs for errors
grep -i error logs/*.log
```

### Build Failures
```bash
REBUILD=1 ./launch/start.sh
```

### Device Issues

**Neurosity:**
- Verify device powered and on WiFi
- Check `.env` credentials
- Test with simulator first

**OpenBCI:**
- Check USB: `ls -l /dev/ttyUSB*`
- Add to dialout group: `sudo usermod -a -G dialout $USER`
- Logout/login required

## Development

### Adding Data Sources

1. Create `nodes/data_acquisition/new_device.py`
2. Publish to `/eeg/raw` and `/eeg/raw_info` (latching QoS)
3. Update `launch/start.sh`
4. Add tests
5. Document

### Directory Structure

```
├── config/                 # Configuration files
├── eeg_data/              # Stored JSONL data
├── launch/                # Launch scripts
│   ├── start.sh
│   └── STARTUP_COMMANDS.md
├── logs/                  # Process logs
├── nodes/
│   ├── data_acquisition/  # Hardware drivers
│   ├── preprocessing/     # Signal processing
│   ├── saver/            # Data persistence
│   └── visualization/    # Plotting tools
├── tests/                # Test suites
└── README.md
```

## Dependencies

### Python Packages
- numpy, scipy, matplotlib
- mne (EEG analysis)
- neurosity (Neurosity SDK)
- openbci-python (OpenBCI SDK)
- python-dotenv, pyyaml

### ROS2 Packages
- rclpy
- healthcare_msgs
- rqt_gui

## License

Apache-2.0

## References

- [ROS2 Documentation](https://docs.ros.org/)
- [healthcare_msgs](https://github.com/ros-medical/healthcare_msgs)
- [Neurosity SDK](https://docs.neurosity.co/)
- [OpenBCI Docs](https://docs.openbci.com/)

