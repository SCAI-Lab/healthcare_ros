import json
import matplotlib.pyplot as plt
import numpy as np

DATA_PATH = '/home/tjalf/neurosity_logs/eeg_data.jsonl'
NUM_CHANNELS = 4
SAMPLES_TO_PLOT = 256  # Show only the first second (if sampling rate is 256 Hz)

# Read one message and extract per-channel data
with open(DATA_PATH, 'r') as f:
    first_msg = json.loads(next(f))
    eeg = np.array(first_msg['eeg'])
    sample_size = first_msg['sample_size']
    # Reshape to (channels, samples)
    eeg_channels = eeg.reshape(NUM_CHANNELS, sample_size)
    # Preprocess: simple moving average
    preprocessed_channels = np.array([
        np.convolve(eeg_channels[ch], np.ones(5)/5, mode='same')
        for ch in range(NUM_CHANNELS)
    ])

# Plot each channel
fig, axes = plt.subplots(NUM_CHANNELS, 1, figsize=(10, 8), sharex=True)
for ch in range(NUM_CHANNELS):
    axes[ch].plot(eeg_channels[ch][:SAMPLES_TO_PLOT], label=f'Raw Channel {ch+1}')
    axes[ch].plot(preprocessed_channels[ch][:SAMPLES_TO_PLOT], label=f'Preprocessed Channel {ch+1}')
    axes[ch].set_ylabel('uV')
    axes[ch].legend(loc='upper right')
axes[-1].set_xlabel('Sample Index')
plt.suptitle('EEG Channels: Raw vs Preprocessed (First Message)')
plt.tight_layout(rect=[0, 0.03, 1, 0.95])
plt.show()
