#!/usr/bin/env python3
"""
Automated Integration Test for EEG Pipeline

Tests the complete EEG data flow:
1. Start simulator + saver
2. Run for specified duration
3. Stop nodes
4. Validate stored data format and completeness
5. Report results
"""

import subprocess
import time
import json
import sys
from pathlib import Path
from datetime import datetime


class EEGIntegrationTest:
    def __init__(self, duration_secs=20, verbose=True):
        self.duration = duration_secs
        self.verbose = verbose
        self.workspace = Path.home() / 'ros2_ws' / 'src' / '-healthcare_msgs_demonstration'
        self.log_dir = Path.home() / 'neurosity_logs'
        self.data_file = self.log_dir / 'eeg_data.jsonl'
        self.results = {'passed': [], 'failed': []}
        
    def log(self, msg):
        """Print message if verbose."""
        if self.verbose:
            print(msg)
    
    def run_test(self):
        """Execute the integration test."""
        self.log("\n" + "=" * 70)
        self.log("EEG INTEGRATION TEST")
        self.log("=" * 70)
        self.log(f"Start time: {datetime.now().isoformat()}")
        self.log(f"Test duration: {self.duration}s")
        
        # Clear old data
        self.log("\n[1/5] Cleaning up old data...")
        self._cleanup()
        
        # Start nodes
        self.log("\n[2/5] Starting simulator + saver...")
        if not self._start_nodes():
            self.log("FAILED to start nodes")
            return False
        
        # Wait
        self.log(f"\n[3/5] Running for {self.duration}s...")
        time.sleep(self.duration)
        
        # Stop nodes
        self.log("\n[4/5] Stopping nodes...")
        self._stop_nodes()
        time.sleep(2)
        
        # Validate
        self.log("\n[5/5] Validating data...")
        self._validate_data()
        
        # Report
        self._report()
        
        return len(self.results['failed']) == 0
    
    def _cleanup(self):
        """Remove old logs and data."""
        try:
            # Kill only neurosity processes by name, not all python3
            subprocess.run(['bash', '-c', 'pkill -f "neurosity_driver|eeg_saver|eeg_simulator"'], 
                         stderr=subprocess.DEVNULL)
            time.sleep(0.5)
            for f in self.log_dir.glob('eeg*.*'):
                f.unlink()
                self.log(f"  Removed {f.name}")
        except Exception as e:
            self.log(f"  Cleanup warning: {e}")
    
    def _start_nodes(self):
        """Start simulator + saver."""
        try:
            cmd = f"cd {self.workspace} && SIMULATE=1 NO_BUILD=1 RUN_NODE=1 nohup bash ./start.sh > /tmp/test_start.log 2>&1 &"
            subprocess.run(cmd, shell=True)
            time.sleep(3)
            
            # Check if PIDs exist
            try:
                with open(self.log_dir / 'eeg_simulator.pid', 'r') as f:
                    sim_pid = int(f.read().strip())
                with open(self.log_dir / 'eeg_saver.pid', 'r') as f:
                    saver_pid = int(f.read().strip())
                
                self.log(f"  ✓ Simulator (PID {sim_pid}) + Saver (PID {saver_pid}) started")
                return True
            except:
                self.log(f"  ✗ Could not verify PIDs")
                return False
        except Exception as e:
            self.log(f"  ✗ Error starting nodes: {e}")
            return False
    
    def _stop_nodes(self):
        """Stop running nodes."""
        try:
            subprocess.run(['bash', '-c', 'pkill -f "neurosity_driver|eeg_saver|eeg_simulator"'],
                         stderr=subprocess.DEVNULL)
            self.log("  ✓ Nodes stopped")
        except Exception as e:
            self.log(f"  Warning: {e}")
    
    def _validate_data(self):
        """Validate stored EEG data."""
        tests = [
            ('Data file exists', self._test_file_exists),
            ('File has content', self._test_file_content),
            ('Message format valid', self._test_message_format),
            ('Channel count correct', self._test_channel_count),
            ('Sample count consistent', self._test_sample_consistency),
            ('Quality scores valid', self._test_quality_valid),
        ]
        
        for test_name, test_func in tests:
            try:
                if test_func():
                    self.results['passed'].append(test_name)
                    self.log(f"  ✓ {test_name}")
                else:
                    self.results['failed'].append(test_name)
                    self.log(f"  ✗ {test_name}")
            except Exception as e:
                self.results['failed'].append(f"{test_name} (exception: {e})")
                self.log(f"  ✗ {test_name}: {e}")
    
    def _test_file_exists(self):
        """Check if eeg_data.jsonl exists."""
        return self.data_file.exists()
    
    def _test_file_content(self):
        """Check if file has at least one message."""
        if not self.data_file.exists():
            return False
        with open(self.data_file, 'r') as f:
            first_line = f.readline()
            return len(first_line.strip()) > 0
    
    def _test_message_format(self):
        """Check if messages have required fields."""
        required_fields = ['header', 'session_id', 'sample_size', 'eeg', 'quality']
        with open(self.data_file, 'r') as f:
            for line in f:
                msg = json.loads(line)
                for field in required_fields:
                    if field not in msg:
                        return False
                # Check nested header fields
                if 'stamp' not in msg['header'] or 'frame_id' not in msg['header']:
                    return False
        return True
    
    def _test_channel_count(self):
        """Verify channel count is consistent (should be 4)."""
        with open(self.data_file, 'r') as f:
            for line in f:
                msg = json.loads(line)
                if len(msg['quality']) != 4:
                    return False
        return True
    
    def _test_sample_consistency(self):
        """Check sample_size matches flattened array length."""
        with open(self.data_file, 'r') as f:
            for line in f:
                msg = json.loads(line)
                expected_len = 4 * msg['sample_size']
                actual_len = len(msg['eeg'])
                if expected_len != actual_len:
                    return False
        return True
    
    def _test_quality_valid(self):
        """Check quality scores are in valid range [0, 1]."""
        with open(self.data_file, 'r') as f:
            for line in f:
                msg = json.loads(line)
                for q in msg['quality']:
                    if not (0.0 <= q <= 1.0):
                        return False
        return True
    
    def _report(self):
        """Print test results."""
        self.log("\n" + "=" * 70)
        self.log("TEST RESULTS")
        self.log("=" * 70)
        
        passed = len(self.results['passed'])
        failed = len(self.results['failed'])
        total = passed + failed
        
        self.log(f"\nPassed: {passed}/{total}")
        for test in self.results['passed']:
            self.log(f"  ✓ {test}")
        
        if self.results['failed']:
            self.log(f"\nFailed: {failed}/{total}")
            for test in self.results['failed']:
                self.log(f"  ✗ {test}")
        
        # Data summary
        if self.data_file.exists():
            with open(self.data_file, 'r') as f:
                lines = f.readlines()
            
            if lines:
                first_msg = json.loads(lines[0])
                num_channels = len(first_msg['quality'])
                sample_size = first_msg['sample_size']
                total_samples = len(lines) * num_channels * sample_size
                
                self.log(f"\nData Summary:")
                self.log(f"  Total messages: {len(lines)}")
                self.log(f"  Channels: {num_channels}")
                self.log(f"  Samples per message: {sample_size}")
                self.log(f"  Total data points: {total_samples}")
        
        self.log("\n" + "=" * 70)
        if failed == 0:
            self.log("✓ ALL TESTS PASSED")
        else:
            self.log("✗ SOME TESTS FAILED")
        self.log("=" * 70 + "\n")


def main():
    duration = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    
    test = EEGIntegrationTest(duration_secs=duration)
    success = test.run_test()
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
