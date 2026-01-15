# Visualization Options

This folder contains EEG visualization tools for the demonstration pipeline.

- `plot_eeg_offline.py`: Offline plotting script for EEG data saved in JSONL format.
- `eeg_visualization_rqt`: ROS 2 rqt plugin for live EEG visualization (if installed) is now located in `visualization/eeg_visualization_rqt/`.

## Usage

By default, offline plotting is used. To use rqt, set `VISUALIZATION_MODE=rqt` before running the start script.
