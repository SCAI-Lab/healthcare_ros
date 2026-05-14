#!/usr/bin/env bash

# Native start script: activates venv, sources ROS2, builds workspace if needed, and launches nodes.

set -euo pipefail

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

VENV_PATH="${VENV_PATH:-$HOME/hcmd-venv}"
WORKSPACE="${WORKSPACE:-$HOME/ros2_ws}"
ROS_DISTRO="${ROS_DISTRO:-jazzy}"
REBUILD="${REBUILD:-0}"
NO_BUILD="${NO_BUILD:-0}"
PRODUCTION="${PRODUCTION:-0}"
DEBUG_SHELL="${DEBUG_SHELL:-0}"

usage() {
    cat <<EOF
Usage: $0 [options] [command]

Commands:
    help        Show this help

Environment variables:
    VENV_PATH   Path to Python venv
    WORKSPACE   Path to ROS2 workspace
    ROS_DISTRO  ROS2 distro
    PRODUCTION  Enable production preset

Example:
    PRODUCTION=1 $0
EOF
}

if [ "${1:-}" = "help" ] || [ "${1:-}" = "--help" ]; then
    usage
    exit 0
fi

echo "--- Starting environment setup ---"

# --------------------------------------------------
# Activate / create venv
# --------------------------------------------------

if [ -d "$VENV_PATH" ]; then
    echo "Activating Python virtual environment: $VENV_PATH"
    source "$VENV_PATH/bin/activate"
else
    echo "Venv not found at $VENV_PATH. Creating a new one..."

    python3 -m venv "$VENV_PATH"

    source "$VENV_PATH/bin/activate"

    echo "Created and activated venv at $VENV_PATH"
fi

# --------------------------------------------------
# Force all child processes to use this venv
# --------------------------------------------------

export VIRTUAL_ENV="$VENV_PATH"
export PATH="$VENV_PATH/bin:$PATH"
export PYTHONPATH="$VENV_PATH/lib/python3.12/site-packages:${PYTHONPATH:-}"
export ROS_PYTHON_EXECUTABLE="$VENV_PATH/bin/python3"

echo ""
echo "============================================"
echo "Python diagnostics"
echo "============================================"
echo "which python3: $(which python3)"
echo "python version: $(python3 --version)"
echo "VIRTUAL_ENV=${VIRTUAL_ENV:-NOT_SET}"
echo "ROS_PYTHON_EXECUTABLE=${ROS_PYTHON_EXECUTABLE:-NOT_SET}"
echo "PYTHONPATH=${PYTHONPATH:-NOT_SET}"
echo "============================================"
echo ""

# --------------------------------------------------
# Source ROS2
# --------------------------------------------------

ROS2_SETUP="/opt/ros/$ROS_DISTRO/setup.bash"

if [ -f "$ROS2_SETUP" ]; then
    echo "Sourcing ROS 2 setup: $ROS2_SETUP"

    set +u
    source "$ROS2_SETUP"
    set -u
else
    echo "ERROR: ROS 2 setup not found at $ROS2_SETUP"
    exit 1
fi

# --------------------------------------------------
# Python dependencies
# --------------------------------------------------

echo "Ensuring required Python packages are installed..."

pip install --upgrade pip setuptools wheel

pip install \
    empy \
    catkin_pkg \
    lark \
    numpy \
    scipy \
    matplotlib \
    pyyaml \
    python-dotenv \
    mne \
    influxdb-client \
    pyserial \
    neurosity

# --------------------------------------------------
# Change to workspace
# --------------------------------------------------

if [ -d "$WORKSPACE" ]; then
    cd "$WORKSPACE"
    echo "Changed to workspace: $WORKSPACE"
else
    echo "ERROR: Workspace not found at $WORKSPACE"
    exit 1
fi

# --------------------------------------------------
# rosdep
# --------------------------------------------------

if command -v rosdep >/dev/null 2>&1; then

    echo "Running rosdep..."

    sudo rosdep init 2>/dev/null || true

    rosdep update || true

    rosdep install \
        --from-paths src \
        --ignore-src \
        -r \
        -y || true

else
    echo "WARNING: rosdep not installed"
fi

# --------------------------------------------------
# Build decision
# --------------------------------------------------

BUILD_NEEDED=0

if [ "$NO_BUILD" = "1" ]; then
    BUILD_NEEDED=0
elif [ "$REBUILD" = "1" ]; then
    BUILD_NEEDED=1
elif [ ! -f "$WORKSPACE/install/setup.bash" ]; then
    BUILD_NEEDED=1
else
    if find "$WORKSPACE/src" -type f -newer "$WORKSPACE/install/setup.bash" | grep -q .; then
        BUILD_NEEDED=1
    fi
fi

# --------------------------------------------------
# Build workspace
# --------------------------------------------------

if [ "$BUILD_NEEDED" -eq 1 ]; then

    echo "Building workspace..."

    unset COLCON_PYTHON_INSTALLER

    rm -rf build install log

    # IMPORTANT:
    # DO NOT USE --symlink-install
    # It triggers editable installs in your environment

    colcon build || {

        echo ""
        echo "============================================"
        echo "BUILD FAILED"
        echo "============================================"
        exit 1
    }
fi

# --------------------------------------------------
# Source overlay
# --------------------------------------------------

if [ -f "$WORKSPACE/install/setup.bash" ]; then

    set +u
    source "$WORKSPACE/install/setup.bash"
    set -u

    echo "Workspace overlay sourced"
fi

echo ""
echo "============================================"
echo "Setup complete"
echo "============================================"
echo ""

# --------------------------------------------------
# Optional debug shell
# --------------------------------------------------

if [ "$DEBUG_SHELL" -eq 1 ]; then

    echo "Opening debug shell..."

    bash --noprofile --norc
fi

# --------------------------------------------------
# Runtime config
# --------------------------------------------------

RUN_NODE="${RUN_NODE:-1}"
USE_ACQUISITION="${USE_ACQUISITION:-0}"

LOG_DIR="$PROJECT_ROOT/logs"

mkdir -p "$LOG_DIR"

# --------------------------------------------------
# Simulator mode
# --------------------------------------------------

if [ "$RUN_NODE" -eq 1 ] && [ "$USE_ACQUISITION" -eq 0 ]; then

    echo "Starting EEG simulator..."

    SIM_SCRIPT="$PROJECT_ROOT/nodes/data_acquisition/eeg_simulator.py"

    nohup "$VENV_PATH/bin/python3" \
        "$SIM_SCRIPT" \
        >> "$LOG_DIR/eeg_simulator.log" 2>&1 &

    SIM_PID=$!

    echo "$SIM_PID" > "$LOG_DIR/eeg_simulator.pid"

    echo "Simulator PID: $SIM_PID"
fi

# --------------------------------------------------
# OpenBCI mode
# --------------------------------------------------

if [ "$RUN_NODE" -eq 1 ] && [ "$USE_ACQUISITION" -eq 1 ]; then

    echo "Starting OpenBCI driver..."

    set +u
    source "/opt/ros/$ROS_DISTRO/setup.bash"
    source "$WORKSPACE/install/setup.bash"
    set -u

    nohup ros2 run openbci_driver openbci_driver \
        >> "$LOG_DIR/openbci_driver.log" 2>&1 &

    NODE_PID=$!

    echo "$NODE_PID" > "$LOG_DIR/openbci_driver.pid"

    echo "OpenBCI PID: $NODE_PID"
fi

# --------------------------------------------------
# Neurosity mode
# --------------------------------------------------

if [ "$RUN_NODE" -eq 1 ] && [ "$USE_ACQUISITION" -eq 2 ]; then

    echo "Starting Neurosity driver..."

    set +u
    source "/opt/ros/$ROS_DISTRO/setup.bash"
    source "$WORKSPACE/install/setup.bash"
    set -u

    nohup ros2 run neurosity_driver neurosity_driver \
        >> "$LOG_DIR/neurosity_driver.log" 2>&1 &

    NODE_PID=$!

    echo "$NODE_PID" > "$LOG_DIR/neurosity_driver.pid"

    echo "Neurosity PID: $NODE_PID"
fi

echo ""
echo "============================================"
echo "Startup complete"
echo "============================================"
echo ""

echo "ROS topics:"
echo "  ros2 topic list"
echo ""

echo "Logs:"
echo "  tail -f logs/*.log"
echo ""

echo "Stop everything:"
echo "  pkill -f ros2"
echo "  pkill -f eeg"
echo ""