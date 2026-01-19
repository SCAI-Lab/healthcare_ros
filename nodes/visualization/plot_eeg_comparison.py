def get_next_plot_number(plots_dir):
    """
    Find the next available plot number by checking existing files.
    """
    if not os.path.exists(plots_dir):
        os.makedirs(plots_dir)
        return 1
    
    existing_files = [f for f in os.listdir(plots_dir) if f.startswith('eeg_comparison_') and f.endswith('.png')]
    if not existing_files:
        return 1
    
    # Extract numbers from filenames
    numbers = []
    for f in existing_files:
        try:
            num = int(f.replace('eeg_comparison_', '').replace('.png', ''))
            numbers.append(num)
        except ValueError:
            continue
    
    return max(numbers) + 1 if numbers else 1

def plot_selected_channels(times, raw_eeg, preprocessed_eeg, channel_names, channels_to_plot, save_path=None):
    """
    Plot raw and preprocessed EEG data for selected channels.
    If save_path is provided, saves the figure instead of showing it.
    """
    plt.figure(figsize=(15, 8))
    for idx, ch in enumerate(channels_to_plot):
        plt.subplot(len(channels_to_plot), 1, idx+1)
        plt.plot(times, raw_eeg[idx], label=f'Raw {channel_names[ch]}', alpha=0.7)
        plt.plot(times, preprocessed_eeg[idx], label=f'Preprocessed {channel_names[ch]}', alpha=0.7)
        plt.title(f'Channel {channel_names[ch]} (Sampling Rate: 256 Hz)')
        plt.xlabel('Time (s)')
        plt.ylabel('EEG Value (uV)')
        plt.legend()
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Plot saved to: {save_path}")
        plt.close()
    else:
        plt.show()

def plot_raw_vs_preprocessed(raw_data_path, preprocessed_data_path, channels_to_plot, seconds_to_plot=10, sampling_rate=256, num_channels=4, channel_names=None, save_path=None):
    """
    Load data and plot raw vs preprocessed for selected channels and time window.
    Reads raw data from raw_data_path and preprocessed data from preprocessed_data_path.
    Each line in the JSONL files should have 'eeg' field as a flat list that needs reshaping.
    If save_path is provided, saves the plot instead of displaying it.
    """
    channel_names = channel_names or ['FP1', 'FP2', 'F3', 'F4']
    samples_to_plot = sampling_rate * seconds_to_plot
    raw_eeg = [[] for _ in channels_to_plot]
    preprocessed_eeg = [[] for _ in channels_to_plot]
    samples_read = 0
    
    # Read raw data
    with open(raw_data_path, 'r') as f:
        for line in f:
            if samples_read >= samples_to_plot:
                break
            msg = json.loads(line)
            # Reshape flat EEG data to channels x samples
            eeg_flat = msg['eeg']
            sample_size = msg['sample_size']
            eeg_reshaped = np.array(eeg_flat).reshape(num_channels, sample_size)
            for idx, ch in enumerate(channels_to_plot):
                raw_eeg[idx].extend(eeg_reshaped[ch])
            samples_read += sample_size
    
    # Read preprocessed data
    samples_read = 0
    with open(preprocessed_data_path, 'r') as f:
        for line in f:
            if samples_read >= samples_to_plot:
                break
            msg = json.loads(line)
            # Reshape flat EEG data to channels x samples
            eeg_flat = msg['eeg']
            sample_size = msg['sample_size']
            eeg_reshaped = np.array(eeg_flat).reshape(num_channels, sample_size)
            for idx, ch in enumerate(channels_to_plot):
                preprocessed_eeg[idx].extend(eeg_reshaped[ch])
            samples_read += sample_size
    
    times = np.arange(len(raw_eeg[0])) / sampling_rate
    plot_selected_channels(times, raw_eeg, preprocessed_eeg, channel_names, channels_to_plot, save_path)


"""
EEG Comparison Plotting Script

This script loads raw and preprocessed EEG data from a JSONL file and plots a comparison for selected channels.
Update DATA_PATH to match your workspace structure.
"""

import json
import matplotlib.pyplot as plt
import numpy as np




# Path to the saved EEG data files
import os
REPO_BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LOGS_DIR = os.path.join(REPO_BASE, 'logs')
EEG_DATA_DIR = os.path.join(REPO_BASE, 'eeg_data')
PLOTS_DIR = os.path.join(REPO_BASE, 'plots')

# Both raw and preprocessed data are in eeg_data/
RAW_DATA_PATH = os.path.join(EEG_DATA_DIR, 'eeg_raw_data.jsonl')
PREPROCESSED_DATA_PATH = os.path.join(EEG_DATA_DIR, 'eeg_preprocessed_data.jsonl')










if __name__ == "__main__":
    # Example usage: plot using functions
    CHANNELS_TO_PLOT = [0, 1, 2]  # FP1, FP2, F3
    
    # Check if data files exist
    if not os.path.exists(RAW_DATA_PATH):
        print(f"Error: Raw data file not found at {RAW_DATA_PATH}")
        print("Please run the simulator and savers first to generate data.")
        exit(1)
    
    if not os.path.exists(PREPROCESSED_DATA_PATH):
        print(f"Error: Preprocessed data file not found at {PREPROCESSED_DATA_PATH}")
        print("Please run the preprocessor node first to generate processed data.")
        exit(1)
    
    print(f"Loading raw data from: {RAW_DATA_PATH}")
    print(f"Loading preprocessed data from: {PREPROCESSED_DATA_PATH}")
    
    # Get next plot number and save to plots/ directory
    plot_number = get_next_plot_number(PLOTS_DIR)
    save_path = os.path.join(PLOTS_DIR, f'eeg_comparison_{plot_number:03d}.png')
    
    # Plot 2 seconds of data and save
    plot_raw_vs_preprocessed(RAW_DATA_PATH, PREPROCESSED_DATA_PATH, CHANNELS_TO_PLOT, 
                            seconds_to_plot=2, save_path=save_path)
