import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    """
    Generates a launch description for the relevant EEG pipeline nodes: Neurosity, OpenBCI, and EEG simulator.
    """
    ld = LaunchDescription()

    # Add EEGSaver node for raw EEG
    raw_eeg_saver = Node(
        package='healthcare_msgs_demonstration',
        executable='eeg_json_saver.py',
        name='raw_eeg_saver',
        parameters=[
            {'topic': '/eeg/raw'},
            {'file_path': str(os.path.expanduser('~/neurosity_logs/raw_eeg.jsonl'))}
        ]
    )
    ld.add_action(raw_eeg_saver)

    # Add EEGSaver node for preprocessed EEG
    preprocessed_eeg_saver = Node(
        package='healthcare_msgs_demonstration',
        executable='eeg_json_saver.py',
        name='preprocessed_eeg_saver',
        parameters=[
            {'topic': '/eeg/processed'},
            {'file_path': str(os.path.expanduser('~/neurosity_logs/preprocessed_eeg.jsonl'))}
        ]
    )
    ld.add_action(preprocessed_eeg_saver)

    return ld
