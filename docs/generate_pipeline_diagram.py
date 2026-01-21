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
fig, ax = plt.subplots(figsize=(24, 18))
ax.set_xlim(0, 24)
ax.set_ylim(0, 18)
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
ax.text(12, 17.5, 'Healthcare EEG Processing Pipeline', 
        fontsize=34, fontweight='bold', ha='center', family='sans-serif')
ax.text(12, 16.85, 'Real-Time Multi-Device Acquisition → Preprocessing → Dual Storage → Visualization',
        fontsize=13, ha='center', style='italic', color='#546E7A')

# ========== DATA ACQUISITION LAYER ==========
acquisition_bg = FancyBboxPatch((0.5, 12.8), 23, 3.0, 
                               boxstyle="round,pad=0.15", 
                               facecolor=COLOR_ACQUISITION, 
                               edgecolor='#3F51B5', linewidth=3, alpha=0.95)
ax.add_patch(acquisition_bg)

ax.text(12, 15.5, 'DATA ACQUISITION LAYER', 
        fontsize=18, fontweight='bold', ha='center', color='#1A237E')

# Active EEG devices (simulator, neurosity, openbci)
eeg_devices = [
    {'x': 5.5, 'name': 'EEG Simulator', 'type': 'Publisher Node',
     'desc': 'Creates synthetic EEG data', 'msgs': 'EEGRaw, EEGInfo',
     'meta': '4 channels, 256 Hz'},
    {'x': 12, 'name': 'Neurosity Crown', 'type': 'Publisher Node',
     'desc': 'Acquires real EEG via WiFi', 'msgs': 'EEGRaw, EEGInfo',
     'meta': '8 channels, 256 Hz'},
    {'x': 18.5, 'name': 'OpenBCI Cyton', 'type': 'Publisher Node',
     'desc': 'Acquires EEG via USB serial', 'msgs': 'EEGRaw, EEGInfo',
     'meta': '8-16 channels, 250 Hz'},
]

# Draw active EEG device boxes
for dev in eeg_devices:
    box = FancyBboxPatch((dev['x']-1.5, 13.5), 3.0, 1.6,
                        boxstyle="round,pad=0.15",
                        facecolor='white', edgecolor='#5C6BC0', linewidth=3, alpha=0.98)
    ax.add_patch(box)
    
    # Headline (bold)
    ax.text(dev['x'], 14.85, dev['name'], 
            fontsize=9, fontweight='bold', ha='center', va='center', color='#1A237E')
    
    # Content with double line breaks and labels
    content = (
        f"Node Type: {dev['type']}\n\n"
        f"Description: {dev['desc']}\n\n"
        f"Additional Information: {dev['meta']}"
    )
    ax.text(dev['x'], 14.15, content, 
            fontsize=6.5, ha='center', va='center', color='#424242', linespacing=1.4)

# Central arrow from devices to raw topic (main data flow - thick solid)
arrow = FancyArrowPatch((12, 12.8), (12, 11.85),
                      arrowstyle='->', mutation_scale=30, 
                      color=COLOR_ARROW, linewidth=4.5, alpha=0.9, zorder=10)
ax.add_patch(arrow)

# ========== RAW TOPICS ==========
raw_topic = FancyBboxPatch((7.5, 11.0), 9, 0.85,
                          boxstyle="round,pad=0.12",
                          facecolor=COLOR_TOPIC, edgecolor='#C62828', linewidth=3, alpha=0.95)
ax.add_patch(raw_topic)
ax.text(12, 11.65, '/eeg/raw', fontsize=15, fontweight='bold', ha='center', color='#B71C1C')
ax.text(12, 11.25, 'header • session_id • sample_size • eeg[] • quality[]', 
        fontsize=8.5, ha='center', color='#424242', family='monospace')

raw_info_topic = FancyBboxPatch((7.5, 9.9), 9, 0.85,
                               boxstyle="round,pad=0.12",
                               facecolor=COLOR_TOPIC, edgecolor='#C62828', linewidth=3, alpha=0.95)
ax.add_patch(raw_info_topic)
ax.text(12, 10.55, '/eeg/raw_info', fontsize=15, fontweight='bold', ha='center', color='#B71C1C')
ax.text(12, 10.15, 'device_info • electrodes • montage | QoS: Latched (transient_local)', 
        fontsize=8.5, ha='center', color='#424242', family='monospace')

# ========== STORAGE LAYER (RAW) ==========
# Arrow to JSON saver (storage - medium solid)
arrow = FancyArrowPatch((7.5, 10.95), (4.85, 10.95),
                       arrowstyle='->', mutation_scale=22, 
                       color=COLOR_ARROW, linewidth=2.5, alpha=0.9, zorder=10)
ax.add_patch(arrow)

json_raw = FancyBboxPatch((1.85, 10.15), 3.0, 1.6,
                         boxstyle="round,pad=0.15",
                         facecolor=COLOR_STORAGE, edgecolor='#388E3C', linewidth=2.5, alpha=0.95)
ax.add_patch(json_raw)

ax.text(3.35, 11.5, 'JSON Saver (Raw)', fontsize=9, fontweight='bold', ha='center', color='#1B5E20')

json_raw_content = (
    "Node Type: Subscriber Node\n\n"
    "Description: Saves raw EEG to JSONL files\n\n"
    "Additional Information: Line-delimited JSON"
)
ax.text(3.35, 10.8, json_raw_content, fontsize=6.5, ha='center', va='center', color='#1B5E20', linespacing=1.4)

# Arrow to Rosbag saver (storage - medium solid)
arrow = FancyArrowPatch((16.5, 10.95), (19.15, 10.95),
                       arrowstyle='->', mutation_scale=22, 
                       color=COLOR_ARROW, linewidth=2.5, alpha=0.9, zorder=10)
ax.add_patch(arrow)

rosbag_raw = FancyBboxPatch((19.15, 10.15), 3.0, 1.6,
                           boxstyle="round,pad=0.15",
                           facecolor=COLOR_STORAGE, edgecolor='#388E3C', linewidth=2.5, alpha=0.95)
ax.add_patch(rosbag_raw)

ax.text(20.65, 11.5, 'Rosbag Saver (Raw)', fontsize=9, fontweight='bold', ha='center', color='#1B5E20')

rosbag_raw_content = (
    "Node Type: Subscriber Node\n\n"
    "Description: Saves raw EEG to MCAP format\n\n"
    "Additional Information: ROS2 native format"
)
ax.text(20.65, 10.8, rosbag_raw_content, fontsize=6.5, ha='center', va='center', color='#1B5E20', linespacing=1.4)

# ========== PREPROCESSING LAYER ==========
# Arrow from raw topics to preprocessing (main data flow - thick solid)
arrow = FancyArrowPatch((12, 9.9), (12, 9.0),
                       arrowstyle='->', mutation_scale=30, 
                       color=COLOR_ARROW, linewidth=4.5, alpha=0.9, zorder=10)
ax.add_patch(arrow)

preproc_bg = FancyBboxPatch((0.5, 6.0), 23, 3.0,
                           boxstyle="round,pad=0.15",
                           facecolor=COLOR_PREPROC, 
                           edgecolor='#EF6C00', linewidth=3, alpha=0.95)
ax.add_patch(preproc_bg)

ax.text(12, 8.7, 'PREPROCESSING LAYER', 
        fontsize=18, fontweight='bold', ha='center', color='#E65100')

# Main preprocessor
preprocessor = FancyBboxPatch((10.5, 6.7), 3.0, 1.6,
                             boxstyle="round,pad=0.15",
                             facecolor='white', edgecolor='#F57C00', linewidth=3, alpha=0.98)
ax.add_patch(preprocessor)

ax.text(12, 8.05, 'EEG Preprocessor Node', fontsize=9, fontweight='bold', ha='center', color='#E65100')

preproc_content = (
    "Node Type: Subscriber & Publisher\n\n"
    "Description: Filters and references EEG signals\n\n"
    "Additional Information: Butterworth, Order 4"
)
ax.text(12, 7.35, preproc_content, fontsize=6.5, ha='center', va='center', color='#424242', linespacing=1.4)

# Helper tools module
tools_box = FancyBboxPatch((17.5, 6.6), 4.0, 1.7,
                          boxstyle="round,pad=0.15",
                          facecolor=COLOR_TOOLS, edgecolor='#1976D2', linewidth=2.5, linestyle='--', alpha=0.9)
ax.add_patch(tools_box)
ax.text(19.5, 8.1, 'Preprocessing Tools', fontsize=11, fontweight='bold', ha='center', color='#0D47A1')
ax.text(19.5, 7.75, 'Module (MNE-based)', fontsize=9, ha='center', style='italic', color='#1565C0')
ax.text(19.5, 7.15, '• ICA • Baseline Correction\n• Epoch Extraction\n• Advanced Filtering', 
        fontsize=7.5, ha='center', color='#0D47A1', linespacing=1.5)

# Arrow to optional tools (optional - dashed thin)
arrow = FancyArrowPatch((13.5, 7.4), (17.5, 7.4),
                       arrowstyle='->', mutation_scale=18, 
                       color=COLOR_ARROW, linewidth=1.8, linestyle='--', alpha=0.7, zorder=10)
ax.add_patch(arrow)

# Arrow from preprocessing to processed topics (main data flow - thick solid)
arrow = FancyArrowPatch((12, 6.0), (12, 5.1),
                       arrowstyle='->', mutation_scale=30, 
                       color=COLOR_ARROW, linewidth=4.5, alpha=0.9, zorder=10)
ax.add_patch(arrow)

# ========== PROCESSED TOPICS ==========
proc_topic = FancyBboxPatch((7.5, 4.25), 9, 0.85,
                           boxstyle="round,pad=0.12",
                           facecolor=COLOR_TOPIC, edgecolor='#C62828', linewidth=3, alpha=0.95)
ax.add_patch(proc_topic)
ax.text(12, 4.9, '/eeg/processed', fontsize=15, fontweight='bold', ha='center', color='#B71C1C')
ax.text(12, 4.5, 'Filtered & Referenced EEG data', fontsize=8.5, ha='center', color='#424242')

proc_info_topic = FancyBboxPatch((7.5, 3.15), 9, 0.85,
                                boxstyle="round,pad=0.12",
                                facecolor=COLOR_TOPIC, edgecolor='#C62828', linewidth=3, alpha=0.95)
ax.add_patch(proc_info_topic)
ax.text(12, 3.8, '/eeg/processed_info', fontsize=15, fontweight='bold', ha='center', color='#B71C1C')
ax.text(12, 3.4, 'Metadata + preprocessing_methods[BANDPASS, CAR]', 
        fontsize=8.5, ha='center', color='#424242', family='monospace')

# ========== STORAGE LAYER (PROCESSED) ==========
# Arrow to JSON processed saver (storage - medium solid)
arrow = FancyArrowPatch((7.5, 4.1), (4.85, 4.1),
                       arrowstyle='->', mutation_scale=22, 
                       color=COLOR_ARROW, linewidth=2.5, alpha=0.9, zorder=10)
ax.add_patch(arrow)

json_proc = FancyBboxPatch((1.85, 3.3), 3.0, 1.6,
                          boxstyle="round,pad=0.15",
                          facecolor=COLOR_STORAGE, edgecolor='#388E3C', linewidth=2.5, alpha=0.95)
ax.add_patch(json_proc)

ax.text(3.35, 4.65, 'JSON Saver (Processed)', fontsize=9, fontweight='bold', ha='center', color='#1B5E20')

json_proc_content = (
    "Node Type: Subscriber Node\n\n"
    "Description: Saves filtered EEG to JSONL\n\n"
    "Additional Information: Line-delimited JSON"
)
ax.text(3.35, 3.95, json_proc_content, fontsize=6.5, ha='center', va='center', color='#1B5E20', linespacing=1.4)

# Arrow to Rosbag processed saver (storage - medium solid)
arrow = FancyArrowPatch((16.5, 4.1), (19.15, 4.1),
                       arrowstyle='->', mutation_scale=22, 
                       color=COLOR_ARROW, linewidth=2.5, alpha=0.9, zorder=10)
ax.add_patch(arrow)

rosbag_proc = FancyBboxPatch((19.15, 3.3), 3.0, 1.6,
                            boxstyle="round,pad=0.15",
                            facecolor=COLOR_STORAGE, edgecolor='#388E3C', linewidth=2.5, alpha=0.95)
ax.add_patch(rosbag_proc)

ax.text(20.65, 4.65, 'Rosbag Saver (Processed)', fontsize=9, fontweight='bold', ha='center', color='#1B5E20')

rosbag_proc_content = (
    "Node Type: Subscriber Node\n\n"
    "Description: Saves filtered EEG to MCAP\n\n"
    "Additional Information: ROS2 native format"
)
ax.text(20.65, 3.95, rosbag_proc_content, fontsize=6.5, ha='center', va='center', color='#1B5E20', linespacing=1.4)

# ========== VISUALIZATION & ANALYZING LAYER ==========
viz_bg = FancyBboxPatch((0.5, -0.8), 23, 3.0,
                       boxstyle="round,pad=0.15",
                       facecolor=COLOR_VIZ, 
                       edgecolor='#7B1FA2', linewidth=3, alpha=0.95)
ax.add_patch(viz_bg)

ax.text(12, 1.9, 'VISUALIZATION & ANALYZING LAYER', 
        fontsize=18, fontweight='bold', ha='center', color='#4A148C')

# Visualization tools (plot comparison, rqt live view)
viz_tools = [
    {'x': 9.0, 'name': 'Plot Comparison', 'type': 'Subscriber Node',
     'desc': 'Compares raw vs filtered EEG', 'meta': 'PNG images, 2s windows'},
    {'x': 15.0, 'name': 'RQT Live View', 'type': 'Subscriber Plugin',
     'desc': 'Real-time EEG visualization', 'meta': 'Qt5 GUI framework'},
]

# Draw visualization tool boxes
for tool in viz_tools:
    box = FancyBboxPatch((tool['x']-1.5, -0.1), 3.0, 1.6,
                        boxstyle="round,pad=0.15",
                        facecolor='white', edgecolor='#7B1FA2', linewidth=2.5, alpha=0.98)
    ax.add_patch(box)
    
    # Headline (bold)
    ax.text(tool['x'], 1.25, tool['name'], 
            fontsize=9, fontweight='bold', ha='center', va='center', color='#4A148C')
    
    # Content with double line breaks and labels
    content = (
        f"Node Type: {tool['type']}\n\n"
        f"Description: {tool['desc']}\n\n"
        f"Additional Information: {tool['meta']}"
    )
    ax.text(tool['x'], 0.55, content, 
            fontsize=6.5, ha='center', va='center', color='#4A148C', linespacing=1.4)

# Central arrow from processed topics to visualization layer (analysis - thin solid)
arrow = FancyArrowPatch((12, 3.15), (12, 2.2),
                       arrowstyle='->', mutation_scale=20, 
                       color=COLOR_ARROW, linewidth=4.5, alpha=0.9, zorder=10)
ax.add_patch(arrow)

# ========== LEGEND ==========
legend_elements = [
    mpatches.Patch(facecolor=COLOR_ACQUISITION, edgecolor='#3F51B5', label='Data Acquisition', linewidth=2.5),
    mpatches.Patch(facecolor=COLOR_PREPROC, edgecolor='#EF6C00', label='Preprocessing', linewidth=2.5),
    mpatches.Patch(facecolor=COLOR_STORAGE, edgecolor='#388E3C', label='Storage', linewidth=2.5),
    mpatches.Patch(facecolor=COLOR_VIZ, edgecolor='#7B1FA2', label='Visualization', linewidth=2.5),
    mpatches.Patch(facecolor=COLOR_TOPIC, edgecolor='#C62828', label='ROS2 Topics', linewidth=2.5),
    mlines.Line2D([], [], color=COLOR_ARROW, linewidth=4.5, label='Main Data Flow'),
    mlines.Line2D([], [], color=COLOR_ARROW, linewidth=2.5, label='Storage'),
    mlines.Line2D([], [], color=COLOR_ARROW, linestyle='--', linewidth=1.8, label='Used Tools'),
]

legend = ax.legend(handles=legend_elements, loc='lower left', bbox_to_anchor=(0.02, 0.01), 
                  fontsize=9, framealpha=0.98, title='Component Types', title_fontsize=10,
                  edgecolor='#424242', fancybox=True, shadow=True, ncol=3)
legend.get_frame().set_linewidth(2)

plt.tight_layout()
plt.savefig('/home/tjalf/ros2_ws/src/-healthcare_demo/docs/pipeline_diagram.png', 
            dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
print("✅ Enhanced pipeline diagram saved to: docs/pipeline_diagram.png")
