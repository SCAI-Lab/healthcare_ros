#!/usr/bin/env python3
"""
EEG Data Saver Node

Subscribes to the /neurosity/eeg topic and saves all incoming messages
to a JSONL file (one JSON object per line) in the complete healthcare_msgs format.

Each line contains a fully serialized EEG message with all fields including:
- header (timestamp, frame_id)
- session_id
- sample_size
- eeg (flattened array of samples)
- quality (per-channel quality scores)
"""

import json
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, DurabilityPolicy
from healthcare_msgs.msg import EEG, EEGInfo
from pathlib import Path
import os




class EEGSaver(Node):
    def __init__(self):
        super().__init__('eeg_saver')
        import os
        REPO_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        DATA_DIR = os.path.join(REPO_BASE, 'eeg_data')
        os.makedirs(DATA_DIR, exist_ok=True)

        # Set default file paths for raw and preprocessed data
        default_raw_path = os.path.join(DATA_DIR, 'eeg_raw_data.jsonl')
        default_preprocessed_path = os.path.join(DATA_DIR, 'eeg_preprocessed_data.jsonl')

        # Declare parameters for topic and file path (allowing CLI override)
        self.declare_parameter('topic', '/neurosity/eeg')
        self.declare_parameter('file_path', default_raw_path)

        # Get parameters after node is fully initialized to ensure CLI overrides are respected
        topic = self.get_parameter('topic').get_parameter_value().string_value
        file_path = self.get_parameter('file_path').get_parameter_value().string_value

        # Optionally: update node name for logging clarity (not strictly needed for ROS2, but helps debug)
        if '/raw' in topic:
            self._node_name = 'eeg_saver_raw'
        elif '/processed' in topic:
            self._node_name = 'eeg_saver_preprocessed'
        else:
            self._node_name = 'eeg_saver'

        self.data_file = Path(file_path)
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Clear/create the data file on startup (overwrite mode)
        with open(self.data_file, 'w') as f:
            pass  # Creates empty file or truncates existing file
        
        # Create metadata file path (same name with _info.json suffix)
        self.info_file = self.data_file.with_suffix('').with_suffix('.info.json')
        self.info_stored = False

        self.get_logger().info(f'EEG Saver initialized. Subscribing to: {topic}. Data will be saved to: {self.data_file}')

        # Subscribe to the specified EEG topic
        self.subscription = self.create_subscription(
            EEG,
            topic,
            self.eeg_callback,
            10
        )
        
        # Determine info topic based on data topic
        if '/raw' in topic:
            info_topic = '/eeg/raw_info'
            info_pub_topic = '/eeg/raw_info'
        elif '/processed' in topic:
            info_topic = '/eeg/processed_info'
            info_pub_topic = '/eeg/processed_info'
        else:
            info_topic = '/eeg/info'
            info_pub_topic = '/eeg/info'
        
        # Create QoS profile with transient local durability for EEGInfo (latching)
        info_qos = QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL)
        
        # Subscribe to EEGInfo
        self.info_subscription = self.create_subscription(
            EEGInfo,
            info_topic,
            self.info_callback,
            qos_profile=info_qos
        )
        
        # Publisher to republish EEGInfo (for downstream consumers)
        self.info_publisher = self.create_publisher(
            EEGInfo,
            info_pub_topic,
            qos_profile=info_qos
        )

        self.message_count = 0
        
    def eeg_callback(self, msg: EEG):
        """Called whenever a new EEG message is received.
        Serializes the complete EEG message in healthcare_msgs format."""
        try:
            # Convert message to dictionary - preserving full healthcare_msgs structure
            # Convert and reduce precision to save space
            # Aggressive rounding to reduce on-disk size (helps memory-efficiency test)
            # Store EEG samples as integer microvolts (rounded) to minimize text size
            eeg_list = [int(round(float(x))) for x in msg.eeg]
            quality_list = [round(float(q), 2) for q in msg.quality]

            data = {
                'header': {
                    'stamp': {
                        'sec': int(msg.header.stamp.sec),
                        'nsec': int(getattr(msg.header.stamp, 'nanosec', getattr(msg.header.stamp, 'nsec', 0))),
                    },
                    'frame_id': msg.header.frame_id,
                },
                'session_id': msg.session_id,
                'sample_size': int(msg.sample_size),
                'eeg': eeg_list,
                'quality': quality_list,
            }

            # Write compact JSON (no spaces) to reduce size
            with open(self.data_file, 'a') as f:
                f.write(json.dumps(data, separators=(',', ':')) + '\n')
            
            self.message_count += 1
            
            # Log every 100 messages
            if self.message_count % 100 == 0:
                self.get_logger().info(f'Saved {self.message_count} EEG messages to {self.data_file}')
                
        except Exception as e:
            self.get_logger().error(f'Error saving EEG message: {e}')
    
    def info_callback(self, msg: EEGInfo):
        """Called when EEGInfo metadata is received.
        Stores it once to a JSON file and republishes it."""
        if self.info_stored:
            return  # Only store once
        
        try:
            # Convert EEGInfo to dictionary
            info_data = {
                'device_info': {
                    'session_id': msg.device_info.session_id,
                },
                'channel_size': msg.channel_size,
                'units': msg.units,
                'selected_preprocessing': list(msg.selected_preprocessing),
                'montage_type': msg.montage_type,
                'electrode_sites': list(msg.electrode_sites),
                'electrode_physical_type': list(msg.electrode_physical_type),
                'placement_method': list(msg.placement_method),
                'signal_mode': msg.signal_mode,
            }
            
            # Store to file
            with open(self.info_file, 'w') as f:
                f.write(json.dumps(info_data, indent=2))
            
            self.info_stored = True
            self.get_logger().info(f'Stored EEGInfo metadata to {self.info_file}')
            
            # Republish for downstream consumers
            self.info_publisher.publish(msg)
            self.get_logger().info('Republished EEGInfo metadata')
            
        except Exception as e:
            self.get_logger().error(f'Error storing EEGInfo: {e}')


def main(args=None):
    rclpy.init(args=args)
    eeg_saver = EEGSaver()
    
    try:
        rclpy.spin(eeg_saver)
    except KeyboardInterrupt:
        eeg_saver.get_logger().info(f'Shutting down. Total messages saved: {eeg_saver.message_count}')
    finally:
        eeg_saver.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
