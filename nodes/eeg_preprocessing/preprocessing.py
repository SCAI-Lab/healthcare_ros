#!/usr/bin/env python3
"""Non-interactive EEG Preprocessing ROS2 node.

This module implements a lightweight preprocessing node that subscribes to
`/eeg/raw` (type: `healthcare_msgs.msg.EEG`), optionally applies a
band-pass filter and downsampling, rounds values to reduce payload size, and
publishes the processed messages on a configurable topic (default
`/eeg/processed`).

This file intentionally contains no console prompts or interactive input so it
can be used inside headless deployments and ROS launch scripts.
"""

from __future__ import annotations


from typing import List, Tuple


import numpy as np
from scipy.signal import decimate

# Import EEGPreprocessingTools with absolute import for direct script execution
from nodes.eeg_preprocessing.preprocessing_tools import EEGPreprocessingTools

import rclpy
from rclpy.node import Node

from healthcare_msgs.msg import EEG  # Importing EEG message from healthcare_msgs



class EEGPreprocessor(Node):
    """
    ROS2 node for non-interactive EEG preprocessing.

    Subscribes to /eeg/raw (healthcare_msgs.msg.EEG), applies band-pass filtering,
    common average referencing, downsampling, and rounding, then publishes processed data to /eeg/processed (configurable).
    """
    def __init__(self):
        """
        Initialize EEGPreprocessor node, declare parameters, and set up publisher/subscriber.
        """
        super().__init__("eeg_preprocessor")

        # Declare parameters with defaults
        # Bandpass filtering is always enabled
        self.declare_parameter("l_freq", 0.5)  # Set default to 0.5 Hz
        self.declare_parameter("h_freq", 45.0) # Set default to 45 Hz
        self.declare_parameter("sampling_rate", 256.0)
        self.declare_parameter("downsample_factor", 1)
        self.declare_parameter("round_precision", 3)
        self.declare_parameter("publish_topic", "/eeg/processed")

        # Load parameters
        self.l_freq = float(self.get_parameter("l_freq").value)
        self.h_freq = float(self.get_parameter("h_freq").value)
        self.sampling_rate = float(self.get_parameter("sampling_rate").value)
        self.downsample_factor = int(self.get_parameter("downsample_factor").value)
        self.round_precision = int(self.get_parameter("round_precision").value)
        self.publish_topic = str(self.get_parameter("publish_topic").value)

        # Set up publisher and subscriber
        self.pub = self.create_publisher(EEG, self.publish_topic, 10)
        self.sub = self.create_subscription(EEG, "/eeg/raw", self._on_eeg, 10)

        # Initialize preprocessing tools
        self.tools = EEGPreprocessingTools()

        self.get_logger().info(f"EEGPreprocessor initialized. Subscribing to: /eeg/raw, Publishing to: {self.publish_topic}")

    def _on_eeg(self, msg: EEG) -> None:
        """
        Callback for incoming EEG messages. Applies preprocessing steps and publishes processed data.

        Steps:
            1. Reshape EEG data to (channels, samples).
            2. Optionally apply band-pass filter (0.5-45 Hz by default).
            3. Apply common average reference.
            4. Optionally downsample.
            5. Optionally round values to reduce payload size.
            6. Prepare and publish processed EEG message.
        """
        try:
            # Reshape EEG data using tools class
            eeg_array, sample_size = self.tools.reshape_eeg(list(msg.eeg), int(msg.sample_size))

            # Always apply band-pass filter (0.5-45 Hz by default)
            eeg_array = self.tools.band_filter(
                eeg_array,
                lower=self.l_freq,
                middle_1=self.h_freq,
                middle_2=self.h_freq,  # No split, just use as upper
                upper=self.h_freq,
                combine_bands=False
            )

            # Apply common average reference using preprocessing tools
            eeg_array = self.tools.set_common_average_as_reference(eeg_array)

            if self.downsample_factor and self.downsample_factor > 1:
                # Decimate along time axis (reduces sample count)
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
                    # Prefer per-channel quality if possible
                    if len(quality) == eeg_array.shape[0]:
                        out.quality = [float(round(q, 2)) for q in quality]
                    else:
                        # Fallback: take average quality and duplicate per channel
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
    """
    Entry point for EEGPreprocessor node.
    Initializes ROS2, starts node, and handles shutdown.
    """
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
