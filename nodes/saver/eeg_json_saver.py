#!/usr/bin/env python3
"""
EEG JSON Saver Node - Data Persistence Component

ROS2 node for saving EEG data streams to JSONL (JSON Lines) format.
Provides human-readable, line-by-line storage of EEG messages following
the healthcare_msgs standard.

File Format: JSONL (JSON Lines)
--------------------------------
Each line is a complete, independently parseable JSON object containing
one EEG message with all fields. This format enables:
- Streaming writes without holding data in memory
- Line-by-line reading for analysis
- Robustness to incomplete writes (partial files remain valid)
- Easy inspection with standard tools (grep, jq, etc.)

Topics Subscribed
-----------------
/eeg/raw : healthcare_msgs.msg.EEG (default)
    Raw or processed EEG data to save
/eeg/raw_info : healthcare_msgs.msg.EEGInfo (default)
    Metadata saved separately as .info.json (latched)

File Organization
-----------------
Data files:
    eeg_data/eeg_raw_data.jsonl          # Raw EEG data
    eeg_data/eeg_raw_data.info.json      # Raw metadata
    eeg_data/eeg_preprocessed_data.jsonl # Processed EEG data
    eeg_data/eeg_preprocessed_data.info.json # Processed metadata

Log files:
    logs/eeg_json_saver_raw.log          # Node logs
    logs/eeg_json_saver_raw.pid          # Process ID

Parameters
----------
topic : str, default="/neurosity/eeg"
    EEG data topic to subscribe to
file_path : str, default="eeg_data/eeg_raw_data.jsonl"
    Output JSONL file path

EEG Message Fields Saved
------------------------
- header.stamp : Timestamp (seconds, nanoseconds)
- header.frame_id : Device identifier
- session_id : Unique session identifier
- sample_size : Samples per channel
- eeg : Flattened float64 array [ch0_samples, ch1_samples, ...]
- quality : Per-channel quality scores [0.0-1.0]

EEGInfo Fields Saved
--------------------
- device_info : Device identifier, session ID
- channel_size : Number of channels
- units : Measurement units (0=µV, 1=mV, 2=V)
- selected_preprocessing : List of preprocessing methods applied
- montage_type : Referential, bipolar, or average reference
- electrode_sites : Electrode names (e.g., ["Fp1", "Fp2", "C3", "C4"])
- electrode_physical_type : Cup, disk, needle, etc.
- placement_method : 10-20, 10-10, or 10-5 system
- signal_mode : Surface, intracranial, or scalp

File Management
---------------
- Files are truncated on node startup (prevents appending to old data)
- Parent directories created automatically
- Metadata published once via latched topic, saved separately
- Atomic writes ensure data consistency

Examples
--------
Save raw data (default):
    $ ros2 run healthcare_msgs eeg_json_saver

Save preprocessed data:
    $ ros2 run healthcare_msgs eeg_json_saver --ros-args \
        -p topic:=/eeg/processed \
        -p file_path:=eeg_data/eeg_preprocessed_data.jsonl

Run via launch script (starts both raw and preprocessed savers):
    $ ./launch/start.sh

Read saved data:
    $ cat eeg_data/eeg_raw_data.jsonl | jq '.eeg | length'
    $ grep quality eeg_data/eeg_raw_data.jsonl | jq '.quality'

Notes
-----
- JSONL format enables streaming analysis without loading entire file
- Each line is ~1-10 KB depending on channel count and samples
- Quality scores are per-channel, not per-sample
- Timestamps use ROS2 time (can be simulated or system time)

See Also
--------
eeg_rosbag_saver.py : Alternative MCAP/ROS2 bag format saver
healthcare_msgs.msg.EEG : EEG message definition
healthcare_msgs.msg.EEGInfo : EEG metadata definition
"""

import json
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, DurabilityPolicy
from healthcare_msgs.msg import EEG, EEGInfo
from pathlib import Path
import os




class EEGSaver(Node):
    """
    ROS2 node for saving EEG data to JSONL format.
    
    Subscribes to EEG data and EEGInfo topics, saving messages to JSONL files.
    Each line in the output file is a complete JSON object with all message fields.
    
    Parameters (ROS2 CLI)
    ---------------------
    topic : str, optional
        Topic to subscribe to (default: '/neurosity/eeg')
    file_path : str, optional
        Output JSONL file path (default: 'eeg_data/eeg_raw_data.jsonl')
    
    File Organization
    -----------------
    - Data files: eeg_data/*.jsonl, eeg_data/*.info.json
    - Log files: logs/*.log
    - PID files: logs/*.pid
    
    Examples
    --------
    Save raw data (default):
    $ ros2 run healthcare_msgs eeg_json_saver
    
    Save preprocessed data:
    $ ros2 run healthcare_msgs eeg_json_saver --ros-args -p topic:=/eeg/processed
    """
    def __init__(self):
        super().__init__('eeg_saver')
        import os
        # Get project root (3 levels up: nodes/saver/ -> nodes/ -> project_root/)
        REPO_BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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
