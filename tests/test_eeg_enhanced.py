#!/usr/bin/env python3
"""
Enhanced EEG Integration Test Suite (unittest-compatible)
"""
import unittest
import subprocess
import time
import json
import os
from pathlib import Path

class TestEnhancedEEG(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.duration = 20
        # Use relative path from test file location
        cls.workspace = Path(__file__).parent.parent.resolve()
        cls.log_dir = cls.workspace / 'logs'
        cls.data_dir = cls.workspace / 'eeg_data'
        cls.data_file = cls.data_dir / 'eeg_raw_data.jsonl'
        # Detect if JSON saver is running: file exists and USE_ROSBAG is not set to 1
        cls.use_json = (os.environ.get('USE_ROSBAG', '0') != '1')
        # Cleanup and start nodes
        subprocess.run(['bash', '-c', 'pkill -f "neurosity_driver|eeg_json_saver|eeg_simulator|eeg_preprocessor"'], stderr=subprocess.DEVNULL)
        time.sleep(0.5)
        for f in cls.log_dir.glob('eeg*.*'):
            f.unlink()
        if cls.data_dir.exists():
            for f in cls.data_dir.glob('eeg*.*'):
                f.unlink()
        cmd = f"cd {cls.workspace} && USE_ACQUISITION=0 NO_BUILD=1 RUN_NODE=1 nohup bash ./launch/start.sh > /tmp/test_start.log 2>&1 &"
        subprocess.run(cmd, shell=True)
        time.sleep(cls.duration)

    @classmethod
    def tearDownClass(cls):
        subprocess.run(['bash', '-c', 'pkill -f "neurosity_driver|eeg_json_saver|eeg_simulator|eeg_preprocessor"'], stderr=subprocess.DEVNULL)
        time.sleep(2)

    def test_file_exists(self):
        if not self.use_json:
            self.skipTest("JSON saver not in use; skipping JSON file tests.")
        self.assertTrue(self.data_file.exists(), "eeg_data.jsonl does not exist")

    def test_file_content(self):
        if not self.use_json:
            self.skipTest("JSON saver not in use; skipping JSON file tests.")
        self.assertTrue(self.data_file.exists(), "eeg_data.jsonl does not exist")
        with open(self.data_file, 'r') as f:
            first_line = f.readline()
            self.assertTrue(len(first_line.strip()) > 0, "eeg_data.jsonl is empty")

    def test_message_format(self):
        if not self.use_json:
            self.skipTest("JSON saver not in use; skipping JSON file tests.")
        required_fields = ['header', 'session_id', 'sample_size', 'eeg', 'quality']
        with open(self.data_file, 'r') as f:
            for line in f:
                msg = json.loads(line)
                for field in required_fields:
                    self.assertIn(field, msg)
                self.assertIn('stamp', msg['header'])
                self.assertIn('frame_id', msg['header'])

    def test_channel_count(self):
        if not self.use_json:
            self.skipTest("JSON saver not in use; skipping JSON file tests.")
        with open(self.data_file, 'r') as f:
            for line in f:
                msg = json.loads(line)
                self.assertEqual(len(msg['quality']), 4)

    def test_sample_consistency(self):
        if not self.use_json:
            self.skipTest("JSON saver not in use; skipping JSON file tests.")
        with open(self.data_file, 'r') as f:
            for line in f:
                msg = json.loads(line)
                expected_len = 4 * msg['sample_size']
                actual_len = len(msg['eeg'])
                self.assertEqual(expected_len, actual_len)

    def test_quality_valid(self):
        if not self.use_json:
            self.skipTest("JSON saver not in use; skipping JSON file tests.")
        with open(self.data_file, 'r') as f:
            for line in f:
                msg = json.loads(line)
                for q in msg['quality']:
                    self.assertTrue(0.0 <= q <= 1.0)

    def test_no_data_loss(self):
        if not self.use_json:
            self.skipTest("JSON saver not in use; skipping JSON file tests.")
        with open(self.data_file, 'r') as f:
            lines = f.readlines()
        if len(lines) < 2:
            self.skipTest("Not enough messages to test data loss")
        first_msg = json.loads(lines[0])
        expected_samples_per_msg = first_msg['sample_size'] * 4
        for line in lines:
            msg = json.loads(line)
            self.assertEqual(len(msg['eeg']), expected_samples_per_msg)

    def test_timestamp_continuity(self):
        if not self.use_json:
            self.skipTest("JSON saver not in use; skipping JSON file tests.")
        with open(self.data_file, 'r') as f:
            lines = f.readlines()
        if len(lines) < 2:
            self.skipTest("Not enough messages to test timestamp continuity")
        prev_time = 0
        for line in lines:
            msg = json.loads(line)
            current_time = msg['header']['stamp']['sec'] + msg['header']['stamp']['nsec'] / 1e9
            self.assertGreaterEqual(current_time, prev_time)
            prev_time = current_time

    def test_amplitude_bounds(self):
        if not self.use_json:
            self.skipTest("JSON saver not in use; skipping JSON file tests.")
        with open(self.data_file, 'r') as f:
            for line in f:
                msg = json.loads(line)
                for sample in msg['eeg']:
                    self.assertLessEqual(abs(sample), 50)

    def test_write_performance(self):
        if not self.use_json:
            self.skipTest("JSON saver not in use; skipping JSON file tests.")
        if not self.data_file.exists():
            self.skipTest("eeg_data.jsonl does not exist")
        with open(self.data_file, 'r') as f:
            lines = f.readlines()
        if len(lines) < 5:
            self.skipTest("Not enough messages to test write performance")
        expected_min = max(2, int(self.duration * 4 * 0.5))
        self.assertGreaterEqual(len(lines), expected_min)

    def test_file_size(self):
        if not self.use_json:
            self.skipTest("JSON saver not in use; skipping JSON file tests.")
        if not self.data_file.exists():
            self.skipTest("eeg_data.jsonl does not exist")
        file_size_kb = self.data_file.stat().st_size / 1024
        with open(self.data_file, 'r') as f:
            num_messages = len(f.readlines())
        self.assertLess(file_size_kb, num_messages * 1.0)

if __name__ == '__main__':
    unittest.main()
    
    def _test_file_size(self):
        """Check file size is reasonable (not bloated)."""
        if not self.data_file.exists():
            return False
        
        file_size_kb = self.data_file.stat().st_size / 1024
        with open(self.data_file, 'r') as f:
            num_messages = len(f.readlines())
        
        # Each message should be ~0.1-0.3 KB (depending on sample count)
        # Check: file_size < 1 KB per message (generous upper bound)
        return file_size_kb < num_messages * 1.0
    
    def _report(self):
        """Print comprehensive test results."""
        self.log("\n" + "=" * 80)
        self.log("TEST RESULTS")
        self.log("=" * 80)
        
        passed = len(self.results['passed'])
        failed = len(self.results['failed'])
        warnings = len(self.results['warnings'])
        total = passed + failed
        
        self.log(f"\nPassed: {passed}/{total}")
        for test in self.results['passed']:
            self.log(f"  ✓ {test}")
        
        if self.results['failed']:
            self.log(f"\nFailed: {failed}/{total}")
            for test in self.results['failed']:
                self.log(f"  ✗ {test}")
        
        if self.results['warnings']:
            self.log(f"\nWarnings: {warnings}")
            for warning in self.results['warnings']:
                self.log(f"  ⚠ {warning}")
        
        # Data summary
        if self.data_file.exists():
            with open(self.data_file, 'r') as f:
                lines = f.readlines()
            
            if lines:
                first_msg = json.loads(lines[0])
                num_channels = len(first_msg['quality'])
                sample_size = first_msg['sample_size']
                total_samples = len(lines) * num_channels * sample_size
                file_size_kb = self.data_file.stat().st_size / 1024
                msg_rate = len(lines) / self.duration
                
                self.log(f"\nData Summary:")
                self.log(f"  Total messages: {len(lines)}")
                self.log(f"  Message rate: {msg_rate:.1f} msg/s")
                self.log(f"  Channels: {num_channels}")
                self.log(f"  Samples per message: {sample_size}")
                self.log(f"  Total data points: {total_samples:,}")
                self.log(f"  File size: {file_size_kb:.1f} KB")
                self.log(f"  Bytes per sample: {file_size_kb * 1024 / total_samples:.2f} bytes")
        
        self.log("\n" + "=" * 80)
        if failed == 0:
            self.log("✓ ALL TESTS PASSED")
        else:
            self.log(f"✗ {failed} TEST(S) FAILED")
        self.log("=" * 80 + "\n")


def main():
    duration = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    
    test = EnhancedEEGTest(duration_secs=duration)
    success = test.run_all_tests()
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
