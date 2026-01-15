import json
import matplotlib.pyplot as plt
import numpy as np

# Path to the saved EEG data file
DATA_PATH = '/home/tjalf/neurosity_logs/eeg_data.jsonl'

raw_eeg = []
preprocessed_eeg = []

# Read the first 100 messages (or fewer if file is short)
with open(DATA_PATH, 'r') as f:
    for i, line in enumerate(f):
        if i >= 100:
            break
        msg = json.loads(line)
        # Raw EEG
        raw_eeg.extend(msg['eeg'])
        # Simulate preprocessed EEG (bandpass + notch) by applying a simple filter
        # For demo: use a moving average as a placeholder for preprocessing
        arr = np.array(msg['eeg'])
        preprocessed = np.convolve(arr, np.ones(5)/5, mode='same')
        preprocessed_eeg.extend(preprocessed)

# Plot comparison
plt.figure(figsize=(15, 6))
plt.plot(raw_eeg, label='Raw EEG', alpha=0.7)
plt.plot(preprocessed_eeg, label='Preprocessed EEG', alpha=0.7)
plt.title('Comparison of Raw and Preprocessed EEG Data')
plt.xlabel('Sample Index')
plt.ylabel('EEG Value (uV)')
plt.legend()
plt.tight_layout()
plt.show()
