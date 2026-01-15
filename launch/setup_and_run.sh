#!/usr/bin/env bash
# One-command setup and launch for native ROS2 EEG workflow
set -euo pipefail

# 1. Activate venv (create if missing)
VENV_PATH="${VENV_PATH:-$HOME/neurosity-venv}"
if [ ! -d "$VENV_PATH" ]; then
    python3 -m venv "$VENV_PATH"
fi
source "$VENV_PATH/bin/activate"

# 2. Install Python dependencies
pip install --upgrade pip
pip install numpy matplotlib rclpy empy python-dotenv neurosity


# 3. Source ROS2 and external healthcare_msgs workspace
ROS_DISTRO="${ROS_DISTRO:-jazzy}"
source "/opt/ros/$ROS_DISTRO/setup.bash"
if [ -f "$HOME/ros2_msgs_ws/install/setup.bash" ]; then
  source "$HOME/ros2_msgs_ws/install/setup.bash"
fi

# 4. Install system dependencies
cd ~/ros2_ws
sudo rosdep update
rosdep install --from-paths src --ignore-src -r -y


# 5. Build workspace and source overlay
colcon build
source install/setup.bash

# 6. Start all nodes and services
cd ~/ros2_ws/src/-healthcare_msgs_demonstration
./start.sh

# 7. Print status and next steps
cat <<EOF

============================================
Setup complete! All nodes/services started.

To check running nodes:
  ros2 node list
To check topics:
  ros2 topic list
To plot EEG data live:
  python3 live_eeg_plot.py
To launch rqt:
  ./start.sh rqt

Logs are in ~/neurosity_logs/
============================================
EOF
