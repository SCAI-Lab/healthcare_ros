#!/usr/bin/env python3
"""
ROS 2 node to launch rosbag record for EEG topics in MCAP format.
This node acts as a wrapper to start/stop rosbag recording as part of the pipeline.
"""
import subprocess
import signal
import os

import rclpy
from rclpy.node import Node

class RosbagSaverNode(Node):
    def __init__(self):
        super().__init__('eeg_rosbag_saver')
        # Use eeg_data directory at project root to match JSON savers
        from pathlib import Path
        import datetime
        # Go from nodes/saver/eeg_rosbag_saver.py -> project_root
        project_root = Path(__file__).parent.parent.parent.resolve()
        # Create timestamped directory in eeg_data folder
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        eeg_data_dir = project_root / 'eeg_data'
        eeg_data_dir.mkdir(exist_ok=True)
        self.output_dir = str(eeg_data_dir / f'rosbag_{timestamp}')
        # Record both EEG data and EEGInfo metadata topics
        self.topics = [
            '/eeg/raw',
            '/eeg/raw_info',
            '/eeg/processed',
            '/eeg/processed_info'
        ]
        self.rosbag_proc = None
        self.start_rosbag()
        self.get_logger().info(f"Started rosbag recording to {self.output_dir} (MCAP format)")

    def start_rosbag(self):
        cmd = [
            'ros2', 'bag', 'record',
            '-o', self.output_dir,
            '--storage', 'mcap',
        ] + self.topics
        # Inherit environment variables (including ROS2 setup) from parent process
        self.rosbag_proc = subprocess.Popen(cmd, env=os.environ.copy())

    def destroy_node(self):
        if self.rosbag_proc:
            self.get_logger().info("Stopping rosbag recording...")
            self.rosbag_proc.send_signal(signal.SIGINT)
            self.rosbag_proc.wait()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = RosbagSaverNode()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, rclpy.executors.ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

if __name__ == '__main__':
    main()
