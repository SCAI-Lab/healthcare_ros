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
from healthcare_msgs.msg import EEG
from pathlib import Path
import os


class EEGSaver(Node):
    def __init__(self):
        super().__init__('eeg_saver')
        
        # Set up log directory
        self.log_dir = Path(os.path.expanduser('~/neurosity_logs'))
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self.data_file = self.log_dir / 'eeg_data.jsonl'
        
        self.get_logger().info(f'EEG Saver initialized. Data will be saved to: {self.data_file}')
        
        # Subscribe to the neurosity EEG topic
        self.subscription = self.create_subscription(
            EEG,
            '/neurosity/eeg',
            self.eeg_callback,
            10
        )
        
        self.message_count = 0
        
    def eeg_callback(self, msg: EEG):
        """Called whenever a new EEG message is received.
        Serializes the complete EEG message in healthcare_msgs format."""
        try:
            # Convert message to dictionary - preserving full healthcare_msgs structure
            data = {
                'header': {
                    'stamp': {
                        'sec': msg.header.stamp.sec,
                        'nsec': msg.header.stamp.nanosec,
                    },
                    'frame_id': msg.header.frame_id,
                },
                'session_id': msg.session_id,
                'sample_size': msg.sample_size,
                'eeg': list(msg.eeg),  # Convert to list for JSON serialization
                'quality': list(msg.quality),  # Convert to list for JSON serialization
            }
            
            # Append to JSONL file (one JSON object per line)
            with open(self.data_file, 'a') as f:
                f.write(json.dumps(data) + '\n')
            
            self.message_count += 1
            
            # Log every 100 messages
            if self.message_count % 100 == 0:
                self.get_logger().info(f'Saved {self.message_count} EEG messages to {self.data_file}')
                
        except Exception as e:
            self.get_logger().error(f'Error saving EEG message: {e}')


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
