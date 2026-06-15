#!/usr/bin/env bash
set -euo pipefail

# Get absolute path to script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
WORKSPACE_ROOT="$(cd "$PROJECT_ROOT/../.." && pwd)"

# Relative paths from workspace
HEALTHCARE_MSGS_PKG_PATH="$WORKSPACE_ROOT/src/healthcare_msgs"
HEALTHCARE_MSGS_PKG_ROOT="$(dirname "$HEALTHCARE_MSGS_PKG_PATH")"

VENV_PATH="${VENV_PATH:-$HOME/hcmd-venv}"
RUN_NODE="${RUN_NODE:-1}"
USE_ACQUISITION="${USE_ACQUISITION:-2}"  # 0=simulator, 1=OpenBCI, 2=Neurosity
DEBUG_SHELL="${DEBUG_SHELL:-0}"

LOG_DIR="$PROJECT_ROOT/logs"
mkdir -p "$LOG_DIR"

echo "=========================================="
echo "  Healthcare EEG Stack (venv-based)"
echo "=========================================="
echo "Config:"
echo "  WORKSPACE_ROOT: $WORKSPACE_ROOT"
echo "  PROJECT_ROOT: $PROJECT_ROOT"
echo "  RUN_NODE=$RUN_NODE"
echo "  USE_ACQUISITION=$USE_ACQUISITION (0=sim, 1=OpenBCI, 2=Neurosity)"
echo "  VENV=$VENV_PATH"
echo "=========================================="

# --------------------------------------------------
# Setup venv (use current Python)
# --------------------------------------------------

if [ ! -d "$VENV_PATH" ]; then
    echo "Creating venv..."
    python3 -m venv "$VENV_PATH"
fi

source "$VENV_PATH/bin/activate"

PYTHON_BIN="$VENV_PATH/bin/python"

ROS_DISTRO="${ROS_DISTRO:-jazzy}"
if [ -f "/opt/ros/$ROS_DISTRO/setup.bash" ]; then
    set +u
    source "/opt/ros/$ROS_DISTRO/setup.bash"
    set -u
    echo "Sourced ROS $ROS_DISTRO environment"
else
    echo "WARNING: /opt/ros/$ROS_DISTRO/setup.bash not found"
fi
if [ -f "$WORKSPACE_ROOT/install/setup.bash" ]; then
    set +u
    source "$WORKSPACE_ROOT/install/setup.bash"
    set -u
    echo "Sourced workspace install overlay"
fi

echo "Python: $(which python)"
echo "Version: $(python --version)"

# --------------------------------------------------
# Install dependencies in venv
# --------------------------------------------------

echo ""
echo "Installing/updating dependencies..."
"$PYTHON_BIN" -m pip install -q --upgrade pip setuptools wheel

"$PYTHON_BIN" -m pip install -q \
    numpy \
    scipy \
    matplotlib \
    pyyaml \
    python-dotenv \
    mne \
    influxdb-client \
    pyserial \
    pyOpenBCI \
    neurosity \
    rclpy \
    fastapi \
    uvicorn

# Install Python packages required for ROS message generation and colcon builds
# These are build-time dependencies (empy, lark-parser, catkin-pkg) that the
# ROS tooling expects to find in the active Python environment when generating
# and installing message type support.
"$PYTHON_BIN" -m pip install -q empy lark-parser catkin-pkg

# Optionally auto-build the workspace (set AUTO_BUILD=1 to enable)
if [ "${AUTO_BUILD:-0}" -eq 1 ]; then
    echo "Auto-building workspace (healthcare_msgs, neurosity_driver)..."
    set +u
    if [ -f "/opt/ros/$ROS_DISTRO/setup.bash" ]; then
        source "/opt/ros/$ROS_DISTRO/setup.bash"
    fi
    if [ -f "$WORKSPACE_ROOT/install/setup.bash" ]; then
        source "$WORKSPACE_ROOT/install/setup.bash"
    fi
    set -u
    (cd "$WORKSPACE_ROOT" && colcon build --packages-select healthcare_msgs neurosity_driver --symlink-install)
    echo "Build complete"
fi

# healthcare_msgs should be available from the sourced ROS workspace overlay.
if [ -d "$HEALTHCARE_MSGS_PKG_PATH" ]; then
    echo "Using workspace healthcare_msgs package at: $HEALTHCARE_MSGS_PKG_PATH"
fi

echo "Dependencies ready ✓"

# --------------------------------------------------
# Start Docker Compose (Dashboard + InfluxDB)
# --------------------------------------------------

echo ""
echo "Starting Docker Compose (Dashboard, InfluxDB, Data API)..."
cd "$PROJECT_ROOT"
docker-compose up -d 2>/dev/null || true
sleep 2

echo "Dashboard: http://localhost:80"
echo "InfluxDB API: http://localhost:8086"
echo ""

# --------------------------------------------------
# Start EEG Data Source
# --------------------------------------------------

# Use full path to python from venv for direct execution
PYTHON_BIN="$VENV_PATH/bin/python"

if [ "$RUN_NODE" -eq 1 ]; then
    case "$USE_ACQUISITION" in
        0)
            echo "Starting EEG Simulator..."
            nohup "$PYTHON_BIN" "$PROJECT_ROOT/nodes/data_acquisition/eeg_simulator.py" \
                >> "$LOG_DIR/eeg_simulator.log" 2>&1 &
            echo $! > "$LOG_DIR/eeg_simulator.pid"
            echo "Simulator started (PID: $(cat $LOG_DIR/eeg_simulator.pid))"
            ;;
        1)
            echo "Starting OpenBCI Driver..."
            nohup "$PYTHON_BIN" "$PROJECT_ROOT/nodes/data_acquisition/openbci_driver/openbci_driver/openbci_driver.py" \
                >> "$LOG_DIR/openbci_driver.log" 2>&1 &
            echo $! > "$LOG_DIR/openbci_driver.pid"
            echo "OpenBCI driver started (PID: $(cat $LOG_DIR/openbci_driver.pid))"
            ;;
        2)
            echo "Starting Neurosity Driver..."
            nohup "$PYTHON_BIN" "$PROJECT_ROOT/nodes/data_acquisition/neurosity_driver/neurosity_driver/neurosity_driver.py" \
                >> "$LOG_DIR/neurosity_driver.log" 2>&1 &
            echo $! > "$LOG_DIR/neurosity_driver.pid"
            echo "Neurosity driver started (PID: $(cat $LOG_DIR/neurosity_driver.pid))"
            ;;
        *)
            echo "Unknown USE_ACQUISITION=$USE_ACQUISITION"
            exit 1
            ;;
    esac
fi

echo ""
echo "=========================================="
echo "  System Started"
echo "=========================================="
echo "Logs:"
echo "  tail -f $LOG_DIR/*.log"
echo ""
echo "Dashboard: http://localhost:80"
echo ""
echo "Stop all: pkill -f 'eeg_simulator\|neurosity_driver' && docker-compose down"
echo "=========================================="