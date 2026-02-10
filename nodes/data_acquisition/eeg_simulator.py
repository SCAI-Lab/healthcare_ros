#!/usr/bin/env python3
"""
EEG Data Simulator Node

Generates realistic 4-channel EEG data at 150 Hz sampling rate and publishes to /eeg/raw topic.
Useful for testing and development without physical EEG hardware.

Features:
- 150 Hz sampling rate (realistic for clinical EEG)
- 30 samples per message at 5 Hz message rate (200ms intervals)
- 4 channels: FP1, FP2, F3, F4 (frontal electrode positions)
- **Eyes Open/Closed Simulation**: Alternates every 60 seconds
  * Eyes OPEN (0-60s, 120-180s, ...): Reduced alpha, increased beta, more eye artifacts
  * Eyes CLOSED (60-120s, 180-240s, ...): Strong alpha, reduced beta, minimal eye artifacts
- Realistic brain signal characteristics:
  * Alpha waves (8-12 Hz) - Dominant when eyes closed (alpha blocking when open)
  * Beta waves (13-30 Hz) - Active thinking, stronger when eyes open
  * Theta waves (4-8 Hz) - Drowsiness/meditation
  * Delta waves (0.5-4 Hz) - Deep relaxation
- Channel-specific characteristics:
  * FP1/FP2 (prefrontal): More eye artifacts, higher noise
  * F3/F4 (frontal): Less artifacts, cleaner signal
  * Hemispheric lateralization (left vs right differences)
- Realistic voltage ranges (10-100 μV typical EEG)
- Realistic artifacts: Eye movements (50-100 μV), blinks (80 μV), muscle (20 μV), 50Hz powerline

Topics:
- /eeg/raw (healthcare_msgs/EEG): Raw EEG samples
- /eeg/raw_info (healthcare_msgs/EEGInfo): Metadata (latched)

Usage:
    python3 eeg_simulator.py
    # Or via start.sh:
    USE_ACQUISITION=0 ./launch/start.sh
"""

import math
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, DurabilityPolicy
from rclpy.duration import Duration
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
        self.sampling_rate = 150  # Hz (realistic EEG sampling rate)
        self.num_channels = 4
        self.channel_names = ['FP1', 'FP2', 'F3', 'F4']
        self.samples_per_message = 30  # samples per message (150Hz / 5 msg/sec = 30 samples)
        self.message_interval = self.samples_per_message / self.sampling_rate  # 0.2s = 5 Hz message rate
        
        # Oscillation parameters for realistic brain signals
        self.time_offset = 0.0
        self.alpha_freq = 10.0  # Hz
        self.beta_freq = 20.0   # Hz
        self.theta_freq = 6.0   # Hz
        self.delta_freq = 2.0   # Hz
        
        # Eyes open/closed simulation (1 minute cycles)
        self.eyes_cycle_duration = 60.0  # seconds
        self.eyes_open = True  # Start with eyes open

        self.sample_count = 0
        self.message_count = 0
        self.info_published = False

        # Anchor simulated timestamps to avoid overlapping samples
        self.start_time = self.get_clock().now()
        
        # Timer for publishing messages
        self.timer = self.create_timer(self.message_interval, self.publish_eeg)
        
        self.get_logger().info(
            f'EEG Simulator started: {self.num_channels} channels, '
            f'{self.sampling_rate} Hz, {self.samples_per_message} samples/msg'
        )
    
    def generate_signal(self, channel, time_sec):
        """Generate realistic EEG-like signal for a channel.
        
        Combines multiple frequency components to simulate brain activity with:
        - Channel-specific characteristics (FP1/FP2 vs F3/F4)
        - Hemispheric lateralization (left vs right)
        - Eyes open/closed state changes (1-minute cycles)
        - Realistic voltage ranges (10-100 μV)
        - Realistic artifacts
        """
        import random
        
        # Determine eyes open/closed state (alternates every 60 seconds)
        cycle_position = time_sec % (2 * self.eyes_cycle_duration)
        self.eyes_open = cycle_position < self.eyes_cycle_duration
        
        # Channel-specific properties
        is_prefrontal = (channel < 2)  # FP1, FP2
        is_left_hemisphere = (channel % 2 == 0)  # FP1, F3
        
        # Base phase shift for spatial variation
        phase_shift = channel * (math.pi / 6)
        
        # === ALPHA WAVES (8-12 Hz) - Strongest when eyes closed ===
        if self.eyes_open:
            # Eyes open: Greatly reduced alpha (alpha blocking)
            alpha_amplitude = 8.0  # μV
        else:
            # Eyes closed: Strong alpha waves (relaxed, awake state)
            alpha_amplitude = 35.0  # μV
        
        # Posterior channels would have more alpha, but we only have frontal
        # Still show alpha modulation in frontal regions
        alpha = alpha_amplitude * math.sin(2 * math.pi * self.alpha_freq * time_sec + phase_shift)
        
        # === BETA WAVES (13-30 Hz) - Active thinking, more in frontal ===
        if self.eyes_open:
            # Eyes open: Increased beta (active processing)
            beta_amplitude = 15.0 if is_prefrontal else 12.0  # μV
        else:
            # Eyes closed: Reduced beta
            beta_amplitude = 8.0 if is_prefrontal else 6.0  # μV
        
        beta = beta_amplitude * math.sin(2 * math.pi * self.beta_freq * time_sec + phase_shift * 1.5)
        
        # === THETA WAVES (4-8 Hz) - Drowsiness, meditation ===
        # More prominent when eyes closed and relaxed
        theta_amplitude = 10.0 if not self.eyes_open else 5.0  # μV
        theta = theta_amplitude * math.sin(2 * math.pi * self.theta_freq * time_sec + phase_shift * 0.5)
        
        # === DELTA WAVES (0.5-4 Hz) - Deep relaxation ===
        delta_amplitude = 12.0 if not self.eyes_open else 4.0  # μV
        delta = delta_amplitude * math.sin(2 * math.pi * self.delta_freq * time_sec + phase_shift * 0.3)
        
        # === HEMISPHERIC LATERALIZATION ===
        # Right hemisphere slightly more active in spatial processing (eyes open)
        # Left hemisphere slightly more active in language processing
        if is_left_hemisphere:
            lateralization_factor = 1.0 + (0.1 if self.eyes_open else 0.05)
        else:
            lateralization_factor = 1.0 + (0.15 if self.eyes_open else 0.05)
        
        # Combine brain rhythms
        signal = (alpha + beta + theta + delta) * lateralization_factor
        
        # === REALISTIC NOISE COMPONENTS ===
        
        # 1. White noise (continuous background) - 2-5 μV
        white_noise = random.gauss(0, 3.0)
        
        # 2. Low-frequency drift and DC offset - will be removed by high-pass filter
        # Add significant DC offset that varies per channel
        dc_offset = 20.0 * (channel + 1)  # 20, 40, 60, 80 μV per channel
        drift = dc_offset + 10.0 * math.sin(2 * math.pi * 0.05 * time_sec)  # 0.05 Hz slow drift
        
        # 3. 50 Hz powerline interference (European standard)
        powerline = 1.5 * math.sin(2 * math.pi * 50 * time_sec)
        
        # 4. Common-mode noise affecting all channels (removed by CAR)
        common_mode_noise = 5.0 * math.sin(2 * math.pi * 0.3 * time_sec)
        
        # 5. Muscle artifacts (EMG) - random bursts, more when eyes open
        muscle_probability = 0.08 if self.eyes_open else 0.03
        if random.random() < muscle_probability:
            muscle_artifact = random.gauss(0, 20)  # 20 μV bursts
        else:
            muscle_artifact = 0
        
        # 5. Eye movement artifacts - MUCH stronger in prefrontal channels (FP1, FP2)
        if is_prefrontal and self.eyes_open:
            # Eye movements and blinks when eyes open
            if random.random() < 0.03:  # 3% chance of eye movement
                eye_artifact = random.gauss(0, 50)  # 50-100 μV (very large!)
            elif random.random() < 0.015:  # 1.5% chance of blink
                eye_artifact = random.gauss(0, 80)  # Blinks are even larger
            else:
                eye_artifact = 0
        elif is_prefrontal and not self.eyes_open:
            # Occasional slow eye movements even with closed eyes
            if random.random() < 0.01:
                eye_artifact = random.gauss(0, 25)
            else:
                eye_artifact = 0
        else:
            # F3, F4 less affected by eye artifacts
            eye_artifact = random.gauss(0, 5) if random.random() < 0.01 else 0
        
        # 6. Channel-specific noise (prefrontal channels are noisier)
        channel_noise_factor = 1.4 if is_prefrontal else 1.0
        
        return (signal + white_noise + drift + powerline + muscle_artifact + eye_artifact + common_mode_noise) * channel_noise_factor
    
    def publish_eeg(self):
        """Publish a simulated EEG message."""
        eeg_msg = EEG()
        message_time = self.start_time + Duration(seconds=self.sample_count / self.sampling_rate)
        eeg_msg.header.stamp = message_time.to_msg()
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
            eyes_state = "OPEN" if self.eyes_open else "CLOSED"
            self.get_logger().info(
                f'Published {self.message_count} EEG messages '
                f'({self.sample_count} samples, {self.time_offset:.1f}s elapsed) - Eyes: {eyes_state}'
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
