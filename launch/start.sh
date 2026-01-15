#!/usr/bin/env bash


# Native start script: activates venv, sources ROS2, builds workspace if needed, and can launch nodes or rqt.

set -euo pipefail

VENV_PATH="${VENV_PATH:-$HOME/neurosity-venv}"
WORKSPACE="${WORKSPACE:-$HOME/ros2_ws}"
ROS_DISTRO="${ROS_DISTRO:-jazzy}"
REBUILD="${REBUILD:-0}"
NO_BUILD="${NO_BUILD:-0}"

usage() {
    cat <<EOF
Usage: $0 [options] [command]

Commands:
  run         Start neurosity_driver node (ros2 run neurosity_driver neurosity_driver)
  rqt         Start rqt with correct overlays
  help        Show this help

Environment variables:
  VENV_PATH   Path to Python venv (default: $VENV_PATH)
  WORKSPACE   Path to ROS2 workspace (default: $WORKSPACE)
  ROS_DISTRO  ROS2 distro (default: $ROS_DISTRO)
Commands:
  run                      nach Setup den node `neurosity_driver` starten (ros2 run)
  help                     diese Hilfe anzeigen
  rqt                      starte rqt mit korrekten ROS2 Overlays

Beispiel:
  ROS_DISTRO=humble VENV_PATH=~/venv $0 run
EOF
}

if [ "${1:-}" = "help" ] || [ "${1:-}" = "--help" ]; then
    usage
    exit 0
fi

if [ "${1:-}" = "rqt" ]; then
    echo "Cleaning Snap and VSCode environment variables for rqt..."
    # Unset all known Snap and VSCode variables
    unset LD_LIBRARY_PATH
    unset LOCPATH
    unset GTK_PATH
    unset GTK_EXE_PREFIX
    unset GIO_MODULE_DIR
    unset XDG_DATA_HOME
    unset XDG_DATA_DIRS
    unset GSETTINGS_SCHEMA_DIR
    unset GTK_IM_MODULE_FILE
    unset SNAP
    unset SNAP_NAME
    unset SNAP_REVISION
    unset SNAP_ARCH
    unset SNAP_LIBRARY_PATH
    unset SNAP_VERSION
    unset SNAP_DATA
    unset SNAP_COMMON
    unset SNAP_USER_COMMON
    unset SNAP_USER_DATA
    unset SNAP_INSTANCE_NAME
    unset SNAP_INSTANCE_KEY
    unset SNAP_COOKIE
    unset SNAP_REAL_HOME
    export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
    set +u
    source /opt/ros/$ROS_DISTRO/setup.bash
    source "$WORKSPACE/install/setup.bash"
    set -u
    export LD_LIBRARY_PATH="/opt/ros/$ROS_DISTRO/lib:$LD_LIBRARY_PATH"
    rqt
    exit 0
fi

echo "--- Starting environment setup ---"

# 1) Activate venv if present
if [ -d "$VENV_PATH" ]; then
    echo "Activating Python virtual environment: $VENV_PATH"
    # shellcheck source=/dev/null
    source "$VENV_PATH/bin/activate"
else
    echo "Venv not found at $VENV_PATH. Creating a new one..."
    python3 -m venv "$VENV_PATH"
    # shellcheck source=/dev/null
    source "$VENV_PATH/bin/activate"
    echo "Created and activated venv at $VENV_PATH"
fi

# Ensure pip is recent
python -m pip install --upgrade pip >/dev/null

# 2) Source ROS 2
ROS2_SETUP="/opt/ros/$ROS_DISTRO/setup.bash"
if [ -f "$ROS2_SETUP" ]; then
    echo "Sourcing ROS 2 setup: $ROS2_SETUP (ROS_DISTRO=$ROS_DISTRO)"
    # shellcheck source=/dev/null
    # Temporarily disable 'nounset' (-u) because some ROS setup scripts
    # reference variables that may be unset in this shell. Restore afterward.
    set +u
    source "$ROS2_SETUP"
    set -u
else
    echo "ERROR: ROS 2 setup not found at $ROS2_SETUP"
    echo "Set a valid ROS_DISTRO or install ROS 2. Aborting."
    exit 1
fi

# 3) Check for essential python packages used during ROS interface generation
echo "Ensuring build-time Python packages (empy) and runtime deps are installed in venv..."
pip_install_if_missing() {
    pkg="$1"
    if ! python -c "import $pkg" &>/dev/null; then
        echo "Installing missing Python package: $pkg"
        pip install "$2"
    else
        echo "Python package '$pkg' already installed"
    fi
}

# empy provides module 'em' used by rosidl_adapter
pip_install_if_missing em empy
pip_install_if_missing neurosity neurosity
pip_install_if_missing dotenv python-dotenv

# 4) Change to workspace
if [ -d "$WORKSPACE" ]; then
    cd "$WORKSPACE"
    echo "Changed to workspace: $WORKSPACE"
else
    echo "ERROR: Workspace not found at $WORKSPACE"
    exit 1
fi

# 5) Install system dependencies via rosdep (idempotent)
if command -v rosdep >/dev/null 2>&1; then
    echo "Running rosdep to install system dependencies (may ask for sudo)..."
    sudo rosdep update || true
    rosdep install --from-paths src --ignore-src -r -y || true
else
    echo "rosdep not found — please install and run 'rosdep install --from-paths src --ignore-src -r -y' manually"
fi

# 6) Decide whether to build
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

if [ "$BUILD_NEEDED" -eq 1 ]; then
    echo "Building workspace (colcon build)..."
    # prefer building the needed packages first, then fallback to full build
    if command -v colcon >/dev/null 2>&1; then
        colcon build --packages-select healthcare_msgs neurosity_driver --symlink-install || {
            echo "First attempt failed; trying full rebuild..."
            colcon build --symlink-install || { echo "colcon build failed twice. Aborting."; exit 1; }
        }
    else
        echo "colcon not found. Install colcon and try again. Aborting."
        exit 1
    fi
else
    echo "Build not required. Skipping colcon.";
fi

# 7) Source overlay if present
if [ -f "$WORKSPACE/install/setup.bash" ]; then
    # shellcheck source=/dev/null
    set +u
    source "$WORKSPACE/install/setup.bash"
    set -u
    echo "Sourced workspace overlay: $WORKSPACE/install/setup.bash"
fi

# Always build healthcare_msgs and source overlays before running nodes or rqt
if [ -d "$WORKSPACE" ]; then
    cd "$WORKSPACE"
    echo "Building healthcare_msgs package..."
    colcon build --packages-select healthcare_msgs || { echo "Failed to build healthcare_msgs"; exit 1; }
    if [ -f "$WORKSPACE/install/setup.bash" ]; then
        set +u
        source "$WORKSPACE/install/setup.bash"
        set -u
        echo "Sourced workspace overlay: $WORKSPACE/install/setup.bash"
    fi
    cd - >/dev/null
fi

echo "--- Setup complete. Environment ready. ---"

# Start the node in background by default (can be disabled with RUN_NODE=0)
RUN_NODE="${RUN_NODE:-1}"
SIMULATE="${SIMULATE:-0}"  # Set SIMULATE=1 to use EEG simulator instead of real device

if [ "$RUN_NODE" -eq 1 ]; then
    LOG_DIR="${LOG_DIR:-$HOME/neurosity_logs}"
    mkdir -p "$LOG_DIR"
    
    if [ "$SIMULATE" -eq 1 ]; then
        echo "Starting EEG SIMULATOR (not real device)..."
        SIM_LOG_FILE="$LOG_DIR/eeg_simulator.log"
        SIM_SCRIPT="$WORKSPACE/src/-healthcare_msgs_demonstration/nodes/eeg_simulator.py"
        
        cd "$WORKSPACE" || { echo "ERROR: Could not cd to $WORKSPACE"; exit 1; }
        
        nohup "$VENV_PATH/bin/python3" "$SIM_SCRIPT" >> "$SIM_LOG_FILE" 2>&1 &
        SIM_PID=$!
        echo "EEG simulator started with PID $SIM_PID. Logs: $SIM_LOG_FILE"
        echo "$SIM_PID" > "$LOG_DIR/eeg_simulator.pid"
    else
        # Start neurosity_driver node
        echo "Starting neurosity_driver node in the background..."
        LOG_FILE="$LOG_DIR/neurosity_driver.log"
        
        # Change to package directory so load_dotenv() can find .env file
        PACKAGE_DIR="$WORKSPACE/src/-healthcare_msgs_demonstration/ros2_hc_drv/neurosity_driver"
        
        cd "$PACKAGE_DIR" || { echo "ERROR: Could not cd to $PACKAGE_DIR"; exit 1; }
        
        # Ensure venv python is used; install missing deps if needed
        "$VENV_PATH/bin/python3" -m pip install --quiet python-dotenv neurosity 2>/dev/null || true
        
        # Use full path to python in venv to run the driver module directly
        nohup "$VENV_PATH/bin/python3" -m neurosity_driver.neurosity_driver >> "$LOG_FILE" 2>&1 &
        NODE_PID=$!
        echo "neurosity_driver started with PID $NODE_PID. Logs: $LOG_FILE"
        echo "$NODE_PID" > "$LOG_DIR/neurosity_driver.pid"
    fi
    
    # Start eeg_saver node
    echo "Starting eeg_saver node in the background..."

    # Default to JSON saver unless USE_ROSBAG=1 is set (handle unset variable safely)
    if [ "${USE_ROSBAG:-0}" = "1" ]; then
        echo "Starting EEG rosbag saver node (MCAP)..."
        SAVER_LOG_FILE="$LOG_DIR/eeg_rosbag_saver.log"
        SAVER_SCRIPT="$WORKSPACE/src/-healthcare_msgs_demonstration/nodes/eeg_rosbag_saver.py"
        nohup "$VENV_PATH/bin/python3" "$SAVER_SCRIPT" >> "$SAVER_LOG_FILE" 2>&1 &
        SAVER_PID=$!
        echo "eeg_rosbag_saver started with PID $SAVER_PID. Logs: $SAVER_LOG_FILE"
        echo "$SAVER_PID" > "$LOG_DIR/eeg_rosbag_saver.pid"
    else
        echo "Starting EEG JSON saver node..."
        SAVER_LOG_FILE="$LOG_DIR/eeg_json_saver.log"
        SAVER_SCRIPT="$WORKSPACE/src/-healthcare_msgs_demonstration/nodes/eeg_json_saver.py"
        nohup "$VENV_PATH/bin/python3" "$SAVER_SCRIPT" >> "$SAVER_LOG_FILE" 2>&1 &
        SAVER_PID=$!
        echo "eeg_json_saver started with PID $SAVER_PID. Logs: $SAVER_LOG_FILE"
        echo "$SAVER_PID" > "$LOG_DIR/eeg_json_saver.pid"
    fi
    
    # Start EEG Preprocessor node (optional)
    echo "Starting eeg_preprocessor node in the background..."
    PREPROC_LOG_FILE="$LOG_DIR/eeg_preprocessor.log"
    PREPROC_SCRIPT="$WORKSPACE/src/-healthcare_msgs_demonstration/nodes/eeg_preprocessing/preprocessing.py"
    if [ -f "$PREPROC_SCRIPT" ]; then
        nohup "$VENV_PATH/bin/python3" "$PREPROC_SCRIPT" >> "$PREPROC_LOG_FILE" 2>&1 &
        PREPROC_PID=$!
        echo "eeg_preprocessor started with PID $PREPROC_PID. Logs: $PREPROC_LOG_FILE"
        echo "$PREPROC_PID" > "$LOG_DIR/eeg_preprocessor.pid"
    else
        echo "Preprocessor script not found at $PREPROC_SCRIPT; skipping preprocessor start"
    fi
fi

# Visualization mode: offline (default), rqt, or none
VISUALIZATION_MODE="${VISUALIZATION_MODE:-offline}"

if [ "$VISUALIZATION_MODE" = "rqt" ]; then
    echo "Starting rqt EEG visualization plugin..."
    # Launch rqt plugin (assume correct overlay sourced)
    # Ensure the rqt plugin is discoverable in the new location
    export RQT_PLUGIN_PATH="$WORKSPACE/src/-healthcare_msgs_demonstration/visualization/eeg_visualization_rqt"
    rqt --standalone eeg_visualization_rqt &
elif [ "$VISUALIZATION_MODE" = "offline" ]; then
    echo "Starting offline EEG plotting script..."
    python3 visualization/plot_eeg_offline.py &
else
    echo "Visualization disabled."
fi

# Optionally launch rqt EEG visualization plugin in container
RUN_RQT="${RUN_RQT:-0}"
if [ "$RUN_RQT" -eq 1 ]; then
    echo "Launching rqt EEG visualization plugin in Docker container..."
    docker build -t ros2-rqt "$WORKSPACE" || { echo "Docker build failed"; exit 1; }
    xhost +local:root
    docker run -it --rm \
    SIMULATE="${SIMULATE:-1}"  # Default: use EEG simulator. Set SIMULATE=0 for real device.
        -v /tmp/.X11-unix:/tmp/.X11-unix \
        -v "$WORKSPACE":/home/devuser/ros2_ws \
        ros2-rqt bash -c "source /opt/ros/humble/setup.bash && cd /home/devuser/ros2_ws && colcon build && source install/setup.bash && rqt"
    xhost -local:root
fi

echo ""
echo "============================================"
echo "Startup complete!"
echo "============================================"
echo ""

if [ "$RUN_NODE" -eq 1 ]; then
    if [ "$SIMULATE" -eq 1 ]; then
        echo "Running in SIMULATOR MODE (test data, no real device needed)"
        echo ""
        echo "Nodes started:"
        echo "  - eeg_simulator (PID: $(cat $LOG_DIR/eeg_simulator.pid 2>/dev/null || echo '?'))"
    else
        echo "Running with REAL NEUROSITY DEVICE"
        echo ""
        echo "Nodes started:"
        echo "  - neurosity_driver (PID: $(cat $LOG_DIR/neurosity_driver.pid 2>/dev/null || echo '?'))"
    fi
    # Show which saver node is running and its PID/log
    if [ "${USE_ROSBAG:-0}" = "1" ]; then
        echo "  - eeg_rosbag_saver (PID: $(cat $LOG_DIR/eeg_rosbag_saver.pid 2>/dev/null || echo '?'))"
        echo "  - Saver:     tail -f $LOG_DIR/eeg_rosbag_saver.log"
    else
        echo "  - eeg_json_saver (PID: $(cat $LOG_DIR/eeg_json_saver.pid 2>/dev/null || echo '?'))"
        echo "  - Saver:     tail -f $LOG_DIR/eeg_json_saver.log"
    fi
    echo ""
    echo "EEG data file (JSONL format):"
    echo "  $LOG_DIR/eeg_data.jsonl"
    echo ""
    echo "View stored data:"
    echo "  head -1 $LOG_DIR/eeg_data.jsonl | python3 -m json.tool"
    echo ""
    echo "Stop all nodes:"
    if [ "$SIMULATE" -eq 1 ]; then
        if [ "${USE_ROSBAG:-0}" = "1" ]; then
            echo "  kill \$(cat $LOG_DIR/eeg_simulator.pid) \$(cat $LOG_DIR/eeg_rosbag_saver.pid)"
        else
            echo "  kill \$(cat $LOG_DIR/eeg_simulator.pid) \$(cat $LOG_DIR/eeg_json_saver.pid)"
        fi
    else
        if [ "${USE_ROSBAG:-0}" = "1" ]; then
            echo "  kill \$(cat $LOG_DIR/neurosity_driver.pid) \$(cat $LOG_DIR/eeg_rosbag_saver.pid)"
        else
            echo "  kill \$(cat $LOG_DIR/neurosity_driver.pid) \$(cat $LOG_DIR/eeg_json_saver.pid)"
        fi
    fi
else
    LOG_DIR="${LOG_DIR:-$HOME/neurosity_logs}"
    echo "Nodes are not running (RUN_NODE=0)."
    echo "To enable auto-start, use: RUN_NODE=1 ./start.sh"
    echo ""
    echo "To use simulator (no device needed):"
    echo "  SIMULATE=1 RUN_NODE=1 ./start.sh"
fi
#chmod +x /home/tjalf/ros2_ws/src/-healthcare_msgs-demonstration/start.sh && /home/tjalf/ros2_ws/src/-healthcare_msgs-demonstration/start.sh run
#source /home/tjalf/ros2_ws/src/-healthcare_msgs_demonstration/start.sh
