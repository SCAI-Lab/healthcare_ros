# EEG Visualization

This directory contains visualization tools for EEG data analysis.

## Components

### 1. RQT Plugin (eeg_visualization_rqt/)
**Type:** ROS2 package - Interactive GUI plugin for rqt

**Purpose:** Real-time visualization of EEG data streams

**Features:**
- Side-by-side comparison of raw and preprocessed EEG signals
- Live plotting with matplotlib embedded in Qt
- Subscribes to `/eeg/raw` and `/eeg/processed` topics
- Multi-channel display with configurable buffer size

**Launch:**
```bash
# Via start.sh
VISUALIZATION_MODE=rqt ./launch/start.sh

# Or manually
export RQT_PLUGIN_PATH="$PWD/nodes/visualization/eeg_visualization_rqt"
rqt --standalone eeg_visualization_rqt
```

**Dependencies:**
- ROS2 (rclpy, rqt_gui, rqt_gui_py)
- Qt (python_qt_binding)
- matplotlib
- numpy
- healthcare_msgs

**Structure:**
```
eeg_visualization_rqt/
├── package.xml          # ROS2 package manifest
├── setup.py             # Python package setup
├── resource/            # Plugin registration XML
└── eeg_visualization_rqt/
    ├── __init__.py
    └── eeg_visualization_widget.py  # Main plugin implementation
```

### 2. Offline Comparison Plot (plot_eeg_comparison.py)
**Type:** Standalone Python script

**Purpose:** Generate static comparison plots from saved JSONL data files

**Features:**
- Loads data from `eeg_data/eeg_raw_data.jsonl` and `eeg_data/eeg_preprocessed_data.jsonl`
- Plots selected channels for specified time window
- Displays raw vs preprocessed signals side-by-side
- Configurable sampling rate, channels, and duration

**Usage:**
```bash
# Via start.sh
VISUALIZATION_MODE=comparison ./launch/start.sh

# Or manually
python3 nodes/visualization/plot_eeg_comparison.py
```

**Configuration:**
Edit the script's `main()` function to customize:
- `channels_to_plot` - Which EEG channels to display (default: [0, 1, 2, 3])
- `seconds_to_plot` - Time window duration (default: 10 seconds)
- `sampling_rate` - Data sampling frequency (default: 256 Hz)
- `num_channels` - Total number of channels (default: 4)
- `channel_names` - Channel labels (default: ['FP1', 'FP2', 'F3', 'F4'])

**Dependencies:**
- matplotlib
- numpy
- json

## Visualization Modes

**Real-time (rqt):**
- Best for: Live monitoring during data collection
- Requires: Running ROS2 nodes publishing to `/eeg/raw` and `/eeg/processed`
- Interactive: Can pause, zoom, pan

**Offline (comparison plot):**
- Best for: Post-processing analysis and quality checks
- Requires: Existing JSONL data files in `eeg_data/`
- Static: Generates matplotlib figure for inspection

## Adding New Visualizations

To add new visualization tools:

1. **For real-time ROS2 visualizations:**
   - Create new ROS2 package in this directory
   - Subscribe to relevant EEG topics
   - Follow rqt plugin pattern if GUI needed

2. **For offline analysis scripts:**
   - Add standalone Python script to this directory
   - Use `eeg_data/*.jsonl` as data source
   - Document usage in this README

## Topics Used

- `/eeg/raw` (healthcare_msgs/EEG) - Raw EEG data from acquisition nodes
- `/eeg/raw_info` (healthcare_msgs/EEGInfo) - Metadata for raw data
- `/eeg/processed` (healthcare_msgs/EEG) - Preprocessed EEG data
- `/eeg/processed_info` (healthcare_msgs/EEGInfo) - Metadata for preprocessed data

## Notes

- The rqt plugin is a ROS2 package and requires building with `colcon build`
- Offline plotting script is standalone and doesn't require ROS2 runtime
- Generated plots and images should not be committed to version control
- For custom analysis, consider creating Jupyter notebooks in a separate `analysis/` directory
