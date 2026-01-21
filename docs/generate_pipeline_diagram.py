#!/usr/bin/env python3
"""
Generate pipeline architecture diagram as PNG using matplotlib.
Shows complete EEG processing pipeline with all active components.
Enhanced layout with much larger fonts and wider boxes for improved readability.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import matplotlib.lines as mlines

# Set up figure with larger dimensions for better readability
fig, ax = plt.subplots(figsize=(32, 26))
ax.set_xlim(0, 32)
ax.set_ylim(-2, 22)
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

# ========== DATA ACQUISITION LAYER ==========
acquisition_bg = FancyBboxPatch((0.7, 16.5), 30.6, 3.5, 
                               boxstyle="round,pad=0.2", 
                               facecolor=COLOR_ACQUISITION, 
                               edgecolor='#3F51B5', linewidth=4, alpha=0.95)
ax.add_patch(acquisition_bg)

ax.text(16, 19.8, 'DATA ACQUISITION LAYER', 
        fontsize=46, fontweight='bold', ha='center', color='#1A237E')

# Active EEG devices (simulator, neurosity, openbci) - WIDER BOXES
eeg_devices = [
    {'x': 7.0, 'name': 'EEG Simulator', 'type': 'Publisher Node',
     'desc': 'Creates synthetic EEG data', 'msgs': 'EEGRaw, EEGInfo',
     'meta': '4 channels, 256 Hz'},
    {'x': 16, 'name': 'Neurosity Crown', 'type': 'Publisher Node',
     'desc': 'Acquires real EEG via WiFi', 'msgs': 'EEGRaw, EEGInfo',
     'meta': '8 channels, 256 Hz'},
    {'x': 25, 'name': 'OpenBCI Cyton', 'type': 'Publisher Node',
     'desc': 'Acquires EEG via USB serial', 'msgs': 'EEGRaw, EEGInfo',
     'meta': '8-16 channels, 250 Hz'},
]

# Draw active EEG device boxes - MUCH WIDER
for dev in eeg_devices:
    box = FancyBboxPatch((dev['x']-4.5, 16.8), 9.0, 2.625,
                        boxstyle="round,pad=0.2",
                        facecolor='white', edgecolor='#5C6BC0', linewidth=4, alpha=0.98)
    ax.add_patch(box)
    
    # Headline (bold) - MUCH LARGER FONT
    ax.text(dev['x'], 18.7, dev['name'], 
            fontsize=35, fontweight='bold', ha='center', va='center', color='#1A237E')
    
    # Content with double line breaks and labels - MUCH LARGER FONT
    content = (
        f"Node Type: {dev['type']}\n\n"
        f"Description: {dev['desc']}\n\n"
        f"Additional Information: {dev['meta']}"
    )
    ax.text(dev['x'], 17.7, content, 
            fontsize=23, ha='center', va='center', color='#424242', linespacing=1.5)

# Central arrow from devices to raw topic (main data flow - thicker solid)
arrow = FancyArrowPatch((16, 16.3), (16, 15.7),
                      arrowstyle='->', mutation_scale=40, 
                      color=COLOR_ARROW, linewidth=6, alpha=0.9, zorder=10)
ax.add_patch(arrow)

# ========== RAW TOPICS - WIDER ==========
raw_topic = FancyBboxPatch((7.0, 14.3), 18, 1.8,
                          boxstyle="round,pad=0.15",
                          facecolor=COLOR_TOPIC, edgecolor='#C62828', linewidth=4, alpha=0.95)
ax.add_patch(raw_topic)
ax.text(16, 15.5, '/eeg/raw', fontsize=42, fontweight='bold', ha='center', color='#B71C1C')
ax.text(16, 14.9, 'header • session_id • sample_size • eeg[] • quality[]', 
        fontsize=21, ha='center', color='#424242', family='monospace')

raw_info_topic = FancyBboxPatch((7.0, 12.5), 18, 1.8,
                               boxstyle="round,pad=0.15",
                               facecolor=COLOR_TOPIC, edgecolor='#C62828', linewidth=4, alpha=0.95)
ax.add_patch(raw_info_topic)
ax.text(16, 13.7, '/eeg/raw_info', fontsize=42, fontweight='bold', ha='center', color='#B71C1C')
ax.text(16, 13.15, 'device_info • electrodes • montage | QoS: Latched (transient_local)', 
        fontsize=21, ha='center', color='#424242', family='monospace')

# ========== STORAGE LAYER (RAW) - WIDER BOXES ==========
# Arrow to JSON saver (storage - thicker solid)
arrow = FancyArrowPatch((7.0, 14.5), (5.5, 14.5),
                       arrowstyle='->', mutation_scale=30, 
                       color=COLOR_ARROW, linewidth=3.5, alpha=0.9, zorder=10)
ax.add_patch(arrow)

json_raw = FancyBboxPatch((0.8, 13.2), 4.5, 2.5,
                         boxstyle="round,pad=0.2",
                         facecolor=COLOR_STORAGE, edgecolor='#388E3C', linewidth=3.5, alpha=0.95)
ax.add_patch(json_raw)

ax.text(3.05, 15.0, 'JSON Saver (Raw)', fontsize=28, fontweight='bold', ha='center', color='#1B5E20')

json_raw_content = (
    "Node Type: Subscriber Node\n\n"
    "Description: Saves raw EEG to JSONL files\n\n"
    "Additional Information: Line-delimited JSON"
)
ax.text(3.05, 14.2, json_raw_content, fontsize=21, ha='center', va='center', color='#1B5E20', linespacing=1.5)

# Arrow to Rosbag saver (storage - thicker solid)
arrow = FancyArrowPatch((25.0, 14.5), (26.5, 14.5),
                       arrowstyle='->', mutation_scale=30, 
                       color=COLOR_ARROW, linewidth=3.5, alpha=0.9, zorder=10)
ax.add_patch(arrow)

rosbag_raw = FancyBboxPatch((26.7, 13.2), 4.5, 2.5,
                           boxstyle="round,pad=0.2",
                           facecolor=COLOR_STORAGE, edgecolor='#388E3C', linewidth=3.5, alpha=0.95)
ax.add_patch(rosbag_raw)

ax.text(28.95, 15.0, 'Rosbag Saver (Raw)', fontsize=28, fontweight='bold', ha='center', color='#1B5E20')

rosbag_raw_content = (
    "Node Type: Subscriber Node\n\n"
    "Description: Saves raw EEG to MCAP format\n\n"
    "Additional Information: ROS2 native format"
)
ax.text(28.95, 14.2, rosbag_raw_content, fontsize=21, ha='center', va='center', color='#1B5E20', linespacing=1.5)

# ========== PREPROCESSING LAYER - LARGER ==========
# Arrow from raw topics to preprocessing (main data flow - thicker solid)
arrow = FancyArrowPatch((16, 12.0), (16, 11.1),
                       arrowstyle='->', mutation_scale=40, 
                       color=COLOR_ARROW, linewidth=6, alpha=0.9, zorder=10)
ax.add_patch(arrow)

preproc_bg = FancyBboxPatch((0.7, 7.5), 30.6, 3.3,
                           boxstyle="round,pad=0.2",
                           facecolor=COLOR_PREPROC, 
                           edgecolor='#EF6C00', linewidth=4, alpha=0.95)
ax.add_patch(preproc_bg)

ax.text(16, 10.6, 'PREPROCESSING LAYER', 
        fontsize=46, fontweight='bold', ha='center', color='#E65100')

# Main preprocessor - WIDER
preprocessor = FancyBboxPatch((11.0, 7.9), 9.0, 2.5,
                             boxstyle="round,pad=0.2",
                             facecolor='white', edgecolor='#F57C00', linewidth=4, alpha=0.98)
ax.add_patch(preprocessor)

ax.text(15.5, 9.7, 'EEG Preprocessor Node', fontsize=35, fontweight='bold', ha='center', color='#E65100')

preproc_content = (
    "Node Type: Subscriber & Publisher\n\n"
    "Description: Filters and references EEG signals\n\n"
    "Additional Information: Butterworth, Order 4"
)
ax.text(15.5, 8.7, preproc_content, fontsize=23, ha='center', va='center', color='#424242', linespacing=1.5)

# Helper tools module - WIDER
tools_box = FancyBboxPatch((23.5, 8.0), 6.0, 2.5,
                          boxstyle="round,pad=0.2",
                          facecolor=COLOR_TOOLS, edgecolor='#1976D2', linewidth=3.5, linestyle='--', alpha=0.9)
ax.add_patch(tools_box)
ax.text(26.5, 9.8, 'Preprocessing Tools', fontsize=28, fontweight='bold', ha='center', color='#0D47A1')
ax.text(26.5, 9.35, 'Module (MNE-based)', fontsize=21, ha='center', style='italic', color='#1565C0')
ax.text(26.5, 8.6, '• ICA • Baseline Correction\n• Epoch Extraction\n• Advanced Filtering', 
        fontsize=19, ha='center', color='#0D47A1', linespacing=1.5)

# Arrow to optional tools (optional - dashed thicker)
arrow = FancyArrowPatch((20.0, 9.0), (23.5, 9.0),
                       arrowstyle='->', mutation_scale=25, 
                       color=COLOR_ARROW, linewidth=2.5, linestyle='--', alpha=0.7, zorder=10)
ax.add_patch(arrow)

# Arrow from preprocessing to processed topics (main data flow - thicker solid)
arrow = FancyArrowPatch((16, 7.5), (16, 6.8),
                       arrowstyle='->', mutation_scale=40, 
                       color=COLOR_ARROW, linewidth=6, alpha=0.9, zorder=10)
ax.add_patch(arrow)

# ========== PROCESSED TOPICS ==========
proc_topic = FancyBboxPatch((7.0, 5.5), 18, 1.8,
                           boxstyle="round,pad=0.15",
                           facecolor=COLOR_TOPIC, edgecolor='#C62828', linewidth=4, alpha=0.95)
ax.add_patch(proc_topic)
ax.text(16, 6.6, '/eeg/processed', fontsize=42, fontweight='bold', ha='center', color='#B71C1C')
ax.text(16, 6.1, 'Filtered & Referenced EEG data', fontsize=21, ha='center', color='#424242')

proc_info_topic = FancyBboxPatch((7.0, 3.8), 18, 1.8,
                                boxstyle="round,pad=0.15",
                                facecolor=COLOR_TOPIC, edgecolor='#C62828', linewidth=4, alpha=0.95)
ax.add_patch(proc_info_topic)
ax.text(16, 4.9, '/eeg/processed_info', fontsize=42, fontweight='bold', ha='center', color='#B71C1C')
ax.text(16, 4.4, 'Metadata + preprocessing_methods[BANDPASS, CAR]', 
        fontsize=21, ha='center', color='#424242', family='monospace')

# ========== STORAGE LAYER (PROCESSED) - WIDER ==========
# Arrow to JSON processed saver (storage - thicker solid)
arrow = FancyArrowPatch((7.0, 5.7), (5.5, 5.7),
                       arrowstyle='->', mutation_scale=30, 
                       color=COLOR_ARROW, linewidth=3.5, alpha=0.9, zorder=10)
ax.add_patch(arrow)

json_proc = FancyBboxPatch((0.8, 4.5), 4.5, 2.5,
                          boxstyle="round,pad=0.2",
                          facecolor=COLOR_STORAGE, edgecolor='#388E3C', linewidth=3.5, alpha=0.95)
ax.add_patch(json_proc)

ax.text(3.05, 6.3, 'JSON Saver (Processed)', fontsize=28, fontweight='bold', ha='center', color='#1B5E20')

json_proc_content = (
    "Node Type: Subscriber Node\n\n"
    "Description: Saves filtered EEG to JSONL\n\n"
    "Additional Information: Line-delimited JSON"
)
ax.text(3.05, 5.5, json_proc_content, fontsize=21, ha='center', va='center', color='#1B5E20', linespacing=1.5)

# Arrow to Rosbag processed saver (storage - thicker solid)
arrow = FancyArrowPatch((25.0, 5.7), (26.5, 5.7),
                       arrowstyle='->', mutation_scale=30, 
                       color=COLOR_ARROW, linewidth=3.5, alpha=0.9, zorder=10)
ax.add_patch(arrow)

rosbag_proc = FancyBboxPatch((26.7, 4.5), 4.5, 2.5,
                            boxstyle="round,pad=0.2",
                            facecolor=COLOR_STORAGE, edgecolor='#388E3C', linewidth=3.5, alpha=0.95)
ax.add_patch(rosbag_proc)

ax.text(28.95, 6.3, 'Rosbag Saver (Processed)', fontsize=28, fontweight='bold', ha='center', color='#1B5E20')

rosbag_proc_content = (
    "Node Type: Subscriber Node\n\n"
    "Description: Saves filtered EEG to MCAP\n\n"
    "Additional Information: ROS2 native format"
)
ax.text(28.95, 5.5, rosbag_proc_content, fontsize=21, ha='center', va='center', color='#1B5E20', linespacing=1.5)

# ========== VISUALIZATION & ANALYZING LAYER - LARGER ==========
viz_bg = FancyBboxPatch((0.7, -0.5), 30.6, 3.3,
                       boxstyle="round,pad=0.2",
                       facecolor=COLOR_VIZ, 
                       edgecolor='#7B1FA2', linewidth=4, alpha=0.95)
ax.add_patch(viz_bg)

ax.text(16, 2.6, 'VISUALIZATION & ANALYZING LAYER', 
        fontsize=46, fontweight='bold', ha='center', color='#4A148C')

# Visualization tools (plot comparison, rqt live view) - WIDER
viz_tools = [
    {'x': 11.5, 'name': 'Plot Comparison', 'type': 'Subscriber Node',
     'desc': 'Compares raw vs filtered EEG', 'meta': 'PNG images, 2s windows'},
    {'x': 20.5, 'name': 'RQT Live View', 'type': 'Subscriber Plugin',
     'desc': 'Real-time EEG visualization', 'meta': 'Qt5 GUI framework'},
]

# Draw visualization tool boxes - WIDER
for tool in viz_tools:
    box = FancyBboxPatch((tool['x']-4.5, 0.2), 9.0, 2.5,
                        boxstyle="round,pad=0.2",
                        facecolor='white', edgecolor='#AB47BC', linewidth=4, alpha=0.98)
    ax.add_patch(box)
    
    # Headline (bold) - MUCH LARGER
    ax.text(tool['x'], 2.0, tool['name'], 
            fontsize=35, fontweight='bold', ha='center', va='center', color='#4A148C')
    
    # Content with double line breaks and labels - MUCH LARGER
    content = (
        f"Node Type: {tool['type']}\n\n"
        f"Description: {tool['desc']}\n\n"
        f"Additional Information: {tool['meta']}"
    )
    ax.text(tool['x'], 1.0, content, 
            fontsize=23, ha='center', va='center', color='#4A148C', linespacing=1.5)

# Central arrow from processed topics to visualization layer (analysis - thicker solid)
arrow = FancyArrowPatch((16, 3.4), (16, 2.8),
                       arrowstyle='->', mutation_scale=30, 
                       color=COLOR_ARROW, linewidth=6, alpha=0.9, zorder=10)
ax.add_patch(arrow)

# Legend removed for cleaner layout - layer headers and color-coding provide sufficient context

plt.tight_layout()
plt.savefig('/home/tjalf/ros2_ws/src/healthcare_demo/docs/pipeline_diagram.png', 
            dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
print("✅ Enhanced pipeline diagram with improved readability saved to: docs/pipeline_diagram.png")
