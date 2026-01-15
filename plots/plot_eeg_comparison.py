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

    SAMPLING_RATE = 256  # Hz
    # Time axis in seconds
    times = np.arange(len(raw_eeg)) / SAMPLING_RATE

    import json
    import matplotlib.pyplot as plt
    import numpy as np

    # Path to the saved EEG data file
    DATA_PATH = '/home/tjalf/neurosity_logs/eeg_data.jsonl'
    SAMPLING_RATE = 256  # Hz
    NUM_CHANNELS = 4
    CHANNEL_NAMES = ['FP1', 'FP2', 'F3', 'F4']
    CHANNELS_TO_PLOT = [0, 1, 2]  # FP1, FP2, F3
    SECONDS_TO_PLOT = 10
    SAMPLES_TO_PLOT = SAMPLING_RATE * SECONDS_TO_PLOT

    raw_eeg = [[] for _ in CHANNELS_TO_PLOT]
    preprocessed_eeg = [[] for _ in CHANNELS_TO_PLOT]

    # Read enough messages to cover the desired time window
    samples_read = 0
    with open(DATA_PATH, 'r') as f:
        for line in f:
            if samples_read >= SAMPLES_TO_PLOT:
                break
            msg = json.loads(line)
            eeg = np.array(msg['eeg'])
            sample_size = msg['sample_size']
            # Extract each channel's samples
            for idx, ch in enumerate(CHANNELS_TO_PLOT):
                ch_samples = eeg[ch::NUM_CHANNELS][:sample_size]
                raw_eeg[idx].extend(ch_samples)
                # Preprocess: moving average
                preprocessed = np.convolve(ch_samples, np.ones(5)/5, mode='same')
                preprocessed_eeg[idx].extend(preprocessed)
            samples_read += sample_size

    # Time axis in seconds
    times = np.arange(len(raw_eeg[0])) / SAMPLING_RATE

    # Plot comparison for three channels
    plt.figure(figsize=(15, 8))
    for idx, ch in enumerate(CHANNELS_TO_PLOT):
        plt.subplot(3, 1, idx+1)
        plt.plot(times, raw_eeg[idx], label=f'Raw {CHANNEL_NAMES[ch]}', alpha=0.7)
        plt.plot(times, preprocessed_eeg[idx], label=f'Preprocessed {CHANNEL_NAMES[ch]}', alpha=0.7)
        plt.title(f'Channel {CHANNEL_NAMES[ch]} (Sampling Rate: {SAMPLING_RATE} Hz)')
        plt.xlabel('Time (s)')
        plt.ylabel('EEG Value (uV)')
        plt.legend()
        plt.tight_layout()
    plt.show()
