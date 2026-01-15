#!/usr/bin/env python3
"""
Offline EEG plotting script: Reads JSONL EEG data and plots using matplotlib.
"""
import json
import matplotlib.pyplot as plt
from pathlib import Path
import sys

log_dir = Path.home() / 'neurosity_logs'
data_file = log_dir / 'eeg_data.jsonl'

if not data_file.exists():
    print(f"No EEG data file found at {data_file}")
    sys.exit(1)

# Read all messages
with open(data_file, 'r') as f:
    messages = [json.loads(line) for line in f if line.strip()]

if not messages:
    print("No EEG data found in file.")
    sys.exit(1)

# Plot EEG for the first channel as an example
SAMPLING_RATE = 256  # Hz (adjust if your simulator uses a different rate)
samples = []
for msg in messages:
    eeg = msg['eeg']
    sample_size = msg['sample_size']
    # Assume 4 channels, interleaved
    ch1 = eeg[0:len(eeg):4]
    samples.extend(ch1)

times = [i / SAMPLING_RATE for i in range(len(samples))]

plt.figure(figsize=(12, 4))
plt.plot(times, samples)
plt.title(f'EEG Channel 1 (Offline Plot) - Sampling Rate: {SAMPLING_RATE} Hz')
plt.xlabel('Time (s)')
plt.ylabel('Amplitude (uV)')
plt.tight_layout()
plt.show()
