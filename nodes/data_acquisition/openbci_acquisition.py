#!/usr/bin/env python3
"""
OpenBCI EEG Driver Node

Connects to an OpenBCI Cyton board via USB serial and publishes EEG data to standardized ROS2 topics.
Supports 8 or 16 channels (with daisy board).
"""
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, DurabilityPolicy
from healthcare_msgs.msg import EEG, EEGInfo
import numpy as np
from openbci_v3 import OpenBCICyton
import uuid
from collections import deque

class OpenBCINode(Node):
    def __init__(self, sample_rate=250, batch_size=10, channel_count=8, port='/dev/ttyUSB0', daisy=False):
        super().__init__('openbci_driver')
        self.session_id = str(uuid.uuid4())
        self.channel_count = channel_count
        self.sample_rate = sample_rate
        self.batch_size = batch_size
        self.sample_buffer = deque(maxlen=batch_size)
        
        # Create QoS profile with transient local durability for EEGInfo (latching)
        info_qos = QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL)
        
        # Publishers - using standardized topic names
        self.publisher_eeg = self.create_publisher(EEG, '/eeg/raw', 10)
        self.publisher_info = self.create_publisher(EEGInfo, '/eeg/raw_info', qos_profile=info_qos)

        self.get_logger().info(f"OpenBCI ROS 2 driver started. Session: {self.session_id}")
        self.get_logger().info(f"Port: {port}, Channels: {channel_count}, Daisy: {daisy}")

        # Setup OpenBCI board
        self.board = OpenBCICyton(port=port, daisy=daisy)
        self.board.start_stream(self.callback)

        self.info_published = False

    def callback(self, sample):
        # Store sample in buffer
        self.sample_buffer.append(sample.channels)

        # Once buffer is full, publish EEG message
        if len(self.sample_buffer) >= self.batch_size:
            batch = np.array(self.sample_buffer).T  # shape: (channels, batch_size)
            eeg_msg = EEG()
            eeg_msg.header.stamp = self.get_clock().now().to_msg()
            eeg_msg.header.frame_id = 'openbci'
            eeg_msg.session_id = self.session_id
            eeg_msg.sample_size = self.batch_size
            eeg_msg.eeg = batch.flatten().tolist()
            eeg_msg.quality = [1.0] * self.channel_count
            self.publisher_eeg.publish(eeg_msg)

            # Clear buffer
            self.sample_buffer.clear()

            # Publish EEGInfo once
            if not self.info_published:
                info_msg = EEGInfo()
                info_msg.device_info.session_id = self.session_id
                info_msg.device_info.device_name = 'OpenBCI Cyton'
                info_msg.device_info.manufacturer = 'OpenBCI'
                info_msg.device_info.serial_number = 'UNKNOWN'
                info_msg.channel_size = self.channel_count
                info_msg.units = EEGInfo.UNIT_UV
                info_msg.selected_preprocessing = []
                info_msg.montage_type = EEGInfo.MONTAGE_TYPE_REFERENTIAL
                info_msg.placement_method = [EEGInfo.PLACEMENT_METHOD_1020] * self.channel_count
                info_msg.electrode_sites = [EEGInfo.ELECTRODE_UNKNOWN] * self.channel_count
                info_msg.electrode_physical_type = [EEGInfo.ELECTRODE_PHYSICAL_DRY] * self.channel_count
                info_msg.signal_mode = EEGInfo.SIGNAL_MODE_SURFACE
                self.publisher_info.publish(info_msg)
                self.get_logger().info('Published EEGInfo metadata')
                self.info_published = True


def main(args=None):
    rclpy.init(args=args)
    
    # Parse command line arguments for OpenBCI configuration
    import sys
    port = '/dev/ttyUSB0'
    channel_count = 8
    daisy = False
    
    for i, arg in enumerate(sys.argv):
        if '--port' in arg and i + 1 < len(sys.argv):
            port = sys.argv[i + 1]
        elif '--channels' in arg and i + 1 < len(sys.argv):
            channel_count = int(sys.argv[i + 1])
            daisy = (channel_count == 16)
    
    node = OpenBCINode(batch_size=10, channel_count=channel_count, port=port, daisy=daisy)
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('Shutting down OpenBCI driver...')
    finally:
        node.board.stop_stream()
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
