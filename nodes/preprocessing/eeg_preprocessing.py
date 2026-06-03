#!/usr/bin/env python3
"""
EEG Preprocessing Node - ROS2 Pipeline Component

Real-time EEG signal preprocessing node that applies digital filtering and
re-referencing techniques to improve signal quality. Designed for headless
deployment in automated pipelines.

Processing Pipeline
-------------------
1. Subscribe to raw EEG data from /eeg/raw
2. Apply bandpass filter (0.5-45 Hz)
3. Apply Common Average Reference (CAR)
4. Publish processed data to /eeg/processed
5. Forward metadata with preprocessing annotations

NOTE:
-----
- This version runs in **streaming mode only (no buffering)**
- **Original timestamps are preserved exactly** for end-to-end latency measurement
"""

from __future__ import annotations

import numpy as np
from scipy.signal import decimate

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, DurabilityPolicy

from healthcare_msgs.msg import EEG, EEGInfo
from eeg_preprocessing_tools import EEGPreprocessingTools


class EEGPreprocessor(Node):
    """
    ROS2 node for real-time EEG preprocessing at 150 Hz.

    Subscribes to /eeg/raw (healthcare_msgs.msg.EEG), applies clinical-grade signal processing,
    and publishes to /eeg/processed.

    Signal Processing Pipeline:
    1. Bandpass filter (0.5-45 Hz)
    2. Common Average Reference (CAR)

    IMPORTANT:
    ----------
    - No buffering
    - No timestamp modification
    - Fully compatible with ROS2 end-to-end latency measurement
    """

    def __init__(self):
        super().__init__("eeg_preprocessor")

        # Declare parameters with defaults
        self.declare_parameter("l_freq", 0.5)
        self.declare_parameter("h_freq", 45.0)
        self.declare_parameter("sampling_rate", 150.0)
        self.declare_parameter("downsample_factor", 1)
        self.declare_parameter("round_precision", 3)

        # Load parameters
        self.l_freq = float(self.get_parameter("l_freq").value)
        self.h_freq = float(self.get_parameter("h_freq").value)
        self.sampling_rate = float(self.get_parameter("sampling_rate").value)
        self.downsample_factor = int(self.get_parameter("downsample_factor").value)
        self.round_precision = int(self.get_parameter("round_precision").value)

        # State
        self.num_channels = None
        self.raw_info = None
        self.info_published = False

        # Create QoS profile with transient local durability for EEGInfo (latching)
        info_qos = QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL)

        # Set up publishers and subscribers
        self.pub = self.create_publisher(EEG, "/eeg/processed", 10)
        self.info_pub = self.create_publisher(EEGInfo, "/eeg/processed_info", qos_profile=info_qos)

        self.sub = self.create_subscription(EEG, "/eeg/raw", self._on_eeg, 10)
        self.info_sub = self.create_subscription(EEGInfo, "/eeg/raw_info", self._on_raw_info, qos_profile=info_qos)

        # Initialize preprocessing tools
        self.tools = EEGPreprocessingTools()

        self.get_logger().info("EEGPreprocessor initialized (streaming mode)")

    # ------------------------------------------------------------------
    # Metadata Handling
    # ------------------------------------------------------------------

    def _on_raw_info(self, msg: EEGInfo) -> None:
        """Store raw EEG metadata for forwarding."""
        self.raw_info = msg
        self.get_logger().info(f"Received raw EEGInfo: {msg.channel_size} channels")

    def publish_eeg_info(self):
        """
        Publish EEGInfo metadata describing the preprocessed output.
        Copies upstream metadata and adds preprocessing annotations.
        """
        info_msg = EEGInfo()

        # Copy metadata from raw EEGInfo if available
        if self.raw_info is not None:
            info_msg.device_info = self.raw_info.device_info
            info_msg.channel_size = self.raw_info.channel_size
            info_msg.units = self.raw_info.units
            info_msg.montage_type = self.raw_info.montage_type
            info_msg.electrode_sites = self.raw_info.electrode_sites
            info_msg.signal_mode = self.raw_info.signal_mode
        else:
            info_msg.channel_size = self.num_channels

        # Add preprocessing steps applied by this node
        info_msg.selected_preprocessing = [
            EEGInfo.EEG_PREPROC_BANDPASS,
            EEGInfo.EEG_PREPROC_CAR
        ]

        self.info_pub.publish(info_msg)
        self.get_logger().info("Published EEGInfo metadata")

    # ------------------------------------------------------------------
    # Main Processing Callback
    # ------------------------------------------------------------------
    # ------------------------------------------------------------------

    def _on_eeg(self, msg: EEG) -> None:
        """
        Callback for incoming EEG messages.

        Steps:
            1. Reshape incoming EEG data
            2. Apply Common Average Reference (CAR)
            3. Apply bandpass filter
            4. Optional downsampling
            5. Optional rounding
            6. Publish processed message

        """
        try:
            # Reshape EEG data
            eeg_array, _ = self.tools.reshape_eeg(list(msg.eeg), int(msg.sample_size))

            if self.num_channels is None:
                self.num_channels = eeg_array.shape[0]
                self.publish_eeg_info()

            # Apply Common Average Reference (CAR)
            referenced = self.tools.apply_common_average_reference_numpy(eeg_array)

            # Apply bandpass filter (0.5-45 Hz) via preprocessing tools
            try:
                filtered = self.tools.apply_bandpass_filter_numpy(
                    referenced,
                    self.l_freq,
                    self.h_freq,
                    sfreq=self.sampling_rate
                )
            except Exception as filter_error:
                self.get_logger().error(f"Bandpass filtering failed, publishing referenced EEG only: {filter_error}")
                filtered = referenced

            processed = filtered

            # Optional downsampling
            if self.downsample_factor > 1:
                processed = decimate(processed, self.downsample_factor, axis=1, zero_phase=True)

            # Optional rounding
            if self.round_precision >= 0:
                factor = 10 ** self.round_precision
                processed = np.round(processed * factor) / factor

            # Prepare output message
            out = EEG()

            out.header = msg.header

            out.session_id = msg.session_id
            out.sample_size = int(processed.shape[1])
            out.eeg = processed.flatten().astype(float).tolist()

            # Copy quality safely
            try:
                if msg.quality and len(msg.quality) == processed.shape[0]:
                    out.quality = list(msg.quality)
                else:
                    out.quality = []
            except Exception:
                out.quality = []

            self.pub.publish(out)

        except Exception as e:
            self.get_logger().error(f"Error processing EEG message: {e}")


def main(args=None):
    """Entry point for EEGPreprocessor node."""
    rclpy.init(args=args)
    node = EEGPreprocessor()

    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, rclpy.executors.ExternalShutdownException):
        node.get_logger().info("Shutting down EEGPreprocessor")
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()