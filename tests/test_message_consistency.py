#!/usr/bin/env python3
"""
Message Consistency Tests for EEG Pipeline

Verifies that EEG data maintains integrity and structure as it flows
through different nodes in the ROS2 pipeline.

Tests:
- Data structure preservation
- Timestamp coherence
- Channel count matching between raw and info messages
- Metadata alignment
"""

import unittest
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, QoSReliabilityPolicy, QoSDurabilityPolicy, QoSHistoryPolicy
from healthcare_msgs.msg import EEG, EEGInfo
import numpy as np
import time
from collections import deque


class MessageConsistencyNode(Node):
    """Helper node to collect and validate messages."""
    
    def __init__(self):
        super().__init__('message_consistency_test_node')
        
        # Storage for received messages
        self.raw_messages = deque(maxlen=100)
        self.raw_info_messages = deque(maxlen=10)
        self.preprocessed_messages = deque(maxlen=100)
        self.preprocessed_info_messages = deque(maxlen=10)
        
        # QoS profiles
        # For info topics: transient_local to receive latched messages
        info_qos = QoSProfile(
            reliability=QoSReliabilityPolicy.RELIABLE,
            durability=QoSDurabilityPolicy.TRANSIENT_LOCAL,
            history=QoSHistoryPolicy.KEEP_LAST,
            depth=10
        )
        
        # For data topics: default QoS
        data_qos = QoSProfile(
            reliability=QoSReliabilityPolicy.RELIABLE,
            history=QoSHistoryPolicy.KEEP_LAST,
            depth=10
        )
        
        # Subscriptions
        self.raw_sub = self.create_subscription(
            EEG, '/eeg/raw', self.raw_callback, data_qos)
        self.raw_info_sub = self.create_subscription(
            EEGInfo, '/eeg/raw_info', self.raw_info_callback, info_qos)
        self.preprocessed_sub = self.create_subscription(
            EEG, '/eeg/processed', self.preprocessed_callback, data_qos)
        self.preprocessed_info_sub = self.create_subscription(
            EEGInfo, '/eeg/processed_info', self.preprocessed_info_callback, info_qos)
    
    def raw_callback(self, msg):
        self.raw_messages.append(msg)
    
    def raw_info_callback(self, msg):
        self.raw_info_messages.append(msg)
    
    def preprocessed_callback(self, msg):
        self.preprocessed_messages.append(msg)
    
    def preprocessed_info_callback(self, msg):
        self.preprocessed_info_messages.append(msg)


class TestMessageConsistency(unittest.TestCase):
    """Test message consistency throughout the EEG pipeline."""
    
    @classmethod
    def setUpClass(cls):
        """Initialize ROS2 and start collecting messages."""
        rclpy.init()
        cls.node = MessageConsistencyNode()
        
        # Collect messages for a few seconds (increased to 8s for preprocessor to catch up)
        cls.node.get_logger().info('Collecting messages for consistency tests...')
        start_time = time.time()
        while time.time() - start_time < 8.0:
            rclpy.spin_once(cls.node, timeout_sec=0.1)
        
        cls.node.get_logger().info(
            f'Collected: {len(cls.node.raw_messages)} raw, '
            f'{len(cls.node.preprocessed_messages)} preprocessed messages'
        )
    
    @classmethod
    def tearDownClass(cls):
        """Cleanup ROS2."""
        cls.node.destroy_node()
        rclpy.shutdown()
    
    def test_raw_messages_received(self):
        """Verify raw EEG messages are being published."""
        self.assertGreater(
            len(self.node.raw_messages), 0,
            "No raw EEG messages received on /eeg/raw"
        )
    
    def test_raw_info_received(self):
        """Verify raw EEG info messages are published."""
        self.assertGreater(
            len(self.node.raw_info_messages), 0,
            "No raw EEG info messages received on /eeg/raw_info"
        )
    
    def test_preprocessed_messages_received(self):
        """Verify preprocessed EEG messages are published."""
        self.assertGreater(
            len(self.node.preprocessed_messages), 0,
            "No preprocessed EEG messages received on /eeg/processed"
        )
    
    def test_channel_count_consistency(self):
        """Verify channel count matches between EEG data and EEGInfo."""
        if len(self.node.raw_info_messages) == 0:
            self.skipTest("No raw info messages available")
        
        if len(self.node.raw_messages) == 0:
            self.skipTest("No raw messages available")
        
        info_msg = self.node.raw_info_messages[-1]
        expected_channels = info_msg.channel_size
        
        for raw_msg in list(self.node.raw_messages)[-10:]:
            # EEG data is flat: total_samples = channels * sample_size
            if raw_msg.sample_size > 0 and len(raw_msg.eeg) > 0:
                actual_channels = len(raw_msg.eeg) // raw_msg.sample_size
                self.assertEqual(
                    actual_channels, expected_channels,
                    f"Channel count mismatch: EEGInfo says {expected_channels}, "
                    f"but EEG message has {actual_channels} channels"
                )
    
    def test_sample_size_consistency(self):
        """Verify sample_size field matches actual data length."""
        if len(self.node.raw_messages) == 0:
            self.skipTest("No raw messages available")
        
        for raw_msg in list(self.node.raw_messages)[-10:]:
            # EEG data is flat 1D array: total_samples = channels * sample_size
            # Verify the total length is divisible by sample_size
            if len(raw_msg.eeg) > 0 and raw_msg.sample_size > 0:
                total_samples = len(raw_msg.eeg)
                self.assertEqual(
                    total_samples % raw_msg.sample_size, 0,
                    f"Total samples {total_samples} not divisible by sample_size {raw_msg.sample_size}"
                )
                # Calculate number of channels
                n_channels = total_samples // raw_msg.sample_size
                self.assertGreater(n_channels, 0, "Calculated zero channels from data")
    
    def test_timestamp_sequential(self):
        """Verify timestamps are sequential and monotonically increasing."""
        if len(self.node.raw_messages) < 2:
            self.skipTest("Need at least 2 messages for timestamp test")
        
        messages = list(self.node.raw_messages)
        prev_timestamp = None
        
        for msg in messages:
            current_timestamp = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9
            
            if prev_timestamp is not None:
                self.assertGreater(
                    current_timestamp, prev_timestamp,
                    f"Timestamps not monotonic: {prev_timestamp} -> {current_timestamp}"
                )
            
            prev_timestamp = current_timestamp
    
    def test_session_id_consistency(self):
        """Verify all messages in a run have the same session_id."""
        if len(self.node.raw_messages) < 2:
            self.skipTest("Need at least 2 messages for session_id test")
        
        messages = list(self.node.raw_messages)
        first_session_id = messages[0].session_id
        
        for idx, msg in enumerate(messages[1:], start=1):
            self.assertEqual(
                msg.session_id, first_session_id,
                f"Session ID mismatch at message {idx}: "
                f"expected {first_session_id}, got {msg.session_id}"
            )
    
    def test_quality_array_size(self):
        """Verify quality array has same length as number of channels."""
        if len(self.node.raw_info_messages) == 0:
            self.skipTest("No raw info messages available")
        
        if len(self.node.raw_messages) == 0:
            self.skipTest("No raw messages available")
        
        info_msg = self.node.raw_info_messages[-1]
        expected_channels = info_msg.channel_size
        
        for raw_msg in list(self.node.raw_messages)[-10:]:
            # Calculate actual channels from flat array
            if raw_msg.sample_size > 0 and len(raw_msg.eeg) > 0:
                actual_channels = len(raw_msg.eeg) // raw_msg.sample_size
                self.assertEqual(
                    len(raw_msg.quality), actual_channels,
                    f"Quality array length {len(raw_msg.quality)} doesn't match "
                    f"channel count {actual_channels}"
                )
    
    def test_preprocessing_maintains_structure(self):
        """Verify preprocessing doesn't alter message structure."""
        if len(self.node.raw_messages) == 0 or len(self.node.preprocessed_messages) == 0:
            self.skipTest("Need both raw and preprocessed messages")
        
        raw_msg = self.node.raw_messages[0]
        prep_msg = self.node.preprocessed_messages[0]
        
        # Same total data length (channels * sample_size)
        self.assertEqual(
            len(raw_msg.eeg), len(prep_msg.eeg),
            "Preprocessing changed data array length"
        )
        
        # Same sample size per channel
        self.assertEqual(
            raw_msg.sample_size, prep_msg.sample_size,
            "Preprocessing changed sample size"
        )
        
        # Same number of channels (calculated)
        if raw_msg.sample_size > 0:
            raw_channels = len(raw_msg.eeg) // raw_msg.sample_size
            prep_channels = len(prep_msg.eeg) // prep_msg.sample_size
            self.assertEqual(
                raw_channels, prep_channels,
                f"Preprocessing changed number of channels: {raw_channels} -> {prep_channels}"
            )
        
        # Same session ID
        self.assertEqual(
            raw_msg.session_id, prep_msg.session_id,
            "Preprocessing changed session ID"
        )
    
    def test_metadata_alignment(self):
        """Verify EEGInfo metadata aligns with actual EEG data characteristics."""
        if len(self.node.raw_info_messages) == 0 or len(self.node.raw_messages) == 0:
            self.skipTest("No info messages available")
        
        info_msg = self.node.raw_info_messages[-1]
        raw_msg = self.node.raw_messages[-1]
        
        # Calculate actual number of channels from EEG data
        if raw_msg.sample_size > 0 and len(raw_msg.eeg) > 0:
            actual_channels = len(raw_msg.eeg) // raw_msg.sample_size
            
            # EEGInfo channel_size should match actual channels
            self.assertEqual(
                info_msg.channel_size, actual_channels,
                f"EEGInfo channel_size ({info_msg.channel_size}) doesn't match "
                f"actual channels ({actual_channels})"
            )
            
            # Electrode sites array should have entry for each channel
            self.assertGreaterEqual(
                len(info_msg.electrode_sites), actual_channels,
                f"Electrode sites array too small: {len(info_msg.electrode_sites)} < {actual_channels}"
            )
    
    def test_preprocessing_methods_recorded(self):
        """Verify preprocessing methods are recorded in preprocessed_info."""
        if len(self.node.preprocessed_info_messages) == 0:
            self.skipTest("No preprocessed info messages available")
        
        info_msg = self.node.preprocessed_info_messages[-1]
        
        # Should have at least one preprocessing method recorded
        self.assertGreater(
            len(info_msg.selected_preprocessing), 0,
            "No preprocessing methods recorded in EEGInfo"
        )
        
        # Common methods should be present (bandpass=1 and/or CAR=4)
        has_expected_method = any(
            method in [1, 4] for method in info_msg.selected_preprocessing
        )
        self.assertTrue(
            has_expected_method,
            f"Expected preprocessing methods not found. Got: {list(info_msg.selected_preprocessing)}"
        )


if __name__ == '__main__':
    unittest.main()
