# Docstring Improvement Recommendations

## Overview
This document identifies Python functions and classes that need improved docstrings following NumPy/Google style conventions.

---

## High Priority: Missing Docstrings

### 1. **nodes/preprocessing/eeg_preprocessing.py**

#### `_on_raw_info(self, msg)`
**Current:** No docstring
**Needs:**
```python
def _on_raw_info(self, msg):
    """
    Callback for receiving raw EEG metadata.
    
    Stores the raw EEGInfo message for later use when publishing processed metadata.
    This enables forwarding of upstream device information and electrode configuration
    to the processed data stream.
    
    Parameters
    ----------
    msg : healthcare_msgs.msg.EEGInfo
        Raw EEG metadata including device info, electrode sites, and configuration.
        
    Notes
    -----
    Uses latching QoS (transient local durability) to ensure late-joining nodes
    receive the metadata even if published before subscription.
    """
```

#### `process_eeg(self, data, num_channels, num_samples, fs)`
**Current:** Basic docstring
**Needs improvement with:**
- Parameter types and shapes
- Return value structure
- Algorithm description
- Example usage

**Suggested:**
```python
def process_eeg(self, data, num_channels, num_samples, fs):
    """
    Apply bandpass filtering and Common Average Reference to EEG data.
    
    Processing Pipeline:
    1. Reshape flattened data to (channels, samples)
    2. Apply Butterworth bandpass filter (0.5-45 Hz)
    3. Apply Common Average Reference (CAR)
    4. Optionally downsample
    5. Round to reduce storage size
    
    Parameters
    ----------
    data : list or np.ndarray
        Flattened EEG data of shape (num_channels * num_samples,)
    num_channels : int
        Number of EEG channels
    num_samples : int
        Number of samples per channel
    fs : float
        Sampling frequency in Hz
        
    Returns
    -------
    processed_data : np.ndarray
        Processed EEG data, shape (num_channels, num_samples_out)
        where num_samples_out = num_samples // downsample_factor
        
    Raises
    ------
    ValueError
        If data length doesn't match num_channels * num_samples
        
    Examples
    --------
    >>> preprocessor = EEGPreprocessor()
    >>> data = [1.0, 2.0, ...] * 256  # 4 channels, 64 samples each
    >>> processed = preprocessor.process_eeg(data, 4, 64, 256.0)
    >>> processed.shape
    (4, 64)
    """
```

#### `publish_eeg_info(self)`
**Current:** Minimal docstring
**Needs:**
```python
def publish_eeg_info(self):
    """
    Publish processed EEG metadata with preprocessing annotations.
    
    Creates a new EEGInfo message that:
    1. Copies all upstream metadata from raw_info (device_info, electrodes, etc.)
    2. Adds preprocessing method constants (BANDPASS, CAR) to selected_preprocessing
    3. Publishes to /eeg/processed_info with latching QoS
    
    The preprocessing constants follow healthcare_msgs.msg.EEGInfo definitions:
    - EEG_PREPROC_BANDPASS (1): Bandpass filtering applied
    - EEG_PREPROC_CAR (4): Common Average Reference applied
    
    Notes
    -----
    Only publishes once per session. Uses transient local durability so late
    subscribers receive the metadata automatically.
    
    See Also
    --------
    healthcare_msgs.msg.EEGInfo : Message definition with preprocessing constants
    """
```

---

### 2. **nodes/saver/eeg_json_saver.py**

#### `__init__(self)`
**Current:** No docstring
**Needs:**
```python
def __init__(self):
    """
    Initialize EEG data saver node.
    
    Sets up:
    - File paths for raw/preprocessed data storage
    - Subscription to EEG data topics
    - Subscription to EEGInfo metadata topics (latching QoS)
    - Truncates existing data files to prevent appending old data
    
    Parameters (ROS2 CLI):
    - topic (str): Topic to subscribe to (default: '/neurosity/eeg')
    - file_path (str): Output JSONL file path (default: 'eeg_data/eeg_raw_data.jsonl')
    
    File Organization:
    - Data files: eeg_data/*.jsonl, eeg_data/*.info.json
    - Log files: logs/*.log
    - PID files: logs/*.pid
    
    Examples
    --------
    Default usage (raw data):
    $ ros2 run healthcare_msgs eeg_json_saver
    
    Save preprocessed data:
    $ ros2 run healthcare_msgs eeg_json_saver --ros-args -p topic:=/eeg/processed
    """
```

#### `eeg_callback(self, msg)`
**Current:** Basic comment
**Needs:**
```python
def eeg_callback(self, msg):
    """
    Process and save incoming EEG messages to JSONL format.
    
    Converts ROS2 EEG message to JSON and appends to output file.
    Each line is a complete JSON object with all message fields.
    
    Parameters
    ----------
    msg : healthcare_msgs.msg.EEG
        EEG message containing:
        - header: timestamp and frame_id
        - session_id: unique session identifier
        - sample_size: samples per channel
        - eeg: flattened float64 array [ch0_samples, ch1_samples, ...]
        - quality: per-channel quality scores [0.0-1.0]
        
    Notes
    -----
    File format is JSONL (JSON Lines): one JSON object per line, enabling
    streaming writes and easy line-by-line parsing. Each line is independently
    parseable, making the format robust to incomplete writes.
    
    See Also
    --------
    healthcare_msgs.msg.EEG : Message definition
    """
```

---

### 3. **nodes/visualization/plot_eeg_comparison.py**

#### `get_next_plot_number(plots_dir)`
**Current:** Basic docstring
**Needs:**
```python
def get_next_plot_number(plots_dir):
    """
    Find next available plot number for auto-incrementing filenames.
    
    Scans plots_dir for existing files matching 'eeg_comparison_NNN.png'
    and returns the next sequential number. Creates directory if missing.
    
    Parameters
    ----------
    plots_dir : str or Path
        Directory containing plot files
        
    Returns
    -------
    int
        Next available number (1 if no files exist, max+1 otherwise)
        
    Examples
    --------
    >>> get_next_plot_number("plots/")
    1  # No existing files
    
    >>> # After creating eeg_comparison_001.png, eeg_comparison_003.png
    >>> get_next_plot_number("plots/")
    4  # Returns max + 1
    
    Notes
    -----
    Handles gaps in numbering (e.g., 001, 003, 005) by returning max+1,
    not the first gap. This prevents overwriting manually deleted files.
    """
```

#### `plot_raw_vs_preprocessed(...)`
**Current:** Minimal docstring
**Needs full parameter documentation:**
```python
def plot_raw_vs_preprocessed(raw_data_path, preprocessed_data_path, 
                            channels_to_plot, seconds_to_plot=10, 
                            sampling_rate=256, num_channels=4, 
                            channel_names=None, save_path=None):
    """
    Generate comparison plots of raw vs preprocessed EEG data.
    
    Reads JSONL data files, extracts specified time window, and creates
    side-by-side comparison plots for selected channels.
    
    Parameters
    ----------
    raw_data_path : str or Path
        Path to raw EEG JSONL file (e.g., 'eeg_data/eeg_raw_data.jsonl')
    preprocessed_data_path : str or Path
        Path to preprocessed JSONL file (e.g., 'eeg_data/eeg_preprocessed_data.jsonl')
    channels_to_plot : list of int
        Channel indices to plot (0-based), e.g., [0, 1, 2, 3]
    seconds_to_plot : float, optional
        Duration of data to plot in seconds (default: 10)
    sampling_rate : float, optional
        Sampling frequency in Hz (default: 256)
    num_channels : int, optional
        Total number of channels in data (default: 4)
    channel_names : list of str, optional
        Names for each channel, e.g., ['Fp1', 'Fp2', 'C3', 'C4']
        If None, uses generic names 'Ch0', 'Ch1', etc.
    save_path : str or Path, optional
        If provided, saves plot to this path instead of displaying
        
    Returns
    -------
    None
    
    Raises
    ------
    FileNotFoundError
        If data files don't exist
    ValueError
        If channels_to_plot contains invalid indices
        
    Examples
    --------
    Plot first 2 seconds of channels 0 and 2:
    >>> plot_raw_vs_preprocessed(
    ...     'eeg_data/eeg_raw_data.jsonl',
    ...     'eeg_data/eeg_preprocessed_data.jsonl',
    ...     channels_to_plot=[0, 2],
    ...     seconds_to_plot=2,
    ...     save_path='plots/eeg_comparison_001.png'
    ... )
    Plot saved to: plots/eeg_comparison_001.png
    
    Notes
    -----
    - Assumes JSONL format with flattened 'eeg' field
    - Data is reshaped to (num_channels, samples_per_channel)
    - Plots are overlaid (raw + preprocessed) per channel
    """
```

---

### 4. **nodes/preprocessing/eeg_preprocessing_tools.py**

#### `apply_bandpass_filter(raw, l_freq, h_freq, sfreq)`
**Current:** Minimal
**Needs:**
```python
def apply_bandpass_filter(self, raw, l_freq, h_freq, sfreq):
    """
    Apply Butterworth bandpass filter to EEG data.
    
    Uses MNE's filter_data with default FIR filter design.
    Typical settings for EEG:
    - 0.5-45 Hz: General purpose, removes DC drift and high-frequency noise
    - 1-30 Hz: Cleaner signal, may lose some theta/delta content
    
    Parameters
    ----------
    raw : mne.io.Raw or np.ndarray
        EEG data to filter, shape (n_channels, n_samples)
    l_freq : float
        Low frequency cutoff in Hz (high-pass threshold)
    h_freq : float
        High frequency cutoff in Hz (low-pass threshold)
    sfreq : float
        Sampling frequency in Hz
        
    Returns
    -------
    filtered : mne.io.Raw or np.ndarray
        Filtered EEG data, same shape as input
        
    Notes
    -----
    Uses FIR filter with default parameters:
    - Filter length: auto-computed for transition bandwidth
    - Phase: zero-phase (non-causal)
    - Method: 'fir' with overlap-add FFT convolution
    
    See Also
    --------
    mne.filter.filter_data : Underlying filtering function
    
    Examples
    --------
    >>> tools = EEGPreprocessingTools()
    >>> filtered = tools.apply_bandpass_filter(raw, 0.5, 45.0, 256.0)
    """
```

#### `apply_car(raw)`
**Current:** Minimal
**Needs:**
```python
def apply_car(self, raw):
    """
    Apply Common Average Reference (CAR) to EEG data.
    
    CAR subtracts the average of all channels from each channel:
    CAR_i = X_i - mean(X_all)
    
    This removes common artifacts present across all channels (e.g.,
    muscle tension, electrical interference) while preserving
    channel-specific activity.
    
    Parameters
    ----------
    raw : mne.io.Raw
        EEG data with shape (n_channels, n_samples)
        
    Returns
    -------
    rereferenced : mne.io.Raw
        CAR-applied data, same shape as input
        
    Notes
    -----
    - Assumes all channels are valid for referencing (no bad channels)
    - Sets reference to 'average' in MNE Raw object metadata
    - Operates in-place on the data
    
    Alternatives
    -----------
    - Linked mastoids reference: Uses average of two mastoid electrodes
    - REST (Reference Electrode Standardization Technique): Model-based
    
    See Also
    --------
    mne.set_eeg_reference : MNE's referencing function
    
    Examples
    --------
    >>> tools = EEGPreprocessingTools()
    >>> car_data = tools.apply_car(raw)
    ```
```

---

## Medium Priority: Incomplete Docstrings

### 5. **nodes/data_acquisition/eeg_simulator.py**

#### `generate_signal(self, channel, time_sec)`
**Current:** Good structure, but could add:
- Mathematical formulation of combined signals
- Frequency component amplitudes rationale
- Reference to EEG frequency bands (alpha, beta, theta)

**Suggested addition:**
```python
"""
...existing content...

Frequency Components:
- Alpha (8-12 Hz): 15 µV amplitude - Dominant in relaxed awake state
- Beta (13-30 Hz): 8 µV amplitude - Associated with active thinking
- Theta (4-8 Hz): 10 µV amplitude - Present in drowsiness

Artifacts Simulated:
- White noise: σ=2 µV continuous background
- Low-frequency drift: 5 µV amplitude, 0.1 Hz
- Powerline: 1.5 µV at 50 Hz
- Muscle artifacts: 5% probability, σ=15 µV
- Eye blinks: 2% probability in frontal channels (Fp1, Fp2), σ=30 µV

Mathematical Formula:
signal = Σ(A_i * sin(2πf_i * t + φ_ch)) + noise + artifacts

where:
- A_i: component amplitude
- f_i: component frequency
- φ_ch: channel-specific phase shift
"""
```

---

## Low Priority: Style Improvements

### General Recommendations:

1. **Add type hints throughout:**
```python
def process_eeg(self, data: List[float], num_channels: int, 
                num_samples: int, fs: float) -> np.ndarray:
```

2. **Use consistent docstring format (NumPy style recommended)**

3. **Add "See Also" sections** linking related functions

4. **Include Examples sections** for complex functions

5. **Document exceptions** with "Raises" section

6. **Add "Notes" sections** for implementation details

7. **Reference healthcare_msgs constants** in docstrings:
```python
"""
Uses healthcare_msgs preprocessing constants:
- EEG_PREPROC_BANDPASS = 1
- EEG_PREPROC_CAR = 4
"""
```

---

## Summary

**Total Functions Needing Improvement: 15+**

**Priority Order:**
1. Preprocessing callbacks and core functions (3)
2. Saver initialization and callbacks (2)
3. Visualization utility functions (2)
4. Preprocessing tool methods (2)
5. Simulator signal generation (1)
6. General style improvements (all files)

**Estimated Effort:** 2-3 hours to add comprehensive docstrings to all identified functions.

**Benefits:**
- Better code maintainability
- Easier onboarding for new contributors
- Automatic API documentation generation with Sphinx
- Improved IDE autocomplete/hints
- Clear parameter/return value contracts
