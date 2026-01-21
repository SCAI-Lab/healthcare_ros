# EEG Pipeline Architecture

## Complete Pipeline Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DATA ACQUISITION LAYER                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐                │
│  │  Simulator   │     │  Neurosity   │     │   OpenBCI    │                │
│  │              │     │   Crown      │     │    Cyton     │                │
│  │  Synthetic   │     │   (WiFi)     │     │ (Serial/BLE) │                │
│  └──────┬───────┘     └──────┬───────┘     └──────┬───────┘                │
│         │                    │                     │                         │
│         └────────────────────┴─────────────────────┘                         │
│                              │                                               │
└──────────────────────────────┼───────────────────────────────────────────────┘
                               │
                               ▼
                    ╔══════════════════════╗
                    ║   /eeg/raw (EEG)     ║  ← Raw EEG data (header, eeg[], quality[])
                    ║   /eeg/raw_info      ║  ← Metadata (device_info, electrodes, etc.)
                    ╚══════════╦═══════════╝
                               ║
                ┌──────────────╫──────────────┐
                │              ║              │
                ▼              ║              ▼
    ┌───────────────────┐     ║     ┌───────────────────┐
    │  JSON Saver (Raw) │     ║     │ Rosbag Saver (Raw)│
    │                   │     ║     │                   │
    │  eeg_data/        │     ║     │  rosbag_data/     │
    │  *.jsonl          │     ║     │  *.mcap           │
    │  *.info.json      │     ║     │                   │
    └───────────────────┘     ║     └───────────────────┘
                               ║
┌──────────────────────────────┼───────────────────────────────────────────────┐
│                       PREPROCESSING LAYER                                     │
├──────────────────────────────┼───────────────────────────────────────────────┤
│                              ▼                                                │
│                   ┌─────────────────────┐                                    │
│                   │  EEG Preprocessor   │                                    │
│                   ├─────────────────────┤                                    │
│                   │ • Bandpass Filter   │ (0.5-45 Hz)                        │
│                   │   (Butterworth)     │                                    │
│                   │ • Common Average    │ (CAR)                              │
│                   │   Reference         │                                    │
│                   │ • Metadata Forward  │ (copies raw_info + adds methods)  │
│                   └──────────┬──────────┘                                    │
│                              │                                                │
└──────────────────────────────┼───────────────────────────────────────────────┘
                               │
                               ▼
                    ╔══════════════════════════╗
                    ║ /eeg/processed (EEG)     ║  ← Filtered EEG data
                    ║ /eeg/processed_info      ║  ← Metadata + preprocessing methods
                    ╚══════════╦═══════════════╝
                               ║
                ┌──────────────╫──────────────┐
                │              ║              │
                ▼              ║              ▼
    ┌───────────────────────┐ ║ ┌───────────────────────────┐
    │ JSON Saver            │ ║ │ Rosbag Saver              │
    │ (Preprocessed)        │ ║ │ (Preprocessed)            │
    │                       │ ║ │                           │
    │ eeg_data/             │ ║ │ rosbag_data/              │
    │ eeg_preprocessed_*    │ ║ │ eeg_preprocessed_*.mcap   │
    └───────────────────────┘ ║ └───────────────────────────┘
                               ║
┌──────────────────────────────┼───────────────────────────────────────────────┐
│                       VISUALIZATION LAYER                                     │
├──────────────────────────────┼───────────────────────────────────────────────┤
│                              ▼                                                │
│                   ┌─────────────────────┐                                    │
│                   │  Plot Comparison    │                                    │
│                   │                     │                                    │
│                   │  • Read JSONL files │                                    │
│                   │  • 2-second windows │                                    │
│                   │  • Auto-numbered    │                                    │
│                   │    plots/           │                                    │
│                   │    eeg_comparison_  │                                    │
│                   │    001.png, ...     │                                    │
│                   └─────────────────────┘                                    │
│                                                                               │
└───────────────────────────────────────────────────────────────────────────────┘
```

## Message Structures

### EEG Message (healthcare_msgs/EEG)
```
header:
  stamp: timestamp
  frame_id: device_identifier
session_id: string
sample_size: uint32
eeg: float64[]          # Flattened array [ch0_samples, ch1_samples, ...]
quality: float64[]      # Per-channel quality scores [0.0-1.0]
```

### EEGInfo Message (healthcare_msgs/EEGInfo)
```
device_info:
  session_id: string
  device_identifier: string
channel_size: uint32
units: uint8                        # UNIT_UV = 0
selected_preprocessing: uint8[]     # [BANDPASS, CAR, ...]
montage_type: uint8                 # MONTAGE_TYPE_REFERENTIAL = 0
electrode_sites: string[]           # ["Fp1", "Fp2", "C3", "C4"]
electrode_physical_type: uint8[]    # [ELECTRODE_TYPE_CUP, ...]
placement_method: uint8[]           # [PLACEMENT_10_20, ...]
signal_mode: uint8                  # SIGNAL_MODE_SURFACE = 0
```

## Quality of Service (QoS)

| Topic Type | Durability       | Reliability | Purpose                |
|------------|------------------|-------------|------------------------|
| /eeg/raw   | Volatile         | Reliable    | Streaming data         |
| /eeg/raw_info | Transient Local | Reliable | Latched metadata       |
| /eeg/processed | Volatile      | Reliable    | Streaming data         |
| /eeg/processed_info | Transient Local | Reliable | Latched metadata |

**Transient Local** = Late joiners receive last message (latching behavior)

## File Organization

```
-healthcare_demo/
├── eeg_data/              # Data files only
│   ├── eeg_raw_data.jsonl
│   ├── eeg_raw_data.info.json
│   ├── eeg_preprocessed_data.jsonl
│   └── eeg_preprocessed_data.info.json
├── logs/                  # Log and PID files
│   ├── eeg_simulator.log
│   ├── eeg_simulator.pid
│   ├── eeg_json_saver_raw.log
│   └── eeg_json_saver_raw.pid
├── plots/                 # Generated visualizations
│   ├── eeg_comparison_001.png
│   ├── eeg_comparison_002.png
│   └── ...
└── rosbag_data/           # MCAP rosbag files
    ├── eeg_raw_*.mcap
    └── eeg_preprocessed_*.mcap
```

## Preprocessing Constants (healthcare_msgs)

| Constant | Value | Description |
|----------|-------|-------------|
| EEG_PREPROC_BANDPASS | 1 | Bandpass filtering |
| EEG_PREPROC_NOTCH | 2 | Notch filtering (50/60 Hz) |
| EEG_PREPROC_ICA | 3 | Independent Component Analysis |
| EEG_PREPROC_CAR | 4 | Common Average Reference |
| EEG_PREPROC_ARTEFACT_REJ | 5 | Artifact rejection |
| EEG_PREPROC_BASELINE_CORR | 6 | Baseline correction |
| EEG_PREPROC_DOWNSAMPLE | 7 | Downsampling |
| EEG_PREPROC_SEGMENTED | 8 | Segmentation/epoching |

## Data Flow Timing

```
Acquisition Rate: 256 Hz (configurable)
Samples per Message: 64 (4 channels × 64 samples)
Message Rate: ~4 Hz (256 Hz ÷ 64 samples)
Message Interval: ~0.25 seconds

Processing Latency:
  Acquisition → Raw Topic:     < 1 ms
  Raw → Preprocessing:         < 5 ms
  Preprocessing → Processed:   < 10 ms
  Total Pipeline Latency:      < 20 ms
```

## Usage Examples

### Start with Simulator
```bash
USE_ACQUISITION=0 ./launch/start.sh
```

### Start with Neurosity Device
```bash
USE_ACQUISITION=2 ./launch/start.sh
```

### Generate Comparison Plot
```bash
python nodes/visualization/plot_eeg_comparison.py
# Output: plots/eeg_comparison_NNN.png (auto-incremented)
```

### Run Tests
```bash
# Unit tests (22 tests)
python tests/test_eeg_unit.py

# Integration tests (11 tests)
RUN_TESTS=1 RUN_NODE=0 ./launch/start.sh
```
