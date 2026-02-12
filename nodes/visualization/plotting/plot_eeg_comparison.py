#!/usr/bin/env python3
"""
EEG Comparison Visualization - Offline Plotting Tool

Generates comparison plots of raw vs preprocessed EEG data from JSONL files.
Useful for validating preprocessing quality and visualizing EEG signal characteristics.

Features:
- Side-by-side comparison of raw and processed signals
- Multi-channel plotting (default: 4 channels - FP1, FP2, F3, F4)
- Configurable time windows (default: 10 seconds)
- Auto-numbering of output SVG files
- High-quality vector graphics (SVG format)

Data Source:
- Raw data: eeg_data/eeg_raw_data.jsonl
- Preprocessed data: eeg_data/eeg_preprocessed_data.jsonl

Output:
- Plots saved to: plots/eeg_comparison_XXX.svg
- Auto-increments file numbers to avoid overwrites

Usage:
    # Basic usage (plots first 10 seconds of all 4 channels):
    python3 plot_eeg_comparison.py
    
    # Via start.sh:
    VISUALIZATION_MODE=comparison ./launch/start.sh
    
Configuration:
- channels_to_plot: [0, 1, 2, 3] for all channels or subset like [0, 2]
- seconds_to_plot: Duration to plot (default: 10s)
- sampling_rate: Should match simulator/hardware (default: 150 Hz)

Requirements:
    matplotlib, numpy, json (all available in hcmd-venv)
"""

import os
import json
import numpy as np
import matplotlib.pyplot as plt

def get_next_plot_number(plots_dir):
    """
    Find the next available plot number by checking existing files.
    Returns incremented number to avoid overwriting plots.
    """
    if not os.path.exists(plots_dir):
        os.makedirs(plots_dir)
        return 1
    
    existing_files = [f for f in os.listdir(plots_dir) if f.startswith('eeg_comparison_') and f.endswith('.svg')]
    if not existing_files:
        return 1
    
    # Extract numbers from filenames
    numbers = []
    for f in existing_files:
        try:
            num = int(f.replace('eeg_comparison_', '').replace('.svg', ''))
            numbers.append(num)
        except ValueError:
            continue
    
    return max(numbers) + 1 if numbers else 1

def plot_selected_channels(times, raw_eeg, preprocessed_eeg, channel_names, channels_to_plot, save_path=None, sampling_rate=150):
    """
    Plot raw and preprocessed EEG data for selected channels.
    
    Args:
        times: Time array in seconds
        raw_eeg: List of raw EEG data arrays (one per channel)
        preprocessed_eeg: List of preprocessed EEG data arrays (one per channel)
        channel_names: List of channel names (e.g., ['FP1', 'FP2', 'F3', 'F4'])
        channels_to_plot: Indices of channels to plot
    """
    plt.figure(figsize=(15, 8))
    for idx, ch in enumerate(channels_to_plot):
        plt.subplot(len(channels_to_plot), 1, idx+1)
        plt.plot(times, raw_eeg[idx], label=f'Raw {channel_names[ch]}', alpha=0.7, linewidth=2)
        plt.plot(times, preprocessed_eeg[idx], label=f'Preprocessed {channel_names[ch]}', alpha=0.7, linewidth=2)
        plt.title(f'Channel {channel_names[ch]} (Sampling Rate: {sampling_rate} Hz)', fontsize=18, fontweight='bold')
        plt.xlabel('Time (s)', fontsize=16, fontweight='bold')
        plt.ylabel('EEG Value (uV)', fontsize=16, fontweight='bold')
        plt.legend(fontsize=14, loc='best')
        plt.tick_params(axis='both', which='major', labelsize=14)
        plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, format='svg', bbox_inches='tight')
        print(f"Plot saved to: {save_path}")
        plt.close()
    else:
        plt.show()

def plot_raw_vs_preprocessed(raw_data_path, preprocessed_data_path, channels_to_plot, seconds_to_plot=10, sampling_rate=150, num_channels=4, channel_names=None, save_path=None):
    """
    Load JSONL data files and generate comparison plots.
    
    Args:
        raw_data_path: Path to raw EEG JSONL file
        preprocessed_data_path: Path to preprocessed EEG JSONL file
        channels_to_plot: List of channel indices to plot (e.g., [0, 1, 2, 3])
        seconds_to_plot: Duration of data to plot (default: 10 seconds)
        sampling_rate: EEG sampling rate in Hz (default: 150 Hz)
        num_channels: Total number of EEG channels (default: 4)
        channel_names: List of channel names (default: ['FP1', 'FP2', 'F3', 'F4'])
        save_path: If provided, saves plot as SVG to this path
        
    Note:
        JSONL format: Each line is a JSON object with 'eeg' (flat list) and 'sample_size' fields.
        The 'eeg' field is reshaped to (num_channels x sample_size) for processing.
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
    plot_selected_channels(times, raw_eeg, preprocessed_eeg, channel_names, channels_to_plot, save_path, sampling_rate=sampling_rate)


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
    save_path = os.path.join(PLOTS_DIR, f'eeg_comparison_{plot_number:03d}.svg')
    
    # Plot 2 seconds of data and save
    plot_raw_vs_preprocessed(RAW_DATA_PATH, PREPROCESSED_DATA_PATH, CHANNELS_TO_PLOT, 
                            seconds_to_plot=2, save_path=save_path)
