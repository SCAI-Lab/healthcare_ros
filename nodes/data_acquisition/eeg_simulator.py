#!/usr/bin/env python3
"""
EEG Data Simulator Node

Publishes simulated EEG data to the /neurosity/eeg topic in the correct
healthcare_msgs format. Useful for testing the eeg_saver without a physical device.

Simulates 4 channels of EEG data with realistic brain signal characteristics:
- Alpha waves (8-12 Hz)
- Beta waves (13-30 Hz)
- Theta waves (4-8 Hz)
"""

import math
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, DurabilityPolicy
from healthcare_msgs.msg import EEG, EEGInfo


class EEGSimulator(Node):
    def __init__(self):
        super().__init__('eeg_simulator')
        
        # Create QoS profile with transient local durability for EEGInfo (latching)
        info_qos = QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL)
        
        # Publishers
        self.eeg_pub = self.create_publisher(EEG, '/eeg/raw', 10)
        self.eeg_info_pub = self.create_publisher(EEGInfo, '/eeg/raw_info', qos_profile=info_qos)
        
        # Simulation parameters
        self.sampling_rate = 256  # Hz
        self.num_channels = 4
        self.channel_names = ['FP1', 'FP2', 'F3', 'F4']
        self.samples_per_message = 64  # samples per message
        self.message_interval = self.samples_per_message / self.sampling_rate
        
        # Oscillation parameters for realistic brain signals
        self.time_offset = 0.0
        self.alpha_freq = 10.0  # Hz
        self.beta_freq = 20.0   # Hz
        self.theta_freq = 6.0   # Hz
        
        self.sample_count = 0
        self.message_count = 0
        self.info_published = False
        
        # Timer for publishing messages
        self.timer = self.create_timer(self.message_interval, self.publish_eeg)
        
        self.get_logger().info(
            f'EEG Simulator started: {self.num_channels} channels, '
            f'{self.sampling_rate} Hz, {self.samples_per_message} samples/msg'
        )
    
    def generate_signal(self, channel, time_sec):
        """Generate realistic EEG-like signal for a channel.
        
        Combines multiple frequency components to simulate brain activity.
        Each channel has slightly different phase and amplitude for realism.
        """
        # Add slight phase shift per channel for spatial variation
        phase_shift = channel * (math.pi / 8)  # Smaller phase difference between channels
        
        # Alpha waves (8-12 Hz) - primary component, dominant in posterior regions
        alpha = 15.0 * math.sin(2 * math.pi * self.alpha_freq * time_sec + phase_shift)
        
        # Beta waves (13-30 Hz) - secondary component, more prominent in frontal regions
        beta = 8.0 * math.sin(2 * math.pi * self.beta_freq * time_sec + phase_shift * 1.5)
        
        # Theta waves (4-8 Hz) - tertiary component
        theta = 10.0 * math.sin(2 * math.pi * self.theta_freq * time_sec + phase_shift * 0.5)
        
        # Combine with channel-specific amplitude variation (±20%)
        amplitude_factor = 1.0 + 0.2 * math.sin(channel * math.pi / 4)
        signal = (alpha + beta + theta) * amplitude_factor
        
        # Add realistic EEG noise components
        import random
        
        # 1. White noise (continuous background)
        white_noise = random.gauss(0, 2.0)
        
        # 2. Low-frequency drift (DC offset changes)
        drift = 5.0 * math.sin(time_sec * 0.1 + channel)
        
        # 3. 50/60 Hz powerline interference
        powerline = 1.5 * math.sin(2 * math.pi * 50 * time_sec)
        
        # 4. Muscle artifacts (random bursts)
        if random.random() < 0.05:  # 5% chance of muscle artifact
            muscle_artifact = random.gauss(0, 15)
        else:
            muscle_artifact = 0
        
        # 5. Eye blink artifacts (mainly in frontal channels FP1, FP2)
        if channel < 2 and random.random() < 0.02:  # 2% chance in frontal channels
            blink_artifact = random.gauss(0, 30)
        else:
            blink_artifact = 0
        
        return signal + white_noise + drift + powerline + muscle_artifact + blink_artifact
    
    def publish_eeg(self):
        """Publish a simulated EEG message."""
        eeg_msg = EEG()
        eeg_msg.header.stamp = self.get_clock().now().to_msg()
        eeg_msg.header.frame_id = 'neurosity_simulator'
        eeg_msg.session_id = 'sim_session_001'
        eeg_msg.sample_size = self.samples_per_message
        
        # Generate flattened EEG data
        eeg_data = []
        quality_data = []
        
        for ch in range(self.num_channels):
            for s in range(self.samples_per_message):
                time_sec = (self.sample_count + s) / self.sampling_rate
                sample = self.generate_signal(ch, time_sec)
                eeg_data.append(sample)
            
            # Quality: simulate varying quality per channel
            quality = 0.85 + 0.1 * math.sin(self.time_offset + ch)
            quality_data.append(max(0.5, min(1.0, quality)))
        
        eeg_msg.eeg = eeg_data
        eeg_msg.quality = quality_data
        
        self.eeg_pub.publish(eeg_msg)
        self.message_count += 1
        self.sample_count += self.samples_per_message
        self.time_offset += self.message_interval
        
        # Publish EEGInfo once
        if not self.info_published:
            self.publish_eeg_info()
            self.info_published = True
        
        # Log progress every 10 messages
        if self.message_count % 10 == 0:
            self.get_logger().info(
                f'Published {self.message_count} EEG messages '
                f'({self.sample_count} samples, {self.time_offset:.1f}s elapsed)'
            )
    
    def publish_eeg_info(self):
        """Publish EEG metadata once."""
        info_msg = EEGInfo()
        info_msg.device_info.session_id = 'sim_session_001'
        info_msg.channel_size = self.num_channels
        info_msg.units = EEGInfo.UNIT_UV
        info_msg.selected_preprocessing = [
            EEGInfo.EEG_PREPROC_BANDPASS,
            EEGInfo.EEG_PREPROC_NOTCH
        ]
        info_msg.montage_type = EEGInfo.MONTAGE_TYPE_REFERENTIAL
        
        # Map channel names to electrode site enums
        info_msg.electrode_sites = [
            EEGInfo.ELECTRODE_FP1,  # FP1
            EEGInfo.ELECTRODE_FP2,  # FP2
            EEGInfo.ELECTRODE_F3,   # F3
            EEGInfo.ELECTRODE_F4,   # F4
        ]
        info_msg.electrode_physical_type = [
            EEGInfo.ELECTRODE_PHYSICAL_DRY
        ] * self.num_channels
        info_msg.placement_method = [
            EEGInfo.PLACEMENT_METHOD_1020
        ] * self.num_channels
        info_msg.signal_mode = EEGInfo.SIGNAL_MODE_SURFACE
        
        self.eeg_info_pub.publish(info_msg)
        self.get_logger().info('Published EEGInfo metadata')


def main(args=None):
    rclpy.init(args=args)
    simulator = EEGSimulator()
    
    try:
        rclpy.spin(simulator)
    except (KeyboardInterrupt, rclpy.executors.ExternalShutdownException):
        simulator.get_logger().info(f'Shutting down. Published {simulator.message_count} messages')
    finally:
        simulator.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
