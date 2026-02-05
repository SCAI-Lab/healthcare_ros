#!/usr/bin/env bash


# Native start script: activates venv, sources ROS2, builds workspace if needed, and can launch nodes or rqt.

set -euo pipefail

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

VENV_PATH="${VENV_PATH:-$HOME/hcmd-venv}"
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
  run         Start the neurosity_driver node after setup (ros2 run)
  help        Show this help message
  rqt         Start rqt with correct ROS2 overlays

Example:
  ROS_DISTRO=humble VENV_PATH=~/venv $0 run
EOF
}

if [ "${1:-}" = "help" ] || [ "${1:-}" = "--help" ]; then
    usage
    exit 0
fi

if [ "${1:-}" = "rqt" ]; then
    echo "Cleaning Snap and VSCode environment variables for rqt..."
    if [ "$VISUALIZATION_MODE" = "comparison" ]; then
        echo "Starting offline EEG plotting script..."
        # Get script directory and navigate to project root
        SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
        PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
        python3 "$PROJECT_ROOT/nodes/visualization/plot_eeg_offline.py" &
    fi
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

# Install all required packages
pip_install_if_missing em empy
pip_install_if_missing numpy numpy
pip_install_if_missing scipy scipy
pip_install_if_missing matplotlib matplotlib
pip_install_if_missing yaml pyyaml
pip_install_if_missing neurosity neurosity
pip_install_if_missing dotenv python-dotenv
pip_install_if_missing mne mne
pip_install_if_missing influxdb_client influxdb-client

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
    echo "Running rosdep to install system dependencies..."
    
    # Initialize rosdep if not already done
    if [ ! -d "/etc/ros/rosdep" ]; then
        echo "Initializing rosdep..."
        sudo rosdep init 2>/dev/null || true
    fi
    
    # Update rosdep database (suppress verbose output)
    rosdep update >/dev/null 2>&1 || true
    
    # Install dependencies (suppress errors from missing build artifacts)
    rosdep install --from-paths src --ignore-src -r -y >/dev/null 2>&1 || true
    echo "System dependencies checked"
else
    echo "WARNING: rosdep not found. Installing..."
    sudo apt update >/dev/null 2>&1
    sudo apt install -y python3-rosdep >/dev/null 2>&1
    if command -v rosdep >/dev/null 2>&1; then
        sudo rosdep init 2>/dev/null || true
        rosdep update >/dev/null 2>&1 || true
        echo "rosdep installed and initialized successfully"
    else
        echo "Failed to install rosdep. Please install manually: sudo apt install python3-rosdep"
    fi
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
    echo "Building workspace with all dependencies..."
    # Build all packages up to and including the demonstration package
    if command -v colcon >/dev/null 2>&1; then
        colcon build --packages-up-to healthcare_demo --symlink-install || {
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

# Run tests if requested (RUN_TESTS=1)
RUN_TESTS="${RUN_TESTS:-0}"
if [ "$RUN_TESTS" -eq 1 ]; then
    echo ""
    echo "============================================"
    echo "Running automated tests..."
    echo "============================================"
    
    TEST_DIR="$PROJECT_ROOT/tests"
    
    # Run unit tests
    if [ -f "$TEST_DIR/test_eeg_unit.py" ]; then
        echo ""
        echo "--- Running Unit Tests ---"
        cd "$PROJECT_ROOT" || exit 1
        "$VENV_PATH/bin/python3" tests/test_eeg_unit.py
        UNIT_TEST_RESULT=$?
    fi
    
    # Run integration tests (requires simulator to be running)
    if [ -f "$TEST_DIR/test_eeg_integration.py" ]; then
        echo ""
        echo "--- Running Integration Tests ---"
        echo "Starting simulator for integration tests..."
        
        # Start simulator temporarily
        LOG_DIR="$PROJECT_ROOT/logs"
        mkdir -p "$LOG_DIR"
        SIM_SCRIPT="$PROJECT_ROOT/nodes/eeg_simulator.py"
        nohup "$VENV_PATH/bin/python3" "$SIM_SCRIPT" >> "$LOG_DIR/test_simulator.log" 2>&1 &
        TEST_SIM_PID=$!
        
        # Wait for simulator to initialize
        sleep 3
        
        # Run integration tests
        cd "$PROJECT_ROOT" || exit 1
        "$VENV_PATH/bin/python3" tests/test_eeg_integration.py 10
        INTEGRATION_TEST_RESULT=$?
        
        # Stop test simulator
        kill $TEST_SIM_PID 2>/dev/null || true
        pkill -f "eeg_simulator|eeg_json_saver" 2>/dev/null || true
    fi
    
    echo ""
    echo "============================================"
    echo "Test Results Summary:"
    echo "============================================"
    [ "$UNIT_TEST_RESULT" -eq 0 ] && echo "✅ Unit Tests: PASSED" || echo "❌ Unit Tests: FAILED"
    [ "$INTEGRATION_TEST_RESULT" -eq 0 ] && echo "✅ Integration Tests: PASSED" || echo "❌ Integration Tests: FAILED"
    echo "============================================"
    echo ""
    
    # Exit if RUN_NODE is not set (tests only mode)
    if [ "${RUN_NODE:-0}" -eq 0 ]; then
        exit 0
    fi
fi

# Start the node in background by default (can be disabled with RUN_NODE=0)
RUN_NODE="${RUN_NODE:-1}"
USE_ACQUISITION="${USE_ACQUISITION:-0}"  # 0=simulator, 1=OpenBCI, 2=Neurosity
OPENBCI_PORT="${OPENBCI_PORT:-/dev/ttyUSB0}"  # OpenBCI serial port
OPENBCI_CHANNELS="${OPENBCI_CHANNELS:-8}"  # OpenBCI channel count (8 or 16)
USE_ROSBAG="${USE_ROSBAG:-0}"  # 1=use rosbag (MCAP), 0=use JSON files
USE_INFLUXDB="${USE_INFLUXDB:-0}"  # 1=enable InfluxDB bridge for web visualization
MANAGE_DOCKER="${MANAGE_DOCKER:-1}"  # 1=automatically start/stop Docker services, 0=manual
ENCRYPTED_ENV="${ENCRYPTED_ENV:-0}"  # 1=use encrypted .env.encrypted file, 0=use plain .env

# Start Docker Compose services if enabled
if [ "$USE_INFLUXDB" -eq 1 ] && [ "$MANAGE_DOCKER" -eq 1 ]; then
    echo "Starting Docker Compose services (InfluxDB + Nginx)..."
    if command -v docker-compose >/dev/null 2>&1; then
        cd "$PROJECT_ROOT" || exit 1
        
        # Handle encrypted or plain credentials
        if [ "$ENCRYPTED_ENV" -eq 1 ]; then
            echo "🔐 Using encrypted credentials..."
            
            # Check if encrypted file exists
            if [ ! -f "$PROJECT_ROOT/.env.encrypted" ]; then
                echo "❌ ERROR: .env.encrypted file not found!"
                echo ""
                echo "Please encrypt your credentials first:"
                echo "  cd $PROJECT_ROOT"
                echo "  python3 scripts/encrypt_credentials.py --setup"
                echo ""
                exit 1
            fi
            
            # Decrypt credentials
            echo "Decrypting credentials..."
            if ! "$VENV_PATH/bin/python3" "$PROJECT_ROOT/scripts/encrypt_credentials.py" --decrypt; then
                echo "❌ Decryption failed!"
                exit 1
            fi
            
            # Clean up decrypted file on exit
            trap 'rm -f "$PROJECT_ROOT/.env" 2>/dev/null' EXIT
        else
            # Load credentials from plain .env file (REQUIRED)
            if [ ! -f "$PROJECT_ROOT/.env" ]; then
                echo "❌ ERROR: .env file not found!"
                echo ""
                echo "The .env file is required for security reasons."
                echo "Please create it before starting:"
                echo ""
                echo "  cd $PROJECT_ROOT"
                echo "  cp .env.example .env"
                echo "  # Edit .env with your secure credentials"
                echo ""
                echo "For better security, use encrypted credentials:"
                echo "  python3 scripts/encrypt_credentials.py --setup"
                echo "  ENCRYPTED_ENV=1 bash launch/start.sh"
                echo ""
                echo "See CREDENTIALS_SETUP.md for details."
                exit 1
            fi
        fi
        
        echo "Loading credentials from .env..."
        set -a  # Export all variables
        source "$PROJECT_ROOT/.env"
        set +a
        
        # Validate required environment variables
        if [ -z "$INFLUXDB_ADMIN_USERNAME" ] || [ -z "$INFLUXDB_ADMIN_PASSWORD" ] || [ -z "$INFLUXDB_ADMIN_TOKEN" ]; then
            echo "❌ ERROR: Missing required credentials in .env file!"
            echo ""
            echo "Required variables:"
            echo "  - INFLUXDB_ADMIN_USERNAME"
            echo "  - INFLUXDB_ADMIN_PASSWORD"
            echo "  - INFLUXDB_ADMIN_TOKEN"
            echo ""
            echo "Please check your .env file and try again."
            exit 1
        fi
        
        # Generate dashboard with credentials
        echo "Generating dashboard with credentials..."
        python3 "$PROJECT_ROOT/nodes/visualization/generate_dashboard.py" || {
            echo "❌ ERROR: Failed to generate dashboard."
            echo "Please check generate_dashboard.py and your .env file."
            exit 1
        }
        
        docker-compose up -d
        echo "Waiting for services to be ready..."
        sleep 3
        
        # Check if services are running
        if docker-compose ps | grep -q "Up"; then
            echo "✅ Docker services started successfully"
            echo "   - InfluxDB: http://localhost:8086"
            echo "   - Dashboard: http://localhost:8080"
        else
            echo "❌ Docker services failed to start. Check: docker-compose logs"
        fi
        cd "$WORKSPACE" || exit 1
    else
        echo "⚠️  docker-compose not found. Install it with: sudo apt-get install docker-compose"
        echo "    Or disable automatic Docker management: MANAGE_DOCKER=0"
    fi
fi

if [ "$RUN_NODE" -eq 1 ]; then
    LOG_DIR="$PROJECT_ROOT/logs"
    mkdir -p "$LOG_DIR"
    
    if [ "$USE_ACQUISITION" -eq 0 ]; then
        echo "Starting EEG SIMULATOR (not real device)..."
        SIM_LOG_FILE="$LOG_DIR/eeg_simulator.log"
        SIM_SCRIPT="$PROJECT_ROOT/nodes/data_acquisition/eeg_simulator.py"
        
        cd "$WORKSPACE" || { echo "ERROR: Could not cd to $WORKSPACE"; exit 1; }
        
        nohup "$VENV_PATH/bin/python3" "$SIM_SCRIPT" >> "$SIM_LOG_FILE" 2>&1 &
        SIM_PID=$!
        echo "EEG simulator started with PID $SIM_PID. Logs: $SIM_LOG_FILE"
        echo "$SIM_PID" > "$LOG_DIR/eeg_simulator.pid"
    elif [ "$USE_ACQUISITION" -eq 1 ]; then
        # Start OpenBCI driver node
        echo "Starting OpenBCI driver node (port: $OPENBCI_PORT, channels: $OPENBCI_CHANNELS)..."
        LOG_FILE="$LOG_DIR/openbci_driver.log"
        
        cd "$WORKSPACE" || { echo "ERROR: Could not cd to $WORKSPACE"; exit 1; }
        
        # Source ROS2 and workspace to use ros2 run
        set +u
        source "/opt/ros/$ROS_DISTRO/setup.bash"
        source "$WORKSPACE/install/setup.bash"
        set -u
        
        # Start OpenBCI driver with ros2 run
        nohup ros2 run openbci_driver openbci_driver --ros-args -p port:="$OPENBCI_PORT" -p channel_count:=$OPENBCI_CHANNELS >> "$LOG_FILE" 2>&1 &
        NODE_PID=$!
        echo "openbci_driver started with PID $NODE_PID. Logs: $LOG_FILE"
        echo "$NODE_PID" > "$LOG_DIR/openbci_driver.pid"
    elif [ "$USE_ACQUISITION" -eq 2 ]; then
        # Start neurosity_driver node using ros2 run
        echo "Starting neurosity_driver node in the background..."
        LOG_FILE="$LOG_DIR/neurosity_driver.log"
        
        # Change to package directory so load_dotenv() can find .env file
        PACKAGE_DIR="$PROJECT_ROOT/nodes/data_acquisition/neurosity_driver"
        
        cd "$PACKAGE_DIR" || { echo "ERROR: Could not cd to $PACKAGE_DIR"; exit 1; }
        
        # Ensure venv has required dependencies
        "$VENV_PATH/bin/python3" -m pip install --quiet python-dotenv neurosity 2>/dev/null || true
        
        # Use ros2 run to start the driver (ROS2 will use the workspace overlay)
        nohup ros2 run neurosity_driver neurosity_driver >> "$LOG_FILE" 2>&1 &
        NODE_PID=$!
        echo "neurosity_driver started with PID $NODE_PID. Logs: $LOG_FILE"
        echo "$NODE_PID" > "$LOG_DIR/neurosity_driver.pid"
    else
        echo "ERROR: Invalid USE_ACQUISITION value: $USE_ACQUISITION (must be 0, 1, or 2)"
        exit 1
    fi
    

    # Start saver nodes: either rosbag (MCAP format) or JSON format
    if [ "${USE_ROSBAG:-0}" = "1" ]; then
        echo "Starting EEG rosbag saver (MCAP format) for all topics..."
        ROSBAG_SAVER_SCRIPT="$PROJECT_ROOT/nodes/saver/eeg_rosbag_saver.py"
        ROSBAG_LOG_FILE="$LOG_DIR/eeg_rosbag_saver.log"
        
        # Source ROS2 and workspace for rosbag command
        set +u
        source "/opt/ros/$ROS_DISTRO/setup.bash"
        source "$WORKSPACE/install/setup.bash"
        set -u
        
        nohup "$VENV_PATH/bin/python3" "$ROSBAG_SAVER_SCRIPT" >> "$ROSBAG_LOG_FILE" 2>&1 &
        ROSBAG_PID=$!
        echo "eeg_rosbag_saver started with PID $ROSBAG_PID. Logs: $ROSBAG_LOG_FILE"
        echo "$ROSBAG_PID" > "$LOG_DIR/eeg_rosbag_saver.pid"
    else
        # Start two EEG JSON Saver nodes: one for raw, one for preprocessed
        echo "Starting EEG JSON saver node for raw data..."
        RAW_SAVER_LOG_FILE="$LOG_DIR/eeg_json_saver_raw.log"
        RAW_SAVER_SCRIPT="$PROJECT_ROOT/nodes/saver/eeg_json_saver.py"
        EEG_DATA_DIR="$PROJECT_ROOT/eeg_data"
        nohup "$VENV_PATH/bin/python3" "$RAW_SAVER_SCRIPT" --ros-args -p topic:=/eeg/raw -p file_path:="$EEG_DATA_DIR/eeg_raw_data.jsonl" >> "$RAW_SAVER_LOG_FILE" 2>&1 &
        RAW_SAVER_PID=$!
        echo "eeg_json_saver (raw) started with PID $RAW_SAVER_PID. Logs: $RAW_SAVER_LOG_FILE"
        echo "$RAW_SAVER_PID" > "$LOG_DIR/eeg_json_saver_raw.pid"

        echo "Starting EEG JSON saver node for preprocessed data..."
        PREPROC_SAVER_LOG_FILE="$LOG_DIR/eeg_json_saver_preprocessed.log"
        PREPROC_SAVER_SCRIPT="$PROJECT_ROOT/nodes/saver/eeg_json_saver.py"
        nohup "$VENV_PATH/bin/python3" "$PREPROC_SAVER_SCRIPT" --ros-args -p topic:=/eeg/processed -p file_path:="$EEG_DATA_DIR/eeg_preprocessed_data.jsonl" >> "$PREPROC_SAVER_LOG_FILE" 2>&1 &
        PREPROC_SAVER_PID=$!
        echo "eeg_json_saver (preprocessed) started with PID $PREPROC_SAVER_PID. Logs: $PREPROC_SAVER_LOG_FILE"
        echo "$PREPROC_SAVER_PID" > "$LOG_DIR/eeg_json_saver_preprocessed.pid"
    fi
    
    # Start EEG Preprocessor node (optional)
    echo "Starting eeg_preprocessor node in the background..."
    PREPROC_LOG_FILE="$LOG_DIR/eeg_preprocessor.log"
    PREPROC_SCRIPT="$PROJECT_ROOT/nodes/preprocessing/eeg_preprocessing.py"
    if [ -f "$PREPROC_SCRIPT" ]; then
        nohup "$VENV_PATH/bin/python3" "$PREPROC_SCRIPT" >> "$PREPROC_LOG_FILE" 2>&1 &
        PREPROC_PID=$!
        echo "eeg_preprocessor started with PID $PREPROC_PID. Logs: $PREPROC_LOG_FILE"
        echo "$PREPROC_PID" > "$LOG_DIR/eeg_preprocessor.pid"
    else
        echo "Preprocessor script not found at $PREPROC_SCRIPT; skipping preprocessor start"
    fi
    
    # Start InfluxDB bridge node (optional)
    if [ "$USE_INFLUXDB" -eq 1 ]; then
        echo "Starting InfluxDB bridge for web-based visualization..."
        INFLUXDB_BRIDGE_LOG_FILE="$LOG_DIR/eeg_influxdb_bridge.log"
        INFLUXDB_BRIDGE_SCRIPT="$PROJECT_ROOT/nodes/saver/eeg_influxdb_bridge.py"
        
        # Ensure credentials are loaded (either from decryption or plain .env)
        if [ ! -f "$PROJECT_ROOT/.env" ]; then
            echo "❌ ERROR: .env file not found!"
            echo "Credentials should have been loaded earlier in the script."
            echo "This is a logic error. Please report this issue."
            exit 1
        fi
        
        # Credentials already loaded earlier, just export what's needed
        export INFLUXDB_URL="${INFLUXDB_URL:-http://localhost:8086}"
        export INFLUXDB_TOKEN="${INFLUXDB_ADMIN_TOKEN}"
        export INFLUXDB_ORG="${INFLUXDB_ORG}"
        export INFLUXDB_BUCKET="${INFLUXDB_BUCKET}"
        
        if [ -f "$INFLUXDB_BRIDGE_SCRIPT" ]; then
            nohup "$VENV_PATH/bin/python3" "$INFLUXDB_BRIDGE_SCRIPT" >> "$INFLUXDB_BRIDGE_LOG_FILE" 2>&1 &
            INFLUXDB_PID=$!
            echo "eeg_influxdb_bridge started with PID $INFLUXDB_PID. Logs: $INFLUXDB_BRIDGE_LOG_FILE"
            echo "$INFLUXDB_PID" > "$LOG_DIR/eeg_influxdb_bridge.pid"
            echo ""
            echo "🌐 Web Visualization URLs:"
            echo "   - Real-Time Dashboard: http://localhost:8080"
            echo "   - InfluxDB UI: $INFLUXDB_URL"
            echo "   - Username: admin"
            echo "   - Password: healthcare2026"
            echo ""
        else
            echo "InfluxDB bridge script not found at $INFLUXDB_BRIDGE_SCRIPT; skipping"
        fi
    fi
fi



# Visualization mode: none (default), comparison, or rqt
VISUALIZATION_MODE="${VISUALIZATION_MODE:-none}"

if [ "$VISUALIZATION_MODE" = "comparison" ]; then
    echo "Starting offline EEG plotting script..."
    python3 "$PROJECT_ROOT/nodes/visualization/plot_eeg_offline.py" &
elif [ "$VISUALIZATION_MODE" = "rqt" ]; then
    echo "Starting rqt EEG visualization plugin..."
    export RQT_PLUGIN_PATH="$PROJECT_ROOT/nodes/visualization/eeg_visualization_rqt"
    rqt --standalone eeg_visualization_rqt &
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
    if [ "$USE_ACQUISITION" -eq 0 ]; then
        echo "Running in SIMULATOR MODE (test data, no real device needed)"
        echo ""
        echo "Nodes started:"
        echo "  - eeg_simulator (PID: $(cat $LOG_DIR/eeg_simulator.pid 2>/dev/null || echo '?'))"
    elif [ "$USE_ACQUISITION" -eq 1 ]; then
        echo "Running with OPENBCI DEVICE"
        echo ""
        echo "Nodes started:"
        echo "  - openbci_driver (PID: $(cat $LOG_DIR/openbci_driver.pid 2>/dev/null || echo '?'))"
    elif [ "$USE_ACQUISITION" -eq 2 ]; then
        echo "Running with NEUROSITY DEVICE"
        echo ""
        echo "Nodes started:"
        echo "  - neurosity_driver (PID: $(cat $LOG_DIR/neurosity_driver.pid 2>/dev/null || echo '?'))"
    fi
    # Show which saver node is running and its PID/log
    if [ "${USE_ROSBAG:-0}" = "1" ]; then
        echo "  - eeg_rosbag_saver (PID: $(cat $LOG_DIR/eeg_rosbag_saver.pid 2>/dev/null || echo '?'))"
        echo "  - eeg_preprocessor (PID: $(cat $LOG_DIR/eeg_preprocessor.pid 2>/dev/null || echo '?'))"
        echo ""
        echo "Rosbag directory (MCAP format):"
        echo "  $PROJECT_ROOT/eeg_data/rosbag_*/"
        echo ""
        echo "View recorded data:"
        echo "  ros2 bag info \$(ls -dt $PROJECT_ROOT/eeg_data/rosbag_* | head -1)"
        echo ""
        echo "Logs:"
        echo "  - Simulator:  tail -f $LOG_DIR/eeg_simulator.log"
        echo "  - Rosbag:     tail -f $LOG_DIR/eeg_rosbag_saver.log"
        echo "  - Preprocessor: tail -f $LOG_DIR/eeg_preprocessor.log"
    else
        echo "  - eeg_json_saver (raw) (PID: $(cat $LOG_DIR/eeg_json_saver_raw.pid 2>/dev/null || echo '?'))"
        echo "  - eeg_json_saver (preprocessed) (PID: $(cat $LOG_DIR/eeg_json_saver_preprocessed.pid 2>/dev/null || echo '?'))"
        echo "  - eeg_preprocessor (PID: $(cat $LOG_DIR/eeg_preprocessor.pid 2>/dev/null || echo '?'))"
        if [ "$USE_INFLUXDB" -eq 1 ]; then
            echo "  - eeg_influxdb_bridge (PID: $(cat $LOG_DIR/eeg_influxdb_bridge.pid 2>/dev/null || echo '?'))"
        fi
        echo ""
        echo "EEG data files (JSONL format):"
        echo "  - Raw:        $PROJECT_ROOT/eeg_data/eeg_raw_data.jsonl"
        echo "  - Preprocessed: $PROJECT_ROOT/eeg_data/eeg_preprocessed_data.jsonl"
        echo ""
        if [ "$USE_INFLUXDB" -eq 1 ]; then
            echo "🌐 Web Visualization:"
            echo "  - Real-Time Dashboard: http://localhost:8080"
            echo "  - InfluxDB UI: ${INFLUXDB_URL:-http://localhost:8086}"
            echo "  - Username: admin"
            echo "  - Password: healthcare2026"
            echo "  - Org: ${INFLUXDB_ORG:-healthcare}"
            echo "  - Bucket: ${INFLUXDB_BUCKET:-eeg_data}"
            echo "  - Measurements: eeg_raw, eeg_preprocessed"
            echo ""
            echo "Docker Services (managed by docker-compose):"
            echo "  - Start: cd $PROJECT_ROOT && docker-compose up -d"
            echo "  - Stop: cd $PROJECT_ROOT && docker-compose down"
            echo "  - Logs: docker-compose logs -f nginx influxdb"
            echo ""
        fi
        echo "View stored data:"
        echo "  head -1 $PROJECT_ROOT/eeg_data/eeg_raw_data.jsonl | python3 -m json.tool"
        echo ""
        echo "Logs:"
        echo "  - Simulator:  tail -f $LOG_DIR/eeg_simulator.log"
        echo "  - Raw Saver:  tail -f $LOG_DIR/eeg_json_saver_raw.log"
        echo "  - Preprocessor: tail -f $LOG_DIR/eeg_preprocessor.log"
        echo "  - Prep Saver: tail -f $LOG_DIR/eeg_json_saver_preprocessed.log"
        if [ "$USE_INFLUXDB" -eq 1 ]; then
            echo "  - InfluxDB:   tail -f $LOG_DIR/eeg_influxdb_bridge.log"
        fi
    fi
    echo ""
    echo "Stop all nodes:"
    if [ "$USE_ACQUISITION" -eq 0 ]; then
        if [ "${USE_ROSBAG:-0}" = "1" ]; then
            echo "  kill \\$(cat $LOG_DIR/eeg_simulator.pid) \\$(cat $LOG_DIR/eeg_rosbag_saver.pid) \\$(cat $LOG_DIR/eeg_preprocessor.pid)"
        else
            echo "  kill \\$(cat $LOG_DIR/eeg_simulator.pid) \\$(cat $LOG_DIR/eeg_json_saver_raw.pid) \\$(cat $LOG_DIR/eeg_preprocessor.pid) \\$(cat $LOG_DIR/eeg_json_saver_preprocessed.pid)"
        fi
    elif [ "$USE_ACQUISITION" -eq 1 ]; then
        if [ "${USE_ROSBAG:-0}" = "1" ]; then
            echo "  kill \\$(cat $LOG_DIR/openbci_driver.pid) \\$(cat $LOG_DIR/eeg_rosbag_saver.pid) \\$(cat $LOG_DIR/eeg_preprocessor.pid)"
        else
            echo "  kill \\$(cat $LOG_DIR/openbci_driver.pid) \\$(cat $LOG_DIR/eeg_json_saver_raw.pid) \\$(cat $LOG_DIR/eeg_preprocessor.pid) \\$(cat $LOG_DIR/eeg_json_saver_preprocessed.pid)"
        fi
    elif [ "$USE_ACQUISITION" -eq 2 ]; then
        if [ "${USE_ROSBAG:-0}" = "1" ]; then
            echo "  kill \\$(cat $LOG_DIR/neurosity_driver.pid) \\$(cat $LOG_DIR/eeg_rosbag_saver.pid) \\$(cat $LOG_DIR/eeg_preprocessor.pid)"
        else
            echo "  kill \\$(cat $LOG_DIR/neurosity_driver.pid) \\$(cat $LOG_DIR/eeg_json_saver_raw.pid) \\$(cat $LOG_DIR/eeg_preprocessor.pid) \\$(cat $LOG_DIR/eeg_json_saver_preprocessed.pid)"
        fi
    fi
else
    LOG_DIR="$PROJECT_ROOT/logs"
    echo ""
    echo "============================================"
    echo "Setup complete! Environment ready."
    echo "============================================"
    echo ""
    echo "Nodes are not running (RUN_NODE=0)."
    echo "To enable auto-start, use: RUN_NODE=1 ./start.sh"
    echo ""
    echo "To use simulator (no device needed):"
    echo "  SIMULATE=1 RUN_NODE=1 ./start.sh"
fi
#chmod +x /home/tjalf/ros2_ws/src/-healthcare_msgs-demonstration/start.sh && /home/tjalf/ros2_ws/src/-healthcare_msgs-demonstration/start.sh run
#source /home/tjalf/ros2_ws/src/-healthcare_demo/start.sh
