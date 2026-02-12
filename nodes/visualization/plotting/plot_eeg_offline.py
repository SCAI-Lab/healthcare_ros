#!/usr/bin/env python3
"""
Enhanced EEG Offline Plotting Script

This script can read EEG data from multiple sources:
1. JSON Lines format (.jsonl files)
2. ROS bag MCAP format (rosbag2 recordings)

It plots raw vs preprocessed EEG data for comparison.
"""

import json
import matplotlib.pyplot as plt
import numpy as np
import os
import sys
from pathlib import Path


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


def load_from_jsonl(file_path, channels_to_plot, samples_to_plot, num_channels=4):
    """
    Load EEG data from JSONL file.
    Returns a list of lists containing data for each selected channel.
    """
    eeg_data = [[] for _ in channels_to_plot]
    samples_read = 0
    
    if not os.path.exists(file_path):
        print(f"Warning: JSONL file not found: {file_path}")
        return None
    
    with open(file_path, 'r') as f:
        for line in f:
            if samples_read >= samples_to_plot:
                break
            msg = json.loads(line)
            # Reshape flat EEG data to channels x samples
            eeg_flat = msg['eeg']
            sample_size = msg['sample_size']
            eeg_reshaped = np.array(eeg_flat).reshape(num_channels, sample_size)
            for idx, ch in enumerate(channels_to_plot):
                eeg_data[idx].extend(eeg_reshaped[ch])
            samples_read += sample_size
    
    return eeg_data


def load_from_rosbag(bag_dir, topic_name, channels_to_plot, samples_to_plot, num_channels=4):
    """
    Load EEG data from ROS bag (MCAP format).
    Returns a list of lists containing data for each selected channel.
    """
    try:
        from rosbag2_py import SequentialReader, StorageOptions, ConverterOptions
        from rclpy.serialization import deserialize_message
        from healthcare_msgs.msg import EEG
    except ImportError as e:
        print(f"Error: Failed to import ROS bag dependencies: {e}")
        print("Make sure rosbag2_py and healthcare_msgs are available.")
        return None
    
    if not os.path.exists(bag_dir):
        print(f"Warning: ROS bag directory not found: {bag_dir}")
        return None
    
    # Find the MCAP file in the directory
    mcap_files = list(Path(bag_dir).glob("*.mcap"))
    if not mcap_files:
        print(f"Warning: No MCAP files found in {bag_dir}")
        return None
    
    # Use the directory path for storage_options (rosbag2 format)
    storage_options = StorageOptions(uri=str(bag_dir), storage_id='mcap')
    converter_options = ConverterOptions(
        input_serialization_format='cdr',
        output_serialization_format='cdr'
    )
    
    reader = SequentialReader()
    
    try:
        reader.open(storage_options, converter_options)
    except RuntimeError:
        # If directory-based reading fails, try direct MCAP file reading
        print(f"Attempting direct MCAP file reading from {mcap_files[0]}")
        storage_options = StorageOptions(uri=str(mcap_files[0]), storage_id='mcap')
        try:
            reader.open(storage_options, converter_options)
        except RuntimeError as e:
            print(f"Error: Could not open MCAP file: {e}")
            print("The bag file may be corrupted or still being written to.")
            print("Try stopping the recording first or using a completed bag.")
            return None
    
    eeg_data = [[] for _ in channels_to_plot]
    samples_read = 0
    
    while reader.has_next() and samples_read < samples_to_plot:
        topic, data, timestamp = reader.read_next()
        
        if topic == topic_name:
            msg = deserialize_message(data, EEG)
            # Reshape flat EEG data to channels x samples
            eeg_flat = msg.eeg
            sample_size = msg.sample_size
            eeg_reshaped = np.array(eeg_flat).reshape(num_channels, sample_size)
            for idx, ch in enumerate(channels_to_plot):
                eeg_data[idx].extend(eeg_reshaped[ch])
            samples_read += sample_size
    
    del reader
    return eeg_data


def find_latest_rosbag(eeg_data_dir):
    """
    Find the most recent rosbag directory in the eeg_data folder.
    """
    rosbag_dirs = sorted(Path(eeg_data_dir).glob("rosbag_*"), reverse=True)
    if rosbag_dirs:
        return str(rosbag_dirs[0])
    return None


def plot_selected_channels(times, raw_eeg, preprocessed_eeg, channel_names, channels_to_plot, save_path=None, data_source="", sampling_rate=256):
    """
    Plot raw and preprocessed EEG data for selected channels.
    If save_path is provided, saves the figure instead of showing it.
    """
    # Increase figure size for better visibility
    plt.figure(figsize=(20, 10))
    
    # Set larger font sizes globally for this figure
    plt.rcParams.update({
        'font.size': 14,
        'axes.titlesize': 16,
        'axes.labelsize': 14,
        'xtick.labelsize': 12,
        'ytick.labelsize': 12,
        'legend.fontsize': 13
    })
    
    for idx, ch in enumerate(channels_to_plot):
        plt.subplot(len(channels_to_plot), 1, idx+1)
        plt.plot(times, raw_eeg[idx], label=f'Raw {channel_names[ch]}', alpha=0.7, linewidth=1.5)
        plt.plot(times, preprocessed_eeg[idx], label=f'Preprocessed {channel_names[ch]}', alpha=0.7, linewidth=1.5)
        plt.title(f'Channel {channel_names[ch]} (Sampling Rate: {sampling_rate} Hz)', fontweight='bold')
        plt.xlabel('Time (s)', fontweight='bold')
        plt.ylabel('EEG Value (uV)', fontweight='bold')
        plt.legend(loc='upper right')
        plt.grid(True, alpha=0.3)
    
    if data_source:
        plt.suptitle(f'EEG Data Comparison - {data_source}', fontsize=18, fontweight='bold', y=0.998)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=200, bbox_inches='tight')
        print(f"Plot saved to: {save_path}")
        plt.close()
    else:
        plt.show()


def plot_eeg_data(eeg_data_dir, plots_dir, use_rosbag=False, channels_to_plot=None, 
                  seconds_to_plot=2, sampling_rate=256, num_channels=4, 
                  channel_names=None):
    """
    Main function to load and plot EEG data from either JSON or ROS bag format.
    
    Args:
        eeg_data_dir: Directory containing EEG data files
        plots_dir: Directory to save plots
        use_rosbag: If True, read from ROS bag; if False, read from JSONL
        channels_to_plot: List of channel indices to plot
        seconds_to_plot: Number of seconds of data to plot
        sampling_rate: Sampling rate in Hz
        num_channels: Total number of channels in the data
        channel_names: List of channel names
    """
    if channels_to_plot is None:
        channels_to_plot = [0, 1, 2]  # FP1, FP2, F3
    
    if channel_names is None:
        channel_names = ['FP1', 'FP2', 'F3', 'F4']
    
    samples_to_plot = sampling_rate * seconds_to_plot
    
    # Load data based on format
    if use_rosbag:
        # Find latest rosbag directory
        latest_bag = find_latest_rosbag(eeg_data_dir)
        if not latest_bag:
            print(f"Error: No rosbag directories found in {eeg_data_dir}")
            print("Please run the system with USE_ROSBAG=1 to generate bag files.")
            return False
        
        print(f"Loading data from ROS bag: {latest_bag}")
        raw_eeg = load_from_rosbag(latest_bag, '/eeg/raw', channels_to_plot, samples_to_plot, num_channels)
        preprocessed_eeg = load_from_rosbag(latest_bag, '/eeg/processed', channels_to_plot, samples_to_plot, num_channels)
        data_source = f"ROS Bag: {Path(latest_bag).name}"
    else:
        # Load from JSONL files
        raw_path = os.path.join(eeg_data_dir, 'eeg_raw_data.jsonl')
        preprocessed_path = os.path.join(eeg_data_dir, 'eeg_preprocessed_data.jsonl')
        
        if not os.path.exists(raw_path):
            print(f"Error: Raw data file not found at {raw_path}")
            print("Please run the simulator and savers first to generate data.")
            return False
        
        if not os.path.exists(preprocessed_path):
            print(f"Error: Preprocessed data file not found at {preprocessed_path}")
            print("Please run the preprocessor node first to generate processed data.")
            return False
        
        print(f"Loading data from JSONL files:")
        print(f"  Raw: {raw_path}")
        print(f"  Preprocessed: {preprocessed_path}")
        
        raw_eeg = load_from_jsonl(raw_path, channels_to_plot, samples_to_plot, num_channels)
        preprocessed_eeg = load_from_jsonl(preprocessed_path, channels_to_plot, samples_to_plot, num_channels)
        data_source = "JSONL Files"
    
    # Check if data was loaded successfully
    if raw_eeg is None or preprocessed_eeg is None:
        print("Error: Failed to load data")
        return False
    
    if not raw_eeg[0] or not preprocessed_eeg[0]:
        print("Error: No data samples found")
        return False
    
    # Create time axis
    times = np.arange(len(raw_eeg[0])) / sampling_rate
    
    # Get next plot number and save
    plot_number = get_next_plot_number(plots_dir)
    save_path = os.path.join(plots_dir, f'eeg_comparison_{plot_number:03d}.png')
    
    # Plot and save
    plot_selected_channels(times, raw_eeg, preprocessed_eeg, channel_names, 
                          channels_to_plot, save_path, data_source, sampling_rate)
    
    print(f"Successfully plotted {seconds_to_plot} seconds of EEG data")
    return True


if __name__ == "__main__":
    # Setup paths
    REPO_BASE = Path(__file__).parent.parent.parent.resolve()
    EEG_DATA_DIR = REPO_BASE / 'eeg_data'
    PLOTS_DIR = REPO_BASE / 'plots'
    
    # Determine data source from environment variable or command line
    use_rosbag = os.environ.get('USE_ROSBAG', '0') == '1'
    
    if len(sys.argv) > 1:
        if sys.argv[1] == '--rosbag':
            use_rosbag = True
        elif sys.argv[1] == '--json':
            use_rosbag = False
    
    # Channels to plot
    CHANNELS_TO_PLOT = [0, 1, 2]  # FP1, FP2, F3
    
    print("=" * 60)
    print("EEG Offline Plotting Tool")
    print("=" * 60)
    print(f"Data source: {'ROS Bag (MCAP)' if use_rosbag else 'JSONL Files'}")
    print(f"EEG data directory: {EEG_DATA_DIR}")
    print(f"Plots directory: {PLOTS_DIR}")
    print("=" * 60)
    
    # Plot the data
    success = plot_eeg_data(
        str(EEG_DATA_DIR),
        str(PLOTS_DIR),
        use_rosbag=use_rosbag,
        channels_to_plot=CHANNELS_TO_PLOT,
        seconds_to_plot=2
    )
    
    if not success:
        sys.exit(1)
