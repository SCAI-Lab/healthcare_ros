# EEG Data Acquisition Drivers

This directory contains data acquisition nodes for the EEG processing pipeline.

## Available Drivers

### 1. EEG Simulator (`eeg_simulator.py`)
Generates synthetic EEG data for testing without hardware.

**Usage:**
```bash
python3 eeg_simulator.py
```

### 2. Neurosity Driver (ROS2 Package)
Located in `ros2_hc_drv/neurosity_driver/`

Connects to Neurosity Crown headset via WiFi.

**Requirements:**
- Neurosity SDK: `pip install neurosity`
- Credentials in `.env` file in the package directory

**Usage:**
```bash
ros2 run neurosity_driver neurosity_driver
```

**Configuration:**
Create a `.env` file in `ros2_hc_drv/neurosity_driver/` with:
```
NEUROSITY_DEVICE_ID=your-device-id
NEUROSITY_EMAIL=your-email@example.com
NEUROSITY_PASSWORD=your-password
```

### 3. OpenBCI Driver (ROS2 Package)
Located in `ros2_hc_drv/openbci_driver/`

Connects to OpenBCI Cyton board via USB serial.

**Requirements:**
- OpenBCI library: `pip install openbci-python`
- USB serial connection to OpenBCI board

**Usage:**
```bash
# 8 channels (Cyton only)
ros2 run openbci_driver openbci_driver --ros-args -p port:=/dev/ttyUSB0 -p channel_count:=8

# 16 channels (Cyton + Daisy)
ros2 run openbci_driver openbci_driver --ros-args -p port:=/dev/ttyUSB0 -p channel_count:=16
```

## Standardized Topics

All drivers publish to:
- `/eeg/raw` - Raw EEG data (healthcare_msgs/EEG)
- `/eeg/raw_info` - Metadata with latching QoS (healthcare_msgs/EEGInfo)

## Integration with Pipeline

These drivers are integrated into the main `launch/start.sh` script:

```bash
# Use simulator (default)
./launch/start.sh

# Use OpenBCI device
USE_ACQUISITION=1 OPENBCI_PORT=/dev/ttyUSB0 OPENBCI_CHANNELS=8 ./launch/start.sh

# Use Neurosity device
USE_ACQUISITION=2 ./launch/start.sh
```

## Adding New Drivers

To add a new EEG device driver:

1. Create a ROS2 package in `ros2_hc_drv/new_device_driver/`
2. Implement a ROS2 node that publishes to:
   - `/eeg/raw` with EEG messages
   - `/eeg/raw_info` with EEGInfo metadata (use latching QoS)
3. Follow the pattern in `neurosity_driver` or `openbci_driver`
4. Add integration to `launch/start.sh`
5. Update this README

**Key requirements:**
- Use `QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL)` for EEGInfo
- Publish EEGInfo once after first data message
- Include proper error handling and logging
