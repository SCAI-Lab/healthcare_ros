SAMPLING_RATE = 256  # Hz (adjust if needed)
"""EEG Visualization Widget for rqt.

This widget subscribes to raw EEG (/neurosity/eeg) and preprocessed EEG
(/neurosity/eeg_processed) topics and displays them side-by-side with
matplotlib plots embedded in Qt.
"""

import sys
from collections import deque
from typing import Optional, Dict, List

import numpy as np
from python_qt_binding import QtCore, QtGui, QtWidgets
from python_qt_binding.QtCore import Qt, pyqtSignal, QTimer

import rclpy
from rclpy.node import Node
from healthcare_msgs.msg import EEG
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class EEGDataBuffer:
    """Thread-safe circular buffer for EEG data."""

    def __init__(self, max_samples: int = 1024):
        self.max_samples = max_samples
        self.buffer = deque(maxlen=max_samples)
        self.lock = QtCore.QMutex()

    def append(self, data: np.ndarray) -> None:
        with QtCore.QMutexLocker(self.lock):
            if data.ndim == 1:
                self.buffer.append(data)
            else:
                # Flatten multi-channel data
                self.buffer.append(data.flatten())

    def get_data(self) -> np.ndarray:
        with QtCore.QMutexLocker(self.lock):
            if not self.buffer:
                return np.array([])
            return np.concatenate(list(self.buffer))

    def clear(self) -> None:
        with QtCore.QMutexLocker(self.lock):
            self.buffer.clear()


class EEGSubscriber(Node):
    """ROS2 Node to subscribe to EEG topics."""

    data_received_raw = pyqtSignal(dict)  # type: ignore
    data_received_processed = pyqtSignal(dict)  # type: ignore

    def __init__(self):
        super().__init__("eeg_visualization_subscriber")

        self.raw_subscription = self.create_subscription(
            EEG, "/neurosity/eeg", self._on_raw_eeg, 10
        )
        self.processed_subscription = self.create_subscription(
            EEG, "/neurosity/eeg_processed", self._on_processed_eeg, 10
        )

        self.get_logger().info("EEG Subscriber node initialized")

    def _on_raw_eeg(self, msg: EEG) -> None:
        data = {
            "eeg": np.array(msg.eeg, dtype=float),
            "quality": np.array(msg.quality, dtype=float),
            "sample_size": msg.sample_size,
            "session_id": msg.session_id,
        }
        self.data_received_raw.emit(data)

    def _on_processed_eeg(self, msg: EEG) -> None:
        data = {
            "eeg": np.array(msg.eeg, dtype=float),
            "quality": np.array(msg.quality, dtype=float),
            "sample_size": msg.sample_size,
            "session_id": msg.session_id,
        }
        self.data_received_processed.emit(data)



# rqt plugin base import
from rqt_gui_py.plugin import Plugin

class EEGVisualizationWidget(QtWidgets.QWidget):
    """Main widget for EEG visualization (not the rqt plugin base)."""
    def __init__(self, context=None):
        super().__init__()
        self.context = context
        self.setWindowTitle("EEG Visualization")
        self.setGeometry(100, 100, 1400, 600)
        # ...existing code...
        # ROS2 node
        if not rclpy.ok():
            rclpy.init()
        self.ros_node = EEGSubscriber()
        # Data buffers
        self.raw_buffer = EEGDataBuffer(max_samples=512)
        self.processed_buffer = EEGDataBuffer(max_samples=512)
        # Message counters
        self.raw_count = 0
        self.processed_count = 0
        # Setup UI
        self._setup_ui()
        # Connect ROS signals
        self.ros_node.data_received_raw.connect(self._on_raw_data_received)
        self.ros_node.data_received_processed.connect(
            self._on_processed_data_received
        )
        # Start ROS2 spin in background thread
        self.ros_thread = QtCore.QThread()
        self.ros_node.moveToThread(self.ros_thread)
        self.ros_thread.started.connect(self._ros_spin)
        self.ros_thread.start()
        # Timer to update plots
        self.plot_timer = QTimer()
        self.plot_timer.timeout.connect(self._update_plots)
        self.plot_timer.start(500)  # Update every 500ms
        self.get_logger().info("EEG Visualization widget initialized")


class EEGVisualizationPlugin(Plugin):
    def __init__(self, context):
        super().__init__(context)
        self.setObjectName('EEGVisualizationPlugin')
        self._widget = EEGVisualizationWidget(context)
        if context.serial_number() > 1:
            self._widget.setWindowTitle(self._widget.windowTitle() + (' (%d)' % context.serial_number()))
        context.add_widget(self._widget)

    def get_logger(self):
        """Provide a logger for UI messages."""

        class SimpleLogger:
            def info(self, msg):
                print(f"[INFO] {msg}")

            def warn(self, msg):
                print(f"[WARN] {msg}")

            def error(self, msg):
                print(f"[ERROR] {msg}")

        return SimpleLogger()

    def _setup_ui(self) -> None:
        """Set up the main UI layout."""
        layout = QtWidgets.QVBoxLayout()

        # Title
        title = QtWidgets.QLabel("EEG Preprocessing Visualization")
        title_font = title.font()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        # Control buttons
        control_layout = QtWidgets.QHBoxLayout()
        self.clear_btn = QtWidgets.QPushButton("Clear Buffers")
        self.clear_btn.clicked.connect(self._clear_buffers)
        control_layout.addWidget(self.clear_btn)

        self.auto_scale_chk = QtWidgets.QCheckBox("Auto-scale Y")
        self.auto_scale_chk.setChecked(True)
        control_layout.addWidget(self.auto_scale_chk)

        self.status_label = QtWidgets.QLabel("Waiting for data...")
        control_layout.addWidget(self.status_label)
        control_layout.addStretch()

        layout.addLayout(control_layout)

        # Create matplotlib figures
        self.fig_raw, self.ax_raw = self._create_figure()
        self.fig_processed, self.ax_processed = self._create_figure()

        # Create canvases
        self.canvas_raw = FigureCanvas(self.fig_raw)
        self.canvas_processed = FigureCanvas(self.fig_processed)

        # Create plots layout (side-by-side)
        plots_layout = QtWidgets.QHBoxLayout()

        # Raw plot section
        raw_section = QtWidgets.QVBoxLayout()
        raw_title = QtWidgets.QLabel("Raw EEG (/neurosity/eeg)")
        raw_title_font = raw_title.font()
        raw_title_font.setBold(True)
        raw_title.setFont(raw_title_font)
        raw_section.addWidget(raw_title)
        raw_section.addWidget(self.canvas_raw)
        self.raw_msg_label = QtWidgets.QLabel("Messages: 0")
        raw_section.addWidget(self.raw_msg_label)

        # Processed plot section
        processed_section = QtWidgets.QVBoxLayout()
        processed_title = QtWidgets.QLabel("Processed EEG (/neurosity/eeg_processed)")
        processed_title_font = processed_title.font()
        processed_title_font.setBold(True)
        processed_title.setFont(processed_title_font)
        processed_section.addWidget(processed_title)
        processed_section.addWidget(self.canvas_processed)
        self.processed_msg_label = QtWidgets.QLabel("Messages: 0")
        processed_section.addWidget(self.processed_msg_label)

        plots_layout.addLayout(raw_section)
        plots_layout.addLayout(processed_section)

        layout.addLayout(plots_layout)
        self.setLayout(layout)

    def _create_figure(self) -> tuple:
        """Create a matplotlib figure with appropriate styling."""
        fig = Figure(figsize=(6, 4), dpi=100)
        ax = fig.add_subplot(111)
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Amplitude (µV)")
        ax.grid(True, alpha=0.3)
        fig.tight_layout()
        return fig, ax

    def _on_raw_data_received(self, data: Dict) -> None:
        """Callback when raw EEG data is received."""
        self.raw_buffer.append(data["eeg"])
        self.raw_count += 1

    def _on_processed_data_received(self, data: Dict) -> None:
        """Callback when processed EEG data is received."""
        self.processed_buffer.append(data["eeg"])
        self.processed_count += 1

    def _update_plots(self) -> None:
        """Update both plot displays."""
        raw_data = self.raw_buffer.get_data()
        processed_data = self.processed_buffer.get_data()

        # Prepare time axes
        raw_times = np.arange(len(raw_data)) / SAMPLING_RATE if len(raw_data) > 0 else []
        processed_times = np.arange(len(processed_data)) / SAMPLING_RATE if len(processed_data) > 0 else []

        # Update raw plot
        self.ax_raw.clear()
        if len(raw_data) > 0:
            self.ax_raw.plot(raw_times, raw_data, linewidth=0.8, color="blue", alpha=0.8)
            self.ax_raw.set_title(f"Raw EEG Signal - Sampling Rate: {SAMPLING_RATE} Hz")
        else:
            self.ax_raw.text(
                0.5, 0.5, "No data", ha="center", va="center", transform=self.ax_raw.transAxes
            )
            self.ax_raw.set_title(f"Raw EEG Signal (Waiting...) - Sampling Rate: {SAMPLING_RATE} Hz")

        if self.auto_scale_chk.isChecked() and len(raw_data) > 0:
            self.ax_raw.autoscale_view()
        self.ax_raw.set_xlabel("Time (s)")
        self.ax_raw.set_ylabel("Amplitude (µV)")
        self.ax_raw.grid(True, alpha=0.3)
        self.fig_raw.tight_layout()
        self.canvas_raw.draw()

        # Update processed plot
        self.ax_processed.clear()
        if len(processed_data) > 0:
            self.ax_processed.plot(processed_times, processed_data, linewidth=0.8, color="green", alpha=0.8)
            self.ax_processed.set_title(f"Preprocessed EEG Signal - Sampling Rate: {SAMPLING_RATE} Hz")
        else:
            self.ax_processed.text(
                0.5, 0.5, "No data", ha="center", va="center", transform=self.ax_processed.transAxes
            )
            self.ax_processed.set_title(f"Preprocessed EEG Signal (Waiting...) - Sampling Rate: {SAMPLING_RATE} Hz")

        if self.auto_scale_chk.isChecked() and len(processed_data) > 0:
            self.ax_processed.autoscale_view()
        self.ax_processed.set_xlabel("Time (s)")
        self.ax_processed.set_ylabel("Amplitude (µV)")
        self.ax_processed.grid(True, alpha=0.3)
        self.fig_processed.tight_layout()
        self.canvas_processed.draw()

        # Update status
        self.raw_msg_label.setText(f"Messages: {self.raw_count}")
        self.processed_msg_label.setText(f"Messages: {self.processed_count}")
        self.status_label.setText(
            f"Raw: {len(raw_data)} samples | Processed: {len(processed_data)} samples"
        )

    def _clear_buffers(self) -> None:
        """Clear data buffers."""
        self.raw_buffer.clear()
        self.processed_buffer.clear()
        self.raw_count = 0
        self.processed_count = 0
        self.get_logger().info("Buffers cleared")

    def _ros_spin(self) -> None:
        """Spin ROS2 node in background thread."""
        try:
            while rclpy.ok():
                rclpy.spin_once(self.ros_node, timeout_sec=0.1)
        except Exception as e:
            self.get_logger().error(f"Error in ROS spin: {e}")

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        """Clean up on widget close."""
        self.plot_timer.stop()
        if self.ros_node:
            self.ros_node.destroy_node()
        self.ros_thread.quit()
        self.ros_thread.wait()
        event.accept()
