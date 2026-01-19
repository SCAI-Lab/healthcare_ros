#!/usr/bin/env python3
"""
EEG Data Acquisition Nodes

This package contains driver nodes for various EEG hardware:
- neurosity_driver.py: Neurosity headset (WiFi)
- openbci_driver.py: OpenBCI Cyton board (USB serial)

All drivers publish to standardized topics:
- /eeg/raw: Raw EEG data (healthcare_msgs/EEG)
- /eeg/raw_info: EEG metadata (healthcare_msgs/EEGInfo)
"""
