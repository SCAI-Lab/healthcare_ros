# Neurosity Driver Startup Commands

## Quick Start

To start the neurosity driver with automatic environment setup, run:

```bash
cd ~/ros2_ws/src/-healthcare_msgs_demonstration && ./start.sh
```

This will:
- Activate the Python virtual environment (`~/neurosity-venv`)
- Source ROS2 Jazzy setup
- Source the workspace overlay
- Install missing Python dependencies
- Build packages if needed
- Start the neurosity_driver node in the background

## Individual Steps (Manual Setup)

If you prefer to set up the environment manually:

### 1. Activate Virtual Environment
```bash
source ~/neurosity-venv/bin/activate
```

### 2. Source ROS2 Jazzy
```bash
source /opt/ros/jazzy/setup.bash
```

### 3. Source Workspace Overlay
```bash
source ~/ros2_ws/install/setup.bash
```

### 4. Start the Driver Node
```bash
cd ~/ros2_ws/src/-healthcare_msgs_demonstration/ros2_hc_drv/neurosity_driver
python3 -m neurosity_driver.neurosity_driver
```

## View Logs

To monitor the node in real-time:
```bash
tail -f ~/neurosity_logs/neurosity_driver.log
```

## Stop the Node

If running in the background:
```bash
kill $(cat ~/neurosity_logs/neurosity_driver.pid)
```

Or to stop all Python processes:
```bash
killall -9 python3
```

## Check ROS2 Topics

View available topics:
```bash
source ~/ros2_ws/install/setup.bash
ros2 topic list
```

View EEG data stream:
```bash
source ~/ros2_ws/install/setup.bash
ros2 topic echo /neurosity/eeg
```

## Environment Variables

You can control script behavior with environment variables:

- `NO_BUILD=1` - Skip building packages (use if already built)
- `RUN_NODE=1` - Start the driver node (default: 1)
- `SIMULATE=1` - Use EEG simulator instead of real device (default: 0)

Example:
```bash
cd ~/ros2_ws/src/-healthcare_msgs_demonstration && SIMULATE=1 NO_BUILD=1 RUN_NODE=1 ./start.sh
```

## Testing & Validation

### Run Automated Integration Test
Test the complete EEG pipeline (simulator + saver) and validate data format:

```bash
cd ~/ros2_ws/src/-healthcare_msgs_demonstration
python3 test_eeg_integration.py 15
```

This will:
- Start simulator for 15 seconds
- Validate 6 checks (file format, channels, sample counts, quality scores)
- Report pass/fail results with data statistics

### Generate EEG Plots & Statistics

Visualize stored EEG data and generate time-domain + frequency-spectrum plots:

```bash
cd ~/ros2_ws/src/-healthcare_msgs_demonstration
python3 visualize_eeg.py ~/neurosity_logs/eeg_data.jsonl
```

Outputs:
- Console statistics (mean, std, min, max per channel in µV)
- `eeg_time_domain.png` — Signal waveforms for 4 channels
- `eeg_frequency_spectrum.png` — FFT plots with Alpha/Beta/Theta markers

## Recommended Workflow

1. **Validate setup (no device needed):**
   ```bash
   SIMULATE=1 ./start.sh &  # Start simulator in background
   sleep 10
   python3 test_eeg_integration.py 10  # Run validation test
   ```

2. **Visualize captured data:**
   ```bash
   python3 visualize_eeg.py ~/neurosity_logs/eeg_data.jsonl
   ```

3. **With real Neurosity device:**
   ```bash
   ./start.sh  # Uses real device (requires .env credentials)
   ```

## Required Files

- `.env` file in `~/ros2_ws/src/-healthcare_msgs_demonstration/ros2_hc_drv/neurosity_driver/.env` with credentials:
  ```
  NEUROSITY_DEVICE_ID=your_device_id
  NEUROSITY_EMAIL=your_email
  NEUROSITY_PASSWORD=your_password
  ```

## Troubleshooting

### Check if node is running
```bash
ps aux | grep neurosity_driver
```

### Check venv activation
```bash
which python3
```
Should show: `/home/tjalf/neurosity-venv/bin/python3`

### View full logs
```bash
cat ~/neurosity_logs/neurosity_driver.log
cat ~/neurosity_logs/eeg_simulator.log
cat ~/neurosity_logs/eeg_saver.log
```
