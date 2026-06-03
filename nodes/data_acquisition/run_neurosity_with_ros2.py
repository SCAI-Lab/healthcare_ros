#!/usr/bin/env python3
"""
ROS2 Neurosity Driver Launcher
Starts the Neurosity driver with proper environment setup
"""
import os
import sys
import subprocess

# Get workspace root from script location
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(SCRIPT_DIR)))
WORKSPACE_ROOT = os.path.dirname(os.path.dirname(PROJECT_ROOT))

# Setup environment
os.environ['ROS_DISTRO'] = os.environ.get('ROS_DISTRO', 'jazzy')

# Source ROS2 setup
ros2_setup = f"/opt/ros/{os.environ['ROS_DISTRO']}/setup.bash"
workspace_setup = f"{WORKSPACE_ROOT}/install/setup.bash"

# Build command to run with proper environment
cmd = f"""
source {ros2_setup} 2>/dev/null || true
source {workspace_setup} 2>/dev/null || true
ros2 run neurosity_driver neurosity_driver
"""

print("Starting Neurosity driver with ROS2 environment...")
print(f"Workspace: {WORKSPACE_ROOT}")
print(f"ROS2 Distro: {os.environ['ROS_DISTRO']}")

# Run with bash to source environment
os.execvp('bash', ['bash', '-c', cmd])
