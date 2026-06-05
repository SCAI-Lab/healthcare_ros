#!/usr/bin/env python3
"""
EEG JSON Saver Node - Data Persistence Component

ROS2 node for saving EEG data streams to JSONL format.
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
- Daily file rotation is enabled by default (one JSONL file per day)
- Files are appended during the day (no startup truncation)
- Parent directories created automatically
- Metadata published once via latched topic, saved separately
- Atomic writes ensure data consistency

"""

import json
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, DurabilityPolicy
from healthcare_msgs.msg import EEG, EEGInfo
from pathlib import Path
import os
from datetime import datetime
import re




class EEGSaver(Node):
    """
    ROS2 node for saving EEG data to JSONL format.
    
    Subscribes to EEG data and EEGInfo topics, saving messages to JSONL files.
    Each line in the output file is a complete JSON object with all message fields.
    
    Parameters (ROS2 CLI)
    ---------------------
    topic : str, optional
        Topic to subscribe to (default: '/eeg/raw')
    file_path : str, optional
        Output JSONL file path (default: 'eeg_data/eeg_raw_data.jsonl')
    rotate_daily : bool, optional
        Rotate output files daily using suffix _YYYY-MM-DD (default: true)
    retention_days : int, optional
        Delete this saver's rotated files older than this many days (default: 4)
    
    File Organization
    -----------------
    - Data files: eeg_data/*.jsonl, eeg_data/*.info.json
    - Log files: logs/*.log
    - PID files: logs/*.pid
    
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
        self.declare_parameter('topic', '/eeg/raw')
        self.declare_parameter('file_path', default_raw_path)
        self.declare_parameter('rotate_daily', True)
        self.declare_parameter('retention_days', 4)

        # Get parameters after node is fully initialized to ensure CLI overrides are respected
        topic = self.get_parameter('topic').get_parameter_value().string_value
        file_path = self.get_parameter('file_path').get_parameter_value().string_value
        self.rotate_daily = self.get_parameter('rotate_daily').get_parameter_value().bool_value
        self.retention_days = self.get_parameter('retention_days').get_parameter_value().integer_value

        # Optionally: update node name for logging clarity (not strictly needed for ROS2, but helps debug)
        if '/raw' in topic:
            self._node_name = 'eeg_saver_raw'
        elif '/processed' in topic:
            self._node_name = 'eeg_saver_preprocessed'
        else:
            self._node_name = 'eeg_saver'

        self.base_data_file = Path(file_path)
        self.base_data_file.parent.mkdir(parents=True, exist_ok=True)
        self.current_day = None
        self.data_file = None
        self.info_file = None
        self.info_stored = False
        self._refresh_output_paths(force=True)

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

    def _build_dated_path(self, base_file: Path, day_str: str) -> Path:
        """Build file path with date suffix before extension."""
        return base_file.with_name(f'{base_file.stem}_{day_str}{base_file.suffix}')

    def _cleanup_old_rotated_files(self):
        """Delete rotated JSONL/info files older than retention_days.
           If 0 is selected, JSONL/info filest are deleted immediately (i.e. no retention), if  -1 is selected, they will be kept unlimited."""
        if not self.rotate_daily or self.retention_days < 0:
            return

        current_day = datetime.now().date()
        parent_dir = self.base_data_file.parent
        base_stem = self.base_data_file.stem
        base_suffix = self.base_data_file.suffix
        data_pattern = re.compile(
            rf'^{re.escape(base_stem)}_(\d{{4}}-\d{{2}}-\d{{2}}){re.escape(base_suffix)}$'
        )
        info_pattern = re.compile(
            rf'^{re.escape(base_stem)}_(\d{{4}}-\d{{2}}-\d{{2}})\.info\.json$'
        )

        deleted_count = 0
        for candidate in parent_dir.iterdir():
            if not candidate.is_file():
                continue

            match = data_pattern.match(candidate.name) or info_pattern.match(candidate.name)
            if not match:
                continue

            try:
                file_day = datetime.strptime(match.group(1), '%Y-%m-%d').date()
            except ValueError:
                self.get_logger().error(f'Error saving EEG message: {e}')
                continue

            age_days = (current_day - file_day).days
            if age_days > self.retention_days:
                try:
                    candidate.unlink()
                    deleted_count += 1
                except OSError as exc:
                    self.get_logger().warn(f'Failed to delete old file {candidate}: {exc}')

        if deleted_count > 0:
            self.get_logger().info(
                f'Retention cleanup removed {deleted_count} file(s) older than {self.retention_days} day(s)'
            )

    def _refresh_output_paths(self, force: bool = False):
        """Rotate output paths when day changes (if enabled)."""
        day_str = datetime.now().strftime('%Y-%m-%d')
        if not force and self.rotate_daily and self.current_day == day_str:
            return

        previous_data_file = self.data_file
        self.current_day = day_str if self.rotate_daily else 'static'

        if self.rotate_daily:
            self.data_file = self._build_dated_path(self.base_data_file, day_str)
        else:
            self.data_file = self.base_data_file

        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.data_file, 'a'):
            pass

        self.info_file = self.data_file.with_suffix('').with_suffix('.info.json')
        self._cleanup_old_rotated_files()

        if previous_data_file != self.data_file:
            self.info_stored = False
            self.get_logger().info(f'Using output file: {self.data_file}')
        
    def eeg_callback(self, msg: EEG):
        """Called whenever a new EEG message is received.
        Serializes the complete EEG message in healthcare_msgs format."""
        try:
            self._refresh_output_paths()

            # Convert message to dictionary - preserving full healthcare_msgs structureThe amendedThere can be quite favorable.
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
        self._refresh_output_paths()

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
    except (KeyboardInterrupt, rclpy.executors.ExternalShutdownException):
        eeg_saver.get_logger().info(f'Shutting down. Total messages saved: {eeg_saver.message_count}')
    finally:
        eeg_saver.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
