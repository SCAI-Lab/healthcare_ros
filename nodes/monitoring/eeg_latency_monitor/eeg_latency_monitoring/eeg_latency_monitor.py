#!/usr/bin/env python3
"""
EEG Latency Publisher Node

Computes true end-to-end latency using ROS2 message timestamps
and publishes it as a topic for downstream consumers (e.g. InfluxDB).

Latency definition:
    latency = now() - msg.header.stamp

Requirements:
- Upstream nodes MUST preserve header.stamp
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32
from healthcare_msgs.msg import EEG


class EEGLatencyPublisher(Node):
    def __init__(self):
        super().__init__('eeg_latency_publisher')

        # Publisher
        self.pub = self.create_publisher(Float32, '/eeg/latency', 10)

        # Subscriber (FINAL stage of pipeline)
        self.sub = self.create_subscription(
            EEG,
            '/eeg/processed',
            self.callback,
            10
        )

        self.get_logger().info("Latency publisher started (topic: /eeg/latency)")

    def callback(self, msg: EEG):
        try:
            # Convert ROS time to nanoseconds
            stamp_ns = msg.header.stamp.sec * 1_000_000_000 + msg.header.stamp.nanosec
            now_ns = self.get_clock().now().nanoseconds

            latency_ms = (now_ns - stamp_ns) / 1_000_000.0

            # Filter invalid values
            if latency_ms < 0:
                self.get_logger().debug(
                    f"Filtered out latency: {latency_ms:.2f}ms "
                    f"(stamp_ns={stamp_ns}, now_ns={now_ns})"
                )
                return

            out = Float32()
            out.data = float(latency_ms)

            self.pub.publish(out)
            
            # Log every 50th message to show latency is working
            if int(latency_ms * 1000) % 50 == 0:
                self.get_logger().info(f"Published latency: {latency_ms:.2f}ms")

        except Exception as e:
            self.get_logger().warn(f"Latency calculation failed: {e}")


def main(args=None):
    rclpy.init(args=args)
    node = EEGLatencyPublisher()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()