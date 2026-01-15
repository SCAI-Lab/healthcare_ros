#!/usr/bin/env python3
"""
ROS 2 node to launch rosbag record for EEG topics in MCAP format.
This node acts as a wrapper to start/stop rosbag recording as part of the pipeline.
"""
import subprocess
import signal
import sys
import os

import rclpy
from rclpy.node import Node

class RosbagSaverNode(Node):
    def __init__(self):
        super().__init__('eeg_rosbag_saver')
        self.output_dir = os.path.expanduser('~/neurosity_rosbag')
        self.topics = ['/neurosity/eeg', '/neurosity/eeg_processed']
        self.rosbag_proc = None
        self.start_rosbag()
        self.get_logger().info(f"Started rosbag recording to {self.output_dir} (MCAP format)")

    def start_rosbag(self):
        cmd = [
            'ros2', 'bag', 'record',
            '-o', self.output_dir,
            '--storage', 'mcap',
        ] + self.topics
        self.rosbag_proc = subprocess.Popen(cmd)

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
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
