import unittest
import subprocess
import time
import os
from pathlib import Path

class TestEEGRosbagSaver(unittest.TestCase):
    def setUp(self):
        self.output_dir = os.path.expanduser('~/neurosity_rosbag')
        # Clean up any previous rosbag output
        if os.path.exists(self.output_dir):
            subprocess.run(['rm', '-rf', self.output_dir])
        # Source healthcare_msgs workspace for rosbag type visibility
        ros2_msgs_ws_setup = os.path.expanduser('~/ros2_msgs_ws/install/setup.bash')
        env = os.environ.copy()
        if os.path.exists(ros2_msgs_ws_setup):
            env['ROS_PACKAGE_PATH'] = env.get('ROS_PACKAGE_PATH', '') + ':' + os.path.expanduser('~/ros2_msgs_ws/install')
            env['AMENT_PREFIX_PATH'] = env.get('AMENT_PREFIX_PATH', '') + ':' + os.path.expanduser('~/ros2_msgs_ws/install')
        # Start the rosbag saver node
        self.proc = subprocess.Popen([
            'python3', 'nodes/saver/eeg_rosbag_saver.py'
        ], env=env)
        # Wait for some data to be recorded (increased wait time for MCAP creation)
        time.sleep(8)

    def tearDown(self):
        if self.proc:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.proc.kill()
        # Clean up rosbag output
        if os.path.exists(self.output_dir):
            subprocess.run(['rm', '-rf', self.output_dir])

    def test_rosbag_mcap_created(self):
        # Check if MCAP directory and files exist
        self.assertTrue(os.path.exists(self.output_dir), "Rosbag output directory not created")
        mcap_files = list(Path(self.output_dir).glob('*.mcap'))
        self.assertTrue(len(mcap_files) > 0, "No MCAP files found in rosbag output")

# Manual step-by-step test sequence (if automated test is slow):
# 1. source /opt/ros/jazzy/setup.bash
# 2. source ~/ros2_msgs_ws/install/setup.bash
# 3. source ~/ros2_ws/install/setup.bash
# 4. SIMULATE=1 RUN_NODE=1 ./start.sh
# 5. python3 -m unittest discover -s tests

if __name__ == '__main__':
    unittest.main()
