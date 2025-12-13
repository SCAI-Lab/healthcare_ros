**Project Overview**
- **Name:** Neurosity ROS2 demo with `healthcare_msgs` proof-of-concept
- **Purpose:** Demonstrates publishing EEG data (using `healthcare_msgs/msg/biosensing/raw_biosignals/EEG.msg`) from a Neurosity device or a simulator and storing it in JSONL format for downstream processing.

**Supported OS**: Linux (instructions are written and tested for a Linux desktop/server environment).

**High-level components**
- `neurosity_driver`: ROS2 Python node that connects to Neurosity SDK and publishes `/neurosity/eeg` and `/neurosity/eeg_info`.
- `eeg_saver.py`: Subscriber node that saves `healthcare_msgs/EEG` messages to `~/neurosity_logs/eeg_data.jsonl` (JSONL: one JSON object per line).
- `eeg_simulator.py`: Optional simulator that publishes synthetic EEG data in the same `healthcare_msgs` format for testing without hardware.
- `start.sh`: Orchestration script that prepares the environment, builds packages (if needed), and starts the driver/simulator + saver.
- `test_eeg_integration.py`: Automated integration test that validates the entire EEG pipeline (data format, channel count, sample consistency, quality scores).
- `visualize_eeg.py`: Visualization and analysis tool that generates time-domain and frequency-spectrum plots from stored EEG data.

**Quick start (tested workflow)**
1. Open a terminal on Linux.
2. Clone this repo into your ROS2 workspace `src/` (if not present):

```bash
# from your workspace root (example: ~/ros2_ws)
cd ~/ros2_ws/src
# git clone <this-repo>  (if not already present)
```

3. Run the setup/start script (creates/uses venv, sources ROS2, builds if required):

```bash
cd ~/ros2_ws/src/-healthcare_msgs_demonstration
# Run with real device (requires .env credentials and device online)
./start.sh

# Or run in SIMULATOR mode (no device needed):
SIMULATE=1 ./start.sh
```

4. Monitor logs and data:

```bash
# View node logs
tail -f ~/neurosity_logs/neurosity_driver.log    # driver (real device)
tail -f ~/neurosity_logs/eeg_simulator.log      # simulator (if SIMULATE=1)
tail -f ~/neurosity_logs/eeg_saver.log          # saver (always)

# View stored EEG samples (JSONL)
head -3 ~/neurosity_logs/eeg_data.jsonl | python3 -m json.tool
```

**Environment details and assumptions**
- Python venv default path: `~/neurosity-venv` (configurable via `VENV_PATH` env var)
- ROS2 distro default: `jazzy` (configurable via `ROS_DISTRO` env var)
- Workspace default: `~/ros2_ws` (configurable via `WORKSPACE` env var)
- Credential file for Neurosity (when using real device): place `.env` in the `neurosity_driver` package directory, example keys:

```
NEUROSITY_DEVICE_ID=your_device_id
NEUROSITY_EMAIL=you@example.com
NEUROSITY_PASSWORD=supersecret
```

**Installation / Build (manual steps)**
1. Ensure ROS2 for your distro is installed and `source /opt/ros/$ROS_DISTRO/setup.bash` works.
2. Create and activate venv (if you prefer manual control):

```bash
python3 -m venv ~/neurosity-venv
source ~/neurosity-venv/bin/activate
python -m pip install --upgrade pip
pip install empy catkin-pkg lark-parser pyyaml neurosity python-dotenv matplotlib numpy
```

3. From workspace root, install system deps and build:

```bash
# run once (may require sudo for rosdep)
rosdep update && rosdep install --from-paths src --ignore-src -r -y

# build packages (the script may already do this)
colcon build --packages-select healthcare_msgs neurosity_driver --symlink-install
source install/setup.bash
```

**Simulator usage (recommended for testing)**
- Start the simulator with `SIMULATE=1 ./start.sh` — it will publish EEG messages to `/neurosity/eeg` in the same `healthcare_msgs` format and `eeg_saver` will record them to `~/neurosity_logs/eeg_data.jsonl`.

**Testing & Validation**
- **Automated integration test:** Run the full pipeline test (simulator + saver) and validate data format, structure, and completeness:
  ```bash
  python3 test_eeg_integration.py 15  # Run for 15 seconds, validate all checks
  ```
  This test verifies:
  - Data file exists and contains valid JSONL
  - EEG message format correct (header, session_id, eeg array, quality)
  - Channel count is 4 across all messages
  - Sample counts match array dimensions
  - Quality scores are in valid range [0, 1]

- **Data visualization:** Generate time-domain and frequency-spectrum plots from stored EEG data:
  ```bash
  python3 visualize_eeg.py ~/neurosity_logs/eeg_data.jsonl
  ```
  Outputs:
  - `eeg_time_domain.png` — 4 subplots (one per channel) with signal waveforms
  - `eeg_frequency_spectrum.png` — FFT plots with frequency band markers (Theta/Alpha/Beta)
  - Console statistics: mean, std, min, max per channel (in µV)

**Simulator usage (recommended for testing)**
- Start the simulator with `SIMULATE=1 ./start.sh` — it will publish EEG messages to `/neurosity/eeg` in the same `healthcare_msgs` format and `eeg_saver` will record them to `~/neurosity_logs/eeg_data.jsonl`.

**Data format**
- Saved file: `~/neurosity_logs/eeg_data.jsonl`
- Each line is a JSON object matching the `healthcare_msgs/EEG` message structure, for example:

```json
{
  "header": {"stamp": {"sec": 123, "nsec": 456}, "frame_id": "neurosity"},
  "session_id": "session_...",
  "sample_size": 64,
  "eeg": [ ... flattened array length = channel_count * sample_size ...],
  "quality": [ ... per-channel quality scores ...]
}
```

**Troubleshooting**
- If editor (VS Code) shows import warnings for `healthcare_msgs`, source the workspace overlay or select the venv Python interpreter in VS Code. The runtime import works if `source ~/ros2_ws/install/setup.bash` and the venv are active.
- If no EEG samples arrive while the driver is running: check device power/network and credentials; use `SIMULATE=1` to validate pipeline without the device.
- If builds fail due to missing Python packages, ensure `empy`, `catkin-pkg`, `lark-parser`, and `pyyaml` are installed in the venv.
- If visualization script fails with `ModuleNotFoundError: No module named 'matplotlib'`, install it: `pip install matplotlib numpy`

**Files added by this demo**
- `start.sh` — setup + start orchestration
- `eeg_saver.py` — subscriber & data recorder
- `eeg_simulator.py` — test data publisher

**Next steps / Suggestions**
- Add a small metadata index file (e.g., `eeg_metadata.json`) alongside `eeg_data.jsonl` to record `EEGInfo` fields published by the driver so consumers can map flattened arrays to channel names.
- Consider rotating logs and data files after they reach a size threshold.

