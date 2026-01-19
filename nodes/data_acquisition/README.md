# EEG Data Acquisition Drivers

This directory contains ROS2 driver nodes for various EEG hardware devices.

## Available Drivers

### 1. Neurosity Driver (`neurosity_driver.py`)
Connects to Neurosity Crown headset via WiFi.

**Requirements:**
- Neurosity SDK: `pip install neurosity`
- Credentials in `.env` file (see below)

**Usage:**
```bash
python3 neurosity_driver.py
```

**Configuration:**
Create a `.env` file with:
```
NEUROSITY_DEVICE_ID=your-device-id
NEUROSITY_EMAIL=your-email@example.com
NEUROSITY_PASSWORD=your-password
```

### 2. OpenBCI Driver (`openbci_driver.py`)
Connects to OpenBCI Cyton board via USB serial.

**Requirements:**
- OpenBCI library: `pip install openbci-python`
- USB serial connection to OpenBCI board

**Usage:**
```bash
# 8 channels (default)
python3 openbci_driver.py --port /dev/ttyUSB0 --channels 8

# 16 channels (with daisy board)
python3 openbci_driver.py --port /dev/ttyUSB0 --channels 16
```

**Command line arguments:**
- `--port`: Serial port (default: `/dev/ttyUSB0`)
- `--channels`: Number of channels: 8 or 16 (default: 8)

## Standardized Topics

All drivers publish to:
- `/eeg/raw` - Raw EEG data (healthcare_msgs/EEG)
- `/eeg/raw_info` - Metadata with latching QoS (healthcare_msgs/EEGInfo)

## Integration with Pipeline

These drivers are integrated into the main `launch/start.sh` script:

```bash
# Use Neurosity device
./launch/start.sh

# Use OpenBCI device
USE_OPENBCI=1 OPENBCI_PORT=/dev/ttyUSB0 OPENBCI_CHANNELS=8 ./launch/start.sh

# Use simulator (no hardware)
SIMULATE=1 ./launch/start.sh
```

## Adding New Drivers

To add a new EEG device driver:

1. Create `new_device_driver.py` in this directory
2. Implement a ROS2 node that publishes to:
   - `/eeg/raw` with EEG messages
   - `/eeg/raw_info` with EEGInfo metadata (use latching QoS)
3. Follow the pattern in existing drivers
4. Update this README

**Key requirements:**
- Use `QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL)` for EEGInfo
- Publish EEGInfo once after first data message
- Include proper error handling and logging
