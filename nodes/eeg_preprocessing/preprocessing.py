#!/usr/bin/env python3
""" EEG Preprocessing ROS2 node.

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
import sys
import os

# Add the current directory to the Python path to ensure local imports work
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Import preprocessing tools directly from current directory
from preprocessing_tools import EEGPreprocessingTools

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, DurabilityPolicy

from healthcare_msgs.msg import EEG, EEGInfo  # Importing EEG and EEGInfo messages from healthcare_msgs



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
        self.declare_parameter("l_freq", 0.5)  # Low frequency cutoff (Hz)
        self.declare_parameter("h_freq", 45.0) # High frequency cutoff (Hz)
        self.declare_parameter("sampling_rate", 256.0)
        self.declare_parameter("downsample_factor", 1)
        self.declare_parameter("round_precision", 3)
        self.declare_parameter("publish_topic", "/eeg/processed")
        self.declare_parameter("buffer_duration", 6.0)  # Buffer duration in seconds for filtering (6s for 0.5 Hz)

        # Load parameters
        self.l_freq = float(self.get_parameter("l_freq").value)
        self.h_freq = float(self.get_parameter("h_freq").value)
        self.sampling_rate = float(self.get_parameter("sampling_rate").value)
        self.downsample_factor = int(self.get_parameter("downsample_factor").value)
        self.round_precision = int(self.get_parameter("round_precision").value)
        self.publish_topic = str(self.get_parameter("publish_topic").value)
        self.buffer_duration = float(self.get_parameter("buffer_duration").value)

        # Initialize data buffer for temporal filtering
        # We need enough samples for proper filtering (e.g., 2 seconds = 512 samples at 256 Hz)
        self.buffer_size = int(self.buffer_duration * self.sampling_rate)
        self.data_buffer = []  # List of (eeg_array, msg) tuples
        self.num_channels = None
        self.info_published = False
        
        # Create QoS profile with transient local durability for EEGInfo (latching)
        info_qos = QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL)
        
        # Set up publishers and subscribers
        self.pub = self.create_publisher(EEG, self.publish_topic, 10)
        self.info_pub = self.create_publisher(EEGInfo, "/eeg/processed_info", qos_profile=info_qos)
        self.sub = self.create_subscription(EEG, "/eeg/raw", self._on_eeg, 10)

        # Initialize preprocessing tools
        self.tools = EEGPreprocessingTools()

        self.get_logger().info(f"EEGPreprocessor initialized. Buffer: {self.buffer_duration}s ({self.buffer_size} samples)")
        self.get_logger().info(f"Filtering: {self.l_freq}-{self.h_freq} Hz, Publishing to: {self.publish_topic}")

    def _on_eeg(self, msg: EEG) -> None:
        """
        Callback for incoming EEG messages. Buffers data and applies preprocessing when buffer is full.

        Steps:
            1. Reshape and add incoming EEG data to buffer
            2. When buffer reaches target size:
               a. Concatenate buffered data
               b. Apply band-pass filter (0.5-45 Hz by default) on full buffer
               c. Apply common average reference
               d. Split back into original messages
               e. Optionally downsample
               f. Optionally round values
               g. Publish all processed messages
        """
        try:
            # Reshape incoming EEG data
            eeg_array, sample_size = self.tools.reshape_eeg(list(msg.eeg), int(msg.sample_size))
            
            # Initialize num_channels on first message
            if self.num_channels is None:
                self.num_channels = eeg_array.shape[0]
                self.get_logger().info(f"Detected {self.num_channels} EEG channels")
            
            # Publish EEGInfo once after detecting channels
            if not self.info_published and self.num_channels is not None:
                self.publish_eeg_info()
                self.info_published = True
            
            # Add to buffer
            self.data_buffer.append((eeg_array, msg))
            
            # Calculate total samples in buffer
            total_samples = sum(arr.shape[1] for arr, _ in self.data_buffer)
            
            # Process when buffer is full enough for filtering
            if total_samples >= self.buffer_size:
                self._process_buffer()
                
        except Exception as e:
            self.get_logger().error(f"Error processing EEG message: {e}")
            import traceback
            self.get_logger().error(traceback.format_exc())

    def _process_buffer(self):
        """
        Process the accumulated buffer with filtering and publish all messages.
        """
        try:
            # Concatenate all buffered data along time axis
            all_data = np.concatenate([arr for arr, _ in self.data_buffer], axis=1)
            
            # IMPORTANT: Apply common average reference FIRST (on raw data)
            # This removes common-mode noise before filtering
            all_data = self.tools.apply_common_average_reference_numpy(all_data)
            
            # THEN apply bandpass filter to the referenced data
            filtered_data = self.tools.apply_bandpass_filter_numpy(
                all_data,
                l_freq=self.l_freq,
                h_freq=self.h_freq,
                sfreq=self.sampling_rate
            )
            
            # Split back into individual messages and publish
            current_idx = 0
            for eeg_array, original_msg in self.data_buffer:
                segment_length = eeg_array.shape[1]
                
                # Extract the corresponding segment from filtered data
                processed_segment = filtered_data[:, current_idx:current_idx + segment_length]
                current_idx += segment_length
                
                # Optionally downsample
                if self.downsample_factor and self.downsample_factor > 1:
                    processed_segment = decimate(processed_segment, self.downsample_factor, axis=1, zero_phase=True)
                
                # Round to reduce payload size
                if self.round_precision >= 0:
                    factor = 10 ** self.round_precision
                    processed_segment = np.round(processed_segment * factor) / factor
                
                # Prepare output message
                out = EEG()
                out.header = original_msg.header
                out.session_id = original_msg.session_id
                out.sample_size = int(processed_segment.shape[1])
                out.eeg = [float(x) for x in processed_segment.flatten().tolist()]
                
                # Copy quality scores
                try:
                    quality = list(original_msg.quality)
                    if quality:
                        if len(quality) == processed_segment.shape[0]:
                            out.quality = [float(round(q, 2)) for q in quality]
                        else:
                            avgq = float(round(sum(map(float, quality)) / max(len(quality), 1), 2))
                            out.quality = [avgq for _ in range(processed_segment.shape[0])]
                    else:
                        out.quality = []
                except Exception:
                    out.quality = []
                
                # Publish processed message
                self.pub.publish(out)
            
            # Clear buffer after processing
            self.data_buffer.clear()
            
        except Exception as e:
            self.get_logger().error(f"Error processing buffer: {e}")
            import traceback
            self.get_logger().error(traceback.format_exc())
            # Clear buffer on error to prevent accumulation
            self.data_buffer.clear()
    
    def publish_eeg_info(self):
        """
        Publish EEGInfo metadata describing the preprocessed output.
        """
        info_msg = EEGInfo()
        info_msg.device_info.session_id = 'preprocessed'
        info_msg.channel_size = self.num_channels
        info_msg.units = EEGInfo.UNIT_UV
        
        # Document the preprocessing steps applied
        info_msg.selected_preprocessing = [
            EEGInfo.EEG_PREPROC_BANDPASS,
            EEGInfo.EEG_PREPROC_CAR  # Common Average Reference
        ]
        
        # Preserve montage information (assumes referential input)
        info_msg.montage_type = EEGInfo.MONTAGE_TYPE_REFERENTIAL
        
        # Note: Electrode sites and other details would ideally be copied from
        # the upstream EEGInfo message. For now, we leave them unspecified.
        # Future enhancement: subscribe to /eeg/raw_info and forward metadata.
        
        info_msg.signal_mode = EEGInfo.SIGNAL_MODE_SURFACE
        
        self.info_pub.publish(info_msg)
        self.get_logger().info(
            f'Published EEGInfo metadata: {self.num_channels} channels, '
            f'{self.l_freq}-{self.h_freq} Hz bandpass, CAR applied'
        )


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
