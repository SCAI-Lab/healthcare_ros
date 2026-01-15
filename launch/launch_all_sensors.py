import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    """
    Generates a launch description for the relevant EEG pipeline nodes: Neurosity, OpenBCI, and EEG simulator.
    """
    ld = LaunchDescription()
    # Add Neurosity node
    # Example:
    # neurosity_node = Node(
    #     package='neurosity_driver',
    #     name='neurosity_driver',
    #     executable='neurosity_driver.py',
    #     parameters=['config/params.yaml']
    # )
    # ld.add_action(neurosity_node)

    # Add OpenBCI node
    # Example:
    # openbci_node = Node(
    #     package='openbci_driver',
    #     name='openbci_driver',
    #     executable='openbci_driver.py',
    #     parameters=['config/params.yaml']
    # )
    # ld.add_action(openbci_node)

    # Add EEG simulator node
    # Example:
    # eeg_simulator_node = Node(
    #     package='eeg_simulator',
    #     name='eeg_simulator',
    #     executable='eeg_simulator.py',
    #     parameters=['config/params.yaml']
    # )
    # ld.add_action(eeg_simulator_node)

    return ld
