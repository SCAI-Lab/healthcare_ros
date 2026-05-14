# --------------------------------------------------
# CLEANUP HELPER
# --------------------------------------------------
stop_all_nodes() {
    echo "Stopping all healthcare_demo processes..."

    pkill -f neurosity_driver || true
    pkill -f openbci_driver || true
    pkill -f eeg_json_saver || true
    pkill -f eeg_preprocessing || true
    pkill -f eeg_influxdb_bridge || true
    pkill -f eeg_latency_monitor || true
    pkill -f eeg_simulator || true

    docker compose down 2>/dev/null || true

    echo "All processes stopped."
}
________________________________________
cd ~/ros2_ws
rm -rf ~/hcmd-venv
python3 -m venv ~/hcmd-venv
rm -rf build install log
rm -rf ~/ros2_ws/build ~/ros2_ws/install ~/ros2_ws/log
cd src
cd healthcare_demo
DEBUG_SHELL=1 USE_ACQUISITION=2 ./launch/start.sh
