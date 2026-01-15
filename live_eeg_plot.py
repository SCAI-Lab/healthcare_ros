#!/usr/bin/env python3
"""
Live EEG Data Plotter for ROS2

Subscribes to /neurosity/eeg (raw) and /neurosity/eeg_processed (preprocessed)
using healthcare_msgs/msg/EEG and plots both in real time for comparison.
"""
import rclpy
from rclpy.node import Node
from healthcare_msgs.msg import EEG
import numpy as np
import matplotlib.pyplot as plt
from collections import deque

# Settings
BUFFER_SIZE = 1024  # Number of samples to keep in buffer
CHANNELS = 4        # Number of EEG channels (adjust if needed)
SAMPLE_RATE = 256   # Hz (adjust if needed)

class EEGPlotter(Node):
    def __init__(self):
        super().__init__('eeg_live_plotter')
        self.raw_buffer = [deque(maxlen=BUFFER_SIZE) for _ in range(CHANNELS)]
        self.proc_buffer = [deque(maxlen=BUFFER_SIZE) for _ in range(CHANNELS)]
        self.channel_names = ['FP1', 'FP2', 'F3', 'F4'][:CHANNELS]

        self.create_subscription(EEG, '/neurosity/eeg', self.raw_callback, 10)
        self.create_subscription(EEG, '/neurosity/eeg_processed', self.proc_callback, 10)

        self.fig, self.axes = plt.subplots(CHANNELS, 1, figsize=(12, 8), sharex=True)
        if CHANNELS == 1:
            self.axes = [self.axes]
        self.lines_raw = []
        self.lines_proc = []
        for ax in self.axes:
            line_raw, = ax.plot([], [], label='Raw', color='steelblue')
            line_proc, = ax.plot([], [], label='Preprocessed', color='orange')
            self.lines_raw.append(line_raw)
            self.lines_proc.append(line_proc)
            ax.legend(loc='upper right')
            ax.grid(True, alpha=0.3)
        self.fig.suptitle('Live EEG: Raw vs Preprocessed')
        plt.tight_layout()
        self.timer = self.create_timer(0.1, self.update_plot)

    def raw_callback(self, msg):
        self._update_buffer(self.raw_buffer, msg)

    def proc_callback(self, msg):
        self._update_buffer(self.proc_buffer, msg)

    def _update_buffer(self, buffer, msg):
        # msg.eeg is a flattened array: [ch1, ch2, ch3, ch4, ...]
        n_ch = msg.channels if hasattr(msg, 'channels') else CHANNELS
        n_samples = msg.sample_size if hasattr(msg, 'sample_size') else len(msg.eeg) // n_ch
        arr = np.array(msg.eeg)
        for ch in range(n_ch):
            start = ch * n_samples
            end = start + n_samples
            buffer[ch].extend(arr[start:end])

    def update_plot(self):
        t = np.arange(BUFFER_SIZE) / SAMPLE_RATE
        for ch in range(CHANNELS):
            raw = np.array(self.raw_buffer[ch])
            proc = np.array(self.proc_buffer[ch])
            self.lines_raw[ch].set_data(t[-len(raw):], raw)
            self.lines_proc[ch].set_data(t[-len(proc):], proc)
            self.axes[ch].set_xlim(max(0, t[-len(raw):][0]), t[-1])
            all_data = np.concatenate([raw, proc]) if len(proc) > 0 else raw
            if len(all_data) > 0:
                self.axes[ch].set_ylim(np.min(all_data)-5, np.max(all_data)+5)
            self.axes[ch].set_ylabel(self.channel_names[ch])
        self.axes[-1].set_xlabel('Time (s)')
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()


def main(args=None):
    rclpy.init(args=args)
    plt.ion()
    node = EEGPlotter()
    try:
        plt.show(block=True)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
