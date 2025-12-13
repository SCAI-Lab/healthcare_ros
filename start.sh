#!/usr/bin/env bash

# Optimiertes Start-Skript (Deutsch):
# - aktiviert das Python-venv
# - sourct ROS2 (konfigurierbar über ROS_DISTRO)
# - installiert fehlende Python-Build-Dependencies in venv (empy u.a.)
# - führt `rosdep install` aus (Systemabhängigkeiten)
# - baut workspace falls nötig (healthcare_msgs, neurosity_driver)
# - sourct install/setup.bash
# - optional: startet den Node mit 'run'

set -euo pipefail

VENV_PATH="${VENV_PATH:-$HOME/neurosity-venv}"
WORKSPACE="${WORKSPACE:-$HOME/ros2_ws}"
ROS_DISTRO="${ROS_DISTRO:-jazzy}"
REBUILD="${REBUILD:-0}"
NO_BUILD="${NO_BUILD:-0}"

usage() {
    cat <<EOF
Usage: $0 [options] [command]

Options (Umgebungsvariablen unterstützt):
  ROS_DISTRO=humble        setze ROS 2 Distribution (default: $ROS_DISTRO)
  VENV_PATH=/path/to/venv   virtuellen Python-Environment Pfad (default: $VENV_PATH)
  WORKSPACE=/path/to/ws     Workspace Pfad (default: $WORKSPACE)
  REBUILD=1                 zwinge colcon rebuild
  NO_BUILD=1                überspringe Build-Schritt

Commands:
  run                      nach Setup den node `neurosity_driver` starten (ros2 run)
  help                     diese Hilfe anzeigen

Beispiel:
  ROS_DISTRO=humble VENV_PATH=~/venv $0 run
EOF
}

if [ "${1:-}" = "help" ] || [ "${1:-}" = "--help" ]; then
    usage
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
        SIM_SCRIPT="$WORKSPACE/src/-healthcare_msgs_demonstration/eeg_simulator.py"
        
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
    SAVER_LOG_FILE="$LOG_DIR/eeg_saver.log"
    SAVER_SCRIPT="$WORKSPACE/src/-healthcare_msgs_demonstration/eeg_saver.py"
    
    cd "$WORKSPACE" || { echo "ERROR: Could not cd to $WORKSPACE"; exit 1; }
    
    nohup "$VENV_PATH/bin/python3" "$SAVER_SCRIPT" >> "$SAVER_LOG_FILE" 2>&1 &
    SAVER_PID=$!
    echo "eeg_saver started with PID $SAVER_PID. Logs: $SAVER_LOG_FILE"
    echo "$SAVER_PID" > "$LOG_DIR/eeg_saver.pid"
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
        echo "  - eeg_saver (PID: $(cat $LOG_DIR/eeg_saver.pid 2>/dev/null || echo '?'))"
    else
        echo "Running with REAL NEUROSITY DEVICE"
        echo ""
        echo "Nodes started:"
        echo "  - neurosity_driver (PID: $(cat $LOG_DIR/neurosity_driver.pid 2>/dev/null || echo '?'))"
        echo "  - eeg_saver (PID: $(cat $LOG_DIR/eeg_saver.pid 2>/dev/null || echo '?'))"
    fi
    echo ""
    echo "Logs:"
    if [ "$SIMULATE" -eq 1 ]; then
        echo "  - Simulator: tail -f $LOG_DIR/eeg_simulator.log"
    else
        echo "  - Driver:    tail -f $LOG_DIR/neurosity_driver.log"
    fi
    echo "  - Saver:     tail -f $LOG_DIR/eeg_saver.log"
    echo ""
    echo "EEG data file (JSONL format):"
    echo "  $LOG_DIR/eeg_data.jsonl"
    echo ""
    echo "View stored data:"
    echo "  head -1 $LOG_DIR/eeg_data.jsonl | python3 -m json.tool"
    echo ""
    echo "Stop all nodes:"
    if [ "$SIMULATE" -eq 1 ]; then
        echo "  kill \$(cat $LOG_DIR/eeg_simulator.pid) \$(cat $LOG_DIR/eeg_saver.pid)"
    else
        echo "  kill \$(cat $LOG_DIR/neurosity_driver.pid) \$(cat $LOG_DIR/eeg_saver.pid)"
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
