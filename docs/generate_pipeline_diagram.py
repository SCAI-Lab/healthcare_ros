#!/usr/bin/env python3
"""
Generate pipeline architecture diagram as PNG using matplotlib.
Shows complete EEG processing pipeline with all active components.
Enhanced layout with better visual hierarchy and spacing.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import matplotlib.lines as mlines

# Set up figure with optimal dimensions
fig, ax = plt.subplots(figsize=(22, 16))
ax.set_xlim(0, 22)
ax.set_ylim(0, 16)
ax.axis('off')

# Professional color palette
COLOR_ACQUISITION = '#E8EAF6'  # Indigo 50
COLOR_PREPROC = '#FFF9C4'      # Yellow 100
COLOR_STORAGE = '#E8F5E9'      # Green 50
COLOR_VIZ = '#F3E5F5'          # Purple 50
COLOR_TOPIC = '#FFEBEE'        # Red 50
COLOR_ARROW = '#263238'        # Blue Grey 900
COLOR_TOOLS = '#E1F5FE'        # Light Blue 50
COLOR_TEST = '#FFF3E0'         # Orange 50

# Title with enhanced typography
ax.text(11, 15.3, 'Healthcare EEG Processing Pipeline', 
        fontsize=32, fontweight='bold', ha='center', family='sans-serif')
ax.text(11, 14.75, 'Real-Time Multi-Device Acquisition → Preprocessing → Dual Storage → Visualization',
        fontsize=12, ha='center', style='italic', color='#546E7A')

# ========== DATA ACQUISITION LAYER ==========
acquisition_bg = FancyBboxPatch((0.5, 12.6), 21, 2.3, 
                               boxstyle="round,pad=0.15", 
                               facecolor=COLOR_ACQUISITION, 
                               edgecolor='#3F51B5', linewidth=3, alpha=0.95)
ax.add_patch(acquisition_bg)

ax.text(11, 14.5, '⚡ DATA ACQUISITION LAYER', 
        fontsize=17, fontweight='bold', ha='center', color='#1A237E')

# Active EEG devices (simulator, neurosity, openbci)
eeg_devices = [
    {'x': 5, 'name': 'EEG Simulator', 'desc': '4 channels\n256 Hz sampling\nSynthetic signals', 
     'icon': '🧠', 'path': 'eeg_simulator.py'},
    {'x': 11, 'name': 'Neurosity Crown', 'desc': '8 channels\n256 Hz sampling\nWiFi connection', 
     'icon': '👑', 'path': 'neurosity_driver/'},
    {'x': 17, 'name': 'OpenBCI Cyton', 'desc': '8/16 channels\n250 Hz sampling\nUSB Serial', 
     'icon': '📡', 'path': 'openbci_driver/'},
]

# Draw active EEG device boxes
for dev in eeg_devices:
    box = FancyBboxPatch((dev['x']-1.2, 13.15), 2.4, 1.2,
                        boxstyle="round,pad=0.12",
                        facecolor='white', edgecolor='#5C6BC0', linewidth=3, alpha=0.98)
    ax.add_patch(box)
    
    ax.text(dev['x'], 14.15, dev['icon'], fontsize=24, ha='center', va='center')
    ax.text(dev['x'], 13.85, dev['name'], 
            fontsize=10, fontweight='bold', ha='center', va='center', color='#1A237E')
    ax.text(dev['x'], 13.35, dev['desc'], 
            fontsize=7, ha='center', va='top', color='#616161', linespacing=1.3)
    ax.text(dev['x'], 13.0, dev['path'], 
            fontsize=6, ha='center', va='bottom', color='#9E9E9E', 
            style='italic', family='monospace')

# Active devices label
ax.text(11, 12.75, '✓ Active Devices in Pipeline', fontsize=10, ha='center', 
        fontweight='bold', color='#2E7D32',
        bbox=dict(boxstyle='round,pad=0.4', facecolor='#C8E6C9', 
                 edgecolor='#66BB6A', linewidth=2))

# Arrows from devices to topics
for dev in eeg_devices:
    arrow = FancyArrowPatch((dev['x'], 13.0), (11, 12.1),
                          arrowstyle='->', mutation_scale=20, 
                          color=COLOR_ARROW, linewidth=2.5, alpha=0.75,
                          connectionstyle="arc3,rad=0.1")
    ax.add_patch(arrow)

# ========== RAW TOPICS ==========
raw_topic = FancyBboxPatch((7, 11.2), 8, 0.75,
                          boxstyle="round,pad=0.1",
                          facecolor=COLOR_TOPIC, edgecolor='#C62828', linewidth=3, alpha=0.95)
ax.add_patch(raw_topic)
ax.text(11, 11.75, '📊 /eeg/raw', fontsize=14, fontweight='bold', ha='center', color='#B71C1C')
ax.text(11, 11.4, 'header • session_id • sample_size • eeg[] • quality[]', 
        fontsize=8, ha='center', color='#424242', family='monospace')

raw_info_topic = FancyBboxPatch((7, 10.2), 8, 0.75,
                               boxstyle="round,pad=0.1",
                               facecolor=COLOR_TOPIC, edgecolor='#C62828', linewidth=3, alpha=0.95)
ax.add_patch(raw_info_topic)
ax.text(11, 10.75, '📋 /eeg/raw_info', fontsize=14, fontweight='bold', ha='center', color='#B71C1C')
ax.text(11, 10.4, 'device_info • electrodes • montage | QoS: Latched (transient_local)', 
        fontsize=8, ha='center', color='#424242', family='monospace')

# ========== STORAGE LAYER (RAW) ==========
arrow = FancyArrowPatch((7.5, 11.5), (5.3, 11.5),
                       arrowstyle='->', mutation_scale=25, 
                       color=COLOR_ARROW, linewidth=3)
ax.add_patch(arrow)

json_raw = FancyBboxPatch((2, 10.0), 3.3, 2.4,
                         boxstyle="round,pad=0.12",
                         facecolor=COLOR_STORAGE, edgecolor='#388E3C', linewidth=2.5, alpha=0.95)
ax.add_patch(json_raw)
ax.text(3.65, 12.15, '💾 JSON Saver', fontsize=12, fontweight='bold', ha='center', color='#1B5E20')
ax.text(3.65, 11.85, '(Raw Data)', fontsize=9, ha='center', style='italic', color='#558B2F')
ax.text(3.65, 11.35, 'eeg_data/', fontsize=8, ha='center', fontweight='bold', 
        family='monospace', color='#33691E')
ax.text(3.65, 10.85, '• eeg_raw_data.jsonl\n• eeg_raw_data.info.json', 
        fontsize=7.5, ha='center', color='#1B5E20', linespacing=1.4)
ax.text(3.65, 10.3, 'Line-delimited JSON\nMetadata sidecar', 
        fontsize=6.5, ha='center', color='#616161', style='italic')

arrow = FancyArrowPatch((14.5, 11.5), (16.7, 11.5),
                       arrowstyle='->', mutation_scale=25, 
                       color=COLOR_ARROW, linewidth=3)
ax.add_patch(arrow)

rosbag_raw = FancyBboxPatch((16.7, 10.0), 3.3, 2.4,
                           boxstyle="round,pad=0.12",
                           facecolor=COLOR_STORAGE, edgecolor='#388E3C', linewidth=2.5, alpha=0.95)
ax.add_patch(rosbag_raw)
ax.text(18.35, 12.15, '🗂️ Rosbag Saver', fontsize=12, fontweight='bold', ha='center', color='#1B5E20')
ax.text(18.35, 11.85, '(Raw Data)', fontsize=9, ha='center', style='italic', color='#558B2F')
ax.text(18.35, 11.35, 'rosbag_data/', fontsize=8, ha='center', fontweight='bold',
        family='monospace', color='#33691E')
ax.text(18.35, 10.85, '• eeg_raw_*.mcap', 
        fontsize=7.5, ha='center', color='#1B5E20')
ax.text(18.35, 10.3, 'ROS2 native format\nPlayback & analysis', 
        fontsize=6.5, ha='center', color='#616161', style='italic')

# ========== PREPROCESSING LAYER ==========
arrow = FancyArrowPatch((11, 10.0), (11, 8.8),
                       arrowstyle='->', mutation_scale=28, 
                       color=COLOR_ARROW, linewidth=3.5)
ax.add_patch(arrow)

preproc_bg = FancyBboxPatch((0.5, 6.5), 21, 2.3,
                           boxstyle="round,pad=0.15",
                           facecolor=COLOR_PREPROC, 
                           edgecolor='#EF6C00', linewidth=3, alpha=0.95)
ax.add_patch(preproc_bg)

ax.text(11, 8.5, '🔬 PREPROCESSING LAYER', 
        fontsize=17, fontweight='bold', ha='center', color='#E65100')

# Main preprocessor
preprocessor = FancyBboxPatch((7, 7.0), 8, 1.4,
                             boxstyle="round,pad=0.12",
                             facecolor='white', edgecolor='#F57C00', linewidth=3, alpha=0.98)
ax.add_patch(preprocessor)
ax.text(11, 8.15, '⚙️ EEG Preprocessor Node', fontsize=12, fontweight='bold', ha='center', color='#E65100')
ax.text(11, 7.6, '• Butterworth Bandpass Filter (0.5-45 Hz)\n• Common Average Reference (CAR)\n• Metadata Forwarding + Method Annotations', 
        fontsize=8, ha='center', color='#424242', linespacing=1.4)

# Helper tools module
tools_box = FancyBboxPatch((16.0, 7.0), 3.5, 1.4,
                          boxstyle="round,pad=0.12",
                          facecolor=COLOR_TOOLS, edgecolor='#1976D2', linewidth=2.5, linestyle='--', alpha=0.9)
ax.add_patch(tools_box)
ax.text(17.75, 8.15, '🛠️ Preprocessing Tools', fontsize=10, fontweight='bold', ha='center', color='#0D47A1')
ax.text(17.75, 7.85, 'Module (MNE-based)', fontsize=8, ha='center', style='italic', color='#1565C0')
ax.text(17.75, 7.35, '• ICA • Baseline Correction\n• Epoch Extraction\n• Advanced Filtering', 
        fontsize=7, ha='center', color='#0D47A1', linespacing=1.4)

arrow = FancyArrowPatch((15, 7.7), (16.0, 7.7),
                       arrowstyle='->', mutation_scale=18, 
                       color='#1976D2', linewidth=2, linestyle='--')
ax.add_patch(arrow)

arrow = FancyArrowPatch((11, 6.9), (11, 5.8),
                       arrowstyle='->', mutation_scale=28, 
                       color=COLOR_ARROW, linewidth=3.5)
ax.add_patch(arrow)

# ========== PROCESSED TOPICS ==========
proc_topic = FancyBboxPatch((7, 5.0), 8, 0.75,
                           boxstyle="round,pad=0.1",
                           facecolor=COLOR_TOPIC, edgecolor='#C62828', linewidth=3, alpha=0.95)
ax.add_patch(proc_topic)
ax.text(11, 5.55, '📊 /eeg/processed', fontsize=14, fontweight='bold', ha='center', color='#B71C1C')
ax.text(11, 5.2, 'Filtered & Referenced EEG data', fontsize=8, ha='center', color='#424242')

proc_info_topic = FancyBboxPatch((7, 4.0), 8, 0.75,
                                boxstyle="round,pad=0.1",
                                facecolor=COLOR_TOPIC, edgecolor='#C62828', linewidth=3, alpha=0.95)
ax.add_patch(proc_info_topic)
ax.text(11, 4.55, '📋 /eeg/processed_info', fontsize=14, fontweight='bold', ha='center', color='#B71C1C')
ax.text(11, 4.2, 'Metadata + preprocessing_methods[BANDPASS, CAR]', 
        fontsize=8, ha='center', color='#424242', family='monospace')

# ========== STORAGE LAYER (PROCESSED) ==========
arrow = FancyArrowPatch((7.5, 5.3), (5.3, 5.3),
                       arrowstyle='->', mutation_scale=25, 
                       color=COLOR_ARROW, linewidth=3)
ax.add_patch(arrow)

json_proc = FancyBboxPatch((2, 3.8), 3.3, 2.4,
                          boxstyle="round,pad=0.12",
                          facecolor=COLOR_STORAGE, edgecolor='#388E3C', linewidth=2.5, alpha=0.95)
ax.add_patch(json_proc)
ax.text(3.65, 5.95, '💾 JSON Saver', fontsize=12, fontweight='bold', ha='center', color='#1B5E20')
ax.text(3.65, 5.65, '(Processed)', fontsize=9, ha='center', style='italic', color='#558B2F')
ax.text(3.65, 5.15, 'eeg_data/', fontsize=8, ha='center', fontweight='bold',
        family='monospace', color='#33691E')
ax.text(3.65, 4.65, '• eeg_preprocessed_*.jsonl\n• .info.json', 
        fontsize=7.5, ha='center', color='#1B5E20', linespacing=1.4)
ax.text(3.65, 4.1, 'Filtered data\nwith metadata', 
        fontsize=6.5, ha='center', color='#616161', style='italic')

arrow = FancyArrowPatch((14.5, 5.3), (16.7, 5.3),
                       arrowstyle='->', mutation_scale=25, 
                       color=COLOR_ARROW, linewidth=3)
ax.add_patch(arrow)

rosbag_proc = FancyBboxPatch((16.7, 3.8), 3.3, 2.4,
                            boxstyle="round,pad=0.12",
                            facecolor=COLOR_STORAGE, edgecolor='#388E3C', linewidth=2.5, alpha=0.95)
ax.add_patch(rosbag_proc)
ax.text(18.35, 5.95, '🗂️ Rosbag Saver', fontsize=12, fontweight='bold', ha='center', color='#1B5E20')
ax.text(18.35, 5.65, '(Processed)', fontsize=9, ha='center', style='italic', color='#558B2F')
ax.text(18.35, 5.15, 'rosbag_data/', fontsize=8, ha='center', fontweight='bold',
        family='monospace', color='#33691E')
ax.text(18.35, 4.65, '• eeg_preprocessed_*.mcap', 
        fontsize=7.5, ha='center', color='#1B5E20')
ax.text(18.35, 4.1, 'ROS2 format\nfor playback', 
        fontsize=6.5, ha='center', color='#616161', style='italic')

# ========== VISUALIZATION & ANALYSIS LAYER ==========
viz_bg = FancyBboxPatch((0.5, 0.3), 21, 3.3,
                       boxstyle="round,pad=0.15",
                       facecolor=COLOR_VIZ, 
                       edgecolor='#7B1FA2', linewidth=3, alpha=0.95)
ax.add_patch(viz_bg)

ax.text(11, 3.35, '📈 VISUALIZATION & ANALYSIS', 
        fontsize=17, fontweight='bold', ha='center', color='#4A148C')

# Plot tool
arrow = FancyArrowPatch((3.65, 3.8), (6.5, 2.9),
                       arrowstyle='->', mutation_scale=20, 
                       color=COLOR_ARROW, linewidth=2, linestyle='dashed', alpha=0.7)
ax.add_patch(arrow)

plot_tool = FancyBboxPatch((6.5, 2.2), 4.5, 1.0,
                          boxstyle="round,pad=0.1",
                          facecolor='white', edgecolor='#7B1FA2', linewidth=2.5, alpha=0.98)
ax.add_patch(plot_tool)
ax.text(8.75, 2.95, '📊 Plot Comparison', fontsize=11, fontweight='bold', ha='center', color='#4A148C')
ax.text(8.75, 2.55, 'Raw vs Preprocessed • 2s windows\nplots/eeg_comparison_NNN.png', 
        fontsize=7.5, ha='center', color='#6A1B9A', linespacing=1.4)

# RQT tool
arrow = FancyArrowPatch((11, 4.0), (12.5, 3.2),
                       arrowstyle='->', mutation_scale=20, 
                       color=COLOR_ARROW, linewidth=2, linestyle='dashed', alpha=0.7)
ax.add_patch(arrow)

rqt_tool = FancyBboxPatch((11.5, 2.2), 4.5, 1.0,
                         boxstyle="round,pad=0.1",
                         facecolor='white', edgecolor='#7B1FA2', linewidth=2.5, alpha=0.98)
ax.add_patch(rqt_tool)
ax.text(13.75, 2.95, '🖥️ RQT Live View', fontsize=11, fontweight='bold', ha='center', color='#4A148C')
ax.text(13.75, 2.55, 'Real-time display • Qt GUI\nSubscribes to /eeg/* topics', 
        fontsize=7.5, ha='center', color='#6A1B9A', linespacing=1.4)

# Test framework
test_box = FancyBboxPatch((6.5, 1.0), 9, 0.95,
                         boxstyle="round,pad=0.1",
                         facecolor=COLOR_TEST, edgecolor='#EF6C00', linewidth=2.5, linestyle='--', alpha=0.95)
ax.add_patch(test_box)
ax.text(11, 1.75, '✅ Test Framework', fontsize=11, fontweight='bold', ha='center', color='#E65100')
ax.text(11, 1.4, '22 Unit Tests • 11 Integration Tests • Message Validation • File Organization', 
        fontsize=7.5, ha='center', color='#BF360C', linespacing=1.4)

# Documentation
doc_box = FancyBboxPatch((6.5, 0.4), 9, 0.45,
                        boxstyle="round,pad=0.08",
                        facecolor='white', edgecolor='#7B1FA2', linewidth=2, linestyle='--', alpha=0.95)
ax.add_patch(doc_box)
ax.text(11, 0.7, '📚 Documentation: Architecture diagrams • Docstrings • Launch scripts • params.yaml', 
        fontsize=7.5, ha='center', color='#4A148C')

# ========== LEGEND ==========
legend_elements = [
    mpatches.Patch(facecolor=COLOR_ACQUISITION, edgecolor='#3F51B5', label='Data Acquisition', linewidth=2.5),
    mpatches.Patch(facecolor=COLOR_PREPROC, edgecolor='#EF6C00', label='Preprocessing', linewidth=2.5),
    mpatches.Patch(facecolor=COLOR_STORAGE, edgecolor='#388E3C', label='Storage', linewidth=2.5),
    mpatches.Patch(facecolor=COLOR_VIZ, edgecolor='#7B1FA2', label='Visualization', linewidth=2.5),
    mpatches.Patch(facecolor=COLOR_TOPIC, edgecolor='#C62828', label='ROS2 Topics', linewidth=2.5),
    mlines.Line2D([], [], color='#1976D2', linestyle='--', linewidth=2, label='Optional/Helper'),
]

legend = ax.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(0.022, 0.22), 
                  fontsize=9.5, framealpha=0.98, title='Component Types', title_fontsize=11,
                  edgecolor='#424242', fancybox=True, shadow=True)
legend.get_frame().set_linewidth(2)

# ========== INFO PANEL ==========
info_text = (
    "🚀 System Overview:\n\n"
    "Active Devices:\n"
    "  • Simulator: 4ch synthetic EEG\n"
    "  • Neurosity Crown: 8ch WiFi EEG\n"
    "  • OpenBCI Cyton: 8/16ch serial EEG\n\n"
    "Processing:\n"
    "  • Butterworth bandpass 0.5-45 Hz\n"
    "  • Common Average Reference\n"
    "  • Latched metadata topics\n\n"
    "Storage:\n"
    "  • JSONL: Human-readable lines\n"
    "  • MCAP: ROS2 binary format\n\n"
    "Testing:\n"
    "  • 33 tests (22 unit + 11 integration)\n"
    "  • healthcare_msgs validation\n"
    "  • File organization checks"
)

ax.text(0.7, 3.2, info_text, fontsize=7.5, va='top', family='monospace',
       bbox=dict(boxstyle='round,pad=0.65', facecolor='#FFF9C4', 
                edgecolor='#F57C00', linewidth=2.5, alpha=0.98))

plt.tight_layout()
plt.savefig('/home/tjalf/ros2_ws/src/-healthcare_msgs_demonstration/docs/pipeline_diagram.png', 
            dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
print("✅ Enhanced pipeline diagram saved to: docs/pipeline_diagram.png")
