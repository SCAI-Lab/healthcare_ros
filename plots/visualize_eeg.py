#!/usr/bin/env python3
"""
EEG Data Visualization

Reads stored EEG data from eeg_data.jsonl and generates plots:
- Time-domain signals (4 channels)
- Frequency spectrum (FFT)
- Signal statistics
"""

import json
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import sys


def load_eeg_data(jsonl_file):
    """Load EEG messages from JSONL file."""
    data = []
    try:
        with open(jsonl_file, 'r') as f:
            for line in f:
                if line.strip():
                    data.append(json.loads(line))
    except FileNotFoundError:
        print(f"ERROR: File not found: {jsonl_file}")
        sys.exit(1)
    
    if not data:
        print("ERROR: No EEG data found in file")
        sys.exit(1)
    
    return data


def extract_channels(messages):
    """Extract per-channel time series from flattened messages."""
    if not messages:
        return None, 0, 0
    
    first_msg = messages[0]
    num_channels = len(first_msg['quality'])
    sample_size = first_msg['sample_size']
    
    # Initialize channels
    channels = [[] for _ in range(num_channels)]
    
    # Flatten all messages into per-channel arrays
    for msg in messages:
        eeg_data = msg['eeg']
        for ch in range(num_channels):
            # Extract channel c: eeg[c*sample_size : (c+1)*sample_size]
            start_idx = ch * sample_size
            end_idx = start_idx + sample_size
            channels[ch].extend(eeg_data[start_idx:end_idx])
    
    return channels, num_channels, sample_size


def plot_time_domain(channels, num_channels, sampling_rate=256):
    """Plot time-domain EEG signals."""
    fig, axes = plt.subplots(num_channels, 1, figsize=(14, 10))
    if num_channels == 1:
        axes = [axes]
    
    channel_names = ['FP1', 'FP2', 'F3', 'F4'][:num_channels]
    
    for ch_idx, ax in enumerate(axes):
        signal = np.array(channels[ch_idx])
        time = np.arange(len(signal)) / sampling_rate
        
        ax.plot(time, signal, linewidth=0.8, color='steelblue')
        ax.set_ylabel(f'{channel_names[ch_idx]} (µV)', fontsize=10)
        ax.set_xlabel('Time (s)', fontsize=10)
        ax.grid(True, alpha=0.3)
        ax.set_title(f'EEG Channel {channel_names[ch_idx]}', fontsize=11, fontweight='bold')
    
    plt.tight_layout()
    return fig


def plot_frequency_spectrum(channels, num_channels, sampling_rate=256):
    """Plot frequency spectrum (FFT) for each channel."""
    fig, axes = plt.subplots(num_channels, 1, figsize=(14, 10))
    if num_channels == 1:
        axes = [axes]
    
    channel_names = ['FP1', 'FP2', 'F3', 'F4'][:num_channels]
    
    for ch_idx, ax in enumerate(axes):
        signal = np.array(channels[ch_idx])
        
        # Compute FFT
        fft_vals = np.fft.fft(signal)
        freqs = np.fft.fftfreq(len(signal), 1 / sampling_rate)
        
        # Keep positive frequencies only
        positive_freqs = freqs[:len(freqs) // 2]
        magnitude = np.abs(fft_vals[:len(fft_vals) // 2])
        
        ax.semilogy(positive_freqs, magnitude, linewidth=1.0, color='darkgreen')
        ax.set_ylabel('Magnitude (log)', fontsize=10)
        ax.set_xlabel('Frequency (Hz)', fontsize=10)
        ax.grid(True, alpha=0.3, which='both')
        ax.set_title(f'Frequency Spectrum: {channel_names[ch_idx]}', fontsize=11, fontweight='bold')
        ax.set_xlim([0, 50])  # Show up to 50 Hz (typical EEG range)
        
        # Add frequency band markers
        ax.axvline(4, color='red', linestyle='--', alpha=0.5, linewidth=1, label='Theta (4 Hz)')
        ax.axvline(8, color='orange', linestyle='--', alpha=0.5, linewidth=1, label='Alpha (8 Hz)')
        ax.axvline(13, color='purple', linestyle='--', alpha=0.5, linewidth=1, label='Beta (13 Hz)')
        if ch_idx == 0:
            ax.legend(loc='upper right', fontsize=8)
    
    plt.tight_layout()
    return fig


def print_statistics(messages, channels, num_channels):
    """Print basic statistics."""
    print("\n" + "=" * 70)
    print("EEG DATA STATISTICS")
    print("=" * 70)
    print(f"Total messages: {len(messages)}")
    print(f"Channels: {num_channels}")
    print(f"Samples per message: {messages[0]['sample_size']}")
    print(f"Total data points: {sum(len(ch) for ch in channels)}")
    
    channel_names = ['FP1', 'FP2', 'F3', 'F4'][:num_channels]
    
    print("\nPer-channel statistics:")
    print(f"{'Channel':<12} {'Mean (µV)':<15} {'Std (µV)':<15} {'Min (µV)':<15} {'Max (µV)':<15}")
    print("-" * 70)
    
    for ch_idx, signal in enumerate(channels):
        signal_arr = np.array(signal)
        mean = np.mean(signal_arr)
        std = np.std(signal_arr)
        min_val = np.min(signal_arr)
        max_val = np.max(signal_arr)
        
        print(f"{channel_names[ch_idx]:<12} {mean:<15.2f} {std:<15.2f} {min_val:<15.2f} {max_val:<15.2f}")
    
    print("=" * 70 + "\n")


def main():
    # Default data file
    data_file = Path.home() / 'neurosity_logs' / 'eeg_data.jsonl'
    
    if len(sys.argv) > 1:
        data_file = Path(sys.argv[1])
    
    print(f"Loading EEG data from: {data_file}")
    
    # Load and process data
    messages = load_eeg_data(data_file)
    channels, num_channels, sample_size = extract_channels(messages)
    
    print(f"Loaded {len(messages)} EEG messages, {num_channels} channels")
    
    # Print statistics
    print_statistics(messages, channels, num_channels)
    
    # Create plots
    print("Generating time-domain plot...")
    fig_time = plot_time_domain(channels, num_channels)
    
    print("Generating frequency spectrum plot...")
    fig_freq = plot_frequency_spectrum(channels, num_channels)
    
    # Save plots
    output_dir = Path.home() / 'neurosity_logs'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    time_plot = output_dir / 'eeg_time_domain.png'
    freq_plot = output_dir / 'eeg_frequency_spectrum.png'
    
    fig_time.savefig(time_plot, dpi=150, bbox_inches='tight')
    print(f"Saved: {time_plot}")
    
    fig_freq.savefig(freq_plot, dpi=150, bbox_inches='tight')
    print(f"Saved: {freq_plot}")
    
    # Show plots
    print("\nDisplaying plots...")
    plt.show()


if __name__ == '__main__':
    main()
