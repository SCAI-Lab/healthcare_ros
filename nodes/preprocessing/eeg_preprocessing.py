#!/usr/bin/env python3
"""
EEG Preprocessing Node - ROS2 Pipeline Component

Real-time EEG signal preprocessing node that applies digital filtering and
re-referencing techniques to improve signal quality. Designed for headless
deployment in automated pipelines.

Processing Pipeline
-------------------
1. Subscribe to raw EEG data from /eeg/raw
2. Apply Butterworth bandpass filter (0.5-45 Hz)
3. Apply Common Average Reference (CAR)
4. Optional: Downsample and round for storage efficiency
5. Publish processed data to /eeg/processed
6. Forward metadata with preprocessing annotations

Topics Subscribed
-----------------
/eeg/raw : healthcare_msgs.msg.EEG
    Raw EEG data from acquisition devices
/eeg/raw_info : healthcare_msgs.msg.EEGInfo
    Raw metadata (latched, QoS: transient_local)

Topics Published
----------------
/eeg/processed : healthcare_msgs.msg.EEG
    Filtered and referenced EEG data
/eeg/processed_info : healthcare_msgs.msg.EEGInfo
    Metadata with preprocessing annotations (latched)

Parameters
----------
l_freq : float, default=0.5
    Low frequency cutoff for bandpass filter (Hz)
h_freq : float, default=45.0
    High frequency cutoff for bandpass filter (Hz)
sampling_rate : float, default=150.0
    Sampling frequency in Hz
downsample_factor : int, default=1
    Downsampling factor (1=no downsampling)
round_precision : int, default=3
    Decimal places for rounding (reduces storage size)
publish_topic : str, default="/eeg/processed"
    Topic for publishing processed data

Preprocessing Methods
---------------------
Bandpass Filter:
    4th-order Butterworth filter removes DC drift (high-pass) and
    high-frequency noise (low-pass). Default 0.5-45 Hz preserves
    delta through gamma bands.

Common Average Reference (CAR):
    Subtracts the average of all channels from each channel:
    CAR_i = X_i - mean(X_all)
    Removes common-mode artifacts while preserving channel-specific activity.

Metadata Forwarding:
    Copies all upstream metadata (device info, electrodes, montage) and
    adds preprocessing method constants:
    - EEG_PREPROC_BANDPASS (1)
    - EEG_PREPROC_CAR (4)

Examples
--------
Run with defaults:
    $ ros2 run healthcare_msgs eeg_preprocessor

Custom filter parameters:
    $ ros2 run healthcare_msgs eeg_preprocessor --ros-args \
        -p l_freq:=1.0 -p h_freq:=30.0 -p downsample_factor:=2

Run via launch script:
    $ ./launch/start.sh  # Automatically starts preprocessor

Notes
-----
- Designed for headless operation (no interactive prompts)
- Uses scipy.signal for filtering, MNE concepts for referencing
- Latched QoS ensures late subscribers receive metadata
- Buffer management prevents memory growth in long sessions

See Also
--------
eeg_preprocessing_tools.EEGPreprocessingTools : Advanced MNE-based tools
healthcare_msgs.msg.EEG : EEG message definition
healthcare_msgs.msg.EEGInfo : EEG metadata with preprocessing constants
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
from eeg_preprocessing_tools import EEGPreprocessingTools

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
        self.declare_parameter("sampling_rate", 150.0)  # Updated to realistic 150 Hz
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
        # We need enough samples for proper filtering (e.g., 2 seconds = 300 samples at 150 Hz)
        self.buffer_size = int(self.buffer_duration * self.sampling_rate)
        self.data_buffer = []  # List of (eeg_array, msg) tuples
        self.num_channels = None
        self.info_published = False
        self.raw_info = None  # Store raw EEGInfo metadata
        
        # Create QoS profile with transient local durability for EEGInfo (latching)
        info_qos = QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL)
        
        # Set up publishers and subscribers
        self.pub = self.create_publisher(EEG, self.publish_topic, 10)
        self.info_pub = self.create_publisher(EEGInfo, "/eeg/processed_info", qos_profile=info_qos)
        self.sub = self.create_subscription(EEG, "/eeg/raw", self._on_eeg, 10)
        
        # Subscribe to raw EEGInfo to copy upstream metadata
        self.info_sub = self.create_subscription(EEGInfo, "/eeg/raw_info", self._on_raw_info, qos_profile=info_qos)

        # Initialize preprocessing tools
        self.tools = EEGPreprocessingTools()

        self.get_logger().info(f"EEGPreprocessor initialized. Buffer: {self.buffer_duration}s ({self.buffer_size} samples)")
        self.get_logger().info(f"Filtering: {self.l_freq}-{self.h_freq} Hz, Publishing to: {self.publish_topic}")

    def _on_raw_info(self, msg: EEGInfo) -> None:
        """
        Callback for receiving raw EEG metadata.
        
        Stores the raw EEGInfo message for later use when publishing processed metadata.
        This enables forwarding of upstream device information and electrode configuration
        to the processed data stream.
        
        Parameters
        ----------
        msg : healthcare_msgs.msg.EEGInfo
            Raw EEG metadata including device info, electrode sites, and configuration.
            
        Notes
        -----
        Uses latching QoS (transient local durability) to ensure late-joining nodes
        receive the metadata even if published before subscription.
        """
        self.raw_info = msg
        self.get_logger().info(f"Received raw EEGInfo: {msg.channel_size} channels")

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
            info_msg.electrode_physical_type = self.raw_info.electrode_physical_type
            info_msg.placement_method = self.raw_info.placement_method
            info_msg.signal_mode = self.raw_info.signal_mode
            info_msg.bipolar_active_sites = self.raw_info.bipolar_active_sites
            info_msg.bipolar_reference_sites = self.raw_info.bipolar_reference_sites
            info_msg.reference_sites = self.raw_info.reference_sites
        else:
            # Fallback if raw info not available
            info_msg.device_info.session_id = 'preprocessed'
            info_msg.channel_size = self.num_channels
            info_msg.units = EEGInfo.UNIT_UV
            info_msg.montage_type = EEGInfo.MONTAGE_TYPE_REFERENTIAL
            info_msg.signal_mode = EEGInfo.SIGNAL_MODE_SURFACE
        
        # Add preprocessing steps applied by this node
        info_msg.selected_preprocessing = [
            EEGInfo.EEG_PREPROC_BANDPASS,
            EEGInfo.EEG_PREPROC_CAR  # Common Average Reference
        ]
        
        self.info_pub.publish(info_msg)
        self.get_logger().info(
            f'Published EEGInfo metadata: {info_msg.channel_size} channels, '
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
    except (KeyboardInterrupt, rclpy.executors.ExternalShutdownException):
        node.get_logger().info("Shutting down EEGPreprocessor")
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
