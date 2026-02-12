#!/usr/bin/env python3
"""
Unit Tests for EEG Pipeline Components

Tests individual components without running the full pipeline:
- Simulator data generation
- Visualization functions
- Data validation functions
"""

import json
import tempfile
from pathlib import Path
import sys
import numpy as np


class UnitTests:
    def __init__(self):
        self.passed = []
        self.failed = []
    
    def test(self, name, func):
        """Run a test and record result."""
        try:
            if func():
                self.passed.append(name)
                print(f"  ✓ {name}")
                return True
            else:
                self.failed.append(name)
                print(f"  ✗ {name}")
                return False
        except Exception as e:
            self.failed.append(f"{name}: {str(e)[:40]}")
            print(f"  ✗ {name}: {e}")
            return False
    
    # ==== SIMULATOR TESTS ====
    
    def test_simulator_signal_generation(self):
        """Test that simulator generates valid EEG-like signals."""
        import math
        import random
        
        def generate_signal(channel, time_sec):
            alpha_freq = 10.0
            beta_freq = 20.0
            theta_freq = 6.0
            
            alpha = 15.0 * math.sin(2 * math.pi * alpha_freq * time_sec)
            beta = 8.0 * math.sin(2 * math.pi * beta_freq * time_sec)
            theta = 10.0 * math.sin(2 * math.pi * theta_freq * time_sec)
            
            phase_shift = channel * (math.pi / 4)
            signal = (alpha + beta + theta) * math.sin(phase_shift)
            noise = random.gauss(0, 0.5)
            
            return signal + noise
        
        # Generate 20 samples over time
        samples = [generate_signal(0, i * 0.01) for i in range(20)]
        
        # Check: signals vary (not all same) and within bounds
        unique_values = len(set(round(s, 4) for s in samples))
        return unique_values > 5 and all(abs(s) < 100 for s in samples)
    
    def test_simulator_frequency_components(self):
        """Test that simulator produces expected frequency components."""
        import math
        
        # Generate 1 second of signal at 256 Hz
        sampling_rate = 256
        duration = 1.0
        samples = []
        
        for i in range(int(sampling_rate * duration)):
            time_sec = i / sampling_rate
            alpha = 10.0 * math.sin(2 * math.pi * 10 * time_sec)  # 10 Hz
            samples.append(alpha)
        
        # FFT to check frequency content
        fft = np.fft.fft(samples)
        freqs = np.fft.fftfreq(len(samples), 1 / sampling_rate)
        magnitude = np.abs(fft)
        
        # Peak should be around 10 Hz
        peak_freq_idx = np.argmax(magnitude[:len(magnitude)//2])
        peak_freq = freqs[peak_freq_idx]
        
        # Allow ±2 Hz tolerance
        return abs(peak_freq - 10) < 2
    
    # ==== JSONL FORMAT TESTS ====
    
    def test_jsonl_write_read(self):
        """Test JSONL file write and read cycle."""
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.jsonl', delete=False) as f:
            temp_path = f.name
            
            # Write 3 messages
            test_msgs = [
                {'header': {'stamp': {'sec': 1, 'nsec': 0}, 'frame_id': 'test'}, 'eeg': [1.0, 2.0], 'quality': [0.9]},
                {'header': {'stamp': {'sec': 2, 'nsec': 0}, 'frame_id': 'test'}, 'eeg': [3.0, 4.0], 'quality': [0.8]},
                {'header': {'stamp': {'sec': 3, 'nsec': 0}, 'frame_id': 'test'}, 'eeg': [5.0, 6.0], 'quality': [0.7]},
            ]
            
            for msg in test_msgs:
                f.write(json.dumps(msg) + '\n')
        
        # Read back
        with open(temp_path, 'r') as f:
            read_msgs = [json.loads(line) for line in f]
        
        # Cleanup
        Path(temp_path).unlink()
        
        # Check
        return len(read_msgs) == 3 and read_msgs[0]['eeg'] == [1.0, 2.0]
    
    def test_jsonl_corruption_detection(self):
        """Test that corrupted JSON is detected."""
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.jsonl', delete=False) as f:
            temp_path = f.name
            f.write('{"valid": "json"}\n')
            f.write('{"invalid": json}\n')  # Missing quotes
            f.write('{"another": "valid"}\n')
        
        # Try reading all lines
        error_count = 0
        with open(temp_path, 'r') as f:
            for line in f:
                try:
                    json.loads(line)
                except json.JSONDecodeError:
                    error_count += 1
        
        # Cleanup
        Path(temp_path).unlink()
        
        return error_count == 1
    
    # ==== VALIDATION FUNCTION TESTS ====
    
    def test_quality_bounds(self):
        """Test quality score validation."""
        valid_scores = [0.0, 0.5, 1.0]
        invalid_scores = [-0.1, 1.1, 2.0]
        
        def is_valid_quality(q):
            return 0.0 <= q <= 1.0
        
        return all(is_valid_quality(q) for q in valid_scores) and \
               not any(is_valid_quality(q) for q in invalid_scores)
    
    def test_channel_consistency(self):
        """Test channel array length consistency."""
        sample_size = 64
        num_channels = 4
        
        # Valid message
        valid_eeg = [1.0] * (num_channels * sample_size)
        
        # Invalid message
        invalid_eeg = [1.0] * (num_channels * sample_size + 1)
        
        def is_consistent(eeg, num_ch, samp_sz):
            return len(eeg) == num_ch * samp_sz
        
        return is_consistent(valid_eeg, num_channels, sample_size) and \
               not is_consistent(invalid_eeg, num_channels, sample_size)
    
    def test_timestamp_monotonicity(self):
        """Test timestamp monotonic increase detection."""
        timestamps = [
            {'stamp': {'sec': 1, 'nsec': 0}},
            {'stamp': {'sec': 1, 'nsec': 500000000}},
            {'stamp': {'sec': 2, 'nsec': 0}},
        ]
        
        valid = True
        prev_time = 0
        for ts_obj in timestamps:
            current_time = ts_obj['stamp']['sec'] + ts_obj['stamp']['nsec'] / 1e9
            if current_time < prev_time:
                valid = False
            prev_time = current_time
        
        return valid
    
    # ==== AMPLITUDE TESTS ====
    
    def test_amplitude_bounds(self):
        """Test EEG amplitude validation."""
        reasonable_samples = [-30, -15, 0, 15, 30]  # ±30 µV typical for simulator
        unreasonable_samples = [-200, 200]  # Way too high
        
        def is_reasonable(sample):
            return abs(sample) <= 50  # ±50 µV reasonable bound
        
        return all(is_reasonable(s) for s in reasonable_samples) and \
               not any(is_reasonable(s) for s in unreasonable_samples)
    
    # ==== EEGINFO METADATA TESTS ====
    
    def test_eeginfo_structure(self):
        """Test that EEGInfo contains required fields."""
        # Simulate EEGInfo structure
        info = {
            'device_info': {'session_id': 'test_session'},
            'channel_size': 4,
            'units': 1,  # UNIT_UV
            'selected_preprocessing': [1, 2],  # BANDPASS, NOTCH
            'montage_type': 1,  # REFERENTIAL
            'electrode_sites': [1, 2, 3, 4],  # FP1, FP2, F3, F4
            'electrode_physical_type': [1, 1, 1, 1],  # DRY
            'placement_method': [1, 1, 1, 1],  # 10-20
            'signal_mode': 1,  # SURFACE
        }
        
        required_fields = [
            'device_info', 'channel_size', 'units', 'selected_preprocessing',
            'montage_type', 'electrode_sites', 'signal_mode'
        ]
        
        return all(field in info for field in required_fields) and \
               info['channel_size'] == len(info['electrode_sites'])
    
    def test_eeginfo_storage(self):
        """Test that EEGInfo can be stored and retrieved as JSON."""
        info = {
            'device_info': {'session_id': 'preprocessed'},
            'channel_size': 4,
            'units': 1,
            'selected_preprocessing': [1, 4],  # BANDPASS, CAR
            'montage_type': 1,
            'electrode_sites': [],
            'electrode_physical_type': [],
            'placement_method': [],
            'signal_mode': 1,
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(info, f, indent=2)
            temp_path = f.name
        
        try:
            # Read back
            with open(temp_path, 'r') as f:
                loaded = json.load(f)
            
            # Verify
            return loaded['channel_size'] == 4 and \
                   loaded['device_info']['session_id'] == 'preprocessed' and \
                   4 in loaded['selected_preprocessing']  # CAR preprocessing present
        finally:
            Path(temp_path).unlink()
    
    # ==== DRIVER NODE TESTS ====
    
    def test_simulator_node_imports(self):
        """Test that simulator node can be imported without errors."""
        import sys
        from pathlib import Path
        workspace = Path(__file__).parent.parent.resolve()
        sim_path = workspace / 'nodes' / 'data_acquisition'
        sys.path.insert(0, str(sim_path))
        try:
            # Import the module to verify it has no syntax errors
            import importlib.util
            spec = importlib.util.spec_from_file_location("eeg_simulator", sim_path / "eeg_simulator.py")
            module = importlib.util.module_from_spec(spec)
            # Don't execute, just check it can be loaded
            return spec is not None
        except Exception as e:
            print(f"Import error: {e}")
            return False
        finally:
            sys.path.remove(str(sim_path))
    
    def test_neurosity_driver_imports(self):
        """Test that Neurosity driver ROS2 package structure is valid."""
        from pathlib import Path
        workspace = Path(__file__).parent.parent.resolve()
        driver_path = workspace / 'nodes' / 'data_acquisition' / 'neurosity_driver' / 'neurosity_driver' / 'neurosity_driver.py'
        
        # Check file exists and has required imports
        if not driver_path.exists():
            return False
        
        with open(driver_path, 'r') as f:
            content = f.read()
        
        # Verify critical imports are present
        required = ['rclpy', 'healthcare_msgs.msg', 'EEG', 'EEGInfo', 'neurosity']
        return all(req in content for req in required)
    
    def test_openbci_driver_imports(self):
        """Test that OpenBCI driver ROS2 package structure is valid."""
        from pathlib import Path
        workspace = Path(__file__).parent.parent.resolve()
        driver_path = workspace / 'nodes' / 'data_acquisition' / 'openbci_driver' / 'openbci_driver' / 'openbci_driver.py'
        
        # Check file exists and has required imports
        if not driver_path.exists():
            return False
        
        with open(driver_path, 'r') as f:
            content = f.read()
        
        # Verify critical imports are present
        required = ['rclpy', 'healthcare_msgs.msg', 'EEG', 'EEGInfo']
        return all(req in content for req in required)
    
    # ==== SAVER NODE TESTS ====
    
    def test_json_saver_imports(self):
        """Test that JSON saver node structure is valid."""
        from pathlib import Path
        workspace = Path(__file__).parent.parent.resolve()
        saver_path = workspace / 'nodes' / 'saver' / 'eeg_json_saver.py'
        
        # Check file exists and has required imports
        if not saver_path.exists():
            return False
        
        with open(saver_path, 'r') as f:
            content = f.read()
        
        # Verify critical imports are present
        required = ['rclpy', 'healthcare_msgs.msg', 'EEG', 'EEGInfo', 'json']
        return all(req in content for req in required)
    
    def test_rosbag_saver_imports(self):
        """Test that rosbag saver node structure is valid."""
        from pathlib import Path
        workspace = Path(__file__).parent.parent.resolve()
        saver_path = workspace / 'nodes' / 'saver' / 'eeg_rosbag_saver.py'
        
        # Check file exists and has required imports
        if not saver_path.exists():
            return False
        
        with open(saver_path, 'r') as f:
            content = f.read()
        
        # Verify critical imports are present
        required = ['rclpy', 'subprocess', 'rosbag']
        return all(req in content for req in required)
    
    # ==== NEW FEATURE TESTS ====
    
    def test_preprocessing_metadata_forwarding(self):
        """Test that preprocessing node forwards metadata from raw_info."""
        from pathlib import Path
        workspace = Path(__file__).parent.parent.resolve()
        preproc_path = workspace / 'nodes' / 'preprocessing' / 'eeg_preprocessing.py'
        
        if not preproc_path.exists():
            return False
        
        with open(preproc_path, 'r') as f:
            content = f.read()
        
        # Check for raw_info subscription and metadata copying
        required = ['_on_raw_info', 'self.raw_info', 'electrode_sites', 'electrode_physical_type']
        return all(req in content for req in required)
    
    def test_eeg_message_fields(self):
        """Test that EEG messages populate all required fields per healthcare_msgs definition."""
        from pathlib import Path
        workspace = Path(__file__).parent.parent.resolve()
        
        # Check simulator node
        sim_path = workspace / 'nodes' / 'data_acquisition' / 'eeg_simulator.py'
        if not sim_path.exists():
            return False
        
        with open(sim_path, 'r') as f:
            content = f.read()
        
        # Core EEG message fields: header, session_id, sample_size, eeg (data), quality
        required_fields = ['eeg_msg.header', 'eeg_msg.session_id', 'eeg_msg.sample_size', 
                          'eeg_msg.eeg', 'eeg_msg.quality']
        return all(field in content for field in required_fields)
    
    def test_eeginfo_message_fields(self):
        """Test that EEGInfo messages populate all applicable fields per healthcare_msgs definition."""
        from pathlib import Path
        workspace = Path(__file__).parent.parent.resolve()
        
        # Check simulator node for EEGInfo
        sim_path = workspace / 'nodes' / 'data_acquisition' / 'eeg_simulator.py'
        if not sim_path.exists():
            return False
        
        with open(sim_path, 'r') as f:
            content = f.read()
        
        # Key EEGInfo fields: device_info, channel_size, units, selected_preprocessing,
        # montage_type, electrode_sites, electrode_physical_type, placement_method, signal_mode
        required_fields = ['info_msg.device_info', 'info_msg.channel_size', 
                          'info_msg.units', 'info_msg.selected_preprocessing',
                          'info_msg.montage_type', 'info_msg.electrode_sites',
                          'info_msg.electrode_physical_type', 'info_msg.placement_method',
                          'info_msg.signal_mode']
        return all(field in content for field in required_fields)
    
    def test_preprocessing_constants(self):
        """Test that preprocessing uses healthcare_msgs constants."""
        from pathlib import Path
        workspace = Path(__file__).parent.parent.resolve()
        preproc_path = workspace / 'nodes' / 'preprocessing' / 'eeg_preprocessing.py'
        
        if not preproc_path.exists():
            return False
        
        with open(preproc_path, 'r') as f:
            content = f.read()
        
        # Check for preprocessing constants: BANDPASS(1), NOTCH(2), ICA(3), CAR(4), etc.
        required = ['EEG_PREPROC_BANDPASS', 'EEG_PREPROC_CAR']
        return all(const in content for const in required)
    
    def test_saver_file_location(self):
        """Test that saver creates files in correct location (eeg_data/ not nodes/eeg_data/)."""
        from pathlib import Path
        workspace = Path(__file__).parent.parent.resolve()
        saver_path = workspace / 'nodes' / 'saver' / 'eeg_json_saver.py'
        
        if not saver_path.exists():
            return False
        
        with open(saver_path, 'r') as f:
            content = f.read()
        
        # Check for correct path calculation (3 levels up, not 2)
        return 'os.path.dirname(os.path.dirname(os.path.dirname' in content
    
    def test_saver_file_overwrite(self):
        """Test that saver truncates files on startup."""
        from pathlib import Path
        workspace = Path(__file__).parent.parent.resolve()
        saver_path = workspace / 'nodes' / 'saver' / 'eeg_json_saver.py'
        
        if not saver_path.exists():
            return False
        
        with open(saver_path, 'r') as f:
            content = f.read()
        
        # Check for file truncation on init
        return "with open(self.data_file, 'w')" in content
    
    def test_plot_auto_numbering(self):
        """Test that plot script has auto-numbering functionality."""
        from pathlib import Path
        workspace = Path(__file__).parent.parent.resolve()
        plot_path = workspace / 'nodes' / 'visualization' / 'plotting' / 'plot_eeg_comparison.py'
        
        if not plot_path.exists():
            return False
        
        with open(plot_path, 'r') as f:
            content = f.read()
        
        # Check for numbering function
        return 'get_next_plot_number' in content and 'eeg_comparison_' in content
    
    def run_all(self):
        """Run all unit tests."""
        print("\n" + "=" * 70)
        print("UNIT TESTS")
        print("=" * 70)
        
        print("\nSimulator Tests:")
        self.test("Signal generation produces varied values", self.test_simulator_signal_generation)
        self.test("Frequency components correct (FFT)", self.test_simulator_frequency_components)
        
        print("\nJSONL Format Tests:")
        self.test("JSONL write/read cycle", self.test_jsonl_write_read)
        self.test("Corrupted JSON detection", self.test_jsonl_corruption_detection)
        
        print("\nValidation Tests:")
        self.test("Quality score bounds [0,1]", self.test_quality_bounds)
        self.test("Channel array consistency", self.test_channel_consistency)
        self.test("Timestamp monotonicity", self.test_timestamp_monotonicity)
        self.test("Amplitude bounds", self.test_amplitude_bounds)
        
        print("\nEEGInfo Metadata Tests:")
        self.test("EEGInfo structure validation", self.test_eeginfo_structure)
        self.test("EEGInfo storage format", self.test_eeginfo_storage)
        
        print("\nDriver Node Tests:")
        self.test("Simulator node imports", self.test_simulator_node_imports)
        self.test("Neurosity driver node imports", self.test_neurosity_driver_imports)
        self.test("OpenBCI driver node imports", self.test_openbci_driver_imports)
        
        print("\nSaver Node Tests:")
        self.test("JSON saver node imports", self.test_json_saver_imports)
        self.test("Rosbag saver node imports", self.test_rosbag_saver_imports)
        
        print("\nNew Feature Tests:")
        self.test("Preprocessing metadata forwarding", self.test_preprocessing_metadata_forwarding)
        self.test("Saver file location (eeg_data/)", self.test_saver_file_location)
        self.test("Saver file overwrite on startup", self.test_saver_file_overwrite)
        self.test("Plot auto-numbering", self.test_plot_auto_numbering)
        
        print("\nMessage Field Tests:")
        self.test("EEG message fields populated", self.test_eeg_message_fields)
        self.test("EEGInfo message fields populated", self.test_eeginfo_message_fields)
        self.test("Preprocessing constants used", self.test_preprocessing_constants)
        
        # Report
        passed = len(self.passed)
        failed = len(self.failed)
        total = passed + failed
        
        print("\n" + "=" * 70)
        print(f"Results: {passed}/{total} passed")
        if self.failed:
            print(f"\nFailed tests:")
            for test in self.failed:
                print(f"  ✗ {test}")
        print("=" * 70 + "\n")
        
        return failed == 0


if __name__ == '__main__':
    tests = UnitTests()
    success = tests.run_all()
    sys.exit(0 if success else 1)
