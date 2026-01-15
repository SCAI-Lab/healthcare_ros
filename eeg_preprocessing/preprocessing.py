#!/usr/bin/env python3
"""Non-interactive EEG Preprocessing ROS2 node.

This module implements a lightweight preprocessing node that subscribes to
`/neurosity/eeg` (type: `healthcare_msgs.msg.EEG`), optionally applies a
band-pass filter and downsampling, rounds values to reduce payload size, and
publishes the processed messages on a configurable topic (default
`/neurosity/eeg_processed`).

This file intentionally contains no console prompts or interactive input so it
can be used inside headless deployments and ROS launch scripts.
"""

from __future__ import annotations

import math
from typing import List, Tuple

import numpy as np
from scipy.signal import butter, filtfilt, decimate

import rclpy
from rclpy.node import Node

from healthcare_msgs.msg import EEG


def _butter_bandpass_filter(data: np.ndarray, l_freq: float, h_freq: float, fs: float, order: int = 4) -> np.ndarray:
    nyq = 0.5 * fs
    if l_freq <= 0 or h_freq <= 0 or l_freq >= h_freq or h_freq >= nyq:
        return data
    b, a = butter(order, [l_freq / nyq, h_freq / nyq], btype="band")
    # apply along axis=1 (time axis) if 2D (channels x samples)
    if data.ndim == 1:
        return filtfilt(b, a, data)
    else:
        return np.vstack([filtfilt(b, a, row) for row in data])


def _reshape_eeg(eeg_list: List[float], sample_size: int) -> Tuple[np.ndarray, int]:
    arr = np.asarray(eeg_list, dtype=float)
    if sample_size and sample_size > 0 and len(arr) % sample_size == 0:
        channels = len(arr) // sample_size
        return arr.reshape((channels, sample_size)), sample_size
    # fallback: treat as single channel
    return arr.reshape((1, -1)), arr.shape[0]


class EEGPreprocessor(Node):
    def __init__(self):
        super().__init__("eeg_preprocessor")

        # Parameters (defaults chosen to match simulator/typical EEG)
        self.declare_parameter("bandpass_enabled", True)
        self.declare_parameter("l_freq", 1.0)
        self.declare_parameter("h_freq", 40.0)
        self.declare_parameter("sampling_rate", 256.0)
        self.declare_parameter("downsample_factor", 1)
        self.declare_parameter("round_precision", 3)
        self.declare_parameter("publish_topic", "/neurosity/eeg_processed")

        self.bandpass_enabled = self.get_parameter("bandpass_enabled").value
        self.l_freq = float(self.get_parameter("l_freq").value)
        self.h_freq = float(self.get_parameter("h_freq").value)
        self.sampling_rate = float(self.get_parameter("sampling_rate").value)
        self.downsample_factor = int(self.get_parameter("downsample_factor").value)
        self.round_precision = int(self.get_parameter("round_precision").value)
        self.publish_topic = str(self.get_parameter("publish_topic").value)

        self.pub = self.create_publisher(EEG, self.publish_topic, 10)
        self.sub = self.create_subscription(EEG, "/neurosity/eeg", self._on_eeg, 10)

        self.get_logger().info(f"EEGPreprocessor initialized. Publishing to: {self.publish_topic}")

    def _on_eeg(self, msg: EEG) -> None:
        try:
            eeg_array, sample_size = _reshape_eeg(list(msg.eeg), int(msg.sample_size))

            # eeg_array shape: (channels, samples)
            if self.bandpass_enabled:
                eeg_array = _butter_bandpass_filter(eeg_array, self.l_freq, self.h_freq, self.sampling_rate)

            if self.downsample_factor and self.downsample_factor > 1:
                # decimate along time axis
                eeg_array = decimate(eeg_array, self.downsample_factor, axis=1, zero_phase=True)

            # Round to reduce payload size
            if self.round_precision >= 0:
                factor = 10 ** self.round_precision
                eeg_array = np.round(eeg_array * factor) / factor

            # Prepare new message preserving header/session_id
            out = EEG()
            out.header = msg.header
            out.session_id = msg.session_id
            out.sample_size = int(eeg_array.shape[1])
            out.eeg = [float(x) for x in eeg_array.flatten().tolist()]

            # Downsample quality if present (simple approach: average quality across grouped samples)
            try:
                quality = list(msg.quality)
                if quality:
                    # keep same length as channels; prefer per-channel quality only
                    # If original quality matched samples, resampling would be needed; here we keep channel-wise quality if possible
                    if len(quality) == eeg_array.shape[0]:
                        out.quality = [float(round(q, 2)) for q in quality]
                    else:
                        # fallback: take average quality and duplicate per channel
                        avgq = float(round(sum(map(float, quality)) / max(len(quality), 1), 2))
                        out.quality = [avgq for _ in range(eeg_array.shape[0])]
                else:
                    out.quality = []
            except Exception:
                out.quality = []

            self.pub.publish(out)

        except Exception as e:
            self.get_logger().error(f"Error processing EEG message: {e}")


def main(args=None):
    rclpy.init(args=args)
    node = EEGPreprocessor()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("Shutting down EEGPreprocessor")
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
