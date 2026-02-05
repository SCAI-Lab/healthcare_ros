#!/usr/bin/env python3
"""
EEG InfluxDB Bridge Node

Subscribes to both /eeg/raw and /eeg/processed topics and writes data to InfluxDB
for real-time visualization via InfluxDB Explorer UI.

Stores:
- Raw EEG samples in 'eeg_raw' measurement
- Preprocessed EEG samples in 'eeg_preprocessed' measurement
- Metadata from EEGInfo messages

Configuration via environment variables:
- INFLUXDB_URL: InfluxDB server URL (default: http://localhost:8086)
- INFLUXDB_TOKEN: Authentication token
- INFLUXDB_ORG: Organization name (default: healthcare)
- INFLUXDB_BUCKET: Bucket name (default: eeg_data)

Usage:
    python3 eeg_influxdb_bridge.py
    
    # Or with custom settings:
    INFLUXDB_URL=http://localhost:8086 \
    INFLUXDB_TOKEN=your-token \
    python3 eeg_influxdb_bridge.py
"""

import os
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, DurabilityPolicy
from healthcare_msgs.msg import EEG, EEGInfo

try:
    from influxdb_client import InfluxDBClient, Point
    from influxdb_client.client.write_api import SYNCHRONOUS
    INFLUXDB_AVAILABLE = True
except ImportError:
    INFLUXDB_AVAILABLE = False
    print("WARNING: influxdb-client not installed. Run: pip install influxdb-client")


class EEGInfluxDBBridge(Node):
    """Bridge node that writes EEG data to InfluxDB for web-based visualization."""
    
    def __init__(self):
        super().__init__('eeg_influxdb_bridge')
        
        if not INFLUXDB_AVAILABLE:
            self.get_logger().error('influxdb-client not available. Install with: pip install influxdb-client')
            raise RuntimeError('InfluxDB client library not installed')
        
        # InfluxDB configuration from environment variables
        self.influx_url = os.getenv('INFLUXDB_URL', 'http://localhost:8086')
        self.influx_token = os.getenv('INFLUXDB_TOKEN', '')
        self.influx_org = os.getenv('INFLUXDB_ORG', 'healthcare')
        self.influx_bucket = os.getenv('INFLUXDB_BUCKET', 'eeg_data')
        
        if not self.influx_token:
            self.get_logger().warn('INFLUXDB_TOKEN not set. Using empty token (may fail for authenticated instances)')
        
        # Initialize InfluxDB client
        try:
            self.influx_client = InfluxDBClient(
                url=self.influx_url,
                token=self.influx_token,
                org=self.influx_org
            )
            self.write_api = self.influx_client.write_api(write_options=SYNCHRONOUS)
            self.get_logger().info(f'Connected to InfluxDB at {self.influx_url}')
            self.get_logger().info(f'Writing to bucket: {self.influx_bucket}')
        except Exception as e:
            self.get_logger().error(f'Failed to connect to InfluxDB: {e}')
            raise
        
        # Metadata storage
        self.raw_info = None
        self.processed_info = None
        self.raw_channel_names = []
        self.processed_channel_names = []
        
        # Message counters
        self.raw_count = 0
        self.processed_count = 0
        
        # QoS profile for latched EEGInfo topics
        info_qos = QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL)
        
        # Subscribe to raw EEG data
        self.raw_sub = self.create_subscription(
            EEG,
            '/eeg/raw',
            self.raw_eeg_callback,
            10
        )
        
        # Subscribe to raw EEG metadata
        self.raw_info_sub = self.create_subscription(
            EEGInfo,
            '/eeg/raw_info',
            self.raw_info_callback,
            qos_profile=info_qos
        )
        
        # Subscribe to preprocessed EEG data
        self.processed_sub = self.create_subscription(
            EEG,
            '/eeg/processed',
            self.processed_eeg_callback,
            10
        )
        
        # Subscribe to preprocessed EEG metadata
        self.processed_info_sub = self.create_subscription(
            EEGInfo,
            '/eeg/processed_info',
            self.processed_info_callback,
            qos_profile=info_qos
        )
        
        self.get_logger().info('EEG InfluxDB Bridge started')
        self.get_logger().info('Subscribed to: /eeg/raw, /eeg/raw_info, /eeg/processed, /eeg/processed_info')
        self.get_logger().info('View data at: ' + self.influx_url)
    
    def raw_info_callback(self, msg: EEGInfo):
        """Store raw EEG metadata for enriching data points."""
        self.raw_info = msg
        self.raw_channel_names = self._get_channel_names(msg)
        self.get_logger().info(f'Received raw EEGInfo: {len(self.raw_channel_names)} channels')
        
        # Write metadata to InfluxDB
        self._write_metadata(msg, 'eeg_raw_metadata')
    
    def processed_info_callback(self, msg: EEGInfo):
        """Store preprocessed EEG metadata for enriching data points."""
        self.processed_info = msg
        self.processed_channel_names = self._get_channel_names(msg)
        self.get_logger().info(f'Received preprocessed EEGInfo: {len(self.processed_channel_names)} channels')
        
        # Write metadata to InfluxDB
        self._write_metadata(msg, 'eeg_preprocessed_metadata')
    
    def raw_eeg_callback(self, msg: EEG):
        """Write raw EEG data to InfluxDB."""
        self._write_eeg_data(msg, 'eeg_raw', self.raw_channel_names)
        self.raw_count += 1
        
        if self.raw_count % 50 == 0:
            self.get_logger().info(f'Written {self.raw_count} raw EEG messages to InfluxDB')
    
    def processed_eeg_callback(self, msg: EEG):
        """Write preprocessed EEG data to InfluxDB."""
        self._write_eeg_data(msg, 'eeg_preprocessed', self.processed_channel_names)
        self.processed_count += 1
        
        if self.processed_count % 50 == 0:
            self.get_logger().info(f'Written {self.processed_count} preprocessed EEG messages to InfluxDB')
    
    def _get_channel_names(self, info_msg: EEGInfo):
        """Extract channel names from EEGInfo electrode sites."""
        electrode_map = {
            1: 'FP1', 2: 'FP2', 3: 'F3', 4: 'F4', 5: 'C3', 6: 'C4',
            7: 'P3', 8: 'P4', 9: 'O1', 10: 'O2', 11: 'F7', 12: 'F8',
            13: 'T3', 14: 'T4', 15: 'T5', 16: 'T6', 17: 'FZ', 18: 'CZ',
            19: 'PZ', 20: 'OZ', 21: 'FT7', 22: 'FT8', 23: 'TP7', 24: 'TP8',
            25: 'CP1', 26: 'CP2', 27: 'CP5', 28: 'CP6', 29: 'FC1', 30: 'FC2',
            31: 'FC5', 32: 'FC6', 0: 'CUSTOM'
        }
        
        channel_names = []
        for i, site in enumerate(info_msg.electrode_sites):
            name = electrode_map.get(site, f'CH{i+1}')
            channel_names.append(name)
        
        return channel_names
    
    def _write_metadata(self, info_msg: EEGInfo, measurement: str):
        """Write EEGInfo metadata to InfluxDB."""
        try:
            point = Point(measurement) \
                .tag('session_id', info_msg.device_info.session_id) \
                .field('channel_count', info_msg.channel_size) \
                .field('units', info_msg.units) \
                .field('montage_type', info_msg.montage_type) \
                .field('signal_mode', info_msg.signal_mode)
            
            # Add preprocessing info if available
            if info_msg.selected_preprocessing:
                preproc_str = ','.join(map(str, info_msg.selected_preprocessing))
                point = point.tag('preprocessing', preproc_str)
            
            self.write_api.write(
                bucket=self.influx_bucket,
                org=self.influx_org,
                record=point
            )
        except Exception as e:
            self.get_logger().error(f'Failed to write metadata: {e}')
    
    def _write_eeg_data(self, msg: EEG, measurement: str, channel_names: list):
        """Write EEG samples to InfluxDB with statistics (mean, min, max, frame length)."""
        try:
            # Extract timestamp from ROS message
            timestamp_ns = msg.header.stamp.sec * 1_000_000_000 + msg.header.stamp.nanosec
            
            # Calculate number of channels from sample_size and data length
            if not msg.eeg or msg.sample_size == 0:
                return
            
            num_channels = len(msg.eeg) // msg.sample_size
            samples_per_channel = msg.sample_size
            
            # Use channel names from metadata if available, otherwise use generic names
            if not channel_names or len(channel_names) != num_channels:
                channel_names = [f'CH{i+1}' for i in range(num_channels)]
            
            # Write each channel's samples as separate points
            # Group samples by channel for efficient writing
            points = []
            
            for ch_idx in range(num_channels):
                channel_name = channel_names[ch_idx]
                
                # Extract this channel's samples from flattened array
                start_idx = ch_idx * samples_per_channel
                end_idx = start_idx + samples_per_channel
                channel_samples = msg.eeg[start_idx:end_idx]
                
                # Calculate statistics for this channel
                if channel_samples:
                    mean_value = sum(channel_samples) / len(channel_samples)
                    min_value = min(channel_samples)
                    max_value = max(channel_samples)
                    frame_length = len(channel_samples)
                    
                    # Create point with channel data and statistics
                    point = Point(measurement) \
                        .tag('channel', channel_name) \
                        .tag('session_id', msg.session_id) \
                        .tag('frame_id', msg.header.frame_id) \
                        .field('mean', float(mean_value)) \
                        .field('min', float(min_value)) \
                        .field('max', float(max_value)) \
                        .field('frame_length', frame_length) \
                        .time(timestamp_ns)
                    
                    points.append(point)
            
            # Write all points in batch
            if points:
                self.write_api.write(
                    bucket=self.influx_bucket,
                    org=self.influx_org,
                    record=points
                )
        except Exception as e:
            self.get_logger().error(f'Failed to write EEG data: {e}')
    
    def destroy_node(self):
        """Clean up InfluxDB connection."""
        if hasattr(self, 'write_api'):
            self.write_api.close()
        if hasattr(self, 'influx_client'):
            self.influx_client.close()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    
    try:
        bridge = EEGInfluxDBBridge()
        rclpy.spin(bridge)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f'Error: {e}')
    finally:
        if 'bridge' in locals():
            bridge.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
