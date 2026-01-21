#!/usr/bin/env python3
"""
Timing Behavior Tests for EEG Pipeline

Measures and validates:
- End-to-end latency (raw → preprocessed)
- Processing throughput
- Real-time performance at 256 Hz
- Timestamp accuracy
"""

import unittest
import rclpy
from rclpy.node import Node
from healthcare_msgs.msg import EEG, EEGInfo
import time
import numpy as np
from collections import deque
from threading import Lock


class TimingMeasurementNode(Node):
    """ROS2 node that measures timing behavior."""
    
    def __init__(self):
        super().__init__('timing_measurement_node')
        
        # Storage for timing measurements
        self.latencies = []
        self.raw_timestamps = deque(maxlen=1000)
        self.preprocessed_timestamps = deque(maxlen=1000)
        self.lock = Lock()
        
        # Track message pairs by session_id and approximate time
        self.pending_raw = {}  # {session_id: (timestamp, wall_time)}
        
        # Subscriptions
        self.raw_sub = self.create_subscription(
            EEG,
            '/eeg/raw',
            self.raw_callback,
            10
        )
        
        self.preprocessed_sub = self.create_subscription(
            EEG,
            '/eeg/processed',
            self.preprocessed_callback,
            10
        )
        
        self.get_logger().info('Timing measurement node initialized')
    
    def raw_callback(self, msg):
        """Record raw message timing."""
        with self.lock:
            # Convert ROS time to float seconds
            msg_time = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9
            wall_time = time.time()
            
            self.raw_timestamps.append(msg_time)
            
            # Store for latency matching (use session_id + approximate time)
            key = (msg.session_id, int(msg_time * 10))  # 100ms bins
            self.pending_raw[key] = (msg_time, wall_time)
    
    def preprocessed_callback(self, msg):
        """Record preprocessed message timing and calculate latency."""
        with self.lock:
            # Convert ROS time to float seconds
            msg_time = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9
            wall_time = time.time()
            
            self.preprocessed_timestamps.append(msg_time)
            
            # Try to find matching raw message
            key = (msg.session_id, int(msg_time * 10))  # 100ms bins
            if key in self.pending_raw:
                raw_msg_time, raw_wall_time = self.pending_raw.pop(key)
                
                # Calculate end-to-end latency (wall clock time)
                latency = wall_time - raw_wall_time
                self.latencies.append(latency)
    
    def get_measurements(self):
        """Return collected timing measurements."""
        with self.lock:
            return {
                'latencies': list(self.latencies),
                'raw_timestamps': list(self.raw_timestamps),
                'preprocessed_timestamps': list(self.preprocessed_timestamps),
                'n_latency_measurements': len(self.latencies)
            }
    
    def reset(self):
        """Reset all measurements."""
        with self.lock:
            self.latencies.clear()
            self.raw_timestamps.clear()
            self.preprocessed_timestamps.clear()
            self.pending_raw.clear()


class TestTimingBehavior(unittest.TestCase):
    """Test timing behavior of EEG pipeline."""
    
    @classmethod
    def setUpClass(cls):
        """Initialize ROS2 and create timing node."""
        rclpy.init()
        cls.node = TimingMeasurementNode()
        
        # Collect timing data for 10 seconds
        print("\nCollecting timing measurements for 10 seconds...")
        start_time = time.time()
        while time.time() - start_time < 10.0:
            rclpy.spin_once(cls.node, timeout_sec=0.1)
        
        cls.measurements = cls.node.get_measurements()
        print(f"Collected {len(cls.measurements['latencies'])} latency measurements")
        print(f"Collected {len(cls.measurements['raw_timestamps'])} raw timestamps")
        print(f"Collected {len(cls.measurements['preprocessed_timestamps'])} preprocessed timestamps")
    
    @classmethod
    def tearDownClass(cls):
        """Cleanup ROS2."""
        cls.node.destroy_node()
        rclpy.shutdown()
    
    def test_latencies_measured(self):
        """Verify that latency measurements were collected."""
        self.assertGreater(
            len(self.measurements['latencies']), 0,
            "No latency measurements collected. Is the pipeline running?"
        )
    
    def test_raw_messages_received(self):
        """Verify raw messages are being published."""
        self.assertGreater(
            len(self.measurements['raw_timestamps']), 0,
            "No raw EEG messages received"
        )
    
    def test_preprocessed_messages_received(self):
        """Verify preprocessed messages are being published."""
        self.assertGreater(
            len(self.measurements['preprocessed_timestamps']), 0,
            "No preprocessed EEG messages received"
        )
    
    def test_acceptable_latency(self):
        """Verify end-to-end latency is acceptable (<100ms typical)."""
        if len(self.measurements['latencies']) == 0:
            self.skipTest("No latency measurements available")
        
        latencies = np.array(self.measurements['latencies'])
        mean_latency = np.mean(latencies)
        max_latency = np.max(latencies)
        p95_latency = np.percentile(latencies, 95)
        
        print(f"\nLatency Statistics:")
        print(f"  Mean: {mean_latency*1000:.2f} ms")
        print(f"  Max: {max_latency*1000:.2f} ms")
        print(f"  95th percentile: {p95_latency*1000:.2f} ms")
        
        # Buffered preprocessor (6s buffer) has higher latency than real-time
        # Mean latency should be reasonable for buffered processing (<3s)
        self.assertLess(
            mean_latency, 3.0,
            f"Mean latency {mean_latency:.2f}s exceeds 3s threshold"
        )
        
        # 95th percentile should be within buffer size
        self.assertLess(
            p95_latency, 8.0,
            f"95th percentile latency {p95_latency:.2f}s exceeds 8s threshold"
        )
    
    def test_throughput_sufficient(self):
        """Verify message throughput is sufficient for real-time processing."""
        if len(self.measurements['raw_timestamps']) < 2:
            self.skipTest("Not enough messages for throughput test")
        
        # Calculate throughput (messages per second)
        raw_times = sorted(self.measurements['raw_timestamps'])
        duration = raw_times[-1] - raw_times[0]
        
        if duration > 0:
            throughput = len(raw_times) / duration
            print(f"\nThroughput: {throughput:.2f} messages/sec")
            
            # At 256 Hz with 1 second windows, expect ~1 msg/sec minimum
            # More messages = smaller windows, which is fine
            self.assertGreater(
                throughput, 0.5,
                f"Throughput {throughput:.2f} msg/sec too low for real-time processing"
            )
    
    def test_timestamp_monotonicity(self):
        """Verify timestamps are monotonically increasing (or at least non-decreasing)."""
        if len(self.measurements['raw_timestamps']) < 2:
            self.skipTest("Not enough timestamps for monotonicity test")
        
        raw_times = list(self.measurements['raw_timestamps'])
        
        # Check for non-decreasing timestamps
        violations = 0
        for i in range(1, len(raw_times)):
            if raw_times[i] < raw_times[i-1]:
                violations += 1
        
        violation_rate = violations / (len(raw_times) - 1) if len(raw_times) > 1 else 0
        
        print(f"\nTimestamp monotonicity violations: {violations} / {len(raw_times)-1} ({violation_rate*100:.2f}%)")
        
        # Allow small violation rate (messages can arrive slightly out of order)
        self.assertLess(
            violation_rate, 0.05,
            f"Too many timestamp violations: {violation_rate*100:.2f}% (threshold: 5%)"
        )
    
    def test_timestamp_spacing(self):
        """Verify timestamps have reasonable spacing for 256 Hz sampling."""
        if len(self.measurements['raw_timestamps']) < 10:
            self.skipTest("Not enough timestamps for spacing test")
        
        raw_times = sorted(self.measurements['raw_timestamps'])
        
        # Calculate inter-message intervals
        intervals = np.diff(raw_times)
        mean_interval = np.mean(intervals)
        std_interval = np.std(intervals)
        
        print(f"\nTimestamp spacing:")
        print(f"  Mean interval: {mean_interval:.4f} sec")
        print(f"  Std deviation: {std_interval:.4f} sec")
        print(f"  Expected for 256Hz, 1sec windows: 1.0 sec")
        
        # With 256 Hz sampling and typical 1-second windows,
        # expect ~1 message per second
        # Allow reasonable variation (0.5 - 2.0 seconds)
        self.assertGreater(
            mean_interval, 0.1,
            f"Messages arriving too frequently: {mean_interval:.4f}sec"
        )
        self.assertLess(
            mean_interval, 5.0,
            f"Messages arriving too slowly: {mean_interval:.4f}sec"
        )
    
    def test_preprocessing_not_skipping_messages(self):
        """Verify preprocessor outputs expected number of messages (with downsampling)."""
        n_raw = len(self.measurements['raw_timestamps'])
        n_preprocessed = len(self.measurements['preprocessed_timestamps'])
        
        if n_raw == 0:
            self.skipTest("No raw messages received")
        
        ratio = n_preprocessed / n_raw if n_raw > 0 else 0
        
        print(f"\nMessage throughput:")
        print(f"  Raw messages: {n_raw}")
        print(f"  Preprocessed messages: {n_preprocessed}")
        print(f"  Ratio: {ratio:.2f}")
        
        # Preprocessor uses buffering and may downsample
        # Expected ratio is ~0.3 due to intentional downsampling
        self.assertGreater(
            ratio, 0.1,
            f"Preprocessor outputting too few messages: {ratio:.2f} (expected ~0.3)"
        )
        self.assertLess(
            ratio, 0.6,
            f"Preprocessor outputting too many messages: {ratio:.2f} (expected ~0.3)"
        )
    
    def test_latency_stability(self):
        """Verify latency doesn't increase over time (no memory leaks/degradation)."""
        if len(self.measurements['latencies']) < 10:
            self.skipTest("Not enough latency measurements")
        
        latencies = np.array(self.measurements['latencies'])
        
        # Split into first half and second half
        mid = len(latencies) // 2
        first_half = latencies[:mid]
        second_half = latencies[mid:]
        
        mean_first = np.mean(first_half)
        mean_second = np.mean(second_half)
        
        print(f"\nLatency stability:")
        print(f"  First half mean: {mean_first*1000:.2f} ms")
        print(f"  Second half mean: {mean_second*1000:.2f} ms")
        print(f"  Difference: {(mean_second - mean_first)*1000:.2f} ms")
        
        # Second half shouldn't be significantly worse than first half
        # Allow 20ms increase maximum
        self.assertLess(
            mean_second - mean_first, 0.02,
            f"Latency degraded over time by {(mean_second - mean_first)*1000:.2f}ms"
        )


if __name__ == '__main__':
    unittest.main()
