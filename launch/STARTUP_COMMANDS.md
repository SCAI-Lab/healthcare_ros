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

### Run Unit Tests
Test individual components (simulator, JSONL format, validation functions):

```bash
cd ~/ros2_ws/src/-healthcare_msgs_demonstration
python3 test_eeg_unit.py
```

Runs 8 independent tests:
- Simulator signal generation and FFT frequency validation
- JSONL write/read cycle and corruption detection
- Quality score bounds, channel consistency, timestamp monotonicity, amplitude bounds

**Status:** ✅ 8/8 passing

### Run Basic Integration Test
Test the complete EEG pipeline (simulator + saver) with 6 fundamental checks:

```bash
cd ~/ros2_ws/src/-healthcare_msgs_demonstration
python3 test_eeg_integration.py 15
```

Validates:
- File format and JSONL validity
- Message structure (header, session_id, eeg, quality fields)
- 4-channel consistency
- Sample count accuracy
- Quality score bounds [0, 1]

**Status:** ✅ 6/6 passing (tested with 38 messages, 9,728 samples)

### Run Enhanced Integration Test
Comprehensive validation with data loss detection, timestamp continuity, amplitude bounds, and performance metrics:

```bash
cd ~/ros2_ws/src/-healthcare_msgs_demonstration
python3 test_eeg_enhanced.py 15
```

Adds 5 advanced checks:
- Data loss detection (sequential message consistency)
- Timestamp continuity (no time wrap, monotonic increase)
- Signal amplitude bounds (±50 µV for simulator)
- Message write performance (message rate monitoring)
- Memory efficiency (bytes per sample)

**Features:** Full performance metrics collection and data summary reporting

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

1. **Quick validation (no device needed):**
   ```bash
   # Run all unit tests (8/8 passing)
   python3 test_eeg_unit.py
   
   # Start simulator and validate basic pipeline (6 checks)
   SIMULATE=1 ./start.sh &
   sleep 10
   python3 test_eeg_integration.py 10
   ```

2. **Comprehensive validation with advanced checks:**
   ```bash
   # Enhanced integration test (11 checks total)
   SIMULATE=1 ./start.sh &
   sleep 5
   python3 test_eeg_enhanced.py 20
   ```

3. **Visualize captured data:**
   ```bash
   python3 visualize_eeg.py ~/neurosity_logs/eeg_data.jsonl
   ```

4. **With real Neurosity device:**
   ```bash
   ./start.sh  # Uses real device (requires .env credentials)
   ```

## Test Coverage Summary

| Test Suite | Type | Checks | Status | Best For |
|-----------|------|--------|--------|----------|
| `test_eeg_unit.py` | Unit | 8 | ✅ 8/8 passing | Component validation, CI/CD |
| `test_eeg_integration.py` | Integration | 6 | ✅ 6/6 passing | Quick smoke test |
| `test_eeg_enhanced.py` | Integration | 11 | Ready | Full pipeline validation with performance metrics |
| `visualize_eeg.py` | Analysis | Plots + stats | ✅ Tested | Data visualization and frequency analysis |

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
