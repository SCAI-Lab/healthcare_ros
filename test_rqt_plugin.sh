#!/usr/bin/env bash
# Test script to verify rqt EEG visualization plugin launches in container and receives data
set -euo pipefail

export RUN_RQT=1
export SIMULATE=1
export RUN_NODE=1

# Start all nodes and rqt in container
./start.sh

echo "If rqt launches and shows EEG plots, the test is successful."
echo "Close rqt to stop the test."
